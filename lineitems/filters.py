import django_filters
from lineitems.models import LineItem
import django.forms


class LineItemFilter(django_filters.FilterSet):
    # workingplan = django_filters.NumberFilter(field_name="workingplan", lookup_expr="gt")
    # has_working_plan_gt = django_filters.BooleanFilter(
    #     label="Working Plan greater than",
    #     field_name="workingplan",
    #     method="filter_working_plan_gt",
    #     widget=django.forms.CheckboxInput,
    # )
    # has_working_plan_lt = django_filters.BooleanFilter(
    #     label="Working Plan less than",
    #     field_name="workingplan",
    #     method="filter_working_plan_lt",
    #     widget=django.forms.CheckboxInput,
    # )
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

    def filter_working_plan_gt(self, queryset, name, value):
        return queryset.filter(workingplan__gt=value)

    def filter_working_plan_lt(self, queryset, name, value):
        return queryset.filter(workingplan__lt=value)

    def filter_has_no_forecast(self, queryset, name, value):
        if value:
            lookup = "__".join([name, "isnull"])
            print(lookup, name, value)
            return queryset.filter(**{lookup: True})
        else:
            return queryset
