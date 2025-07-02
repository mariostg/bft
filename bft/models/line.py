
import numpy as np
import pandas as pd
from django.contrib import messages
from django.db import models
from django.db.models import F, QuerySet, Sum
from django.forms.models import model_to_dict

from utils.dataframe import BFTDataFrame

class LineItemManager(models.Manager):
    """A custom manager for LineItem model that provides additional query functionality and data transformation methods.

    This manager extends Django's base manager to provide specialized querying and data manipulation
    for LineItem objects, particularly focused on cost center operations and DataFrame conversions.

    Methods:
        cost_center(costcenter: str) -> QuerySet:
            Retrieves line items for a specific cost center.

        has_line_items(costcenter: CostCenter) -> bool:
            Checks if there are any line items associated with a given cost center.

        line_item_dataframe(fund: str = None, doctype: str = None) -> pd.DataFrame:
            Converts line items to a pandas DataFrame with optional filtering by fund and document type.

        line_item_detailed_dataframe(fund: str = None, doctype: str = None) -> pd.DataFrame:
            Creates a detailed DataFrame merging line items with forecast data and cost center information.
    """

    def cost_center(self, costcenter: str):
        """
        Filter queryset by cost center code.

        Args:
            costcenter (str): The cost center code to filter by. Case insensitive.

        Returns:
            QuerySet: Filtered queryset containing only records matching the cost center.
            None: If the cost center does not exist.
        """
        costcenter = costcenter.upper()
        try:
            cc = CostCenter.objects.get(costcenter=costcenter)
        except CostCenter.DoesNotExist:
            return None
        return self.filter(costcenter=cc)

    def has_line_items(self, costcenter: "CostCenter") -> bool:
        """
        Checks if any line items exist for a given cost center.

        Args:
            costcenter (CostCenter): The cost center to check for line items.

        Returns:
            bool: True if line items exist for the cost center, False otherwise.
        """
        return LineItem.objects.filter(costcenter=costcenter).exists()

    def line_item_dataframe(self, fund: str = None, doctype: str = None) -> pd.DataFrame:
        """Retrieves line items from database and converts them to a pandas DataFrame.

        This method filters line items by fund and document type if provided, then
        creates a DataFrame with separate columns for different document type balances.

        Args:
            fund (str, optional): Fund code to filter by. Will be converted to uppercase.
            doctype (str, optional): Document type to filter by. Will be converted to uppercase.

        Returns:
            pd.DataFrame: DataFrame containing line items with the following columns:
                - Original line item fields
                - CO: Balance amount if doctype is CO, else 0
                - PC: Balance amount if doctype is PC, else 0
                - FR: Balance amount if doctype is FR, else 0
                Returns empty DataFrame if no data found.
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
        Returns a detailed DataFrame containing line item information merged with forecast and cost center data.

        This method enhances the basic line item DataFrame by joining it with forecast and cost center
        information. It performs the following operations:
        1. Retrieves the base line item DataFrame
        2. Merges forecast data if available (defaults to 0 if no forecasts exist)
        3. Merges cost center information

        Parameters
        ----------
        fund : str, optional
            Filter results by fund identifier
        doctype : str, optional
            Filter results by document type

        Returns
        -------
        pd.DataFrame
            A DataFrame containing line item details with additional forecast and cost center information.
            Returns empty DataFrame if no line items match the filter criteria.

        Notes
        -----
        - Forecast values are converted to integer type
        - Left joins are used to preserve all line items even if no matching forecast/cost center exists
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
    """A Django model class representing a line item in a financial system.

    This model stores detailed information about financial transactions, including document numbers,
    line numbers, amounts, and various financial codes and references.

    Attributes:
        docno (CharField): Document number, max 10 characters
        lineno (CharField): Line number/account assignment number, max 7 characters
        spent (DecimalField): Amount spent, max 10 digits with 2 decimal places
        balance (DecimalField): Current balance, max 10 digits with 2 decimal places
        workingplan (DecimalField): Working plan amount, max 10 digits with 2 decimal places
        fundcenter (CharField): Fund center code, max 6 characters
        fund (CharField): Fund code, max 4 characters
        costcenter (ForeignKey): Reference to CostCenter model
        internalorder (CharField): Internal order number, max 7 characters, optional
        doctype (CharField): Document type code, max 2 characters, optional
        enctype (CharField): Encumbrance type, max 21 characters
        linetext (CharField): Line item description, max 50 characters, optional
        predecessordocno (CharField): Previous document number reference, max 20 characters, optional
        predecessorlineno (CharField): Previous line number reference, max 3 characters, optional
        reference (CharField): Reference number, max 16 characters, optional
        gl (CharField): General ledger code, max 5 characters
        duedate (DateField): Due date for the line item, optional
        vendor (CharField): Vendor name/information, max 50 characters, optional
        createdby (CharField): Creator's identifier, max 50 characters, optional
        status (CharField): Current status of the line item, max 10 characters, optional
        fcintegrity (BooleanField): Fund center integrity check flag

    Methods:
        get_orphan_lines(costcenter): Returns lines that exist in line items but not in encumbrances
        mark_orphan_lines(orphans): Marks specified lines as orphaned and zeros their amounts
        insert_line_item(ei): Creates a new line item from an import record
        update_line_item(li, ei): Updates an existing line item with import data
        import_lines(): Imports and updates lines from the encumbrance import table
        set_fund_center_integrity(): Validates and sets fund center integrity flags
        set_doctype(): Sets document types based on encumbrance types
        __str__(): Returns string representation of the line item

    Meta:
        ordering: Ordered by document number (descending) and line number
        verbose_name_plural: "Line Items"
    """

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
    predecessordocno = models.CharField(
        max_length=20, null=True, blank=True, default=""
    )
    predecessorlineno = models.CharField(
        max_length=3, null=True, blank=True, default=""
    )
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
        """Return orphaned line items.

        This method identifies line items that exist in LineItem but not in LineItemImport.
        An orphan line is one where the combination of document number and line number exists
        in LineItem but does not have a corresponding entry in LineItemImport.

        Args:
            costcenter (Union[str, CostCenter], optional): Cost center to filter lines by.
                Can be either a string cost center code or CostCenter object.
                If None, checks all cost centers. Defaults to None.

        Returns:
            Set[Tuple[str, str]] | None: Set of tuples containing (docno, lineno) for orphaned lines.
                Returns None if specified cost center string doesn't exist.
                Returns empty set if no orphans found.

        Example:
            >>> model.get_orphan_lines('CC001')  # Get orphans for specific cost center
            {('DOC1', '1'), ('DOC2', '3')}
            >>> model.get_orphan_lines()  # Get orphans across all cost centers
            {('DOC1', '1'), ('DOC2', '3'), ('DOC3', '2')}
        """

        if costcenter:
            if isinstance(costcenter, str):
                try:
                    costcenter = CostCenter.objects.get(costcenter=costcenter.upper())
                except CostCenter.DoesNotExist:
                    return None
            lines = set(
                LineItem.objects.filter(costcenter=costcenter).values_list(
                    "docno", "lineno"
                )
            )
        else:
            lines = set(LineItem.objects.values_list("docno", "lineno"))

        enc = set(LineItemImport.objects.values_list("docno", "lineno"))
        orphans = lines.difference(enc)

        if costcenter:
            logger.info(
                f"Found {len(orphans)} orphan lines for cost center {costcenter}."
            )
        else:
            logger.info(
                f"Found {len(orphans)} orphan lines considering all cost centers."
            )

        return orphans

    def mark_orphan_lines(self, orphans: set):

        def mark_orphan_lines(self, orphans: set) -> None:
            """
            Marks specified lines as orphan and updates their financial values to zero.

            This method processes a set of docno/lineno tuples, setting their status to 'orphan'
            and zeroing out their financial fields (spent, workingplan, balance).
            It also updates any associated line forecasts to zero.

            Args:
                orphans (set): A set of tuples containing (docno, lineno) pairs to be marked as orphans

            Returns:
                None

            Example:
                >>> mark_orphan_lines({('DOC123', 1), ('DOC124', 2)})
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
        Insert a new line item into the database based on a LineItemImport object.

        Args:
            ei (LineItemImport): The line item import object containing data to be inserted.

        Returns:
            int: The ID of the newly created line item.

        Raises:
            CostCenter.DoesNotExist: If the cost center specified in ei.costcenter does not exist.

        Note:
            The method performs the following operations:
            1. Retrieves the CostCenter object based on the import data
            2. Converts the import object to a dictionary
            3. Creates a new LineItem with 'New' status
            4. Saves the line item to the database
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
        Updates a line item with data from a line item import.

        Args:
            li (LineItem): The line item to update.
            ei (LineItemImport): The line item import containing new data.

        Returns:
            LineItem: The updated line item if the cost center exists.
            None: If the cost center does not exist.

        Updates the following fields if cost center exists:
            - costcenter
            - fundcenter
            - spent
            - workingplan
            - balance
            - fund
            - status (set to "Updated")
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
        Import and update line items from LineItemImport table to LineItem table.

        First marks all existing LineItem records as "old" status. Then processes each LineItemImport record:
        - Skips lines with cost centers marked as not updatable
        - Updates existing LineItem records that match on docno and lineno
        - Creates new LineItem records for lines that don't exist

        Updates are logged using the logger.

        Returns:
            None

        Side Effects:
            - Updates status field of all existing LineItem records to "old"
            - Creates or updates LineItem records based on LineItemImport data
            - Logs import progress and counts
        """

        count = LineItem.objects.all().update(status="old")
        logger.info(f"Set {count} lines to old.")

        cc_no_update = CostCenter.objects.filter(isupdatable=False).values_list("costcenter", flat=True)
        encumbrance = LineItemImport.objects.all()
        logger.info(f"Retreived {encumbrance.count()} encumbrance lines.")
        for e in encumbrance:
            if e.costcenter in cc_no_update:
                continue
            try:
                target = LineItem.objects.get(docno=e.docno, lineno=e.lineno)
                self.update_line_item(target, e)
            except LineItem.DoesNotExist:
                self.insert_line_item(e)

    def set_fund_center_integrity(self):
        """
        Validates and updates fund center integrity for line items based on cost center relationships.

        This method performs the following operations:
        1. Creates a set of valid (cost center, fund center) pairs from CostCenter objects
        2. Resets fund center integrity flag to False for all LineItem objects
        3. Updates fund center integrity flag to True for LineItems where cost center and fund center match valid pairs

        The fund center integrity is considered valid when a line item's cost center and fund center combination
        exists in the established cost center hierarchy relationships.

        Returns
            None

        Side Effects:
            - Updates fcintegrity field in LineItem table
            - Logs process start and completion via logger
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
        """Sets document type for line items based on encoding type.

        This method maps specific encoding types to their corresponding document types
        and updates the LineItem records in the database accordingly.

        The mapping is as follows:
            - Funds Commitment -> CO
            - Funds Precommitment -> PC
            - Funds Reservation -> FR
            - Purchase Order -> CO
            - Purchase Requisitions -> PC

        Returns:
            None
        """
        logger.info("Set doctype begins")
        types = [
            {"enctype": "Funds Commitment", "doctype": "CO"},
            {"enctype": "Funds Precommitment", "doctype": "PC"},
            {"enctype": "Funds Reservation", "doctype": "FR"},
            {"enctype": "Purchase Order", "doctype": "CO"},
            {"enctype": "Purchase Requisitions", "doctype": "PC"},
        ]
        for t in types:
            li = LineItem.objects.filter(enctype=t["enctype"]).update(
                doctype=t["doctype"]
            )
            logger.info(f"Set {li} lines to {t['doctype']}")
        logger.info("Set doctype complete")


