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
