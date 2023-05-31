from django.db import models

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

    def __str__(self):
        text = f"{self.enctype} {self.docno}-{self.lineno}"
        return str(text)

    class Meta:
        ordering = ["-docno", "lineno"]
        verbose_name_plural = "Line Items"

    def get_orphan_lines(self):
        lines = set(LineItem.objects.values_list("docno", "lineno"))
        enc = set(EncumbranceImport.objects.values_list("docno", "lineno"))
        return lines.difference(enc)

    def insert_line_item(self, ei: EncumbranceImport):
        cc = CostCenter.objects.get(costcenter=ei.costcenter)
        di = model_to_dict(ei)
        di["costcenter"] = cc
        del di["id"]
        target = LineItem(**di)
        target.status = "New"
        target.save()
        return target.id

    def update_line_item(self, li: "LineItem", ei: EncumbranceImport):
        li.spent = ei.spent
        li.workingplan = ei.workingplan
        li.balance = ei.balance
        li.status = "Updated"
        # TODO More to come
        li.save()
        return li

    def import_lines(self):
        """
        import_line function relies on content of encumbrance_import.  It is
        responsible to import new lines, update current ones and zero out lines
        no longer in DRMIS
        """
        encumbrance = EncumbranceImport.objects.all()

        for e in encumbrance:
            try:
                target = LineItem.objects.get(docno=e.docno, lineno=e.lineno)
                self.update_line_item(target, e)
            except LineItem.DoesNotExist:
                self.insert_line_item(e)
