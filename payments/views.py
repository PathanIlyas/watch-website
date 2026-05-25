import json
import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from orders.models import Cart, CartItem, Order, OrderItem, Payment, OrderStatusHistory
from store.models import Watch
from orders.emails import send_order_confirmation, send_payment_success, send_admin_new_order

from .models import RazorpayPayment
from .utils import create_razorpay_order, verify_razorpay_signature

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Helper: resolve the active cart
# ─────────────────────────────────────────────
def _get_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_id=session_id)
    return cart


# ─────────────────────────────────────────────
# 1. Checkout page (GET) + order creation (POST)
# ─────────────────────────────────────────────
def checkout(request):
    """
    GET  → render checkout form with cart summary.
    POST → validate form, create a pending Order + Razorpay order,
           return JSON with Razorpay order details for the JS popup.
    """
    cart = _get_cart(request)
    items = cart.items.select_related('watch').all()

    if not items.exists():
        return redirect('collection')

    subtotal = sum(item.watch.price * item.quantity for item in items)
    shipping = 0  # Complimentary
    tax = round(subtotal * 0, 2)  # 0 % — adjust as needed
    total = subtotal + shipping + tax

    if request.method == 'POST':
        # ── Collect form data ──────────────────────────────────────────
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        country = request.POST.get('country', '').strip()
        payment_method = request.POST.get('payment_method', 'razorpay')

        # ── Basic validation ───────────────────────────────────────────
        required = [first_name, last_name, email, phone, address, city, postal_code, country]
        if not all(required):
            return JsonResponse({'success': False, 'error': 'Please fill in all required fields.'}, status=400)

        # ── Checkout OTP gate ──────────────────────────────────────────
        from otp_auth.utils import normalize_phone as _norm_phone
        norm_phone = _norm_phone(phone)
        verified_phone = request.session.get('checkout_otp_verified_phone', '')
        if verified_phone != norm_phone:
            return JsonResponse({
                'success': False,
                'otp_required': True,
                'phone': norm_phone,
                'masked_phone': f"{'*'*(len(norm_phone)-4)}{norm_phone[-4:]}",
                'expiry_minutes': getattr(settings, 'OTP_EXPIRY_MINUTES', 5),
                'message': 'Please verify your phone number to place the order.',
            })

        # ── Cash on Delivery path ──────────────────────────────────────
        if payment_method == 'cod':
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                first_name=first_name, last_name=last_name,
                email=email, phone=phone, address=address,
                city=city, state=state, postal_code=postal_code,
                country=country, total_amount=total,
            )
            for item in items:
                OrderItem.objects.create(
                    order=order, watch=item.watch,
                    price=item.watch.price, quantity=item.quantity,
                )
                # Reduce stock
                Watch.objects.filter(pk=item.watch.pk).update(
                    stock_quantity=item.watch.stock_quantity - item.quantity
                )
            Payment.objects.create(
                order=order, payment_method='Cash on Delivery',
                amount=total, status='Pending',
            )
            cart.items.all().delete()
            # Log status history
            OrderStatusHistory.objects.create(order=order, status='Confirmed', note='Order placed via Cash on Delivery')
            # Send branded emails
            cod_items = order.items.select_related('watch').all()
            send_order_confirmation(order, cod_items)
            send_admin_new_order(order, cod_items)
            return JsonResponse({'success': True, 'redirect': f'/payments/success/{order.id}/?cod=1'})

        # ── Razorpay path ──────────────────────────────────────────────
        # Create the Django Order first (status stays Pending until payment verified)
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            first_name=first_name, last_name=last_name,
            email=email, phone=phone, address=address,
            city=city, state=state, postal_code=postal_code,
            country=country, total_amount=total,
        )

        # Create Razorpay order
        rz_order = create_razorpay_order(
            amount_inr=float(total),
            receipt=f'order_{order.id}',
            notes={'customer': f'{first_name} {last_name}', 'email': email},
        )

        if not rz_order:
            order.delete()
            return JsonResponse({'success': False, 'error': 'Payment gateway error. Please try again.'}, status=500)

        # Persist Razorpay order record
        RazorpayPayment.objects.create(
            user=request.user if request.user.is_authenticated else None,
            order=order,
            razorpay_order_id=rz_order['id'],
            amount=total,
            status='created',
        )

        return JsonResponse({
            'success': True,
            'razorpay': True,
            'razorpay_order_id': rz_order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'amount': int(float(total) * 100),  # paise
            'currency': 'INR',
            'order_id': order.id,
            'name': 'CHRONOS Luxury Watches',
            'description': f'Order #{order.id}',
            'prefill': {
                'name': f'{first_name} {last_name}',
                'email': email,
                'contact': phone,
            },
        })

    context = {
        'items': items,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'total': total,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    }
    return render(request, 'checkout.html', context)


