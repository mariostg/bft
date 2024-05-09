import pytest

from django.test import Client


@pytest.mark.django_db
class TestCostCenterMonthlyPlanViews:
    def test_no_params(self):
        response = Client().get("/reports/costcenter-monthly-plan")
        assert response.status_code == 200
