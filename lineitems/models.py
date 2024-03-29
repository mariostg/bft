from django.db import models
from django.db.models import F
from django.contrib import messages
import logging
from costcenter.models import CostCenter, CostCenterManager
from users.models import BftUser
from utils.dataframe import BFTDataFrame
from django.forms.models import model_to_dict
import pandas as pd
import numpy as np

logger = logging.getLogger("uploadcsv")


class LineItemManager(models.Manager):
    def cost_center(self, costcenter: str):
        costcenter = costcenter.upper()
        try:
            cc = CostCenter.objects.get(costcenter=costcenter)
        except CostCenter.DoesNotExist:
            return None
        return self.filter(costcenter=cc)

    def has_line_items(self, costcenter: "CostCenter") -> bool:
        return LineItem.objects.filter(costcenter=costcenter).exists()

    def line_item_dataframe(self, fund: str = None, doctype: str = None) -> pd.DataFrame:
        """Prepare a pandas dataframe of the DRMIS line items.  Columns are renamed
        with a more friendly name.

        Returns:
            pd.DataFrame: A dataframe of DRMIS line items
        """
        data = LineItem.objects.all()
        if fund:
            data = data.filter(fund=fund.upper())
        if doctype:
            data = data.filter(doctype=doctype.upper())
        if data:
            df = BFTDataFrame(LineItem).build(data)
            df["CO"] = np.where(df["Doctype"] == "CO", df["Balance"], 0)
            df["PC"] = np.where(df["Doctype"] == "PC", df["Balance"], 0)
            df["FR"] = np.where(df["Doctype"] == "FR", df["Balance"], 0)
            return df
        else:
            return pd.DataFrame({})

    def line_item_detailed_dataframe(self, fund=None, doctype=None) -> pd.DataFrame:
        """
        Prepare a pandas dataframe of merged line items, forecast line items and cost center.

        Returns:
            pd.DataFrame : A dataframe of line items including forecast.
        """
        li_df = self.line_item_dataframe(fund=fund, doctype=doctype)
        if li_df.empty:
            return li_df
        if len(li_df) > 0:
            fcst_df = LineForecastManager().forecast_dataframe()
            cc_df = CostCenterManager().cost_center_dataframe(CostCenter.objects.all())

            if len(fcst_df) > 0:
                li_df = pd.merge(li_df, fcst_df, how="left", on="Lineitem_ID").fillna(0)
                li_df["Forecast"] = li_df["Forecast"].astype("int")
            else:
                li_df["Forecast"] = 0
            li_df = pd.merge(li_df, cc_df, how="left", on="Costcenter_ID")

        return li_df


