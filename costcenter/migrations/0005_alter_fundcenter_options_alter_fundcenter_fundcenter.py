# Generated by Django 4.2.1 on 2023-05-17 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("costcenter", "0004_alter_source_source"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="fundcenter",
            options={"ordering": ["fundcenter"], "verbose_name_plural": "Fund Centers"},
        ),
        migrations.AlterField(
            model_name="fundcenter",
            name="fundcenter",
            field=models.CharField(max_length=6),
        ),
    ]
