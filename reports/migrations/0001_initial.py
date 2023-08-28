# Generated by Django 4.2.1 on 2023-08-28 14:55

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CostCenterMonthly",
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
                ("source", models.CharField(max_length=24)),
                (
                    "cost_center",
                    models.CharField(max_length=6, verbose_name="Cost Center"),
                ),
                ("period", models.CharField(max_length=2)),
                ("fy", models.CharField(max_length=4)),
                (
                    "spent",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "commitment",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "pre_commitment",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "fund_reservation",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "balance",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "working_plan",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "charges",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "allocation",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "forecast",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="costcentermonthly",
            constraint=models.UniqueConstraint(
                fields=("fund", "source", "cost_center", "period", "fy"),
                name="unique_cost_center_monthly_row",
            ),
        ),
    ]
