import django_filters
from lineitems.models import LineItem
import django.forms


class LineItemFilter(django_filters.FilterSet):
    has_no_forecast = django_filters.BooleanFilter(
        label="Has no Forecast",
        field_name="fcst",
        method="filter_has_no_forecast",
        widget=django.forms.CheckboxInput,
    )

    class Meta:
        model = LineItem
        fields = {
            "costcenter": ["exact"],
            "fund": ["iexact"],
            "doctype": ["iexact"],
            "docno": ["iexact"],
            "linetext": ["icontains"],
            "createdby": ["icontains"],
            "status": ["iexact"],
            "workingplan": ["gt", "lt"],
        }

    def filter_has_no_forecast(self, queryset, name, value):
        if value:
            lookup = "__".join([name, "isnull"])
            print(lookup, name, value)
            return queryset.filter(**{lookup: True})
        else:
            return queryset
