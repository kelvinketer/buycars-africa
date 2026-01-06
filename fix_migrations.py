import os
import django
from django.db import connection

# Setup Django context
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buycars_project.settings')
django.setup()

def fix():
    with connection.cursor() as cursor:
        print("Starting Final Database Rescue...")

        # 1. Clear Migration History
        # We need Django to "forget" it failed so it tries again from scratch.
        print("Resetting migration history...")
        cursor.execute("DELETE FROM django_migrations WHERE app IN ('cars', 'payments');")

        # 2. Fix 'SearchTerm' collision
        print("Dropping cars_searchterm table...")
        cursor.execute("DROP TABLE IF EXISTS cars_searchterm CASCADE;")

        # 3. Clear Payments (Prevent Foreign Key Crashes)
        print("Clearing old payment records...")
        cursor.execute("TRUNCATE TABLE payments_payment RESTART IDENTITY CASCADE;")

        # 4. PREP FOR DELETION: Add 'mileage_km' if missing
        print("Checking 'mileage_km'...")
        cursor.execute("SELECT count(*) FROM information_schema.columns WHERE table_name='cars_car' AND column_name='mileage_km';")
        if cursor.fetchone()[0] == 0:
            print("Adding dummy 'mileage_km'...")
            cursor.execute("ALTER TABLE cars_car ADD COLUMN mileage_km integer NULL;")

        # 5. PREP FOR ADDITION: Drop ALL conflicting columns
        # These are the columns currently blocking the migration. 
        # We drop them so Django can recreate them cleanly.
        conflicting_columns = [
            'body_type', 
            'color', 
            'condition', 
            'transmission', 
            'drive_type', 
            'fuel_type',
            'engine_size',
            'engine_size_cc',
            'is_available_for_rent',  # <--- THIS IS THE ONE BLOCKING YOU NOW
            'rent_price_per_day',
            'min_hire_days',
            'is_featured',
            'location',
            'vin',
            'description'
        ]

        print("Checking for conflicting columns...")
        for col in conflicting_columns:
            cursor.execute(f"SELECT count(*) FROM information_schema.columns WHERE table_name='cars_car' AND column_name='{col}';")
            if cursor.fetchone()[0] > 0:
                print(f"Column '{col}' exists. Dropping it to allow fresh migration...")
                cursor.execute(f"ALTER TABLE cars_car DROP COLUMN {col} CASCADE;")

        print("Cleanup successful. The path for Migration 0002 is now clear.")

if __name__ == "__main__":
    fix()