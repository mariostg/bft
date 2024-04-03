from typing import Any

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from bft.models import (BftStatus, BftUser, CapitalInYear, CapitalNewYear,
                        CapitalProject, CapitalYearEnd, CostCenter,
                        CostCenterAllocation, CostCenterManager,
                        FinancialStructureManager, ForecastAdjustment, Fund,
                        FundCenter, FundCenterAllocation, FundCenterManager,
                        LineForecast, LineItem, Source)


class BftStatusForm(forms.ModelForm):
    class Meta:
        model = BftStatus
        fields = ["value"]

    def __init__(self, *args, **kwargs):
        super(BftStatusForm, self).__init__(*args, **kwargs)


class UploadForm(forms.Form):
    source_file = forms.FileField()


class ChargeUploadForm(forms.Form):
    period = forms.CharField(label="Period", max_length=2, initial=0)
    fy = forms.CharField(label="Fiscal Year", initial=0)
    source_file = forms.FileField()


class FundForm(forms.ModelForm):
    class Meta:
        model = Fund
        fields = ["fund", "name", "vote", "download"]

    def clean_vote(self):
        vote = self.cleaned_data["vote"]
        if not vote:
            return vote
        if vote != "1" and vote != "5":
            self.add_error("vote", "Vote must be 1 or 5")
        return vote

    def clean_fund(self):
        fund = self.cleaned_data["fund"].upper()
        if not fund:
            return fund
        if not fund[0].isalpha():
            self.add_error("fund", "Fund must begin with a letter")
        if len(fund) != 4:
            self.add_error("fund", "Fund must be 4 characters long.")
        return fund

    def __init__(self, *args, **kwargs):
        super(FundForm, self).__init__(*args, **kwargs)


class SourceForm(forms.ModelForm):
    class Meta:
        model = Source
        fields = ["source"]

    def clean_source(self):
        source = self.cleaned_data["source"]
        if not source.isupper() or source.islower():
            source = source.capitalize()
        return source

    def __init__(self, *args, **kwargs):
        super(SourceForm, self).__init__(*args, **kwargs)


class FundCenterForm(forms.ModelForm):
    class Meta:
        model = FundCenter
        fields = ["fundcenter", "shortname", "fundcenter_parent"]

    def __init__(self, *args, **kwargs):
        super(FundCenterForm, self).__init__(*args, **kwargs)


class FundCenterAllocationForm(forms.ModelForm):
    class Meta:
        model = FundCenterAllocation
        readonly_fields = ("owner", "updated", "created")
        fields = ["fundcenter", "fund", "fy", "quarter", "amount", "note", "owner"]

    def __init__(self, *args, **kwargs):
        super(FundCenterAllocationForm, self).__init__(*args, **kwargs)


class CapitalProjectForm(forms.ModelForm):
    class Meta:
        model = CapitalProject
        fields = [
            "project_no",
            "shortname",
            "fundcenter",
            "isupdatable",
            "procurement_officer",
            "note",
        ]

    def __init__(self, *args, **kwargs):
        super(CapitalProjectForm, self).__init__(*args, **kwargs)


class CapitalForecastingInYearForm(forms.ModelForm):
    class Meta:
        model = CapitalInYear
        fields = [
            "capital_project",
            "commit_item",
            "fund",
            "quarter",
            "fy",
            "allocation",
            "spent",
            "co",
            "pc",
            "fr",
            "le",
            "mle",
            "he",
            "notes",
        ]

    def __init__(self, *args, **kwargs):
        super(CapitalForecastingInYearForm, self).__init__(*args, **kwargs)


class CapitalForecastingNewYearForm(forms.ModelForm):
    class Meta:
        model = CapitalNewYear
        fields = [
            "capital_project",
            "commit_item",
            "fund",
            "fy",
            "initial_allocation",
            "notes",
        ]


class CapitalForecastingYearEndForm(forms.ModelForm):
    class Meta:
        model = CapitalYearEnd
        fields = [
            "capital_project",
            "commit_item",
            "fund",
            "fy",
            "ye_spent",
            "notes",
        ]


class CostCenterForm(forms.ModelForm):
    class Meta:
        model = CostCenter
        fields = [
            "costcenter",
            "shortname",
            "fund",
            "source",
            "costcenter_parent",
            "isforecastable",
            "isupdatable",
            "procurement_officer",
            "note",
        ]

    def __init__(self, *args, **kwargs):
        super(CostCenterForm, self).__init__(*args, **kwargs)


