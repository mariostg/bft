import logging

import pandas as pd
from django.db.models import F, IntegerField, Q, QuerySet, Sum, Value
from django.db.models.functions import Cast

from bft import conf
from bft.models import (CostCenter, CostCenterAllocation, CostCenterManager,
                        ForecastAdjustment, FundCenter, FundCenterAllocation,
                        FundCenterManager, FundManager, LineForecast, LineItem)
from reports.models import (CostCenterInYearEncumbrance,
                            CostCenterMonthlyAllocation,
                            CostCenterMonthlyEncumbrance,
                            CostCenterMonthlyForecastAdjustment,
                            CostCenterMonthlyLineItemForecast)
from utils.dataframe import BFTDataFrame

logger = logging.getLogger("django")


class InYearReport:

    def __init__(self, fy, costcenter: str = None, fund: str = None, quarter=None):
        fy = str(fy)
        if len(fy) != 4 or not fy.isdigit():
            raise ValueError("Fiscal Year must be 4 digits long.")
        try:
            self.costcenter = costcenter.upper()
        except AttributeError:
            self.costcenter = None
        try:
            self.fund = fund.upper()
        except AttributeError:
            self.fund = None
        self.fy = fy


class MonthlyReport:

    def __init__(self, fy, period, costcenter: str = None, fund: str = None, quarter=None):
        fy = str(fy)
        period = str(period)
        try:
            self.costcenter = costcenter.upper()
        except AttributeError:
            self.costcenter = None
        try:
            self.fund = fund.upper()
        except AttributeError:
            self.fund = None
        self.fy = fy
        if conf.is_quarter(quarter):
            self.quarter = quarter
        elif quarter:
            raise ValueError(
                f"{quarter} is not a valid quarter.  Expected value is one of {(', ').join(map(str,conf.QUARTERKEYS))}"
            )
        if conf.is_period(period):
            self.period = period
        else:
            self.period = None


class CostCenterMonthlyAllocationReport(MonthlyReport):
    def sum_allocation_cost_center(self) -> QuerySet:
        """Given a FY, quarter and period, sum the allocation of cost centers grouped by fund and period."""
        if not all([self.fy, self.quarter, self.period]):
            raise ValueError(f"Argument cannot be none in FY={self.fy}, quarter={self.quarter}, period={self.period}")
        grouped_sum = (
            CostCenterAllocation.objects.filter(quarter=self.quarter)
            .values("costcenter__costcenter", "fund__fund")
            .annotate(
                allocation=Sum("amount"),
                fy=Value(self.fy),
                period=Value(self.period),
                source=Value(""),
                costcenter=F("costcenter__costcenter"),
                fund=F("fund__fund"),
            )
        )
        return grouped_sum.values(
            "allocation",
            "fund",
            "fy",
            "period",
            "source",
            "costcenter",
        )

    def insert_grouped_allocation(self, lines: QuerySet) -> int:
        """Delete all allocations for a given FY and period and insert allocations from given queryset of lines."""
        if len(lines) == 0:
            logger.info("There are no allocations to insert given the queryset provided.")
            # return 0  otherwise, on delete an allocation, it will exit here because queryset is empty.
        CostCenterMonthlyAllocation.objects.filter(fy=self.fy, period=self.period).delete()
        md = CostCenterMonthlyAllocation.objects.bulk_create([CostCenterMonthlyAllocation(**q) for q in lines])
        return len(md)

    def dataframe(self) -> pd.DataFrame:
        """Create a pandas dataframe using CostCenterMonthlyAllocation data as source
        for the given FY and period.
        Returns:
            pandas.DataFrame: dataframe containing cost center monthly data with the following colums:
            "ID",
            "Fund",
            "Source",
            "Cost Center",
            "Fund Center",
            "FY",
            "Period",
            allocation
        """
        qst = (
            CostCenterMonthlyAllocation.search.fy(self.fy)
            .period(self.period)
            .fund(self.fund)
            .costcenter(self.costcenter)
        )

        if qst.count() == 0:
            return pd.DataFrame()
        monthly_df = BFTDataFrame(CostCenterMonthlyAllocation)
        return monthly_df.build(qst)


