import os
import django
from django.db import connection

# Setup Django context
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buycars_project.settings')
django.setup()

def fix():
    with connection.cursor() as cursor:
        print("Starting FINAL Database Rescue...")

        # 1. Clear Migration History
        print("Resetting migration history...")
        cursor.execute("DELETE FROM django_migrations WHERE app IN ('cars', 'payments');")

        # 2. DROP ALL AUXILIARY TABLES (The "Zombie Tables")
        # We drop these so Django can recreate them fresh.
        tables_to_drop = [
            'cars_searchterm',
            'cars_booking',
            'cars_carview',   # <--- THE CURRENT ERROR
            'cars_carimage',  # <--- PROACTIVE: Drop images table if it exists
            'cars_feature',   # <--- PROACTIVE: Drop features table if it exists
        ]
        
        print("Dropping auxiliary tables...")
        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")

        # 3. Clear Payments (Prevent Foreign Key Crashes)
        print("Clearing old payment records...")
        cursor.execute("TRUNCATE TABLE payments_payment RESTART IDENTITY CASCADE;")

        # 4. PREP cars_car: Add 'mileage_km' if missing
        print("Checking 'mileage_km'...")
        cursor.execute("SELECT count(*) FROM information_schema.columns WHERE table_name='cars_car' AND column_name='mileage_km';")
        if cursor.fetchone()[0] == 0:
            print("Adding dummy 'mileage_km'...")
            cursor.execute("ALTER TABLE cars_car ADD COLUMN mileage_km integer NULL;")

        # 5. PREP cars_car: Drop ALL conflicting columns
        # This list removes any column that might block the migration.
        conflicting_columns = [
            'body_type', 'color', 'condition', 'transmission', 
            'drive_type', 'fuel_type', 'engine_size', 'engine_size_cc',
            'is_available_for_rent', 'listing_type', 'rent_price_per_day',
            'min_hire_days', 'is_featured', 'location', 'vin', 
            'description', 'mileage', 'discount_price', 
            'registration_number', 'video_url', 'views_count', 'priority'
        ]

        print("Checking for conflicting columns in cars_car...")
        for col in conflicting_columns:
            cursor.execute(f"SELECT count(*) FROM information_schema.columns WHERE table_name='cars_car' AND column_name='{col}';")
            if cursor.fetchone()[0] > 0:
                print(f"Column '{col}' exists. Dropping it to allow fresh migration...")
                cursor.execute(f"ALTER TABLE cars_car DROP COLUMN {col} CASCADE;")

        print("Cleanup successful. Ready for fresh migration.")

if __name__ == "__main__":
    fix()