class LineForecastManager(models.Manager):
    """LineForecastManager handles database operations for LineForecast model.

    This manager provides methods to retrieve, update and manipulate LineForecast objects,
    including forecast calculations and history tracking.

    Methods:
        get_line_forecast(lineitem): Returns LineForecast object for given LineItem if exists
        forecast_dataframe(): Returns pandas DataFrame containing all LineForecast data
        update_owner(costcenter, new_owner, old_owner): Updates forecast owner for given cost center
        set_underforecasted(costcenter): Adjusts forecasts that are lower than actual spent
        set_overforecasted(costcenter): Adjusts forecasts that exceed working plan
        set_encumbrance_history_record(costcenter): Creates initial forecast records for new line items

    Inherits from:
        django.db.models.Manager
    """

    def get_line_forecast(self, lineitem: LineItem) -> "LineForecast | None":
        """
        Retrieves the line forecast associated with a given line item.

        Args:
            lineitem (LineItem): The line item object to get the forecast for.

        Returns:
            LineForecast | None: The associated LineForecast object if it exists,
                                None if the line item has no forecast.
        """
        if hasattr(lineitem, "fcst"):
            return LineForecast.objects.get(lineitem_id=lineitem.id)
        else:
            return None

    def forecast_dataframe(self) -> pd.DataFrame:
        """
        Returns a pandas DataFrame containing line forecast data.

        The method retrieves all LineForecast objects from the database and converts them
        to a DataFrame format. If no LineForecast objects exist, returns an empty DataFrame.

        Returns:
            pd.DataFrame: DataFrame containing line forecast data, or empty DataFrame if no data exists

        Example:
            >>> model.forecast_dataframe()
            # Returns DataFrame with LineForecast data
        """
        if not LineForecast.objects.exists():
            return pd.DataFrame()
        data = LineForecast.objects.all()
        df = BFTDataFrame(LineForecast).build(data)
        return df

    def update_owner(self, costcenter: CostCenter, new_owner: BftUser, old_owner: BftUser = None) -> int:
        """Updates the owner of all line forecasts associated with a specific cost center.

        This method finds all LineForecast objects linked to the given cost center and updates
        their owner to the new specified user.

        Args:
            costcenter (CostCenter): The cost center to update line forecast owners for
            new_owner (BftUser): The new user to set as owner
            old_owner (BftUser, optional): The previous owner (not currently used). Defaults to None.

        Returns:
            int: The number of line forecasts that were updated
        """

        lines = LineForecast.objects.filter(lineitem__costcenter=costcenter)
        if lines:
            return lines.update(owner=new_owner)

    def set_underforecasted(self, costcenter: CostCenter = None) -> int:
        """Updates forecast amounts for lines where actual spent exceeds forecast amount.

        This method finds all line items where the actual spent amount is greater than
        the forecasted amount and updates the forecast to match the spent amount.

        Args:
            costcenter (CostCenter, optional): If provided, only updates lines for the specified
                cost center. If None, updates lines across all cost centers. Defaults to None.

        Returns:
            int: Number of line items that were successfully updated.

        Example:
            >>> budget.set_underforecasted()  # Updates all underforecasted lines
            >>> budget.set_underforecasted(cost_center_obj)  # Updates only specified cost center
        """
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
        """Sets forecast amount equal to working plan for overforecasted lines.

        This method identifies line forecasts where the working plan is less than the forecast
        amount (overforecasted) and adjusts the forecast amount to match the working plan.

        Args:
            costcenter (Union[CostCenter, str], optional): Cost center to filter lines by.
                If None, all overforecasted lines are processed. Defaults to None.

        Returns:
            int: Number of line forecasts that were successfully updated.

        Example:
            >>> model.set_overforecasted()  # Update all overforecasted lines
            >>> model.set_overforecasted("CC001")  # Update only lines for cost center CC001

        Note:
            Uses bulk_update for efficient database operations.
        """
        lines = LineForecast.objects.filter(
            lineitem__workingplan__lt=F("forecastamount")
        )
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
        """Sets encumbrance history record for line items with 'New' status.

        This method creates LineForecast records for eligible line items that are in 'New' status.
        Only line items with forecastable cost centers are processed.

        Args:
            costcenter (CostCenter, optional): If provided, only process line items for this cost center.
                Defaults to None which processes all eligible line items.

        Returns:
            int: Number of line items for which encumbrance history was successfully set.

        Note:
            - Only processes line items where costcenter.isforecastable is True
            - Logs information about number of records processed
            - Creates LineForecast entries with initial spent, workingplan and balance values
        """
        lines = LineItem.objects.filter(status="New")
        if costcenter:
            lines = lines.filter(costcenter=costcenter)
        maxlines = lines.count()
        logger.info(f"{maxlines} new lines need encumbrance record history to be set.")
        counter = 0
        li: LineItem
        for li in lines:
            if not li.costcenter.isforecastable:
                continue
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
            logger.warning(f"Encumbrance history set for {counter} out of {maxlines}")
        return counter