class LineItem(models.Model):
    docno = models.CharField(max_length=10)
    lineno = models.CharField(max_length=7)  # lineno : acctassno
    spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    workingplan = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fundcenter = models.CharField(max_length=6)
    fund = models.CharField(max_length=4)
    costcenter = models.ForeignKey(CostCenter, on_delete=models.RESTRICT)
    internalorder = models.CharField(max_length=7, null=True, blank=True)
    doctype = models.CharField(max_length=2, null=True, blank=True)
    enctype = models.CharField(max_length=21)
    linetext = models.CharField(max_length=50, null=True, blank=True, default="")
    predecessordocno = models.CharField(max_length=20, null=True, blank=True, default="")
    predecessorlineno = models.CharField(max_length=3, null=True, blank=True, default="")
    reference = models.CharField(max_length=16, null=True, blank=True, default="")
    gl = models.CharField(max_length=5)
    duedate = models.DateField(null=True, blank=True)
    vendor = models.CharField(max_length=50, null=True, blank=True)
    createdby = models.CharField(max_length=50, null=True, blank=True, default="")
    status = models.CharField(max_length=10, null=True, blank=True, default="")
    fcintegrity = models.BooleanField(default=False)

    # lineitem = models.Manager()
    objects = LineItemManager()

    def __str__(self):
        text = f"{self.enctype} {self.docno}-{self.lineno}"
        return str(text)

    class Meta:
        ordering = ["-docno", "lineno"]
        verbose_name_plural = "Line Items"

    def get_orphan_lines(self, costcenter: str | CostCenter = None):
        """
        Compare the docno and lineno combination in both line item table and
        encumbrance table.  When specifying costcenter, only the lines of the specified cost center will be considered.
        """
        if costcenter:
            if isinstance(costcenter, str):
                try:
                    costcenter = CostCenter.objects.get(costcenter=costcenter.upper())
                except CostCenter.DoesNotExist:
                    return None
            lines = set(LineItem.objects.filter(costcenter=costcenter).values_list("docno", "lineno"))
        else:
            lines = set(LineItem.objects.values_list("docno", "lineno"))

        enc = set(LineItemImport.objects.values_list("docno", "lineno"))
        orphans = lines.difference(enc)

        if costcenter:
            logger.info(f"Found {len(orphans)} orphan lines for cost center {costcenter}.")
        else:
            logger.info(f"Found {len(orphans)} orphan lines considering all cost centers.")

        return orphans

    def mark_orphan_lines(self, orphans: set):
        """Set the status of the line item to orphan.  Because these lines are orphans, their forecast amount is also set to 0 leaving comments and description unaffected.

        Args:
            orphans (set): Lines that need to have their status updated to orphan.
        """
        logger.info("Begin marking orphan lines")
        for o in orphans:
            docno, lineno = o
            try:
                li = LineItem.objects.get(docno=docno, lineno=lineno)
                li.spent = 0
                li.workingplan = 0
                li.balance = 0
                li.status = "orphan"
                li.save()
            except LineItem.DoesNotExist:
                logger.info(f"LineItem {docno} - {lineno} does not exist")
        LineForecast.objects.filter(lineitem__status="orphan").update(forecastamount=0)

    def insert_line_item(self, ei: "LineItemImport"):
        """
        Insert the encumbrance line in line item table.  Such line is set as new in the
        status field.
        """
        cc = CostCenter.objects.get(costcenter=ei.costcenter)
        di = model_to_dict(ei)
        di["costcenter"] = cc
        del di["id"]
        target = LineItem(**di)
        target.status = "New"
        target.save()
        return target.id

    def update_line_item(self, li: "LineItem", ei: "LineItemImport"):
        """
        Update line items fields using values from encumbrance line.
        """
        cc = None
        try:
            cc = CostCenter.objects.get(costcenter=ei.costcenter)
        except CostCenter.DoesNotExist:
            pass  # for now.

        if cc:
            li.costcenter = cc
            li.fundcenter = ei.fundcenter
            li.spent = ei.spent
            li.workingplan = ei.workingplan
            li.balance = ei.balance
            li.fund = ei.fund
            li.status = "Updated"
            # TODO More to come
            li.save()
            return li
        else:
            return None

    def import_lines(self):
        """
        import_line function relies on content of encumbrance_import.  It is
        responsible to import new lines, update current ones and zero out lines
        no longer in DRMIS
        """

        count = LineItem.objects.all().update(status="old")
        logger.info(f"Set {count} lines to old.")

        encumbrance = LineItemImport.objects.all()
        logger.info(f"Retreived {encumbrance.count()} encumbrance lines.")
        for e in encumbrance:
            try:
                target = LineItem.objects.get(docno=e.docno, lineno=e.lineno)
                self.update_line_item(target, e)
            except LineItem.DoesNotExist:
                self.insert_line_item(e)

    def set_fund_center_integrity(self):
        """
        Compare all line items cost center - fund center pair with
        cost center - fund center pair from cost center table.  When comparison
        match for a given line, set its fcintegrity to True.  All fcintegrity are
        set to False to start with.
        """
        logger.info("Fund center integrity check begins.")
        cc = CostCenter.objects.select_related()
        cc_set = set()
        for c in cc:
            cc_set.add((c.costcenter, c.costcenter_parent.fundcenter))

        li = LineItem.objects.select_related()
        li.update(fcintegrity=False)

        for item in li:
            t = (item.costcenter.costcenter, item.fundcenter)
            if t in cc_set:
                item.fcintegrity = True
                item.save()
        logger.info("Fund center integrity check completed.")

    def set_doctype(self):
        logger.info("Set doctype begins")
        types = [
            {"enctype": "Funds Commitment", "doctype": "CO"},
            {"enctype": "Funds Precommitment", "doctype": "PC"},
            {"enctype": "Funds Reservation", "doctype": "FR"},
            {"enctype": "Purchase Order", "doctype": "CO"},
            {"enctype": "Purchase Requisitions", "doctype": "PC"},
        ]
        for t in types:
            li = LineItem.objects.filter(enctype=t["enctype"]).update(doctype=t["doctype"])
            logger.info(f"Set {li} lines to {t['doctype']}")
        logger.info("Set doctype complete")


