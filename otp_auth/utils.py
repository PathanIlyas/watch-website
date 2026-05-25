"""
OTP utility functions — generation, validation, rate limiting.
"""
import random
import re
import logging
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────
OTP_LENGTH       = 6
MAX_ATTEMPTS     = getattr(settings, 'OTP_MAX_ATTEMPTS', 5)
EXPIRY_MINUTES   = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
RATE_LIMIT_MINS  = getattr(settings, 'OTP_RATE_LIMIT_MINUTES', 1)


def generate_otp() -> str:
    """Generate a cryptographically random 6-digit OTP."""
    return str(random.SystemRandom().randint(100000, 999999))


def normalize_phone(phone: str) -> str:
    """
    Normalize phone to E.164 format (+91XXXXXXXXXX for India).
    Accepts: 9876543210 / 09876543210 / +919876543210 / 919876543210
    """
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 10:
        return f'+91{digits}'
    if len(digits) == 11 and digits.startswith('0'):
        return f'+91{digits[1:]}'
    if len(digits) == 12 and digits.startswith('91'):
        return f'+{digits}'
    if len(digits) == 13 and digits.startswith('91'):
        return f'+{digits}'
    if phone.startswith('+'):
        return phone
    return f'+{digits}'


def validate_phone(phone: str) -> tuple[bool, str]:
    """
    Returns (is_valid, error_message).
    Validates Indian mobile numbers (10 digits starting with 6-9).
    """
    digits = re.sub(r'\D', '', phone)
    # Strip country code
    if digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]
    if digits.startswith('0') and len(digits) == 11:
        digits = digits[1:]

    if len(digits) != 10:
        return False, 'Phone number must be 10 digits.'
    if not digits[0] in '6789':
        return False, 'Enter a valid Indian mobile number.'
    return True, ''


def create_otp_record(phone: str, purpose: str = 'login', user=None, ip: str = None):
    """
    Invalidate any existing pending OTPs for this phone+purpose,
    then create a fresh OTP record. Returns (otp_plain, record).
    """
    from .models import OTPVerification

    # Expire old records for this phone+purpose
    OTPVerification.objects.filter(
        phone=phone, purpose=purpose, status='pending'
    ).update(status='expired')

    otp_plain = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=EXPIRY_MINUTES)

    record = OTPVerification.objects.create(
        user=user,
        phone=phone,
        otp_hash=OTPVerification.hash_otp(otp_plain),
        purpose=purpose,
        status='pending',
        expires_at=expires_at,
        ip_address=ip,
    )
    return otp_plain, record


def verify_otp_code(phone: str, otp_input: str, purpose: str = 'login') -> tuple[bool, str]:
    """
    Verify OTP for a phone+purpose.
    Returns (success, message).
    """
    from .models import OTPVerification

    try:
        record = OTPVerification.objects.filter(
            phone=phone, purpose=purpose, status='pending'
        ).latest('created_at')
    except OTPVerification.DoesNotExist:
        return False, 'No active OTP found. Please request a new one.'

    if record.is_expired:
        record.status = 'expired'
        record.save(update_fields=['status'])
        return False, 'OTP has expired. Please request a new one.'

    if record.is_blocked:
        return False, 'Too many incorrect attempts. Please request a new OTP.'

    if not record.check_otp(otp_input.strip()):
        record.increment_attempts()
        remaining = MAX_ATTEMPTS - record.attempts
        if remaining > 0:
            return False, f'Incorrect OTP. {remaining} attempt(s) remaining.'
        return False, 'Too many incorrect attempts. Please request a new OTP.'

    record.mark_verified()
    return True, 'OTP verified successfully.'


def is_rate_limited(phone: str, purpose: str = 'login') -> bool:
    """
    Returns True if a new OTP was sent within the last RATE_LIMIT_MINS minutes.
    Prevents OTP spam.
    """
    from .models import OTPVerification
    cutoff = timezone.now() - timedelta(minutes=RATE_LIMIT_MINS)
    return OTPVerification.objects.filter(
        phone=phone, purpose=purpose, created_at__gte=cutoff
    ).exists()


def get_client_ip(request) -> str:
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')
