import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from bft.forms import (CostCenterLineItemUploadForm,
                       FundCenterLineItemUploadForm)


@pytest.mark.django_db
class TestCostCenterLineItemUpload:
    @pytest.fixture
    def setup(self):
        self.data = {
            "fundcenter": "2184DA",
            "costcenter": "8484wa",
        }
        self.files = {
            "source_file": SimpleUploadedFile(
                "file.txt", b"file-content", content_type="text/plain"
            )
        }

    def test_form_is_valid(self, setup, populatedata):
        data = {
            "fundcenter": "2184a3",
            "costcenter": "8484wa",
        }
        f = CostCenterLineItemUploadForm(data=data, files=self.files)
        assert f.is_valid()

    def test_form_costcenter_not_the_child(self, setup, populatedata):
        data = {
            "fundcenter": "2184DA",
            "costcenter": "8484wa",
        }
        f = CostCenterLineItemUploadForm(data=data, files=self.files)
        assert "is not a direct descendant of" in f.errors["__all__"][0]

    def test_form_invalid_fund_center(self, setup, populatedata):
        self.data = {
            "fundcenter": "2184XX",
            "costcenter": "8484wa",
        }
        f = CostCenterLineItemUploadForm(data=self.data, files=self.files)
        assert f"Fund Center {self.data['fundcenter']} does not exist" in f.errors["fundcenter"]
        assert f.is_valid() == False

    def test_form_invalid_cost_center(self, setup, populatedata):
        self.data = {
            "fundcenter": "2184DA",
            "costcenter": "8484UU",
        }
        f = CostCenterLineItemUploadForm(data=self.data, files=self.files)
        assert "Cost Center 8484UU does not exist" in f.errors["costcenter"]
        assert f.is_valid() == False


@pytest.mark.django_db
class TestFundCenterLineItemUpload:
    @pytest.fixture
    def setup(self):
        self.data = {
            "fundcenter": "2184DA",
        }
        self.files = {
            "source_file": SimpleUploadedFile(
                "file.txt", b"file-content", content_type="text/plain"
            )
        }

    def test_form_is_valid(self, setup, populatedata):
        f = FundCenterLineItemUploadForm(data=self.data, files=self.files)
        assert f.is_valid()

    def test_form_invalid_fund_center(self, setup, populatedata):
        self.data = {
            "fundcenter": "2184XX",
        }
        f = FundCenterLineItemUploadForm(data=self.data, files=self.files)
        assert f"Fund Center {self.data['fundcenter']} does not exist" in f.errors["fundcenter"]
        assert f.is_valid() == False
