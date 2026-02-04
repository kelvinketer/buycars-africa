from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_admin(apps, schema_editor):
    User = apps.get_model('users', 'User')  # Replace 'users' with your auth app label if different
    if not User.objects.filter(username="admin").exists():
        User.objects.create(
            username="admin",
            email="admin@buycars.africa",
            password=make_password("admin123"), # Sets password to 'admin123'
            is_superuser=True,
            is_staff=True,
            is_active=True
        )

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'), # Ensure this points to a valid previous migration
    ]

    operations = [
        migrations.RunPython(create_admin),
    ]
    