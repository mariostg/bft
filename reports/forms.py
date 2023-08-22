from django import forms
from costcenter.models import FundCenterAllocation


class SearchAllocationAnalysisForm(forms.ModelForm):
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