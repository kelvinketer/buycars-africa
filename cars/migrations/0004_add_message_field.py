from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0003_add_renter_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='message',
            field=models.TextField(blank=True, null=True),
        ),
    ]