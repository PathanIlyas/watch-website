from django.contrib import admin
from .models import OTPVerification, SMSLog


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display  = ('phone', 'purpose', 'status', 'attempts', 'created_at', 'expires_at')
    list_filter   = ('status', 'purpose')
    search_fields = ('phone',)
    readonly_fields = ('otp_hash', 'created_at', 'verified_at')
    ordering = ('-created_at',)


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display  = ('phone', 'provider', 'status', 'purpose', 'created_at')
    list_filter   = ('status', 'provider', 'purpose')
    search_fields = ('phone',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
