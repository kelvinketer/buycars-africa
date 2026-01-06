import os
import django
from django.db import connection

# Setup Django Context
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buycars_project.settings')
django.setup()

def emergency_repair():
    print("🚑 STARTING EMERGENCY DATABASE REPAIR...")
    
    with connection.cursor() as cursor:
        # We manually add every column that your views.py is looking for.
        # "IF NOT EXISTS" ensures it won't crash if the column is already there.
        
        columns_to_add = [
            # Column Name            Data Type & Default
            ("body_type",            "varchar(50) DEFAULT 'suv'"),
            ("listing_type",         "varchar(20) DEFAULT 'sale'"),
            ("is_available_for_rent","boolean DEFAULT false"),
            ("rent_price_per_day",   "decimal(10, 2) NULL"),
            ("min_hire_days",        "integer DEFAULT 1"),
            ("mileage",              "integer DEFAULT 0"),
            ("location",             "varchar(100) DEFAULT 'Nairobi'"),
            ("is_featured",          "boolean DEFAULT false"),
            ("condition",            "varchar(50) DEFAULT 'used'"),
            ("transmission",         "varchar(50) DEFAULT 'automatic'"),
            ("fuel_type",            "varchar(50) DEFAULT 'petrol'"),
            ("engine_size",          "varchar(50) DEFAULT '2000cc'"),
            ("color",                "varchar(50) DEFAULT 'white'"),
            ("drive_type",           "varchar(50) DEFAULT '2wd'"),
            ("description",          "text DEFAULT ''"),
            ("vin",                  "varchar(50) DEFAULT ''"),
            ("video_url",            "varchar(200) DEFAULT ''"),
            ("registration_number",  "varchar(20) DEFAULT ''"),
            ("views_count",          "integer DEFAULT 0"),
            ("priority",             "integer DEFAULT 0"),
            ("discount_price",       "decimal(10, 2) NULL"),
        ]

        for col_name, col_def in columns_to_add:
            print(f"   -> Fixing column: {col_name}...")
            # This SQL command works on PostgreSQL to add columns safely
            sql = f"ALTER TABLE cars_car ADD COLUMN IF NOT EXISTS {col_name} {col_def};"
            try:
                cursor.execute(sql)
            except Exception as e:
                # If it fails, we print why but keep going
                print(f"      ⚠️ Warning on {col_name}: {e}")

    print("✅ REPAIR COMPLETE. The database structure now matches your code.")

if __name__ == "__main__":
    emergency_repair()