import random
import urllib.request
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from cars.models import Car, CarImage
from users.models import DealerProfile
from django.core.files.base import ContentFile

User = get_user_model()

class Command(BaseCommand):
    help = 'Wipes old test data and generates 100 cars WITH RELIABLE images.'

    def handle(self, *args, **kwargs):
        self.stdout.write("🧹 Cleaning up old test data...")
        
        # 1. Find the Dummy Dealer
        dealer = User.objects.filter(username="BulkImporter").first()
        if dealer:
            Car.objects.filter(dealer=dealer).delete()
        else:
            dealer = User.objects.create(username="BulkImporter", email='bulk@buycars.africa', role='DEALER')
            dealer.set_password("Bulk@123")
            dealer.save()
            DealerProfile.objects.create(user=dealer, business_name='Bulk Imports Kenya', plan_type='PRO', is_verified=True, city='MSA')

        # 2. Download Master Images (Using Placehold.co which NEVER blocks)
        self.stdout.write("📥 Downloading Placeholder Images...")
        
        # We use text in the image so you can instantly tell them apart
        IMAGE_URLS = {
            'SUV': "https://placehold.co/800x600/2ecc71/ffffff.png?text=SUV+Stock+Photo",
            'Sedan': "https://placehold.co/800x600/3498db/ffffff.png?text=Sedan+Stock+Photo",
            'Hatchback': "https://placehold.co/800x600/e74c3c/ffffff.png?text=Hatchback+Stock+Photo",
            'Pickup': "https://placehold.co/800x600/f1c40f/ffffff.png?text=Pickup+Stock+Photo"
        }

        master_images = {}
        for body, url in IMAGE_URLS.items():
            try:
                # User-Agent header tricks servers into thinking we are a real browser, not a script
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                response = urllib.request.urlopen(req)
                master_images[body] = response.read()
                self.stdout.write(f"   ✅ Saved image for {body}")
            except Exception as e:
                self.stdout.write(f"   ⚠️ Failed to download {body}: {e}")

        # 3. Generate 100 Cars
        MAKES_MODELS = {
            'Toyota': [('Vitz', 850000, 'Hatchback'), ('Prado', 6500000, 'SUV'), ('Fielder', 1400000, 'Wagon'), ('Hilux', 4500000, 'Pickup')],
            'Subaru': [('Forester', 2800000, 'SUV'), ('Impreza', 1600000, 'Hatchback')],
            'Mazda':  [('Demio', 750000, 'Hatchback'), ('CX-5', 2900000, 'SUV')],
            'Honda':  [('Fit', 900000, 'Hatchback'), ('CR-V', 3500000, 'SUV')],
            'Nissan': [('Note', 800000, 'Hatchback'), ('X-Trail', 2400000, 'SUV')],
            'Mercedes-Benz': [('C-Class', 3800000, 'Sedan'), ('E-Class', 5500000, 'Sedan')],
        }
        
        CITIES = ['Nairobi', 'Mombasa', 'Nakuru', 'Kisumu']

        self.stdout.write("🚀 Generating 100 Cars...")
        
        for i in range(100):
            make = random.choice(list(MAKES_MODELS.keys()))
            model_data = random.choice(MAKES_MODELS[make])
            model_name, base_price, body = model_data

            img_body = body if body in master_images else 'SUV' 
            if body == 'Wagon': img_body = 'SUV'

            car = Car.objects.create(
                dealer=dealer,
                make=make,
                model=model_name,
                year=random.randint(2015, 2024),
                price=max(500000, base_price + random.randint(-100000, 100000)),
                listing_currency='KES',
                mileage=random.randint(5000, 120000),
                engine_cc=random.choice([1500, 1800, 2000, 2500]),
                transmission=random.choice(['Automatic', 'Manual']),
                body_type=body,
                color=random.choice(['White', 'Black', 'Silver', 'Blue']),
                fuel_type=random.choice(['Petrol', 'Diesel']),
                drive_type=random.choice(['2WD', '4WD']),
                condition='Foreign Used',
                status='AVAILABLE',
                city=random.choice(CITIES),
                description=f"Fresh import {make} {model_name}. Clean unit.",
                is_featured=random.choice([True, False])
            )

            if img_body in master_images:
                car_img = CarImage(car=car, is_main=True)
                car_img.image.save(f"seed_{car.id}.jpg", ContentFile(master_images[img_body]), save=True)

            if i % 10 == 0:
                self.stdout.write(f"   [{i}%] Created {make} {model_name}")

        self.stdout.write(self.style.SUCCESS("🎉 DONE! 100 Cars with IMAGES created."))
        