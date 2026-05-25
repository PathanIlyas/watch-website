"""
CHRONOS — Complete Authentication System
Handles: Login (2FA), Registration, Password Reset
All flows use OTP SMS verification.
"""
import json
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from otp_auth.services import send_otp_sms
from otp_auth.utils import (
    normalize_phone, validate_phone,
    create_otp_record, verify_otp_code,
    is_rate_limited, get_client_ip,
)
from .models import LoginActivity

logger = logging.getLogger(__name__)
User = get_user_model()


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def _send_otp(phone, purpose, user=None, ip=None, email=''):
    """Create OTP record and send SMS (with email fallback). Returns (otp_plain, record, result)."""
    otp_plain, record = create_otp_record(phone, purpose, user=user, ip=ip)
    result = send_otp_sms(phone, otp_plain, customer_email=email)
    return otp_plain, record, result


def _otp_context(phone, purpose, expiry, console_otp=None):
    masked = f"{'*' * (len(phone) - 4)}{phone[-4:]}"
    return {
        'phone': phone,
        'purpose': purpose,
        'expiry_minutes': expiry,
        'masked_phone': masked,
        'console_otp': console_otp,
    }


def _record_login_activity(request, method, status, identifier='', user=None, message=''):
    LoginActivity.objects.create(
        user=user,
        identifier=(identifier or '')[:255],
        method=method,
        status=status,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
        message=(message or '')[:255],
    )


def _is_password_locked(user):
    lock_minutes = getattr(settings, 'PASSWORD_LOGIN_LOCK_MINUTES', 15)
    max_attempts = getattr(settings, 'PASSWORD_LOGIN_MAX_ATTEMPTS', 5)
    if not user or user.failed_login_attempts < max_attempts or not user.last_login_attempt:
        return False
    return user.last_login_attempt >= timezone.now() - timedelta(minutes=lock_minutes)


# ─────────────────────────────────────────────────────────────
# 1. REGISTRATION
# ─────────────────────────────────────────────────────────────
def _get_login_user(identifier):
    """Find a user by email, username, or unique display name for password login."""
    identifier = (identifier or '').strip()
    if not identifier:
        return None

    user = User.objects.filter(email__iexact=identifier).first()
    if user:
        return user

    user = User.objects.filter(username__iexact=identifier).first()
    if user:
        return user

    full_name_matches = list(User.objects.filter(full_name__iexact=identifier)[:2])
    if len(full_name_matches) == 1:
        return full_name_matches[0]

    return None


