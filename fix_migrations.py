import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buycars_project.settings')
django.setup()

def fix():
    with connection.cursor() as cursor:
        print("Starting Database Cleanup...")
        
        # 1. Drop the specific table causing the "Already Exists" error
        # This is safe because it just stores search history
        print("Dropping cars_searchterm table...")
        cursor.execute("DROP TABLE IF EXISTS cars_searchterm CASCADE;")
        
        # 2. Clear Payment data to prevent "ForeignKey" crashes
        # (Since we have a new Booking table, old payments pointing to old bookings will crash the deploy)
        print("Clearing old payment records...")
        cursor.execute("TRUNCATE TABLE payments_payment RESTART IDENTITY CASCADE;")

        # 3. Clear the migration history so Django thinks it's starting fresh
        print("Resetting migration history...")
        cursor.execute("DELETE FROM django_migrations WHERE app IN ('cars', 'payments');")
        
        print("Cleanup successful. Ready for fresh migration.")

if __name__ == "__main__":
    fix()