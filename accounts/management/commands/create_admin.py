"""
Management command: create_admin
Reads ADMIN_USERNAME / ADMIN_EMAIL / ADMIN_PASSWORD from settings (sourced from .env)
and creates a superuser if one does not already exist.

Usage:
    python manage.py create_admin
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Auto-create superuser from .env credentials (idempotent — safe to run repeatedly)'

    def handle(self, *args, **options):
        User = get_user_model()

        username = (getattr(settings, 'ADMIN_USERNAME', 'admin') or 'admin').strip()
        email = (getattr(settings, 'ADMIN_EMAIL', 'admin@chronos.com') or 'admin@chronos.com').strip()
        password = (getattr(settings, 'ADMIN_PASSWORD', 'admin') or 'admin').strip()

        if not username or not password:
            self.stderr.write(self.style.ERROR(
                'ADMIN_USERNAME and ADMIN_PASSWORD must be set in .env'
            ))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(
                f'Admin user "{username}" already exists — skipping creation.'
            ))
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        # Also mark as dashboard admin
        user.is_dashboard_admin = True
        user.save(update_fields=['is_dashboard_admin'])

        self.stdout.write(self.style.SUCCESS(
            f'✓ Superuser "{username}" created successfully.'
        ))
