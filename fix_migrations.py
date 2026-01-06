import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buycars_project.settings')
django.setup()

def fix():
    with connection.cursor() as cursor:
        print("Starting Database Cleanup & Prep...")

        # 1. Clear Migration History (Crucial)
        print("Resetting migration history...")
        cursor.execute("DELETE FROM django_migrations WHERE app IN ('cars', 'payments');")

        # 2. Fix 'SearchTerm' collision
        print("Dropping cars_searchterm table...")
        cursor.execute("DROP TABLE IF EXISTS cars_searchterm CASCADE;")

        # 3. Fix 'Payment' foreign key issues
        print("Clearing old payment records...")
        cursor.execute("TRUNCATE TABLE payments_payment RESTART IDENTITY CASCADE;")

        # 4. FIX MILEAGE_KM (Must EXIST for migration to delete it)
        print("Checking schema for 'mileage_km'...")
        cursor.execute("SELECT count(*) FROM information_schema.columns WHERE table_name='cars_car' AND column_name='mileage_km';")
        if cursor.fetchone()[0] == 0:
            print("Column 'mileage_km' missing. Adding dummy column...")
            cursor.execute("ALTER TABLE cars_car ADD COLUMN mileage_km integer NULL;")

        # 5. FIX BODY_TYPE (Must NOT EXIST for migration to add it)
        print("Checking schema for 'body_type'...")
        cursor.execute("SELECT count(*) FROM information_schema.columns WHERE table_name='cars_car' AND column_name='body_type';")
        if cursor.fetchone()[0] > 0:
            print("Column 'body_type' exists. Dropping it to allow fresh migration...")
            cursor.execute("ALTER TABLE cars_car DROP COLUMN body_type;")

        print("Cleanup successful. Ready for migration.")

if __name__ == "__main__":
    fix()