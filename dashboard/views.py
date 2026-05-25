from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from store.models import Watch, Category, HomepageBanner, ContactMessage, WatchImage
from orders.models import Order, OrderStatusHistory
from payments.models import RazorpayPayment
from otp_auth.models import OTPVerification, SMSLog
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from accounts.models import LoginActivity
from .forms import WatchForm, CategoryForm, OrderStatusForm, BannerForm
from orders.emails import send_shipping_update, send_out_for_delivery, send_delivered
import datetime

User = get_user_model()

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@user_passes_test(is_admin)
def dashboard_home(request):
    total_revenue = Order.objects.filter(status='Delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders  = Order.objects.count()
    total_users   = User.objects.count()
    total_watches = Watch.objects.count()
    recent_orders = Order.objects.select_related('payment').order_by('-created_at')[:5]

    # Payment stats
    successful_payments    = RazorpayPayment.objects.filter(status='paid').count()
    failed_payments        = RazorpayPayment.objects.filter(status='failed').count()
    total_razorpay_revenue = RazorpayPayment.objects.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0

    # Recent contacts
    recent_contacts = ContactMessage.objects.order_by('-created_at')[:5]
    unread_contacts = ContactMessage.objects.filter(is_read=False).count()

    context = {
        'total_revenue':         total_revenue,
        'total_orders':          total_orders,
        'total_users':           total_users,
        'total_watches':         total_watches,
        'recent_orders':         recent_orders,
        'successful_payments':   successful_payments,
        'failed_payments':       failed_payments,
        'total_razorpay_revenue':total_razorpay_revenue,
        'recent_contacts':       recent_contacts,
        'unread_contacts':       unread_contacts,
    }
    return render(request, 'dashboard/index.html', context)

@user_passes_test(is_admin)
def product_list(request):
    watches = Watch.objects.all().order_by('-created_date')
    return render(request, 'dashboard/products/list.html', {'watches': watches})

@user_passes_test(is_admin)
def product_create(request):
    if request.method == 'POST':
        form = WatchForm(request.POST, request.FILES)
        if form.is_valid():
            watch = form.save()
            image = form.cleaned_data.get('image')
            if image:
                WatchImage.objects.create(watch=watch, image=image, is_primary=True)
            messages.success(request, 'Watch created successfully.')
            return redirect('dashboard_products')
    else:
        form = WatchForm()
    return render(request, 'dashboard/products/form.html', {'form': form, 'title': 'Add Watch'})

@user_passes_test(is_admin)
def product_update(request, pk):
    watch = get_object_or_404(Watch, pk=pk)
    if request.method == 'POST':
        form = WatchForm(request.POST, request.FILES, instance=watch)
        if form.is_valid():
            watch = form.save()
            image = form.cleaned_data.get('image')
            if image:
                # Remove old primary image if needed, or just add new one as primary
                WatchImage.objects.filter(watch=watch).update(is_primary=False)
                WatchImage.objects.create(watch=watch, image=image, is_primary=True)
            messages.success(request, 'Watch updated successfully.')
            return redirect('dashboard_products')
    else:
        form = WatchForm(instance=watch)
    return render(request, 'dashboard/products/form.html', {'form': form, 'title': 'Edit Watch', 'watch': watch})

@user_passes_test(is_admin)
def product_delete(request, pk):
    watch = get_object_or_404(Watch, pk=pk)
    if request.method == 'POST':
        watch.delete()
        messages.success(request, 'Watch deleted successfully.')
        return redirect('dashboard_products')
    return render(request, 'dashboard/products/delete.html', {'watch': watch})

@user_passes_test(is_admin)
def order_list(request):
    orders = Order.objects.select_related('payment').order_by('-created_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'dashboard/orders/list.html', {
        'orders': orders,
        'order_statuses': Order.STATUS_CHOICES,
    })

@user_passes_test(is_admin)
def order_update(request, pk):
    order = get_object_or_404(Order, pk=pk)
    old_status = order.status
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            updated_order = form.save(commit=False)
            new_status = updated_order.status

            # Capture tracking fields from POST
            updated_order.tracking_number    = request.POST.get('tracking_number', order.tracking_number)
            updated_order.courier_name       = request.POST.get('courier_name', order.courier_name)
            updated_order.admin_notes        = request.POST.get('admin_notes', order.admin_notes)
            est = request.POST.get('estimated_delivery', '')
            if est:
                try:
                    from datetime import date
                    updated_order.estimated_delivery = date.fromisoformat(est)
                except ValueError:
                    pass

            # Timestamps
            from django.utils import timezone
            if new_status == 'Shipped' and old_status != 'Shipped':
                updated_order.shipped_at = timezone.now()
            if new_status == 'Delivered' and old_status != 'Delivered':
                updated_order.delivered_at = timezone.now()

            updated_order.save()

            # Log history if status changed
            if new_status != old_status:
                note = request.POST.get('admin_notes', '')
                OrderStatusHistory.objects.create(order=updated_order, status=new_status, note=note)

                # Trigger branded customer email
                try:
                    if new_status == 'Shipped':
                        send_shipping_update(updated_order)
                    elif new_status == 'Out for Delivery':
                        send_out_for_delivery(updated_order)
                    elif new_status == 'Delivered':
                        send_delivered(updated_order)
                except Exception as e:
                    messages.warning(request, f'Status updated but email failed: {e}')

            messages.success(request, f'Order #{order.id} status updated to {new_status}.')
            return redirect('dashboard_orders')
    else:
        form = OrderStatusForm(instance=order)

    history = order.history.all()
    return render(request, 'dashboard/orders/form.html', {
        'form': form, 'order': order, 'history': history
    })

