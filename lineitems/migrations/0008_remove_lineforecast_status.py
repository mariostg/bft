# Generated by Django 4.2.1 on 2024-01-30 14:48

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("lineitems", "0007_lineitemimport"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="lineforecast",
            name="status",
        ),
    ]