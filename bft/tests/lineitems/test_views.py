import pytest
from django.test import Client

from bft.models import CostCenter


@pytest.mark.django_db
class TestCostCenterLineItem:

    def test_url_is_good(self, populatedata):
        c = Client()
        cc_id = CostCenter.objects.cost_center("8484wa").id
        response = c.get(f"/bft/lineitem/?costcenter={cc_id}")
        assert 200 == response.status_code
