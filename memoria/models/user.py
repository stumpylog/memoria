from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    bio = models.TextField(blank=True)

    images_per_page = models.PositiveSmallIntegerField(
        default=30,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(200),
        ],
    )

    def __str__(self):
        return f"{self.user.username}'s profile"
