import datetime
from http import HTTPStatus

import pytest
from django.test.client import Client
from django.utils import timezone

from memoria.imageops.models import RotationEnum
from memoria.models import Album
from memoria.models import Image
from memoria.models import ImageInAlbum
from memoria.models import Person
from memoria.models import PersonInImage
from memoria.models import Pet
from memoria.models import PetInImage
from memoria.models import RoughDate
from memoria.models import RoughLocation
from memoria.tests.mixins import FileSystemAssertsMixin


@pytest.mark.usefixtures("sample_image_environment")
@pytest.mark.django_db
class TestImageFileReads(FileSystemAssertsMixin):
    def test_image_generated_files_match(self, client: Client):
        img = Image.objects.first()
        assert img is not None

        # Thumbnail
        assert img.thumbnail_path.exists()
        assert img.thumbnail_path.is_file()

        resp = client.get(f"/api/image/{img.pk}/thumbnail/")

        assert resp.status_code == HTTPStatus.OK
        assert resp["ETag"] == f'"{img.thumbnail_checksum}"'
        assert resp["Last-Modified"] == img.modified.strftime("%a, %d %b %Y %H:%M:%S GMT")

        thumbnail_data = b"".join(resp.streaming_content)

        self.assertFileContents(img.thumbnail_path, thumbnail_data)

        # Fullsize, WebP
        assert img.full_size_path.exists()
        assert img.full_size_path.is_file()

        resp = client.get(f"/api/image/{img.pk}/full/")

        assert resp.status_code == HTTPStatus.OK
        assert resp["ETag"] == f'"{img.full_size_checksum}"'
        assert resp["Last-Modified"] == img.modified.strftime("%a, %d %b %Y %H:%M:%S GMT")

        full_size_data = b"".join(resp.streaming_content)

        self.assertFileContents(img.full_size_path, full_size_data)

        # Original
        assert img.original_path.exists()
        assert img.original_path.is_file()

        resp = client.get(f"/api/image/{img.pk}/original/")

        assert resp.status_code == HTTPStatus.OK
        assert resp["Content-Type"] == "image/jpeg"
        assert resp["ETag"] == f'"{img.original_checksum}"'
        assert resp["Content-Length"] == str(img.file_size)
        assert resp["Last-Modified"] == img.modified.strftime("%a, %d %b %Y %H:%M:%S GMT")

        original_data = b"".join(resp.streaming_content)

        self.assertFileContents(img.original_path, original_data)


@pytest.mark.usefixtures("sample_image_environment")
@pytest.mark.django_db
class TestImageReadApi:
    def test_get_image_faces(self, client: Client):
        img = Image.objects.last()
        assert img is not None

        resp = client.get(f"/api/image/{img.pk}/faces/")
        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data == [
            {
                "box": {
                    "center_x": 0.466361,
                    "center_y": 0.186927,
                    "height": 0.0940367,
                    "width": 0.0428135,
                },
                "person_id": 1,
            },
        ]

    def test_get_image_pets(self, client: Client):
        img = Image.objects.first()
        assert img is not None

        resp = client.get(f"/api/image/{img.pk}/pets/")
        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data == [
            {
                "pet_id": 1,
                "box": {
                    "center_x": 0.616699,
                    "center_y": 0.768668,
                    "height": 0.284041,
                    "width": 0.202148,
                },
            },
        ]

    def test_get_image_metadata(self, client: Client):
        img = Image.objects.first()
        assert img is not None

        resp = client.get(f"/api/image/{img.pk}/metadata/")
        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data == {
            "date_id": 1,
            "description": (
                "President Barack Obama throws a ball for Bo, the family dog, "
                "in the Rose Garden of the White House, Sept. 9, 2010.  "
                "(Official White House Photo by Pete Souza)"
            ),
            "location_id": 1,
            "orientation": RotationEnum.HORIZONTAL,
        }

    def test_get_image_tags(self, client: Client):
        img = Image.objects.first()
        assert img is not None

        resp = client.get(f"/api/image/{img.pk}/tags/")
        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data == [3]

    def test_get_image_albums(self, client: Client):
        img = Image.objects.first()
        assert img is not None

        resp = client.get(f"/api/image/{img.pk}/albums/")
        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data == []

        instance = Album.objects.create(
            name="test name",
            description="test desc",
        )

        ImageInAlbum.objects.get_or_create(
            album=instance,
            image=img,
            sort_order=1,
        )

        resp = client.get(f"/api/image/{img.pk}/albums/")
        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data == [instance.pk]


