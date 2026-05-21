from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    is_customer = models.BooleanField(default=True)
    is_dashboard_admin = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username