class CostCenterMonthlyForecastLineItemReport(MonthlyReport):
    def sum_forecast_line_item(self) -> QuerySet:
        grouped_sum = LineForecast.objects.values("lineitem__costcenter", "lineitem__fund").annotate(
            line_item_forecast=Sum("forecastamount"),
            fy=Value(self.fy),
            period=Value(self.period),
            source=Value(""),
            costcenter=F("lineitem__costcenter__costcenter"),
            fund=F("lineitem__fund"),
        )

        return grouped_sum.values(
            "line_item_forecast",
            "fund",
            "fy",
            "period",
            "source",
            "costcenter",
        )

    def insert_grouped_forecast_line_item(self, lines: QuerySet) -> int:
        if len(lines) == 0:
            logger.info("There are no line items.")
            return 0
        CostCenterMonthlyLineItemForecast.objects.filter(fy=self.fy, period=self.period).delete()
        md = CostCenterMonthlyLineItemForecast.objects.bulk_create(
            [CostCenterMonthlyLineItemForecast(**q) for q in lines]
        )
        return len(md)

    def dataframe(self) -> pd.DataFrame:
        """Create a pandas dataframe using CostCenterMonthlyLineItemForecast data as source
        for the given FY and period.
        Returns:
            pandas.DataFrame: dataframe containing cost center monthly data with the following colums:
            "ID",
            "Fund",
            "Source",
            "Cost Center",
            "Fund Center",
            "FY",
            "Period",
            line_item_forecast
        """
        qst = (
            CostCenterMonthlyLineItemForecast.search.fy(self.fy)
            .period(self.period)
            .fund(self.fund)
            .costcenter(self.costcenter)
        )

        if qst.count() == 0:
            return pd.DataFrame()
        monthly_df = BFTDataFrame(CostCenterMonthlyLineItemForecast)
        return monthly_df.build(qst)


class CostCenterMonthlyForecastAdjustmentReport(MonthlyReport):

    def sum_forecast_adjustments(self) -> QuerySet:
        grouped_sum = ForecastAdjustment.objects.values("costcenter__costcenter", "fund__fund").annotate(
            forecast_adjustment=Sum("amount"),
            fy=Value(self.fy),
            period=Value(self.period),
            source=Value(""),
            costcenter=F("costcenter__costcenter"),
            fund=F("fund__fund"),
        )

        return grouped_sum.values(
            "forecast_adjustment",
            "fund",
            "fy",
            "period",
            "source",
            "costcenter",
        )

    def insert_grouped_forecast_adjustment(self, lines: QuerySet) -> int:
        if len(lines) == 0:
            logger.info("There are no forecast adjustments to insert")
        CostCenterMonthlyForecastAdjustment.objects.filter(fy=self.fy, period=self.period).delete()
        md = CostCenterMonthlyForecastAdjustment.objects.bulk_create(
            [CostCenterMonthlyForecastAdjustment(**q) for q in lines]
        )
        return len(md)

    def dataframe(self) -> pd.DataFrame:
        """Create a pandas dataframe using CostCenterMonthlyForecastAdjustment data as source
        for the given FY and period.
        Returns:
            pandas.DataFrame: dataframe containing cost center monthly data with the following colums:
            "ID",
            "Fund",
            "Source",
            "Cost Center",
            "Fund Center",
            "FY",
            "Period",
            Forecast Adjustment
        """
        qst = (
            CostCenterMonthlyForecastAdjustment.search.fy(self.fy)
            .period(self.period)
            .fund(self.fund)
            .costcenter(self.costcenter)
        )
        if qst.count() == 0:
            return pd.DataFrame()
        monthly_df = BFTDataFrame(CostCenterMonthlyForecastAdjustment)
        return monthly_df.build(qst)


