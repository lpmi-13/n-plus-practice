# N+1 Query Exercises

## Learning Path

Work through these exercises in order. Each builds on concepts from the previous one.

| Exercise | Difficulty | Skill | Target |
|----------|-----------|-------|--------|
| 01 | Basic | `select_related` | ~30 queries → 2 |
| 02 | Intermediate | `prefetch_related` | ~50 queries → 3 |
| 03 | Advanced | Strawberry DataLoaders | ~100 queries → 5 |

## How to Work

1. **Read the brief** in each exercise folder (`BRIEF.md`)
2. **Run the query** in the GraphiQL explorer at `http://localhost:8000/graphql`
3. **Watch the console** — SQL queries are logged to stdout
4. **Check your progress** with the validation harness:
   ```bash
   # Check a specific query
   docker compose exec web python manage.py check_queries products_with_category

   # Check all queries
   docker compose exec web python manage.py check_queries

   # Run the test suite
   docker compose exec web pytest
   ```
5. **Read the solution** only after you've attempted the fix

## Key Concepts

### What is an N+1 Query?

When you fetch a list of N items and then, for each item, execute an additional query to fetch related data, you end up with 1 + N queries instead of a constant number. This is the "N+1 problem."

### Django's Tools for Fixing N+1

- **`select_related(*fields)`** — Uses SQL JOINs to fetch FK/OneToOne relations in one query. Use for single-object relationships.
- **`prefetch_related(*fields)`** — Executes a separate query for the related set, then joins in Python. Use for reverse FK / M2M relationships.
- **`Prefetch(lookup, queryset)`** — Fine-grained control over prefetched querysets.

### GraphQL-Specific: DataLoaders

In GraphQL, resolvers run independently per field. Django's `select_related` / `prefetch_related` can't always help because the ORM queryset may already be evaluated. **DataLoaders** solve this by batching and caching lookups across resolvers within a single request.

See [Strawberry DataLoader docs](https://strawberry.rocks/docs/guides/dataloaders) for details.
