import logging

import numpy as np

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


np.set_printoptions(suppress=True)
logger = logging.getLogger("uploadcsv")


class BftUserManager(BaseUserManager):
    """BftUserManager class for managing BFT user accounts.

    This class extends Django's BaseUserManager to provide custom user management
    functionality specifically for the BFT application. It handles user creation,
    normalization of user data, and email validation specifically for forces.gc.ca domain.

    Methods:
        normalize_user(obj: BftUser) -> BftUser:
            Normalizes user's first and last names by capitalizing them.

        make_username(email: str) -> str:
            Extracts and returns username from email address.

        normalize_email(email: str) -> str:
            Normalizes email and validates it belongs to forces.gc.ca domain.

        create_user(email: str, password: str, **extra_fields) -> BftUser:
            Creates and saves a new user with the given email and password.

        create_superuser(email: str, password: str, **extra_fields) -> BftUser:
            Creates and saves a new superuser with the given email and password.

    Raises:
        ValueError: If email is empty, domain is not forces.gc.ca, or superuser flags are invalid.
    """

    @classmethod
    def normalize_user(cls, obj: "BftUser"):
        """Normalizes a BftUser object by capitalizing first and last names.

        Args:
            obj (BftUser): User object to be normalized.

        Returns:
            BftUser: The normalized user object with capitalized names.

        Example:
            >>> user = BftUser(first_name="john", last_name="doe")
            >>> normalized = BftUser.normalize_user(user)
            >>> print(normalized.first_name, normalized.last_name)
            John Doe
        """

        obj.first_name = obj.first_name.capitalize()
        obj.last_name = obj.last_name.capitalize()
        return obj

    @classmethod
    def make_username(cls, email) -> str:
        """Create a username from an email address.

        This method extracts the username portion from an email address by removing
        the domain part (everything after '@') and converting it to lowercase.

        Args:
            email (str): The email address to extract username from.

        Returns:
            str: The extracted username in lowercase.

        Example:
            >>> make_username("User.Name@example.com")
            "user.name"
        """

        username, _ = email.strip().rsplit("@", 1)
        return username.lower()

    @classmethod
    def normalize_email(cls, email):
        """
        Normalize an email address by converting to lowercase and validating domain.

        This method processes an email address by splitting it into local and domain parts,
        converting both to lowercase, and ensuring the domain is 'forces.gc.ca'.

        Args:
            email (str): The email address to normalize.

        Returns:
            str: The normalized email address.

        Raises:
            ValueError: If the domain part is not 'forces.gc.ca'.

        Example:
            >>> normalize_email("User.Name@FORCES.GC.CA")
            'user.name@forces.gc.ca'
        """

        email = email or ""
        try:
            email_name, domain_part = email.strip().rsplit("@", 1)
        except ValueError:
            pass
        else:
            email_name = email_name.lower()
            domain_part = domain_part.lower()
            email = email_name + "@" + domain_part

        if domain_part != "forces.gc.ca":
            raise ValueError("Domain Part of email not valid.  Expected forces.gc.ca")
        return email

    def create_user(self, email, password, **extra_fields):
        """
        Create a new user with the specified email and password.

        Args:
            email (str): The email address for the new user. Required.
            password (str): The password for the new user. Required.
            **extra_fields: Additional fields to be set on the user model.

        Returns:
            User: The newly created user instance.

        Raises:
            ValueError: If email is not provided.

        Note:
            The username is automatically generated from the email address by taking
            the part before the @ symbol.
        """

        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        username, _ = email.strip().rsplit("@", 1)
        user_model = get_user_model()
        user = user_model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Creates and saves a superuser with the given email and password.

        Args:
            email (str): The email address for the superuser.
            password (str): The password for the superuser.
            **extra_fields: Additional fields to be set for the superuser.

        Returns:
            User: The created superuser instance.

        Raises:
            ValueError: If is_staff or is_superuser is not True.

        Notes:
            - Sets is_staff, is_superuser, and is_active to True by default
            - Removes username field if present in extra_fields
            - Delegates actual user creation to create_user method
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
        except Exception:
            pass
        return self.create_user(email, password, **extra_fields)


class BftUser(AbstractUser):
    """A custom user model extending Django's AbstractUser.

    This model extends Django's AbstractUser to add custom fields and functionality
    specific to the BFT (Business Financial Tool) application.

    Attributes:
        default_fc (FundCenter): The user's default fund center, if any.
        default_cc (CostCenter): The user's default cost center, if any.
        procurement_officer (bool): Flag indicating if user has procurement officer privileges.
        objects (BftUserManager): Custom manager for BftUser model.

    Permissions:
        create_data: Allows user to create new data entries.
        upload_data: Allows user to upload data files.

    Note:
        This model uses RESTRICT for foreign key deletion to prevent accidental
        deletion of fund centers and cost centers that are set as defaults.
    """
    default_fc = models.OneToOneField(
        "FundCenter",
        on_delete=models.RESTRICT,
        verbose_name="Default FC",
        blank=True,
        null=True,
    )
    default_cc = models.OneToOneField(
        "CostCenter",
        on_delete=models.RESTRICT,
        verbose_name="Default CC",
        blank=True,
        null=True,
    )
    procurement_officer = models.BooleanField(default=False)
    objects = BftUserManager()

    class Meta:
        permissions = (
            ("create_data", "can create data"),
            ("upload_data", "can upload data"),
        )
