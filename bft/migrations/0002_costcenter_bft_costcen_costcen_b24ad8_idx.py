# Generated by Django 5.0.4 on 2024-05-09 13:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bft", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="costcenter",
            index=models.Index(fields=["costcenter"], name="bft_costcen_costcen_b24ad8_idx"),
        ),
    ]
