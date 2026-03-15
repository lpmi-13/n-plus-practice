import datetime
from decimal import Decimal
from typing import Optional

import strawberry
from strawberry import Private

from catalog import models


@strawberry.type
class AuthorType:
    id: strawberry.ID
    name: str
    email: str


@strawberry.type
class ReviewType:
    id: strawberry.ID
    rating: int
    text: str
    created_at: datetime.datetime
    _author: Private[object]  # Django Author instance, not exposed in schema

    # N+1: Each review triggers a separate query to fetch its author
    @strawberry.field
    def author(self) -> AuthorType:
        author = self._author
        return AuthorType(id=author.id, name=author.name, email=author.email)


@strawberry.type
class VariantType:
    id: strawberry.ID
    size: str
    color: str
    sku: str
    stock: int


@strawberry.type
class ProductType:
    id: strawberry.ID
    name: str
    description: str
    price: Decimal
    created_at: datetime.datetime
    _product: Private[object]  # Django Product instance, not exposed in schema

    # N+1: Each product triggers a separate query to fetch its variants
    @strawberry.field
    def variants(self) -> list[VariantType]:
        return [
            VariantType(
                id=v.id, size=v.size, color=v.color, sku=v.sku, stock=v.stock
            )
            for v in self._product.variants.all()
        ]

    # N+1: Each product triggers a separate query to fetch its reviews
    @strawberry.field
    def reviews(self) -> list[ReviewType]:
        return [
            ReviewType(
                id=r.id,
                rating=r.rating,
                text=r.text,
                created_at=r.created_at,
                _author=r.author,
            )
            for r in self._product.reviews.all()
        ]

    # N+1: Computes average by loading all reviews via Python
    @strawberry.field
    def average_rating(self) -> Optional[float]:
        reviews = list(self._product.reviews.all())
        if not reviews:
            return None
        return sum(r.rating for r in reviews) / len(reviews)

    # N+1: Each product triggers a separate query to fetch its category
    @strawberry.field
    def category(self) -> "CategoryType":
        cat = self._product.category
        return CategoryType(
            id=cat.id, name=cat.name, description=cat.description, _category=cat
        )


@strawberry.type
class CategoryType:
    id: strawberry.ID
    name: str
    description: str
    _category: Private[object]  # Django Category instance, not exposed in schema

    # N+1: Each category triggers a separate query to fetch its products
    @strawberry.field
    def products(self) -> list[ProductType]:
        return [_product_to_type(p) for p in self._category.products.all()]


def _product_to_type(p: models.Product) -> ProductType:
    """Convert a Django Product model instance to a ProductType."""
    return ProductType(
        id=p.id,
        name=p.name,
        description=p.description,
        price=p.price,
        created_at=p.created_at,
        _product=p,
    )


@strawberry.type
class Query:
    @strawberry.field
    def categories(self) -> list[CategoryType]:
        return [
            CategoryType(
                id=c.id, name=c.name, description=c.description, _category=c
            )
            for c in models.Category.objects.all()
        ]

    @strawberry.field
    def products(self) -> list[ProductType]:
        return [_product_to_type(p) for p in models.Product.objects.all()]

    @strawberry.field
    def product(self, id: strawberry.ID) -> Optional[ProductType]:
        try:
            p = models.Product.objects.get(pk=id)
            return _product_to_type(p)
        except models.Product.DoesNotExist:
            return None


schema = strawberry.Schema(query=Query)
