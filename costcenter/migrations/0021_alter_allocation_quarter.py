# Generated by Django 4.2.1 on 2023-08-28 14:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("costcenter", "0020_alter_costcenter_sequence"),
    ]

    operations = [
        migrations.AlterField(
            model_name="allocation",
            name="quarter",
            field=models.TextField(
                choices=[
                    ("0", "Q0"),
                    ("1", "Q1"),
                    ("2", "Q2"),
                    ("3", "Q3"),
                    ("4", "Q4"),
                ],
                default="Q0",
                max_length=2,
            ),
        ),
    ]