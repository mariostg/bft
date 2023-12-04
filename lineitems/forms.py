from django import forms
from .models import LineForecast, LineItem
from bft.forms import UploadForm


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
            "owner",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"cols": 80, "rows": 5}),
            "comment": forms.Textarea(attrs={"cols": 80, "rows": 5}),
        }
        # TODO readonly_fields = ["updated"]

    # def __init__(self, *args, **kwargs):
    # super(LineForecastForm, self).__init__(*args, **kwargs)


class DocumentNumberForm(forms.Form):
    docno = forms.CharField(label="Document Number", max_length=24)
    forecastamount = forms.DecimalField(label="Forecast Amount", max_digits=10, decimal_places=2)


class CostCenterForecastForm(forms.Form):
    costcenter = forms.CharField(label="Cost Center", max_length=6)
    forecastamount = forms.DecimalField(label="Forecast Amount", max_digits=10, decimal_places=2)


class LineItemUploadForm(UploadForm):
    fundcenter = forms.CharField(label="Fund center", max_length=6, initial=None)
