from django.urls import path
from . import views

urlpatterns = [
    path('send/',   views.send_otp_view,   name='otp_send'),
    path('verify/', views.verify_otp_view, name='otp_verify'),
    path('resend/', views.resend_otp_view, name='otp_resend'),
    path('status/', views.otp_status_view, name='otp_status'),
]
