# Generated by Django 4.2.1 on 2023-09-14 17:19

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("lineitems", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lineforecast",
            name="forecastamount",
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=10, verbose_name="Forecast"
            ),
        ),
    ]