# ─────────────────────────────────────────────
# 2. Payment verification (called by JS after popup)
# ─────────────────────────────────────────────
@require_POST
def verify_payment(request):
    """
    Receives Razorpay callback data, verifies HMAC signature,
    finalises the order, clears the cart.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

    razorpay_order_id = data.get('razorpay_order_id', '')
    razorpay_payment_id = data.get('razorpay_payment_id', '')
    razorpay_signature = data.get('razorpay_signature', '')
    order_id = data.get('order_id')

    # Fetch our records
    rz_payment = get_object_or_404(RazorpayPayment, razorpay_order_id=razorpay_order_id)
    order = rz_payment.order

    # Verify signature
    if not verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        rz_payment.status = 'failed'
        rz_payment.save()
        logger.warning("Razorpay signature verification FAILED for order %s", order.id)
        return JsonResponse({'success': False, 'error': 'Payment verification failed. Contact support.'}, status=400)

    # ── Signature valid — finalise order ──────────────────────────────
    rz_payment.razorpay_payment_id = razorpay_payment_id
    rz_payment.razorpay_signature = razorpay_signature
    rz_payment.status = 'paid'
    rz_payment.save()

    # Create order items & reduce stock
    cart = _get_cart(request)
    items = cart.items.select_related('watch').all()
    for item in items:
        OrderItem.objects.get_or_create(
            order=order, watch=item.watch,
            defaults={'price': item.watch.price, 'quantity': item.quantity},
        )
        Watch.objects.filter(pk=item.watch.pk).update(
            stock_quantity=item.watch.stock_quantity - item.quantity
        )

    # Update legacy Payment record
    Payment.objects.update_or_create(
        order=order,
        defaults={
            'payment_method': 'Razorpay',
            'transaction_id': razorpay_payment_id,
            'amount': order.total_amount,
            'status': 'Completed',
        },
    )

    order.status = 'Processing'
    order.save()

    # Log status history
    OrderStatusHistory.objects.create(order=order, status='Confirmed', note='Payment verified via Razorpay')

    # Clear cart
    cart.items.all().delete()

    # Send branded emails
    confirmed_items = order.items.select_related('watch').all()
    send_order_confirmation(order, confirmed_items)
    send_payment_success(order, razorpay_payment_id)
    send_admin_new_order(order, confirmed_items)

    return JsonResponse({'success': True, 'redirect': f'/payments/success/{order.id}/'})


# ─────────────────────────────────────────────
# 3. Payment failure handler
# ─────────────────────────────────────────────
@require_POST
def payment_failed(request):
    """Mark the Razorpay payment as failed and redirect to failure page."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False}, status=400)

    razorpay_order_id = data.get('razorpay_order_id', '')
    error_description = data.get('error', 'Payment was not completed.')

    try:
        rz_payment = RazorpayPayment.objects.get(razorpay_order_id=razorpay_order_id)
        rz_payment.status = 'failed'
        rz_payment.save()
        order_id = rz_payment.order.id
    except RazorpayPayment.DoesNotExist:
        order_id = None

    return JsonResponse({
        'success': True,
        'redirect': f'/payments/failed/?order_id={order_id}&error={error_description}',
    })


