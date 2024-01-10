from django import forms
from django.core.exceptions import ValidationError
from .models import LineForecast, LineItem
from costcenter.models import FundCenterManager, CostCenterManager
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


class CostCenterLineItemUploadForm(UploadForm):
    def validate_fundcenter_exists(fc: str):
        if not FundCenterManager().exists(fc):
            raise ValidationError(f"Fund Center {fc} does not exist", "invalid")

    def validate_costcenter_exists(cc: str):
        if not CostCenterManager().exists(cc):
            raise ValidationError(f"Cost Center {cc} does not exist", "invalid")

    fundcenter = forms.CharField(
        label="Fund center", max_length=6, initial=None, validators=[validate_fundcenter_exists]
    )
    costcenter = forms.CharField(
        label="cost center", max_length=6, initial=None, validators=[validate_costcenter_exists]
    )