class LineForecast(models.Model):
    """
    A Django model representing forecasting data for line items in a financial system.

    This class manages forecast amounts, tracking of delivery status, and ownership information
    for individual line items. It includes methods for forecast validation and calculation.

    Attributes:
        forecastamount (DecimalField): The forecasted amount for the line item
        spent_initial (DecimalField): Initial spent amount
        balance_initial (DecimalField): Initial balance amount
        workingplan_initial (DecimalField): Initial working plan amount
        description (CharField): Optional description text
        comment (CharField): Optional comment text
        deliverydate (DateField): Expected delivery date
        delivered (BooleanField): Indicates if item has been delivered
        lineitem (OneToOneField): Reference to associated LineItem
        buyer (CharField): PWGSC buyer identifier
        owner (ForeignKey): Reference to BftUser who owns this forecast
        updated (DateTimeField): Last update timestamp
        created (DateTimeField): Creation timestamp

    Methods:
        save(): Validates and saves forecast amounts within allowed bounds
        forecastable(): Checks if the line item can be forecasted
        below_spent(request, lineitem): Validates forecast is not below spent amount
        above_working_plan(request, lineitem): Validates forecast is not above working plan
        forecast_lines(lines, ratio): Forecasts multiple lines using given ratio
        forecast_line_by_docno(docno, forecast): Forecasts lines for a document number
        forecast_costcenter_lines(costcenter, forecast): Forecasts lines for a cost center
    """
    forecastamount = models.DecimalField(
        "Forecast", max_digits=10, decimal_places=2, default=0
    )
    spent_initial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_initial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    workingplan_initial = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    description = models.CharField(max_length=512, null=True, blank=True)
    comment = models.CharField(max_length=512, null=True, blank=True)
    deliverydate = models.DateField("Delivery Date", null=True, blank=True)
    delivered = models.BooleanField(default=False)
    lineitem = models.OneToOneField(
        LineItem, on_delete=models.SET_NULL, related_name="fcst", null=True
    )
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
        """
        Save method for LineForecast model.

        This method ensures forecast amounts are properly constrained before saving:
        - If not forecastable, uses the lineitem's current forecast amount
        - Cannot exceed the working plan amount
        - Cannot be less than the spent amount

        Overrides the default model save method.

        Args:
            *args: Variable length argument list to pass to parent save
            **kwargs: Arbitrary keyword arguments to pass to parent save

        Returns:
            None
        """
        if not self.forecastable():
            self.forecastamount = self.lineitem.fcst.forecastamount
        if self.forecastamount > self.lineitem.workingplan:
            self.forecastamount = self.lineitem.workingplan
        if self.forecastamount < self.lineitem.spent:
            self.forecastamount = self.lineitem.spent
        super(LineForecast, self).save(*args, **kwargs)

    def forecastable(self) -> bool:
        """
        Property that indicates whether a line item is forecastable.

        Returns:
            bool: True if the associated cost center is forecastable, False otherwise.
        """
        return self.lineitem.costcenter.isforecastable

    def below_spent(self, request, lineitem: LineItem) -> bool:
        """
        Check if the forecast amount is below the spent amount.

        This method compares the forecast amount against the spent amount of a line item
        and shows a warning message if the forecast is smaller than what was spent.

        Args:
            request: The HTTP request object used for displaying messages
            lineitem (LineItem): The line item object containing the spent amount

        Returns:
            bool: True if forecast amount is below spent amount, False otherwise
        """
        if self.forecastamount < lineitem.spent:
            messages.warning(
                request,
                f"Forecast {self.forecastamount} cannot be smaller than spent {lineitem.spent}",
            )
            return True
        return False

    def above_working_plan(self, request, lineitem: LineItem) -> bool:
        """
        Check if forecast amount exceeds working plan and display warning message.

        Args:
            request: The HTTP request object
            lineitem (LineItem): The line item object containing working plan amount

        Returns:
            bool: True if forecast amount is above working plan, False otherwise
        """
        if self.forecastamount > lineitem.workingplan:
            messages.warning(
                request,
                f"Forecast {self.forecastamount} cannot be higher than working plan {lineitem.workingplan}",
            )
            return True
        return False

    def forecast_lines(self, lines: QuerySet[LineItem], ratio):
        """
        Updates or creates forecast lines for a given set of line items based on a ratio.

        Args:
            lines (QuerySet[LineItem]): A queryset of LineItem objects to forecast.
            ratio (float): The multiplier to apply to the working plan amount.

        The method performs the following:
        - For existing line forecasts: updates the forecast amount
        - For new line items: creates a new line forecast
        - Forecast amount is calculated as workingplan * ratio

        Note:
            LineForecast objects are saved to the database in both cases.
        """
        for li in lines:
            if hasattr(li, "fcst"):
                li_fcst = LineForecastManager().get_line_forecast(li)
                li_fcst.forecastamount = float(li.workingplan) * ratio
                li_fcst.save()
            else:
                li_fcst = LineForecast(lineitem=li, forecastamount=float(li.workingplan) * ratio)
                li_fcst.save()

    def forecast_line_by_docno(self, docno: str, forecast: float) -> int:
        """
        Forecasts line items for a given document number by distributing the forecast amount proportionally.

        This method splits the forecast between lines with spent amounts and those without,
        maintaining the proportional distribution of the working plan while accounting for
        already spent amounts.

        Args:
            docno (str): The document number to identify relevant line items
            forecast (float): The total forecast amount to be distributed

        Returns:
            int: The total number of line items processed

        Note:
            - Lines with spent amounts are forecasted first
            - Remaining forecast amount is distributed among lines with no spent amounts
            - If there are no lines for the given docno, returns 0
        """
        lines = LineItem.objects.filter(docno=docno)
        if not lines:
            return 0

        lines_with_spent = lines.filter(spent__gt=0)
        lines_no_spent = lines.filter(spent=0)

        full_working_plan = lines.aggregate(models.Sum("workingplan"))["workingplan__sum"]
        unspent_working_plan = lines_no_spent.aggregate(models.Sum("workingplan"))["workingplan__sum"]

        spent_ratio = float(forecast) / float(full_working_plan)
        spent_forecast = 0
        if lines_with_spent:
            self.forecast_lines(lines_with_spent, spent_ratio)
            spent_forecast = LineItem.objects.filter(docno=docno, spent__gt=0).aggregate(Sum("fcst__forecastamount"))[
                "fcst__forecastamount__sum"
            ]

        if unspent_working_plan:
            unspent_ratio = (float(forecast) - float(spent_forecast)) / float(unspent_working_plan)
            self.forecast_lines(lines_no_spent, unspent_ratio)
        return len(lines)

    def forecast_costcenter_lines(self, costcenter: str, forecast: float) -> int:
        """
        Forecast the cost center lines based on the given cost center and forecast amount.

        This method calculates and updates forecast amounts for all line items under a cost center,
        handling both lines with spent amounts and unspent lines differently.

        Args:
            costcenter (str): The cost center identifier to forecast
            forecast (float): The total forecast amount to be distributed

        Returns:
            int: The number of line items processed for the cost center.
                Returns 0 if the cost center doesn't exist or has no lines.

        The method:
        1. Separates lines into those with spent amounts and those without
        2. Calculates ratios based on working plan amounts
        3. Distributes forecast amount proportionally:
           - First to lines with existing spent amounts
           - Then remaining forecast to unspent lines
        """
        costcenter = CostCenterManager().cost_center(costcenter)
        if not costcenter:
            return 0
        lines = LineItem.objects.filter(costcenter=costcenter)
        if not lines:
            return 0

        lines_with_spent = lines.filter(spent__gt=0)
        lines_no_spent = lines.filter(spent=0)

        full_working_plan = lines.aggregate(models.Sum("workingplan"))["workingplan__sum"]
        unspent_working_plan = lines_no_spent.aggregate(models.Sum("workingplan"))["workingplan__sum"]

        spent_ratio = float(forecast) / float(full_working_plan)
        spent_forecast = 0

        if lines_with_spent:
            self.forecast_lines(lines_with_spent, spent_ratio)
            spent_forecast = LineItem.objects.filter(costcenter=costcenter, spent__gt=0).aggregate(
                Sum("fcst__forecastamount")
            )["fcst__forecastamount__sum"]

        if unspent_working_plan:
            unspent_ratio = (float(forecast) - float(spent_forecast)) / float(unspent_working_plan)
            self.forecast_lines(lines_no_spent, unspent_ratio)

        return len(lines)


