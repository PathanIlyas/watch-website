from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/send-otp/', views.checkout_send_otp, name='checkout_send_otp'),
    path('checkout/verify-otp/', views.checkout_verify_otp, name='checkout_verify_otp'),
    path('verify/', views.verify_payment, name='verify_payment'),
    path('failed-handler/', views.payment_failed, name='payment_failed'),
    path('success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('failed/', views.payment_failure, name='payment_failure'),
    path('webhook/', views.razorpay_webhook, name='razorpay_webhook'),
]
