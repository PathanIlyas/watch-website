from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, LoginActivity


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 'email', 'phone_number', 'is_phone_verified',
        'failed_login_attempts', 'is_staff', 'date_joined',
    )
    search_fields = ('username', 'email', 'phone_number', 'full_name')
    list_filter = ('is_phone_verified', 'is_staff', 'is_active')


@admin.register(LoginActivity)
class LoginActivityAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'user', 'method', 'status', 'ip_address', 'created_at')
    list_filter = ('method', 'status', 'created_at')
    search_fields = ('identifier', 'user__username', 'user__email', 'ip_address')
    readonly_fields = ('created_at',)
