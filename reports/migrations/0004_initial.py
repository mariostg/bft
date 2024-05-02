# Generated by Django 5.0.4 on 2024-05-02 18:50

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("reports", "0003_delete_costcentermonthly"),
    ]

    operations = [
        migrations.CreateModel(
            name="CostCenterMonthly",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fund", models.CharField(max_length=4, verbose_name="Fund")),
                ("source", models.CharField(max_length=24, verbose_name="Source")),
                ("costcenter", models.CharField(max_length=6, verbose_name="Cost Center")),
                ("period", models.CharField(max_length=2, verbose_name="Period")),
                ("fy", models.CharField(max_length=4, verbose_name="FY")),
                (
                    "spent",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10, null=True, verbose_name="Spent"),
                ),
                (
                    "commitment",
                    models.DecimalField(
                        decimal_places=2, default=0, max_digits=10, null=True, verbose_name="Commitment"
                    ),
                ),
                (
                    "pre_commitment",
                    models.DecimalField(
                        decimal_places=2, default=0, max_digits=10, null=True, verbose_name="Pre Commitment"
                    ),
                ),
                (
                    "fund_reservation",
                    models.DecimalField(
                        decimal_places=2, default=0, max_digits=10, null=True, verbose_name="Fund Reservation"
                    ),
                ),
                (
                    "balance",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10, null=True, verbose_name="Balance"),
                ),
                (
                    "working_plan",
                    models.DecimalField(
                        decimal_places=2, default=0, max_digits=10, null=True, verbose_name="Working Plan"
                    ),
                ),
                (
                    "forecast_adjustment",
                    models.DecimalField(
                        decimal_places=2, default=0, max_digits=10, null=True, verbose_name="Forecast Adjustment"
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Cost Center Monthly",
            },
        ),
    ]
