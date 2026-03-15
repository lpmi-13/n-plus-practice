# Exercise 02: Fix the Nested Category Query (Intermediate)

## The Problem

Run this query:

```graphql
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
```

Check the console. You'll see queries exploding at two levels:
1. One query per category to fetch its products
2. One query per product to fetch its variants

With 5 categories, 30 products, and 60+ variants, this produces **35+ queries**.

## Your Task

Fix the resolvers so this query uses at most **3 SQL queries**.

## Hints

1. `select_related` won't work here because `products` and `variants` are **reverse foreign key** relationships (one-to-many).
2. Look at Django's `prefetch_related()` — it executes a separate query for each relation and joins the results in Python.
3. You can nest prefetches: `prefetch_related("products", "products__variants")`.
4. You'll need to modify the root `categories` query in `catalog/schema.py`.
5. The tricky part: Strawberry resolvers access `self.products.all()`. After prefetching, this will use the cached result instead of hitting the database — **but only if the queryset was prefetched at the root level**.

## Check Your Work

```bash
docker compose exec web python manage.py check_queries categories_products_variants
```

Target: **<= 3 queries**

## Relevant Django Docs

- [prefetch_related](https://docs.djangoproject.com/en/5.1/ref/models/querysets/#prefetch-related)
- [Prefetch objects](https://docs.djangoproject.com/en/5.1/ref/models/querysets/#django.db.models.Prefetch)
