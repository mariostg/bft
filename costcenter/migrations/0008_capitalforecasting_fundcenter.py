# Generated by Django 4.2.1 on 2024-02-07 19:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("costcenter", "0007_remove_capitalproject_sequence"),
    ]

    operations = [
        migrations.AddField(
            model_name="capitalforecasting",
            name="fundcenter",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="costcenter.fundcenter",
                verbose_name="Fund Center",
            ),
        ),
    ]
