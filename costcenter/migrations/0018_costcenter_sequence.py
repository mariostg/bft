# Generated by Django 4.2.1 on 2023-08-07 17:38

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("costcenter", "0017_fundcenterallocation"),
    ]

    operations = [
        migrations.AddField(
            model_name="costcenter",
            name="sequence",
            field=models.CharField(
                default="", max_length=25, unique=True, verbose_name="Sequence No"
            ),
        ),
    ]