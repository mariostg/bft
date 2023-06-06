from django.db import models
from django.contrib import messages
from costcenter.models import CostCenter
from encumbrance.models import EncumbranceImport
from django.forms.models import model_to_dict


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

    def __str__(self):
        text = f"{self.enctype} {self.docno}-{self.lineno}"
        return str(text)

    class Meta:
        ordering = ["-docno", "lineno"]
        verbose_name_plural = "Line Items"

    def get_orphan_lines(self):
        """
        Compare the docno and lineno combination in both line item table and
        encumbrance table.
        """
        lines = set(LineItem.objects.values_list("docno", "lineno"))
        enc = set(EncumbranceImport.objects.values_list("docno", "lineno"))
        orphans = lines.difference(enc)
        self.import_progress("info", f"Found {len(orphans)} orphan lines.")
        return orphans

    def mark_orphan_lines(self, orphans: set):
        """
        Set the status of the line item to orphan.
        """
        self.import_progress("info", "Begin marking orphan lines")
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
                self.import_progress("error", f"LineItem {docno} - {lineno} does not exist")
        # TODO need to set forecast too.

    def insert_line_item(self, ei: EncumbranceImport):
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

    def update_line_item(self, li: "LineItem", ei: EncumbranceImport):
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
            li.status = "Updated"
            # TODO More to come
            li.save()
            return li
        else:
            return None

    def import_progress(self, status_type, msg):
        """
        Keeps a record of messages issued during import lines process.
        """
        if status_type not in ("info", "success", "warning", "error"):
            status_type = "unknown"
        if not self.status:
            self.status = []

        self.status.append((status_type, msg))

    def display_import_progress(self):
        if not self.status:
            print("Nothing in download progress report.")
        else:
            for item in self.status:
                print(f"[{item[0]}]: {item[1]}")

    def import_lines(self):
        """
        import_line function relies on content of encumbrance_import.  It is
        responsible to import new lines, update current ones and zero out lines
        no longer in DRMIS
        """

        count = LineItem.objects.all().update(status="old")
        self.import_progress("info", f"Set {count} lines to old.")

        orphan = self.get_orphan_lines()
        self.mark_orphan_lines(orphan)

        encumbrance = EncumbranceImport.objects.all()
        self.import_progress("info", f"Retreived {encumbrance.count()} encumbrance lines.")
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
        self.import_progress("info", "Fund center integrity check begins.")
        cc = CostCenter.objects.select_related()
        cc_set = set()
        for c in cc:
            cc_set.add((c.costcenter, c.parent.fundcenter))

        li = LineItem.objects.select_related()
        li.update(fcintegrity=False)

        for item in li:
            t = (item.costcenter.costcenter, item.fundcenter)
            if t in cc_set:
                item.fcintegrity = True
                item.save()
        self.import_progress("info", "Fund center integrity check completed.")


class LineForecast(models.Model):
    forecastamount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.CharField(max_length=512, null=True, blank=True)
    comment = models.CharField(max_length=512, null=True, blank=True)
    deliverydate = models.DateField(null=True, blank=True)
    delivered = models.BooleanField(default=False)
    lineitem = models.OneToOneField(LineItem, on_delete=models.SET_NULL, related_name="fcst", null=True)
    buyer = models.CharField(max_length=175, null=True, blank=True)  # PWGSC buyer
    # TODO procurement_officer
    updated = models.DateTimeField(auto_now=True, null=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    status = models.CharField(max_length=10, default="", blank=True, null=True)

    def __str__(self):
        text = f"{self.forecastamount} - {self.id} -  {self.lineitem.id}"
        return str(text)

    def validate(self, request, lineitem: LineItem) -> True:
        print(f"working plan {lineitem.workingplan}, forecast {self.forecastamount}")
        if lineitem.workingplan < self.forecastamount:
            messages.warning(
                request,
                f"Forecast {self.forecastamount} cannot be higher than working plan {lineitem.workingplan}",
            )
            return False
        if lineitem.spent > self.forecastamount:
            messages.warning(
                request,
                f"Forecast {self.forecastamount} cannot be smaller than spent {lineitem.spent}",
            )
            return False

    def save(self, *args, **kwargs):
        # do_something before()
        super.save(*args, **kwargs)
        # do_something_after()
