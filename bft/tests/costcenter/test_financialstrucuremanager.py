import pytest

from bft.exceptions import ParentDoesNotExistError
from bft.models import (
    CostCenter,
    CostCenterManager,
    FinancialStructureManager,
    FundCenter,
    FundCenterManager,
    FundManager,
    SourceManager,
    Fund,
    Source,
)


@pytest.mark.django_db
class TestFinancialStructureManager:
    # Write a function that create the fund center 0162ND, 2184DA, 2184A3, 2184AA, 2184BE, 1111AA
    @pytest.fixture
    def populatedata(self):
        # Create some fund centers
        root_fc = FundCenter.objects.create(fundcenter="0162ND", shortname="ND")
        fc_1111aa = FundCenter.objects.create(fundcenter="1111AA", shortname="AA", fundcenter_parent=root_fc)
        fc_2184aa = FundCenter.objects.create(fundcenter="2184AA", shortname="AA", fundcenter_parent=root_fc)
        fc_2184da = FundCenter.objects.create(fundcenter="2184DA", shortname="DA", fundcenter_parent=fc_2184aa)
        print(fc_2184da.sequence)
        FundCenter.objects.create(fundcenter="2184A3", shortname="A3", fundcenter_parent=fc_2184da)
        FundCenter.objects.create(fundcenter="2184BE", shortname="BE", fundcenter_parent=fc_2184da)

        # Create cost center 8484WA with fund center 2184A3 as parent and fund C113 and source Basement
        fund = Fund.objects.create(fund="C113", name="National Procurement", vote="1")
        source = Source.objects.create(source="Basement")
        CostCenter.objects.create(
            costcenter="8484WA",
            shortname="WA",
            fund=fund,
            source=source,
            costcenter_parent=FundCenter.objects.get(fundcenter="2184A3"),
        )
        # Create cost center 8484XA with fund center 2184A3 as parent and fund C113 and source Basement
        CostCenter.objects.create(
            costcenter="8484XA",
            shortname="WA",
            fund=fund,
            source=source,
            costcenter_parent=FundCenter.objects.get(fundcenter="2184A3"),
        )
        # Create cost center 8484YA with fund center 2184A3 as parent and fund C113 and source Basement
        CostCenter.objects.create(
            costcenter="8484YA",
            shortname="WA",
            fund=fund,
            source=source,
            costcenter_parent=FundCenter.objects.get(fundcenter="2184A3"),
        )

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
        direct_descendants = len(FinancialStructureManager().get_sequence_direct_descendants(parent))
        assert 2 == direct_descendants

        parent = "1.2.1"
        assert 2 == len(FinancialStructureManager().get_sequence_direct_descendants(parent))

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
        assert "1.3" == child  # 1.1 alreadey set

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

    def test_set_parent_with_no_parent_empty_db(self):
        """Test set_parent returns '1' when no parent is provided and db is empty"""
        fsm = FinancialStructureManager()
        sequence = fsm.set_parent()
        assert sequence == "1"

    def test_set_parent_with_no_parent_existing_roots(self):
        """Test set_parent increments root sequence when roots exist"""
        # Create initial root fund center
        FundCenter.objects.create(fundcenter="1111AA", shortname="First Root", sequence="1")

        fsm = FinancialStructureManager()
        sequence = fsm.set_parent()
        assert sequence == "2"

    def test_set_parent_with_parent_fund_center(self):
        """Test set_parent creates correct sequence for fund center child"""
        parent = FundCenter.objects.create(fundcenter="1111AA", shortname="Parent", sequence="1")

        fsm = FinancialStructureManager()
        sequence = fsm.set_parent(parent)
        assert sequence == "1.1"

    def test_set_parent_with_parent_cost_center(self):
        """Test set_parent creates correct sequence for cost center child"""
        parent = FundCenter.objects.create(fundcenter="1111AA", shortname="Parent", sequence="1")

        fsm = FinancialStructureManager()
        sequence = fsm.set_parent(parent, costcenter_child=True)
        assert sequence == "1.0.1"

    def test_set_parent_multiple_children(self):
        """Test set_parent handles multiple children correctly"""
        parent = FundCenter.objects.create(fundcenter="1111AA", shortname="Parent", sequence="1")

        fsm = FinancialStructureManager()

        # Create first child
        sequence1 = fsm.set_parent(parent)
        assert sequence1 == "1.1"

        FundCenter.objects.create(
            fundcenter="2222AA", shortname="Child 1", sequence=sequence1, fundcenter_parent=parent
        )

        # Create second child
        sequence2 = fsm.set_parent(parent)
        assert sequence2 == "1.2"

    def test_set_parent_multiple_cost_center_children(self):
        """Test set_parent handles multiple cost center children correctly"""
        parent = FundCenter.objects.create(fundcenter="1111AA", shortname="Parent", sequence="1")

        fsm = FinancialStructureManager()
        # Create first a fund which will be assigned to the cost center
        fund = Fund.objects.create(fund="C113", name="National Procurement", vote="1")
        source = Source.objects.create(source="Basement")

        # Create first cost center child
        sequence1 = fsm.set_parent(parent, costcenter_child=True)
        assert sequence1 == "1.0.1"
        CostCenter.objects.create(
            costcenter="2222AA",
            shortname="Child 1",
            sequence=sequence1,
            costcenter_parent=parent,
            fund=fund,
            source=source,
        )

        # Create second cost center child
        sequence2 = fsm.set_parent(parent, costcenter_child=True)
        assert sequence2 == "1.0.2"
