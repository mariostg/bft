from django import forms
from bft.models import BftStatusManager


class ChargeUploadForm(forms.Form):
    period = forms.CharField(label="Period", max_length=2, initial=BftStatusManager().period())
    fy = forms.CharField(label="Fiscal Year", initial=BftStatusManager().fy)
    source_file = forms.FileField()
