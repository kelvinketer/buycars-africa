import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "buycars_project.settings")
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(username='admin').exists():
    print("Creating superuser...")
    # You can change the password here if you want
    User.objects.create_superuser('admin', 'admin@buycars.africa', 'AdminPass123!')
    print("Superuser created!")
else:
    print("Superuser already exists.")
    