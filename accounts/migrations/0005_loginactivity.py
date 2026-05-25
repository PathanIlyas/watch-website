# Generated for CHRONOS dual authentication audit logging.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0004_customuser_created_at_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoginActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(blank=True, max_length=255)),
                ('method', models.CharField(choices=[('password', 'Password'), ('otp', 'OTP')], max_length=20)),
                ('status', models.CharField(choices=[('success', 'Success'), ('failed', 'Failed')], max_length=20)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=255)),
                ('message', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='login_activities', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Login Activity',
                'verbose_name_plural': 'Login Activities',
                'ordering': ['-created_at'],
            },
        ),
    ]
