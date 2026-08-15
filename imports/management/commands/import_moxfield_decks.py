import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from commanders.models import Commander
from decks.models import Deck
from decks.services import replace_deck_cards
from imports.moxfield_parser import extract_moxfield_deck_id, is_commander_card, parse_moxfield_export
from players.models import Player


class Command(BaseCommand):
    help = "Sync decks/deck_cards from Moxfield plain-text exports, per data/moxfield-decks.json."

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

            owner = Player.objects.filter(pk=entry["playerId"]).first()
            if owner is None:
                self.stderr.write(f"Skipping {commander.name}: playerId {entry['playerId']} not found in players table")
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
                    "is_commander": is_commander_card(card["cardName"], commander.name),
                }
                for card in parsed
            ]

            if not any(r["is_commander"] for r in rows):
                self.stderr.write(
                    f"Warning: no card in {commander.name}'s export matched the commander name "
                    f'"{commander.name}" — is_commander will be false for all rows'
                )

            moxfield_deck_id = extract_moxfield_deck_id(entry["moxfieldUrl"])
            if moxfield_deck_id is None:
                raise ValueError(f"Could not extract a deck id from Moxfield URL: {entry['moxfieldUrl']}")

            with transaction.atomic():
                deck, _ = Deck.objects.get_or_create(
                    owner=owner,
                    commander=commander,
                    defaults={"source": "moxfield"},
                )
                deck.source = "moxfield"
                deck.moxfield_deck_id = moxfield_deck_id
                deck.moxfield_url = entry["moxfieldUrl"]
                deck.save(update_fields=["source", "moxfield_deck_id", "moxfield_url", "updated_at"])
                replace_deck_cards(deck.id, rows)

            self.stdout.write(f"Synced {owner.name}'s {commander.name}: {len(rows)} cards from {entry['moxfieldUrl']}")
