from django.contrib import admin

from .models import Author, Category, Product, Review, Variant

admin.site.register(Category)
admin.site.register(Author)
admin.site.register(Product)
admin.site.register(Variant)
admin.site.register(Review)