@pytest.mark.usefixtures("sample_image_environment")
@pytest.mark.django_db
class TestImageReadWithFiltersApi:
    def test_get_images_filter_includes_person(self, client: Client):
        """
        Test getting all images with include a particular person
        """
        person = Person.objects.get(pk=3)
        assert person is not None
        assert person.name == "Hillary Clinton"

        resp = client.get("/api/image/", data={"includes_people": [person.pk]})
        assert resp.status_code == HTTPStatus.OK

        assert resp.json() == {"count": 1, "items": [3]}

    def test_get_images_filter_includes_people(self, client: Client):
        """
        Test getting all images with include all people
        """
        barak = Person.objects.get(pk=1)
        assert barak is not None
        assert barak.name == "Barack Obama"

        hrc = Person.objects.get(pk=3)
        assert hrc is not None
        assert hrc.name == "Hillary Clinton"

        resp = client.get("/api/image/", data={"includes_people": [barak.pk, hrc.pk]})
        assert resp.status_code == HTTPStatus.OK

        assert resp.json() == {"count": 1, "items": [3]}

    def test_get_images_filter_include_and_exclude_people(self, client: Client):
        """
        Test getting all images with include and exclude people
        """
        includes_person = Person.objects.get(pk=1)
        excludes_person = Person.objects.get(pk=3)
        assert includes_person is not None
        assert includes_person.name == "Barack Obama"

        assert excludes_person is not None
        assert excludes_person.name == "Hillary Clinton"

        resp = client.get(
            "/api/image/",
            data={"includes_people": [includes_person.pk], "excludes_people": [excludes_person.pk]},
        )
        assert resp.status_code == HTTPStatus.OK

        assert resp.json() == {"count": 3, "items": [1, 2, 4]}

    def test_get_images_filter_include_person_include_pet(self, client: Client):
        """
        Test getting all images with include person and include pet
        """
        includes_person = Person.objects.get(pk=1)
        assert includes_person is not None
        assert includes_person.name == "Barack Obama"

        include_pet = Pet.objects.get(pk=1)
        assert include_pet is not None
        assert include_pet.name == "Bo"

        resp = client.get(
            "/api/image/",
            data={"includes_people": [includes_person.pk], "includes_pets": [include_pet.pk]},
        )
        assert resp.status_code == HTTPStatus.OK

        # TODO: Image 4 does not include the pet box, that should be fixed
        assert resp.json() == {"count": 1, "items": [1]}

    def test_get_images_filter_include_person_exclude_pet(self, client: Client):
        """
        Test getting all images with include person and exclude pet
        """
        includes_person = Person.objects.get(pk=1)
        assert includes_person is not None
        assert includes_person.name == "Barack Obama"

        exclude_pet = Pet.objects.get(pk=1)
        assert exclude_pet is not None
        assert exclude_pet.name == "Bo"

        resp = client.get(
            "/api/image/",
            data={"includes_people": [includes_person.pk], "excludes_pets": [exclude_pet.pk]},
        )
        assert resp.status_code == HTTPStatus.OK

        # TODO: Image 4 does not include the pet box, that should be fixed and 4 removed
        assert resp.json() == {"count": 3, "items": [2, 3, 4]}

    def test_get_images_filter_include_location(self, client: Client):
        """
        Test getting all images with include location
        """
        include_location = RoughLocation.objects.get(pk=1)

        assert include_location is not None

        resp = client.get(
            "/api/image/",
            data={"includes_locations": [include_location.pk]},
        )
        assert resp.status_code == HTTPStatus.OK

        assert resp.json() == {"count": 3, "items": [1, 2, 3]}

    def test_get_images_filter_include_and_exclude_location(self, client: Client):
        """
        Test getting all images with include location and exclude location
        """
        include_location = RoughLocation.objects.get(pk=1)
        exclude_location = RoughLocation.objects.get(pk=2)

        assert include_location is not None

        resp = client.get(
            "/api/image/",
            data={"includes_locations": [include_location.pk], "excludes_locations": [exclude_location.pk]},
        )
        assert resp.status_code == HTTPStatus.OK

        assert resp.json() == {"count": 3, "items": [1, 2, 3]}


