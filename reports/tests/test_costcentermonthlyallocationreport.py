import pytest
from django.db.models import Sum

from bft.management.commands import populate
from bft.models import (BftStatusManager, CostCenterAllocation,
                        CostCenterManager, FundManager)
from reports.models import CostCenterMonthlyAllocation
from reports.utils import CostCenterMonthlyAllocationReport


@pytest.mark.django_db
class TestCostCenterMonthlyAllocationReport:
    @pytest.fixture
    def populate(self):
        hnd = populate.Command()
        hnd.handle()

        bftm = BftStatusManager()
        self.fy = bftm.fy()
        self.period = bftm.period()
        self.quarter = bftm.quarter()
        self.cc_str = "8484WA"
        self.costcenter = CostCenterManager().cost_center(self.cc_str)
        self.fund = FundManager().fund("c113")

    def test_populate_allocation(self, populate):
        """Check our test data has expected allocation"""
        alloc_sum = CostCenterAllocation.objects.aggregate(Sum("amount"))
        assert 20010.99 == float(alloc_sum["amount__sum"])

    def test_costcenter_monthly_allocation_on_insert_allocation(self, populate):
        """After populate, 8484WA C113 has allocation of 10.  Insert 1000 allocation."""
        new_alloc = CostCenterAllocation()
        new_alloc.amount = 1000
        new_alloc.fund = self.fund
        new_alloc.costcenter = self.costcenter
        new_alloc.quarter = 1
        new_alloc.save()

        CCMAR = CostCenterMonthlyAllocationReport(fy=self.fy, period=self.period, quarter=self.quarter)

        grouped_sum = CCMAR.sum_allocation_cost_center()
        assert 1010 == float(grouped_sum[0]["allocation"])

        affected_count = CCMAR.insert_grouped_allocation(grouped_sum)
        assert 2 == affected_count

        cc_alloc = CostCenterMonthlyAllocation.objects.filter(costcenter=self.cc_str).aggregate(Sum("allocation"))
        assert 1010 == float(cc_alloc["allocation__sum"])

    def test_costcenter_monthly_allocation_on_update_allocation(self, populate):
        """After populate, 8484WA C113 has allocation of 10.  Let's update to 2000."""
        update_alloc = CostCenterAllocation.objects.get(
            costcenter=self.costcenter,
            fund=self.fund,
            quarter=self.quarter,
            fy=self.fy,
        )
        update_alloc.amount = 2000
        update_alloc.save()

        CCMAR = CostCenterMonthlyAllocationReport(fy=self.fy, period=self.period, quarter=self.quarter)

        grouped_sum = CCMAR.sum_allocation_cost_center()
        assert 2000 == float(grouped_sum[0]["allocation"])

        affected_count = CCMAR.insert_grouped_allocation(grouped_sum)
        assert 2 == affected_count

        cc_alloc = CostCenterMonthlyAllocation.objects.filter(costcenter=self.cc_str).aggregate(Sum("allocation"))
        assert 2000 == float(cc_alloc["allocation__sum"])
