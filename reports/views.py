import csv

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Value as V
from django.db.models.functions import Concat
from django.http import HttpResponse
from django.shortcuts import render

from bft import conf
from bft.conf import QUARTERKEYS
from bft.exceptions import LineItemsDoNotExistError
from bft.models import (BftStatus, BftStatusManager, CapitalProjectManager,
                        CostCenterAllocation, CostCenterChargeMonthly,
                        CostCenterManager, FinancialStructureManager,
                        FundCenterAllocation, FundCenterManager, FundManager,
                        LineItem)
from reports import capitalforecasting, screeningreport, utils
from reports.forms import (SearchAllocationAnalysisForm,
                           SearchCapitalEstimatesForm, SearchCapitalFearsForm,
                           SearchCapitalForecastingDashboardForm,
                           SearchCapitalHistoricalForm,
                           SearchCapitalYeRatiosForm,
                           SearchCostCenterInYearDataForm,
                           SearchCostCenterMonthlyDataForm,
                           SearchCostCenterScreeningReportForm,
                           UpdateCostCenterAllocationMonthlyForm,
                           UpdateCostCenterEncumbranceMonthlyForm,
                           UpdateCostCenterForecastAdjustmentMonthlyForm,
                           UpdateCostCenterForecastLineItemMonthlyForm)
from utils.getrequestfilter import set_query_string


def bmt_screening_report(request):
    fundcenter = fund = ""
    fy = BftStatus.current.fy()
    quarter = BftStatus.current.quarter()
    query_string = None
    table = None
    form_filter = True
    context = {}

    has_cc_allocation = CostCenterAllocation.objects.exists()
    has_fc_allocation = FundCenterAllocation.objects.exists()

    if not len(request.GET) and not has_cc_allocation and not has_fc_allocation:
        messages.warning(request, "There are no allocation to report, hence nothing really to screen")
        form_filter = False

    if len(request.GET):
        fundcenter = FundCenterManager().get_request(request)
        fund = FundManager().get_request(request)
        quarter = int(request.GET.get("quarter")) if request.GET.get("quarter") else 0
        fy = set_fy(request)

        if str(quarter) not in QUARTERKEYS:
            messages.warning(request, "Quarter is invalid.  Either value is missing or outside range")
        if fundcenter and fund and quarter and fy:
            query_string = set_query_string(fundcenter=fundcenter, fund=fund, fy=fy, quarter=quarter)

    initial = {
        "fundcenter": fundcenter,
        "fund": fund,
        "fy": fy,
        "quarter": quarter,
    }

    if query_string and (has_cc_allocation or has_fc_allocation):
        fund = FundManager().fund(fund)
        fundcenter = FundCenterManager().fundcenter(fundcenter)
    if fundcenter and fund:
        sr = screeningreport.ScreeningReport(fundcenter, fund, fy, quarter)
        try:
            sr.main()
            table = sr.html()
        except LineItemsDoNotExistError:
            messages.warning(request, f"No lines items found for {fund} and {fundcenter}")
            table = ""

    form = SearchCostCenterScreeningReportForm(initial=initial)
    context = {
        "form": form,
        "form_filter": form_filter,
        "initial": initial,
        "table": table,
        "fy": BftStatus.current.fy(),
        "url_name": "bmt-screening-report",
        "title": "BMT Screening Report",
        "query_string": request.GET.urlencode(),
    }
    return render(request, "bmt-screening-report.html", context)


