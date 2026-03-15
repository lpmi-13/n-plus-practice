# Solution: Exercise 01

## The Fix

In `catalog/schema.py`, modify the `products` root query to use `select_related`:

```python
@strawberry.field
def products(self) -> list[ProductType]:
    return models.Product.objects.select_related("category").all()
```

## Why This Works

`select_related("category")` tells Django to use a SQL JOIN to fetch each product's category in the **same query**:

```sql
SELECT catalog_product.*, catalog_category.*
FROM catalog_product
INNER JOIN catalog_category ON (catalog_product.category_id = catalog_category.id)
```

Now when Strawberry's `ProductType.category` resolver accesses `self.category`, the data is already loaded — no additional query is needed.

## Result

- **Before:** 1 + N queries (31 with 30 products)
- **After:** 1 query (the JOIN handles everything)

## Key Takeaway

Use `select_related()` for **ForeignKey** and **OneToOneField** relationships. It's the simplest and most effective tool for fixing N+1 on single-valued relations.
