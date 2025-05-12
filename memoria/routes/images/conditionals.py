import datetime

from django.http import HttpRequest
from scansteward.models import Image


def original_image_etag(request: HttpRequest, image_id: int) -> str:  # noqa: ARG001
    """
    Returns an ETag for the specified image based on its ID.

    Args:
        request (HttpRequest): The incoming HTTP request.
        image_id (int): The ID of the image to generate an ETag for.
    Returns:
        str: The generated ETag.
    """
    return Image.objects.get(pk=image_id).original_checksum


def image_last_modified(request: HttpRequest, image_id: int) -> datetime.datetime:  # noqa: ARG001
    """
    Returns the last modified date for the specified image based on its ID.
    """
    return Image.objects.get(pk=image_id).modified


def thumbnail_etag(request: HttpRequest, image_id: int) -> str:  # noqa: ARG001
    """
    Returns an ETag for the specified thumbnail based on its parent image ID.
    """
    return Image.objects.get(pk=image_id).thumbnail_checksum


def full_size_etag(request: HttpRequest, image_id: int) -> str:  # noqa: ARG001
    """
    Returns an ETag for the specified full size image based on its parent image ID.
    """
    return Image.objects.get(pk=image_id).full_size_checksum
