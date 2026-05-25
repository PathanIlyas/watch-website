from django.db import models
from django.conf import settings
from django.utils import timezone
from store.models import Watch


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    session_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart {self.id}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    watch = models.ForeignKey(Watch, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.watch.name}"


class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist'
    )
    watch = models.ForeignKey(Watch, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'watch')

    def __str__(self):
        return f"{self.user.username}'s wishlist: {self.watch.name}"


class Order(models.Model):
    # ── Full ecommerce tracking status flow ──────────────────────────
    STATUS_CHOICES = (
        ('Pending',          'Pending'),
        ('Confirmed',        'Order Confirmed'),
        ('Processing',       'Processing'),
        ('Packed',           'Packed'),
        ('Shipped',          'Shipped'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered',        'Delivered'),
        ('Cancelled',        'Cancelled'),
    )

    # Status → step index (for progress bar)
    STATUS_STEPS = {
        'Pending':          0,
        'Confirmed':        1,
        'Processing':       2,
        'Packed':           3,
        'Shipped':          4,
        'Out for Delivery': 5,
        'Delivered':        6,
        'Cancelled':        -1,
    }

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    first_name    = models.CharField(max_length=100)
    last_name     = models.CharField(max_length=100)
    email         = models.EmailField()
    phone         = models.CharField(max_length=20)
    address       = models.TextField()
    city          = models.CharField(max_length=100)
    state         = models.CharField(max_length=100, blank=True, null=True)
    postal_code   = models.CharField(max_length=20)
    country       = models.CharField(max_length=100)
    total_amount  = models.DecimalField(max_digits=10, decimal_places=2)
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    # Tracking extras
    tracking_number       = models.CharField(max_length=100, blank=True, null=True)
    courier_name          = models.CharField(max_length=100, blank=True, null=True)
    estimated_delivery    = models.DateField(blank=True, null=True)
    shipped_at            = models.DateTimeField(blank=True, null=True)
    delivered_at          = models.DateTimeField(blank=True, null=True)
    admin_notes           = models.TextField(blank=True, null=True)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} — {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_address(self):
        parts = [self.address, self.city]
        if self.state:
            parts.append(self.state)
        parts += [self.postal_code, self.country]
        return ', '.join(parts)

    @property
    def step(self):
        return self.STATUS_STEPS.get(self.status, 0)

    @property
    def is_cancelled(self):
        return self.status == 'Cancelled'


class OrderItem(models.Model):
    order    = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    watch    = models.ForeignKey(Watch, on_delete=models.CASCADE)
    price    = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.watch.name} in Order #{self.order.id}"

    @property
    def subtotal(self):
        return self.price * self.quantity


class OrderStatusHistory(models.Model):
    """Immutable log of every status change for an order."""
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='history')
    status     = models.CharField(max_length=30)
    note       = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Order #{self.order.id} → {self.status}"


class Payment(models.Model):
    order          = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=100)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    status         = models.CharField(max_length=50, default='Pending')
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} for Order #{self.order.id}"
