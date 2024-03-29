# Generated by Django 4.2.1 on 2024-02-22 19:53

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CostCenterChargeImport",
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
                ("fund", models.CharField(max_length=4)),
                ("costcenter", models.CharField(max_length=6)),
                ("gl", models.CharField(max_length=5)),
                ("ref_doc_no", models.CharField(max_length=10)),
                ("aux_acct_asmnt", models.CharField(max_length=20)),
                (
                    "amount",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                ("doc_type", models.CharField(blank=True, max_length=2, null=True)),
                ("posting_date", models.DateField()),
                ("period", models.CharField(max_length=2)),
                (
                    "fy",
                    models.PositiveSmallIntegerField(
                        default=0, verbose_name="Fiscal Year"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CostCenterChargeMonthly",
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
                ("fund", models.CharField(max_length=4)),
                (
                    "costcenter",
                    models.CharField(max_length=6, verbose_name="Cost Center"),
                ),
                (
                    "amount",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                ("period", models.CharField(max_length=2)),
                (
                    "fy",
                    models.PositiveSmallIntegerField(
                        default=0, verbose_name="Fiscal Year"
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Cost Center charges monthly",
            },
        ),
    ]
