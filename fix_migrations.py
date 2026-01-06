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
        print("Resetting migration history...")
        cursor.execute("DELETE FROM django_migrations WHERE app IN ('cars', 'payments');")

        # 2. DROP CONFLICTING TABLES
        # This is the new fix: Drop the booking table that is blocking the deploy
        print("Dropping conflict tables (searchterm, booking)...")
        cursor.execute("DROP TABLE IF EXISTS cars_searchterm CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS cars_booking CASCADE;")  # <--- NEW ADDITION

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
        # We keep this list to ensure no column blocks us after the table is fixed
        conflicting_columns = [
            'body_type', 'color', 'condition', 'transmission', 
            'drive_type', 'fuel_type', 'engine_size', 'engine_size_cc',
            'is_available_for_rent', 'listing_type', 'rent_price_per_day',
            'min_hire_days', 'is_featured', 'location', 'vin', 
            'description', 'mileage', 'discount_price', 
            'registration_number', 'video_url', 'views_count', 'priority'
        ]

        print("Checking for conflicting columns...")
        for col in conflicting_columns:
            cursor.execute(f"SELECT count(*) FROM information_schema.columns WHERE table_name='cars_car' AND column_name='{col}';")
            if cursor.fetchone()[0] > 0:
                print(f"Column '{col}' exists. Dropping it to allow fresh migration...")
                cursor.execute(f"ALTER TABLE cars_car DROP COLUMN {col} CASCADE;")

        print("Cleanup successful. Ready for fresh migration.")

if __name__ == "__main__":
    fix()