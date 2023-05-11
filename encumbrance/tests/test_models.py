from django.test import TestCase

import unittest
from encumbrance.models import Encumbrance, EncumbranceImport

import os
from main.settings import BASE_DIR


class TestEncumbrance(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.path = os.path.join(BASE_DIR, "drmis_data")

    def test_drmis_data_folder_exists(self):
        self.assertTrue(os.path.exists(self.path), "Drmis data directory not found")

    def test_find_fund_center_line_good(self):
        er = Encumbrance()
        fc = er.find_fund("|Funds Center        |2184AA |")
        self.assertEqual(fc, "2184AA")

    def test_find_fundcenter_line_bad(self):
        er = Encumbrance()
        fc = er.find_fund("Funds Center        |2184AA |")
        self.assertNotEqual(fc, "2184AA")

    def test_find_fy_line_good(self):
        er = Encumbrance()
        fy = er.find_base_fy("|Base Fiscal Year    |2023   |")
        self.assertEqual(fy, "2023")

    def test_find_fy_line_bad(self):
        er = Encumbrance()
        fy = er.find_base_fy("Base Fiscal Year    |2023   |")
        self.assertNotEqual(fy, "2023")

    def test_find_layout_line_good(self):
        er = Encumbrance()
        fy = er.find_layout("|Layout              |/BFT_NP|")
        self.assertEqual(fy, "/BFT_NP")

    def test_find_layout_line_bad(self):
        er = Encumbrance()
        fy = er.find_layout("Layout              |/BFT_NP|")
        self.assertNotEqual(fy, "/BFT_NP")

    def test_is_dnd_cost_center_report(self):
        fname = os.path.join(BASE_DIR, "drmis_data/encumbrance_P1a.txt")
        print(f"File name is ::::{fname}")
        er = Encumbrance(fname)
        ok = er.is_dnd_cost_center_report()
        self.assertTrue(ok)

    def test_is_not_dnd_cost_center_report(self):
        fname = os.path.join(self.path, "drmis_data/Errors_in_file.txt")
        er = Encumbrance(fname)
        ok = er.is_dnd_cost_center_report()
        self.assertFalse(ok)

    def test_clean_header(self):
        header = "|Document N|Line Numbe|AcctAssNo.| Cur Year s|    Cur YR Bal|    Total Cur.|Funds Cent|Fund|Cost Cente|Order       |Document T|Encumbrance Type     |Line Text                                         |Prd.doc.no|Pred doc.i|Reference       |G/L Accoun|Due date  |Vendor nam                         |Created by  |"
        header = header.split("|")
        er = Encumbrance()
        er.clean_header(header)
        self.assertEqual(len(er.data["header"]), er.COLUMNS - 2)

    def test_find_header_line(self):
        fname = os.path.join(self.path, "encumbrance_P1a.txt")
        er = Encumbrance(fname)
        lineno = er.find_header_line()
        self.assertGreater(lineno, 0)

    def test_is_data_line(self):
        er = Encumbrance()
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
        er = Encumbrance()
        result_ok = er.line_to_csv(
            "|col1|col2|col3|col4|col5|col6|col7|col8|col9|col10|col11|col12|col13|col14|col15|col16|col17|col18|col19|col20|"
        )
        result_bad = er.line_to_csv(
            "|col1|col2|col3|col4|col5|col6|col7|col8|col9|col10|col11|col12|col13|col14|col15|col16|col17|col18|col19|"
        )

        self.assertEqual(20, len(result_ok), "List does not contain 20 elements")
        self.assertTrue(type(result_ok) is list, "Argument does not return a list")

        self.assertIsNone(result_bad, "Must returns none when list is not good")


if __name__ == "__main__":
    unittest.main()