class CostCenterMonthlyEncumbranceReport(MonthlyReport):

    def sum_line_items(self) -> QuerySet:
        line_item_group = LineItem.objects.values("costcenter__costcenter", "fund").annotate(
            spent=Sum("spent"),
            commitment=Sum("balance", filter=Q(doctype="CO")),
            pre_commitment=Sum("balance", filter=Q(doctype="PC")),
            fund_reservation=Sum("balance", filter=Q(doctype="FR")),
            balance=Sum("balance"),
            working_plan=Sum("workingplan"),
            fy=Value(self.fy),
            period=Value(self.period),
            source=Value(""),
            costcenter=F("costcenter__costcenter"),
        )
        return line_item_group.values(
            "spent",
            "fund",
            "commitment",
            "pre_commitment",
            "fund_reservation",
            "balance",
            "working_plan",
            "fy",
            "period",
            "source",
            "costcenter",
        )

    def insert_line_items(self, lines: QuerySet) -> int:
        if len(lines) == 0:
            logger.info("There are no lines to insert")
            return 0
        CostCenterMonthlyEncumbrance.objects.filter(fy=self.fy, period=self.period).delete()
        md = CostCenterMonthlyEncumbrance.objects.bulk_create([CostCenterMonthlyEncumbrance(**q) for q in lines])
        return len(md)

    def dataframe(self) -> pd.DataFrame:
        """Create a pandas dataframe using CostCenterMonthly data as source for the given FY and period.

        Returns:
            pandas.DataFrame: dataframe containing cost center monthly data with the following columns :
            "ID",
            "Fund",
            "Source",
            "Cost Center",
            "Fund Center",
            "FY",
            "Period",
            "Spent",
            "Commitment",
            "Pre Commitment",
            "Fund Reservation",
            "Balance",
            "Working Plan"
        """
        qst = (
            CostCenterMonthlyEncumbrance.search.fy(self.fy)
            .period(self.period)
            .fund(self.fund)
            .costcenter(self.costcenter)
        )
        if qst.count() == 0:
            return pd.DataFrame()
        monthly_df = BFTDataFrame(CostCenterMonthlyEncumbrance)
        return monthly_df.build(qst)