def allocation_status_report(request):
    """This function relies on provision of fundcenter, fund, fy, quarter which are extracted from GET request.  If not
    part of GET request, exception will be raised and displayed as a message to the user.

    Args:
        request (HtpRequest): _description_

    Returns:
        Content to display the Allocation Status Report
    """

    fundcenter = fund = fy = quarter = ""
    context = {}  # Dict sent to the template
    table = None  # dataframe html formatted to include in context
    form_filter = True
    has_cc_allocation = CostCenterAllocation.objects.exists()
    has_fc_allocation = FundCenterAllocation.objects.exists()

    if not len(request.GET) and not has_cc_allocation and not has_fc_allocation:
        messages.warning(request, "There are no allocation to report")
        form_filter = False

    if len(request.GET):
        fundcenter = FundCenterManager().get_request(request)
        fund = FundManager().get_request(request)
        quarter = int(request.GET.get("quarter")) if request.GET.get("quarter") else 0
        fy = fy = set_fy(request)

        if str(quarter) not in QUARTERKEYS:
            messages.warning(request, "Quarter is invalid.  Either value is missing or outside range")

    initial = {
        "fundcenter": fundcenter,
        "fund": fund,
        "fy": BftStatus.current.fy(),
        "quarter": BftStatus.current.quarter(),
    }

    if has_cc_allocation or has_fc_allocation:
        r = utils.AllocationStatusReport()
        table = r.main(
            fundcenter, fund, fy, quarter
        )  # allocation_status_dataframe(fundcenter, fund, fy, int(quarter))

    form = SearchAllocationAnalysisForm(initial=initial)
    context = {
        "form": form,
        "form_filter": form_filter,
        "table": table,
        "title": "Allocation Status Report",
        "url_name": "allocation-status-report",
    }
    return render(request, "allocation-status-report.html", context)


def costcenter_monthly_forecast_line_item(request):
    initial = set_initial(request)
    form = SearchCostCenterMonthlyDataForm(initial=initial)

    context = {
        "title": f"{initial['costcenter_name']} Monthly Forecast Line Item",
        "url_name": "costcenter-monthly-forecast-line-item",
        "form_filter": True,
        "form": form,
        "table": "FY and period are mandatory fields.",
    }

    if len(request.GET):
        if "" in [initial["costcenter"], initial["fund"]]:
            form.initial = initial
            context["form"] = form
            return render(request, "costcenter-monthly-data.html", context)

        form.initial = initial
        if "" in [initial["fund"], initial["costcenter"]]:
            return render(request, "costcenter-monthly-data.html", context)

        r = utils.CostCenterMonthlyForecastLineItemReport(
            fy=initial["fy"], fund=initial["fund"], costcenter=initial["costcenter"], period=initial["period"]
        )
        df = r.dataframe()
        if not df.empty:
            df_columns = ["Fund", "Source", "Line Item Forecast"]
            if initial["costcenter"] is None:
                df_columns = ["Cost Center"] + df_columns
            df = df[df_columns]
            df = df.style.format(thousands=",", precision=0)
            df = df.to_html()
        elif len(request.GET):
            df = "There are no data to report using the given parameters."
        else:
            df = ""

        context["table"] = df
        context["form"] = form

    return render(request, "costcenter-monthly-data.html", context)


def set_fy(request) -> int:
    try:
        fy_ = request.GET.get("fy")
        fy = int(fy_)
    except ValueError as err:
        messages.error(request, f"Invalid Fiscal Year, {fy_}<br>{err}")
        return 0
    return fy


def set_initial(request):
    initial = {
        "costcenter": "",
        "costcenter_name": "All Cost Centers",
        "fund": "",
        "fy": BftStatusManager().fy(),
        "period": BftStatusManager().period(),
    }
    if not len(request.GET):
        return initial

    initial["costcenter"] = CostCenterManager().get_request(request)
    if initial["costcenter"]:
        initial["costcenter_name"] = CostCenterManager().cost_center(initial["costcenter"])
    initial["fund"] = FundManager().get_request(request)
    initial["fy"] = set_fy(request)

    period = int(request.GET.get("period")) if request.GET.get("period") else 1
    if conf.is_period(period):
        initial["period"] = period
    else:
        msg = f"{period} is not a valid period.  Expected value is one of {(', ').join(map(str,conf.PERIODKEYS))}"
        messages.warning(request, msg)

    return initial


def costcenter_monthly_allocation_update(request):
    form = UpdateCostCenterAllocationMonthlyForm()
    if request.method == "POST":
        form = UpdateCostCenterAllocationMonthlyForm(request.POST)
        if form.is_valid():
            fy = request.POST.get("fy")
            quarter = request.POST.get("quarter")
            period = request.POST.get("period")
            c = utils.CostCenterMonthlyAllocationReport(fy, period, quarter=quarter)
            c.insert_grouped_allocation(c.sum_allocation_cost_center())
    context = {
        "form": form,
        "url_name": "costcenter-monthly-allocation-update",
        "title": "CC Monthly Allocation Update",
    }
    return render(request, "costcenter-monthly-allocation-update-form.html", context)


