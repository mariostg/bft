# Generated by Django 4.2.1 on 2023-06-01 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lineitems", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="lineitem",
            name="fcintegrity",
            field=models.BooleanField(default=False),
        ),
    ]