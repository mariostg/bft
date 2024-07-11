import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.shortcuts import redirect, render

from bft.forms import BftUserForm, PasswordResetForm, UserSelfRegisterForm
from bft.models import BftUser, BftUserManager

logger = logging.getLogger("django")


def user_login(request):
    if request.user.is_authenticated:
        return redirect("profile")

    if request.method == "POST":
        username = request.POST["username"].lower()
        password = request.POST["password"]

        try:
            user = BftUser.objects.get(username=username)
        except BftUser.DoesNotExist:
            messages.error(request, "Username does not exist")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
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
            try:
                user_obj = form.save(commit=False)
            except ValueError as e:
                messages.error(request, e)
                return redirect("register")
            user_obj.username = BftUserManager.make_username(user_obj.email)
            logger.info(f"Creating username {user_obj.username}")
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
                _user.set_password(_user.password)
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
        try:
            if form.is_valid():
                _user = form.save(commit=False)
                _user = BftUserManager.normalize_user(_user)
                _user.save()
                return redirect("user-table")
        except ValueError as e:
            messages.error(request, e)

    return render(request, "users/user-form.html", {"form": form})


def user_delete(request, pk):
    _user = BftUser.objects.get(id=pk)
    if request.method == "POST":
        _user.delete()
        return redirect("user-table")
    context = {"object": BftUser, "back": "user-table"}
    return render(request, "core/delete-object.html", context)


def user_password_reset(request, pk):
    _user = BftUser.objects.get(id=pk)
    # print("INITIAL:", _user.password)
    form = PasswordResetForm(instance=_user)

    if request.method == "POST":
        form = PasswordResetForm(request.POST, instance=_user)
        if form.is_valid():
            _user = form.save(commit=False)
            # print("FORM 1:", _user.password)
            _user.set_password(_user.password)
            # print("FORM 2:", _user.password)
            _user.save()
            return redirect("user-table")

    return render(
        request,
        "users/user-password-reset-form.html",
        {"form": form, "username": _user.username},
    )