def costcenter_monthly_forecast_adjustment_update(request):
    url_name = "costcenter-monthly-forecast-adjustment-update"
    form = UpdateCostCenterForecastAdjustmentMonthlyForm()
    if request.method == "POST":
        form = UpdateCostCenterForecastAdjustmentMonthlyForm(request.POST)
        if form.is_valid():
            fy = request.POST.get("fy")
            period = request.POST.get("period")
            c = utils.CostCenterMonthlyForecastAdjustmentReport(fy, period)
            c.insert_grouped_forecast_adjustment(c.sum_forecast_adjustments())
    context = {
        "form": form,
        "url_name": url_name,
        "title": "Cost Center Monthly Forecast Adjustment Update",
    }
    return render(request, f"{url_name}-form.html", context)


def costcenter_monthly_forecast_line_item_update(request):
    url_name = "costcenter-monthly-forecast-line-item-update"
    form = UpdateCostCenterForecastLineItemMonthlyForm()
    if request.method == "POST":
        form = UpdateCostCenterForecastLineItemMonthlyForm(request.POST)
        if form.is_valid():
            fy = request.POST.get("fy")
            period = request.POST.get("period")
            c = utils.CostCenterMonthlyForecastLineItemReport(fy, period)
            c.insert_grouped_forecast_line_item(c.sum_forecast_line_item())
    context = {
        "form": form,
        "url_name": url_name,
        "title": "Cost Center Monthly Forecast Adjustment Update",
    }
    return render(request, f"{url_name}-form.html", context)


def costcenter_monthly_encumbrance_update(request):
    url_name = "costcenter-monthly-encumbrance-update"
    form = UpdateCostCenterEncumbranceMonthlyForm()
    if request.method == "POST":
        form = UpdateCostCenterEncumbranceMonthlyForm(request.POST)
        if form.is_valid():
            fy = request.POST.get("fy")
            period = request.POST.get("period")
            c = utils.CostCenterMonthlyEncumbranceReport(fy, period)
            c.insert_line_items(c.sum_line_items())
    context = {
        "form": form,
        "url_name": url_name,
        "title": "Cost Center Monthly Encumbrance Update",
    }
    return render(request, f"{url_name}-form.html", context)


def costcenter_monthly_allocation(request):
    initial = set_initial(request)
    form = SearchCostCenterMonthlyDataForm(initial=initial)

    context = {
        "title": f"{initial['costcenter_name']} Monthly Allocation",
        "url_name": "costcenter-monthly-allocation",
        "form_filter": True,
        "form": form,
        "table": "FY and period are mandatory fields.",
    }

    if len(request.GET):
        if "" in [initial["costcenter"], initial["fund"]]:
            form.initial = initial
            context["form"] = form
            return render(request, "costcenter-monthly-data.html", context)

        form.initial = initial
        if "" in [initial["fund"], initial["costcenter"]]:
            return render(request, "costcenter-monthly-data.html", context)

        r = utils.CostCenterMonthlyAllocationReport(
            fy=initial["fy"], fund=initial["fund"], costcenter=initial["costcenter"], period=initial["period"]
        )
        df = r.dataframe()
        if not df.empty:
            df_columns = ["Fund", "Source", "Allocation"]
            if initial["costcenter"] is None:
                df_columns = ["Cost Center"] + df_columns
            df = df[df_columns]
            df = df.style.format(thousands=",", precision=0)
            df = df.to_html()
        elif len(request.GET):
            df = "There are no data to report using the given parameters."
        else:
            df = ""

        context["table"] = df
        context["form"] = form
        context["query_string"] = request.GET.urlencode()

    return render(request, "costcenter-monthly-data.html", context)


