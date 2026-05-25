"""
CHRONOS OTP Delivery Service
─────────────────────────────
Priority order:
  1. Fast2SMS  (SMS to customer phone — needs ₹100 recharge on fast2sms.com)
  2. Twilio    (SMS to customer phone — needs Twilio account)
  3. Email OTP (sends OTP to customer email — works immediately, no cost)
  4. Console   (prints to terminal — dev only)

OTP is ALWAYS sent to the CUSTOMER's own phone/email.
Admin/developer number is NEVER used.
"""
import logging
import requests
from django.conf import settings
from django.core.mail import send_mail
from .models import SMSLog

logger = logging.getLogger(__name__)

OTP_MESSAGE = (
    "CHRONOS Verification Code: {otp}\n"
    "Valid for {minutes} minutes. Do not share this code with anyone."
)

OTP_EMAIL_SUBJECT = "CHRONOS — Your Verification Code"
OTP_EMAIL_BODY = """
Your CHRONOS verification code is:

  {otp}

This code is valid for {minutes} minutes.
Do not share this code with anyone.

— CHRONOS Luxury Watches
"""


def _log(phone, message, provider, status, response='', error='', purpose='otp'):
    try:
        SMSLog.objects.create(
            phone=phone, message=message, provider=provider,
            status=status, response=str(response)[:500],
            error=str(error)[:500], purpose=purpose,
        )
    except Exception as e:
        logger.error("SMSLog write failed: %s", e)


# ─────────────────────────────────────────────────────────────
# Fast2SMS — sends to CUSTOMER phone number
# ─────────────────────────────────────────────────────────────
def _send_fast2sms(phone: str, otp: str, minutes: int) -> dict:
    api_key = getattr(settings, 'FAST2SMS_API_KEY', '')
    if not api_key or api_key == 'your_fast2sms_api_key_here':
        return {'success': False, 'error': 'Fast2SMS API key not configured'}

    # Fast2SMS expects 10-digit number (strips +91)
    clean_phone = phone.lstrip('+').lstrip('91')[-10:]
    message = OTP_MESSAGE.format(otp=otp, minutes=minutes)

    try:
        resp = requests.post(
            'https://www.fast2sms.com/dev/bulkV2',
            json={
                'route': 'q',
                'message': message,
                'language': 'english',
                'flash': 0,
                'numbers': clean_phone,   # ← CUSTOMER's number, not admin
            },
            headers={'authorization': api_key, 'Content-Type': 'application/json'},
            timeout=10,
        )
        data = resp.json()
        if data.get('return') is True:
            _log(phone, message, 'fast2sms', 'sent', response=data)
            logger.info("[OTP] Fast2SMS → customer %s", phone)
            return {'success': True}
        else:
            err = str(data.get('message', data))
            _log(phone, message, 'fast2sms', 'failed', error=err)
            logger.warning("[OTP] Fast2SMS failed for %s: %s", phone, err)
            return {'success': False, 'error': err}
    except requests.Timeout:
        err = 'Fast2SMS timed out'
        _log(phone, message, 'fast2sms', 'failed', error=err)
        return {'success': False, 'error': err}
    except Exception as exc:
        _log(phone, message, 'fast2sms', 'failed', error=str(exc))
        return {'success': False, 'error': str(exc)}


# ─────────────────────────────────────────────────────────────
# Twilio — sends to CUSTOMER phone number
# ─────────────────────────────────────────────────────────────
def _send_twilio(phone: str, otp: str, minutes: int) -> dict:
    sid   = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_ = getattr(settings, 'TWILIO_PHONE_NUMBER', '')

    if not all([sid, token, from_]):
        return {'success': False, 'error': 'Twilio credentials not configured'}

    message = OTP_MESSAGE.format(otp=otp, minutes=minutes)
    try:
        resp = requests.post(
            f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json',
            data={'From': from_, 'To': phone, 'Body': message},  # ← CUSTOMER's number
            auth=(sid, token),
            timeout=10,
        )
        data = resp.json()
        if resp.status_code in (200, 201):
            _log(phone, message, 'twilio', 'sent', response=data)
            logger.info("[OTP] Twilio → customer %s", phone)
            return {'success': True}
        else:
            err = data.get('message', str(data))
            _log(phone, message, 'twilio', 'failed', error=err)
            return {'success': False, 'error': err}
    except Exception as exc:
        _log(phone, message, 'twilio', 'failed', error=str(exc))
        return {'success': False, 'error': str(exc)}


