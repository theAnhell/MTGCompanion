from django.core.management.base import BaseCommand

from cards.services import sync_scryfall_cards


class Command(BaseCommand):
    help = "Sync the local Card table from Scryfall's live Oracle Cards bulk data."

    def handle(self, *args, **options):
        self.stdout.write("Fetching Scryfall bulk-data index and Oracle Cards payload…")
        count = sync_scryfall_cards()
        self.stdout.write(self.style.SUCCESS(f"Synced {count} cards."))
