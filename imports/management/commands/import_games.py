import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from commanders.models import Commander
from games.models import Game, GamePlayer
from players.models import Player


class Command(BaseCommand):
    help = "Import games from the MythicTrack AllGames.json export (idempotent, upserts by UUID)."

    def handle(self, *args, **options):
        games_path = Path(settings.GAMES_EXPORT_PATH)
        if not games_path.exists():
            raise CommandError(f"Missing games export at {games_path}")
        games = json.loads(games_path.read_text())
        if not isinstance(games, list) or not games:
            raise CommandError(f"Expected a non-empty array at {games_path}")

        merges_path = Path(settings.PLAYER_MERGES_PATH)
        merges = json.loads(merges_path.read_text()) if merges_path.exists() else []

        commander_rows: dict = {}
        player_rows: dict = {}
        game_rows: list = []
        game_player_rows: list = []

        for game in games:
            game_rows.append(
                Game(
                    id=game["id"],
                    name=game["name"],
                    notes=game.get("notes"),
                    tags=game.get("tags"),
                    discord_server_url=game.get("discordServerUrl"),
                    discord_server_name=game.get("discordServerName"),
                    created_on=game["createdOn"],  # stored naively as-is, no TZ conversion
                    game_type=game.get("gameType"),
                    game_status=game.get("gameStatus"),
                    win_condition=game.get("winCondition"),
                    platform=game.get("platform"),
                    bracket=game.get("bracket"),
                    total_turns=game.get("totalTurns"),
                    game_time_in_minutes=game.get("gameTimeInMinutes"),
                    is_public=game.get("isPublic") or False,
                    key_cards=game.get("keyCards") or [],
                    custom_stats=game.get("customStats") or [],
                    turn_logs=game.get("turnLogs") or [],
                )
            )

            for entry in game.get("players") or []:
                commander_rows[entry["commander"]["id"]] = self._commander_to_model(entry["commander"])
                partner = entry.get("commanderPartner")
                if partner:
                    commander_rows[partner["id"]] = self._commander_to_model(partner)
                player_rows[entry["player"]["id"]] = self._player_to_model(entry["player"])

                game_player_rows.append(
                    GamePlayer(
                        id=entry["id"],
                        game_id=game["id"],  # NOT entry.get("gameId"), which is always the zero UUID in the export
                        player_id=entry["player"]["id"],
                        commander_id=entry["commander"]["id"],
                        commander_partner_id=partner["id"] if partner else None,
                        has_partners=entry.get("hasPartners") or False,
                        turn_order=entry.get("turnOrder"),
                        mulligans=entry.get("mulligans"),
                        is_winner=entry.get("isWinner") or False,
                    )
                )

        with transaction.atomic():
            Commander.objects.bulk_create(
                commander_rows.values(),
                update_conflicts=True,
                unique_fields=["id"],
                update_fields=[
                    "scryfall_id",
                    "name",
                    "colors",
                    "image_uri",
                    "image_uri_partner",
                    "edhrec_rank",
                    "cmc",
                    "mythic_rank",
                    "disabled",
                    "deck_id",
                    "deck_name",
                    "decklist_url",
                    "art_image_uri",
                    "art_image_uri_partner",
                    "updated_at",
                ],
            )
            Player.objects.bulk_create(
                player_rows.values(),
                update_conflicts=True,
                unique_fields=["id"],
                update_fields=[
                    "name",
                    "username",
                    "color",
                    "is_you",
                    "is_random",
                    "favorite",
                    "patron_tier",
                    "discord_user_id",
                    "friend_code",
                    "updated_at",
                ],
            )
            Game.objects.bulk_create(
                game_rows,
                update_conflicts=True,
                unique_fields=["id"],
                update_fields=[
                    "name",
                    "notes",
                    "tags",
                    "discord_server_url",
                    "discord_server_name",
                    "created_on",
                    "game_type",
                    "game_status",
                    "win_condition",
                    "platform",
                    "bracket",
                    "total_turns",
                    "game_time_in_minutes",
                    "is_public",
                    "key_cards",
                    "custom_stats",
                    "turn_logs",
                    "updated_at",
                ],
            )
            GamePlayer.objects.bulk_create(
                game_player_rows,
                update_conflicts=True,
                unique_fields=["id"],
                update_fields=[
                    "game_id",
                    "player_id",
                    "commander_id",
                    "commander_partner_id",
                    "has_partners",
                    "turn_order",
                    "mulligans",
                    "is_winner",
                    "updated_at",
                ],
            )

            merges_applied = 0
            for merge in merges:
                canonical = Player.objects.filter(pk=merge["canonicalId"]).first()
                if canonical is None:
                    self.stderr.write(f"Skipping merge: canonicalId {merge['canonicalId']} not found")
                    continue
                if canonical.merged_into_id:
                    raise CommandError(
                        f"player-merges.json: canonicalId {merge['canonicalId']} is itself an "
                        "alias (merge chains are not allowed)"
                    )
                alias = Player.objects.filter(pk=merge["aliasId"]).first()
                if alias is None:
                    self.stderr.write(f"Skipping merge: aliasId {merge['aliasId']} not found")
                    continue
                Player.objects.filter(pk=merge["aliasId"]).update(
                    merged_into_id=merge["canonicalId"], updated_at=timezone.now()
                )
                merges_applied += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Upserted: {len(game_rows)} games, {len(game_player_rows)} game_players, "
                f"{len(player_rows)} players, {len(commander_rows)} commanders, "
                f"{merges_applied} player merge(s) applied."
            )
        )

    @staticmethod
    def _commander_to_model(c: dict) -> Commander:
        return Commander(
            id=c["id"],
            scryfall_id=c.get("scryfallId"),
            name=c["name"],
            colors=c.get("colors"),
            image_uri=c.get("imageUri"),
            image_uri_partner=c.get("imageUriPartner"),
            edhrec_rank=c.get("edhrecRank"),
            cmc=c.get("cmc"),
            mythic_rank=c.get("mythicRank"),
            disabled=c.get("disabled") or False,
            deck_id=c.get("deckId"),
            deck_name=c.get("deckName"),
            decklist_url=c.get("decklistUrl"),
            art_image_uri=c.get("artImageUri"),
            art_image_uri_partner=c.get("artImageUriPartner"),
        )

    @staticmethod
    def _player_to_model(p: dict) -> Player:
        return Player(
            id=p["id"],
            name=(p.get("friendlyName") or p.get("name") or "").strip(),
            username=p.get("username"),
            color=p.get("color"),
            is_you=p.get("isYou") or False,
            is_random=p.get("isRandom") or False,
            favorite=p.get("favorite") or False,
            patron_tier=p.get("patronTier"),
            discord_user_id=p.get("discordUserId"),
            friend_code=p.get("friendCode"),
        )
