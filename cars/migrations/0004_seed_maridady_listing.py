from django.db import migrations
from django.contrib.auth.hashers import make_password
from django.utils import timezone
import urllib.request
from django.core.files.base import ContentFile

def add_maridady_listing(apps, schema_editor):
    # 1. Load the "Historical" models to avoid type mismatches
    # We assume your custom user app is named 'users' and model is 'User'
    User = apps.get_model('users', 'User') 
    DealerProfile = apps.get_model('users', 'DealerProfile')
    Car = apps.get_model('cars', 'Car')
    CarImage = apps.get_model('cars', 'CarImage')

    # 2. Get or Create the Dealer User
    # We use filter().first() safely
    dealer = User.objects.filter(username="MaridadyMotors").first()
    
    if not dealer:
        dealer = User.objects.create(
            username="MaridadyMotors",
            email="info@maridadymotors.com",
            is_staff=False,
            is_active=True,
            password=make_password("Maridady@2026") # Securely hash the password
        )

    # 3. Create/Update Profile (Blue Tick)
    # FIX: We use 'user_id' instead of 'user' to avoid "Must be User instance" errors
    DealerProfile.objects.update_or_create(
        user_id=dealer.id,
        defaults={
            "business_name": "Maridady Motors",
            "phone_number": "0709888777",
            "city": "NBI",
            "address": "Kiambu Road, Ridgeways Nairobi",
            "plan_type": "PRO",
            "is_verified": True
        }
    )

    # 4. Create the Car
    # FIX: Use 'dealer_id' instead of 'dealer'
    if not Car.objects.filter(dealer_id=dealer.id, model="Outlander", year=2018).exists():
        car = Car.objects.create(
            dealer_id=dealer.id,
            make="Mitsubishi",
            model="Outlander",
            year=2018,
            price=3102750,
            listing_currency="KES",
            mileage=90415,
            engine_cc=2000,
            transmission="Automatic",
            body_type="SUV",
            color="White",
            fuel_type="Hybrid",
            drive_type="4WD",
            condition="Foreign Used",
            status="AVAILABLE",
            description="Duty Paid. Stock ID: E107-1437. 2.0L MIVEC Engine. Clean import from Japan.",
            city="Nairobi",
            is_featured=True,
            created_at=timezone.now()
        )

        # 5. Add Images
        image_urls = [
            "https://media.ed.edmunds-media.com/mitsubishi/outlander-sport/2018/oem/2018_mitsubishi_outlander-sport_4dr-suv_24-se_fq_oem_1_1600.jpg",
            "https://media.ed.edmunds-media.com/mitsubishi/outlander/2018/oem/2018_mitsubishi_outlander_4dr-suv_gt_f_oem_1_1600.jpg",
            "https://media.ed.edmunds-media.com/mitsubishi/outlander/2018/oem/2018_mitsubishi_outlander_4dr-suv_gt_d_oem_1_1600.jpg"
        ]

        for index, url in enumerate(image_urls):
            try:
                response = urllib.request.urlopen(url)
                if response.status == 200:
                    image_content = ContentFile(response.read())
                    # Use car_id to be safe
                    car_img = CarImage(car_id=car.id, is_main=(index == 0))
                    filename = f"outlander_{car.id}_{index}.jpg"
                    car_img.image.save(filename, image_content, save=True)
            except Exception as e:
                print(f"Skipping image {url}: {e}")

class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0003_remove_car_engine_size_car_drive_type_car_engine_cc_and_more'),
        ('users', '0008_dealerprofile_is_verified'),
    ]

    operations = [
        migrations.RunPython(add_maridady_listing),
    ]
    