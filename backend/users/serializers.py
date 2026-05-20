from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ["id", "name", "email", "birthdate", "gender", "country", "creation_date"]
        read_only_fields = ["id", "email", "creation_date"]  # can't change these