class CostCenterScreeningReport:
    def __init__(self):
        self.fcm = FundCenterManager()
        self.ccm = CostCenterManager()

    def fund_center_alloc_to_dict(self, alloc: QuerySet[FundCenterAllocation]) -> dict:
        lst = {}
        try:
            iter(alloc)
        except TypeError:
            alloc = [alloc]  # when one item only in queryset
        for item in alloc:
            _id = item.fundcenter.id
            fc = item.fundcenter
            pid = fc.fundcenter_parent.id
            d = {
                "Cost Element": fc.fundcenter,
                "Cost Element Name": fc.shortname,
                "Fund Center ID": fc.id,
                "Parent ID": pid,
                "Fund": item.fund.fund,
                "Path": fc.sequence,
                "Parent Path": fc.fundcenter_parent.sequence,
                "Parent Fund Center": fc.fundcenter_parent.fundcenter,
                "Allocation": float(item.amount),
                "Type": "FC",
            }
            lst[_id] = d
        return lst

    def cost_center_alloc_to_dict(self, alloc: QuerySet[CostCenterAllocation]) -> dict:
        lst = {}
        d = {}
        for item in alloc:
            _id = item.costcenter.id
            cc = item.costcenter
            pid = cc.costcenter_parent.id
            d = {
                "Cost Element": cc.costcenter,
                "Cost Element Name": cc.shortname,
                "Fund Center ID": cc.id,
                "Fund": cc.fund.fund,
                "Parent ID": pid,
                "Path": cc.sequence,
                "Parent Path": cc.costcenter_parent.sequence,
                "Parent Fund Center": cc.costcenter_parent.fundcenter,
                "Allocation": float(item.amount),
                "Type": "CC",
            }
            lst[_id] = d
        return lst

    def cost_element_allocations(self, fundcenter: str, fund: str, fy: int, quarter: int) -> dict:
        """Produce a dictionay of allocation including all descendants of the specified fund center.  The key element of each entry is the id of the cost element.

        Args:
            fundcenter (str): Fund Center
            fund (str): Fund.
            fy (str): Fiscal Year.  Required for allocation
            quarter (str): Quarter. Required for allocation.

        Returns:
            dict: A dictionary of allocation for all descendants of the specified fund center.
        """
        root = self.fcm.fundcenter(fundcenter)
        alloc_cc = {}
        alloc_fc = {}

        fund = FundManager().fund(fund)
        if not fund:
            return {}
        alloc_fc = (
            FundCenterAllocation.objects.descendants_fundcenter(root).fund(fund).fy(fy).quarter(quarter)
        )
        alloc_fc = self.fund_center_alloc_to_dict(alloc_fc)

        alloc_cc = (
            CostCenterAllocation.objects.descendants_costcenter(root).fund(fund).fy(fy).quarter(quarter)
        )
        alloc_cc = self.cost_center_alloc_to_dict(alloc_cc)

        return {**alloc_fc, **alloc_cc}

    def cost_element_line_items(self, fundcenter: str, fund, doctype=None) -> dict:
        """Produce a dictionary of line items including forecast, CO, PC, FR, Working Plan, Spent, Balance.  If fundcenter is specified, all decendants will be included.  Data will be grouped by cost center.

        Args:
            fundcenter (str): Parent Fund center.
            fund (str): Fund.
            doctype (str, optional): Document Type. Defaults to None.

        Returns:
            dict: _description_
        """
        lines = LineItem.objects.all()
        fc = FundCenter.objects.get(fundcenter=fundcenter.upper())
        path = fc.sequence
        ccs = CostCenter.objects.filter(sequence__startswith=path)
        lines = lines.filter(costcenter__in=ccs)
        lines = lines.filter(fund=fund.upper())
        if doctype:
            lines = lines.filter(doctype=doctype.upper())

        def caster(value):
            return Cast(value, IntegerField())

        lines = lines.values("costcenter__costcenter", "costcenter__sequence", "costcenter", "fund").annotate(
            Working_plan=caster(Sum("workingplan")),
            Spent=caster(Sum("spent")),
            Balance=caster(Sum("balance")),
            Forecast=caster(Sum("fcst__forecastamount", default=0)),
            CO=caster(Sum("balance", filter=Q(doctype="CO"), default=0)),
            PC=caster(Sum("balance", filter=Q(doctype="PC"), default=0)),
            FR=caster(Sum("balance", filter=Q(doctype="FR"), default=0)),
        )

        line_dict = {}
        for item in lines:
            d = {
                "Cost Element": item["costcenter__costcenter"],
                "Costcenter_ID": item["costcenter"],
                "Working Plan": item["Working_plan"],
                "Spent": item["Spent"],
                "Balance": item["Balance"],
                "Forecast": item["Forecast"],
                "CO": item["CO"],
                "PC": item["PC"],
                "FR": item["FR"],
                "Path": item["costcenter__sequence"],
            }
            line_dict[item["costcenter"]] = d
        return line_dict

    def id_to_sequence(self, data: dict) -> dict:
        """REbuild a dictionary by switching the key with the path of the cost element

        Args:
            data (dict): A dictinary who has a path (sequence No) as part of its content for each entry.

        Returns:
            dict: A dictionary whose key is the path of the cost element
        """
        ids = {}

        for _, v in data.items():
            ids[v["Path"]] = v
        return ids

    def allocation_rollup(self, alloc: dict) -> dict:
        """Update the financial data of the specified dict by summing up the numbers based on parent hierarchy.

        Args:
            alloc (dict): Allocations to process

        Returns:
            dict: A dictionary which financial data is rolled up.
        """

        for _, item in alloc.items():
            parent_path = alloc.get(item["Parent Path"], {"Path": None})["Path"]
            if parent_path:
                for p in alloc:
                    if alloc[p]["Path"] == parent_path:
                        continue
                    if parent_path in alloc[p]["Path"]:
                        alloc[parent_path]["Spent"] += item["Spent"]

        return alloc

    def init_fin_values(self, allocation: dict) -> dict:
        init_values = {
            "CO": 0,
            "PC": 0,
            "FR": 0,
            "Working Plan": 0,
            "Balance": 0,
            "Spent": 0,
            "Forecast": 0,
            "Forecast Adjustment": 0,
            "Variance": 0,
        }
        return {**allocation, **init_values}

    def dict_html_table(self, data: dict) -> str:
        headings = [
            "Cost Element",
            "Cost Element Name",
            "Fund",
            "Spent",
            "Balance",
            "Working Plan",
            "CO",
            "PC",
            "FR",
            "Forecast",
            "Forecast Adjustment",
            "Forecast Total",
            "Allocation",
            "Variance",
        ]
        _sorted = list(data.keys())
        _sorted.sort()
        thead = ""
        for h in headings:
            thead += f"<th>{h}</th>"
        thead = f"<thead><tr>{thead}</tr></thead>"

        trows = ""
        for s in _sorted:
            tr = ""
            for h in headings:
                level = len(data[s]["Path"].split("."))
                if h == "Path" or h == "Parent Path":
                    continue  # don't show these columns
                match h:
                    case h if h in [
                        "Spent",
                        "Balance",
                        "Working Plan",
                        "CO",
                        "PC",
                        "FR",
                        "Forecast",
                        "Allocation",
                        "Variance",
                    ]:
                        tr += f"<td>{data[s][h]:,}</td>"
                    case _:
                        tr += f"<td>{data[s][h]}</td>"
            tr = f"<tr class='level{level}'>{tr}</tr>"
            trows += tr

        table = f"<table id='screeningreport'>{thead}<tbody>{trows}</tbody></table>"

        return table