@pytest.mark.usefixtures("sample_image_environment")
@pytest.mark.django_db
class TestImageUpdateApi:
    def test_update_face_bounding_box(self, client: Client):
        image = Image.objects.last()
        assert image is not None
        person = image.people.first()
        assert person is not None

        resp = client.patch(
            f"/api/image/{image.pk}/faces/",
            content_type="application/json",
            data=[
                {
                    "person_id": person.pk,
                    "box": {"center_x": 0.5, "center_y": 0.3, "height": 0.1, "width": 0.9},
                },
            ],
        )
        assert resp.status_code == HTTPStatus.OK

        new_box = PersonInImage.objects.get(image=image, person=person)
        assert new_box is not None
        assert new_box.center_x == 0.5
        assert new_box.center_y == 0.3
        assert new_box.height == 0.1
        assert new_box.width == 0.9

    def test_update_pet_bounding_box(self, client: Client):
        image = Image.objects.first()
        assert image is not None
        pet = image.pets.first()
        assert pet is not None

        resp = client.patch(
            f"/api/image/{image.pk}/pets/",
            content_type="application/json",
            data=[
                {
                    "pet_id": pet.pk,
                    "box": {"center_x": 0.5, "center_y": 0.3, "height": 0.1, "width": 0.9},
                },
            ],
        )
        assert resp.status_code == HTTPStatus.OK

        new_box = PetInImage.objects.get(image=image, pet=pet)
        assert new_box is not None
        assert new_box.center_x == 0.5
        assert new_box.center_y == 0.3
        assert new_box.height == 0.1
        assert new_box.width == 0.9

    def test_update_image_metadata(self, client: Client, date_today_utc: datetime.date):
        image = Image.objects.last()
        assert image is not None

        new_loc = RoughLocation.objects.create(country_code="US")
        new_date = RoughDate.objects.create(date=date_today_utc)

        resp = client.get(f"/api/image/{image.pk}/metadata/")
        assert resp.status_code == HTTPStatus.OK

        existing = resp.json()
        existing["orientation"] = RotationEnum.MIRROR_HORIZONTAL
        existing["description"] = "New Desc"
        existing["location_id"] = new_loc.pk
        existing["date_id"] = new_date.pk

        resp = client.patch(f"/api/image/{image.pk}/metadata/", content_type="application/json", data=existing)
        assert resp.status_code == HTTPStatus.OK

    def test_update_image_tags(self, client: Client):
        image = Image.objects.first()
        assert image is not None

        resp = client.patch(f"/api/image/{image.pk}/tags/", content_type="application/json", data=[1, 2])
        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data == [1, 2]

        resp = client.patch(f"/api/image/{image.pk}/tags/", content_type="application/json", data=[2, 3])
        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data == [2, 3]


