import os
import django
from django.db import connection

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "buycars_project.settings")
django.setup()

print("⚠️ STARTING DATABASE WIPE...")

# Connect to the database and delete all tables (Schema Reset)
with connection.cursor() as cursor:
    cursor.execute("DROP SCHEMA public CASCADE;")
    cursor.execute("CREATE SCHEMA public;")

print("✅ DATABASE WIPED SUCCESSFULLY. READY FOR NEW MIGRATIONS.")