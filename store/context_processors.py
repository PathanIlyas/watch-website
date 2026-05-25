from orders.models import Cart
from django.db.models import Sum
from django.db.models.functions import Coalesce

def cart_context(request):
    cart_filter = None
    user = getattr(request, 'user', None)

    if user is not None and user.is_authenticated:
        cart_filter = {'user': user}
    else:
        session = getattr(request, 'session', None)
        session_id = getattr(session, 'session_key', None)
        if session_id:
            cart_filter = {'session_id': session_id}

    cart_count = 0
    if cart_filter:
        cart_count = (
            Cart.objects
            .filter(**cart_filter)
            .order_by('id')
            .annotate(total_items=Coalesce(Sum('items__quantity'), 0))
            .values_list('total_items', flat=True)
            .first()
            or 0
        )

    return {'cart_count': cart_count}
