import pytest
from costcenter.structure import Structure, ParentDoesNotExistError


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

    def test_create_child(self):
        s = Structure()
        family = self.family["obs"]
        child = s.create_child(family, "1.1")
        assert "1.1.2" == child
        child = s.create_child(family, "1.2.1")
        assert "1.2.1.1" == child
        with pytest.raises(ParentDoesNotExistError):
            child = s.create_child(family, "3")