class LineForecastManager(models.Manager):
    def get_line_forecast(self, lineitem: LineItem) -> "LineForecast | None":
        if hasattr(lineitem, "fcst"):
            return LineForecast.objects.get(lineitem_id=lineitem.id)
        else:
            return None

    def forecast_dataframe(self) -> pd.DataFrame:
        """Prepare a pandas dataframe of the forecast line items.  Columns are renamed
        with a more friendly name.

        Returns:
            pd.DataFrame: A dataframe of forecast lines
        """
        if not LineForecast.objects.exists():
            return pd.DataFrame()
        data = LineForecast.objects.all()
        df = BFTDataFrame(LineForecast).build(data)
        return df

    def update_owner(self, costcenter: CostCenter, new_owner: BftUser, old_owner: BftUser = None) -> int:
        """This function allows for transfer ownership of forecasted lines for a given cost center and optionally the loosing owner.

        Args:
            costcenter (CostCenter): Cost center of choice for which lines will be moved
            new_owner (BftUser): Bft User that will be assigned the lines.
            old_owner (BftUser, optional): Bft User whose lines will be transfered. Defaults to None.. Defaults to None.

        Returns:
            int: Number of lines transfered.
        """

        lines = LineForecast.objects.filter(lineitem__costcenter=costcenter)
        if lines:
            return lines.update(owner=new_owner)

    def set_underforecasted(self, costcenter: CostCenter = None) -> int:
        """Adjust the forecast of line items to match the spent if the forecast is lower than the spent"""
        lines = LineForecast.objects.filter(lineitem__spent__gt=F("forecastamount"))
        if costcenter:
            lines = lines.filter(lineitem__costcenter=costcenter)
        maxlines = lines.count()
        logger.info(f"{maxlines} lines with spent greater than forecast.")
        for li in lines:
            li.forecastamount = li.lineitem.spent
        affected = LineForecast.objects.bulk_update(lines, ["forecastamount"])
        logger.info(f"Forecasted to spent {affected} out of {maxlines} lines")
        return affected

    def set_overforecasted(self, costcenter: CostCenter | str = None) -> int:
        """Adjust the forecast of line items to match the working plan if the forecast is highr than the working plan"""
        lines = LineForecast.objects.filter(lineitem__workingplan__lt=F("forecastamount"))
        if costcenter:
            lines = lines.filter(lineitem__costcenter=costcenter)
        maxlines = lines.count()
        logger.info(f"{maxlines} lines with working plan less than forecast.")
        for li in lines:
            li.forecastamount = li.lineitem.workingplan
        affected = LineForecast.objects.bulk_update(lines, ["forecastamount"])
        logger.info(f"Forecasted to working plan {affected} out of {maxlines} lines")
        return affected

    def set_encumbrance_history_record(self, costcenter: CostCenter = None) -> int:
        """Primarily used during line import, set the working plans, spent and balance values in the LineForecast model for historical purpose.  These will remain uneditable.

        Returns:
            int: Number of lines affected.
        """
        lines = LineItem.objects.filter(status="New")
        if costcenter:
            lines = lines.filter(costcenter=costcenter)
        maxlines = lines.count()
        logger.info(f"{maxlines} new lines need encumbrance record history to be set.")
        counter = 0
        for li in lines:
            counter += 1
            li_fcst = LineForecast(
                lineitem=li,
                spent_initial=li.spent,
                workingplan_initial=li.workingplan,
                balance_initial=li.balance,
            )
            li_fcst.save()
        if counter == maxlines:
            logger.info(f"Encumbrance history set for {counter} out of {maxlines}")
        else:
            logger.warn(f"Encumbrance history set for {counter} out of {maxlines}")
        return counter