class AllocationStatusReport:
    def fund_center_alloc_to_dict(self, alloc: QuerySet[FundCenterAllocation]) -> dict:
        if not alloc:
            return {}
        lst = {}
        try:
            iter(alloc)
        except TypeError:
            alloc = [alloc]
        for item in alloc:
            id = item.fundcenter.id
            fc = item.fundcenter
            pid = fc.fundcenter_parent.id
            d = {
                "Cost Element": fc.fundcenter,
                "Cost Element Name": fc.shortname,
                "Fund Center ID": fc.id,
                "Parent ID": pid,
                "Path": fc.sequence,
                "Parent Path": fc.fundcenter_parent.sequence,
                "Allocation": float(item.amount),
                "Type": "FC",
            }
            lst[id] = d
        return lst

    def fund_center_set_sub_id(self, alloc: dict) -> dict:
        d = {}
        for id in alloc:
            pid = alloc[id]["Parent ID"]
            if not d.get(id):
                d[id] = alloc.get(id)
                d[id]["sub_id"] = []
            if not d.get(pid):
                d[pid] = alloc.get(pid, {})
                d[pid]["sub_id"] = [id]
            else:
                d[pid]["sub_id"].append(id)
        return d

    def cost_center_alloc_to_dict(self, alloc: QuerySet[CostCenterAllocation]) -> dict:
        lst = {}
        d = {}
        for item in alloc:
            id = item.costcenter.id
            cc = item.costcenter
            pid = cc.costcenter_parent.id
            d = {
                "Cost Element": cc.costcenter,
                "Cost Element Name": cc.shortname,
                "Fund Center ID": cc.id,
                "Parent ID": pid,
                "Path": cc.sequence,
                "Parent Path": cc.costcenter_parent.sequence,
                "Allocation": float(item.amount),
                "Type": "CC",
            }
            lst[id] = d
        return lst

    def main(self, fundcenter: str, fund: str, fy: int, quarter: int) -> str:
        if not fundcenter or not fund or not fy or not quarter:
            return ""
        fcm = FundCenterManager()
        root = fcm.fundcenter(fundcenter)
        if not root:
            return ""

        alloc_data = CostCenterScreeningReport().cost_element_allocations(fundcenter, fund, fy, quarter)
        data = self.fund_center_set_sub_id({**alloc_data})

        for v in data.values():
            ce = v.get("Cost Element")
            if not ce:
                continue

            tbody = ""
            zebra = {0: "fc-even", -1: "fc-odd"}
            odd = 0
            for allocation in data.values():
                ce = allocation.get("Cost Element")
                if not ce or allocation.get("Type") == "CC":
                    continue
                odd = ~odd

                trow = f"<tr class='{zebra[odd]}'>"
                trow += f"<td>{ce}</td>"
                parent_allocation = int(allocation.get("Allocation"))
                if parent_allocation:
                    trow += f"<td class='numbers'>{parent_allocation:,}</td>"
                    subtotal = variation = 0
                    sub_id = allocation.get("sub_id")
                    sub_table = ""
                    if sub_id:
                        sub_table = "<table>"
                        for sid in sub_id:
                            sub_row = "<tr>"
                            sub_data = data.get(sid)
                            sub_allocation = int(sub_data.get("Allocation", 0))
                            sub_ce = sub_data.get("Cost Element")
                            sub_row += f"<td>{sub_ce}</td><td class='numbers'> {sub_allocation:,}</td></tr>"
                            subtotal += sub_allocation
                            sub_table += sub_row

                        variation = parent_allocation - subtotal
                        if variation:
                            sub_table += f"<tr><td>Sub Total</td><td class='numbers'>{subtotal:,}</td></tr><tr><td class='alert--warning'>Variation</td><td class='numbers'>{variation:,}</td></tr>"
                        else:
                            sub_table += f"<tr><td>Sub Total</td><td class='numbers'>{subtotal:,}</td></tr>"
                        sub_table = f"<td>{sub_table}</table></td>"
                    else:
                        sub_table = "<td class='alert--info'>No Sub Allocation</td>"

                    trow += f"{sub_table}"
                tbody += trow
            thead = "<thead><th>Fund Center</th><th>Allocation</th><th>Sub-Allocations</th></thead>"
            table = f"<table class=''>{thead}{tbody}</table>"
            return table


