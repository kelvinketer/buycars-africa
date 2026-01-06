import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buycars_project.settings')
django.setup()

def fix():
    with connection.cursor() as cursor:
        print("Starting Comprehensive Database Cleanup...")

        # 1. Reset Migration History
        # We tell Django to forget previous attempts so it can run the migration fresh.
        print("Resetting migration history...")
        cursor.execute("DELETE FROM django_migrations WHERE app IN ('cars', 'payments');")

        # 2. Drop Conflict Tables
        print("Dropping cars_searchterm table...")
        cursor.execute("DROP TABLE IF EXISTS cars_searchterm CASCADE;")

        # 3. Clear Payments (Prevent Foreign Key Crashes)
        print("Clearing old payment records...")
        cursor.execute("TRUNCATE TABLE payments_payment RESTART IDENTITY CASCADE;")

        # 4. PREP FOR DELETION: Add 'mileage_km' if missing
        # Django wants to delete this column. If it's already gone, we add a dummy so Django doesn't crash.
        print("Checking 'mileage_km'...")
        cursor.execute("SELECT count(*) FROM information_schema.columns WHERE table_name='cars_car' AND column_name='mileage_km';")
        if cursor.fetchone()[0] == 0:
            print("Adding dummy 'mileage_km'...")
            cursor.execute("ALTER TABLE cars_car ADD COLUMN mileage_km integer NULL;")

        # 5. PREP FOR ADDITION: Drop ALL potentially conflicting columns
        # We drop these so Django can recreate them cleanly during the migration.
        # This covers every column likely involved in your recent updates.
        conflicting_columns = [
            'body_type', 
            'color', 
            'condition', 
            'transmission', 
            'drive_type', 
            'fuel_type',
            'engine_size',
            'engine_size_cc',
            'is_available_for_rent',  # The one causing your current error
            'is_featured',            # Likely next error
            'location',               # Likely next error
            'vin',                    # Likely next error
            'description'             # Often modified
        ]

        print("Checking for conflicting columns...")
        for col in conflicting_columns:
            # Check if column exists
            cursor.execute(f"SELECT count(*) FROM information_schema.columns WHERE table_name='cars_car' AND column_name='{col}';")
            if cursor.fetchone()[0] > 0:
                print(f"Column '{col}' exists. Dropping it to allow fresh migration...")
                # We use CASCADE to handle any dependencies automatically
                cursor.execute(f"ALTER TABLE cars_car DROP COLUMN {col} CASCADE;")

        print("Cleanup successful. Database is ready for migration 0002.")

if __name__ == "__main__":
    fix()