class LineForecast(models.Model):
    forecastamount = models.DecimalField("Forecast", max_digits=10, decimal_places=2, default=0)
    spent_initial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_initial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    workingplan_initial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.CharField(max_length=512, null=True, blank=True)
    comment = models.CharField(max_length=512, null=True, blank=True)
    deliverydate = models.DateField("Delivery Date", null=True, blank=True)
    delivered = models.BooleanField(default=False)
    lineitem = models.OneToOneField(LineItem, on_delete=models.SET_NULL, related_name="fcst", null=True)
    buyer = models.CharField(max_length=175, null=True, blank=True)  # PWGSC buyer
    owner = models.ForeignKey(
        BftUser,
        on_delete=models.RESTRICT,
        default="",
        null=True,
        limit_choices_to={"procurement_officer": True},
    )
    updated = models.DateTimeField(auto_now=True, null=True)
    created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        text = ""
        if self.lineitem:
            text = f"{self.forecastamount} - {self.id} -  {self.lineitem.id}"
        return str(text)

    def save(self, *args, **kwargs):
        if self.forecastamount > self.lineitem.workingplan:
            self.forecastamount = self.lineitem.workingplan
            print("TOO HIGH")
        if self.forecastamount < self.lineitem.spent:
            self.forecastamount = self.lineitem.spent
            print("TOO LOW")
        super(LineForecast, self).save(*args, **kwargs)

    def below_spent(self, request, lineitem: LineItem) -> bool:
        if self.forecastamount < lineitem.spent:
            messages.warning(
                request,
                f"Forecast {self.forecastamount} cannot be smaller than spent {lineitem.spent}",
            )
            return True
        return False

    def above_working_plan(self, request, lineitem: LineItem) -> bool:
        if self.forecastamount > lineitem.workingplan:
            messages.warning(
                request,
                f"Forecast {self.forecastamount} cannot be higher than working plan {lineitem.workingplan}",
            )
            return True
        return False

    def forecast_line_by_line(self, docno: str, forecast: float) -> int:
        lines = LineItem.objects.filter(docno=docno)
        if not lines:
            return 0
        document_working_plan = lines.aggregate(models.Sum("workingplan"))["workingplan__sum"]
        ratio = float(forecast) / float(document_working_plan)
        for li in lines:
            if hasattr(li, "fcst"):
                li_fcst = LineForecastManager().get_line_forecast(li)
                li_fcst.forecastamount = float(li.workingplan) * ratio
                li_fcst.save()
            else:
                li_fcst = LineForecast(lineitem=li, forecastamount=float(li.workingplan) * ratio)
                li_fcst.save()
        return len(lines)

    def forecast_costcenter_lines(self, costcenter: str, forecast: float) -> int:
        lines = LineItem.objects.filter(costcenter=costcenter)
        if not lines:
            return 0
        lines_working_plan = lines.aggregate(models.Sum("workingplan"))["workingplan__sum"]
        ratio = float(forecast) / float(lines_working_plan)
        for li in lines:
            if hasattr(li, "fcst"):
                li_fcst = LineForecastManager().get_line_forecast(li)
                li_fcst.forecastamount = float(li.workingplan) * ratio
                li_fcst.save()
            else:
                li_fcst = LineForecast(lineitem=li, forecastamount=float(li.workingplan) * ratio)
                li_fcst.save()
        return len(lines)


class LineItemImport(models.Model):
    """
    LineItemImport class defines the model that represents the DND cost
    center encumbrance report single line item.  Each line read from the
    encumbrance report during the uploadcsv command must match this model
    """

    docno = models.CharField(max_length=10)
    lineno = models.CharField(max_length=7)  # lineno : acctassno
    # acctassno = models.CharField(max_length=3, null=True, blank=True)
    spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    workingplan = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fundcenter = models.CharField(max_length=6)
    fund = models.CharField(max_length=4)
    costcenter = models.CharField(max_length=6)
    internalorder = models.CharField(max_length=7, null=True, blank=True)
    doctype = models.CharField(max_length=2, null=True, blank=True)
    enctype = models.CharField(max_length=21)
    linetext = models.CharField(max_length=50, null=True, blank=True, default="")
    predecessordocno = models.CharField(max_length=20, null=True, blank=True, default="")
    predecessorlineno = models.CharField(max_length=3, null=True, blank=True, default="")
    reference = models.CharField(max_length=16, null=True, blank=True, default="")
    gl = models.CharField(max_length=5)
    duedate = models.DateField(null=True, blank=True)
    vendor = models.CharField(max_length=50, null=True, blank=True)
    createdby = models.CharField(max_length=50, null=True, blank=True, default="")
