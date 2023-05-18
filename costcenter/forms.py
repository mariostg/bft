from django import forms

from costcenter.models import Fund, Source, FundCenter, CostCenter


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


class FundCenterForm(forms.ModelForm):
    class Meta:
        model = FundCenter
        fields = ["fundcenter", "shortname", "parent"]

    def __init__(self, *args, **kwargs):
        super(FundCenterForm, self).__init__(*args, **kwargs)


class CostCenterForm(forms.ModelForm):
    class Meta:
        model = CostCenter
        fields = [
            "costcenter",
            "shortname",
            "fund",
            "source",
            "parent",
            "isforecastable",
            "isupdatable",
            "note",
        ]

    def __init__(self, *args, **kwargs):
        super(CostCenterForm, self).__init__(*args, **kwargs)