class CostCenterMonthlyPlanReport(MonthlyReport):

    def __init__(self, fy, period, costcenter=None, fund=None):
        self.params = {"fy": fy, "period": period, "costcenter": costcenter, "fund": fund}

    def dataframe(self) -> pd.DataFrame:
        if all([self.params["fy"], self.params["period"]]) == False:
            return pd.DataFrame()
        encumbrance = CostCenterMonthlyEncumbranceReport(**self.params)
        allocation = CostCenterMonthlyAllocationReport(**self.params)
        forecast_adjustment = CostCenterMonthlyForecastAdjustmentReport(**self.params)
        forecast_line_items = CostCenterMonthlyForecastLineItemReport(**self.params)

        on_grouping = [
            "Fund",
            "Source",
            "Cost Center",
            "FY",
            "Period",
        ]
        encumbrance_fields = [
            "Spent",
            "Commitment",
            "Pre Commitment",
            "Fund Reservation",
            "Balance",
            "Working Plan",
        ]

        report_fields = on_grouping[0:3] + encumbrance_fields
        allocation__fields = ["Allocation"]
        forecast_adjustment_fields = ["Forecast Adjustment"]
        forecast_line_item_fields = ["Line Item Forecast"]

        encumbrance_df = encumbrance.dataframe()
        allocation_df = allocation.dataframe()
        forecast_adjustment_df = forecast_adjustment.dataframe()
        forecast_line_items_df = forecast_line_items.dataframe()

        df_report = pd.DataFrame()
        if len(encumbrance_df):
            encumbrance_df = encumbrance_df[[*on_grouping, *encumbrance_fields]]
            df_report = encumbrance_df
        else:
            return df_report

        if len(allocation_df):
            report_fields.extend(allocation__fields)
            allocation_df = allocation_df[[*on_grouping, *allocation__fields]]
            if not df_report.empty:
                df_report = df_report.merge(allocation_df, how="outer", on=on_grouping)
            else:
                df_report = allocation_df

        if len(forecast_adjustment_df):
            report_fields.extend(forecast_adjustment_fields)
            forecast_adjustment_df = forecast_adjustment_df[[*on_grouping, *forecast_adjustment_fields]]
            if not df_report.empty:
                df_report = df_report.merge(forecast_adjustment_df, how="outer", on=on_grouping)
            else:
                df_report = forecast_adjustment_df
        else:
            df_report["Forecast Adjustment"] = 0

        if len(forecast_line_items_df):
            report_fields.extend(forecast_line_item_fields)
            forecast_line_items_df = forecast_line_items_df[[*on_grouping, *forecast_line_item_fields]]
            if not df_report.empty:
                df_report = df_report.merge(forecast_line_items_df, how="outer", on=on_grouping)
            else:
                df_report = forecast_line_items_df

        if not df_report.empty:
            df_report.fillna(0, inplace=True)
            df_report["Total Forecast"] = df_report["Forecast Adjustment"] + df_report["Line Item Forecast"]
            df_report = df_report[report_fields]
            df_report

        df_report["% Spent"] = df_report["Spent"] / df_report["Working Plan"]
        df_report["% Commit"] = (df_report["Spent"] + df_report["Commitment"]) / df_report["Working Plan"]
        if len(allocation_df):
            df_report["% Programmed"] = df_report["Working Plan"] / df_report["Allocation"]

        return df_report


