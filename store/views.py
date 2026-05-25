from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Watch, Category, HomepageBanner, ContactMessage
from orders.emails import send_contact_confirmation, send_contact_admin_notification


def home(request):
    featured_watches = Watch.objects.filter(is_featured=True)[:4]
    trending_watches = Watch.objects.filter(is_trending=True)[:4]
    banners = HomepageBanner.objects.filter(is_active=True)
    return render(request, 'index.html', {
        'featured_watches': featured_watches,
        'trending_watches': trending_watches,
        'banners': banners,
    })


def collection(request):
    watches = Watch.objects.all().order_by('-created_date')
    categories = Category.objects.all()
    return render(request, 'collection.html', {
        'watches': watches,
        'categories': categories,
    })


def product(request, slug):
    watch = get_object_or_404(Watch, slug=slug)
    related_watches = Watch.objects.filter(category=watch.category).exclude(id=watch.id)[:4]
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
