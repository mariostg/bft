from costcenter.models import (
    CostCenter,
    CostCenterAllocation,
    FundCenter,
    FundCenterAllocation,
    CapitalProject,
    CapitalInYear,
    CapitalNewYear,
    CapitalYearEnd,
)
import django_filters


class FundCenterFilter(django_filters.FilterSet):
    class Meta:
        model = FundCenter
        fields = {
            "fundcenter": ["iexact"],
            "shortname": ["icontains"],
            "fundcenter_parent__shortname": ["icontains"],
            "fundcenter_parent__fundcenter": ["icontains"],
        }


class CapitalProjectFilter(django_filters.FilterSet):
    class Meta:
        model = CapitalProject
        fields = {
            "project_no": ["icontains"],
            "shortname": ["icontains"],
            "fundcenter__shortname": ["icontains"],
            "fundcenter__fundcenter": ["icontains"],
        }


class CapitalNewYearFilter(django_filters.FilterSet):
    class Meta:
        model = CapitalNewYear
        fields = {
            "capital_project__project_no": ["icontains"],
            "fund__fund": ["iexact"],
        }


class CapitalInYearFilter(django_filters.FilterSet):
    class Meta:
        model = CapitalInYear
        fields = {
            "capital_project__project_no": ["icontains"],
            "fund__fund": ["iexact"],
        }


class CapitalYearEndFilter(django_filters.FilterSet):
    class Meta:
        model = CapitalYearEnd
        fields = {
            "capital_project__project_no": ["icontains"],
            "fund__fund": ["iexact"],
        }


class CostCenterFilter(django_filters.FilterSet):
    class Meta:
        model = CostCenter
        fields = {
            "costcenter": ["iexact"],
            "shortname": ["icontains"],
            "costcenter_parent__shortname": ["icontains"],
            "costcenter_parent__fundcenter": ["icontains"],
            "isupdatable": ["exact"],
            "isforecastable": ["exact"],
        }


class FundCenterAllocationFilter(django_filters.FilterSet):
    class Meta:
        model = FundCenterAllocation
        fields = {
            "fundcenter": ["exact"],
            "fund": ["exact"],
            "fy": ["iexact"],
            "quarter": ["iexact"],
        }


class CostCenterAllocationFilter(django_filters.FilterSet):
    class Meta:
        model = CostCenterAllocation
        fields = {
            "costcenter": ["exact"],
            "fund": ["exact"],
            "fy": ["iexact"],
            "quarter": ["iexact"],
        }
