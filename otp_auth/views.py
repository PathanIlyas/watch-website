import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone

from .models import OTPVerification
from .services import send_otp_sms
from .utils import (
    normalize_phone, validate_phone,
    create_otp_record, verify_otp_code,
    is_rate_limited, get_client_ip,
)

logger = logging.getLogger(__name__)
User = get_user_model()


# ─────────────────────────────────────────────────────────────
# 1. Send OTP page (GET) + send OTP (POST)
# ─────────────────────────────────────────────────────────────
def send_otp_view(request):
    """
    GET  → render phone number entry form
    POST → validate phone, generate OTP, send SMS, redirect to verify page
    """
    purpose = request.GET.get('purpose', 'login')

    if request.method == 'POST':
        phone_raw = request.POST.get('phone', '').strip()
        purpose   = request.POST.get('purpose', 'login')

        # Validate
        valid, err = validate_phone(phone_raw)
        if not valid:
            return render(request, 'otp_auth/send_otp.html', {
                'error': err, 'purpose': purpose, 'phone': phone_raw
            })

        phone = normalize_phone(phone_raw)

        # Rate limit check
        if is_rate_limited(phone, purpose):
            expiry = getattr(settings, 'OTP_RATE_LIMIT_MINUTES', 1)
            return render(request, 'otp_auth/send_otp.html', {
                'error': f'Please wait {expiry} minute(s) before requesting another OTP.',
                'purpose': purpose, 'phone': phone_raw,
            })

        # Find the existing user for login. Login should not silently create
        # a partial account because that can block the real registration flow.
        user = None
        if purpose == 'login':
            try:
                user = User.objects.get(phone_number=phone)
            except User.DoesNotExist:
                return render(request, 'otp_auth/send_otp.html', {
                    'error': 'No account exists with this mobile number. Please register first.',
                    'purpose': purpose,
                    'phone': phone_raw,
                })

        # Create OTP record
        ip = get_client_ip(request)
        otp_plain, record = create_otp_record(phone, purpose, user=user, ip=ip)

        # Send SMS
        result = send_otp_sms(phone, otp_plain, customer_email=getattr(user, 'email', ''))

        if not result.get('success'):
            logger.error("[OTP] SMS send failed for %s: %s", phone, result.get('error'))
            return render(request, 'otp_auth/send_otp.html', {
                'error': 'Failed to send OTP. Please try again.',
                'purpose': purpose, 'phone': phone_raw,
            })

        # Store phone in session for verify step
        request.session['otp_phone']   = phone
        request.session['otp_purpose'] = purpose
        request.session['otp_record_id'] = record.id
        if purpose == 'login' and user:
            request.session['pending_user_id'] = user.id

        # Console mode: show OTP on screen in DEBUG
        console_otp = otp_plain if (result.get('console') and settings.DEBUG) else None

        return render(request, 'otp_auth/verify_otp.html', {
            'phone': phone,
            'purpose': purpose,
            'expiry_minutes': getattr(settings, 'OTP_EXPIRY_MINUTES', 5),
            'console_otp': console_otp,
            'masked_phone': f"{'*' * (len(phone) - 4)}{phone[-4:]}",
        })

    return render(request, 'otp_auth/send_otp.html', {
        'purpose': purpose,
    })


