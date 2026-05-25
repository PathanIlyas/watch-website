"""
Razorpay utility functions.
Centralises all SDK interactions so views stay clean.
"""
import hmac
import hashlib
import razorpay
from django.conf import settings


def get_razorpay_client():
    """Return an authenticated Razorpay client."""
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


def create_razorpay_order(amount_inr: float, receipt: str, notes: dict = None):
    """
    Create a Razorpay order.

    :param amount_inr: Amount in INR (will be converted to paise).
    :param receipt:    Unique receipt string (e.g. "order_<pk>").
    :param notes:      Optional dict of extra metadata.
    :return:           Razorpay order dict on success, None on failure.
    """
    client = get_razorpay_client()
    amount_paise = int(float(amount_inr) * 100)  # Razorpay expects paise
    payload = {
        'amount': amount_paise,
        'currency': 'INR',
        'receipt': receipt,
        'payment_capture': 1,  # Auto-capture
        'notes': notes or {},
    }
    try:
        return client.order.create(data=payload)
    except Exception as exc:
        print(f"[Razorpay] Order creation failed: {exc}")
        return None


def verify_razorpay_signature(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> bool:
    """
    Verify the HMAC-SHA256 signature returned by Razorpay after payment.

    Returns True if the signature is valid, False otherwise.
    """
    key_secret = settings.RAZORPAY_KEY_SECRET.encode('utf-8')
    message = f"{razorpay_order_id}|{razorpay_payment_id}".encode('utf-8')
    generated = hmac.new(key_secret, message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(generated, razorpay_signature)


def fetch_razorpay_payment(razorpay_payment_id: str):
    """Fetch payment details from Razorpay API."""
    client = get_razorpay_client()
    try:
        return client.payment.fetch(razorpay_payment_id)
    except Exception as exc:
        print(f"[Razorpay] Fetch payment failed: {exc}")
        return None
