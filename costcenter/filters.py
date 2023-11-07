from costcenter.models import CostCenter, FundCenter
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
