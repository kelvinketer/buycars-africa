import os
import django
from django.core.management import call_command

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buycars_project.settings')
django.setup()

def fix_zombie_migration():
    print("🧟 HANDLING ZOMBIE MIGRATION...")
    
    try:
        # We tell Django to "fake" the specific migration that is crashing.
        # This marks it as complete without trying to run the SQL (create table) again.
        print("   -> Faking 'cars' app migration 0002...")
        call_command('migrate', 'cars', '0002', fake=True)
        print("   ✅ Migration 0002 marked as DONE.")
    except Exception as e:
        print(f"   ⚠️ Could not fake 0002 (It might be done already): {e}")

    print("🚀 Running the rest of the migrations normally...")
    try:
        call_command('migrate')
        print("✅ All migrations completed successfully!")
    except Exception as e:
        print(f"❌ Standard migration failed: {e}")

if __name__ == "__main__":
    fix_zombie_migration()