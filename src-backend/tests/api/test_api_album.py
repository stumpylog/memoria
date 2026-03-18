import itertools
import logging
import zipfile
from http import HTTPStatus
from pathlib import Path

import pytest
from django.test.client import Client
from faker import Faker
from ninja.testing import TestClient

from memoria.models import Album
from memoria.models import Image
from tests.api.conftest import AlbumFactory
from tests.api.conftest import GroupFactory
from tests.api.conftest import UserFactory


@pytest.mark.django_db
class TestApiAlbumRead:
    def test_read_no_albums_not_logged_in(self, client: TestClient, album_base_url: str) -> None:
        resp = client.get(album_base_url)

        assert resp.status_code == HTTPStatus.UNAUTHORIZED

    def test_read_no_albums(self, logged_in_client: TestClient, album_base_url: str) -> None:
        resp = logged_in_client.get(album_base_url)

        assert resp.status_code == HTTPStatus.OK

        assert resp.json() == {"count": 0, "items": []}

    def test_read_albums_no_access(self, logged_in_client: Client, album_factory: AlbumFactory, album_base_url: str):
        album_factory.create_batch(size=2)
        resp = logged_in_client.get(album_base_url)

        assert resp.status_code == HTTPStatus.OK

        # No view/edit access
        assert resp.json() == {"count": 0, "items": []}

    def test_read_albums_some_access(
        self,
        client: Client,
        album_factory: AlbumFactory,
        album_base_url: str,
        user_factory: UserFactory,
        group_factory: GroupFactory,
    ):
        edit_group = group_factory.create()
        view_group = group_factory.create()
        user = user_factory.create(groups=[view_group])
        client.login(username=user.username, password="password123")

        viewable_album = album_factory.create(view_groups=[view_group], edit_groups=[edit_group])
        album_factory.create()

        resp = client.get(album_base_url)

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()

        assert data["count"] == 1
        items = data["items"]
        assert len(items) == 1
        item = items[0]
        assert item["id"] == viewable_album.id
        assert item["name"] == viewable_album.name
        assert item["description"] == viewable_album.description
        assert item["view_groups"] == [{"id": view_group.pk, "name": view_group.name}]
        assert item["edit_groups"] == [{"id": edit_group.pk, "name": edit_group.name}]
        assert item["image_count"] == 0

    def test_get_single_album(self, superuser_client: Client, faker: Faker, album_base_url: str):
        instance = Album.objects.create(name=faker.unique.name())

        resp = superuser_client.get(f"{album_base_url}{instance.pk}/")

        assert resp.status_code == HTTPStatus.OK
        assert resp.json()["name"] == instance.name

    @pytest.mark.parametrize(
        ("last_idx",),  # noqa: PT006
        [
            (-1,),
            (-2,),
            (-3,),
            (-8,),
        ],
    )
    def test_get_filtered_albums(self, superuser_client: Client, faker: Faker, last_idx: int):
        name = faker.unique.name()

        Album.objects.create(name=name)

        resp = superuser_client.get("/api/album/", data={"album_name": name[:last_idx]})

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["count"] == 1
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["name"] == name
        assert item["description"] is None
        assert "id" in item


@pytest.mark.django_db
class TestApiAlbumCreate:
    def test_create_album(self, faker: Faker, album_api_create_factory):
        album_name = faker.unique.name()
        resp = album_api_create_factory(album_name)

        assert resp.status_code == HTTPStatus.CREATED
        data = resp.json()
        assert data["name"] == album_name
        assert data["description"] is None
        assert "id" in data

        assert Album.objects.filter(id=data["id"]).exists()
        assert Album.objects.get(id=data["id"]).name == album_name
        assert Album.objects.get(id=data["id"]).images.count() == 0

    def test_create_album_with_description(self, faker: Faker, album_api_create_factory):
        album_name = faker.unique.name()
        desc = faker.unique.sentence()
        resp = album_api_create_factory(album_name, desc)

        assert resp.status_code == HTTPStatus.CREATED
        data = resp.json()
        assert data["name"] == album_name
        assert data["description"] == desc
        assert "id" in data

        assert Album.objects.filter(id=data["id"]).exists()
        assert Album.objects.get(id=data["id"]).name == album_name
        assert Album.objects.get(id=data["id"]).description == desc
        assert Album.objects.get(id=data["id"]).images.count() == 0


