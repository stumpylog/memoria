import secrets

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def generate_token():
    return secrets.token_hex(32)


class Token(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tokens")
    key = models.CharField(max_length=64, default=generate_token, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)  # noqa: DJ001

    def __str__(self):
        return f"{self.user.username} - {self.name or self.key[:10]}"

    def is_valid(self):
        return not (self.expires_at and self.expires_at < timezone.now())

    def update_last_used(self):
        self.last_used_at = timezone.now()
        self.save()
