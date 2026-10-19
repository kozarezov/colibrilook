"""Curated content, not a blind feed import. Re-running preserves editorial changes."""
import json
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from boutique.models import Category, Product, ProductImage, Look, Store, SiteSettings

class Command(BaseCommand):
    help = "Добавить проверенные материалы Colibri. Существующие записи не изменяются."

    @transaction.atomic
    def handle(self, *args, **options):
        data = json.loads((Path(settings.BASE_DIR) / "content/catalog.json").read_text())
        categories = {}
        for order, (slug, name) in enumerate(data["categories"]):
            categories[slug], _ = Category.objects.get_or_create(slug=slug, defaults={"name": name, "order": order})
        products = {}
        for order, record in enumerate(data["products"]):
            row = record.copy()
            slug, photos = row.pop("slug"), row.pop("photos")
            row["category"] = categories[row["category"]]
            row.update(order=order, is_published=True, image_alt=row["name"] + " — Colibri LOOK")
            product, created = Product.objects.get_or_create(slug=slug, defaults=row)
            products[slug] = product
            if created:
                for index, photo in enumerate(photos):
                    ProductImage.objects.create(product=product, seed_image=photo, image_alt=product.name, order=index)
        for order, record in enumerate(data["looks"]):
            row = record.copy()
            slug, items = row.pop("slug"), row.pop("products")
            row.update(order=order, is_published=True, image_alt=row["title"] + " — Colibri LOOK")
            look, created = Look.objects.get_or_create(slug=slug, defaults=row)
            if created:
                look.products.set([products[slug] for slug in items])
        for record in data["stores"]:
            row = record.copy()
            telegram = row.pop("telegram")
            Store.objects.get_or_create(telegram=telegram, defaults=row)
        if not SiteSettings.objects.exists():
            SiteSettings.objects.create(**data["settings"])
        self.stdout.write(self.style.SUCCESS("Материалы добавлены. Существующие правки сохранены."))
