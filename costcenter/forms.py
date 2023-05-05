from django import forms

from costcenter.models import Fund


class FundForm(forms.ModelForm):
    class Meta:
        model = Fund
        fields = ["fund", "name", "vote", "download"]

    def __init__(self, *args, **kwargs):
        super(FundForm, self).__init__(*args, **kwargs)
