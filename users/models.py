from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime
from django.contrib.auth.base_user import BaseUserManager


class BftUserManager(BaseUserManager):
    """
    Bft user model manager where userbane is the unique identifiers and is derived from the email address
    for authentication.  email address domain must be @forces.gc.ca
    """

    @classmethod
    def normalize_email(cls, email):
        """
        Normalize the email address by lowercasing the domain part of it.
        """
        email = email or ""
        try:
            email_name, domain_part = email.strip().rsplit("@", 1)
        except ValueError:
            pass
        else:
            email = email_name.lower() + "@" + domain_part.lower()

        if domain_part != "forces.gc.ca":
            raise ValueError("Domain Part of email not valid.  Expected forces.gc.ca")
        return email

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        username, _ = email.strip().rsplit("@", 1)

        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        try:
            extra_fields.pop("username")
        except:
            pass
        return self.create_user(email, password, **extra_fields)


class BftUser(AbstractUser):
    default_fc = models.CharField("Default FC", max_length=6, blank=True)
    default_cc = models.CharField("Default CC", max_length=6, blank=True)

    objects = BftUserManager()
