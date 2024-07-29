import pytest
from django.db import IntegrityError
from django.db.models import RestrictedError
from django.test import Client

from bft.exceptions import (InvalidAllocationException,
                            InvalidFiscalYearException, InvalidOptionException)
from bft.management.commands import populate
from bft.models import (CostCenter, CostCenterAllocation, CostCenterManager,
                        FinancialStructureManager, ForecastAdjustment, Fund,
                        FundCenter, FundManager, Source)

FUND_C113 = {"fund": "C113", "name": "National Procurement", "vote": "1"}
SOURCE_1 = {"source": "Basement"}
FC_1111AA = {"fundcenter": "1111aa", "shortname": "bedroom", "fundcenter_parent": None}
CC_1234FF = {
    "costcenter": "1234ff",
    "shortname": "Food and drink",
    "fund": None,
    "source": None,
    "isforecastable": True,
    "isupdatable": True,
    "note": "A quick and short note for 1234FF",
    "costcenter_parent": None,
}


@pytest.mark.django_db
class TestFundModel:
    def test_string_representation(self):
        fund = Fund(fund="C113", name="NP Capital", vote=1)
        assert str(fund) == "C113 - NP Capital"

    def test_verbose_name_plural(self):
        assert str(Fund._meta.verbose_name_plural) == "Funds"

    def test_can_save_and_retrieve_funds(self):
        first_fund = Fund()
        first_fund.fund = "c113"
        first_fund.name = "National procurement"
        first_fund.vote = "1"
        first_fund.download = True
        first_fund.save()

        first_fund = Fund()
        first_fund.fund = "X999"
        first_fund.name = "Not an interesting fund"
        first_fund.vote = "5"
        first_fund.download = False
        first_fund.save()

        saved_funds = Fund.objects.all()
        first_saved_fund = saved_funds[0]
        second_saved_fund = saved_funds[1]
        assert "C113" == first_saved_fund.fund
        assert "X999" == second_saved_fund.fund

    def test_saved_fund_is_capitalized(self):
        f = Fund()
        f.fund = "c113"
        f.name = "National procurement"
        f.vote = "1"
        f.download = True
        f.save()

        saved = Fund.objects.get(pk=f.pk)
        assert "C113" == saved.fund

    def test_fund_cannot_be_saved_twice(self):
        fund_1 = Fund()
        fund_1.fund = "C113"
        fund_1.name = "National procurement"
        fund_1.vote = "1"
        fund_1.download = True
        fund_1.save()

        fund_2 = Fund()
        fund_2.fund = "C113"
        fund_2.name = "Not an interesting fund"
        fund_2.vote = "5"
        fund_2.download = False
        with pytest.raises(IntegrityError):
            fund_2.save()

    def test_can_save_POST_request(self):
        data = {
            "fund": "C113",
            "name": "National Procurement",
            "vote": "1",
            "download": True,
        }

        c = Client()
        response = c.post("/fund/fund-add/", data=data)
        assert response.status_code == 302
        assert Fund.objects.count() == 1
        new_fund = Fund.objects.first()
        assert new_fund.fund == "C113"

    def test_can_delete_POST_request(self):
        data = {
            "fund": "C999",
            "name": "National Procurement",
            "vote": "1",
            "download": True,
        }
        fund = Fund.objects.create(**data)

        c = Client()
        response = c.post(f"/fund/fund-delete/{fund.id}")
        assert response.status_code == 301  # redirect to confirm page

    def test_can_update_fund_column_values(self):
        f0 = Fund(**FUND_C113)
        f0.save()

        f1 = Fund.objects.filter(fund="C113").first()
        f1.fund = "X999"
        f1.name = "New Name"
        f1.vote = 4
        f1.save()

        f2 = Fund.objects.filter(pk=f1.pk).first()
        assert "X999" == f2.fund
        assert "New Name" == f2.name
        assert "4" == f2.vote

    def test_can_delete_fund(self):
        f0 = Fund(**FUND_C113)
        f0.save()

        f1 = Fund.objects.get(pk=f0.id)
        f1.delete()

        assert 0 == Fund.objects.count()

    def test_delete_fund_with_cc_raises_restricted_error(self):
        fund = Fund(**FUND_C113)
        fund.save()
        source = Source(**SOURCE_1)
        source.save()
        parent = FundCenter(**FC_1111AA)
        parent.save()
        f0 = CostCenter(**CC_1234FF)
        f0.fund = fund
        f0.source = source
        f0.costcenter_parent = parent
        f0.save()

        with pytest.raises(RestrictedError):
            fund.delete()


