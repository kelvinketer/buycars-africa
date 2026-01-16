from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cars', '0002_searchterm_remove_car_mileage_km_car_body_type_and_more'),
    ]

    operations = [
        # 1. Handle 'renter' field (SKIP DB CREATION, JUST UPDATE STATE)
        migrations.SeparateDatabaseAndState(
            state_operations=[
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
            ],
            # We leave this empty so Postgres doesn't try to create "renter_id" again
            database_operations=[], 
        ),

        # 2. Handle 'total_price' (Try to create it normally)
        # If this also fails with "already exists", we will wrap it like above.
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