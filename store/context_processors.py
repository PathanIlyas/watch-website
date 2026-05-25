from orders.models import Cart

def cart_context(request):
    cart_count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_count = sum(item.quantity for item in cart.items.all())
    else:
        session_id = request.session.session_key
        if session_id:
            cart = Cart.objects.filter(session_id=session_id).first()
            if cart:
                cart_count = sum(item.quantity for item in cart.items.all())
    return {'cart_count': cart_count}
