import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from bft.models import CostCenter, FundCenter, FundManager, SourceManager
from bft.uploadprocessor import CostCenterLineItemProcessor, LineItemProcessor


@pytest.mark.django_db
class TestLineItemProcessor:
    @pytest.fixture
    def setup(self):
        self.source_file = f"{settings.BASE_DIR}/test-data/8486jm.txt"
        self.file_content = b"""
DND Cost Center Encumbrance Report

Funds Center :     2184JA and all subordinates
Base Fiscal Year : 2024
"""

    def test_no_file_path_provided(self):
        with pytest.raises(ValueError) as r:
            LineItemProcessor()
        expected = "No file name provided"
        assert expected in str(r.value)

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError) as r:
            LineItemProcessor(settings.BASE_DIR / "awol.txt")
        expected = f"{settings.BASE_DIR}/awol.txt was not found"
        assert expected == str(r.value)

    def test_not_finding_fundcenter(self, setup):
        p = LineItemProcessor(self.source_file)
        assert None is p.find_fund_center("blablabla")

    def test_find_fundcenter(self, setup):
        p = LineItemProcessor(self.source_file)
        assert "1111DD" == p.find_fund_center("Funds Center : 1111DD")

    def test_not_finding_base_fy(self, setup):
        p = LineItemProcessor(self.source_file)
        assert p.find_base_fy("Fiscal Year:") is None

    def test_find_base_fy(self, setup):
        p = LineItemProcessor(self.source_file)
        assert "2020" == p.find_base_fy("Base Fiscal Year : 2020")

    def test_report_does_not_match_post_request(self, setup, populatedata):
        c = Client()
        source_file = SimpleUploadedFile("file.txt", self.file_content, content_type="text/plain")
        c.post(reverse("fundcenter-lineitem-upload"), {"fundcenter": "2184DA", "source_file": source_file})
        with open(settings.UPLOAD_LOG, "r") as f:
            lastline = list(f)[-1]
        assert "does not match report found in dataset:" in lastline

    def test_not_a_dnd_costcenter_encumbrance_report(self, setup, populatedata):
        c = Client()
        content = b"""
DND Some Other Report

Funds Center :     2184DA and all subordinates
Base Fiscal Year : 2024
"""
        source_file = SimpleUploadedFile("file.txt", content, content_type="text/plain")
        c.post(reverse("fundcenter-lineitem-upload"), {"fundcenter": "2184DA", "source_file": source_file})
        with open(settings.UPLOAD_LOG, "r") as f:
            lastline = list(f)[-1]
        assert "DID not find DND Cost center report" in lastline


@pytest.mark.django_db
class TestCostCenterLineItemProcessor:
    @pytest.fixture
    def setup(self):
        self.source_file = f"{settings.BASE_DIR}/test-data/8486jm.txt"

    @pytest.fixture
    def create_costcenter(self):
        fund = FundManager().fund("C113")
        source = SourceManager().source("Common")
        parent = FundCenter.objects.create(**{"fundcenter": "2184JZ", "shortname": "JA NAME"})
        CostCenter(
            **{
                "costcenter": "8486JM",
                "fund": fund,
                "source": source,
                "costcenter_parent": parent,
                "isforecastable": True,
                "isupdatable": True,
            }
        ).save()

    def test_source_file_has_more_than_one_costcenter(self, setup, populatedata, create_costcenter):
        self.source_file = f"{settings.BASE_DIR}/test-data/8486jm-with-extra-cc.txt"
        c = CostCenterLineItemProcessor(self.source_file, "8486JM", "2184JZ")
        c.main()
        with open(settings.UPLOAD_LOG, "r") as f:
            lastline = list(f)[-1]
        assert "There are more that one cost center in the report" in lastline

    def test_init(self, setup, populatedata, create_costcenter):
        c = CostCenterLineItemProcessor(self.source_file, "8486JM", "2184JZ")
        c.main()
