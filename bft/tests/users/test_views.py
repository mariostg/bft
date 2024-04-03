import pytest
from django.test import Client
from bft.models import BftUser


@pytest.mark.django_db
class TestBftUserViews:
    def test_add_user_create_username(self):
        data = {
            "first_name": "Cardinal",
            "last_name": "Rouge",
            "email": "cardinal@forces.gc.ca",
            "password": "HelloYou!!",
        }
        response = Client().post("/bft/user-add/", data=data)
        assert response.status_code == 302
        assert BftUser.objects.count() == 1
        new_user = BftUser.objects.first()
        assert new_user.username == "cardinal"

    def test_add_user_not_using_expected_domain_email(self):
        data = {
            "first_name": "Cardinal",
            "last_name": "Rouge",
            "email": "cardinal@force.gc.ca",
        }
        response = Client().post("/bft/user-add/", data=data)
        assert "Domain Part of email not valid.  Expected forces.gc.ca" in str(
            response.content
        )