@pytest.mark.django_db
class TestSourceModel:
    def test_string_representation(self):
        obj = Source(source="Bedroom")
        assert str(obj) == "Bedroom"

    def test_verbose_name_plural(self):
        assert str(Source._meta.verbose_name_plural) == "Sources"

    def test_can_save_and_retrieve_sources(self):
        first_source = Source()
        first_source.source = "Primary"
        first_source.save()

        first_source = Source()
        first_source.source = "Secondary"
        first_source.save()

        saved_sources = Source.objects.all()
        first_saved_source = saved_sources[0]
        second_saved_source = saved_sources[1]
        assert "Primary" == first_saved_source.source
        assert "Secondary" == second_saved_source.source

    def test_saved_source_is_capitalized(self):
        s = Source(source="my source")
        s.save()

        saved = Source.objects.get(pk=s.pk)
        assert "My source" == saved.source

    def test_source_cannot_be_saved_twice(self):
        Source.objects.all().delete()

        source_1 = Source()
        source_1.source = "Primary"
        source_1.save()

        source_2 = Source()
        source_2.source = "Primary"

        with pytest.raises(IntegrityError):
            source_2.save()

    def test_can_save_POST_request(self):
        data = {"source": "Ternaire"}
        response = Client().post("/source/source-add/", data=data)
        assert response.status_code == 302
        assert Source.objects.count() == 1
        new_source = Source.objects.first()
        assert new_source.source == "Ternaire"

    def test_can_update_source_column_values(self):
        f0 = Source()
        f0.source = "qwerty"
        f0.save()

        f1 = Source.objects.filter(source=f0.source).first()
        f1.source = "secondary"
        f1.save()

        f2 = Source.objects.filter(pk=f1.pk).first()
        assert "Secondary" == f2.source

    def test_delete_Source_with_cc_raises_restricted_error(self):
        fund = Fund(**FUND_C113)
        fund.save()
        source = Source(**SOURCE_1)
        source.save()
        parent = FundCenter(**FC_1111AA)
        parent.save()
        f0 = CostCenter(**CC_1234FF)
        f0.fund = fund
        f0.source = source
        f0.costcenter_parent = parent
        f0.save()

        with pytest.raises(RestrictedError):
            source.delete()


