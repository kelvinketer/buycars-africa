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
        # This adds the column 'renter_id' to the database
        migrations.AddField(
            model_name='booking',
            name='renter',
            field=models.ForeignKey(
                default=1, # Temporary default to handle existing rows if any
                on_delete=django.db.models.deletion.CASCADE,
                related_name='rentals',
                to=settings.AUTH_USER_MODEL
            ),
            preserve_default=False,
        ),
    ]