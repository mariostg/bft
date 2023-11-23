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
    def populate(self):
        self.fsm = FinancialStructureManager()
        hnd = populate.Command()
        hnd.handle()

    def upload(self):
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_2184a3.txt")

    def test_cost_center_is_child_of(self, populate):
        parent = FundCenterManager().fundcenter(fundcenter="2184A3")
        child = CostCenterManager().cost_center(costcenter="8484WA")
        assert True == self.fsm.is_child_of(parent, child)

    def test_cost_center_is_not_child_of(self, populate):
        parent = FundCenterManager().fundcenter(fundcenter="2184AA")
        child = CostCenterManager().cost_center(costcenter="8484WA")
        assert False == self.fsm.is_child_of(parent, child)

    def test_fund_center_is_child_of(self, populate):
        parent = FundCenterManager().fundcenter(fundcenter="2184DA")
        child = FundCenterManager().fundcenter(fundcenter="2184A3")

        assert True == self.fsm.is_child_of(parent, child)

    def test_fund_center_is_not_child_of(self, populate):
        parent = FundCenterManager().fundcenter(fundcenter="2184A3")
        child = FundCenterManager().fundcenter(fundcenter="1111AC")

        assert False == self.fsm.is_child_of(parent, child)

    def test_fund_center_is_descendant_of(self, populate):
        parent = FundCenterManager().fundcenter(fundcenter="2184AA")
        child = FundCenterManager().fundcenter(fundcenter="2184A3")

        assert True == self.fsm.is_descendant_of(parent, child)

    def test_fund_center_is_not_descendant_of(self, populate):
        parent = FundCenterManager().fundcenter(fundcenter="2184BE")
        child = FundCenterManager().fundcenter(fundcenter="2184DA")

        assert False == self.fsm.is_descendant_of(parent, child)

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

    def test_get_fund_center_cost_centers(self, populate):
        parent = FundCenterManager().fundcenter(fundcenter="2184A3")
        cc = self.fsm.get_fund_center_cost_centers(parent)
        assert 3 == cc.count()

    def test_get_fund_center_cost_centers_none(self, populate):
        parent = FundCenterManager().fundcenter(fundcenter="1111AA")
        cc = self.fsm.get_fund_center_cost_centers(parent)
        assert 0 == cc.count()

    def test_get_sequence_direct_descendants(self, populate):
        parent = "1"
        assert 2 == len(FinancialStructureManager().get_sequence_direct_descendants(parent))

        parent = "1.1.1.1"
        assert 2 == len(FinancialStructureManager().get_sequence_direct_descendants(parent))

        parent = FundCenterManager().fundcenter("2184da")
        assert 6 == len(FinancialStructureManager().get_sequence_direct_descendants(parent.sequence))

        parent = "2"
        with pytest.raises(ParentDoesNotExistError):
            FinancialStructureManager().get_sequence_direct_descendants(parent)

    def test_create_root_sequence(self):
        sequence = FinancialStructureManager().set_parent()
        assert "1" == sequence

    def test_create_child_of_root(self, populate):
        root = FinancialStructureManager().FundCenters(fundcenter="0162ND").first()
        child = FinancialStructureManager().set_parent(root)
        assert "1.3" == child  # 1.1 and 1.2 alreadey set

    def test_create_child_using_parent(self, populate):
        parent_obj = self.fsm.FundCenters(fundcenter="2184A3").first()
        new_seqno = self.fsm.create_child(parent_obj.fundcenter)
        assert parent_obj.sequence + ".1" == new_seqno

    def test_move_fundcenter_to_another_one(self, populate):
        family = list(self.fsm.FundCenters().values_list("sequence", flat=True))

        # create a fundcenter and assign it to SOFCOM
        parent = FundCenter.objects.get(fundcenter="2184BT")
        new_fc = FundCenter.objects.create(fundcenter="0000AA", shortname="AA", fundcenter_parent=parent)
        family = list(self.fsm.FundCenters().values_list("sequence", flat=True))
        assert new_fc.sequence in family

        # move fund center from 1.1.1.12.2 to 1.1.2
        fc = FundCenter.objects.get(fundcenter="2184A3")
        parent = FundCenter.objects.get(fundcenter="2184BT")
        fc.fundcenter_parent = parent
        fc.save()
        saved_fc = FundCenter.objects.get(fundcenter="2184A3")
        assert fc.sequence == saved_fc.sequence

    def test_set_parent(self, populate):
        parent = self.fsm.FundCenters(fundcenter="2184BT").first()
        p = self.fsm.set_parent(fundcenter_parent=parent)
        assert parent.sequence + ".1" == p

    def test_set_parent_of_cost_center(self, populate):
        parent = FundCenterManager().fundcenter("2184BT")
        cc = CostCenterManager().cost_center("8484WA")
        cc.costcenter_parent = parent
        cc.save()
        assert parent.sequence + ".0.1" == CostCenterManager().cost_center("8484WA").sequence

    def test_sequence_on_create_cost_center_under_level_2(self, populate):
        parent = FundCenterManager().fundcenter("2184AA")
        fund = FundManager().fund("C113")
        source = SourceManager().source("Kitchen")
        cc = {"costcenter": "2222zz", "fund": fund, "source": source, "costcenter_parent": parent}
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
        fc = {"fundcenter": "2184A3", "shortname": "root 2", "fundcenter_parent": None}
        FundCenter.objects.create(**fc)
        fsm = FinancialStructureManager()

        assert "2" == fsm.last_root()
