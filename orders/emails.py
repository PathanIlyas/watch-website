"""
CHRONOS Luxury Watches — Centralised Email System
All branded HTML emails are built here and sent via Django's email backend.
"""
import logging
import threading
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

logger = logging.getLogger(__name__)

BRAND = 'CHRONOS'
GOLD  = '#D4AF37'
DARK  = '#0B0B0B'
CARD  = '#1A1A1A'
TEXT  = '#F5F5F5'
MUTED = '#A0A0A0'


# ─────────────────────────────────────────────────────────────────────────────
# Base HTML wrapper — every email shares this shell
# ─────────────────────────────────────────────────────────────────────────────
def _base(title: str, body_html: str) -> str:
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    year = timezone.now().year
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
</head>
<body style="margin:0;padding:0;background:{DARK};font-family:'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:{DARK};padding:40px 20px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

  <!-- HEADER -->
  <tr>
    <td align="center" style="padding:40px 0 30px;">
      <div style="font-size:32px;font-weight:900;letter-spacing:8px;color:{GOLD};
                  font-family:Georgia,serif;">{BRAND}</div>
      <div style="font-size:11px;letter-spacing:4px;color:{MUTED};margin-top:6px;
                  text-transform:uppercase;">Precision · Elegance · Legacy</div>
      <div style="width:60px;height:2px;background:{GOLD};margin:20px auto 0;"></div>
    </td>
  </tr>

  <!-- BODY CARD -->
  <tr>
    <td style="background:{CARD};border-radius:16px;border:1px solid rgba(212,175,55,0.2);
               padding:40px 40px 32px;box-shadow:0 20px 60px rgba(0,0,0,0.6);">
      {body_html}
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td align="center" style="padding:32px 0 20px;">
      <div style="color:{MUTED};font-size:12px;line-height:1.8;">
        <strong style="color:{GOLD};">{BRAND} Luxury Watches</strong><br>
        The Pinnacle of Horological Excellence<br>
        <a href="{site_url}" style="color:{GOLD};text-decoration:none;">{site_url}</a>
      </div>
      <div style="margin-top:16px;color:rgba(160,160,160,0.4);font-size:11px;">
        &copy; {year} {BRAND}. All rights reserved.
      </div>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Shared components
# ─────────────────────────────────────────────────────────────────────────────
def _btn(label: str, url: str) -> str:
    return f"""<div style="text-align:center;margin:28px 0;">
  <a href="{url}" style="display:inline-block;background:linear-gradient(135deg,{GOLD},{DARK});
     color:#000;font-weight:700;font-size:14px;letter-spacing:2px;text-transform:uppercase;
     text-decoration:none;padding:14px 36px;border-radius:8px;
     border:1px solid {GOLD};">{label}</a>
</div>"""


def _divider() -> str:
    return f'<div style="border-top:1px solid rgba(212,175,55,0.15);margin:24px 0;"></div>'


def _heading(text: str) -> str:
    return f'<h2 style="color:{TEXT};font-family:Georgia,serif;font-size:24px;margin:0 0 8px;">{text}</h2>'


def _subheading(text: str) -> str:
    return f'<p style="color:{MUTED};font-size:13px;letter-spacing:1px;text-transform:uppercase;margin:0 0 24px;">{text}</p>'


def _para(text: str) -> str:
    return f'<p style="color:{MUTED};font-size:15px;line-height:1.7;margin:0 0 16px;">{text}</p>'


def _badge(label: str, color: str = GOLD) -> str:
    return (f'<span style="display:inline-block;background:rgba(212,175,55,0.12);'
            f'color:{color};border:1px solid {color};border-radius:20px;'
            f'padding:4px 14px;font-size:12px;font-weight:600;">{label}</span>')


def _order_items_table(items) -> str:
    rows = ''
    for item in items:
        rows += f"""<tr>
          <td style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.05);
                     color:{TEXT};font-size:14px;">{item.watch.name}</td>
          <td style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.05);
                     color:{MUTED};font-size:14px;text-align:center;">x{item.quantity}</td>
          <td style="padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.05);
                     color:{GOLD};font-size:14px;text-align:right;font-weight:700;">
                     &#8377;{item.price}</td>
        </tr>"""
    return f"""<table width="100%" cellpadding="0" cellspacing="0" style="margin:16px 0;">
      <tr>
        <th style="color:{MUTED};font-size:11px;letter-spacing:1px;text-transform:uppercase;
                   padding-bottom:10px;text-align:left;border-bottom:1px solid rgba(212,175,55,0.2);">
                   Item</th>
        <th style="color:{MUTED};font-size:11px;letter-spacing:1px;text-transform:uppercase;
                   padding-bottom:10px;text-align:center;border-bottom:1px solid rgba(212,175,55,0.2);">
                   Qty</th>
        <th style="color:{MUTED};font-size:11px;letter-spacing:1px;text-transform:uppercase;
                   padding-bottom:10px;text-align:right;border-bottom:1px solid rgba(212,175,55,0.2);">
                   Price</th>
      </tr>
      {rows}
    </table>"""