# ─────────────────────────────────────────────────────────────
# 2. Verify OTP (POST — AJAX or form)
# ─────────────────────────────────────────────────────────────
@require_POST
def verify_otp_view(request):
    """
    Accepts both AJAX (JSON) and regular form POST.
    Verifies OTP, logs user in on success.
    """
    # Support both JSON and form POST
    if request.content_type and 'application/json' in request.content_type:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)
        otp_input = data.get('otp', '').strip()
        phone     = data.get('phone', '') or request.session.get('otp_phone', '')
        purpose   = data.get('purpose', '') or request.session.get('otp_purpose', 'login')
        is_ajax   = True
    else:
        otp_input = request.POST.get('otp', '').strip()
        phone     = request.POST.get('phone', '') or request.session.get('otp_phone', '')
        purpose   = request.POST.get('purpose', '') or request.session.get('otp_purpose', 'login')
        is_ajax   = False

    if not phone or not otp_input:
        msg = 'Phone number and OTP are required.'
        return JsonResponse({'success': False, 'error': msg}, status=400) if is_ajax else \
               render(request, 'otp_auth/verify_otp.html', {'error': msg, 'phone': phone, 'purpose': purpose})

    success, message = verify_otp_code(phone, otp_input, purpose)

    if not success:
        if is_ajax:
            return JsonResponse({'success': False, 'error': message})
        return render(request, 'otp_auth/verify_otp.html', {
            'error': message, 'phone': phone, 'purpose': purpose,
            'expiry_minutes': getattr(settings, 'OTP_EXPIRY_MINUTES', 5),
            'masked_phone': f"{'*' * (len(phone) - 4)}{phone[-4:]}",
        })

    # ── OTP valid — log user in ───────────────────────────────
    purpose = data.get('purpose', '') or request.session.get('otp_purpose', 'login') if is_ajax else \
              request.POST.get('purpose', '') or request.session.get('otp_purpose', 'login')

    # Route to purpose-specific handler
    if purpose == 'register':
        from accounts.views import register_verify_otp
        return register_verify_otp(request)
    if purpose == 'login':
        from accounts.views import login_verify_otp
        return login_verify_otp(request)
    if purpose == 'reset':
        from accounts.views import reset_verify_otp
        return reset_verify_otp(request)

    # Generic: try to log in by phone
    try:
        user = User.objects.get(phone_number=phone)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        for key in ('otp_phone', 'otp_purpose', 'otp_record_id'):
            request.session.pop(key, None)
        redirect_url = '/dashboard/' if (user.is_staff or user.is_superuser) else '/'
        if is_ajax:
            return JsonResponse({'success': True, 'redirect': redirect_url})
        return redirect(redirect_url)
    except User.DoesNotExist:
        msg = 'User not found.'
        if is_ajax:
            return JsonResponse({'success': False, 'error': msg})
        return render(request, 'otp_auth/verify_otp.html', {'error': msg, 'phone': phone, 'purpose': purpose})


# ─────────────────────────────────────────────────────────────
# 3. Resend OTP (AJAX POST)
# ─────────────────────────────────────────────────────────────
@require_POST
def resend_otp_view(request):
    """AJAX endpoint to resend OTP."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

    phone   = data.get('phone', '') or request.session.get('otp_phone', '')
    purpose = data.get('purpose', 'login') or request.session.get('otp_purpose', 'login')

    if not phone:
        return JsonResponse({'success': False, 'error': 'Phone number missing.'})

    if is_rate_limited(phone, purpose):
        return JsonResponse({
            'success': False,
            'error': f"Please wait before requesting another OTP.",
        })

    ip = get_client_ip(request)
    user = None
    try:
        user = User.objects.get(phone_number=phone)
    except User.DoesNotExist:
        pass

    otp_plain, record = create_otp_record(phone, purpose, user=user, ip=ip)
    customer_email = getattr(user, 'email', '') or request.session.get('reg_email', '')
    result = send_otp_sms(phone, otp_plain, customer_email=customer_email)

    if not result.get('success'):
        return JsonResponse({'success': False, 'error': 'Failed to resend OTP. Try again.'})

    request.session['otp_record_id'] = record.id
    if purpose == 'login' and user:
        request.session['pending_user_id'] = user.id
    expiry = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)

    response_data = {
        'success': True,
        'message': f'OTP resent successfully. Valid for {expiry} minutes.',
    }
    if result.get('console') and settings.DEBUG:
        response_data['console_otp'] = otp_plain

    return JsonResponse(response_data)


# ─────────────────────────────────────────────────────────────
# 4. OTP Status check (AJAX GET — for countdown sync)
# ─────────────────────────────────────────────────────────────
def otp_status_view(request):
    record_id = request.session.get('otp_record_id')
    if not record_id:
        return JsonResponse({'active': False})
    try:
        record = OTPVerification.objects.get(id=record_id)
        remaining = max(0, int((record.expires_at - timezone.now()).total_seconds()))
        return JsonResponse({
            'active': not record.is_expired and record.status == 'pending',
            'remaining_seconds': remaining,
            'attempts': record.attempts,
            'max_attempts': getattr(settings, 'OTP_MAX_ATTEMPTS', 5),
        })
    except OTPVerification.DoesNotExist:
        return JsonResponse({'active': False})