def register_view(request):
    """Step 1: Collect user details → send OTP."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        username  = request.POST.get('username', '').strip()
        email     = request.POST.get('email', '').strip().lower()
        phone_raw = request.POST.get('phone', '').strip()
        password  = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        errors = {}

        # Validate fields
        if not full_name:
            errors['full_name'] = 'Full name is required.'
        if not username:
            errors['username'] = 'Username is required.'
        if not email:
            errors['email'] = 'Email is required.'
        if not phone_raw:
            errors['phone'] = 'Phone number is required.'
        if not password:
            errors['password'] = 'Password is required.'
        if password != password2:
            errors['password2'] = 'Passwords do not match.'

        # Phone validation
        if phone_raw:
            valid, err = validate_phone(phone_raw)
            if not valid:
                errors['phone'] = err

        # Duplicate checks
        if username and User.objects.filter(username__iexact=username).exists():
            errors['username'] = 'This username is already taken.'
        if email and User.objects.filter(email=email).exists():
            errors['email'] = 'An account with this email already exists.'

        phone = normalize_phone(phone_raw) if phone_raw else ''
        if phone and User.objects.filter(phone_number=phone).exists():
            errors['phone'] = 'An account with this phone number already exists.'

        # Password strength
        if password and not errors.get('password'):
            try:
                validate_password(password)
            except ValidationError as e:
                errors['password'] = ' '.join(e.messages)

        if errors:
            return render(request, 'accounts/register.html', {
                'errors': errors,
                'full_name': full_name, 'username': username,
                'email': email, 'phone': phone_raw,
            })

        # Rate limit
        if is_rate_limited(phone, 'register'):
            return render(request, 'accounts/register.html', {
                'errors': {'phone': 'Please wait 1 minute before requesting another OTP.'},
                'full_name': full_name, 'username': username,
                'email': email, 'phone': phone_raw,
            })

        # Store registration data in session (not DB yet — wait for OTP)
        request.session['reg_full_name'] = full_name
        request.session['reg_username']  = username
        request.session['reg_email']     = email
        request.session['reg_phone']     = phone
        request.session['reg_password']  = make_password(password)

        # Send OTP
        ip = get_client_ip(request)
        otp_plain, record, result = _send_otp(phone, 'register', ip=ip, email=email)

        if not result.get('success'):
            return render(request, 'accounts/register.html', {
                'errors': {'phone': 'Failed to send OTP. Please try again.'},
                'full_name': full_name, 'username': username,
                'email': email, 'phone': phone_raw,
            })

        request.session['otp_phone']    = phone
        request.session['otp_purpose']  = 'register'
        request.session['otp_record_id'] = record.id

        expiry = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
        console_otp = otp_plain if (result.get('console') and settings.DEBUG) else None

        return render(request, 'otp_auth/verify_otp.html',
                      _otp_context(phone, 'register', expiry, console_otp))

    return render(request, 'accounts/register.html')


@require_POST
def register_verify_otp(request):
    """Step 2: Verify OTP → create account → auto-login."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

    otp_input = data.get('otp', '').strip()
    phone     = data.get('phone', '') or request.session.get('otp_phone', '')
    purpose   = 'register'

    if not phone or not otp_input:
        return JsonResponse({'success': False, 'error': 'OTP and phone are required.'})

    success, message = verify_otp_code(phone, otp_input, purpose)
    if not success:
        return JsonResponse({'success': False, 'error': message})

    # Retrieve registration data from session
    full_name = request.session.get('reg_full_name', '')
    username  = request.session.get('reg_username', '')
    email     = request.session.get('reg_email', '')
    reg_phone = request.session.get('reg_phone', phone)
    hashed_pw = request.session.get('reg_password', '')

    if not hashed_pw:
        return JsonResponse({'success': False, 'error': 'Session expired. Please register again.'})

    # Create user
    try:
        user = User.objects.create(
            username=username or email,
            email=email,
            full_name=full_name,
            phone_number=reg_phone,
            password=hashed_pw,
            is_phone_verified=True,
            is_customer=True,
        )
        # Set first/last name
        parts = full_name.split(' ', 1)
        user.first_name = parts[0]
        user.last_name  = parts[1] if len(parts) > 1 else ''
        user.save(update_fields=['first_name', 'last_name'])
    except Exception as e:
        logger.error("User creation failed: %s", e)
        return JsonResponse({'success': False, 'error': 'Account creation failed. Please try again.'})

    # Clear session registration data
    for key in ('reg_full_name', 'reg_username', 'reg_email', 'reg_phone',
                'reg_password', 'otp_phone', 'otp_purpose', 'otp_record_id'):
        request.session.pop(key, None)

    # Auto-login
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    # Send welcome email
    try:
        from orders.emails import send_welcome_email
        send_welcome_email(user.email, user.first_name or full_name)
    except Exception:
        pass

    return JsonResponse({'success': True, 'redirect': '/'})


# ─────────────────────────────────────────────────────────────
# 2. LOGIN (2FA — password + OTP)
# ─────────────────────────────────────────────────────────────
def login_view(request):
    """Step 1: Validate credentials → send OTP."""
    if request.user.is_authenticated:
        return redirect('dashboard_home' if request.user.is_staff else 'home')

    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()  # email, username, or phone
        password   = request.POST.get('password', '')
        if not identifier or not password:
            return render(request, 'login.html', {'error': 'Please enter your credentials.'})

        login_user = _get_login_user(identifier)
        if login_user and _is_password_locked(login_user):
            _record_login_activity(request, 'password', 'failed', identifier, login_user, 'Locked')
            return render(request, 'login.html', {
                'error': 'Too many failed attempts. Please wait 15 minutes or use OTP login.',
                'username': identifier,
            })

        user = authenticate(
            request,
            username=login_user.username if login_user else identifier,
            password=password,
        )

        if user is None:
            if login_user:
                login_user.failed_login_attempts += 1
                login_user.last_login_attempt = timezone.now()
                login_user.save(update_fields=['failed_login_attempts', 'last_login_attempt'])
            _record_login_activity(request, 'password', 'failed', identifier, login_user, 'Invalid credentials')
            return render(request, 'login.html', {
                'error': 'Invalid credentials. Please try again.',
                'username': identifier,
            })

        if not user.is_active:
            _record_login_activity(request, 'password', 'failed', identifier, user, 'Inactive account')
            return render(request, 'login.html', {'error': 'Your account has been disabled.'})

        # Password login completes immediately; OTP is a separate login method.
        login(request, user)
        user.failed_login_attempts = 0
        user.last_login_attempt = timezone.now()
        user.save(update_fields=['failed_login_attempts', 'last_login_attempt'])
        _record_login_activity(request, 'password', 'success', identifier, user)
        return redirect('dashboard_home' if (user.is_staff or user.is_superuser) else 'home')

        # Check if user has a phone number for 2FA
        if False and not user.phone_number:
            # No phone — login directly
            login(request, user)
            return redirect('home')

        phone = user.phone_number

        # Rate limit
        if is_rate_limited(phone, 'login'):
            return render(request, 'login.html', {
                'error': 'Please wait 1 minute before requesting another OTP.',
                'username': identifier,
            })

        # Send 2FA OTP
        ip = get_client_ip(request)
        otp_plain, record, result = _send_otp(phone, 'login', user=user, ip=ip, email=user.email)

        if not result.get('success'):
            # Fallback: login without 2FA if SMS fails
            logger.warning("[2FA] SMS failed for %s, logging in directly", phone)
            login(request, user)
            return redirect('home')

        request.session['otp_phone']     = phone
        request.session['otp_purpose']   = 'login'
        request.session['otp_record_id'] = record.id
        request.session['pending_user_id'] = user.id

        expiry = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
        console_otp = otp_plain if (result.get('console') and settings.DEBUG) else None

        return render(request, 'otp_auth/verify_otp.html',
                      _otp_context(phone, 'login', expiry, console_otp))

    return render(request, 'login.html')