def _info_row(label: str, value: str) -> str:
    return f"""<tr>
      <td style="color:{MUTED};font-size:13px;padding:8px 0;width:40%;">{label}</td>
      <td style="color:{TEXT};font-size:13px;padding:8px 0;font-weight:500;">{value}</td>
    </tr>"""


# ─────────────────────────────────────────────────────────────────────────────
# Core send helper
# ─────────────────────────────────────────────────────────────────────────────
def _send_sync(subject: str, to: str, html: str, text: str = '', reply_to: str = ''):
    """Send a single HTML email. Falls back to plain text (synchronous, run inside a thread)."""
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text or 'Please view this email in an HTML-capable client.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to],
            reply_to=[reply_to] if reply_to else [],
        )
        msg.attach_alternative(html, 'text/html')
        msg.send(fail_silently=False)
        logger.info('[EMAIL] Sent "%s" → %s', subject, to)
        return True
    except Exception as exc:
        logger.error('[EMAIL] Failed to send "%s" → %s: %s', subject, to, exc)
        return False


def _send(subject: str, to: str, html: str, text: str = '', reply_to: str = ''):
    """Asynchronously dispatch email in a background thread to prevent blocking HTTP requests."""
    thread = threading.Thread(target=_send_sync, args=(subject, to, html, text, reply_to))
    thread.daemon = True
    thread.start()
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 1. Order Confirmation
# ─────────────────────────────────────────────────────────────────────────────
def send_order_confirmation(order, items):
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    track_url = f"{site_url}/orders/track/?order_id={order.id}"

    body = f"""
    {_heading(f'Order Confirmed, {order.first_name}!')}
    {_subheading(f'Order #{order.id} · {order.created_at.strftime("%d %B %Y")}' if order.created_at else f'Order #{order.id}')}
    {_para('Thank you for choosing CHRONOS. Your order has been received and is being prepared with the utmost care.')}
    {_divider()}
    {_order_items_table(items)}
    {_divider()}
    <table width="100%" cellpadding="0" cellspacing="0">
      {_info_row('Order Total', f'&#8377;{order.total_amount}')}
      {_info_row('Shipping', 'Complimentary')}
      {_info_row('Shipping Address', order.full_address)}
      {_info_row('Payment Status', _badge('Confirmed'))}
    </table>
    {_divider()}
    {_btn('Track Your Order', track_url)}
    {_para('You will receive updates as your timepiece progresses through our fulfilment process.')}
    """
    html = _base(f'Order Confirmed — CHRONOS #{order.id}', body)
    _send(f'Your CHRONOS Order #{order.id} is Confirmed ✓', order.email, html)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Payment Success
# ─────────────────────────────────────────────────────────────────────────────
def send_payment_success(order, payment_id=''):
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    track_url = f"{site_url}/orders/track/?order_id={order.id}"

    body = f"""
    {_heading('Payment Successful')}
    {_subheading(f'Transaction confirmed for Order #{order.id}')}
    {_para(f'Dear {order.first_name}, your payment of <strong style="color:{GOLD};">&#8377;{order.total_amount}</strong> has been successfully processed.')}
    {_divider()}
    <table width="100%" cellpadding="0" cellspacing="0">
      {_info_row('Order ID', f'#{order.id}')}
      {_info_row('Amount Paid', f'&#8377;{order.total_amount}')}
      {_info_row('Payment ID', payment_id or '—')}
      {_info_row('Payment Method', 'Razorpay')}
      {_info_row('Status', _badge('Paid', '#28a745'))}
    </table>
    {_divider()}
    {_btn('View Order Details', track_url)}
    {_para('Your luxury timepiece is now being prepared for dispatch. Expect a shipping notification soon.')}
    """
    html = _base(f'Payment Confirmed — CHRONOS #{order.id}', body)
    _send(f'Payment Confirmed — CHRONOS Order #{order.id}', order.email, html)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Shipping Update
