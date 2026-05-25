import os
import sys
import django
from django.core.files import File
import shutil

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from store.models import Watch, Category, WatchImage
from django.conf import settings

def run():
    # Ensure a category exists
    cat, created = Category.objects.get_or_create(
        name="Luxury Collection",
        slug="luxury-collection",
        defaults={'description': "Our most exquisite luxury timepieces."}
    )

    watches_data = [
        {
            "name": "Chronos Aureus Premium",
            "brand": "CHRONOS",
            "slug": "chronos-aureus-premium",
            "price": 32500.00,
            "description": "An ultra-premium 18k solid gold automatic luxury watch featuring a masterfully crafted skeleton dial. Designed for those who appreciate the finest horology, this masterpiece reveals the intricate mechanical heart beating within a flawless gold casing.",
            "features": "18k Solid Gold, Automatic Movement, Skeleton Dial, Sapphire Crystal, 50m Water Resistance, Alligator Leather Strap",
            "stock_quantity": 10,
            "is_featured": True,
            "is_trending": True,
            "image_filename": "premium_gold.png"
        },
        {
            "name": "Chronos Argentum Elite",
            "brand": "CHRONOS",
            "slug": "chronos-argentum-elite",
            "price": 18200.00,
            "description": "A sophisticated stainless steel luxury chronograph with a mesmerizing sunburst blue dial. This timepiece perfectly balances sporty elegance with professional precision. The crisp polished metal and deep blue create a stunning visual contrast for any occasion.",
            "features": "Stainless Steel, Chronograph Complication, Sunburst Blue Dial, Tachymeter Bezel, 100m Water Resistance, Steel Bracelet",
            "stock_quantity": 10,
            "is_featured": True,
            "is_trending": True,
            "image_filename": "premium_silver.png"
        },
        {
            "name": "Chronos Obsidian Stealth",
            "brand": "CHRONOS",
            "slug": "chronos-obsidian-stealth",
            "price": 24000.00,
            "description": "A modern, stealthy matte black ceramic watch with striking crimson and gold accents. Engineered for the avant-garde collector, its lightweight yet virtually scratch-proof ceramic body houses an incredibly precise automatic movement.",
            "features": "Matte Black Ceramic, Automatic Movement, Luminous Hands, Scratch-Resistant, 100m Water Resistance, Rubber Strap",
            "stock_quantity": 10,
            "is_featured": True,
            "is_trending": True,
            "image_filename": "premium_black.png"
        },
        {
            "name": "Chronos Heritage Gold",
            "brand": "CHRONOS",
            "slug": "chronos-heritage-gold",
            "price": 28000.00,
            "description": "A classic take on luxury, the Heritage Gold is crafted for the traditionalist. The warm gold tones pair perfectly with formal attire, ensuring a commanding presence in any boardroom.",
            "features": "Rose Gold Plated, Quartz Movement, Date Window, Sapphire Crystal, 30m Water Resistance",
            "stock_quantity": 10,
            "is_featured": False,
            "is_trending": True,
            "image_filename": "gold.png"
        },
        {
            "name": "Chronos Aviator Silver",
            "brand": "CHRONOS",
            "slug": "chronos-aviator-silver",
            "price": 15500.00,
            "description": "Inspired by aviation history, this silver timepiece features a highly legible dial and robust construction. A reliable companion for the modern adventurer who demands style and durability.",
            "features": "Aviation Grade Steel, Large Numerals, Anti-Reflective Coating, 100m Water Resistance",
            "stock_quantity": 10,
            "is_featured": False,
            "is_trending": True,
            "image_filename": "silver.png"
        },
        {
            "name": "Chronos Phantom Black",
            "brand": "CHRONOS",
            "slug": "chronos-phantom-black",
            "price": 21500.00,
            "description": "The Phantom Black embraces minimalist design. Its sleek, all-black profile offers a sophisticated edge that seamlessly transitions from day to night.",
            "features": "PVD Coated Steel, Minimalist Dial, Stealth Look, 50m Water Resistance",
            "stock_quantity": 10,
            "is_featured": False,
            "is_trending": True,
            "image_filename": "black.png"
        }
    ]

    static_images_dir = os.path.join(settings.BASE_DIR, 'static', 'images')
    
    # Ensure media directory exists
    media_watches_dir = os.path.join(settings.MEDIA_ROOT, 'watches')
    os.makedirs(media_watches_dir, exist_ok=True)

    for data in watches_data:
        image_filename = data.pop('image_filename')
        
        # Check if watch already exists
        watch, created = Watch.objects.update_or_create(
            slug=data['slug'],
            defaults={
                'name': data['name'],
                'brand': data['brand'],
                'price': data['price'],
                'description': data['description'],
                'features': data['features'],
                'stock_quantity': data['stock_quantity'],
                'category': cat,
                'is_featured': data['is_featured'],
                'is_trending': data['is_trending'],
            }
        )
        
        # Add image if it exists in static folder
        source_img_path = os.path.join(static_images_dir, image_filename)
        if os.path.exists(source_img_path):
            # We must open it as a Django File to save it to an ImageField properly,
            # or just copy it to media and set the relative path.
            # Let's just create a WatchImage instance.
            
            # Clear old images
            WatchImage.objects.filter(watch=watch).delete()
            
            # Since we are just copying from static to media
            dest_img_path = os.path.join(media_watches_dir, image_filename)
            shutil.copy(source_img_path, dest_img_path)
            
            WatchImage.objects.create(
                watch=watch,
                image=f'watches/{image_filename}',
                is_primary=True
            )
            print(f"Added {watch.name} with image {image_filename}")
        else:
            print(f"Added {watch.name} without image (image not found: {source_img_path})")

    print("All premium watches have been successfully added/updated in the database!")

if __name__ == '__main__':
    run()
