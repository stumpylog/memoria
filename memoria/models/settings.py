from typing import Final

from django.db import models
from django.utils.translation import gettext_lazy as _

from memoria.models.abstract import AbstractTimestampMixin

DEFAULT_SINGLETON_INSTANCE_ID: Final[int] = 1


class SiteAdminSettings(AbstractTimestampMixin, models.Model):
    """
    Settings which are common across more than 1 parser
    """

    class Meta:
        verbose_name = _("memoria site-wide application settings")

    def __str__(self) -> str:  # pragma: no cover
        return "SiteAdminSettings"

    def save(self, *args, **kwargs):
        """
        Always save as the first and only model
        """
        self.pk = DEFAULT_SINGLETON_INSTANCE_ID
        super().save(*args, **kwargs)
