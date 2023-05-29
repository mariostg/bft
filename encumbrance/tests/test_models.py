from django.test import TestCase

import unittest
from encumbrance.models import Encumbrance, EncumbranceImport

import os
from main.settings import BASE_DIR


class TestEncumbrance(TestCase):
    GOODFILE = "encumbrance_small.txt"
    WRONGFC = "encumbrance_wrong_fc.txt"
    WRONGFY = "encumbrance_wrong_fy.txt"
    WRONGLAYOUT = "encumbrance_wrong_layout.txt"

    @classmethod
    def setUpTestData(cls):
        cls.path = os.path.join(BASE_DIR, "drmis_data")

    def test_drmis_data_folder_exists(self):
        self.assertTrue(os.path.exists(self.path), "Drmis data directory not found")

    def test_exception_raised_if_no_file_provided(self):
        with self.assertRaises(ValueError):
            Encumbrance()

    def test_exception_raised_if_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            Encumbrance("Fakefile")

    def test_find_fund_center_line_good(self):
        er = Encumbrance(self.GOODFILE)
        fc = er.find_fund_center("|Funds Center        |2184AA |")
        self.assertEqual(fc, "2184AA")

    def test_find_fundcenter_line_bad(self):
        er = Encumbrance(self.WRONGFC)
        fc = er.find_fund_center("Funds Center        |2184AA |")
        self.assertNotEqual(fc, "2184AA")

    def test_find_fy_line_good(self):
        er = Encumbrance(self.GOODFILE)
        fy = er.find_base_fy("|Base Fiscal Year    |2023   |")
        self.assertEqual(fy, "2023")

    def test_find_fy_line_bad(self):
        er = Encumbrance(self.WRONGFY)
        fy = er.find_base_fy("Base Fiscal Year    |2023   |")
        self.assertNotEqual(fy, "2023")

    def test_find_layout_line_good(self):
        er = Encumbrance(self.GOODFILE)
        fy = er.find_layout("|Layout              |/BFT_NP|")
        self.assertEqual(fy, "/BFT_NP")

    def test_find_layout_line_bad(self):
        er = Encumbrance(self.WRONGLAYOUT)
        fy = er.find_layout("Layout              |/BFT_NP|")
        self.assertNotEqual(fy, "/BFT_NP")

    def test_is_dnd_cost_center_report(self):
        er = Encumbrance("encumbrance_P1a.txt")
        ok = er.is_dnd_cost_center_report()
        self.assertTrue(ok)

    def test_is_not_dnd_cost_center_report(self):
        fname = os.path.join(self.path, "encumbrance_errors_in_file.txt")
        er = Encumbrance(fname)
        ok = er.is_dnd_cost_center_report()
        self.assertFalse(ok)

    def test_clean_header(self):
        header = "|Document N|Line Numbe|AcctAssNo.| Cur Year s|    Cur YR Bal|    Total Cur.|Funds Cent|Fund|Cost Cente|Order       |Document T|Encumbrance Type     |Line Text                                         |Prd.doc.no|Pred doc.i|Reference       |G/L Accoun|Due date  |Vendor nam                         |Created by  |"
        header = header.split("|")
        er = Encumbrance(self.GOODFILE)
        er.clean_header(header)
        self.assertEqual(len(er.data["header"]), er.COLUMNS - 2)

    def test_find_header_line_returns_zero_on_failure(self):
        er = Encumbrance("encumbrance_no_line_header.txt")
        lineno = er.find_header_line()
        self.assertEqual(lineno, 0)

    def test_find_header_line_returns_non_zero_on_success(self):
        er = Encumbrance(self.GOODFILE)
        lineno = er.find_header_line()
        self.assertGreater(lineno, 0)

    def test_is_data_line(self):
        er = Encumbrance(self.GOODFILE)
        lines = [
            {"line": "|14518705  |       240|", "result": True},
            {"line": "|1451870511|       240|", "result": True},
            {"line": "|1451-8705 |       240|", "result": False},
            {"line": "|Docum     |       240|", "result": False},
            {"line": "Funds Center          ", "result": False},
        ]
        for line in lines:
            self.assertEqual(er.is_data_line(line["line"]), line["result"])

    def test_line_to_csv_returns_list_or_none(self):
        er = Encumbrance(self.GOODFILE)
        result_ok = er.line_to_csv(
            "|col1|col2|col3|col4|col5|col6|col7|col8|col9|col10|col11|col12|col13|col14|col15|col16|col17|col18|col19|col20|"
        )
        result_bad = er.line_to_csv(
            "|col1|col2|col3|col4|col5|col6|col7|col8|col9|col10|col11|col12|col13|col14|col15|col16|col17|col18|col19|"
        )

        self.assertEqual(20, len(result_ok), "List does not contain 20 elements")
        self.assertTrue(type(result_ok) is list, "Argument does not return a list")

        self.assertIsNone(result_bad, "Must returns none when list is not good")

    def test_run_all_stops_on_bad_cost_center_report(self):
        er = Encumbrance(self.GOODFILE)
        self.assertFalse(er.run_all())


if __name__ == "__main__":
    unittest.main()
