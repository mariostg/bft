# Generated by Django 5.0.6 on 2024-08-01 15:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bft", "0006_alter_bookmark_bookmark_link"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="bookmark",
            managers=[],
        ),
        migrations.AlterField(
            model_name="bookmark",
            name="bookmark_link",
            field=models.CharField(max_length=125),
        ),
        migrations.AddConstraint(
            model_name="bookmark",
            constraint=models.UniqueConstraint(fields=("bookmark_link", "owner"), name="bft_bookmark_is_unique"),
        ),
    ]
