from django.db import migrations
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.utils import timezone
import urllib.request

def add_maridady_listing(apps, schema_editor):
    # We use apps.get_model to safely get models during migrations
    User = get_user_model() 
    DealerProfile = apps.get_model('users', 'DealerProfile')
    Car = apps.get_model('cars', 'Car')
    CarImage = apps.get_model('cars', 'CarImage')

    # 1. Create the Dealer User
    # Note: We can't use .create_user() in migrations easily, so we use objects.create() 
    # and set password manually if needed, but for migrations, simple creation is safer.
    if User.objects.filter(username="MaridadyMotors").exists():
        dealer = User.objects.get(username="MaridadyMotors")
    else:
        dealer = User.objects.create(
            username="MaridadyMotors",
            email="info@maridadymotors.com",
            is_staff=False,
            is_active=True
        )
        dealer.set_password("Maridady@2026")
        dealer.save()

    # 2. Create/Update Profile (Blue Tick)
    # We use update_or_create to ensure we don't duplicate if run twice
    DealerProfile.objects.update_or_create(
        user=dealer,
        defaults={
            "business_name": "Maridady Motors",
            "phone_number": "0709888777",
            "city": "NBI",
            "address": "Kiambu Road, Ridgeways Nairobi",
            "plan_type": "PRO",
            "is_verified": True  # The critical Blue Tick
        }
    )

    # 3. Create the Car
    # Check if car exists to avoid duplicates
    if not Car.objects.filter(dealer=dealer, model="Outlander", year=2018).exists():
        car = Car.objects.create(
            dealer=dealer,
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

        # 4. Add Images
        image_urls = [
            "https://media.ed.edmunds-media.com/mitsubishi/outlander-sport/2018/oem/2018_mitsubishi_outlander-sport_4dr-suv_24-se_fq_oem_1_1600.jpg",
            "https://media.ed.edmunds-media.com/mitsubishi/outlander/2018/oem/2018_mitsubishi_outlander_4dr-suv_gt_f_oem_1_1600.jpg",
            "https://media.ed.edmunds-media.com/mitsubishi/outlander/2018/oem/2018_mitsubishi_outlander_4dr-suv_gt_d_oem_1_1600.jpg"
        ]

        for index, url in enumerate(image_urls):
            try:
                # Use urllib to download
                response = urllib.request.urlopen(url)
                if response.status == 200:
                    image_content = ContentFile(response.read())
                    car_img = CarImage(car=car, is_main=(index == 0))
                    # Assign name and file content
                    filename = f"outlander_{car.id}_{index}.jpg"
                    car_img.image.save(filename, image_content, save=True)
            except Exception as e:
                print(f"Skipping image {url}: {e}")

class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0003_remove_car_engine_size_car_drive_type_car_engine_cc_and_more'), # Ensure this matches your last migration name
        ('users', '0008_dealerprofile_is_verified'),
    ]

    operations = [
        migrations.RunPython(add_maridady_listing),
    ]
    