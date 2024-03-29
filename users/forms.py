from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms
from users.models import BftUser


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