def costcenter_monthly_plan(request):
    initial = set_initial(request)
    form = SearchCostCenterMonthlyDataForm(initial=initial)

    context = {
        "title": f"{initial['costcenter_name']} Monthly Plan",
        "url_name": "costcenter-monthly-plan",
        "form_filter": True,
        "form": form,
        "table": "FY and period are mandatory fields.",
    }

    if len(request.GET):
        if "" in [initial["costcenter"], initial["fund"]]:
            form.initial = initial
            return render(request, "costcenter-monthly-data.html", context)

        form.initial = initial
        if "" in [initial["fund"], initial["costcenter"]]:
            return render(request, "costcenter-monthly-data.html", context)

        r = utils.CostCenterMonthlyPlanReport(
            fy=initial["fy"], fund=initial["fund"], costcenter=initial["costcenter"], period=initial["period"]
        )
        df = r.dataframe()
        if not df.empty:
            df = df.style.format(
                {
                    "Spent": "{:,.0f}",
                    "Commitment": "{:,.0f}",
                    "Pre Commitment": "{:,.0f}",
                    "Fund Reservation": "{:,.0f}",
                    "Balance": "{:,.0f}",
                    "Working Plan": "{:,.0f}",
                    "Allocation": "{:,.0f}",
                    "Line Item Forecast": "{:,.0f}",
                    "Forecast Adjustment": "{:,.0f}",
                    "% Spent": "{:.1%}",
                    "% Commit": "{:.1%}",
                    "% Programmed": "{:.1%}",
                }
            )

            df = df.to_html()
        elif len(request.GET):
            df = "There are no data to report using the given parameters."
        else:
            df = ""

        context["table"] = df
        context["form"] = form
        context["query_string"] = request.GET.urlencode()
    return render(request, "costcenter-monthly-data.html", context)


def costcenter_monthly_encumbrance(request):
    initial = set_initial(request)
    form = SearchCostCenterMonthlyDataForm(initial=initial)

    context = {
        "title": f"{initial['costcenter_name']} Monthly Encumbrance",
        "url_name": "costcenter-monthly-encumbrance",
        "query_string": "",
        "form_filter": True,
        "form": form,
        "table": "FY and period are mandatory fields.",
    }
    if len(request.GET):
        if "" in [initial["costcenter"], initial["fund"]]:
            form.initial = initial
            context["form"] = form
            return render(request, "costcenter-monthly-data.html", context)

        form.initial = initial
        if "" in [initial["fund"], initial["costcenter"]]:
            return render(request, "costcenter-monthly-data.html", context)

        r = utils.CostCenterMonthlyEncumbranceReport(
            fy=initial["fy"], fund=initial["fund"], costcenter=initial["costcenter"], period=initial["period"]
        )
        df = r.dataframe()
        if not df.empty:
            df_columns = [
                "Fund",
                "Source",
                "Spent",
                "Commitment",
                "Pre Commitment",
                "Fund Reservation",
                "Balance",
                "Working Plan",
            ]
            if initial["costcenter"] is None:
                df_columns = ["Cost Center"] + df_columns
            df = df[df_columns]
            df = df.style.format(thousands=",", precision=0)
            df = df.to_html()
        elif len(request.GET):
            df = "There are no data to report using the given parameters."
        else:
            df = ""

        context["table"] = df
        context["form"] = form
        context["query_string"] = request.GET.urlencode()
    return render(request, "costcenter-monthly-data.html", context)


def costcenter_monthly_forecast_adjustment(request):
    initial = set_initial(request)
    form = SearchCostCenterMonthlyDataForm(initial=initial)

    context = {
        "title": f"{initial['costcenter_name']} Monthly Forecast Adjustment",
        "url_name": "costcenter-monthly-forecast-adjustment",
        "form_filter": True,
        "form": form,
        "table": "FY and period are mandatory fields.",
    }
    if len(request.GET):
        if "" in [initial["costcenter"], initial["fund"]]:
            form.initial = initial
            context["form"] = form
            return render(request, "costcenter-monthly-data.html", context)

        form.initial = initial
        if "" in [initial["fund"], initial["costcenter"]]:
            return render(request, "costcenter-monthly-data.html", context)

        r = utils.CostCenterMonthlyForecastAdjustmentReport(
            fy=initial["fy"], fund=initial["fund"], costcenter=initial["costcenter"], period=initial["period"]
        )
        df = r.dataframe()
        if not df.empty:
            df_columns = ["Fund", "Source", "Forecast Adjustment"]
            if initial["costcenter"] is None:
                df_columns = ["Cost Center"] + df_columns
            df = df[df_columns]
            df = df.style.format(thousands=",", precision=0)
            df = df.to_html()
        elif len(request.GET):
            df = "There are no data to report using the given parameters."
        else:
            df = ""

        context["table"] = df
        context["form"] = form
    return render(request, "costcenter-monthly-data.html", context)


