from django import forms

from bft.models import FundCenterAllocation


class UpdateCostCenterEncumbranceMonthlyForm(forms.Form):
    fy = forms.CharField()
    period = forms.CharField()


class UpdateCostCenterForecastLineItemMonthlyForm(forms.Form):
    fy = forms.CharField()
    period = forms.CharField()


class UpdateCostCenterForecastAdjustmentMonthlyForm(forms.Form):
    fy = forms.CharField()
    period = forms.CharField()


class UpdateCostCenterAllocationMonthlyForm(forms.Form):
    fy = forms.CharField()
    quarter = forms.CharField()
    period = forms.CharField()


class SearchCostCenterInYearDataForm(forms.Form):
    costcenter = forms.CharField(required=False)
    fund = forms.CharField(required=False)
    fy = forms.CharField(required=False)


class SearchCostCenterMonthlyDataForm(forms.Form):
    costcenter = forms.CharField(required=False)
    fund = forms.CharField(required=False)
    fy = forms.CharField(required=False)
    period = forms.CharField(required=False)


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


class SearchCostCenterScreeningReportForm(forms.ModelForm):
    fundcenter = forms.CharField(required=False)
    fund = forms.CharField(required=False)
    quarter = forms.CharField(required=False)

    class Meta:
        model = FundCenterAllocation
        fields = (
            "fundcenter",
            "fund",
            "fy",
            "quarter",
        )


class SearchCapitalForecastingDashboardForm(forms.Form):
    capital_project = forms.CharField(required=True)
    fund = forms.CharField(required=True)
    fy = forms.CharField(required=True)
    quarter = forms.CharField(required=False)


class SearchCapitalEstimatesForm(forms.Form):
    capital_project = forms.CharField(required=True)
    fund = forms.CharField(required=True)
    fy = forms.CharField(required=True)


class SearchCapitalFearsForm(forms.Form):
    capital_project = forms.CharField(required=True)
    fund = forms.CharField(required=True)
    fy = forms.CharField(required=True)


class SearchCapitalHistoricalForm(forms.Form):
    capital_project = forms.CharField(required=True)
    fund = forms.CharField(required=True)
    fy = forms.CharField(required=True)


class SearchCapitalYeRatiosForm(forms.Form):
    capital_project = forms.CharField(required=True)
    fund = forms.CharField(required=True)
    fy = forms.CharField(required=True)
