import pytest
from django.contrib.auth import get_user_model
from users.models import BftUserManager


class TestBftUserManager:
    @pytest.fixture
    def setup(self):
        self.user = get_user_model()

    def test_normalise_email_has_invalid_domain(self, setup):
        with pytest.raises(ValueError):
            BftUserManager.normalize_email("luigi@frces.gc.ca")

    @pytest.mark.django_db
    def test_create_user(self, setup):

        new_user = self.user.objects.create_user(email="luigi@forces.gc.ca", password="foo")

        assert "luigi@forces.gc.ca" == new_user.email
        assert "luigi" == new_user.username
        print(new_user)
