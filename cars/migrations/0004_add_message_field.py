from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0003_add_renter_field'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                # Update Django's internal memory that 'message' exists
                migrations.AddField(
                    model_name='booking',
                    name='message',
                    field=models.TextField(blank=True, null=True),
                ),
            ],
            # Do NOT run any SQL commands on the database (avoids the crash)
            database_operations=[],
        ),
    ]