@pytest.mark.django_db
class TestApiAlbumUpdate:
    def test_update_album(self, client: Client, faker: Faker, album_api_create_factory):
        album_name = faker.unique.name()
        resp = album_api_create_factory(album_name)

        assert resp.status_code == HTTPStatus.CREATED
        data = resp.json()

        assert data["name"] == album_name
        assert data["description"] is None
        album_id = data["id"]

        assert Album.objects.filter(id=album_id).exists()
        assert Album.objects.get(id=album_id).name == album_name
        assert Album.objects.get(id=album_id).images.count() == 0

        new_name = "A New Name"

        assert album_name != new_name

        resp = client.patch(
            f"/api/album/{album_id}/",
            content_type="application/json",
            data={"name": new_name},
        )

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["name"] == new_name
        assert data["description"] is None
        assert data["id"] == album_id
        assert Album.objects.filter(id=album_id).exists()
        assert Album.objects.get(id=album_id).name == new_name
        assert Album.objects.get(id=album_id).images.count() == 0

    def test_add_album_description(
        self,
        client: Client,
        faker: Faker,
        album_api_create_factory,
    ):
        album_name = faker.unique.name()
        resp = album_api_create_factory(album_name)

        assert resp.status_code == HTTPStatus.CREATED
        data = resp.json()
        assert data["name"] == album_name
        assert data["description"] is None
        album_id = data["id"]
        assert Album.objects.get(id=album_id).name == album_name
        assert Album.objects.get(id=album_id).description is None

        desc = "This is a description"

        resp = client.patch(
            f"/api/album/{album_id}/",
            content_type="application/json",
            data={"description": desc},
        )

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["name"] == album_name
        assert data["description"] == desc
        assert data["id"] == album_id
        assert Album.objects.get(id=album_id).name == album_name
        assert Album.objects.get(id=album_id).description == desc

    def test_update_album_no_data(
        self,
        client: Client,
        faker: Faker,
        album_api_create_factory,
    ):
        album_name = faker.unique.name()
        resp = album_api_create_factory(album_name)

        album_id = resp.json()["id"]

        resp = client.patch(
            f"/api/album/{album_id}/",
            content_type="application/json",
            data={},
        )

        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.django_db
class TestApiAlbumDelete:
    def test_delete_album(self, client: Client, faker: Faker, album_api_create_factory):
        album_name = faker.unique.name()
        resp = album_api_create_factory(album_name)

        assert resp.status_code == HTTPStatus.CREATED
        data = resp.json()
        assert data["name"] == album_name
        assert data["description"] is None
        album_id = data["id"]

        resp = client.delete(f"/api/album/{album_id}/")

        assert resp.status_code == HTTPStatus.NO_CONTENT

    def test_delete_does_not_exist(self, logged_in_client: Client):
        resp = logged_in_client.delete("/api/album/1/")

        assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.usefixtures("sample_image_database")
