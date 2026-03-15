"""
Query count validation harness.

These tests verify the current (broken) query counts for various GraphQL queries.
Each test includes a commented-out GOAL assertion showing the target query count
after fixing the N+1 problems.

Workflow:
1. Run `pytest` — all tests should pass (they assert the CURRENT broken counts)
2. Work through the exercises to fix N+1 problems
3. Un-comment the GOAL assertions and update/remove the "broken" assertions
4. Run `pytest` again — tests should pass with the lower query counts
"""

import pytest


class TestBasicQueryCounts:
    """Exercise 01: Basic — Fix product listing with select_related."""

    def test_products_with_category(self, seeded_db, graphql_client, count_queries):
        """Listing products and accessing their category triggers N+1."""
        query = """
        {
            products {
                name
                price
                category {
                    name
                }
            }
        }
        """
        with count_queries() as ctx:
            result = graphql_client(query)

        assert result.errors is None
        num_queries = len(ctx.captured_queries)

        # BROKEN: 1 query for products + 1 per product for category
        assert num_queries > 5, f"Expected N+1 pattern, got {num_queries} queries"

        # GOAL: assert num_queries <= 2  # 1 query with select_related


class TestIntermediateQueryCounts:
    """Exercise 02: Intermediate — Fix nested prefetching."""

    def test_categories_with_products_and_variants(
        self, seeded_db, graphql_client, count_queries
    ):
        """Fetching categories → products → variants triggers nested N+1."""
        query = """
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
        """
        with count_queries() as ctx:
            result = graphql_client(query)

        assert result.errors is None
        num_queries = len(ctx.captured_queries)

        # BROKEN: 1 (categories) + N (products per cat) + N*M (variants per product)
        assert num_queries > 10, f"Expected N+1 pattern, got {num_queries} queries"

        # GOAL: assert num_queries <= 3  # categories + products + variants


class TestAdvancedQueryCounts:
    """Exercise 03: Advanced — Fix deep nested query with DataLoaders."""

    def test_categories_full_depth(self, seeded_db, graphql_client, count_queries):
        """The full-depth query triggers severe N+1 at every level."""
        query = """
        {
            categories {
                name
                products {
                    name
                    reviews {
                        text
                        rating
                        author {
                            name
                        }
                    }
                    variants {
                        size
                        color
                    }
                }
            }
        }
        """
        with count_queries() as ctx:
            result = graphql_client(query)

        assert result.errors is None
        num_queries = len(ctx.captured_queries)

        # BROKEN: explodes to many queries across all levels
        assert num_queries > 20, f"Expected severe N+1 pattern, got {num_queries} queries"

        # GOAL: assert num_queries <= 5  # With DataLoaders batching all levels

    def test_product_average_rating(self, seeded_db, graphql_client, count_queries):
        """Computing average_rating triggers extra queries per product."""
        query = """
        {
            products {
                name
                averageRating
            }
        }
        """
        with count_queries() as ctx:
            result = graphql_client(query)

        assert result.errors is None
        num_queries = len(ctx.captured_queries)

        # BROKEN: 1 query for products + 1 per product for reviews
        assert num_queries > 5, f"Expected N+1 pattern, got {num_queries} queries"

        # GOAL: assert num_queries <= 2  # Annotated or DataLoader-based
