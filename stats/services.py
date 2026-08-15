"""Port of src/domain/stats/stats.service.ts. All aggregation happens in
Python over the joined game_players+games+commanders rows, exactly like the
Node version does in JS rather than in SQL — kept that way here for a
faithful, side-by-side port."""

from dataclasses import dataclass, field

from decks.services import get_retired_commander_id_set
from games.services import EnrichedGamePlayerFilters, list_enriched_game_players
from players.services import get_family_ids, get_player_identity_map

from .collation import locale_sort_key
from .dates import days_since, round1, ymd


@dataclass
class DeckAgg:
    commander_id: object
    commander_name: str
    count: int = 0
    wins: int = 0
    last_played: object = None
    first_played: object = None
    last_win: object = None
    win_minutes: list = field(default_factory=list)
    win_turns: list = field(default_factory=list)
    players: set = field(default_factory=set)


def build_deck_map(rows) -> dict:
    deck_map: dict = {}
    for row in rows:
        agg = deck_map.get(row.commander_id)
        if agg is None:
            agg = DeckAgg(commander_id=row.commander_id, commander_name=row.commander.name)
            deck_map[row.commander_id] = agg
        agg.count += 1
        created_on = row.game.created_on
        if agg.last_played is None or created_on > agg.last_played:
            agg.last_played = created_on
        if agg.first_played is None or created_on < agg.first_played:
            agg.first_played = created_on
        if row.is_winner:
            agg.wins += 1
            if agg.last_win is None or created_on > agg.last_win:
                agg.last_win = created_on
            if row.game.game_time_in_minutes is not None:
                agg.win_minutes.append(row.game.game_time_in_minutes)
            if row.game.total_turns is not None:
                agg.win_turns.append(row.game.total_turns)
    return deck_map


def to_deck_stat_dto(agg: DeckAgg, retired_set: set) -> dict:
    return {
        "commanderId": str(agg.commander_id),
        "commanderName": agg.commander_name,
        "gamesPlayed": agg.count,
        "wins": agg.wins,
        "winRate": round1((agg.wins / agg.count) * 100) if agg.count else 0,
        "lastPlayed": ymd(agg.last_played) if agg.last_played else None,
        "firstPlayed": ymd(agg.first_played) if agg.first_played else None,
        "daysSinceLastPlayed": days_since(agg.last_played) if agg.last_played else None,
        "retired": agg.commander_id in retired_set,
    }


def get_player_rows(canonical_player_id, include_retired: bool = False):
    family_ids = get_family_ids(canonical_player_id)
    retired_set = get_retired_commander_id_set(family_ids)
    all_rows = list(list_enriched_game_players(EnrichedGamePlayerFilters(player_family_ids=family_ids)))
    rows = all_rows if include_retired else [r for r in all_rows if r.commander_id not in retired_set]
    return rows, retired_set


def get_player_decks(canonical_player_id, include_retired: bool = False) -> list[dict]:
    rows, retired_set = get_player_rows(canonical_player_id, include_retired)
    deck_map = build_deck_map(rows)
    aggs = sorted(deck_map.values(), key=lambda a: (-a.count, locale_sort_key(a.commander_name)))
    return [to_deck_stat_dto(a, retired_set) for a in aggs]


def get_least_played_decks(canonical_player_id, limit: int = 10, include_retired: bool = False) -> list[dict]:
    rows, retired_set = get_player_rows(canonical_player_id, include_retired)
    deck_map = build_deck_map(rows)

    def sort_key(a: DeckAgg):
        days = days_since(a.last_played) if a.last_played else -1
        return (a.count, -days, locale_sort_key(a.commander_name))

    aggs = sorted(deck_map.values(), key=sort_key)
    return [to_deck_stat_dto(a, retired_set) for a in aggs[:limit]]


