from django.core.management.base import BaseCommand
from django.core.files.base import File
from django.conf import settings

from store.models import Category, Watch, WatchImage


WATCHES = [
    {
        "name": "Chronos Aureus Premium",
        "brand": "CHRONOS",
        "slug": "chronos-aureus-premium",
        "price": 32500.00,
        "description": "An ultra-premium 18k solid gold automatic luxury watch featuring a masterfully crafted skeleton dial.",
        "features": "18k Solid Gold, Automatic Movement, Skeleton Dial, Sapphire Crystal, 50m Water Resistance, Alligator Leather Strap",
        "stock_quantity": 10,
        "is_featured": True,
        "is_trending": True,
        "image_filename": "premium_gold.png",
    },
    {
        "name": "Chronos Argentum Elite",
        "brand": "CHRONOS",
        "slug": "chronos-argentum-elite",
        "price": 18200.00,
        "description": "A sophisticated stainless steel luxury chronograph with a mesmerizing sunburst blue dial.",
        "features": "Stainless Steel, Chronograph Complication, Sunburst Blue Dial, Tachymeter Bezel, 100m Water Resistance, Steel Bracelet",
        "stock_quantity": 10,
        "is_featured": True,
        "is_trending": True,
        "image_filename": "premium_silver.png",
    },
    {
        "name": "Chronos Obsidian Stealth",
        "brand": "CHRONOS",
        "slug": "chronos-obsidian-stealth",
        "price": 24000.00,
        "description": "A modern, stealthy matte black ceramic watch with striking crimson and gold accents.",
        "features": "Matte Black Ceramic, Automatic Movement, Luminous Hands, Scratch-Resistant, 100m Water Resistance, Rubber Strap",
        "stock_quantity": 10,
        "is_featured": True,
        "is_trending": True,
        "image_filename": "premium_black.png",
    },
    {
        "name": "Chronos Heritage Gold",
        "brand": "CHRONOS",
        "slug": "chronos-heritage-gold",
        "price": 28000.00,
        "description": "A classic take on luxury, crafted for formal occasions and collectors.",
        "features": "Rose Gold Plated, Quartz Movement, Date Window, Sapphire Crystal, 30m Water Resistance",
        "stock_quantity": 10,
        "is_featured": False,
        "is_trending": True,
        "image_filename": "gold.png",
    },
    {
        "name": "Chronos Aviator Silver",
        "brand": "CHRONOS",
        "slug": "chronos-aviator-silver",
        "price": 15500.00,
        "description": "Inspired by aviation history, with a highly legible dial and robust construction.",
        "features": "Aviation Grade Steel, Large Numerals, Anti-Reflective Coating, 100m Water Resistance",
        "stock_quantity": 10,
        "is_featured": False,
        "is_trending": True,
        "image_filename": "silver.png",
    },
    {
        "name": "Chronos Phantom Black",
        "brand": "CHRONOS",
        "slug": "chronos-phantom-black",
        "price": 21500.00,
        "description": "A sleek all-black minimalist profile for day-to-night wear.",
        "features": "PVD Coated Steel, Minimalist Dial, Stealth Look, 50m Water Resistance",
        "stock_quantity": 10,
        "is_featured": False,
        "is_trending": True,
        "image_filename": "black.png",
    },
]


class Command(BaseCommand):
    help = "Create or update the default CHRONOS watch collection."

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            slug="luxury-collection",
            defaults={
                "name": "Luxury Collection",
                "description": "Our most exquisite luxury timepieces.",
            },
        )

        for source_watch_data in WATCHES:
            watch_data = source_watch_data.copy()
            image_filename = watch_data.pop("image_filename")
            watch, _ = Watch.objects.update_or_create(
                slug=watch_data["slug"],
                defaults={**watch_data, "category": category},
            )

            image_path = settings.BASE_DIR / "static" / "images" / image_filename
            if image_path.exists():
                WatchImage.objects.filter(watch=watch).delete()
                with image_path.open("rb") as image_file:
                    WatchImage.objects.create(
                        watch=watch,
                        image=File(image_file, name=image_filename),
                        is_primary=True,
                    )

            self.stdout.write(self.style.SUCCESS(f"Seeded {watch.name}"))

        self.stdout.write(self.style.SUCCESS("Watch collection is ready."))
