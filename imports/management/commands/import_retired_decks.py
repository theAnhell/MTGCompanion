import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from commanders.models import Commander
from decks.models import RetiredDeck
from players.services import resolve_canonical_player


class Command(BaseCommand):
    help = "Import retired decks from the legacy global/per-player JSON files."

    def handle(self, *args, **options):
        by_player: dict = {}

        global_path = Path(settings.RETIRED_GLOBAL_PATH)
        if global_path.exists():
            data = json.loads(global_path.read_text())
            for player_name, deck_names in (data.get("players") or {}).items():
                self._add_decks(by_player, player_name, deck_names or [], "global-json")

        retired_dir = Path(settings.RETIRED_DIR_PATH)
        if retired_dir.exists():
            for file in sorted(retired_dir.iterdir()):
                if file.suffix != ".json":
                    continue
                data = json.loads(file.read_text())
                player_name = data.get("player")
                if not player_name:
                    continue
                self._add_decks(by_player, player_name, data.get("retired") or [], "per-player-json")

        rows_to_insert = []
        warnings = []

        for entry in by_player.values():
            player_name = entry["originalName"]
            player = resolve_canonical_player(player_name)
            if player is None:
                warnings.append(f'Unresolved player "{player_name}" — {len(entry["decks"])} deck(s) skipped')
                continue
            for deck_name, source in entry["decks"].values():
                commander = Commander.objects.filter(name__iexact=deck_name.strip()).first()
                if commander is None:
                    warnings.append(f'Unresolved deck "{deck_name}" for player "{player_name}"')
                    continue
                rows_to_insert.append({"player_id": player.id, "commander_id": commander.id, "source": source})

        if rows_to_insert:
            RetiredDeck.objects.bulk_create([RetiredDeck(**row) for row in rows_to_insert], ignore_conflicts=True)

        self.stdout.write(
            self.style.SUCCESS(f"Inserted (or already present): {len(rows_to_insert)} retired-deck pairs.")
        )
        if warnings:
            self.stdout.write(f"\nWarnings ({len(warnings)}) — review manually, nothing was guessed:")
            for w in warnings:
                self.stdout.write(f"  - {w}")

    @staticmethod
    def _add_decks(by_player: dict, player_name: str, deck_names: list, source: str) -> None:
        key = player_name.strip().lower()
        entry = by_player.setdefault(key, {"originalName": player_name, "decks": {}})
        for deck_name in deck_names:
            deck_key = deck_name.strip().lower()
            entry["decks"].setdefault(deck_key, (deck_name, source))
