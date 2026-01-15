import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buycars_project.settings')
django.setup()

def check():
    with connection.cursor() as cursor:
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='cars_car';")
        columns = [row[0] for row in cursor.fetchall()]
        
        print("\n--- CAR TABLE COLUMNS ---")
        if 'body_type' in columns:
            print("✅ body_type EXISTS!")
        else:
            print("❌ body_type is MISSING!")
            
        if 'listing_type' in columns:
            print("✅ listing_type EXISTS!")
        else:
            print("❌ listing_type is MISSING!")

if __name__ == "__main__":
    check()