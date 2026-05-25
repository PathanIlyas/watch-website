from django.db import models
from django.conf import settings
from orders.models import Order


class RazorpayPayment(models.Model):
    """Stores Razorpay-specific payment details linked to an Order."""

    PAYMENT_STATUS_CHOICES = (
        ('created', 'Created'),
        ('attempted', 'Attempted'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='razorpay_payments',
    )
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='razorpay_payment',
    )
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    payment_method = models.CharField(max_length=50, default='razorpay')
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Razorpay Payment'
        verbose_name_plural = 'Razorpay Payments'

    def __str__(self):
        return f"Payment {self.razorpay_order_id} — {self.status}"
