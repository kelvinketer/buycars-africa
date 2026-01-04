import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buycars_project.settings')
django.setup()

def fix():
    with connection.cursor() as cursor:
        print("Cleaning up inconsistent migration history...")
        # This removes the history for cars and payments so they can be re-applied cleanly
        cursor.execute("DELETE FROM django_migrations WHERE app = 'cars' OR app = 'payments';")
        print("Cleanup successful.")

if __name__ == "__main__":
    fix()