def get_longest_since_played_decks(canonical_player_id, limit: int = 10, include_retired: bool = False) -> list[dict]:
    rows, retired_set = get_player_rows(canonical_player_id, include_retired)
    deck_map = build_deck_map(rows)
    aggs = sorted(
        (a for a in deck_map.values() if a.last_played),
        key=lambda a: (-days_since(a.last_played), locale_sort_key(a.commander_name)),
    )
    return [to_deck_stat_dto(a, retired_set) for a in aggs[:limit]]


def _rank_by_speed(deck_map: dict, metric: str, wins_min: int, limit: int, direction: str, retired_set: set) -> list[dict]:
    candidates = []
    for agg in deck_map.values():
        arr = agg.win_minutes if metric == "minutes" else agg.win_turns
        if len(arr) < wins_min:
            continue
        avg = sum(arr) / len(arr)
        candidates.append({"agg": agg, "avg": avg, "min": min(arr), "max": max(arr), "wins": len(arr)})

    candidates.sort(
        key=lambda r: (
            r["avg"] if direction == "fast" else -r["avg"],
            -r["wins"],
            locale_sort_key(r["agg"].commander_name),
        )
    )

    out = []
    for r in candidates[:limit]:
        dto = to_deck_stat_dto(r["agg"], retired_set)
        dto.update({"avg": round1(r["avg"]), "min": r["min"], "max": r["max"], "unit": metric})
        out.append(dto)
    return out


def get_fastest_to_win_decks(
    canonical_player_id, metric: str = "minutes", wins_min: int = 1, limit: int = 10, include_retired: bool = False
) -> list[dict]:
    rows, retired_set = get_player_rows(canonical_player_id, include_retired)
    deck_map = build_deck_map(rows)
    return _rank_by_speed(deck_map, metric, wins_min, limit, "fast", retired_set)


def get_slowest_to_win_decks(
    canonical_player_id, metric: str = "minutes", wins_min: int = 1, limit: int = 10, include_retired: bool = False
) -> list[dict]:
    rows, retired_set = get_player_rows(canonical_player_id, include_retired)
    deck_map = build_deck_map(rows)
    return _rank_by_speed(deck_map, metric, wins_min, limit, "slow", retired_set)


def compute_streaks_from_events(events: list[dict]) -> dict:
    empty = {"length": 0, "startDate": None, "endDate": None}
    if not events:
        return {"longestWinStreak": empty, "longestLossStreak": empty}

    sorted_events = sorted(events, key=lambda e: e["date"])
    cur_type = None
    cur_len = 0
    cur_start = None
    best_win = {"len": 0, "start": None, "end": None}
    best_loss = {"len": 0, "start": None, "end": None}

    def commit(end_date):
        nonlocal best_win, best_loss
        if cur_type == "win" and cur_len > best_win["len"]:
            best_win = {"len": cur_len, "start": cur_start, "end": end_date}
        elif cur_type == "loss" and cur_len > best_loss["len"]:
            best_loss = {"len": cur_len, "start": cur_start, "end": end_date}

    for i, ev in enumerate(sorted_events):
        t = "win" if ev["win"] else "loss"
        if cur_type is None:
            cur_type, cur_len, cur_start = t, 1, ev["date"]
        elif t == cur_type:
            cur_len += 1
        else:
            commit(sorted_events[i - 1]["date"])
            cur_type, cur_len, cur_start = t, 1, ev["date"]
    commit(sorted_events[-1]["date"])

    return {
        "longestWinStreak": {
            "length": best_win["len"],
            "startDate": ymd(best_win["start"]) if best_win["start"] else None,
            "endDate": ymd(best_win["end"]) if best_win["end"] else None,
        },
        "longestLossStreak": {
            "length": best_loss["len"],
            "startDate": ymd(best_loss["start"]) if best_loss["start"] else None,
            "endDate": ymd(best_loss["end"]) if best_loss["end"] else None,
        },
    }


def get_player_streaks(canonical_player_id, include_retired: bool = False) -> dict:
    rows, _ = get_player_rows(canonical_player_id, include_retired)
    events = [{"date": r.game.created_on, "win": r.is_winner} for r in rows]
    return compute_streaks_from_events(events)


