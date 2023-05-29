from django import forms

from costcenter.models import Fund, Source, FundCenter, CostCenter


class FundForm(forms.ModelForm):
    class Meta:
        model = Fund
        fields = ["fund", "name", "vote", "download"]

    def clean_vote(self):
        vote = self.cleaned_data["vote"]
        if not vote:
            return vote
        if vote != "1" and vote != "5":
            self.add_error("Vote must be 1 or 5")
        return vote

    def clean_fund(self):
        fund = self.cleaned_data["fund"]
        if not fund:
            return fund
        if not fund[0].isalpha():
            self.add_error("fund", "Fund must begin with a letter")
        if len(fund) != 4:
            self.add_error("fund", "Fund must be 4 characters long.")
        return fund

    def __init__(self, *args, **kwargs):
        super(FundForm, self).__init__(*args, **kwargs)


class SourceForm(forms.ModelForm):
    class Meta:
        model = Source
        fields = ["source"]

    def __init__(self, *args, **kwargs):
        super(SourceForm, self).__init__(*args, **kwargs)


class FundCenterForm(forms.ModelForm):
    class Meta:
        model = FundCenter
        fields = ["fundcenter", "shortname", "parent"]

    def __init__(self, *args, **kwargs):
        super(FundCenterForm, self).__init__(*args, **kwargs)


class CostCenterForm(forms.ModelForm):
    class Meta:
        model = CostCenter
        fields = [
            "costcenter",
            "shortname",
            "fund",
            "source",
            "parent",
            "isforecastable",
            "isupdatable",
            "note",
        ]

    def __init__(self, *args, **kwargs):
        super(CostCenterForm, self).__init__(*args, **kwargs)
