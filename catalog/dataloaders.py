"""
DataLoader implementations for fixing N+1 query problems.

This file is a starting scaffold for Exercise 03 (Advanced).
Learners will implement DataLoaders here to batch and cache
database queries in the GraphQL resolvers.

Example DataLoader pattern with Strawberry:

    from strawberry.dataloader import DataLoader

    async def load_authors(keys: list[int]) -> list[Author]:
        authors = Author.objects.filter(id__in=keys)
        author_map = {a.id: a for a in authors}
        return [author_map[k] for k in keys]

    author_loader = DataLoader(load_fn=load_authors)

See: https://strawberry.rocks/docs/guides/dataloaders
"""