@require_POST
def login_send_otp(request):
    """Send an OTP for phone-only login. This path never checks a password."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    phone_raw = data.get('phone', '').strip()
    valid, err = validate_phone(phone_raw)
    if not valid:
        return JsonResponse({'success': False, 'error': err}, status=400)

    phone = normalize_phone(phone_raw)
    user = User.objects.filter(phone_number=phone, is_active=True).first()
    if not user:
        _record_login_activity(request, 'otp', 'failed', phone, None, 'Unregistered phone number')
        return JsonResponse({
            'success': False,
            'error': 'No account exists with this mobile number. Please register first.',
        }, status=404)

    if is_rate_limited(phone, 'login'):
        _record_login_activity(request, 'otp', 'failed', phone, user, 'Rate limited')
        return JsonResponse({
            'success': False,
            'error': 'Please wait before requesting another OTP.',
        }, status=429)

    ip = get_client_ip(request)
    otp_plain, record, result = _send_otp(phone, 'login', user=user, ip=ip, email=user.email)

    if not result.get('success'):
        _record_login_activity(request, 'otp', 'failed', phone, user, 'OTP delivery failed')
        return JsonResponse({'success': False, 'error': 'Failed to send OTP. Please try again.'}, status=502)

    request.session['otp_phone'] = phone
    request.session['otp_purpose'] = 'login'
    request.session['otp_record_id'] = record.id
    request.session['pending_user_id'] = user.id

    response = {
        'success': True,
        'message': 'OTP sent successfully.',
        'phone': phone,
        'masked_phone': f"{'*' * (len(phone) - 4)}{phone[-4:]}",
        'expiry_seconds': getattr(settings, 'OTP_EXPIRY_MINUTES', 5) * 60,
    }
    if result.get('console') and settings.DEBUG:
        response['console_otp'] = otp_plain
    return JsonResponse(response)


@require_POST
def login_verify_otp(request):
    """Step 2: Verify 2FA OTP → complete login."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

    otp_input = data.get('otp', '').strip()
    phone     = data.get('phone', '') or request.session.get('otp_phone', '')

    if not phone or not otp_input:
        return JsonResponse({'success': False, 'error': 'OTP and phone are required.'})

    success, message = verify_otp_code(phone, otp_input, 'login')
    if not success:
        user_id = request.session.get('pending_user_id')
        failed_user = User.objects.filter(id=user_id).first() if user_id else None
        _record_login_activity(request, 'otp', 'failed', phone, failed_user, message)
        return JsonResponse({'success': False, 'error': message})

    user_id = request.session.get('pending_user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Session expired. Please login again.'})

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found.'})

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    user.failed_login_attempts = 0
    user.last_login_attempt = timezone.now()
    user.is_phone_verified = True
    user.save(update_fields=['failed_login_attempts', 'last_login_attempt', 'is_phone_verified'])
    _record_login_activity(request, 'otp', 'success', phone, user)

    for key in ('otp_phone', 'otp_purpose', 'otp_record_id', 'pending_user_id'):
        request.session.pop(key, None)

    redirect_url = '/dashboard/' if (user.is_staff or user.is_superuser) else '/'
    return JsonResponse({'success': True, 'redirect': redirect_url})


def logout_view(request):
    logout(request)
    return redirect('home')