# ─────────────────────────────────────────────────────────────────────────────
def send_shipping_update(order):
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    track_url = f"{site_url}/orders/track/?order_id={order.id}"

    est = order.estimated_delivery.strftime('%d %B %Y') if order.estimated_delivery else 'Soon'
    courier = order.courier_name or 'Premium Courier'
    tracking_no = order.tracking_number or '—'

    body = f"""
    {_heading('Your Order Has Shipped!')}
    {_subheading(f'Order #{order.id} is on its way')}
    {_para(f'Dear {order.first_name}, your CHRONOS timepiece has been dispatched and is on its way to you.')}
    {_divider()}
    <table width="100%" cellpadding="0" cellspacing="0">
      {_info_row('Order ID', f'#{order.id}')}
      {_info_row('Courier', courier)}
      {_info_row('Tracking Number', tracking_no)}
      {_info_row('Estimated Delivery', est)}
      {_info_row('Shipping To', order.full_address)}
      {_info_row('Status', _badge('Shipped'))}
    </table>
    {_divider()}
    {_btn('Track Your Shipment', track_url)}
    {_para('Please ensure someone is available to receive the package. A signature may be required.')}
    """
    html = _base(f'Your CHRONOS Order #{order.id} Has Shipped', body)
    _send(f'Your CHRONOS Order #{order.id} Has Shipped 🚚', order.email, html)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Out for Delivery
# ─────────────────────────────────────────────────────────────────────────────
def send_out_for_delivery(order):
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    track_url = f"{site_url}/orders/track/?order_id={order.id}"

    body = f"""
    {_heading('Out for Delivery Today!')}
    {_subheading(f'Order #{order.id} arrives today')}
    {_para(f'Dear {order.first_name}, your CHRONOS timepiece is out for delivery and will arrive at your address today.')}
    {_divider()}
    <table width="100%" cellpadding="0" cellspacing="0">
      {_info_row('Order ID', f'#{order.id}')}
      {_info_row('Delivering To', order.full_address)}
      {_info_row('Status', _badge('Out for Delivery', '#17a2b8'))}
    </table>
    {_divider()}
    {_btn('Track Your Order', track_url)}
    {_para('Please be available to receive your package. A signature may be required upon delivery.')}
    """
    html = _base(f'CHRONOS Order #{order.id} — Out for Delivery', body)
    _send(f'Your CHRONOS Order #{order.id} is Out for Delivery 📦', order.email, html)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Delivered
# ─────────────────────────────────────────────────────────────────────────────
def send_delivered(order):
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    shop_url = f"{site_url}/collection/"

    body = f"""
    {_heading('Your Order Has Been Delivered!')}
    {_subheading(f'Order #{order.id} · Delivered')}
    {_para(f'Dear {order.first_name}, your CHRONOS luxury timepiece has been delivered. We hope you love it.')}
    {_divider()}
    <div style="text-align:center;padding:20px 0;">
      <div style="font-size:48px;">⌚</div>
      <p style="color:{GOLD};font-family:Georgia,serif;font-size:18px;margin:12px 0 4px;">
        Welcome to the CHRONOS Family
      </p>
      <p style="color:{MUTED};font-size:13px;">Precision. Elegance. Legacy.</p>
    </div>
    {_divider()}
    <table width="100%" cellpadding="0" cellspacing="0">
      {_info_row('Order ID', f'#{order.id}')}
      {_info_row('Delivered To', order.full_address)}
      {_info_row('Status', _badge('Delivered', '#28a745'))}
    </table>
    {_divider()}
    {_btn('Explore More Timepieces', shop_url)}
    {_para('If you have any questions or concerns about your order, please do not hesitate to contact our concierge team.')}
    """
    html = _base(f'CHRONOS Order #{order.id} Delivered', body)
    _send(f'Your CHRONOS Timepiece Has Been Delivered ✓', order.email, html)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Contact Confirmation (to customer)
# ─────────────────────────────────────────────────────────────────────────────
def send_contact_confirmation(name: str, email: str, subject: str):
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    body = f"""
    {_heading(f'Thank You, {name}!')}
    {_subheading('We have received your message')}
    {_para(f'Thank you for reaching out to CHRONOS. We have received your enquiry regarding <strong style="color:{TEXT};">"{subject}"</strong> and our concierge team will respond within 24 hours.')}
    {_divider()}
    <div style="background:rgba(212,175,55,0.06);border:1px solid rgba(212,175,55,0.15);
                border-radius:10px;padding:20px 24px;margin:16px 0;">
      <p style="color:{MUTED};font-size:13px;margin:0;">
        <strong style="color:{GOLD};">Reference:</strong> Your enquiry has been logged and assigned to our team.
        We typically respond within <strong style="color:{TEXT};">24 business hours</strong>.
      </p>
    </div>
    {_divider()}
    {_btn('Visit Our Collection', f'{site_url}/collection/')}
    {_para('In the meantime, feel free to explore our curated collection of luxury timepieces.')}
    """
    html = _base('Message Received — CHRONOS', body)
    _send(f'We received your message — CHRONOS', email, html)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Contact Admin Notification
