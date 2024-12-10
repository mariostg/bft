import pytest

from bft.exceptions import ParentDoesNotExistError
from bft.models import (CostCenter, CostCenterManager,
                        FinancialStructureManager, FundCenter,
                        FundCenterManager, FundManager, SourceManager)


@pytest.mark.django_db
class TestFinancialStructureManager:

    def test_cost_center_is_child_of(self, populatedata):
        parent = FundCenterManager().fundcenter(fundcenter="2184A3")
        child = CostCenterManager().cost_center(costcenter="8484WA")
        assert True == FinancialStructureManager().is_child_of(parent, child)

    def test_cost_center_is_not_child_of(self, populatedata):
        parent = FundCenterManager().fundcenter(fundcenter="2184AA")
        child = CostCenterManager().cost_center(costcenter="8484WA")
        assert False == FinancialStructureManager().is_child_of(parent, child)

    def test_fund_center_is_child_of(self, populatedata):
        parent = FundCenterManager().fundcenter(fundcenter="2184DA")
        child = FundCenterManager().fundcenter(fundcenter="2184A3")

        assert True == FinancialStructureManager().is_child_of(parent, child)

    def test_fund_center_is_not_child_of(self, populatedata):
        parent = FundCenterManager().fundcenter(fundcenter="2184A3")
        child = FundCenterManager().fundcenter(fundcenter="1111AC")

        assert False == FinancialStructureManager().is_child_of(parent, child)

    def test_fund_center_is_descendant_of(self, populatedata):
        parent = FundCenterManager().fundcenter(fundcenter="2184AA")
        child = FundCenterManager().fundcenter(fundcenter="2184A3")

        assert True == FinancialStructureManager().is_descendant_of(parent, child)

    def test_fund_center_is_not_descendant_of(self, populatedata):
        parent = FundCenterManager().fundcenter(fundcenter="2184BE")
        child = FundCenterManager().fundcenter(fundcenter="2184DA")

        assert False == FinancialStructureManager().is_descendant_of(parent, child)

    def test_is_sequence_child_of(self):
        fsm = FinancialStructureManager()
        assert True == fsm.is_sequence_child_of("1", "1.1")
        assert True == fsm.is_sequence_child_of("1.1", "1.1.1")
        assert False == fsm.is_sequence_child_of("1.1", "1.1")
        assert False == fsm.is_sequence_child_of("2.1", "2.1.1.1")
        assert True == fsm.is_sequence_child_of("2.1", "2.1.0.1")

    def test_is_sequence_descendant_of(self):
        fsm = FinancialStructureManager()
        assert False == fsm.is_sequence_descendant_of("1", "1")
        assert True == fsm.is_sequence_descendant_of("1", "1.1.1")
        assert True == fsm.is_sequence_descendant_of("1.1", "1.1.1")
        assert False == fsm.is_sequence_descendant_of("1.1,1", "1.1")
        assert True == fsm.is_sequence_descendant_of("1.1.1", "1.1.1.0.1")
        assert True == fsm.is_sequence_descendant_of("1.10", "1.10.1.1")
        with pytest.raises(AttributeError):
            fsm.is_sequence_descendant_of("1.0.", "1.0.1.1")
        with pytest.raises(AttributeError):
            fsm.is_sequence_descendant_of("1.0", "1.0.1.1")

    def test_get_fund_center_cost_centers(self, populatedata):
        parent = FundCenterManager().fundcenter(fundcenter="2184A3")
        cc = FinancialStructureManager().get_fund_center_cost_centers(parent)
        assert 3 == cc.count()

    def test_get_fund_center_cost_centers_none(self, populatedata):
        parent = FundCenterManager().fundcenter(fundcenter="1111AA")
        cc = FinancialStructureManager().get_fund_center_cost_centers(parent)
        assert 0 == cc.count()

    def test_get_sequence_direct_descendants(self, populatedata):
        parent = "1"
        assert 1 == len(
            FinancialStructureManager().get_sequence_direct_descendants(parent)
        )

        parent = "1.1.1.1"
        assert 9 == len(FinancialStructureManager().get_sequence_direct_descendants(parent))

        parent = FundCenterManager().fundcenter("2184a3")
        assert 3 == len(
            FinancialStructureManager().get_sequence_direct_descendants(parent.sequence)
        )

        parent = "2"
        with pytest.raises(ParentDoesNotExistError):
            FinancialStructureManager().get_sequence_direct_descendants(parent)

    def test_create_root_sequence(self):
        sequence = FinancialStructureManager().set_parent()
        assert "1" == sequence

    def test_create_child_of_root(self, populatedata):
        root = FinancialStructureManager().FundCenters(fundcenter="0162ND").first()
        child = FinancialStructureManager().set_parent(root)
        assert "1.1.3" == child  # 1.1 alreadey set

    def test_create_child_using_parent(self, populatedata):
        parent_obj = FinancialStructureManager().FundCenters(fundcenter="2184A3").first()
        new_seqno = FinancialStructureManager().create_child(parent_obj.fundcenter)
        assert parent_obj.sequence + ".1" == new_seqno

    def test_move_fundcenter_to_another_one(self, populatedata):
        family = list(FinancialStructureManager().FundCenters().values_list("sequence", flat=True))

        # create a fundcenter and assign it to 2184DA
        parent = FundCenter.objects.get(fundcenter="2184A3")
        new_fc = FundCenter.objects.create(
            fundcenter="0000AA", shortname="AA", fundcenter_parent=parent
        )
        family = list(FinancialStructureManager().FundCenters().values_list("sequence", flat=True))
        assert new_fc.sequence in family

        # move fund center from 1.1.1.12.2 to 1.1.2
        fc = FundCenter.objects.get(fundcenter="0000AA")
        parent = FundCenter.objects.get(fundcenter="2184DA")
        fc.fundcenter_parent = parent
        fc.save()
        saved_fc = FundCenter.objects.get(fundcenter="0000AA")
        assert fc.sequence == saved_fc.sequence

    def test_set_parent(self, populatedata):
        parent = FinancialStructureManager().FundCenters(fundcenter="2184AA").first()
        p = FinancialStructureManager().set_parent(fundcenter_parent=parent)
        assert parent.sequence + ".14" == p

    def test_set_parent_of_cost_center(self, populatedata):
        parent = FundCenterManager().fundcenter("2184A3")
        cc = CostCenterManager().cost_center("8484WA")
        cc.costcenter_parent = parent
        cc.save()
        assert (
            parent.sequence + ".0.1"
            == CostCenterManager().cost_center("8484WA").sequence
        )

    def test_sequence_on_create_cost_center_under_level_2(self, populatedata):
        parent = FundCenterManager().fundcenter("2184AA")
        fund = FundManager().fund("C113")
        source = SourceManager().source("Basement")
        cc = {
            "costcenter": "2222zz",
            "fund": fund,
            "source": source,
            "costcenter_parent": parent,
        }
        costcenter = CostCenter.objects.create(**cc)
        assert "1.1.1.1.0.1" == costcenter.sequence

    def test_last_root_with_no_root_element(self):
        assert FinancialStructureManager().last_root() is None

    def test_last_root_with_one_root_element(self):
        fc = {"fundcenter": "1111AA", "shortname": "root 1", "fundcenter_parent": None}
        FundCenter.objects.create(**fc)

        assert "1" == FinancialStructureManager().last_root()

    def test_last_root_with_two_roots_element(self):
        fc = {"fundcenter": "1111AA", "shortname": "root 1", "fundcenter_parent": None}
        FundCenter.objects.create(**fc)
        fc = {"fundcenter": "2184A3", "shortname": "root 2", "fundcenter_parent": None}
        FundCenter.objects.create(**fc)

        assert "2" == FinancialStructureManager().last_root()
