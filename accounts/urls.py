from django.urls import path
from . import views

urlpatterns = [
    # Standard login/logout
    path('login/',    views.login_view,    name='login'),
    path('logout/',   views.logout_view,   name='logout'),

    # Registration
    path('register/',            views.register_view,       name='register'),
    path('register/verify-otp/', views.register_verify_otp, name='register_verify_otp'),

    # Login 2FA OTP verify
    path('login/send-otp/', views.login_send_otp,   name='login_send_otp'),
    path('login/verify-otp/', views.login_verify_otp, name='login_verify_otp'),

    # Password reset
    path('forgot-password/',  views.forgot_password_view, name='forgot_password'),
    path('reset/verify-otp/', views.reset_verify_otp,     name='reset_verify_otp'),
    path('reset-password/',   views.reset_password_view,  name='reset_password'),

    # Profile
    path('profile/', views.profile_view, name='profile'),
]
