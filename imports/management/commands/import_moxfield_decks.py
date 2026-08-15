import json
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from commanders.models import Commander
from decks.services import replace_deck_cards
from imports.moxfield_parser import normalize_card_name, parse_moxfield_export


class Command(BaseCommand):
    help = "Sync deck_cards from Moxfield plain-text exports, per config/moxfield-decks.json."

    def handle(self, *args, **options):
        config_path = Path(settings.MOXFIELD_DECKS_CONFIG_PATH)
        entries = json.loads(config_path.read_text()) if config_path.exists() else []
        if not entries:
            self.stdout.write("No entries in moxfield-decks.json, nothing to import.")
            return

        config_dir = config_path.parent

        for entry in entries:
            commander = Commander.objects.filter(pk=entry["commanderId"]).first()
            if commander is None:
                self.stderr.write(
                    f"Skipping {entry.get('commanderName', entry['commanderId'])}: "
                    "commanderId not found in commanders table"
                )
                continue

            export_path = (config_dir / entry["exportFile"]).resolve()
            if not export_path.exists():
                self.stderr.write(f"Skipping {commander.name}: export file not found at {export_path}")
                continue

            parsed = parse_moxfield_export(export_path.read_text())

            rows = [
                {
                    "card_name": card["cardName"],
                    "set_code": card["setCode"],
                    "collector_number": card["collectorNumber"],
                    "quantity": card["quantity"],
                    "is_foil": card["isFoil"],
                    "is_commander": self._is_commander_card(card["cardName"], commander.name),
                }
                for card in parsed
            ]

            if not any(r["is_commander"] for r in rows):
                self.stderr.write(
                    f"Warning: no card in {commander.name}'s export matched the commander name "
                    f'"{commander.name}" — is_commander will be false for all rows'
                )

            deck_id = self._extract_moxfield_deck_id(entry["moxfieldUrl"])

            with transaction.atomic():
                replace_deck_cards(commander.id, rows)
                commander.deck_id = deck_id
                commander.decklist_url = entry["moxfieldUrl"]
                commander.save(update_fields=["deck_id", "decklist_url", "updated_at"])

            self.stdout.write(f"Synced {commander.name}: {len(rows)} cards from {entry['moxfieldUrl']}")

    @staticmethod
    def _extract_moxfield_deck_id(url: str) -> str:
        match = re.search(r"/decks/([^/?#]+)", url)
        if not match:
            raise ValueError(f"Could not extract a deck id from Moxfield URL: {url}")
        return match.group(1)

    @staticmethod
    def _is_commander_card(card_name: str, commander_name: str) -> bool:
        """A card is the commander if its (normalized) name matches the commander's
        own name, front-face-only for split/MDFC cards."""
        normalized_card = normalize_card_name(card_name).lower()
        normalized_commander = commander_name.strip().lower()
        if normalized_card == normalized_commander:
            return True
        front_face = normalized_card.split(" // ")[0]
        return front_face == normalized_commander
