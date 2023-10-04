import pytest
from costcenter.models import (
    CostCenterManager,
    FinancialStructureManager,
    FundCenter,
    FundCenterManager,
    FundManager,
    SourceManager,
    CostCenter,
)
from bft.exceptions import ParentDoesNotExistError, IncompatibleArgumentsError
from bft.management.commands import populate, uploadcsv


@pytest.mark.django_db
class TestFinancialStructureManager:
    @pytest.fixture
    def setup(self):
        self.fsm = FinancialStructureManager()
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_tiny.txt")

    def test_cost_center_is_child_of(self, setup):
        parent = FundCenterManager().fundcenter(fundcenter="1111AB")
        child = CostCenterManager().cost_center(costcenter="8486C1")
        assert True == self.fsm.is_child_of(parent, child)

    def test_cost_center_is_not_child_of(self, setup):
        parent = FundCenterManager().fundcenter(fundcenter="1111AB")
        child = CostCenterManager().cost_center(costcenter="8486B1")
        assert False == self.fsm.is_child_of(parent, child)

    def test_fund_center_is_child_of(self, setup):
        parent = FundCenterManager().fundcenter(fundcenter="1111AA")
        child = FundCenterManager().fundcenter(fundcenter="1111AB")

        assert True == self.fsm.is_child_of(parent, child)

    def test_fund_center_is_not_child_of(self, setup):
        parent = FundCenterManager().fundcenter(fundcenter="1111AB")
        child = FundCenterManager().fundcenter(fundcenter="1111AC")

        assert False == self.fsm.is_child_of(parent, child)

    def test_fund_center_is_descendant_of(self, setup):
        parent = FundCenterManager().fundcenter(fundcenter="1111AA")
        child = FundCenterManager().fundcenter(fundcenter="2222BB")

        assert True == self.fsm.is_descendant_of(parent, child)

    def test_fund_center_is_not_descendant_of(self, setup):
        parent = FundCenterManager().fundcenter(fundcenter="1111AC")
        child = FundCenterManager().fundcenter(fundcenter="2222BB")

        assert False == self.fsm.is_descendant_of(parent, child)

    def test_is_sequence_child_of(self, setup):
        assert True == self.fsm.is_sequence_child_of("1", "1.1")
        assert True == self.fsm.is_sequence_child_of("1.1", "1.1.1")
        assert False == self.fsm.is_sequence_child_of("1.1", "1.1")
        assert False == self.fsm.is_sequence_child_of("2.1", "2.1.1.1")
        assert True == self.fsm.is_sequence_child_of("2.1", "2.1.0.1")

    def test_is_sequence_descendant_of(self, setup):
        assert False == self.fsm.is_sequence_descendant_of("1", "1")
        assert True == self.fsm.is_sequence_descendant_of("1", "1.1.1")
        assert True == self.fsm.is_sequence_descendant_of("1.1", "1.1.1")
        assert False == self.fsm.is_sequence_descendant_of("1.1,1", "1.1")
        assert True == self.fsm.is_sequence_descendant_of("1.1.1", "1.1.1.0.1")
        assert True == self.fsm.is_sequence_descendant_of("1.10", "1.10.1.1")
        with pytest.raises(AttributeError):
            self.fsm.is_sequence_descendant_of("1.0.", "1.0.1.1")
        with pytest.raises(AttributeError):
            self.fsm.is_sequence_descendant_of("1.0", "1.0.1.1")

    def test_get_fund_center_cost_centers(self, setup):
        parent = FundCenterManager().fundcenter(fundcenter="1111AB")
        cc = self.fsm.get_fund_center_cost_centers(parent)
        assert 2 == cc.count()

    def test_get_fund_center_cost_centers_none(self, setup):
        parent = FundCenterManager().fundcenter(fundcenter="1111AA")
        cc = self.fsm.get_fund_center_cost_centers(parent)
        assert 0 == cc.count()

    def test_get_sequence_direct_descendants(self, setup):
        pc = populate.Command()
        pc.handle()

        parent = "1"
        assert 2 == len(self.fsm.get_sequence_direct_descendants(parent))

        parent = "1.1"
        assert 4 == len(self.fsm.get_sequence_direct_descendants(parent))

        parent = "1.2"
        assert 1 == len(self.fsm.get_sequence_direct_descendants(parent))

        parent = "2"
        with pytest.raises(ParentDoesNotExistError):
            self.fsm.get_sequence_direct_descendants(parent)

    def test_create_root_sequence(self, setup):
        sequence = self.fsm.set_parent()
        assert "2" == sequence

    def test_create_child_of_root(self, setup):
        pc = populate.Command()
        pc.handle()
        root = self.fsm.FundCenters(fundcenter="1111aa").first()
        child = self.fsm.set_parent(root)
        print(child)

    def test_create_child_using_parent(self, setup):
        pp = populate.Command()
        pp.handle()
        parent_obj = self.fsm.FundCenters(fundcenter="1111AC").first()
        new_seqno = self.fsm.create_child(parent_obj.fundcenter)
        assert "1.2.1" == new_seqno

    def test_move_fundcenter_to_another_one(self, setup):
        pp = populate.Command()
        pp.handle()
        family = list(self.fsm.FundCenters().values_list("sequence", flat=True))

        # create a fundcenter and assign it to 1.1.1
        assert "1.1.1.1" not in family
        parent = FundCenter.objects.get(sequence="1.1.1")
        FundCenter.objects.create(fundcenter="3333WW", shortname="ww", fundcenter_parent=parent, sequence="1.1.1.1")
        family = list(self.fsm.FundCenters().values_list("sequence", flat=True))
        assert "1.1.1.1" in family

        # move fund center from 1.1.1 to 1.1.2
        fc = FundCenter.objects.filter(fundcenter="3333WW").first()
        parent = self.fsm.FundCenters(fundcenter="2222BB").first()
        fc.sequence = self.fsm.set_parent(fundcenter_parent=parent)
        fc.save()
        saved_fc = FundCenter.objects.get(fundcenter="3333WW")
        assert fc.sequence == saved_fc.sequence

    def test_set_parent(self, setup):
        pc = populate.Command()
        pc.handle()

        parent = self.fsm.FundCenters(fundcenter="2222BB").first()
        p = self.fsm.set_parent(fundcenter_parent=parent)
        assert "1.1.2.1" == p

    def test_set_parent_of_cost_center(self, setup):
        pc = populate.Command()
        pc.handle()

        parent = FundCenterManager().fundcenter("2222BB")
        cc = CostCenterManager().cost_center("8486B1")
        p = self.fsm.set_parent(fundcenter_parent=parent, costcenter_child=True)
        cc.sequence = p
        cc.costcenter_parent = parent
        cc.save()
        assert "1.1.2.0.1" == CostCenterManager().cost_center("8486B1").sequence
        cc = CostCenterManager().cost_center("8486C1")
        p = self.fsm.set_parent(fundcenter_parent=parent, costcenter_child=True)
        cc.sequence = p
        cc.costcenter_parent = parent
        cc.save()
        assert "1.1.2.0.2" == CostCenterManager().cost_center("8486C1").sequence

    def test_sequence_on_create_cost_center_under_level_2(self, setup):
        pc = populate.Command()
        pc.handle()

        parent = FundCenterManager().fundcenter("2222BA")
        fund = FundManager().fund("C113")
        source = SourceManager().source("Kitchen")
        cc = {"costcenter": "2222zz", "fund": fund, "source": source, "costcenter_parent": parent}
        cc["sequence"] = self.fsm.set_parent(parent, True)
        costcenter = CostCenter.objects.create(**cc)
        assert "1.1.1.0.1" == costcenter.sequence

    def test_last_root_with_no_root_element(self):
        fsm = FinancialStructureManager()

        assert None == fsm.last_root()

    def test_last_root_with_one_root_element(self):
        fc = {"fundcenter": "1111AA", "shortname": "root 1", "fundcenter_parent": None}
        FundCenter.objects.create(**fc)
        fsm = FinancialStructureManager()

        assert "1" == fsm.last_root()

    def test_last_root_with_two_roots_element(self):
        fc = {"fundcenter": "1111AA", "shortname": "root 1", "fundcenter_parent": None}
        FundCenter.objects.create(**fc)
        fc = {"fundcenter": "1111AB", "shortname": "root 2", "fundcenter_parent": None}
        FundCenter.objects.create(**fc)
        fsm = FinancialStructureManager()

        assert "2" == fsm.last_root()
