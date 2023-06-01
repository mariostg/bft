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


class LineItemImportTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        filldata = populate.Command()
        filldata.handle()
        runner = Encumbrance("encumbrance_tiny.txt")
        runner.run_all()

    def test_insert_line_item_from_encumbrance_line(self):
        obj = LineItem()
        enc = EncumbranceImport.objects.first()
        retval = obj.insert_line_item(enc)

        self.assertEqual(1, retval)

    def test_update_line_item_from_encumbrance_line(self):
        obj = LineItem()
        enc = EncumbranceImport.objects.first()
        retval = obj.insert_line_item(enc)

        enc.workingplan = enc.workingplan + 10000
        enc.spent = enc.spent + 10000
        enc.balance = enc.balance + 10000
        li = LineItem.objects.get(pk=retval)
        updated = obj.update_line_item(li, enc)

        self.assertEqual(enc.workingplan, updated.workingplan)

    def test_update_line_item_bogus_cost_center(self):
        obj = LineItem()
        enc = EncumbranceImport.objects.first()
        retval = obj.insert_line_item(enc)

        li = LineItem.objects.get(pk=retval)
        enc.costcenter = "QQQQ33"

        updated = obj.update_line_item(li, enc)

        self.assertEqual(None, updated)

    def test_line_items_have_orphans(self):
        # bring lines in
        li = LineItem()
        li.import_lines()

        # alter a line to make it orphan
        li = LineItem.objects.first()
        li.docno = "999999"  # To make it orphan.
        li.lineno = "123"
        li.save()

        # check it out
        orphan = li.get_orphan_lines()
        self.assertIn(("999999", "123"), orphan)
        self.assertIsInstance(orphan, set)

    def test_line_items_no_orphans(self):
        # bring lines in
        li = LineItem()
        li.import_lines()

        # check it out
        orphan = li.get_orphan_lines()
        self.assertEqual(0, len(orphan))
        self.assertIsInstance(orphan, set)

    def test_mark_line_orphan(self):
        # bring lines in
        li = LineItem()
        li.import_lines()

        li = LineItem.objects.first()
        li.docno = "999999"  # To make it orphan.
        li.lineno = "123"
        li.save()

        orphan = li.get_orphan_lines()
        li.mark_orphan_lines(orphan)
        li = LineItem.objects.get(docno="999999", lineno="123")
        self.assertEqual(0, li.workingplan)
        self.assertEqual(0, li.spent)
        self.assertEqual(0, li.balance)
        self.assertEqual("orphan", li.status)


class LineItemManagementTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        filldata = populate.Command()
        filldata.handle()
        runner = Encumbrance("encumbrance_tiny.txt")
        runner.run_all()

    def test_line_item_fund_center_wrong(self):
        # bring lines in and assign a bogus fund center
        li = LineItem()
        li.import_lines()
        li = LineItem.objects.first()
        li.fundcenter = "xxxx11"
        li.save()

        li.set_fund_center_integrity()
        self.assertEqual(1, LineItem.objects.filter(fcintegrity=False).count())
