# Generated by Django 4.2.1 on 2023-11-20 19:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("lineitems", "0004_alter_lineforecast_owner"),
    ]

    operations = [
        migrations.AddField(
            model_name="lineforecast",
            name="balance",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="lineforecast",
            name="spent",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="lineforecast",
            name="workingplan",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]