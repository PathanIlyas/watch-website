from django.shortcuts import render, redirect, get_object_or_404
from store.models import Watch
from store.views import attach_display_images
from .models import Cart, CartItem, Order, OrderItem, Payment, OrderStatusHistory


def get_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_id=session_id)
    return cart


def cart(request):
    cart = get_cart(request)
    items = cart.items.select_related('watch').all()
    watches = [item.watch for item in items]
    attach_display_images(watches)
    total = sum(item.watch.price * item.quantity for item in items)
    return render(request, 'cart.html', {'items': items, 'total': total})


def add_to_cart(request, watch_id):
    watch = get_object_or_404(Watch, id=watch_id)
    cart = get_cart(request)
    item, created = CartItem.objects.get_or_create(cart=cart, watch=watch)
    if not created:
        item.quantity += 1
        item.save()
    return redirect('cart')


def update_cart(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(CartItem, id=item_id)
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            item.quantity = quantity
            item.save()
        else:
            item.delete()
    return redirect('cart')


def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    return redirect('cart')


def track_order(request):
    """
    Public order tracking page.
    GET  → show search form (optionally pre-filled from ?order_id=)
    POST → look up order and show tracking timeline
    """
    order = None
    error = None
    history = []

    # Support both GET (from success page link) and POST (form submit)
    order_id = request.POST.get('order_id') or request.GET.get('order_id')

    if order_id:
        try:
            order = Order.objects.prefetch_related('items__watch', 'history').get(id=int(order_id))
            history = order.history.all()
        except (Order.DoesNotExist, ValueError):
            error = f'No order found with ID #{order_id}. Please check and try again.'

    # Build timeline steps for the progress UI
    STEPS = [
        ('Confirmed',        'Order Confirmed',   'fas fa-check-circle'),
        ('Processing',       'Processing',        'fas fa-cog'),
        ('Packed',           'Packed',            'fas fa-box'),
        ('Shipped',          'Shipped',           'fas fa-shipping-fast'),
        ('Out for Delivery', 'Out for Delivery',  'fas fa-truck'),
        ('Delivered',        'Delivered',         'fas fa-home'),
    ]

    current_step = order.step if order else 0

    return render(request, 'track_order.html', {
        'order': order,
        'error': error,
        'history': history,
        'steps': STEPS,
        'current_step': current_step,
        'order_id_input': order_id or '',
    })
