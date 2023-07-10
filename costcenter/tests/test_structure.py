import pytest
import django

django.setup()
from costcenter.models import FinancialStructureManager, FundCenter
from costcenter.structure import Structure
from costcenter.structure import Structure, ParentDoesNotExistError
from encumbrance.management.commands import populate
from bft.exceptions import IncompatibleArgumentsError


class TestObs:
    family = {
        "obs": ["1", "1.1", "1.1.1", "1.2", "1.2.1"],
        "FC": ["DGLEPM", "DAEME", "DAEME 1", "DAVPM", "DAVPM 1"],
    }

    def test_is_child_of_parent(self):
        s = Structure()
        assert True == s.is_child_of_parent("1", "1.1")
        assert True == s.is_child_of_parent("1.1", "1.1.1")
        assert False == s.is_child_of_parent("1.1", "1.1")
        assert False == s.is_child_of_parent("2.1", "2.1.1.1")

    def test_is_descendant_of_parent(self):
        s = Structure()
        assert True == s.is_descendant_of_parent("1", "1.1.1")
        assert True == s.is_descendant_of_parent("1.1", "1.1.1")
        assert False == s.is_descendant_of_parent("1.1,1", "1.1")

    def test_get_descendants(self):
        s = Structure()
        family = self.family["obs"]
        descendants = s.get_descendants(family, "1")
        assert 4 == len(descendants)
        descendants = s.get_descendants(family, "1.1")
        assert 1 == len(descendants)
        descendants = s.get_descendants(family, "1.2")
        assert 1 == len(descendants)
        with pytest.raises(ParentDoesNotExistError):
            descendants = s.get_descendants(family, "3")

    def test_get_direct_descendants(self):
        s = Structure()
        family = self.family["obs"]
        parent = "1"
        assert 2 == len(s.get_direct_descendants(family, parent))
        parent = "1.1"
        assert 1 == len(s.get_direct_descendants(family, parent))
        parent = "1.2"
        assert 1 == len(s.get_direct_descendants(family, parent))
        parent = "2"
        with pytest.raises(ParentDoesNotExistError):
            s.get_direct_descendants(family, parent)

    def test_create_child_using_parent_and_seqno(self):
        s = Structure()
        family = self.family["obs"]
        with pytest.raises(IncompatibleArgumentsError):
            s.create_child(family, parent="1111AA", seqno="1.1")

    def test_create_child_using_seqno(self):
        s = Structure()
        family = self.family["obs"]
        child = s.create_child(family, seqno="1.1")
        assert "1.1.2" == child
        child = s.create_child(family, seqno="1.2.1")
        assert "1.2.1.1" == child
        with pytest.raises(ParentDoesNotExistError):
            child = s.create_child(family, seqno="3")

    def test_create_child_using_parent(self):
        pp = populate.Command()
        pp.handle()
        parent_obj = FinancialStructureManager().FundCenters(fundcenter="1111AC").first()
        tree_elements = [x.sequence for x in FinancialStructureManager().FundCenters()]
        s = Structure()
        new_seqno = s.create_child(tree_elements, parent_obj.fundcenter)
        assert "1.2.1" == new_seqno
        # print(new_tree_elements)

    def test_move_fundcenter_to_another_one(self):
        # pp = populate.Command()
        # pp.handle()
        s = Structure()
        tree_elements = [x.sequence for x in FinancialStructureManager().FundCenters()]

        # create a fundcenter and assign it to 1.1
        assert "1.1.1" not in tree_elements
        parent = FundCenter.objects.get(sequence="1.1")
        FundCenter.objects.create(fundcenter="3333WW", shortname="zz", parent=parent, sequence="1.1.1")
        tree_elements = [x.sequence for x in FinancialStructureManager().FundCenters()]
        assert "1.1.1" in tree_elements

        # move fund center from 1.1 to 1.2
        fsm = FinancialStructureManager()
        fc = fsm.FundCenters(fundcenter="3333WW").first()
        parent = fsm.FundCenters(fundcenter="1111AC").first()
        fsm.set_parent(fundcenter_child=fc, fundcenter_parent=parent)
