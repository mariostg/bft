# Generated by Django 4.2.1 on 2023-10-04 16:38

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "costcenter",
            "0004_remove_costcenter_parent_remove_fundcenter_parent_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="fundcenter",
            name="sequence",
            field=models.CharField(
                max_length=25, unique=True, verbose_name="FC Sequence No"
            ),
        ),
    ]