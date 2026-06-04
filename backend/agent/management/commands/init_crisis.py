from django.core.management.base import BaseCommand, CommandParser
from agent.safety.crisis_detector import (
    init_crisis_collection,
    populate_crisis_collection,
    _get_client,
    CRISIS_COLLECTION,
)


class Command(BaseCommand):
    help = "Initialize and populate the Qdrant crisis_knowledge collection"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "--recreate",
            "-r",
            action="store_true",
            default=False,
            help="Drop and recreate the collection before populating (deletes existing vectors)",
        )

    def handle(self, *args, **options):
        if options["recreate"]:
            self.stdout.write(self.style.WARNING(
                "Recreating collection — all existing vectors will be deleted."
            ))
            try:
                client = _get_client()
                if client.collection_exists(CRISIS_COLLECTION):
                    client.delete_collection(CRISIS_COLLECTION)
                    self.stdout.write(f"Deleted existing collection: {CRISIS_COLLECTION}")
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to delete collection: {e}"))
                return

        self.stdout.write("Initializing crisis collection...")
        init_crisis_collection()

        self.stdout.write("Populating crisis phrases...")
        populate_crisis_collection()

        self.stdout.write(self.style.SUCCESS("Crisis collection ready."))
