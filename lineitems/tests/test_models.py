from django.test import TestCase

from lineitems.models import LineItem
from encumbrance.models import EncumbranceImport, Encumbrance
from encumbrance.management.commands import populate


class LineItemModelTest(TestCase):
    def test_string_representation(self):
        str_repr = LineItem(docno="4510XX45", lineno="45", enctype="Purchase Order")
        self.assertEqual(str(str_repr), "Purchase Order 4510XX45-45")

    def test_verbose_name_plural(self):
        self.assertEqual(str(LineItem._meta.verbose_name_plural), "Line Items")

    def test_number_of_fields(self):
        obj = LineItem()
        c = obj._meta.get_fields()
        self.assertEqual(21, len(c))

    def test_insert_line_item_from_encumbrance_line(self):
        filldata = populate.Command()
        filldata.handle()
        runner = Encumbrance("encumbrance_tiny.txt")
        runner.run_all()

        obj = LineItem()
        enc = EncumbranceImport.objects.first()
        retval = obj.insert_line_item(enc)

        self.assertEqual(1, retval)

    def test_update_line_item_from_encumbrance_line(self):
        filldata = populate.Command()
        filldata.handle()
        runner = Encumbrance("encumbrance_tiny.txt")
        runner.run_all()

        obj = LineItem()
        enc = EncumbranceImport.objects.first()
        retval = obj.insert_line_item(enc)

        enc.workingplan = enc.workingplan + 10000
        enc.spent = enc.spent + 10000
        enc.balance = enc.balance + 10000
        li = LineItem.objects.get(pk=retval)
        updated = obj.update_line_item(li, enc)

        self.assertEqual(enc.workingplan, updated.workingplan)
