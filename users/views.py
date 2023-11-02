from django.shortcuts import render, redirect
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from users.forms import UserSelfRegisterForm, BftUserForm

from users.models import BftUser, BftUserManager


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
            user_obj.username = BftUserManager.make_username(user_obj.email)
            print("USERNAME : ", user_obj)
            user_obj.is_active = False
            user_obj.save()
            return redirect("login")
    else:
        form = UserSelfRegisterForm

    return render(request, "users/user-register-form.html", {"form": form})


def user_page(request):
    users = BftUser.objects.all()
    return render(request, "users/user-table.html", context={"users": users})


def user_add(request):
    if request.method == "POST":
        form = BftUserForm(request.POST)
        try:
            if form.is_valid():
                _user = form.save(commit=False)
                _user.username = BftUserManager.make_username(_user.email)
                _user = BftUserManager.normalize_user(_user)
                _user.save()
                return redirect("user-table")
        except ValueError as e:
            messages.error(request, e)
        except IntegrityError as e:
            if "username" in str(e):
                e = "username already exists"
            messages.error(request, e)
    else:
        form = BftUserForm

    return render(request, "users/user-form.html", {"form": form})


def user_update(request, pk):
    _user = BftUser.objects.get(id=pk)
    form = BftUserForm(instance=_user)

    if request.method == "POST":
        form = BftUserForm(request.POST, instance=_user)
        if form.is_valid():
            _user = form.save(commit=False)
            _user = BftUserManager.normalize_user(_user)
            _user.save()
            return redirect("user-table")

    return render(request, "users/user-form.html", {"form": form})


def user_delete(request, pk):
    _user = BftUser.objects.get(id=pk)
    if request.method == "POST":
        _user.delete()
        return redirect("user-table")
    context = {"object": BftUser, "back": "user-table"}
    return render(request, "core/delete-object.html", context)
