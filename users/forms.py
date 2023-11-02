from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model


class UserSelfRegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ["first_name", "last_name", "email"]
        help_texts = {
            "email": "Only @forces.gc.ca email addresses accepted",
        }
