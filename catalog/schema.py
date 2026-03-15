from decimal import Decimal
from typing import Optional

import strawberry
import strawberry.django
from strawberry import auto

from catalog import models


@strawberry.django.type(models.Author)
class AuthorType:
    id: auto
    name: auto
    email: auto


@strawberry.django.type(models.Review)
class ReviewType:
    id: auto
    rating: auto
    text: auto
    created_at: auto

    # N+1: Each review triggers a separate query to fetch its author
    @strawberry.field
    def author(self) -> AuthorType:
        return self.author


@strawberry.django.type(models.Variant)
class VariantType:
    id: auto
    size: auto
    color: auto
    sku: auto
    stock: auto


@strawberry.django.type(models.Product)
class ProductType:
    id: auto
    name: auto
    description: auto
    price: Decimal
    created_at: auto

    # N+1: Each product triggers a separate query to fetch its variants
    @strawberry.field
    def variants(self) -> list[VariantType]:
        return self.variants.all()

    # N+1: Each product triggers a separate query to fetch its reviews
    @strawberry.field
    def reviews(self) -> list[ReviewType]:
        return self.reviews.all()

    # N+1: Computes average by loading all reviews via Python
    @strawberry.field
    def average_rating(self) -> Optional[float]:
        reviews = list(self.reviews.all())
        if not reviews:
            return None
        return sum(r.rating for r in reviews) / len(reviews)

    # N+1: Each product triggers a separate query to fetch its category
    @strawberry.field
    def category(self) -> "CategoryType":
        return self.category


@strawberry.django.type(models.Category)
class CategoryType:
    id: auto
    name: auto
    description: auto

    # N+1: Each category triggers a separate query to fetch its products
    @strawberry.field
    def products(self) -> list[ProductType]:
        return self.products.all()


@strawberry.type
class Query:
    @strawberry.field
    def categories(self) -> list[CategoryType]:
        return models.Category.objects.all()

    @strawberry.field
    def products(self) -> list[ProductType]:
        return models.Product.objects.all()

    @strawberry.field
    def product(self, id: strawberry.ID) -> Optional[ProductType]:
        try:
            return models.Product.objects.get(pk=id)
        except models.Product.DoesNotExist:
            return None


schema = strawberry.Schema(query=Query)
