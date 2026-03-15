from django.core.management.base import BaseCommand
from django.db import connection
from django.test.utils import CaptureQueriesContext

from catalog.schema import schema

QUERIES = {
    "products_with_category": {
        "query": """
        {
            products {
                name
                price
                category { name }
            }
        }
        """,
        "target": 2,
        "exercise": "01 (Basic)",
    },
    "categories_products_variants": {
        "query": """
        {
            categories {
                name
                products {
                    name
                    variants {
                        size
                        color
                        stock
                    }
                }
            }
        }
        """,
        "target": 3,
        "exercise": "02 (Intermediate)",
    },
    "full_depth": {
        "query": """
        {
            categories {
                name
                products {
                    name
                    reviews {
                        text
                        rating
                        author { name }
                    }
                    variants {
                        size
                        color
                    }
                }
            }
        }
        """,
        "target": 5,
        "exercise": "03 (Advanced)",
    },
    "average_rating": {
        "query": """
        {
            products {
                name
                averageRating
            }
        }
        """,
        "target": 2,
        "exercise": "03 (Advanced)",
    },
}


class Command(BaseCommand):
    help = "Run a named GraphQL query and report the SQL query count vs target"

    def add_arguments(self, parser):
        parser.add_argument(
            "query_name",
            nargs="?",
            default=None,
            help=f"Query to run. Options: {', '.join(QUERIES.keys())}. Omit to run all.",
        )

    def handle(self, *args, **options):
        query_name = options["query_name"]

        if query_name and query_name not in QUERIES:
            self.stderr.write(
                f"Unknown query: {query_name}\n"
                f"Available: {', '.join(QUERIES.keys())}"
            )
            return

        queries_to_run = (
            {query_name: QUERIES[query_name]} if query_name else QUERIES
        )

        self.stdout.write("")
        for name, config in queries_to_run.items():
            ctx = CaptureQueriesContext(connection)
            with ctx:
                result = schema.execute_sync(config["query"])

            count = len(ctx.captured_queries)
            target = config["target"]
            exercise = config["exercise"]

            if result.errors:
                self.stderr.write(f"  {name}: ERROR — {result.errors}")
                continue

            status = self.style.SUCCESS("PASS") if count <= target else self.style.ERROR("NEEDS FIX")
            self.stdout.write(
                f"  [{status}] {name}\n"
                f"         Exercise:  {exercise}\n"
                f"         Queries:   {count} (target: <= {target})\n"
            )