# ─────────────────────────────────────────────────────────────────────────────
def send_contact_admin_notification(name: str, email: str, subject: str, message: str):
    admin_email = getattr(settings, 'ADMIN_EMAIL', '')
    if not admin_email:
        return

    body = f"""
    {_heading('New Contact Enquiry')}
    {_subheading('A customer has submitted a contact form')}
    {_divider()}
    <table width="100%" cellpadding="0" cellspacing="0">
      {_info_row('Name', name)}
      {_info_row('Email', f'<a href="mailto:{email}" style="color:{GOLD};text-decoration:none;">{email}</a>')}
      {_info_row('Subject', subject)}
    </table>
    {_divider()}
    <p style="color:{MUTED};font-size:13px;margin:0 0 8px;text-transform:uppercase;letter-spacing:1px;">Message</p>
    <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);
                border-radius:8px;padding:16px 20px;">
      <p style="color:{TEXT};font-size:14px;line-height:1.7;margin:0;">{message}</p>
    </div>
    {_divider()}
    <div style="text-align:center;margin:20px 0;">
      <a href="mailto:{email}?subject=Re: {subject}&body=Dear {name},%0A%0A"
         style="display:inline-block;background:linear-gradient(135deg,{GOLD},{DARK});
                color:#000;font-weight:700;font-size:14px;letter-spacing:2px;text-transform:uppercase;
                text-decoration:none;padding:14px 36px;border-radius:8px;border:1px solid {GOLD};">
        Reply to {name}
      </a>
    </div>
    <p style="color:{MUTED};font-size:12px;text-align:center;margin:0;">
      Clicking "Reply" in your email client will also reply directly to the customer.
    </p>
    """
    html = _base(f'New Enquiry from {name} — CHRONOS', body)
    # reply_to = customer email so admin can reply directly from inbox
    _send(f'[CHRONOS] New Contact: {subject}', admin_email, html, reply_to=email)


# ─────────────────────────────────────────────────────────────────────────────
# 8. Welcome Email (on registration)
# ─────────────────────────────────────────────────────────────────────────────
def send_welcome_email(user_email: str, first_name: str):
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    body = f"""
    {_heading(f'Welcome to CHRONOS, {first_name}!')}
    {_subheading('Your journey into luxury horology begins here')}
    {_para('You have joined an exclusive community of discerning collectors who appreciate the finest in Swiss watchmaking. Every CHRONOS timepiece is a masterpiece of precision engineering and artistic craftsmanship.')}
    {_divider()}
    <div style="text-align:center;padding:16px 0;">
      <div style="font-size:40px;margin-bottom:12px;">⌚</div>
      <p style="color:{GOLD};font-family:Georgia,serif;font-size:16px;margin:0;">
        Precision · Elegance · Legacy
      </p>
    </div>
    {_divider()}
    {_btn('Explore the Collection', f'{site_url}/collection/')}
    {_para('Discover our curated selection of luxury timepieces, from classic dress watches to sophisticated sports models.')}
    """
    html = _base('Welcome to CHRONOS', body)
    _send('Welcome to CHRONOS Luxury Watches', user_email, html)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Admin New Order Notification
# ─────────────────────────────────────────────────────────────────────────────
def send_admin_new_order(order, items):
    admin_email = getattr(settings, 'ADMIN_EMAIL', '')
    if not admin_email:
        return
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    dashboard_url = f"{site_url}/dashboard/orders/{order.id}/update/"

    body = f"""
    {_heading(f'New Order #{order.id}')}
    {_subheading(f'Placed by {order.full_name}')}
    {_divider()}
    <table width="100%" cellpadding="0" cellspacing="0">
      {_info_row('Customer', order.full_name)}
      {_info_row('Email', order.email)}
      {_info_row('Phone', order.phone)}
      {_info_row('Total', f'&#8377;{order.total_amount}')}
      {_info_row('Address', order.full_address)}
    </table>
    {_divider()}
    {_order_items_table(items)}
    {_divider()}
    {_btn('Manage Order in Dashboard', dashboard_url)}
    """
    html = _base(f'New Order #{order.id} — CHRONOS Admin', body)
    _send(f'[CHRONOS] New Order #{order.id} — ₹{order.total_amount}', admin_email, html)