@pytest.mark.django_db
class TestApiAlbumImages:
    def test_add_single_image(self, client: Client, faker: Faker, album_api_create_factory):
        album_name = faker.unique.name()
        resp = album_api_create_factory(album_name)

        assert resp.status_code == HTTPStatus.CREATED
        album_id = resp.json()["id"]

        img = Image.objects.order_by("pk").first()

        resp = client.patch(
            f"/api/album/{album_id}/add/",
            content_type="application/json",
            data={"image_ids": [img.pk]},
        )

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["name"] == album_name
        assert data["description"] is None
        assert data["id"] == album_id
        assert data["image_ids"] == [img.pk]

        resp = client.get(f"/api/album/{album_id}/")

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["name"] == album_name
        assert data["description"] is None
        assert data["id"] == album_id
        assert data["image_ids"] == [img.pk]

    def test_add_multiple_images(
        self,
        client: Client,
        faker: Faker,
        album_api_create_factory,
    ):
        album_name = faker.unique.name()
        resp = album_api_create_factory(album_name)

        assert resp.status_code == HTTPStatus.CREATED
        album_id = resp.json()["id"]

        img_one, img_two = Image.objects.order_by("pk")[:2]

        resp = client.patch(
            f"/api/album/{album_id}/add/",
            content_type="application/json",
            data={"image_ids": [img_one.pk, img_two.pk]},
        )

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["name"] == album_name
        assert data["description"] is None
        assert data["id"] == album_id
        assert data["image_ids"] == [img_one.pk, img_two.pk]

        album = Album.objects.get(pk=album_id)

        assert album.images.count() == 2

    def test_remove_image(self, client: Client, faker: Faker, album_api_create_factory):
        album_name = faker.unique.name()
        resp = album_api_create_factory(album_name)

        assert resp.status_code == HTTPStatus.CREATED
        album_id = resp.json()["id"]

        resp = client.patch(
            f"/api/album/{album_id}/add/",
            content_type="application/json",
            data={"image_ids": [img.pk for img in Image.objects.all()]},
        )
        assert resp.status_code == HTTPStatus.OK

        test_img = Image.objects.order_by("pk").first()
        removed_pk = test_img.pk

        resp = client.patch(
            f"/api/album/{album_id}/remove/",
            content_type="application/json",
            data={"image_ids": [test_img.pk]},
        )
        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["name"] == album_name
        assert data["description"] is None
        assert data["id"] == album_id
        assert data["image_ids"] == [x.pk for x in Image.objects.exclude(pk=removed_pk).all()]

    def test_remove_image_not_in_album(
        self,
        caplog: pytest.LogCaptureFixture,
        client: Client,
        faker: Faker,
        album_api_create_factory,
    ):
        album_name = faker.unique.name()
        resp = album_api_create_factory(album_name)

        assert resp.status_code == HTTPStatus.CREATED
        album_id = resp.json()["id"]

        not_added_image = Image.objects.order_by("pk").last()
        dont_add_pk = not_added_image.pk
        resp = client.patch(
            f"/api/album/{album_id}/add/",
            content_type="application/json",
            data={"image_ids": [img.pk for img in Image.objects.exclude(pk=dont_add_pk).all()]},
        )
        assert resp.status_code == HTTPStatus.OK

        # The memoria logger has propagate=False in settings, so caplog can't
        # capture its records via the root logger. Temporarily enable propagation.
        memoria_logger = logging.getLogger("memoria")
        memoria_logger.propagate = True
        caplog.set_level(logging.WARNING)
        caplog.clear()
        resp = client.patch(
            f"/api/album/{album_id}/remove/",
            content_type="application/json",
            data={"image_ids": [not_added_image.pk]},
        )
        memoria_logger.propagate = False
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.message == f"No images from {[not_added_image.pk]} found in album {album_id}"
        assert record.levelname == "WARNING"
        assert resp.status_code == HTTPStatus.OK

        resp = client.get(f"/api/album/{album_id}/")
        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["name"] == album_name
        assert data["description"] is None
        assert data["id"] == album_id
        assert data["image_ids"] == [x.pk for x in Image.objects.exclude(pk=dont_add_pk).all()]

    def test_remove_last_album_image(
        self,
        client: Client,
        faker: Faker,
        album_api_create_factory,
    ):
        album_name = faker.unique.name()
        resp = album_api_create_factory(album_name)

        assert resp.status_code == HTTPStatus.CREATED
        album_id = resp.json()["id"]

        resp = client.patch(
            f"/api/album/{album_id}/add/",
            content_type="application/json",
            data={"image_ids": [img.pk for img in Image.objects.all()]},
        )
        assert resp.status_code == HTTPStatus.OK

        test_img = Image.objects.last()
        assert test_img is not None

        resp = client.patch(
            f"/api/album/{album_id}/remove/",
            content_type="application/json",
            data={"image_ids": [test_img.pk]},
        )
        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["name"] == album_name
        assert data["description"] is None
        assert data["id"] == album_id
        assert data["image_ids"] == [x.pk for x in Image.objects.exclude(pk=test_img.pk).all()]

    def test_add_remove_no_items(
        self,
        client: Client,
        faker: Faker,
        album_api_create_factory,
    ):
        album_name = faker.unique.name()
        resp = album_api_create_factory(album_name)

        assert resp.status_code == HTTPStatus.CREATED
        album_id = resp.json()["id"]

        resp = client.patch(
            f"/api/album/{album_id}/add/",
            content_type="application/json",
            data={"image_ids": [img.pk for img in Image.objects.all()]},
        )
        assert resp.status_code == HTTPStatus.OK

        resp = client.patch(
            f"/api/album/{album_id}/remove/",
            content_type="application/json",
            data={"image_ids": []},
        )

        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

        resp = client.patch(
            f"/api/album/{album_id}/add/",
            content_type="application/json",
            data={"image_ids": []},
        )

        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.usefixtures("sample_image_database")
