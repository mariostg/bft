# """
# A useful script to throw some data into BFT for testing purposes. To be used in DEBUG mode.
# """

import os, sys
from pathlib import Path

import django
from django.core.management import call_command


PWD = os.getenv("PWD")
BASE_DIR = Path(PWD).resolve()
if BASE_DIR not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from main import settings  # isort:skip
from bft.models import ForecastAdjustment, CostCenterManager, FundManager  # isort:skip
from reports.utils import (
    CostCenterMonthlyAllocationReport,
    CostCenterMonthlyForecastLineItemReport,
    CostCenterMonthlyForecastAdjustmentReport,
    CostCenterInYearEncumbranceReport,
    CostCenterMonthlyPlanReport,
    CostCenterMonthlyEncumbranceReport,
)  # isort:skip


def do_monthly(fy, period, quarter):
    c = CostCenterInYearEncumbranceReport(fy, period)
    c.insert_line_items(c.sum_line_items())

    c = CostCenterMonthlyForecastLineItemReport(fy, period)
    c.insert_grouped_forecast_line_item(c.sum_forecast_line_item())

    c = CostCenterMonthlyAllocationReport(fy=fy, period=period, quarter=quarter)
    c.insert_grouped_allocation(c.sum_allocation_cost_center())

    c = CostCenterMonthlyForecastAdjustmentReport(fy, period)
    c.insert_grouped_forecast_adjustment(c.sum_forecast_adjustments())

    c = CostCenterMonthlyEncumbranceReport(fy, period)
    c.insert_line_items(c.sum_line_items())

    c = CostCenterMonthlyPlanReport(fy=fy, period=period)


call_command("populate")

cc = CostCenterManager().cost_center("8484WA")
fund = FundManager().fund("C113")

call_command("uploadcsv", f"{settings.BASE_DIR}/test-data/encumbrance_2184A3-p1.txt")
fa = ForecastAdjustment()
fa.costcenter = cc
fa.fund = fund
fa.amount = 1000
fa.note = "Increase in demand"
fa.save()
for p in range(1, 14):
    do_monthly(2023, p, 1)
    call_command("uploadcsv", f"test-data/encumbrance_2184A3-p{p}.txt")
