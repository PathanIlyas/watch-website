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
from django.core.mail import EmailMultiAlternatives
from .models import SMSLog

logger = logging.getLogger(__name__)

OTP_MESSAGE = (
    "CHRONOS Verification Code: {otp}\n"
    "Valid for {minutes} minutes. Do not share this code with anyone."
)

OTP_EMAIL_SUBJECT = "CHRONOS — Your Verification Code"

# ── Luxury HTML OTP Email ─────────────────────────────────────────────
def _build_otp_email_html(otp: str, minutes: int) -> str:
    year = __import__('datetime').datetime.now().year
    digits = ''.join(
        f'<td style="padding:0 6px;"><div style="'
        f'width:52px;height:64px;background:#1A1A1A;border:2px solid #D4AF37;'
        f'border-radius:10px;display:inline-block;text-align:center;'
        f'line-height:64px;font-size:28px;font-weight:700;color:#D4AF37;'
        f'font-family:Georgia,serif;letter-spacing:0;">{d}</div></td>'
        for d in str(otp)
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CHRONOS — Verification Code</title>
</head>
<body style="margin:0;padding:0;background:#0B0B0B;font-family:'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0B0B0B;padding:40px 20px;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;">

  <!-- HEADER -->
  <tr>
    <td align="center" style="padding:40px 0 30px;">
      <div style="font-size:34px;font-weight:900;letter-spacing:10px;color:#D4AF37;
                  font-family:Georgia,serif;">CHRONOS</div>
      <div style="font-size:11px;letter-spacing:4px;color:#666;margin-top:6px;
                  text-transform:uppercase;">Precision · Elegance · Legacy</div>
      <div style="width:60px;height:2px;background:#D4AF37;margin:18px auto 0;opacity:.7;"></div>
    </td>
  </tr>

  <!-- CARD -->
  <tr>
    <td style="background:#1A1A1A;border-radius:18px;border:1px solid rgba(212,175,55,0.25);
               padding:44px 40px 36px;box-shadow:0 20px 60px rgba(0,0,0,0.7);">

      <!-- Icon -->
      <div style="text-align:center;margin-bottom:24px;">
        <div style="display:inline-block;width:64px;height:64px;border-radius:50%;
                    background:rgba(212,175,55,0.1);border:2px solid rgba(212,175,55,0.3);
                    line-height:64px;font-size:28px;">🔐</div>
      </div>

      <!-- Title -->
      <h2 style="color:#F5F5F5;font-family:Georgia,serif;font-size:24px;
                 text-align:center;margin:0 0 8px;">Verification Code</h2>
      <p style="color:#888;font-size:14px;text-align:center;margin:0 0 32px;line-height:1.6;">
        Use the code below to verify your identity.<br>
        Do <strong style="color:#F5F5F5;">not</strong> share this code with anyone.
      </p>

      <!-- OTP Digits -->
      <div style="text-align:center;margin:0 0 28px;">
        <table cellpadding="0" cellspacing="0" style="display:inline-table;">
          <tr>{digits}</tr>
        </table>
      </div>

      <!-- Divider -->
      <div style="border-top:1px solid rgba(255,255,255,0.07);margin:28px 0;"></div>

      <!-- Expiry info -->
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="background:rgba(212,175,55,0.07);border:1px solid rgba(212,175,55,0.15);
                     border-radius:10px;padding:16px 20px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="width:32px;vertical-align:top;padding-top:2px;">
                  <span style="font-size:18px;">⏱</span>
                </td>
                <td style="padding-left:10px;">
                  <p style="color:#D4AF37;font-size:13px;font-weight:600;margin:0 0 3px;">
                    Expires in {minutes} minutes
                  </p>
                  <p style="color:#888;font-size:12px;margin:0;line-height:1.5;">
                    This code is single-use and will expire automatically.
                    If you did not request this, please ignore this email.
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>

      <!-- Divider -->
      <div style="border-top:1px solid rgba(255,255,255,0.07);margin:28px 0;"></div>

      <!-- Security note -->
      <p style="color:#555;font-size:12px;text-align:center;margin:0;line-height:1.7;">
        🔒 &nbsp;CHRONOS will <strong style="color:#888;">never</strong> ask for your OTP
        via phone call, chat, or email reply.<br>
        If you did not initiate this request, contact us immediately.
      </p>

    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td align="center" style="padding:28px 0 16px;">
      <div style="color:#444;font-size:12px;line-height:1.8;">
        <strong style="color:#D4AF37;">CHRONOS Luxury Watches</strong><br>
        The Pinnacle of Horological Excellence
      </div>
      <div style="margin-top:14px;color:rgba(100,100,100,0.5);font-size:11px;">
        &copy; {year} CHRONOS. All rights reserved.
      </div>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def _build_otp_email_text(otp: str, minutes: int) -> str:
    return (
        f"CHRONOS — Verification Code\n"
        f"{'='*40}\n\n"
        f"Your verification code is:  {otp}\n\n"
        f"Valid for {minutes} minutes.\n"
        f"Do not share this code with anyone.\n\n"
        f"— CHRONOS Luxury Watches\n"
    )


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
    """Send luxury HTML OTP email to the customer."""
    if not email:
        return {'success': False, 'error': 'No email address provided'}
    try:
        html_body = _build_otp_email_html(otp, minutes)
        text_body = _build_otp_email_text(otp, minutes)

        msg = EmailMultiAlternatives(
            subject=OTP_EMAIL_SUBJECT,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)

        _log(email, f'OTP:{otp}', 'email', 'sent', response='html_email_sent')
        logger.info("[OTP] HTML Email OTP → customer %s", email)
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
