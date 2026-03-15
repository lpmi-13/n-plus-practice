# Solution: Exercise 02

## The Fix

In `catalog/schema.py`, modify the `categories` root query:

```python
@strawberry.field
def categories(self) -> list[CategoryType]:
    return models.Category.objects.prefetch_related(
        "products",
        "products__variants",
    ).all()
```

## Why This Works

`prefetch_related` executes **separate, efficient queries** for each relationship and caches the results:

```sql
-- Query 1: All categories
SELECT * FROM catalog_category

-- Query 2: All products for those categories
SELECT * FROM catalog_product WHERE category_id IN (1, 2, 3, 4, 5)

-- Query 3: All variants for those products
SELECT * FROM catalog_variant WHERE product_id IN (1, 2, 3, ..., 30)
```

When the resolvers call `self.products.all()` and `self.variants.all()`, Django returns the **cached prefetch results** instead of executing new queries.

## Why Not select_related?

`select_related` only works for **forward** ForeignKey and OneToOne relationships (many-to-one). Here, we're going from Category → Products (one-to-many), which is a **reverse** relationship. `prefetch_related` handles these by executing a second query with an `IN` clause.

## Result

- **Before:** 1 + 5 + 30 = 36 queries
- **After:** 3 queries (one per table)

## Key Takeaway

Use `prefetch_related()` for **reverse FK** and **ManyToMany** relationships. Use the double-underscore syntax (`"products__variants"`) to prefetch nested relations in a single call.
