from accounts.models import CustomUser

try:
    user = CustomUser.objects.get(username='admin')
    user.set_password('admin123')
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print("Password for 'admin' has been reset to 'admin123'")
except CustomUser.DoesNotExist:
    user = CustomUser.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Superuser 'admin' created with password 'admin123'")