class CostCenterAllocationForm(forms.ModelForm):
    class Meta:
        model = CostCenterAllocation
        readonly_fields = ("owner", "updated", "created")
        fields = ["costcenter", "fund", "fy", "quarter", "amount", "note", "owner"]

    def __init__(self, *args, **kwargs):
        super(CostCenterAllocationForm, self).__init__(*args, **kwargs)


class ForecastadjustmentForm(forms.ModelForm):
    class Meta:
        model = ForecastAdjustment
        fields = ["costcenter", "fund", "amount", "note"]

    def __init__(self, *args, **kwargs):
        super(ForecastadjustmentForm, self).__init__(*args, **kwargs)

        self.fields["note"] = forms.CharField(
            widget=forms.Textarea(attrs={"class": "input"})
        )
        self.fields["amount"] = forms.CharField(
            widget=forms.TextInput(attrs={"class": "input"})
        )


class FundCenterAllocationUploadForm(UploadForm):
    quarter = forms.CharField(label="Quarter", max_length=1, initial=None)
    fy = forms.CharField(label="Fiscal Year", initial=None)


class CostCenterAllocationUploadForm(UploadForm):
    quarter = forms.CharField(label="Quarter", max_length=1, initial=None)
    fy = forms.CharField(label="Fiscal Year", initial=None)


class CapitalProjectForecastUploadForm(UploadForm):
    pass


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
    docno = forms.CharField(
        label="Document Number",
        max_length=24,
        widget=forms.TextInput(attrs={"disabled": "disbled"}),
    )
    forecastamount = forms.DecimalField(
        label="Forecast Amount", max_digits=10, decimal_places=2
    )


class CostCenterForecastForm(forms.Form):
    costcenter_pk = forms.CharField(label="Cost Center", widget=forms.HiddenInput())
    forecastamount = forms.DecimalField(
        label="Forecast Amount", max_digits=10, decimal_places=2
    )


class FundCenterLineItemUploadForm(UploadForm):
    def validate_fundcenter_exists(fc: str):
        fc = fc.upper()
        if not FundCenterManager().exists(fc):
            raise ValidationError(f"Fund Center {fc} does not exist", "invalid")

    fundcenter = forms.CharField(
        label="Fund center",
        max_length=6,
        initial=None,
        validators=[validate_fundcenter_exists],
    )


class CostCenterLineItemUploadForm(UploadForm):
    def validate_fundcenter_exists(fc: str):
        fc = fc.upper()
        if not FundCenterManager().exists(fc):
            raise ValidationError(f"Fund Center {fc} does not exist", "invalid")

    def validate_costcenter_exists(cc: str):
        cc = cc.upper()
        if not CostCenterManager().exists(cc):
            raise ValidationError(f"Cost Center {cc} does not exist", "invalid")

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        cc = cleaned_data.get("costcenter")
        fc = cleaned_data.get("fundcenter")
        if cc and fc:
            cc = CostCenterManager().cost_center(cc)
            fc = FundCenterManager().fundcenter(fc)
            if not FinancialStructureManager().is_child_of(fc, cc):
                raise ValidationError(
                    f"{cc} is not a direct descendant of {fc}", code="invalid"
                )

    fundcenter = forms.CharField(
        label="Fund center",
        max_length=6,
        initial=None,
        validators=[validate_fundcenter_exists],
        help_text="Fund center must be direct parent of cost center.",
    )
    costcenter = forms.CharField(
        label="cost center",
        max_length=6,
        initial=None,
        validators=[validate_costcenter_exists],
        help_text="Cost center must be unique in encumbrance report.",
    )


class UserSelfRegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ["first_name", "last_name", "email"]
        help_texts = {
            "email": "Only @forces.gc.ca email addresses accepted",
        }


class BftUserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BftUserForm, self).__init__(*args, **kwargs)
        if "instance" in kwargs:
            self.fields.pop("password")

    class Meta:
        model = BftUser
        fields = [
            "first_name",
            "last_name",
            "default_fc",
            "default_cc",
            "email",
            "is_active",
            "procurement_officer",
            "password",
        ]


class PasswordResetForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)

    password = forms.CharField(widget=forms.PasswordInput())
    username = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = BftUser
        fields = [
            "username",
            "password",
        ]
