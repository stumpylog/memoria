from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from timezone_field import TimeZoneField

from memoria.models.abstract import AbstractTimestampMixin


class UserProfile(AbstractTimestampMixin, models.Model):
    class ImagesPerPageChoices(models.IntegerChoices):
        TEN = 10, _("10")
        TWENTY = 20, _("20")
        THIRTY = 30, _("30")
        FORTY = 40, _("40")
        FIFTY = 50, _("50")
        SIXTY = 60, _("60")
        SEVENTY = 70, _("70")
        EIGHTY = 80, _("80")
        NINETY = 90, _("90")
        ONE_HUNDRED = 100, _("100")

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    bio = models.TextField(blank=True)

    items_per_page = models.PositiveSmallIntegerField(
        default=ImagesPerPageChoices.THIRTY,
        choices=ImagesPerPageChoices.choices,
    )

    timezone = TimeZoneField(default="America/Los_Angeles", use_pytz=False)

    @property
    def timezone_name(self) -> str:
        return str(self.timezone)

    def __str__(self):
        return f"{self.user.username}'s profile"
