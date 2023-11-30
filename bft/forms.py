from django import forms

from bft.models import BftStatus


class BftStatusForm(forms.ModelForm):
    class Meta:
        model = BftStatus
        fields = ["value"]

    def __init__(self, *args, **kwargs):
        super(BftStatusForm, self).__init__(*args, **kwargs)


class UploadForm(forms.Form):
    source_file = forms.FileField()