@pytest.mark.django_db
class TestApiAlbumSorting:
    def test_update_sorting_reversed(
        self,
        client: Client,
        faker: Faker,
        album_api_create_factory,
    ):
        album_name = faker.unique.name()
        resp = album_api_create_factory(album_name)

        assert resp.status_code == HTTPStatus.CREATED
        album_id = resp.json()["id"]

        resp = client.patch(
            f"/api/album/{album_id}/add/",
            content_type="application/json",
            data={"image_ids": [img.pk for img in Image.objects.all()]},
        )
        assert resp.status_code == HTTPStatus.OK

        resp = client.get(f"/api/album/{album_id}/")
        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["name"] == album_name
        assert data["description"] is None
        assert data["id"] == album_id
        assert data["image_ids"] == [img.pk for img in Image.objects.order_by("pk").all()]

        resp = client.patch(
            f"/api/album/{album_id}/sort/",
            content_type="application/json",
            data={"sorting": [img.pk for img in Image.objects.order_by("pk").all().reverse()]},
        )

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["name"] == album_name
        assert data["description"] is None
        assert data["id"] == album_id
        assert data["image_ids"] == [img.pk for img in Image.objects.order_by("pk").all().reverse()]

    def test_custom_sorting(self, client: Client, faker: Faker, album_api_create_factory):
        album_name = faker.unique.name()
        resp = album_api_create_factory(album_name)

        assert resp.status_code == HTTPStatus.CREATED
        album_id = resp.json()["id"]

        resp = client.patch(
            f"/api/album/{album_id}/add/",
            content_type="application/json",
            data={"image_ids": [img.pk for img in Image.objects.all()]},
        )
        assert resp.status_code == HTTPStatus.OK

        pk_list = [img.pk for img in Image.objects.order_by("pk").all()]

        for permutation in itertools.permutations(pk_list):
            resp = client.patch(
                f"/api/album/{album_id}/sort/",
                content_type="application/json",
                data={
                    "sorting": permutation,
                },
            )

            assert resp.status_code == HTTPStatus.OK
            data = resp.json()
            assert data["name"] == album_name
            assert data["description"] is None
            assert data["id"] == album_id
            assert data["image_ids"] == list(permutation)

    def test_sorting_invalid_length(
        self,
        client: Client,
        faker: Faker,
        album_api_create_factory,
    ):
        album_name = faker.unique.name()
        resp = album_api_create_factory(album_name)

        assert resp.status_code == HTTPStatus.CREATED
        album_id = resp.json()["id"]

        resp = client.patch(
            f"/api/album/{album_id}/add/",
            content_type="application/json",
            data={"image_ids": [img.pk for img in Image.objects.all()]},
        )
        assert resp.status_code == HTTPStatus.OK

        resp = client.patch(
            f"/api/album/{album_id}/sort/",
            content_type="application/json",
            data={"sorting": [Image.objects.all().last().pk, Image.objects.all().first().pk]},
        )

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    def test_update_sorting_with_no_sorting_defined(
        self,
        client: Client,
        faker: Faker,
        album_api_create_factory,
    ):
        album_name = faker.unique.name()
        resp = album_api_create_factory(album_name)

        assert resp.status_code == HTTPStatus.CREATED
        album_id = resp.json()["id"]

        resp = client.patch(
            f"/api/album/{album_id}/add/",
            content_type="application/json",
            data={"image_ids": [img.pk for img in Image.objects.all()]},
        )
        assert resp.status_code == HTTPStatus.OK

        resp = client.patch(
            f"/api/album/{album_id}/sort/",
            content_type="application/json",
            data={
                "sorting": [],
            },
        )

        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.usefixtures("sample_image_environment")
