from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    # Profile
    full_name           = models.CharField(max_length=200, blank=True, null=True)
    phone_number        = models.CharField(max_length=20, blank=True, null=True, unique=True)
    address             = models.TextField(blank=True, null=True)

    # Verification flags
    is_phone_verified   = models.BooleanField(default=False)
    is_email_verified   = models.BooleanField(default=False)
    is_customer         = models.BooleanField(default=True)
    is_dashboard_admin  = models.BooleanField(default=False)

    # Security
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    last_login_attempt    = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.username

    @property
    def display_name(self):
        return self.full_name or self.get_full_name() or self.username


class LoginActivity(models.Model):
    METHOD_CHOICES = (
        ('password', 'Password'),
        ('otp', 'OTP'),
    )

    STATUS_CHOICES = (
        ('success', 'Success'),
        ('failed', 'Failed'),
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='login_activities',
    )
    identifier = models.CharField(max_length=255, blank=True)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    message = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Login Activity'
        verbose_name_plural = 'Login Activities'

    def __str__(self):
        return f"{self.get_method_display()} {self.get_status_display()} - {self.identifier}"
