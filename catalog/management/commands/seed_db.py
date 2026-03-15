import random
from decimal import Decimal

from django.core.management.base import BaseCommand

from catalog.models import Author, Category, Product, Review, Variant

CATEGORIES = [
    ("Electronics", "Gadgets, devices, and accessories"),
    ("Clothing", "Apparel and fashion items"),
    ("Books", "Physical and digital books"),
    ("Home & Garden", "Furniture, decor, and garden supplies"),
    ("Sports", "Sports equipment and outdoor gear"),
]

AUTHORS = [
    ("Alice Johnson", "alice@example.com"),
    ("Bob Smith", "bob@example.com"),
    ("Carol Williams", "carol@example.com"),
    ("David Brown", "david@example.com"),
    ("Eva Martinez", "eva@example.com"),
    ("Frank Lee", "frank@example.com"),
    ("Grace Kim", "grace@example.com"),
    ("Henry Davis", "henry@example.com"),
    ("Irene Wilson", "irene@example.com"),
    ("Jack Taylor", "jack@example.com"),
]

PRODUCTS_BY_CATEGORY = {
    "Electronics": [
        "Wireless Headphones",
        "USB-C Hub",
        "Mechanical Keyboard",
        "Portable Charger",
        "Webcam HD",
        "Bluetooth Speaker",
    ],
    "Clothing": [
        "Cotton T-Shirt",
        "Denim Jeans",
        "Running Shoes",
        "Winter Jacket",
        "Baseball Cap",
        "Wool Socks",
    ],
    "Books": [
        "Python Cookbook",
        "Database Internals",
        "Clean Code",
        "Design Patterns",
        "The Pragmatic Programmer",
        "SQL Performance Explained",
    ],
    "Home & Garden": [
        "Desk Lamp",
        "Plant Pot Set",
        "Tool Kit",
        "Storage Bins",
        "Garden Hose",
        "Wall Clock",
    ],
    "Sports": [
        "Yoga Mat",
        "Resistance Bands",
        "Water Bottle",
        "Jump Rope",
        "Foam Roller",
        "Gym Bag",
    ],
}

SIZES = ["S", "M", "L", "XL"]
COLORS = ["Black", "White", "Blue", "Red", "Green", "Gray"]

REVIEW_TEXTS = [
    "Great product, exactly what I needed!",
    "Good quality but shipping was slow.",
    "Decent for the price. Would buy again.",
    "Not what I expected. The description was misleading.",
    "Absolutely love it! Highly recommend.",
    "Works well but could be better.",
    "Perfect gift for a friend.",
    "Broke after a week. Very disappointed.",
    "Best purchase I've made this year.",
    "Okay product, nothing special.",
    "Exceeded my expectations!",
    "The quality is outstanding for this price range.",
    "Would not recommend. Too many issues.",
    "Solid build quality and great design.",
    "Average product. Does what it says.",
]


class Command(BaseCommand):
    help = "Seed the database with sample data (idempotent: clears and recreates)"

    def handle(self, *args, **options):
        self.stdout.write("Clearing existing data...")
        Review.objects.all().delete()
        Variant.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Author.objects.all().delete()

        self.stdout.write("Creating authors...")
        authors = []
        for name, email in AUTHORS:
            authors.append(Author.objects.create(name=name, email=email))

        self.stdout.write("Creating categories and products...")
        sku_counter = 1000
        all_products = []

        for cat_name, cat_desc in CATEGORIES:
            category = Category.objects.create(name=cat_name, description=cat_desc)

            for product_name in PRODUCTS_BY_CATEGORY[cat_name]:
                product = Product.objects.create(
                    name=product_name,
                    description=f"A high-quality {product_name.lower()} in our {cat_name.lower()} collection.",
                    price=Decimal(f"{random.randint(999, 19999) / 100:.2f}"),
                    category=category,
                )
                all_products.append(product)

                # Create 2-3 variants per product
                num_variants = random.randint(2, 3)
                used_combos = set()
                for _ in range(num_variants):
                    while True:
                        size = random.choice(SIZES)
                        color = random.choice(COLORS)
                        if (size, color) not in used_combos:
                            used_combos.add((size, color))
                            break
                    sku_counter += 1
                    Variant.objects.create(
                        product=product,
                        size=size,
                        color=color,
                        sku=f"SKU-{sku_counter}",
                        stock=random.randint(0, 50),
                    )

        self.stdout.write("Creating reviews...")
        for product in all_products:
            num_reviews = random.randint(2, 5)
            reviewers = random.sample(authors, num_reviews)
            for author in reviewers:
                Review.objects.create(
                    product=product,
                    author=author,
                    rating=random.randint(1, 5),
                    text=random.choice(REVIEW_TEXTS),
                )

        total_products = Product.objects.count()
        total_variants = Variant.objects.count()
        total_reviews = Review.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded: {len(CATEGORIES)} categories, {total_products} products, "
                f"{total_variants} variants, {len(authors)} authors, {total_reviews} reviews"
            )
        )
