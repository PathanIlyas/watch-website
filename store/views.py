from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Prefetch
from django.core.paginator import Paginator
from django.templatetags.static import static
from .models import Watch, WatchImage, Category, HomepageBanner, ContactMessage
from orders.emails import send_contact_confirmation, send_contact_admin_notification


STATIC_WATCH_IMAGES = {
    'chronos-aureus-premium': 'premium_gold.png',
    'chronos-argentum-elite': 'premium_silver.png',
    'chronos-obsidian-stealth': 'premium_black.png',
    'chronos-heritage-gold': 'gold.png',
    'chronos-aviator-silver': 'silver.png',
    'chronos-phantom-black': 'black.png',
}


def attach_display_images(watches):
    for watch in watches:
        image_name = STATIC_WATCH_IMAGES.get(watch.slug)
        if image_name:
            watch.display_image_src = static(f'images/{image_name}')
            # Set static_url for all individual images/thumbnails of static-seeded watches
            for img in getattr(watch, 'display_images', []):
                img.static_url = static(f'images/{image_name}')
            try:
                for img in watch.images.all():
                    img.static_url = static(f'images/{image_name}')
            except Exception:
                pass
            continue

        images = getattr(watch, 'display_images', [])
        image = images[0] if images else None
        watch.display_image_src = image.image.url if image else static('images/black.png')
    return watches


def home(request):
    display_image_prefetch = Prefetch(
        'images',
        queryset=WatchImage.objects.order_by('-is_primary', 'id'),
        to_attr='display_images',
    )
    featured_watches = attach_display_images(
        list(Watch.objects.filter(is_featured=True).prefetch_related(display_image_prefetch)[:4])
    )
    trending_watches = attach_display_images(
        list(Watch.objects.filter(is_trending=True).prefetch_related(display_image_prefetch)[:4])
    )
    banners = HomepageBanner.objects.filter(is_active=True)
    return render(request, 'index.html', {
        'featured_watches': featured_watches,
        'trending_watches': trending_watches,
        'banners': banners,
    })


def collection(request):
    display_image_prefetch = Prefetch(
        'images',
        queryset=WatchImage.objects.order_by('-is_primary', 'id'),
        to_attr='display_images',
    )
    watches_queryset = Watch.objects.all().order_by('-created_date').prefetch_related(display_image_prefetch)
    paginator = Paginator(watches_queryset, 6)
    page_obj = paginator.get_page(request.GET.get('page'))
    watches = attach_display_images(list(page_obj.object_list))
    categories = Category.objects.all()
    return render(request, 'collection.html', {
        'watches': watches,
        'categories': categories,
        'page_obj': page_obj,
        'paginator': paginator,
    })


def product(request, slug):
    display_image_prefetch = Prefetch(
        'images',
        queryset=WatchImage.objects.order_by('-is_primary', 'id'),
        to_attr='display_images',
    )
    watch = get_object_or_404(Watch.objects.prefetch_related(display_image_prefetch), slug=slug)
    attach_display_images([watch])
    related_watches = attach_display_images(
        list(Watch.objects.filter(category=watch.category).exclude(id=watch.id).prefetch_related(display_image_prefetch)[:4])
    )
    return render(request, 'product.html', {
        'watch': watch,
        'related_watches': related_watches,
    })


def about(request):
    return render(request, 'about.html')


def contact(request):
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        email   = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if name and email and message:
            # Save to DB
            ContactMessage.objects.create(
                name=name, email=email,
                subject=subject or 'General Enquiry',
                message=message,
            )
            # Send branded emails
            send_contact_confirmation(name, email, subject or 'General Enquiry')
            send_contact_admin_notification(name, email, subject or 'General Enquiry', message)

            messages.success(request, 'Your message has been sent. We will respond within 24 hours.')
            return redirect('contact')
        else:
            messages.error(request, 'Please fill in all required fields.')

    return render(request, 'contact.html')
