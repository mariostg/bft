from django import forms

from costcenter.models import (
    Fund,
    Source,
    FundCenter,
    CostCenter,
    CostCenterAllocation,
    FundCenterAllocation,
    ForecastAdjustment,
)


class FundForm(forms.ModelForm):
    class Meta:
        model = Fund
        fields = ["fund", "name", "vote", "download"]

    def clean_vote(self):
        vote = self.cleaned_data["vote"]
        if not vote:
            return vote
        if vote != "1" and vote != "5":
            self.add_error("vote", "Vote must be 1 or 5")
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


class FundCenterAllocationForm(forms.ModelForm):
    class Meta:
        model = FundCenterAllocation
        readonly_fields = ("owner", "updated", "created")
        fields = ["fundcenter", "fund", "fy", "quarter", "amount", "note", "owner"]

    def __init__(self, *args, **kwargs):
        super(FundCenterAllocationForm, self).__init__(*args, **kwargs)


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


class CostCenterAllocationForm(forms.ModelForm):
    class Meta:
        model = CostCenterAllocation
        readonly_fields = ("owner", "updated", "created")
        fields = ["costcenter", "fund", "fy", "quarter", "amount", "note", "owner"]

    def __init__(self, *args, **kwargs):
        super(CostCenterAllocationForm, self).__init__(*args, **kwargs)


class ForecastadjustmentForm(forms.ModelForm):
    class Meta:
        model = ForecastAdjustment
        fields = ["costcenter", "fund", "amount", "note"]

    def __init__(self, *args, **kwargs):
        super(ForecastadjustmentForm, self).__init__(*args, **kwargs)

        self.fields["note"] = forms.CharField(widget=forms.Textarea(attrs={"class": "input"}))
        self.fields["amount"] = forms.CharField(widget=forms.TextInput(attrs={"class": "input"}))


class SearchFundCenterAllocationForm(forms.ModelForm):
    fundcenter = forms.CharField(required=False)
    fund = forms.CharField(required=False)
    fy = forms.CharField(required=False)
    quarter = forms.CharField(required=False)

    class Meta:
        model = FundCenterAllocation
        fields = (
            "fundcenter",
            "fund",
            "fy",
            "quarter",
        )
