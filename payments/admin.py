from django.contrib import admin
from .models import RazorpayPayment


@admin.register(RazorpayPayment)
class RazorpayPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'razorpay_order_id', 'razorpay_payment_id',
        'order', 'amount', 'currency', 'status', 'created_at',
    )
    list_filter = ('status', 'currency', 'payment_method')
    search_fields = ('razorpay_order_id', 'razorpay_payment_id', 'order__email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
