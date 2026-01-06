import os
import django
from django.db import connection

# Setup Django Context
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buycars_project.settings')
django.setup()

def reconstruct_tables():
    print("🏗️ STARTING TABLE RECONSTRUCTION...")
    
    with connection.cursor() as cursor:
        # 1. Recreate 'CarImage' Table (Fixes the current error)
        print("   -> Recreating table: cars_carimage...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cars_carimage (
                id bigserial PRIMARY KEY,
                image varchar(200) NOT NULL,
                is_main boolean DEFAULT false,
                car_id bigint NOT NULL REFERENCES cars_car(id) DEFERRABLE INITIALLY DEFERRED
            );
            CREATE INDEX IF NOT EXISTS cars_carimage_car_id_idx ON cars_carimage(car_id);
        """)
        
        # 2. Recreate 'Booking' Table (Prevents the next error)
        print("   -> Recreating table: cars_booking...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cars_booking (
                id bigserial PRIMARY KEY,
                full_name varchar(100) NOT NULL,
                email varchar(254) NOT NULL,
                phone varchar(20) NOT NULL,
                start_date date NOT NULL,
                end_date date NOT NULL,
                total_cost numeric(10, 2) NOT NULL,
                status varchar(20) NOT NULL,
                created_at timestamp with time zone NOT NULL,
                car_id bigint NOT NULL REFERENCES cars_car(id) DEFERRABLE INITIALLY DEFERRED
            );
            CREATE INDEX IF NOT EXISTS cars_booking_car_id_idx ON cars_booking(car_id);
        """)

        # 3. Recreate 'SearchTerm' Table
        print("   -> Recreating table: cars_searchterm...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cars_searchterm (
                id bigserial PRIMARY KEY,
                term varchar(255) NOT NULL,
                search_date timestamp with time zone NOT NULL
            );
        """)

        # 4. Recreate 'CarView' Table
        print("   -> Recreating table: cars_carview...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cars_carview (
                id bigserial PRIMARY KEY,
                ip_address varchar(45) NULL,
                session_id varchar(255) NULL,
                timestamp timestamp with time zone NOT NULL,
                car_id bigint NOT NULL REFERENCES cars_car(id) DEFERRABLE INITIALLY DEFERRED
            );
        """)

        # 5. FAKE the migration history (Crucial Step)
        # We tell Django: "Hey, we manually built migration 0001, assume it's done."
        # This prevents Django from trying to run it again and crashing.
        print("   -> Marking migration 0001 as complete...")
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied)
            VALUES ('cars', '0001_initial', NOW())
            ON CONFLICT DO NOTHING;
        """)

    print("✅ RECONSTRUCTION COMPLETE. Tables restored & migration faked.")

if __name__ == "__main__":
    reconstruct_tables()