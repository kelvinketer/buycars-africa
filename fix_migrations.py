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

        # 2. Fix 'SearchTerm' collision (Drop it so Django can recreate it)
        print("Dropping cars_searchterm table...")
        cursor.execute("DROP TABLE IF EXISTS cars_searchterm CASCADE;")

        # 3. Fix 'Payment' foreign key issues
        print("Clearing old payment records...")
        cursor.execute("TRUNCATE TABLE payments_payment RESTART IDENTITY CASCADE;")

        # 4. THE TRICK: Add 'mileage_km' if missing
        # Django wants to delete this column in migration 0002. 
        # If it's already gone, we add a dummy version so Django doesn't crash.
        print("Checking schema for 'mileage_km'...")
        cursor.execute("""
            SELECT count(*) 
            FROM information_schema.columns 
            WHERE table_name='cars_car' AND column_name='mileage_km';
        """)
        exists = cursor.fetchone()[0]
        
        if not exists:
            print("Column 'mileage_km' missing. Adding dummy column to satisfy migration...")
            cursor.execute("ALTER TABLE cars_car ADD COLUMN mileage_km integer NULL;")
        else:
            print("Column 'mileage_km' found. Migration should proceed normally.")

        print("Cleanup successful. Ready for migration.")

if __name__ == "__main__":
    fix()