class LineItemImport(models.Model):
    """
    A Django model representing a line item import in a financial system.

    This model stores detailed information about financial transactions including
    document numbers, spending, balances, accounting codes, and related metadata.

    Attributes:
        docno (str): Document number, max length 10 characters
        lineno (str): Line number/account assignment number, max length 7 characters
        spent (Decimal): Amount spent, with 2 decimal places
        balance (Decimal): Current balance, with 2 decimal places
        workingplan (Decimal): Working plan amount, with 2 decimal places
        fundcenter (str): Fund center code, max length 6 characters
        fund (str): Fund code, max length 4 characters
        costcenter (str): Cost center code, max length 6 characters
        internalorder (str): Internal order number, max length 7 characters, optional
        doctype (str): Document type code, max length 2 characters, optional
        enctype (str): Encumbrance type, max length 21 characters
        linetext (str): Line item description, max length 50 characters, optional
        predecessordocno (str): Previous document number, max length 20 characters, optional
        predecessorlineno (str): Previous line number, max length 3 characters, optional
        reference (str): Reference number, max length 16 characters, optional
        gl (str): General ledger code, max length 5 characters
        duedate (Date): Due date of the transaction, optional
        vendor (str): Vendor name, max length 50 characters, optional
        createdby (str): Creator's identifier, max length 50 characters, optional
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
    predecessordocno = models.CharField(
        max_length=20, null=True, blank=True, default=""
    )
    predecessorlineno = models.CharField(
        max_length=3, null=True, blank=True, default=""
    )
    reference = models.CharField(max_length=16, null=True, blank=True, default="")
    gl = models.CharField(max_length=5)
    duedate = models.DateField(null=True, blank=True)
    vendor = models.CharField(max_length=50, null=True, blank=True)
    createdby = models.CharField(max_length=50, null=True, blank=True, default="")

