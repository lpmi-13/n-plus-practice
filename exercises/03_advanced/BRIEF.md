# Exercise 03: Fix the Full-Depth Query with DataLoaders (Advanced)

## The Problem

Run the full-depth query:

```graphql
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
```

This query fans out at **every level**: categories → products → reviews → authors, plus variants. The result is 50-100+ queries depending on the data.

Also try:

```graphql
{
  products {
    name
    averageRating
  }
}
```

This triggers N+1 because `average_rating` loads each product's reviews separately.

## Why prefetch_related Isn't Enough

You _could_ fix some of this with deeply nested `prefetch_related`, but in a GraphQL API:

- You don't know which fields the client will request
- Different queries need different prefetch strategies
- Resolvers run independently — the ORM queryset may already be evaluated

**DataLoaders** solve this by **batching** individual lookups. When multiple resolvers ask for related objects, the DataLoader collects all the IDs and executes **one** batched query.

## Your Task

1. Implement DataLoaders in `catalog/dataloaders.py`
2. Update the resolvers in `catalog/schema.py` to use the DataLoaders
3. Target: the full-depth query should use **<= 5 queries**

## Step-by-Step Guide

### 1. Create DataLoaders

In `catalog/dataloaders.py`, implement loaders for each relationship:

```python
from strawberry.dataloader import DataLoader
from catalog.models import Product, Variant, Review, Author

# Example: load products by category_id
async def load_products_by_category(keys: list[int]) -> list[list[Product]]:
    products = Product.objects.filter(category_id__in=keys)
    # Group by category_id
    grouped = {k: [] for k in keys}
    for p in products:
        grouped[p.category_id].append(p)
    return [grouped[k] for k in keys]
```

You'll need loaders for:
- Products by category ID
- Variants by product ID
- Reviews by product ID
- Authors by author ID

### 2. Add Context with DataLoaders

Strawberry DataLoaders work through the `Info` context. You'll need to set up a custom context that creates DataLoader instances per request.

### 3. Update Resolvers

Change each resolver to use `info.context.loaders.xyz.load(key)` instead of direct ORM access.

## Check Your Work

```bash
docker compose exec web python manage.py check_queries full_depth
docker compose exec web python manage.py check_queries average_rating
```

Targets:
- `full_depth`: **<= 5 queries**
- `average_rating`: **<= 2 queries**

## Relevant Docs

- [Strawberry DataLoaders](https://strawberry.rocks/docs/guides/dataloaders)
- [DataLoader pattern (explained)](https://github.com/graphql/dataloader)