def costcenter_monthly_data(request):
    costcenter = fund = fy = ""
    period = 1
    context = {}
    form_filter = True
    if len(request.GET):
        costcenter = CostCenterManager().get_request(request)
        fy = fy = set_fy(request)
        fund = FundManager().get_request(request)
        period = int(request.GET.get("period")) if request.GET.get("period") else 1

        if not conf.is_period(period):
            messages.warning(request, "Period is invalid.  Either value is missing or outside range")

    initial = {
        "costcenter": costcenter,
        "fund": fund,
        "fy": fy,
        "period": period,
    }
    form = SearchCostCenterMonthlyDataForm(initial=initial)
    r = utils.CostCenterMonthlyEncumbranceReport(fy=fy, fund=fund, costcenter=costcenter, period=period)
    df = r.dataframe()
    df = df.style.format(thousands=",")

    context = {"table": df.to_html(), "form_filter": form_filter, "form": form}
    return render(request, "costcenter-monthly-data.html", context)


def costcenter_in_year_fear(request):
    initial = set_initial(request)
    form = SearchCostCenterInYearDataForm(initial=initial)

    context = {
        "title": f"{initial['costcenter_name']} In Year FEARS",
        "url_name": "costcenter-in-year-fear",
        "form_filter": True,
        "form": form,
        "table": "Cost Center and Fund are mandatory fields.",
    }
    if len(request.GET):
        if "" in [initial["costcenter"], initial["fund"]]:
            form.initial = initial
            context["form"] = form
            return render(request, "costcenter-in-year-data.html", context)

        form.initial = initial
        if "" in [initial["fund"], initial["costcenter"]]:
            return render(request, "costcenter-in-year-data.html", context)

        r = utils.CostCenterInYearEncumbranceReport(
            fy=initial["fy"], fund=initial["fund"], costcenter=initial["costcenter"]
        )
        table_df = r.dataframe()
        if not table_df.empty:
            df_columns = [
                "Period",
                "Fund",
                "Source",
                "Spent",
                "Commitment",
                "Pre Commitment",
                "Fund Reservation",
                "Balance",
                "Working Plan",
            ]
            chart_df = table_df[df_columns]
            chart_df = chart_df.groupby(["Fund", "Period"]).sum().reset_index()

            df_columns = ["Cost Center"] + df_columns
            table_df = table_df[df_columns].sort_values("Cost Center")
            table_df = table_df.style.format(thousands=",", precision=0)
            table_df = table_df.to_html()

            context["data"] = chart_df.to_json(orient="records")  # json data for chart.  To be worked on
            # CC allocation for given cc, fund, quarter and period.  For chart threshold line
            mgr = CostCenterManager()
            cc_df = mgr.allocation_dataframe(
                costcenter=initial["costcenter"], fund=initial["fund"], fy=initial["fy"], quarter=1
            )
            context["allocation"] = cc_df.Allocation.to_json(orient="records")

            # CC forecast adjustment for given CC, period and fund.  For chart threshold line
            fcst_adj = utils.CostCenterMonthlyForecastAdjustmentReport(
                fy=initial["fy"],
                period=BftStatusManager().period(),
                costcenter=initial["costcenter"],
                fund=initial["fund"],
            )
            fcst_adj_df = fcst_adj.dataframe()
            fcst_line_items = utils.CostCenterMonthlyForecastLineItemReport(
                fy=initial["fy"],
                period=BftStatusManager().period(),
                costcenter=initial["costcenter"],
                fund=initial["fund"],
            )
            fcst_line_df = fcst_line_items.dataframe()

            if not fcst_adj_df.empty and not fcst_line_df.empty:
                context["fcst"] = (fcst_line_df["Line Item Forecast"] + fcst_adj_df["Forecast Adjustment"]).to_json(
                    orient="records"
                )
            elif not fcst_line_df.empty:
                context["fcst"] = fcst_line_df["Line Item Forecast"].to_json(orient="records")
            elif not fcst_adj_df.empty:
                context["fcst"] = fcst_adj_df["Forecast Adjustment"].to_json(orient="records")

        elif len(request.GET):
            table_df = "There are no data to report using the given parameters."
        else:
            table_df = ""

        context["table"] = table_df
        context["form"] = form
    return render(request, "costcenter-in-year-data.html", context)