# ─────────────────────────────────────────────
# 4. Success page
# ─────────────────────────────────────────────
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = order.items.select_related('watch').all()
    try:
        rz_payment = order.razorpay_payment
    except RazorpayPayment.DoesNotExist:
        rz_payment = None

    is_cod = request.GET.get('cod') == '1'

    context = {
        'order': order,
        'items': items,
        'rz_payment': rz_payment,
        'is_cod': is_cod,
    }
    return render(request, 'payments/success.html', context)


# ─────────────────────────────────────────────
# 5. Failure page
# ─────────────────────────────────────────────
def payment_failure(request):
    order_id = request.GET.get('order_id')
    error = request.GET.get('error', 'Your payment could not be processed.')
    order = None
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            pass
    return render(request, 'payments/failed.html', {'order': order, 'error': error})


# ─────────────────────────────────────────────
# 6. Razorpay Webhook (optional, for server-side events)
# ─────────────────────────────────────────────
@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """
    Handles Razorpay webhook events.
    Verify the webhook signature using the Razorpay-Signature header.
    """
    import hmac as _hmac
    import hashlib as _hashlib

    webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
    if not webhook_secret:
        return JsonResponse({'status': 'webhook secret not configured'}, status=200)

    received_sig = request.headers.get('X-Razorpay-Signature', '')
    body = request.body

    expected = _hmac.new(
        webhook_secret.encode('utf-8'), body, _hashlib.sha256
    ).hexdigest()

    if not _hmac.compare_digest(expected, received_sig):
        logger.warning("Razorpay webhook signature mismatch.")
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    event = payload.get('event', '')

    if event == 'payment.captured':
        payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
        rz_order_id = payment_entity.get('order_id', '')
        rz_payment_id = payment_entity.get('id', '')
        try:
            rz_payment = RazorpayPayment.objects.get(razorpay_order_id=rz_order_id)
            if rz_payment.status != 'paid':
                rz_payment.razorpay_payment_id = rz_payment_id
                rz_payment.status = 'paid'
                rz_payment.save()
                rz_payment.order.status = 'Processing'
                rz_payment.order.save()
        except RazorpayPayment.DoesNotExist:
            pass

    elif event == 'payment.failed':
        payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
        rz_order_id = payment_entity.get('order_id', '')
        try:
            rz_payment = RazorpayPayment.objects.get(razorpay_order_id=rz_order_id)
            rz_payment.status = 'failed'
            rz_payment.save()
        except RazorpayPayment.DoesNotExist:
            pass

    return JsonResponse({'status': 'ok'})


# ─────────────────────────────────────────────
# (email sending is handled by orders.emails module)
# ─────────────────────────────────────────────


