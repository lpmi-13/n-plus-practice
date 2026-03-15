# Solution: Exercise 03

## Overview

This solution implements Strawberry DataLoaders to batch all database access. The key insight is that DataLoaders **collect individual load requests** and execute them as a single batched query.

## Step 1: Implement DataLoaders

Replace the contents of `catalog/dataloaders.py`:

```python
from collections import defaultdict

from strawberry.dataloader import DataLoader

from catalog.models import Author, Product, Review, Variant


async def load_products_by_category(keys: list[int]) -> list[list[Product]]:
    """Batch-load products grouped by category_id."""
    products = Product.objects.filter(category_id__in=keys).select_related("category")
    grouped = defaultdict(list)
    for product in products:
        grouped[product.category_id].append(product)
    return [grouped.get(key, []) for key in keys]


async def load_variants_by_product(keys: list[int]) -> list[list[Variant]]:
    """Batch-load variants grouped by product_id."""
    variants = Variant.objects.filter(product_id__in=keys)
    grouped = defaultdict(list)
    for variant in variants:
        grouped[variant.product_id].append(variant)
    return [grouped.get(key, []) for key in keys]


async def load_reviews_by_product(keys: list[int]) -> list[list[Review]]:
    """Batch-load reviews grouped by product_id."""
    reviews = Review.objects.filter(product_id__in=keys)
    grouped = defaultdict(list)
    for review in reviews:
        grouped[review.product_id].append(review)
    return [grouped.get(key, []) for key in keys]


async def load_authors(keys: list[int]) -> list[Author]:
    """Batch-load authors by ID."""
    authors = Author.objects.filter(id__in=keys)
    author_map = {a.id: a for a in authors}
    return [author_map[key] for key in keys]


class Loaders:
    """Container for all DataLoaders, created once per request."""

    def __init__(self):
        self.products_by_category = DataLoader(load_fn=load_products_by_category)
        self.variants_by_product = DataLoader(load_fn=load_variants_by_product)
        self.reviews_by_product = DataLoader(load_fn=load_reviews_by_product)
        self.authors = DataLoader(load_fn=load_authors)
```

## Step 2: Set Up Custom Context

In `catalog/schema.py`, add a context getter:

```python
from catalog.dataloaders import Loaders

async def get_context():
    return {"loaders": Loaders()}
```

Update `config/urls.py` to pass the context:

```python
from catalog.schema import schema
from catalog.dataloaders import Loaders
from strawberry.django.views import AsyncGraphQLView

async def get_context(request):
    return {"loaders": Loaders()}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("graphql", AsyncGraphQLView.as_view(schema=schema)),
]
```

## Step 3: Update Resolvers

```python
import strawberry
from strawberry.types import Info

@strawberry.django.type(models.Category)
class CategoryType:
    id: auto
    name: auto
    description: auto

    @strawberry.field
    async def products(self, info: Info) -> list[ProductType]:
        return await info.context["loaders"].products_by_category.load(self.id)


@strawberry.django.type(models.Product)
class ProductType:
    id: auto
    name: auto
    description: auto
    price: Decimal
    created_at: auto

    @strawberry.field
    async def variants(self, info: Info) -> list[VariantType]:
        return await info.context["loaders"].variants_by_product.load(self.id)

    @strawberry.field
    async def reviews(self, info: Info) -> list[ReviewType]:
        return await info.context["loaders"].reviews_by_product.load(self.id)

    @strawberry.field
    async def average_rating(self, info: Info) -> Optional[float]:
        reviews = await info.context["loaders"].reviews_by_product.load(self.id)
        if not reviews:
            return None
        return sum(r.rating for r in reviews) / len(reviews)

    @strawberry.field
    async def category(self) -> CategoryType:
        return self.category  # Already loaded via select_related in the DataLoader


@strawberry.django.type(models.Review)
class ReviewType:
    id: auto
    rating: auto
    text: auto
    created_at: auto

    @strawberry.field
    async def author(self, info: Info) -> AuthorType:
        return await info.context["loaders"].authors.load(self.author_id)
```

## Why This Works

Without DataLoaders, each resolver independently hits the database:
```
resolve category.products → SELECT * FROM product WHERE category_id = 1
resolve category.products → SELECT * FROM product WHERE category_id = 2
resolve category.products → SELECT * FROM product WHERE category_id = 3
```

With DataLoaders, these calls are **batched** within the same event loop tick:
```
DataLoader collects keys [1, 2, 3]
→ SELECT * FROM product WHERE category_id IN (1, 2, 3)
```

## Result

- **Before:** 50-100+ queries
- **After:** 5 queries (categories, products, variants, reviews, authors)

## Key Takeaway

DataLoaders are essential for GraphQL APIs. They solve the fundamental tension between GraphQL's field-level resolution and efficient database access. The batching happens automatically — you just call `.load(key)` and the DataLoader handles the rest.
