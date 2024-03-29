from django import forms

from costcenter.models import (
    Fund,
    Source,
    FundCenter,
    CostCenter,
    CapitalProject,
    CapitalInYear,
    CapitalNewYear,
    CapitalYearEnd,
    CostCenterAllocation,
    FundCenterAllocation,
    ForecastAdjustment,
)
from bft.forms import UploadForm


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
        fund = self.cleaned_data["fund"].upper()
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

    def clean_source(self):
        source = self.cleaned_data["source"]
        if not source.isupper() or source.islower():
            source = source.capitalize()
        return source

    def __init__(self, *args, **kwargs):
        super(SourceForm, self).__init__(*args, **kwargs)


class FundCenterForm(forms.ModelForm):
    class Meta:
        model = FundCenter
        fields = ["fundcenter", "shortname", "fundcenter_parent"]

    def __init__(self, *args, **kwargs):
        super(FundCenterForm, self).__init__(*args, **kwargs)


class FundCenterAllocationForm(forms.ModelForm):
    class Meta:
        model = FundCenterAllocation
        readonly_fields = ("owner", "updated", "created")
        fields = ["fundcenter", "fund", "fy", "quarter", "amount", "note", "owner"]

    def __init__(self, *args, **kwargs):
        super(FundCenterAllocationForm, self).__init__(*args, **kwargs)


class CapitalProjectForm(forms.ModelForm):
    class Meta:
        model = CapitalProject
        fields = [
            "project_no",
            "shortname",
            "fundcenter",
            "isupdatable",
            "procurement_officer",
            "note",
        ]

    def __init__(self, *args, **kwargs):
        super(CapitalProjectForm, self).__init__(*args, **kwargs)


class CapitalForecastingInYearForm(forms.ModelForm):
    class Meta:
        model = CapitalInYear
        fields = [
            "capital_project",
            "commit_item",
            "fund",
            "quarter",
            "fy",
            "allocation",
            "spent",
            "co",
            "pc",
            "fr",
            "le",
            "mle",
            "he",
            "notes",
        ]

    def __init__(self, *args, **kwargs):
        super(CapitalForecastingInYearForm, self).__init__(*args, **kwargs)


class CapitalForecastingNewYearForm(forms.ModelForm):
    class Meta:
        model = CapitalNewYear
        fields = [
            "capital_project",
            "commit_item",
            "fund",
            "fy",
            "initial_allocation",
            "notes",
        ]


class CapitalForecastingYearEndForm(forms.ModelForm):
    class Meta:
        model = CapitalYearEnd
        fields = [
            "capital_project",
            "commit_item",
            "fund",
            "fy",
            "ye_spent",
            "notes",
        ]


class CostCenterForm(forms.ModelForm):
    class Meta:
        model = CostCenter
        fields = [
            "costcenter",
            "shortname",
            "fund",
            "source",
            "costcenter_parent",
            "isforecastable",
            "isupdatable",
            "procurement_officer",
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


class FundCenterAllocationUploadForm(UploadForm):
    quarter = forms.CharField(label="Quarter", max_length=1, initial=None)
    fy = forms.CharField(label="Fiscal Year", initial=None)


class CostCenterAllocationUploadForm(UploadForm):
    quarter = forms.CharField(label="Quarter", max_length=1, initial=None)
    fy = forms.CharField(label="Fiscal Year", initial=None)


class CapitalProjectForecastUploadForm(UploadForm):
    pass