class CostCenterInYearEncumbranceReport(InYearReport):

    def sum_line_items(self) -> QuerySet:
        line_item_group = LineItem.objects.values("costcenter__costcenter", "fund").annotate(
            spent=Sum("spent"),
            commitment=Sum("balance", filter=Q(doctype="CO")),
            pre_commitment=Sum("balance", filter=Q(doctype="PC")),
            fund_reservation=Sum("balance", filter=Q(doctype="FR")),
            balance=Sum("balance"),
            working_plan=Sum("workingplan"),
            fy=Value(self.fy),
            source=Value(""),
            costcenter=F("costcenter__costcenter"),
        )
        return line_item_group.values(
            "spent",
            "fund",
            "commitment",
            "pre_commitment",
            "fund_reservation",
            "balance",
            "working_plan",
            "fy",
            "source",
            "costcenter",
        )

    def insert_line_items(self, lines: QuerySet) -> int:
        if len(lines) == 0:
            logger.info("There are no lines to insert")
            return 0
        CostCenterInYearEncumbrance.objects.filter(fy=self.fy).delete()
        md = CostCenterInYearEncumbrance.objects.bulk_create([CostCenterInYearEncumbrance(**q) for q in lines])
        return len(md)

    def dataframe(self) -> pd.DataFrame:
        """Create a pandas dataframe using CostCenterInYear data as source for the given FY.

        Returns:
            pandas.DataFrame: dataframe containing cost center monthly data with the following columns :
            "ID",
            "Fund",
            "Source",
            "Cost Center",
            "Fund Center",
            "FY",
            "Spent",
            "Commitment",
            "Pre Commitment",
            "Fund Reservation",
            "Balance",
            "Working Plan"
        """
        inyear_df = BFTDataFrame(CostCenterMonthlyEncumbrance)
        qst = CostCenterMonthlyEncumbrance.objects.filter(fy=self.fy)
        if self.fund:
            qst = qst.filter(fund=self.fund)
        if self.costcenter:
            qst = qst.filter(costcenter=self.costcenter)
        if qst.count() == 0:
            return pd.DataFrame()
        inyear_df = inyear_df.build(qst)
        inyear_df.Period = inyear_df.Period.astype("int")
        inyear_df = inyear_df.sort_values("Period")
        print(inyear_df.dtypes)
        return inyear_df