# ─────────────────────────────────────────────
# 7. Checkout OTP — Send
# ─────────────────────────────────────────────
@require_POST
def checkout_send_otp(request):
    """Send OTP to phone number before allowing order placement."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

    phone_raw = data.get('phone', '').strip()
    if not phone_raw:
        return JsonResponse({'success': False, 'error': 'Phone number is required.'})

    from otp_auth.utils import (
        validate_phone, normalize_phone,
        create_otp_record, is_rate_limited, get_client_ip,
    )
    from otp_auth.services import send_otp_sms

    valid, err = validate_phone(phone_raw)
    if not valid:
        return JsonResponse({'success': False, 'error': err})

    phone = normalize_phone(phone_raw)

    if is_rate_limited(phone, 'checkout'):
        return JsonResponse({'success': False, 'error': 'Please wait 1 minute before requesting another OTP.'})

    user = request.user if request.user.is_authenticated else None
    ip   = get_client_ip(request)
    otp_plain, record = create_otp_record(phone, 'checkout', user=user, ip=ip)
    customer_email = getattr(user, 'email', '') if user else ''
    result = send_otp_sms(phone, otp_plain, customer_email=customer_email)

    if not result.get('success'):
        return JsonResponse({'success': False, 'error': 'Failed to send OTP. Please try again.'})

    request.session['otp_phone']     = phone
    request.session['otp_purpose']   = 'checkout'
    request.session['otp_record_id'] = record.id
    request.session.modified = True   # force session save

    expiry = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
    resp = {
        'success': True,
        'message': f'OTP sent to your phone. Valid for {expiry} minutes.',
        'expiry_minutes': expiry,
        'masked_phone': f"{'*'*(len(phone)-4)}{phone[-4:]}",
        'normalized_phone': phone,      # send back to JS so verify uses correct format
        'record_id': record.id,         # send record_id so verify doesn't need session
    }
    if result.get('console') and settings.DEBUG:
        resp['console_otp'] = otp_plain
    return JsonResponse(resp)


# ─────────────────────────────────────────────
# 8. Checkout OTP — Verify
# ─────────────────────────────────────────────
@require_POST
def checkout_verify_otp(request):
    """Verify checkout OTP and mark phone as verified in session."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

    otp_input = data.get('otp', '').strip()
    record_id = data.get('record_id')          # preferred — passed from JS
    phone     = data.get('phone', '').strip()  # normalized phone from JS

    if not otp_input:
        return JsonResponse({'success': False, 'error': 'OTP is required.'})

    from otp_auth.utils import normalize_phone
    from otp_auth.models import OTPVerification
    from django.utils import timezone

    # ── Strategy 1: use record_id (most reliable, no session needed) ──
    if record_id:
        try:
            record = OTPVerification.objects.get(id=record_id, purpose='checkout', status='pending')
            phone = record.phone  # use phone from DB record — guaranteed correct format
        except OTPVerification.DoesNotExist:
            # record_id stale — fall through to phone lookup
            record_id = None

    # ── Strategy 2: use normalized phone from session or JS ───────────
    if not record_id:
        # Try session first
        phone = request.session.get('otp_phone', '') or phone
        # Normalize if needed
        if phone and not phone.startswith('+'):
            phone = normalize_phone(phone)

        if not phone:
            return JsonResponse({'success': False, 'error': 'Session expired. Please request a new OTP.'})

        try:
            record = OTPVerification.objects.filter(
                phone=phone, purpose='checkout', status='pending'
            ).latest('created_at')
        except OTPVerification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'No active OTP found. Please request a new one.'})

    # ── Validate OTP ──────────────────────────────────────────────────
    if record.is_expired:
        record.status = 'expired'
        record.save(update_fields=['status'])
        return JsonResponse({'success': False, 'error': 'OTP has expired. Please request a new one.'})

    if record.is_blocked:
        return JsonResponse({'success': False, 'error': 'Too many incorrect attempts. Please request a new OTP.'})

    if not record.check_otp(otp_input):
        record.increment_attempts()
        from django.conf import settings as _s
        remaining = getattr(_s, 'OTP_MAX_ATTEMPTS', 5) - record.attempts
        if remaining > 0:
            return JsonResponse({'success': False, 'error': f'Incorrect OTP. {remaining} attempt(s) remaining.'})
        return JsonResponse({'success': False, 'error': 'Too many incorrect attempts. Please request a new OTP.'})

    # ── OTP correct ───────────────────────────────────────────────────
    record.mark_verified()

    # Mark phone as checkout-verified in session
    request.session['checkout_otp_verified_phone'] = record.phone
    request.session.modified = True
    for key in ('otp_phone', 'otp_purpose', 'otp_record_id'):
        request.session.pop(key, None)

    return JsonResponse({'success': True, 'message': 'Phone verified. You can now place your order.'})