@pytest.mark.usefixtures("sample_image_environment")
@pytest.mark.django_db
class TestImageDeleteApi:
    def test_delete_face_from_image(self, client: Client):
        image = Image.objects.first()
        assert image is not None
        person = image.people.first()
        assert person is not None

        initial_people_count = Person.objects.count()
        initial_pet_count = Pet.objects.count()
        initial_box_count = PersonInImage.objects.count()
        initial_people_in_img_count = image.people.count()
        initial_pet_in_img_count = image.pets.count()

        resp = client.delete(
            f"/api/image/{image.pk}/faces/",
            content_type="application/json",
            data={"people_ids": [person.pk]},
        )
        assert resp.status_code == HTTPStatus.OK

        image.refresh_from_db()

        assert image.people.count() == (initial_people_in_img_count - 1)
        assert image.pets.count() == initial_pet_in_img_count
        assert PersonInImage.objects.count() == (initial_box_count - 1)
        assert Pet.objects.count() == initial_pet_count
        assert Person.objects.count() == initial_people_count

    def test_delete_face_from_image_not_in_image(self, client: Client):
        image = Image.objects.last()
        assert image is not None
        person = image.people.first()
        assert person is not None

        initial_people_count = Person.objects.count()
        initial_pet_count = Pet.objects.count()
        initial_pet_box_count = PetInImage.objects.count()
        initial_person_box_count = PersonInImage.objects.count()
        initial_people_in_img_count = image.people.count()
        initial_pet_in_img_count = image.pets.count()

        resp = client.delete(
            f"/api/image/{image.pk}/faces/",
            content_type="application/json",
            data={"people_ids": [person.pk + 5]},
        )
        assert resp.status_code == HTTPStatus.OK

        image.refresh_from_db()

        assert image.people.count() == initial_people_in_img_count
        assert image.pets.count() == initial_pet_in_img_count
        assert PersonInImage.objects.count() == initial_person_box_count
        assert PetInImage.objects.count() == initial_pet_box_count
        assert Pet.objects.count() == initial_pet_count
        assert Person.objects.count() == initial_people_count

    def test_delete_pet_from_image(self, client: Client):
        image = Image.objects.first()
        assert image is not None
        pet = image.pets.first()
        assert pet is not None

        initial_people_count = Person.objects.count()
        initial_pet_count = Pet.objects.count()
        initial_pet_box_count = PetInImage.objects.count()
        initial_person_box_count = PersonInImage.objects.count()
        initial_people_in_img_count = image.people.count()
        initial_pet_in_img_count = image.pets.count()

        resp = client.delete(
            f"/api/image/{image.pk}/pets/",
            content_type="application/json",
            data={"pet_ids": [pet.pk]},
        )
        assert resp.status_code == HTTPStatus.OK

        image.refresh_from_db()

        assert image.people.count() == initial_people_in_img_count
        assert image.pets.count() == (initial_pet_in_img_count - 1)
        assert PersonInImage.objects.count() == initial_person_box_count
        assert PetInImage.objects.count() == (initial_pet_box_count - 1)
        assert Pet.objects.count() == initial_pet_count
        assert Person.objects.count() == initial_people_count

    def test_delete_pet_from_image_not_in(self, client: Client):
        image = Image.objects.first()
        assert image is not None
        pet = image.pets.first()
        assert pet is not None

        initial_people_count = Person.objects.count()
        initial_pet_count = Pet.objects.count()
        initial_pet_box_count = PetInImage.objects.count()
        initial_person_box_count = PersonInImage.objects.count()
        initial_people_in_img_count = image.people.count()
        initial_pet_in_img_count = image.pets.count()

        resp = client.delete(
            f"/api/image/{image.pk}/pets/",
            content_type="application/json",
            data={"pet_ids": [pet.pk + 1]},
        )
        assert resp.status_code == HTTPStatus.OK

        image.refresh_from_db()

        assert image.people.count() == initial_people_in_img_count
        assert image.pets.count() == initial_pet_in_img_count
        assert PersonInImage.objects.count() == initial_person_box_count
        assert PetInImage.objects.count() == initial_pet_box_count
        assert Pet.objects.count() == initial_pet_count
        assert Person.objects.count() == initial_people_count

    def test_image_restore_but_not_deleted(self, client: Client):
        image = Image.objects.first()
        assert image is not None

        resp = client.patch(f"/api/image/{image.pk}/restore/")
        assert resp.status_code == HTTPStatus.CONFLICT

        image.refresh_from_db()

        assert image.deleted_at is None

    def test_image_delete_and_restore(self, client: Client):
        image = Image.objects.last()
        assert image is not None

        resp = client.delete(f"/api/image/{image.pk}/delete/")
        assert resp.status_code == HTTPStatus.NO_CONTENT

        image.refresh_from_db()

        assert image.deleted_at is not None
        assert image.deleted_at.timestamp() == pytest.approx(
            timezone.now().timestamp(),
            rel=datetime.timedelta(seconds=1).total_seconds(),
        )

        resp = client.patch(f"/api/image/{image.pk}/restore/")

        image.refresh_from_db()
        assert image.deleted_at is None
