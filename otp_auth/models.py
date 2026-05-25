import hashlib
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class OTPVerification(models.Model):
    """Stores one active OTP record per phone number."""

    PURPOSE_CHOICES = (
        ('login',     'Login'),
        ('register',  'Registration'),
        ('reset',     'Password Reset'),
        ('checkout',  'Checkout Verification'),
        ('mobile',    'Mobile Verification'),
    )

    STATUS_CHOICES = (
        ('pending',  'Pending'),
        ('verified', 'Verified'),
        ('expired',  'Expired'),
        ('blocked',  'Blocked'),
    )

    user         = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=True, blank=True, related_name='otp_records'
    )
    phone        = models.CharField(max_length=15)
    # Store hashed OTP — never plain text
    otp_hash     = models.CharField(max_length=64)
    purpose      = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='login')
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    attempts     = models.PositiveSmallIntegerField(default=0)
    created_at   = models.DateTimeField(auto_now_add=True)
    expires_at   = models.DateTimeField()
    verified_at  = models.DateTimeField(null=True, blank=True)
    ip_address   = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'OTP Verification'
        verbose_name_plural = 'OTP Verifications'

    def __str__(self):
        return f"{self.phone} [{self.purpose}] — {self.status}"

    # ── Helpers ──────────────────────────────────────────────
    @staticmethod
    def hash_otp(otp: str) -> str:
        return hashlib.sha256(otp.encode()).hexdigest()

    def check_otp(self, otp: str) -> bool:
        return self.otp_hash == self.hash_otp(otp)

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_blocked(self) -> bool:
        max_attempts = getattr(settings, 'OTP_MAX_ATTEMPTS', 5)
        return self.attempts >= max_attempts

    def mark_verified(self):
        self.status = 'verified'
        self.verified_at = timezone.now()
        self.save(update_fields=['status', 'verified_at'])

    def increment_attempts(self):
        self.attempts += 1
        max_attempts = getattr(settings, 'OTP_MAX_ATTEMPTS', 5)
        if self.attempts >= max_attempts:
            self.status = 'blocked'
        self.save(update_fields=['attempts', 'status'])


class SMSLog(models.Model):
    """Audit log for every SMS send attempt."""

    STATUS_CHOICES = (
        ('sent',    'Sent'),
        ('failed',  'Failed'),
        ('pending', 'Pending'),
    )

    phone      = models.CharField(max_length=15)
    message    = models.TextField()
    provider   = models.CharField(max_length=50, default='fast2sms')
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    response   = models.TextField(blank=True, null=True)
    error      = models.TextField(blank=True, null=True)
    purpose    = models.CharField(max_length=20, default='otp')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'SMS Log'
        verbose_name_plural = 'SMS Logs'

    def __str__(self):
        return f"{self.phone} [{self.status}] {self.created_at:%d %b %Y %H:%M}"
