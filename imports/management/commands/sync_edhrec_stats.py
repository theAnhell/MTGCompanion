import requests
from django.core.management.base import BaseCommand

from commanders.models import Commander
from commanders.services import sync_commander_card_stats


class Command(BaseCommand):
    help = (
        "Sync cached EDHREC card-inclusion stats. By default only syncs "
        "commanders with at least one owned deck; use --all for every "
        "commander or --commander <id> for a single one."
    )

    def add_arguments(self, parser):
        parser.add_argument("--commander", help="Sync only this commander id")
        parser.add_argument("--all", action="store_true", help="Sync every commander, not just ones with owned decks")

    def handle(self, *args, **options):
        if options["commander"]:
            commanders = Commander.objects.filter(pk=options["commander"])
        elif options["all"]:
            commanders = Commander.objects.all()
        else:
            commanders = Commander.objects.filter(decks__isnull=False).distinct()

        if not commanders:
            self.stdout.write("No commanders to sync.")
            return

        for commander in commanders:
            try:
                count = sync_commander_card_stats(commander.id)
                self.stdout.write(f"Synced {commander.name}: {count} cards")
            except requests.HTTPError as e:
                self.stderr.write(f"Skipping {commander.name}: EDHREC fetch failed ({e})")
            except requests.RequestException as e:
                self.stderr.write(f"Skipping {commander.name}: request error ({e})")
