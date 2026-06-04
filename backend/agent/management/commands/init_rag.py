from django.core.management.base import BaseCommand, CommandParser
from agent.tools.rag.embeddings import ingest_sources_to_qdrant


class Command(BaseCommand):
    help = "Ingest knowledge sources (PDFs, URLs) into the Qdrant RAG collection"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "--recreate",
            "-r",
            action="store_true",
            default=False,
            help="Drop and recreate the collection before ingesting (deletes existing vectors)",
        )

    def handle(self, *args, **options):
        recreate = options["recreate"]
        try:
            if recreate:
                self.stdout.write(self.style.WARNING("Recreating collection — all existing vectors will be deleted."))
                ingest_sources_to_qdrant(recreate=recreate)

            else:
                self.stdout.write("Ingesting into existing collection (use --recreate to start fresh)...")
                ingest_sources_to_qdrant()
            
            self.stdout.write(self.style.SUCCESS("RAG knowledge base ready."))
        except ValueError as e:
            self.stderr.write(self.style.ERROR(f"Ingestion failed: {e}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Unexpected error: {e}"))
