# Exercise 01: Fix the Product Listing (Basic)

## The Problem

Run this query in the GraphiQL explorer at `http://localhost:8000/graphql`:

```graphql
{
  products {
    name
    price
    category {
      name
    }
  }
}
```

Now look at the console output. You'll see something like:

```
SELECT * FROM catalog_product                           -- 1 query
SELECT * FROM catalog_category WHERE id = 1             -- +1
SELECT * FROM catalog_category WHERE id = 2             -- +1
SELECT * FROM catalog_category WHERE id = 3             -- +1
... (one per product)
```

With 30 products, that's **31 queries** instead of **1-2**.

## Your Task

Fix the resolver so that fetching products with their category uses at most **2 SQL queries**.

## Hints

1. The issue is that each `ProductType.category` resolver accesses `self.category`, which triggers a lazy FK load.
2. Look at Django's `select_related()` — it uses SQL JOINs to fetch related objects in the same query.
3. You'll need to modify the root `products` query in `catalog/schema.py` to use `select_related("category")` on the queryset.

## Check Your Work

```bash
docker compose exec web python manage.py check_queries products_with_category
```

Target: **<= 2 queries**

## Relevant Django Docs

- [select_related](https://docs.djangoproject.com/en/5.1/ref/models/querysets/#select-related)
