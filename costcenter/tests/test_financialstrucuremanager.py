import pytest
from costcenter.models import CostCenterManager, FinancialStructureManager, FundCenter, FundCenterManager
from bft.exceptions import ParentDoesNotExistError, IncompatibleArgumentsError
from encumbrance.management.commands import populate, uploadcsv


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

    def test_is_sequence_descendant_of(self, setup):
        assert True == self.fsm.is_sequence_descendant_of("1", "1.1.1")
        assert True == self.fsm.is_sequence_descendant_of("1.1", "1.1.1")
        assert False == self.fsm.is_sequence_descendant_of("1.1,1", "1.1")

    def test_get_fund_center_cost_centers(self, setup):
        parent = FundCenterManager().fundcenter(fundcenter="1111AB")
        cc = self.fsm.get_fund_center_cost_centers(parent)
        assert 2 == cc.count()

    def test_get_fund_center_cost_centers_none(self, setup):
        parent = FundCenterManager().fundcenter(fundcenter="1111AA")
        cc = self.fsm.get_fund_center_cost_centers(parent)
        assert 0 == cc.count()

    def test_get_fund_center_direct_descendants(self, setup):
        parent = FundCenterManager().fundcenter(fundcenter="1111AA")
        descendants = self.fsm.get_fundcenter_direct_descendants(parent)
        assert 2 == len(descendants)

    def test_get_fund_center_direct_descendants_empty(self, setup):
        parent = FundCenterManager().fundcenter(fundcenter="2222BB")
        descendants = self.fsm.get_fundcenter_direct_descendants(parent)
        assert 0 == len(descendants)

    def test_get_fund_center_direct_descendants_nonetype(self, setup):
        parent = FundCenterManager().fundcenter(fundcenter="2222ZZ")
        descendants = self.fsm.get_fundcenter_direct_descendants(parent)
        assert None == descendants

    def test_get_sequence_direct_descendants(self, setup):
        pc = populate.Command()
        pc.handle()

        parent = "1"
        assert 2 == len(self.fsm.get_sequence_direct_descendants(parent))

        parent = "1.1"
        assert 2 == len(self.fsm.get_sequence_direct_descendants(parent))

        parent = "1.2"
        assert 0 == len(self.fsm.get_sequence_direct_descendants(parent))

        parent = "2"
        with pytest.raises(ParentDoesNotExistError):
            self.fsm.get_sequence_direct_descendants(parent)

    def test_create_child_using_parent_and_seqno(self, setup):
        pc = populate.Command()
        pc.handle()
        family = list(self.fsm.FundCenters().values_list("sequence", flat=True))

        with pytest.raises(IncompatibleArgumentsError):
            self.fsm.create_child(family, parent="1111AA", seqno="1.1")

    def test_create_child_using_seqno(self, setup):
        pc = populate.Command()
        pc.handle()
        family = list(self.fsm.FundCenters().values_list("sequence", flat=True))

        child = self.fsm.create_child(family, seqno="1.1")
        assert "1.1.3" == child

        child = self.fsm.create_child(family, seqno="1.1.2")
        assert "1.1.2.1" == child

        with pytest.raises(ParentDoesNotExistError):
            self.fsm.create_child(family, seqno="3")

    def test_create_root_sequence(self, setup):
        sequence = self.fsm.set_parent()
        assert "1" == sequence

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
        family = list(self.fsm.FundCenters().values_list("sequence", flat=True))
        new_seqno = self.fsm.create_child(family, parent_obj.fundcenter)
        assert "1.2.1" == new_seqno

    def test_move_fundcenter_to_another_one(self, setup):
        pp = populate.Command()
        pp.handle()
        family = list(self.fsm.FundCenters().values_list("sequence", flat=True))

        # create a fundcenter and assign it to 1.1.1
        assert "1.1.1.1" not in family
        parent = FundCenter.objects.get(sequence="1.1.1")
        FundCenter.objects.create(fundcenter="3333WW", shortname="ww", parent=parent, sequence="1.1.1.1")
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

    def test_set_parent_without_parent(self, setup):
        pc = populate.Command()
        pc.handle()

        p = self.fsm.set_parent()
        assert "1" == p