# ---- Yearly summary (cross-player) ----


def get_yearly_summary(
    year: int,
    include_retired: bool = False,
    top: int = 10,
    min_games: int = 5,
    wins_min: int = 2,
    metric: str = "minutes",
    per_player_commanders: bool = False,
) -> dict:
    all_rows = list(list_enriched_game_players(EnrichedGamePlayerFilters(year=year)))
    canonical_id_by_raw_id, name_by_canonical_id = get_player_identity_map()

    retired_cache: dict = {}

    def retired_set_for(canonical_id) -> set:
        if canonical_id not in retired_cache:
            family_ids = get_family_ids(canonical_id)
            retired_cache[canonical_id] = get_retired_commander_id_set(family_ids)
        return retired_cache[canonical_id]

    rows = []
    for row in all_rows:
        canonical_player_id = canonical_id_by_raw_id.get(row.player_id, row.player_id)
        if not include_retired and row.commander_id in retired_set_for(canonical_player_id):
            continue
        rows.append((row, canonical_player_id))

    players: dict = {}
    decks: dict = {}
    game_ids_in_year: set = set()
    turns_sum = turns_n = mins_sum = mins_n = 0
    seen_game_metric: set = set()

    for row, canonical_player_id in rows:
        game_ids_in_year.add(row.game_id)
        if row.game_id not in seen_game_metric:
            seen_game_metric.add(row.game_id)
            if row.game.total_turns is not None:
                turns_sum += row.game.total_turns
                turns_n += 1
            if row.game.game_time_in_minutes is not None:
                mins_sum += row.game.game_time_in_minutes
                mins_n += 1

        p_agg = players.setdefault(
            canonical_player_id, {"games": 0, "wins": 0, "uniqueDecks": set(), "events": []}
        )
        p_agg["games"] += 1
        p_agg["uniqueDecks"].add(row.commander_id)
        p_agg["events"].append({"date": row.game.created_on, "win": row.is_winner})
        if row.is_winner:
            p_agg["wins"] += 1

        d_agg = decks.get(row.commander_id)
        if d_agg is None:
            d_agg = DeckAgg(commander_id=row.commander_id, commander_name=row.commander.name)
            decks[row.commander_id] = d_agg
        d_agg.count += 1
        d_agg.players.add(canonical_player_id)
        created_on = row.game.created_on
        if d_agg.last_played is None or created_on > d_agg.last_played:
            d_agg.last_played = created_on
        if d_agg.first_played is None or created_on < d_agg.first_played:
            d_agg.first_played = created_on
        if row.is_winner:
            d_agg.wins += 1
            if d_agg.last_win is None or created_on > d_agg.last_win:
                d_agg.last_win = created_on
            if row.game.game_time_in_minutes is not None:
                d_agg.win_minutes.append(row.game.game_time_in_minutes)
            if row.game.total_turns is not None:
                d_agg.win_turns.append(row.game.total_turns)

    def name_of(player_id) -> str:
        return name_by_canonical_id.get(player_id, str(player_id))

    players_by_unique_decks = sorted(
        (
            {"playerId": str(pid), "name": name_of(pid), "uniqueDecks": len(p["uniqueDecks"]), "games": p["games"]}
            for pid, p in players.items()
        ),
        key=lambda x: (-x["uniqueDecks"], -x["games"], locale_sort_key(x["name"])),
    )[:top]

    players_by_win_rate = sorted(
        (
            {
                "playerId": str(pid),
                "name": name_of(pid),
                "games": p["games"],
                "wins": p["wins"],
                "rate": round1((p["wins"] / p["games"]) * 100),
            }
            for pid, p in players.items()
            if p["games"] >= min_games
        ),
        key=lambda x: (-x["rate"], -x["wins"], -x["games"], locale_sort_key(x["name"])),
    )[:top]

    players_by_wins = sorted(
        ({"playerId": str(pid), "name": name_of(pid), "wins": p["wins"], "games": p["games"]} for pid, p in players.items()),
        key=lambda x: (-x["wins"], -x["games"], locale_sort_key(x["name"])),
    )[:top]

    players_by_games = sorted(
        (
            {"playerId": str(pid), "name": name_of(pid), "games": p["games"], "uniqueDecks": len(p["uniqueDecks"])}
            for pid, p in players.items()
        ),
        key=lambda x: (-x["games"], -x["uniqueDecks"], locale_sort_key(x["name"])),
    )[:top]

    def streak_rows(kind: str) -> list[dict]:
        out = []
        for pid, p in players.items():
            streaks = compute_streaks_from_events(p["events"])
            s = streaks["longestWinStreak"] if kind == "win" else streaks["longestLossStreak"]
            if s["length"] > 0:
                out.append({"playerId": str(pid), "name": name_of(pid), "length": s["length"], "startDate": s["startDate"], "endDate": s["endDate"]})
        out.sort(key=lambda x: (-x["length"], locale_sort_key(x["name"])))
        return out[:top]

    commanders_by_most_played = sorted(
        (
            {"commanderId": str(d.commander_id), "name": d.commander_name, "games": d.count, "players": len(d.players), "wins": d.wins}
            for d in decks.values()
        ),
        key=lambda x: (-x["games"], -x["players"], -x["wins"], locale_sort_key(x["name"])),
    )[:top]

    commanders_by_most_wins = sorted(
        (
            {
                "commanderId": str(d.commander_id),
                "name": d.commander_name,
                "wins": d.wins,
                "games": d.count,
                "rate": round1((d.wins / d.count) * 100) if d.count else 0,
            }
            for d in decks.values()
        ),
        key=lambda x: (-x["wins"], -x["rate"], -x["games"], locale_sort_key(x["name"])),
    )[:top]

    def speed_rows(direction: str) -> list[dict]:
        candidates = []
        for d in decks.values():
            arr = d.win_minutes if metric == "minutes" else d.win_turns
            if len(arr) < wins_min:
                continue
            candidates.append(
                {
                    "commanderId": str(d.commander_id),
                    "name": d.commander_name,
                    "wins": len(arr),
                    "avg": round1(sum(arr) / len(arr)),
                    "min": min(arr),
                    "max": max(arr),
                }
            )
        candidates.sort(key=lambda x: (x["avg"] if direction == "fast" else -x["avg"], -x["wins"], locale_sort_key(x["name"])))
        return candidates[:top]

    result = {
        "year": year,
        "totalGames": len(game_ids_in_year),
        "avgMinutesPerGame": round1(mins_sum / mins_n) if mins_n else None,
        "avgTurnsPerGame": round1(turns_sum / turns_n) if turns_n else None,
        "uniquePlayers": len(players),
        "uniqueCommanders": len(decks),
        "playersByUniqueDecks": players_by_unique_decks,
        "playersByWinRate": players_by_win_rate,
        "playersByWins": players_by_wins,
        "playersByGames": players_by_games,
        "playersByWinStreak": streak_rows("win"),
        "playersByLossStreak": streak_rows("loss"),
        "commandersByMostPlayed": commanders_by_most_played,
        "commandersByMostWins": commanders_by_most_wins,
        "commandersFastestToWin": speed_rows("fast"),
        "commandersSlowestToWin": speed_rows("slow"),
    }

    if per_player_commanders:
        per_player = {}
        for pid in players:
            retired = set() if include_retired else retired_set_for(pid)
            player_rows = [row for row, cpid in rows if cpid == pid]
            deck_map = build_deck_map(player_rows)
            aggs = sorted(deck_map.values(), key=lambda a: (-a.count, locale_sort_key(a.commander_name)))
            per_player[str(pid)] = {"name": name_of(pid), "decks": [to_deck_stat_dto(a, retired) for a in aggs]}
        result["perPlayerCommanders"] = per_player

    return result
