# Generated by Django 4.2.1 on 2024-01-05 14:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("costcenter", "0005_alter_costcenterallocation_fy_and_more"),
        ("users", "0003_alter_bftuser_default_cc"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bftuser",
            name="default_cc",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                to="costcenter.costcenter",
                verbose_name="Default CC",
            ),
        ),
    ]
