from contextlib import contextmanager
from decimal import Decimal

import pytest
from django.test.utils import CaptureQueriesContext
from django.db import connection

from catalog.models import Author, Category, Product, Review, Variant


@contextmanager
def query_counter():
    """Context manager that counts the number of SQL queries executed."""
    context = CaptureQueriesContext(connection)
    with context:
        yield context


@pytest.fixture
def count_queries():
    """Fixture that returns the query_counter context manager."""
    return query_counter


@pytest.fixture
def seeded_db(db):
    """Create a small but sufficient dataset for testing N+1 patterns."""
    authors = [
        Author.objects.create(name=f"Author {i}", email=f"author{i}@example.com")
        for i in range(5)
    ]

    categories = []
    for i in range(3):
        categories.append(
            Category.objects.create(name=f"Category {i}", description=f"Desc {i}")
        )

    products = []
    for cat in categories:
        for j in range(4):
            products.append(
                Product.objects.create(
                    name=f"{cat.name} Product {j}",
                    description=f"A product in {cat.name}",
                    price=Decimal("19.99"),
                    category=cat,
                )
            )

    for product in products:
        for k in range(2):
            Variant.objects.create(
                product=product,
                size=["S", "M", "L"][k % 3],
                color=["Red", "Blue"][k % 2],
                sku=f"SKU-{product.id}-{k}",
                stock=10,
            )

    import random

    for product in products:
        for author in random.sample(authors, 3):
            Review.objects.create(
                product=product,
                author=author,
                rating=random.randint(1, 5),
                text=f"Review by {author.name}",
            )

    return {
        "authors": authors,
        "categories": categories,
        "products": products,
    }


@pytest.fixture
def graphql_client():
    """Return a function that executes GraphQL queries against the schema."""
    from catalog.schema import schema

    def execute(query, variable_values=None):
        return schema.execute_sync(query, variable_values=variable_values)

    return execute
