from django import forms

from costcenter.models import Fund, Source


class FundForm(forms.ModelForm):
    class Meta:
        model = Fund
        fields = ["fund", "name", "vote", "download"]

    def __init__(self, *args, **kwargs):
        super(FundForm, self).__init__(*args, **kwargs)


class SourceForm(forms.ModelForm):
    class Meta:
        model = Source
        fields = ["source"]

    def __init__(self, *args, **kwargs):
        super(SourceForm, self).__init__(*args, **kwargs)
