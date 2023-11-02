from django import forms
from bft.models import BftStatusManager


class ChargeUploadForm(forms.Form):
    period = forms.CharField(label="Period", max_length=2, initial=0)
    fy = forms.CharField(label="Fiscal Year", initial=0)
    source_file = forms.FileField()
