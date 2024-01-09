from django.test import TestCase

from costcenter.forms import FundForm
from costcenter.models import Fund


class FundFormTest(TestCase):
    def test_empty_form(self):
        form = FundForm()
        assert "fund" in form.fields
        assert "name" in form.fields
        assert "vote" in form.fields
        assert "download" in form.fields
        # test just one rendered field
        self.assertInHTML(
            '<input class="input" type="text" name="fund" maxlength="4" required="" id="id_fund">',
            str(form),
        )

    def test_filled_form(self):
        data = {"fund": "C119", "name": "National Procurement", "vote": 1, "download": True}
        f = FundForm(data=data)
        self.assertTrue(f.is_valid())

    def test_vote_not_1_or_5(self):
        data = {"fund": "C113", "name": "NP", "vote": "6", "download": 1}
        form = FundForm(data=data)

        self.assertEqual(form.errors["vote"], ["Vote must be 1 or 5"])

    def test_fund_starts_with_non_letter(self):
        data = {"fund": "3113"}
        form = FundForm(data=data)

        self.assertEqual(form.errors["fund"], ["Fund must begin with a letter"])

    def test_fund_is_not_4_characters_long(self):
        data = {"fund": "c3456"}
        form = FundForm(data=data)
        msg = f"Ensure this value has at most 4 characters (it has {len(data['fund'])})."
        self.assertEqual(form.errors["fund"], [msg])

    def test_fund_exists(self):
        data = {"fund": "C113", "vote": "1", "name": "NP"}
        fund = Fund(**data)
        fund.save()

        frm = FundForm(data=data)
        self.assertFalse(frm.is_valid())