@pytest.mark.django_db
class TestFundCenterModel:
    fc_1111AA = {"fundcenter": "1111aa", "shortname": "bedroom", "fundcenter_parent": None}

    def test_string_representation(self):
        obj = FundCenter(fundcenter="1234aa", shortname="abcdef", fundcenter_parent=None)
        assert "1234AA - ABCDEF" == str(obj)

    def test_verbose_name_plural(self):
        assert "Fund Centers" == str(FundCenter._meta.verbose_name_plural)

    def test_create_fund_center_on_empy_db(self):
        fc_1111AA = {"fundcenter": "1111aa", "shortname": "bedroom"}
        fc = FundCenter.objects.create(**fc_1111AA)
        assert "1" == fc.sequence

    def test_create_fund_center_on_empy_db_and_a_child(self):
        fc_1111AA = {"fundcenter": "1111aa", "shortname": "home"}
        parent = FundCenter.objects.create(**fc_1111AA)

        fsm = FinancialStructureManager()
        child_sequence = fsm.set_parent(fundcenter_parent=parent)

        assert "1.1" == child_sequence
        fc_1111bb = {
            "fundcenter": "1111bb",
            "shortname": "bedroom",
            "fundcenter_parent": parent,
            "sequence": child_sequence,
        }
        child_fc = FundCenter.objects.create(**fc_1111bb)
        assert "1.1" == child_fc.sequence

    def test_can_save_and_retrieve_fund_centers(self):
        first_fc = FundCenter()
        first_fc.fundcenter = "1111aa"
        first_fc.shortname = "defgth"
        first_fc.sequence = "1"
        first_fc.fundcenter_parent = None
        first_fc.full_clean()
        first_fc.save()

        saved_fc = FundCenter.objects.get(pk=first_fc.pk)
        assert "1111AA" == saved_fc.fundcenter

    def test_create_fund_center_assigns_level(self):
        # Create a root level fund center, level should be one
        first_fc = FundCenter()
        first_fc.fundcenter = "1111aa"
        first_fc.shortname = "defgth"
        first_fc.sequence = "1"
        first_fc.fundcenter_parent = None
        first_fc.full_clean()
        first_fc.save()

        saved_fc = FundCenter.objects.get(pk=first_fc.pk)
        assert 1 == saved_fc.level

        # create a child to root level, level should be 2
        second_fc = FundCenter()
        second_fc.fundcenter = "1111bb"
        second_fc.shortname = "defgth"
        second_fc.sequence = FinancialStructureManager().set_parent(first_fc)
        second_fc.fundcenter_parent = first_fc
        second_fc.full_clean()
        second_fc.save()

        saved_fc = FundCenter.objects.get(pk=second_fc.pk)
        assert 2 == saved_fc.level

    def test_can_save_without_sequence_and_without_parent(self):
        fc = {"fundcenter": "1111aa", "shortname": "defgh"}
        first_fc = FundCenter(**fc)
        first_fc.save()

        saved_fc = FundCenter.objects.get(pk=first_fc.pk)
        assert "1111AA" == saved_fc.fundcenter
        assert "1" == saved_fc.sequence

    def test_save_without_shortname(self):
        first_fc = FundCenter()
        first_fc.fundcenter = "1111aa"
        first_fc.sequence = "1"
        first_fc.fundcenter_parent = None
        first_fc.full_clean()
        first_fc.save()

        saved_fc = FundCenter.objects.get(pk=first_fc.pk)
        assert "1111AA" == saved_fc.fundcenter

    def test_save_without_parent(self):
        first_fc = FundCenter()
        first_fc.fundcenter = "1111aa"
        first_fc.shortname = "defgth"
        first_fc.sequence = "1"
        first_fc.full_clean()
        first_fc.save()

        saved_fc = FundCenter.objects.get(pk=first_fc.pk)
        assert "1111AA" == saved_fc.fundcenter

    def test_saved_fund_center_as_uppercase(self):
        first_fc = FundCenter()
        first_fc.fundcenter = "1111aa"
        first_fc.shortname = "defgth"
        first_fc.sequence = "1"
        first_fc.fundcenter_parent = None
        first_fc.full_clean()
        first_fc.save()

        saved = FundCenter.objects.get(pk=first_fc.pk)
        assert "1111AA" == saved.fundcenter
        assert "DEFGTH" == saved.shortname

    def test_can_save_POST_request(self):
        data = {"fundcenter": "zzzz33", "shortname": "Basement FC", "fundcenter_parent": ""}
        response = Client().post("/bft/fundcenter-add/", data=data)
        assert response.status_code == 302
        assert FundCenter.objects.count() == 1
        obj = FundCenter.objects.first()
        assert obj.fundcenter == "ZZZZ33"
        assert obj.shortname == "BASEMENT FC"

    # TODO
    # def test_can_delete_POST_request():
    #    pass

    def test_can_update_fund_center_column_values(self):
        f0 = FundCenter(**self.fc_1111AA)
        f0.save()

        f1 = FundCenter.objects.get(pk=f0.pk)
        f1.fundcenter = "0000ff"
        f1.save()

        f2 = FundCenter.objects.get(pk=f1.pk)
        assert "0000FF" == f2.fundcenter

    def test_can_delete_fund_center(self):
        f0 = FundCenter(**self.fc_1111AA)
        f0.save()

        f1 = FundCenter.objects.get(pk=f0.id)
        f1.delete()

        assert 0 == Fund.objects.count()

    def test_set_parent_to_itself_not_allowed(self):
        fc1 = FundCenter()
        fc1.fundcenter = "1111aa"
        fc1.shortname = "defgth"
        fc1.fundcenter_parent = None
        fc1.save()

        fc1.fundcenter_parent = fc1
        with pytest.raises(IntegrityError):
            fc1.save()


