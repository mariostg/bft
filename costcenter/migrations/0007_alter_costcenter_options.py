# Generated by Django 4.2.1 on 2023-06-01 12:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("costcenter", "0006_alter_fundcenter_fundcenter"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="costcenter",
            options={"ordering": ["costcenter"], "verbose_name_plural": "Cost Centers"},
        ),
    ]