def line_items(request):
    data = (
        LineItem.objects.annotate(doc=Concat("docno", V("-"), "lineno"))
        .order_by("fundcenter", "costcenter", "fund", "docno", "lineno")
        .filter(balance__gt=0)
    )
    paginator = Paginator(data, 25)
    page_number = request.GET.get("page")
    context = {
        "data": paginator.get_page(page_number),
        "title": "Line Items Export to CSV",
        "url_name": "lineitem-report",
    }
    return render(request, "lineitem-report.html", context)


def financial_structure_report(request):
    fsm = FinancialStructureManager()
    data = fsm.financial_structure_dataframe()
    if not data.empty:
        data = fsm.financial_structure_styler(data)
        data = data.to_html(bold_rows=False)
    else:
        messages.info(request, "No data")
        data = ""
    return render(
        request,
        "financial-structure-report.html",
        {
            "table": data,
            "title": "Financial Structure Report",
            "url_name": "financial-structure-report",
        },
    )


"""
Writes line item report to csv.
"""


def csv_line_items(request):
    data = (
        LineItem.objects.annotate(doc=Concat("docno", V("-"), "lineno"))
        .order_by("fundcenter", "costcenter", "fund", "docno", "lineno")
        .filter(balance__gt=0)
    )
    field_names = [field.name for field in data.model._meta.fields]
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="lineitems.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow(field_names)
    for obj in data:
        writer.writerow([getattr(obj, field) for field in field_names])
    return response


def cost_center_charge_table(request, cc: str, fy: int, period: int):
    cc = cc.upper()
    table = ""
    data = CostCenterChargeMonthly.objects.filter(costcenter=cc, fy=fy, period=period)
    if data:
        df = utils.BFTDataFrame(CostCenterChargeMonthly).build(data).set_index(["Cost Center", "Fund"])
        df = df[["Amount", "Fiscal Year", "Period"]]
        df = df.style.format(thousands=",")
        table = df.to_html()
    else:
        messages.info(request, f"There are no charges agains {cc} for FY {fy} and period {period}")
    return render(request, "costcenter-monthly-charge-data.html", {"table": table})


def capital_forecasting_set_initial(request):
    initial = {
        "capital_project": "",
        "fund": "",
        "fy": BftStatusManager().fy(),
    }
    if not len(request.GET):
        return initial

    initial["capital_project"] = CapitalProjectManager().get_request(request)
    initial["fund"] = FundManager().get_request(request)
    initial["fy"] = set_fy(request)

    return initial


def capital_forecasting_estimates(request):
    initial = capital_forecasting_set_initial(request)
    form = SearchCapitalEstimatesForm(initial=initial)

    context = {
        **initial,
        "title": f"{initial['capital_project']} Capital Forecasting Estimates",
        "url_name": "capital-forecasting-estimates",
        "form_filter": True,
        "form": form,
        "table": "All fields are mandatory.",
    }

    if len(request.GET):
        estimates = capitalforecasting.EstimateReport(initial["fund"], initial["fy"], initial["capital_project"])
        estimates.dataframe()
        if estimates.df.size:
            estimates.df.quarter = "Q" + estimates.df.quarter
            data = estimates.df.to_json(orient="records")
            context["data"] = data
            context["table"] = estimates.to_html()
            context["query_string"] = request.GET.urlencode()

        else:
            messages.warning(request, "Capital forecasting estimate is empty")
    return render(request, "capital-forecasting-estimates.html", context)


