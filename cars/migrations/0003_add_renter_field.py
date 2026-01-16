from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        # Points to your last known good migration
        ('cars', '0002_searchterm_remove_car_mileage_km_car_body_type_and_more'),
    ]

    operations = [
        # 1. Add the missing 'renter' column
        migrations.AddField(
            model_name='booking',
            name='renter',
            field=models.ForeignKey(
                default=1, 
                on_delete=django.db.models.deletion.CASCADE,
                related_name='rentals',
                to=settings.AUTH_USER_MODEL
            ),
            preserve_default=False,
        ),
        # 2. Add the missing 'total_price' column
        migrations.AddField(
            model_name='booking',
            name='total_price',
            field=models.DecimalField(
                decimal_places=2,
                default=0.00,
                max_digits=10
            ),
            preserve_default=False,
        ),
    ]