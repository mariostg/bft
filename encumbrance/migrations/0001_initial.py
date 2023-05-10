# Generated by Django 4.2.1 on 2023-05-10 15:14

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="EncumbranceImport",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("docno", models.CharField(max_length=10)),
                ("lineno", models.CharField(max_length=7)),
                (
                    "spent",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "balance",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "workingplan",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                ("fundcenter", models.CharField(max_length=6)),
                ("fund", models.CharField(max_length=4)),
                ("costcenter", models.CharField(max_length=6)),
                (
                    "internalorder",
                    models.CharField(blank=True, max_length=7, null=True),
                ),
                ("doctype", models.CharField(blank=True, max_length=2, null=True)),
                ("enctype", models.CharField(max_length=21)),
                (
                    "linetext",
                    models.CharField(blank=True, default="", max_length=50, null=True),
                ),
                (
                    "predecessordocno",
                    models.CharField(blank=True, default="", max_length=20, null=True),
                ),
                (
                    "predecessorlineno",
                    models.CharField(blank=True, default="", max_length=3, null=True),
                ),
                (
                    "reference",
                    models.CharField(blank=True, default="", max_length=16, null=True),
                ),
                ("gl", models.CharField(max_length=5)),
                ("duedate", models.DateField(blank=True, null=True)),
                ("vendor", models.CharField(blank=True, max_length=50, null=True)),
                (
                    "createdby",
                    models.CharField(blank=True, default="", max_length=50, null=True),
                ),
            ],
        ),
    ]
