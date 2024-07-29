import pytest

from bft.management.commands import uploadcsv


@pytest.fixture
def upload():
    up = uploadcsv.Command()
    up.handle(encumbrancefile="test-data/encumbrance_2184A3.txt")
