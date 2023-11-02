from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from users.forms import UserSelfRegisterForm

from users.models import BftUser


def user_login(request):
    if request.user.is_authenticated:
        return redirect("profile")

    if request.method == "POST":
        username = request.POST["username"].lower()
        password = request.POST["password"]

        try:
            user = BftUser.objects.get(username=username)
        except:
            messages.error(request, "Username does not exist")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            request.session["greeting"] = "Hello"
            return redirect(request.GET["next"] if "next" in request.GET else "bft")
        else:
            messages.error(request, "Username OR password is incorrect")

    return render(request, "users/user-login-form.html")


def user_profile(request):
    return render(request, "users/user-profile.html")


def user_logout(request):
    logout(request)
    return redirect("login")


def register_new_user(request):
    if request.method == "POST":
        form = UserSelfRegisterForm(request.POST)
        if form.is_valid:
            user_obj = form.save(commit=False)
            user_obj.username = user_obj.email.split("@")[0]
            user_obj.is_active = False
            user_obj.save()
            return redirect("login")
    else:
        form = UserSelfRegisterForm

    return render(request, "users/user-register-form.html", {"form": form})