@pytest.mark.django_db
class TestApiAlbumDownload:
    def download_test_common(
        self,
        client: Client,
        faker: Faker,
        tmp_path: Path,
        album_api_create_factory,
        *,
        use_original_download=False,
    ):
        album_name = faker.unique.name()
        resp = album_api_create_factory(album_name)

        assert resp.status_code == HTTPStatus.CREATED
        album_id = resp.json()["id"]

        resp = client.patch(
            f"/api/album/{album_id}/add/",
            content_type="application/json",
            data={"image_ids": [image.pk for image in Image.objects.all()]},
        )
        assert resp.status_code == HTTPStatus.OK

        # Download album
        if not use_original_download:
            resp = client.get(f"/api/album/{album_id}/download/")
        else:
            resp = client.get(f"/api/album/{album_id}/download/?zip_originals=True")
        assert resp.status_code == HTTPStatus.OK

        zipped_album = tmp_path / "test.zip"
        zipped_album.write_bytes(b"".join(resp.streaming_content))

        with zipfile.ZipFile(zipped_album) as downloaded_zip:
            info = downloaded_zip.infolist()
            assert len(info) == 4
            for index, image in enumerate(
                Album.objects.get(id=album_id).images.order_by("imageinalbum__sort_order").all(),
            ):
                if not use_original_download:
                    arcname = f"{index + 1:010}{image.full_size_path.suffix}"
                else:
                    arcname = f"{index + 1:010}{image.original_path.suffix}"
                try:
                    downloaded_zip.getinfo(arcname)
                except KeyError:
                    pytest.fail(f"{arcname} not present in zipfile")

    def test_album_download_full_size(
        self,
        client: Client,
        faker: Faker,
        tmp_path: Path,
        album_api_create_factory,
    ):
        self.download_test_common(client, faker, tmp_path, album_api_create_factory, use_original_download=False)

    def test_album_download_original(
        self,
        client: Client,
        faker: Faker,
        tmp_path: Path,
        album_api_create_factory,
    ):
        self.download_test_common(client, faker, tmp_path, album_api_create_factory, use_original_download=True)

    def test_album_no_images(self, client: Client, faker: Faker, album_api_create_factory):
        album_name = faker.unique.name()
        resp = album_api_create_factory(album_name)

        assert resp.status_code == HTTPStatus.CREATED
        album_id = resp.json()["id"]

        resp = client.get(f"/api/album/{album_id}/download/")

        assert resp.status_code == HTTPStatus.BAD_REQUEST