@pytest.mark.django_db
class TestCostCenterModel:
    @pytest.fixture
    def populate(self):
        hnd = populate.Command()
        hnd.handle()

    def test_string_representation(self):
        obj = CostCenter(**CC_1234FF)
        assert "1234FF - Food and drink" == str(obj)

    def test_verbose_name_plural(self):
        assert "Cost Centers" == str(CostCenter._meta.verbose_name_plural)

    def test_can_save_and_retrieve_cost_centers(self):
        fund = Fund(**FUND_C113)
        fund.save()
        source = Source(**SOURCE_1)
        source.save()
        parent = FundCenter(**FC_1111AA)
        parent.save()
        cc = CostCenter(**CC_1234FF)
        cc.fund = fund
        cc.source = source
        cc.costcenter_parent = parent
        # cc.full_clean()
        cc.save()

        saved_cc = CostCenter.objects.cost_center(cc.costcenter)
        assert CC_1234FF["costcenter"].upper() == saved_cc.costcenter

    def test_saved_cost_center_as_uppercase(self):
        FSM = FinancialStructureManager()
        fund = Fund(**FUND_C113)
        fund.save()
        source = Source(**SOURCE_1)
        source.save()
        parent = FundCenter(**FC_1111AA)
        parent.save()
        cc = CostCenter(**CC_1234FF)
        cc.fund = fund
        cc.source = source
        cc.costcenter_parent = parent
        cc.costcenter = "1111aa"
        cc.shortname = "should be uppercase"
        cc.sequence = FSM.set_parent(cc.costcenter_parent, cc)
        cc.full_clean()
        cc.save()

        saved = CostCenter.objects.cost_center(cc.costcenter)
        assert cc.costcenter.upper() == saved.costcenter
        assert cc.shortname.upper() == saved.shortname

    def test_can_save_POST_request(self):
        data = CC_1234FF.copy()
        fund = Fund(**FUND_C113)
        fund.save()
        source = Source(**SOURCE_1)
        source.save()
        parent = FundCenter(**FC_1111AA)
        parent.save()
        data["fund"] = fund.pk
        data["source"] = source.pk
        data["costcenter_parent"] = parent.pk
        response = Client().post("/costcenter/costcenter-add/", data=data)
        assert response.status_code == 302
        assert CostCenter.objects.count() == 1
        obj = CostCenter.objects.first()
        assert CC_1234FF["costcenter"].upper() == obj.costcenter
        assert CC_1234FF["shortname"].upper() == obj.shortname

    def test_can_update_cost_center_column_values(self):
        fund = Fund(**FUND_C113)
        fund.save()
        source = Source(**SOURCE_1)
        source.save()
        parent = FundCenter(**FC_1111AA)
        parent.save()

        f0 = CostCenter(**CC_1234FF)
        f0.fund = fund
        f0.source = source
        f0.costcenter_parent = parent
        f0.save()
        f1 = CostCenter.objects.get(pk=f0.pk)
        f1.shortname = "new shortname"
        f1.save()

        f2 = CostCenter.objects.cost_center(f1.costcenter)
        assert f1.shortname.upper() == f2.shortname

    def test_can_delete_cost_center(self):
        fund = Fund(**FUND_C113)
        fund.save()
        source = Source(**SOURCE_1)
        source.save()
        parent = FundCenter(**FC_1111AA)
        parent.save()
        f0 = CostCenter(**CC_1234FF)
        f0.fund = fund
        f0.source = source
        f0.costcenter_parent = parent
        f0.save()

        f1 = CostCenter.objects.cost_center(f0.costcenter)
        f1.delete()

        assert 0 == CostCenter.objects.count()

    def test_parent_cannot_be_cost_center(self, populate):
        cc = CostCenterManager().cost_center("8484WA")

        parent = CostCenterManager().cost_center("8484XA")

        with pytest.raises(ValueError):
            cc.costcenter_parent = parent  # set a cost center as parent
            cc.save()


