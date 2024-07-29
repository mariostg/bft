import pytest

from bft.management.commands import populate
from bft.models import LineItem, LineItemManager


@pytest.mark.django_db
class TestLineItemManager:
    @pytest.fixture
    def populate(self):
        hnd = populate.Command()
        hnd.handle()

    # Line Items tests
    def test_line_item_dataframe_no_line_items(self):
        r = LineItem

        assert True == r.objects.line_item_dataframe().empty

    def test_line_item_dataframe(self, populate, upload):
        df = LineItemManager().line_item_dataframe()
        assert 0 < len(df)
        assert "Lineitem_ID" in df.columns
        assert "Costcenter_ID" in df.columns

    def test_line_item_dataframe_single_fund(self, populate, upload):
        df = LineItemManager().line_item_dataframe(fund="c113")
        assert 6 == len(df)
        assert "Lineitem_ID" in df.columns
        assert "Costcenter_ID" in df.columns

    def test_line_item_dataframe_single_doctype(self, populate, upload):
        df = LineItemManager().line_item_dataframe(doctype="co")
        assert 3 == len(df)
        assert "Lineitem_ID" in df.columns
        assert "Costcenter_ID" in df.columns

    def test_line_item_detailed_dataframe_empty(self):
        r = LineItem
        assert True == r.objects.line_item_detailed_dataframe().empty

    def test_line_item_detailed_dataframe(self, populate, upload):
        li_df = LineItemManager().line_item_detailed_dataframe()
        assert "int" == li_df.dtypes.Spent
        assert "int" == li_df.dtypes.Forecast
        expected_columns = [
            "Lineitem_ID",
            "Docno",
            "Lineno",
            "Spent",
            "Balance",
            "Workingplan",
            "Fundcenter",
            "Fund",
            "Costcenter_ID",
            "Internalorder",
            "Doctype",
            "Enctype",
            "Linetext",
            "Predecessordocno",
            "Predecessorlineno",
            "Reference",
            "Gl",
            "Duedate",
            "Vendor",
            "Createdby",
            "Status",
            "Fcintegrity",
            "CO",
            "PC",
            "FR",
            "Lineforecast_ID",
            "Forecast",
            "spent initial",
            "balance initial",
            "workingplan initial",
            "Description",
            "Comment",
            "Delivery Date",
            "Delivered",
            "Buyer",
            "Owner_ID",
            "Updated",
            "Created",
            "Cost Center",
            "Cost Center Name",
            "Fund_ID",
            "Source_ID",
            "Is Forecastable",
            "Is Updatable",
            "Note",
            "CC Path",
            "Costcenter_parent_ID",
            "Procurement_officer_ID",
            "Fundcenter_ID",
            "Fund Center",
            "Fund Center Name",
            "FC Path",
            "Level",
            "Fundcenter_parent_ID",
        ]

        columns_found = li_df.columns

        for c in expected_columns:
            assert c in columns_found
        for c in columns_found:
            assert c in expected_columns

    def test_line_item_detailed_dataframe_single_doctype(self, populate, upload):
        df = LineItemManager().line_item_detailed_dataframe(doctype="co")
        assert 3 == len(df)
        assert "Lineitem_ID" in df.columns
        assert "Costcenter_ID" in df.columns

    def test_line_item_detailed_dataframe_single_fund(self, populate, upload):
        df = LineItemManager().line_item_detailed_dataframe(fund="C113")
        assert 6 == len(df)
        assert "Lineitem_ID" in df.columns
        assert "Costcenter_ID" in df.columns