# ─────────────────────────────────────────────────────────────
# Email OTP — sends to CUSTOMER email (free, works immediately)
# Used as fallback when SMS provider is not yet activated
# ─────────────────────────────────────────────────────────────
def _send_email_otp(email: str, otp: str, minutes: int) -> dict:
    """Send OTP via email to the customer. Free fallback."""
    if not email:
        return {'success': False, 'error': 'No email address provided'}
    try:
        send_mail(
            subject=OTP_EMAIL_SUBJECT,
            message=OTP_EMAIL_BODY.format(otp=otp, minutes=minutes),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],   # ← CUSTOMER's email, not admin
            fail_silently=False,
        )
        _log(email, f'OTP:{otp}', 'email', 'sent', response='email_sent')
        logger.info("[OTP] Email OTP → customer %s", email)
        return {'success': True, 'via_email': True}
    except Exception as exc:
        _log(email, f'OTP:{otp}', 'email', 'failed', error=str(exc))
        logger.error("[OTP] Email OTP failed for %s: %s", email, exc)
        return {'success': False, 'error': str(exc)}


# ─────────────────────────────────────────────────────────────
# Console — dev only, prints OTP to terminal
# ─────────────────────────────────────────────────────────────
def _send_console(phone: str, otp: str, minutes: int) -> dict:
    message = OTP_MESSAGE.format(otp=otp, minutes=minutes)
    print(f"\n{'='*52}")
    print(f"  [CHRONOS OTP — CONSOLE MODE]")
    print(f"  Sending to : {phone}")
    print(f"  OTP Code   : {otp}")
    print(f"  Expires in : {minutes} minutes")
    print(f"{'='*52}\n")
    _log(phone, message, 'console', 'sent', response='console_output')
    return {'success': True, 'console': True}


# ─────────────────────────────────────────────────────────────
# Main dispatcher — always sends to CUSTOMER, never to admin
# ─────────────────────────────────────────────────────────────
def send_otp_sms(phone: str, otp: str, customer_email: str = '') -> dict:
    """
    Send OTP to the CUSTOMER's phone number (or email as fallback).

    Args:
        phone          : Customer's phone number (E.164 format, e.g. +919876543210)
        otp            : The 6-digit OTP code
        customer_email : Customer's email (used as fallback if SMS fails)

    Returns:
        dict with 'success' bool and optional 'via_email', 'console' flags
    """
    minutes  = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
    provider = getattr(settings, 'SMS_PROVIDER', 'console').lower()

    fast2sms_key = getattr(settings, 'FAST2SMS_API_KEY', '')
    twilio_sid   = getattr(settings, 'TWILIO_ACCOUNT_SID', '')

    # ── Try Fast2SMS ──────────────────────────────────────────
    if provider == 'fast2sms' and fast2sms_key and fast2sms_key != 'your_fast2sms_api_key_here':
        result = _send_fast2sms(phone, otp, minutes)
        if result['success']:
            return result
        # SMS failed — try email fallback
        logger.warning("[OTP] Fast2SMS failed (%s), trying email fallback", result.get('error'))
        if customer_email:
            email_result = _send_email_otp(customer_email, otp, minutes)
            if email_result['success']:
                return email_result
        # Last resort: console
        return _send_console(phone, otp, minutes)

    # ── Try Twilio ────────────────────────────────────────────
    if provider == 'twilio' and twilio_sid:
        result = _send_twilio(phone, otp, minutes)
        if result['success']:
            return result
        logger.warning("[OTP] Twilio failed (%s), trying email fallback", result.get('error'))
        if customer_email:
            email_result = _send_email_otp(customer_email, otp, minutes)
            if email_result['success']:
                return email_result
        return _send_console(phone, otp, minutes)

    # ── Email OTP (when SMS_PROVIDER=email) ───────────────────
    if provider == 'email' and customer_email:
        return _send_email_otp(customer_email, otp, minutes)

    # ── Console (dev default) ─────────────────────────────────
    return _send_console(phone, otp, minutes)
