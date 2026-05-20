import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, name, password, **extra):
        user = self.model(email=self.normalize_email(email), name=name, **extra)
        user.set_password(password)  # handles bcrypt hashing
        user.save()
        return user

class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    birthdate = models.DateField()
    gender = models.CharField(max_length=10, choices=[("male", "male"), ("female", "female")])
    country = models.CharField(max_length=2)
    creation_date = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]
    objects = UserManager()

    class Meta:
        db_table = "users"