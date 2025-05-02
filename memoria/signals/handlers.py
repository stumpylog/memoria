from django.contrib.auth import get_user_model
from django.db import models
from django.dispatch import receiver

from memoria.models import Image
from memoria.models import Person
from memoria.models import Pet
from memoria.models import RoughDate
from memoria.models import RoughLocation
from memoria.models import UserProfile

User = get_user_model()


@receiver(models.signals.post_save, sender=User)
def handle_create_user_profile(sender: type[User], instance: User, created: bool, **kwargs):  # noqa: ARG001, FBT001
    """
    When a user is created, create a profile for them
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(models.signals.post_delete, sender=Image)
def cleanup_files_on_delete(sender, instance: Image, using, **kwargs):  # noqa: ARG001
    """
    Removes files associated with the image when it is deleted.
    """
    if instance.full_size_path.exists():
        instance.full_size_path.unlink()
    if instance.thumbnail_path.exists():
        instance.thumbnail_path.unlink()
    # TODO: Maybe leave the original alone?
    if instance.original_path.exists():
        instance.original_path.unlink()


@receiver(models.signals.post_save, sender=Image)
def mark_image_as_dirty(sender, instance: Image, **kwargs):  # noqa: ARG001
    """
    Mark the image as dirty, ie, requiring a metadata sync to the file
    """

    # Use update so this doesn't loop
    Image.objects.filter(pk=instance.pk).update(is_dirty=True)


# On change
@receiver(models.signals.post_save, sender=Pet)
@receiver(models.signals.post_save, sender=Person)
# On delete
@receiver(models.signals.pre_delete, sender=Pet)
@receiver(models.signals.pre_delete, sender=Person)
def mark_images_as_dirty_on_m2m_change(
    sender: type[Pet | Person],  # noqa: ARG001
    instance: Pet | Person,
    *args,  # noqa: ARG001
    **kwargs,  # noqa: ARG001
):
    """
    Mark the image as dirty, ie, requiring a metadata sync to the file when various
    m2m relationships are changed
    """

    if isinstance(instance, Person):
        Image.objects.filter(people__pk=instance.pk).update(is_dirty=True)
    elif isinstance(instance, Pet):
        Image.objects.filter(pets__pk=instance.pk).update(is_dirty=True)


# On change
@receiver(models.signals.post_save, sender=RoughLocation)
@receiver(models.signals.post_save, sender=RoughDate)
# On delete
@receiver(models.signals.pre_delete, sender=RoughLocation)
@receiver(models.signals.pre_delete, sender=RoughDate)
def mark_images_as_dirty_on_fk_change(
    sender: type[RoughLocation | RoughDate],  # noqa: ARG001
    instance: RoughLocation | RoughDate,
    *args,  # noqa: ARG001
    **kwargs,  # noqa: ARG001
):
    """
    Mark the image as dirty, ie, requiring a metadata sync to the file when various
    foreign key relationships are changed
    """
    instance.images.all().update(is_dirty=True)
