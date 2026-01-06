import os
import django
from django.db import connection
from django.core.management import call_command

# 1. Setup Django Context
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buycars_project.settings')
django.setup()

def fix_and_deploy():
    print("🚀 STARTING AUTO-DEPLOYMENT SCRIPT...")

    with connection.cursor() as cursor:
        # --- PHASE 1: DATABASE CLEANUP ---
        print("\n[1/3] Cleaning 'Zombie' Tables & Columns...")

        # A. Reset Migration History
        cursor.execute("DELETE FROM django_migrations WHERE app IN ('cars', 'payments');")

        # B. Drop Auxiliary Tables (These block migration 0001/0002)
        # We drop these so Django can recreate them fresh.
        aux_tables = [
            'cars_searchterm', 'cars_booking', 'cars_carview', 
            'cars_carimage', 'cars_feature'
        ]
        for table in aux_tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")

        # C. Clear Payments (To prevent ForeignKey crashes)
        cursor.execute("TRUNCATE TABLE payments_payment RESTART IDENTITY CASCADE;")

        # D. PREP cars_car: Ensure 'mileage_km' exists (so Migration 0002 can delete it)
        cursor.execute("SELECT count(*) FROM information_schema.columns WHERE table_name='cars_car' AND column_name='mileage_km';")
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE cars_car ADD COLUMN mileage_km integer NULL;")

        # E. PREP cars_car: Drop ALL conflicting new columns (so Migration 0002 can add them)
        # This prevents "Column already exists" errors.
        conflicting_columns = [
            'body_type', 'listing_type', 'color', 'condition', 'transmission', 
            'drive_type', 'fuel_type', 'engine_size', 'engine_size_cc',
            'is_available_for_rent', 'rent_price_per_day', 'min_hire_days', 
            'is_featured', 'location', 'vin', 'description', 'mileage', 
            'discount_price', 'registration_number', 'video_url', 'views_count', 'priority'
        ]
        for col in conflicting_columns:
            cursor.execute(f"SELECT count(*) FROM information_schema.columns WHERE table_name='cars_car' AND column_name='{col}';")
            if cursor.fetchone()[0] > 0:
                print(f"   - Dropping column: {col}")
                cursor.execute(f"ALTER TABLE cars_car DROP COLUMN {col} CASCADE;")

    # --- PHASE 2: EXECUTE MIGRATION ---
    print("\n[2/3] Applying Migrations with --fake-initial...")
    try:
        # This is the MAGIC command. It forces the flag directly in Python.
        call_command('migrate', fake_initial=True)
        print("✅ Migration Successful!")
    except Exception as e:
        print(f"❌ Migration Failed: {e}")
        raise e

    print("\n[3/3] Deployment Logic Complete.")

if __name__ == "__main__":
    fix_and_deploy()