import pytest
from costcenter.models import FinancialStructureManager, FundCenter, FundCenterManager
from bft.exceptions import ParentDoesNotExistError, IncompatibleArgumentsError
from encumbrance.management.commands import populate


@pytest.mark.django_db
class TestFinancialStructureManager:
    @pytest.fixture
    def setup(self):
        self.fsm = FinancialStructureManager()

    def test_is_child_of_parent(self, setup):

        assert True == self.fsm.is_child_of_parent("1", "1.1")
        assert True == self.fsm.is_child_of_parent("1.1", "1.1.1")
        assert False == self.fsm.is_child_of_parent("1.1", "1.1")
        assert False == self.fsm.is_child_of_parent("2.1", "2.1.1.1")

    def test_is_descendant_of_parent(self, setup):
        assert True == self.fsm.is_descendant_of_parent("1", "1.1.1")
        assert True == self.fsm.is_descendant_of_parent("1.1", "1.1.1")
        assert False == self.fsm.is_descendant_of_parent("1.1,1", "1.1")

    def test_get_descendants(self, setup):
        pc = populate.Command()
        pc.handle()
        family = list(self.fsm.FundCenters().values_list("sequence", flat=True))
        print(family)
        descendants = self.fsm.get_descendants(family, "1")
        assert 4 == len(descendants)
        descendants = self.fsm.get_descendants(family, "1.1")
        assert 2 == len(descendants)
        descendants = self.fsm.get_descendants(family, "1.2")
        assert 0 == len(descendants)
        with pytest.raises(ParentDoesNotExistError):
            descendants = self.fsm.get_descendants(family, "3")

    def test_get_direct_descendants(self, setup):
        pc = populate.Command()
        pc.handle()
        family = list(self.fsm.FundCenters().values_list("sequence", flat=True))

        parent = "1"
        assert 2 == len(self.fsm.get_direct_descendants(family, parent))

        parent = "1.1"
        assert 2 == len(self.fsm.get_direct_descendants(family, parent))

        parent = "1.2"
        assert 0 == len(self.fsm.get_direct_descendants(family, parent))

        parent = "2"
        with pytest.raises(ParentDoesNotExistError):
            self.fsm.get_direct_descendants(family, parent)

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