@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    login_history = LoginActivity.objects.select_related('user').order_by('-created_at')[:50]
    failed_login_count = LoginActivity.objects.filter(status='failed').count()
    otp_login_count = LoginActivity.objects.filter(method='otp', status='success').count()
    password_login_count = LoginActivity.objects.filter(method='password', status='success').count()
    verified_users = User.objects.filter(is_phone_verified=True).count()
    return render(request, 'dashboard/users/list.html', {
        'users': users,
        'login_history': login_history,
        'failed_login_count': failed_login_count,
        'otp_login_count': otp_login_count,
        'password_login_count': password_login_count,
        'verified_users': verified_users,
    })

@user_passes_test(is_admin)
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'dashboard/categories/list.html', {'categories': categories})

@user_passes_test(is_admin)
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully.')
            return redirect('dashboard_categories')
    else:
        form = CategoryForm()
    return render(request, 'dashboard/categories/form.html', {'form': form, 'title': 'Add Category'})

@user_passes_test(is_admin)
def banner_list(request):
    banners = HomepageBanner.objects.all()
    return render(request, 'dashboard/banners/list.html', {'banners': banners})

@user_passes_test(is_admin)
def banner_create(request):
    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Banner created successfully.')
            return redirect('dashboard_banners')
    else:
        form = BannerForm()
    return render(request, 'dashboard/banners/form.html', {'form': form, 'title': 'Add Banner'})

@user_passes_test(is_admin)
def contact_list(request):
    contacts = ContactMessage.objects.all().order_by('-created_at')
    unread_count = contacts.filter(is_read=False).count()
    return render(request, 'dashboard/contacts/list.html', {
        'contacts': contacts,
        'unread_count': unread_count,
    })

@user_passes_test(is_admin)
def contact_mark_read(request, pk):
    contact = get_object_or_404(ContactMessage, pk=pk)
    contact.is_read = not contact.is_read
    contact.save(update_fields=['is_read'])
    return redirect('dashboard_contacts')

@user_passes_test(is_admin)
def contact_delete(request, pk):
    contact = get_object_or_404(ContactMessage, pk=pk)
    contact.delete()
    messages.success(request, 'Message deleted successfully.')
    return redirect('dashboard_contacts')


@user_passes_test(is_admin)
def payment_list(request):
    """Dashboard: full payment history with analytics."""
    payments = RazorpayPayment.objects.select_related('order', 'user').order_by('-created_at')

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        payments = payments.filter(status=status_filter)

    # Aggregates
    total_paid = RazorpayPayment.objects.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    total_failed = RazorpayPayment.objects.filter(status='failed').count()
    total_created = RazorpayPayment.objects.filter(status='created').count()
    total_count = RazorpayPayment.objects.count()

    context = {
        'payments': payments,
        'total_paid': total_paid,
        'total_failed': total_failed,
        'total_created': total_created,
        'total_count': total_count,
        'status_filter': status_filter,
    }
    return render(request, 'dashboard/payments/list.html', context)


@user_passes_test(is_admin)
def otp_dashboard(request):
    """Dashboard: OTP verification logs and SMS delivery analytics."""
    otps = OTPVerification.objects.select_related('user').order_by('-created_at')
    sms_logs = SMSLog.objects.order_by('-created_at')

    # Filters
    status_filter = request.GET.get('status', '')
    purpose_filter = request.GET.get('purpose', '')
    if status_filter:
        otps = otps.filter(status=status_filter)
    if purpose_filter:
        otps = otps.filter(purpose=purpose_filter)

    # Analytics
    total_sent     = SMSLog.objects.filter(status='sent').count()
    total_failed   = SMSLog.objects.filter(status='failed').count()
    total_verified = OTPVerification.objects.filter(status='verified').count()
    total_expired  = OTPVerification.objects.filter(status='expired').count()
    total_blocked  = OTPVerification.objects.filter(status='blocked').count()

    context = {
        'otps':           otps[:100],
        'sms_logs':       sms_logs[:50],
        'total_sent':     total_sent,
        'total_failed':   total_failed,
        'total_verified': total_verified,
        'total_expired':  total_expired,
        'total_blocked':  total_blocked,
        'status_filter':  status_filter,
        'purpose_filter': purpose_filter,
    }
    return render(request, 'dashboard/otp/list.html', context)
