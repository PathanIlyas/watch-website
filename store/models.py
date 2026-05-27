from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    def __str__(self):
        return self.name

class Watch(models.Model):
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    description = models.TextField()
    features = models.TextField(help_text="Comma separated features")
    stock_quantity = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='watches')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @property
    def display_image_src(self):
        static_images = {
            'chronos-aureus-premium': 'premium_gold.png',
            'chronos-argentum-elite': 'premium_silver.png',
            'chronos-obsidian-stealth': 'premium_black.png',
            'chronos-heritage-gold': 'gold.png',
            'chronos-aviator-silver': 'silver.png',
            'chronos-phantom-black': 'black.png',
        }
        image_name = static_images.get(self.slug)
        from django.templatetags.static import static
        if image_name:
            return static(f'images/{image_name}')
        
        # Check database images
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary.image.url
        first = self.images.first()
        if first:
            return first.image.url
        
        # fallback
        return static('images/watch_logo_mark.png')

class WatchImage(models.Model):
    watch = models.ForeignKey(Watch, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='watches/')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.watch.name}"

class Review(models.Model):
    watch = models.ForeignKey(Watch, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=5)
    comment = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s review of {self.watch.name}"

class HomepageBanner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True, null=True)
    image = models.ImageField(upload_to='banners/')
    link = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"
