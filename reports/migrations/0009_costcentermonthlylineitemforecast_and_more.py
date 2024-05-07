# Generated by Django 5.0.4 on 2024-05-07 12:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0008_costcentermonthlyforecastadjustment_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="CostCenterMonthlyLineItemForecast",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fund", models.CharField(max_length=4, verbose_name="Fund")),
                ("source", models.CharField(max_length=24, verbose_name="Source")),
                ("costcenter", models.CharField(max_length=6, verbose_name="Cost Center")),
                ("period", models.CharField(max_length=2, verbose_name="Period")),
                ("fy", models.CharField(max_length=4, verbose_name="FY")),
                (
                    "line_item_forecast",
                    models.DecimalField(
                        decimal_places=2, default=0, max_digits=10, null=True, verbose_name="Line Item Forecast"
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Line Item Monthly Forecast",
                "abstract": False,
            },
        ),
        migrations.AddConstraint(
            model_name="costcentermonthlylineitemforecast",
            constraint=models.UniqueConstraint(
                fields=("fund", "source", "costcenter", "period", "fy"),
                name="reports_costcentermonthlylineitemforecast_is_unique",
            ),
        ),
    ]