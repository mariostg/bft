from django import forms

from bft.models import BftStatus


class BftForm(forms.ModelForm):
    class Meta:
        model = BftStatus
        fields = ["value"]

    def __init__(self, *args, **kwargs):
        super(BftForm, self).__init__(*args, **kwargs)
