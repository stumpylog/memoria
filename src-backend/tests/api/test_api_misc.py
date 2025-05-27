from http import HTTPStatus

import pytest
from django.test.client import Client

from memoria.models import Image


class TestCustom404:
    def test_custom_404_handle(self, client: Client):
        resp = client.get("/api/thisisnthere/")

        assert resp.status_code == HTTPStatus.NOT_FOUND

        data = resp.json()

        assert data["error"] == 'The resource "/api/thisisnthere/" was not found'
        assert data["status_code"] == HTTPStatus.NOT_FOUND


@pytest.mark.usefixtures("sample_image_environment")
@pytest.mark.django_db
class TestImageDelete:
    def test_image_delete(self):
        img = Image.objects.first()
        assert img is not None

        original_path = img.original_path
        full_size_path = img.full_size_path
        thumbnail_path = img.thumbnail_path

        assert original_path.exists()
        assert full_size_path.exists()
        assert thumbnail_path.exists()

        img.delete()

        assert not original_path.exists()
        assert not full_size_path.exists()
        assert not thumbnail_path.exists()
