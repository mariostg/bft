import pytest
from django.contrib.auth import get_user_model

from bft.models import BftUser, BftUserManager


class TestBftUserManager:
    @pytest.fixture
    def setup(self):
        self.user = get_user_model()

    def test_normalise_email_has_invalid_domain(self, setup):
        with pytest.raises(ValueError):
            BftUserManager.normalize_email("luigi@frces.gc.ca")

    def test_normalise_email_with_upper_case(self):
        email = "JOE@FORCES.GC.CA"
        assert "joe@forces.gc.ca" == BftUserManager.normalize_email(email)

    def test_make_username(self):
        username = BftUserManager.make_username("joe@forces.gc.ca")
        assert "joe" == username

    @pytest.mark.django_db
    def test_create_user(self, setup):

        new_user = self.user.objects.create_user(
            email="luigi@forces.gc.ca", password="foo"
        )

        assert "luigi@forces.gc.ca" == new_user.email
        assert "luigi" == new_user.username

    @pytest.mark.django_db
    def test_create_superuser(self, setup):
        new_user = self.user.objects.create_superuser(
            email="luigi@forces.gc.ca", password="eeee"
        )

        assert "luigi@forces.gc.ca" == new_user.email
        assert "luigi" == new_user.username