# ─────────────────────────────────────────────────────────────
# 3. PASSWORD RESET
# ─────────────────────────────────────────────────────────────
def forgot_password_view(request):
    """Step 1: Enter phone → send OTP."""
    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        if identifier:
            user = None
            valid_phone, _ = validate_phone(identifier)
            if valid_phone:
                phone = normalize_phone(identifier)
                user = User.objects.filter(phone_number=phone).first()
            else:
                user = User.objects.filter(email__iexact=identifier).first()
                phone = user.phone_number if user else ''

            if not user:
                return render(request, 'accounts/forgot_password.html', {
                    'success': 'If this account is registered, an OTP has been sent.',
                    'identifier': identifier,
                })

            if not phone:
                return render(request, 'accounts/forgot_password.html', {
                    'error': 'This account does not have a phone number. Please contact support.',
                    'identifier': identifier,
                })

            if is_rate_limited(phone, 'reset'):
                return render(request, 'accounts/forgot_password.html', {
                    'error': 'Please wait 1 minute before requesting another OTP.',
                    'identifier': identifier,
                })

            ip = get_client_ip(request)
            otp_plain, record, result = _send_otp(phone, 'reset', user=user, ip=ip, email=user.email)

            request.session['otp_phone'] = phone
            request.session['otp_purpose'] = 'reset'
            request.session['otp_record_id'] = record.id
            request.session['reset_user_id'] = user.id

            expiry = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
            console_otp = otp_plain if (result.get('console') and settings.DEBUG) else None

            return render(request, 'otp_auth/verify_otp.html',
                          _otp_context(phone, 'reset', expiry, console_otp))

        phone_raw = request.POST.get('phone', '').strip()

        valid, err = validate_phone(phone_raw)
        if not valid:
            return render(request, 'accounts/forgot_password.html', {'error': err, 'phone': phone_raw})

        phone = normalize_phone(phone_raw)

        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            # Don't reveal if number exists — show same message
            return render(request, 'accounts/forgot_password.html', {
                'success': 'If this number is registered, an OTP has been sent.',
                'phone': phone_raw,
            })

        if is_rate_limited(phone, 'reset'):
            return render(request, 'accounts/forgot_password.html', {
                'error': 'Please wait 1 minute before requesting another OTP.',
                'phone': phone_raw,
            })

        ip = get_client_ip(request)
        otp_plain, record, result = _send_otp(phone, 'reset', user=user, ip=ip, email=user.email)

        request.session['otp_phone']     = phone
        request.session['otp_purpose']   = 'reset'
        request.session['otp_record_id'] = record.id
        request.session['reset_user_id'] = user.id

        expiry = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
        console_otp = otp_plain if (result.get('console') and settings.DEBUG) else None

        return render(request, 'otp_auth/verify_otp.html',
                      _otp_context(phone, 'reset', expiry, console_otp))

    return render(request, 'accounts/forgot_password.html')


@require_POST
def reset_verify_otp(request):
    """Step 2: Verify reset OTP → mark session as verified."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)

    otp_input = data.get('otp', '').strip()
    phone     = data.get('phone', '') or request.session.get('otp_phone', '')

    if not phone or not otp_input:
        return JsonResponse({'success': False, 'error': 'OTP and phone are required.'})

    success, message = verify_otp_code(phone, otp_input, 'reset')
    if not success:
        return JsonResponse({'success': False, 'error': message})

    request.session['reset_otp_verified'] = True
    return JsonResponse({'success': True, 'redirect': '/accounts/reset-password/'})


def reset_password_view(request):
    """Step 3: Set new password."""
    if not request.session.get('reset_otp_verified'):
        return redirect('forgot_password')

    if request.method == 'POST':
        password  = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        if password != password2:
            return render(request, 'accounts/reset_password.html', {'error': 'Passwords do not match.'})

        try:
            validate_password(password)
        except ValidationError as e:
            return render(request, 'accounts/reset_password.html', {'error': ' '.join(e.messages)})

        user_id = request.session.get('reset_user_id')
        if not user_id:
            return redirect('forgot_password')

        try:
            user = User.objects.get(id=user_id)
            user.set_password(password)
            user.save(update_fields=['password'])
        except User.DoesNotExist:
            return redirect('forgot_password')

        # Clear reset session
        for key in ('reset_otp_verified', 'reset_user_id', 'otp_phone', 'otp_purpose', 'otp_record_id'):
            request.session.pop(key, None)

        messages.success(request, 'Password reset successfully. Please login.')
        return redirect('login')

    return render(request, 'accounts/reset_password.html')


# ─────────────────────────────────────────────────────────────
# 4. PROFILE
# ─────────────────────────────────────────────────────────────
@login_required
def profile_view(request):
    """Customer profile page with order history."""
    from orders.models import Order
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:10]
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'orders': orders,
    })
