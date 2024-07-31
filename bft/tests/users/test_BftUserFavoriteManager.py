import pytest

from bft.models import BftUserManager, Bookmark


@pytest.mark.django_db
class TestBookmarkManager:

    def test_create_user_favorite(self):
        owner = BftUserManager().create_user(email="luigi@forces.gc.ca", password="foo")
        link = "costcenter-table"
        name = "My Cost Centers"

        bm = Bookmark(owner=owner, bookmark_link=link, bookmark_name=name)
        bm.save()
        bm = Bookmark.search.owner(owner)

        assert len(bm) == 1
