import pytest

from utils.getrequestfilter import set_query_string


class TestSetQueryString:
    def test_query_string_empty(self):
        assert "" == set_query_string()

    def test_query_string(self):
        s = set_query_string(fundcenter="2184aa", fund="c113", fy=2023, q="1")
        assert 39 == len(s)