def capital_forecasting_fears(request):
    initial = capital_forecasting_set_initial(request)
    form = SearchCapitalFearsForm(initial=initial)

    context = {
        **initial,
        "title": f"{initial['capital_project']} Capital FEAR Estimates",
        "url_name": "capital-forecasting-fears",
        "form_filter": True,
        "form": form,
        "table": "All fields are mandatory.",
    }

    if len(request.GET):
        quarterly = capitalforecasting.FEARStatusReport(initial["fund"], initial["fy"], initial["capital_project"])
        quarterly.dataframe()
        if quarterly.df.size:
            quarterly.df.Quarters = "Q" + quarterly.df.Quarters
            context["data"] = quarterly.df.to_json(orient="records")
            context["table"] = quarterly.to_html()
            context["query_string"] = request.GET.urlencode()

        else:
            messages.warning(request, "Capital forecasting FEARS is empty")

    return render(request, "capital-forecasting-fears.html", context)


def capital_historical_outlook(request):
    initial = capital_forecasting_set_initial(request)
    form = SearchCapitalHistoricalForm(initial=initial)

    context = {
        **initial,
        "title": f"{initial['capital_project']} Capital Historical Outlook",
        "url_name": "capital-historical-outlook",
        "form_filter": True,
        "form": form,
        "table": "All fields are mandatory.",
    }

    if len(request.GET):
        outlook = capitalforecasting.HistoricalOutlookReport(
            initial["fund"], initial["fy"], initial["capital_project"]
        )
        outlook.dataframe()
        if outlook.df.size:
            context["data"] = outlook.df.to_json(orient="records")
            context["table"] = outlook.to_html()
        else:
            messages.warning(request, "Capital forecasting historical outlook is empty")

    return render(request, "capital-historical-outlook.html", context)


def capital_forecasting_ye_ratios(request):
    initial = capital_forecasting_set_initial(request)
    form = SearchCapitalYeRatiosForm(initial=initial)

    context = {
        **initial,
        "title": f"{initial['capital_project']} Capital Forecasting Year End Ratios",
        "url_name": "capital-forecasting-ye-ratios",
        "form_filter": True,
        "form": form,
        "table": "All fields are mandatory.",
    }
    if len(request.GET):
        outlook = capitalforecasting.HistoricalOutlookReport(
            initial["fund"], initial["fy"], initial["capital_project"]
        )
        outlook.dataframe()
        context["data"] = outlook.df.to_json(orient="records")
        context["table"] = outlook.to_html()

    return render(request, "capital-forecasting-ye-ratios.html", context)


def capital_forecasting_dashboard(request):
    fund = capital_project = ""

    initial = capital_forecasting_set_initial(request)
    form = SearchCapitalForecastingDashboardForm(initial=initial)

    context = {
        **initial,
        "title": f"{initial['capital_project']} Capital Forecasting Year End Ratios",
        "url_name": "capital-forecasting-ye-ratios",
        "form_filter": True,
        "form": form,
        "table": "All fields are mandatory.",
    }

    if len(request.GET):
        fund, fy, capital_project = initial["fund"], initial["fy"], initial["capital_project"]
        estimates = capitalforecasting.EstimateReport(fund, fy, capital_project)
        estimates.dataframe()
        if estimates.df.size:
            estimates.df.quarter = "Q" + estimates.df.quarter
            context["source_estimates"] = estimates.df.to_json(orient="records")
        else:
            messages.warning(request, "Capital forecasting estimate is empty")

        quarterly = capitalforecasting.FEARStatusReport(fund, fy, capital_project)
        quarterly.dataframe()
        if quarterly.df.size:
            quarterly.df.Quarters = "Q" + quarterly.df.Quarters
            context["source_quarterly"] = quarterly.df.to_json(orient="records")
        else:
            messages.warning(request, "Capital forecasting FEARS is empty")

        outlook = capitalforecasting.HistoricalOutlookReport(fund, fy, capital_project)
        outlook.dataframe()
        if outlook.df.size:
            context["source_outlook"] = outlook.df.to_json(orient="records")
        else:
            messages.warning(request, "Capital forecasting historical outlook is empty")

    return render(request, "capital-forecasting-dashboard.html", context)