@pytest.mark.django_db
class TestForecastAdjustmentModel:

    @pytest.fixture
    def populate(self):
        hnd = populate.Command()
        hnd.handle()

    def test_string_representation(self):
        fund = Fund(fund="C113", name="NP", vote=1)
        cc = CostCenter(costcenter="8484WA", shortname="Basement", fund=fund)
        obj = ForecastAdjustment(costcenter=cc, fund=fund, amount=1000)
        assert str(obj) == "8484WA - Basement - C113 - NP - 1000"

    def test_verbose_name_plural(self):
        assert str(ForecastAdjustment._meta.verbose_name_plural) == "Forecast Adjustments"

    def test_can_save_and_retreive_forecast_adjustment(self, populate, upload):
        cc = CostCenterManager().cost_center("8484WA")
        fund = FundManager().fund("C113")
        fa = ForecastAdjustment()
        fa.costcenter = cc
        fa.fund = fund
        fa.amount = 1000
        fa.note = "Increase in demand"
        fa.save()

        f_saved = ForecastAdjustment.objects.get(pk=fa.pk)
        assert fa.amount == f_saved.amount


@pytest.mark.django_db
class TestCostCenterAllocation:
    @pytest.fixture
    def populate(self):
        hnd = populate.Command()
        hnd.handle()

    def test_string_representation(self, populate):
        cc = CostCenterManager().cost_center("8484WA")
        fund = FundManager().fund("C113")
        allocation = CostCenterAllocation.objects.get(costcenter=cc, fund=fund, fy=2023, quarter=1)
        assert str(allocation) == "8484WA - BASEMENT - C113 - Basement Procurement - 2023 Q1 100000.00"

    def test_verbose_name_plural(self):
        assert str(ForecastAdjustment._meta.verbose_name_plural) == "Forecast Adjustments"

    def test_save_and_retreive_allocation(self, populate):
        cc = CostCenterManager().cost_center("8484WA")
        fund = FundManager().fund("C523")

        allocation = CostCenterAllocation(costcenter=cc, fund=fund, fy=2025, quarter=1, amount=100)
        allocation.save()

        saved = CostCenterAllocation.objects.get(costcenter=cc, fund=fund, fy=2025, quarter=1)
        assert 100 == saved.amount

    def test_save_with_invalid_quarter(self, populate):
        cc = CostCenterManager().cost_center("8484WA")
        fund = FundManager().fund("C523")

        allocation = CostCenterAllocation(costcenter=cc, fund=fund, fy=2025, quarter=5, amount=100)
        with pytest.raises(InvalidOptionException):
            allocation.save()

    def test_save_with_negative_allocation(self, populate):
        cc = CostCenterManager().cost_center("8484WA")
        fund = FundManager().fund("C523")

        allocation = CostCenterAllocation(costcenter=cc, fund=fund, fy=2025, quarter=1, amount=-100)
        with pytest.raises(InvalidAllocationException):
            allocation.save()

    def test_save_with_invalid_year(self, populate):
        cc = CostCenterManager().cost_center("8484WA")
        fund = FundManager().fund("C523")

        allocation = CostCenterAllocation(costcenter=cc, fund=fund, fy=3025, quarter=1, amount=100)
        with pytest.raises(InvalidFiscalYearException):
            allocation.save()
