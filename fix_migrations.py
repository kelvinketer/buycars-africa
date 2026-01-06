import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buycars_project.settings')
django.setup()

def fix():
    with connection.cursor() as cursor:
        print("Starting Comprehensive Database Cleanup...")

        # 1. Reset Migration History
        print("Resetting migration history...")
        cursor.execute("DELETE FROM django_migrations WHERE app IN ('cars', 'payments');")

        # 2. Drop Conflict Tables
        print("Dropping cars_searchterm table...")
        cursor.execute("DROP TABLE IF EXISTS cars_searchterm CASCADE;")

        # 3. Clear Payments (Prevent Foreign Key Crashes)
        print("Clearing old payment records...")
        cursor.execute("TRUNCATE TABLE payments_payment RESTART IDENTITY CASCADE;")

        # 4. PREP FOR DELETION: Add 'mileage_km' if missing
        # Django expects this to exist so it can delete it.
        print("Checking 'mileage_km'...")
        cursor.execute("SELECT count(*) FROM information_schema.columns WHERE table_name='cars_car' AND column_name='mileage_km';")
        if cursor.fetchone()[0] == 0:
            print("Adding dummy 'mileage_km'...")
            cursor.execute("ALTER TABLE cars_car ADD COLUMN mileage_km integer NULL;")

        # 5. PREP FOR ADDITION: Drop columns that shouldn't exist yet
        # These are the fields Migration 0002 tries to add. If they exist, the migration crashes.
        # We drop them so Django can recreate them cleanly.
        conflicting_columns = [
            'body_type', 
            'color', 
            'condition', 
            'transmission', 
            'drive_type', 
            'fuel_type',
            'engine_size', # Sometimes named engine_size_cc, checking generic
            'engine_size_cc'
        ]

        print("Checking for conflicting columns...")
        for col in conflicting_columns:
            cursor.execute(f"SELECT count(*) FROM information_schema.columns WHERE table_name='cars_car' AND column_name='{col}';")
            if cursor.fetchone()[0] > 0:
                print(f"Column '{col}' exists. Dropping it to allow fresh migration...")
                cursor.execute(f"ALTER TABLE cars_car DROP COLUMN {col};")

        print("Cleanup successful. Database is ready for migration 0002.")

if __name__ == "__main__":
    fix()