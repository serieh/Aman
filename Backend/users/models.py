import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, name, password, **extra):
        user = self.model(email=self.normalize_email(email), name=name, **extra)
        user.set_password(password)  # handles bcrypt hashing
        user.save()
        return user

    def create_superuser(self, email, name, password, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_active", True)
        # Handle birthdate/gender/country if not provided
        extra.setdefault("birthdate", "2000-01-01")
        extra.setdefault("gender", "male")
        extra.setdefault("country", "US")
        return self.create_user(email, name, password, **extra)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    birthdate = models.DateField()
    gender = models.CharField(max_length=10, choices=[("male", "male"), ("female", "female")])
    country = models.CharField(max_length=2)
    creation_date = models.DateTimeField(auto_now_add=True)

    # Preferences
    theme = models.CharField(max_length=10, default="light")
    language = models.CharField(max_length=10, default="en")
    default_persona_id = models.CharField(max_length=50, default="aman")

    # Django Admin / Permissions
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]
    objects = UserManager()

    class Meta:
        db_table = "users"