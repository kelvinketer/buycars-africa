from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cars', '0002_searchterm_remove_car_mileage_km_car_body_type_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                # 1. Update Django's internal state for 'renter'
                migrations.AddField(
                    model_name='booking',
                    name='renter',
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='rentals',
                        to=settings.AUTH_USER_MODEL
                    ),
                ),
                # 2. Update Django's internal state for 'total_price'
                migrations.AddField(
                    model_name='booking',
                    name='total_price',
                    field=models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        default=0.00
                    ),
                ),
            ],
            # Leave database_operations empty because these columns ALREADY EXIST in Postgres
            database_operations=[], 
        ),
    ]