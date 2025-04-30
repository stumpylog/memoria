from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from memoria.models import UserProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_profile(sender: type[User], instance: User, created: bool, **kwargs):  # noqa: ARG001, FBT001
    if created:
        UserProfile.objects.create(user=instance)
