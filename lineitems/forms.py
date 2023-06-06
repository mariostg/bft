from django import forms
from .models import LineForecast, LineItem


class LineForecastForm(forms.ModelForm):
    class Meta:
        model = LineForecast
        fields = [
            "forecastamount",
            "description",
            "comment",
            "deliverydate",
            "delivered",
            "buyer",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"cols": 80, "rows": 5}),
            "comment": forms.Textarea(attrs={"cols": 80, "rows": 5}),
        }
        # TODO readonly_fields = ["updated"]

    # def __init__(self, *args, **kwargs):
    # super(LineForecastForm, self).__init__(*args, **kwargs)


class SearchLineItemForm(forms.ModelForm):
    costcenter = forms.CharField(required=False)
    fund = forms.CharField(required=False)
    linetext = forms.CharField(required=False)
    doctype = forms.CharField(required=False)
    docno = forms.CharField(required=False)
    createdby = forms.CharField(required=False)
    status = forms.CharField(required=False)
    has_forecast = forms.BooleanField(required=False)
    has_workingplan = forms.BooleanField(required=False)

    class Meta:
        model = LineItem
        fields = (
            "costcenter",
            "fund",
            "doctype",
            "docno",
            "linetext",
            "createdby",
            "status",
        )
