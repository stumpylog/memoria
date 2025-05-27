from http import HTTPStatus

import pytest
from django.test.client import Client
from faker import Faker

from memoria.models import Pet
from memoria.tests.api.types import PetApiGeneratorProtocol
from memoria.tests.api.types import PetGeneratorProtocol


@pytest.mark.django_db
class TestApiPetsRead:
    def test_get_pets_with_no_pets(self, client: Client):
        resp = client.get(
            "/api/pet/",
        )

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data["count"] == 0
        assert len(data["items"]) == 0

    def test_get_pet_does_not_exist(self, client: Client):
        resp = client.get(
            "/api/pet/1/",
        )

        assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_get_pet_does_exist(self, client: Client, pet_db_factory: PetGeneratorProtocol):
        pet = Pet.objects.get(pk=pet_db_factory())

        resp = client.get(
            f"/api/pet/{pet.pk}/",
        )

        assert resp.status_code == HTTPStatus.OK
        assert resp.json() == {"id": pet.pk, "name": pet.name, "description": None}

    def test_list_pets(self, client: Client, pet_db_factory: PetGeneratorProtocol):
        count = 5
        for _ in range(count):
            pet_db_factory()

        resp = client.get(
            "/api/pet/",
        )

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data["count"] == count
        assert len(data["items"]) == count

    def test_list_pet_page(self, client: Client, pet_db_factory: PetGeneratorProtocol):
        count = 5
        for _ in range(count):
            pet_db_factory()

        page = 1
        resp = client.get(
            f"/api/pet/?page={page}",
        )

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data["count"] == count
        assert len(data["items"]) == count

        page = 10
        resp = client.get(
            f"/api/pet/?page={page}",
        )

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data["count"] == count
        assert len(data["items"]) == 0


@pytest.mark.django_db
class TestApiPetsCreate:
    def test_create_pet(self, faker: Faker, pet_api_create_factory: PetApiGeneratorProtocol):
        pet_name = faker.name()
        resp = pet_api_create_factory(pet_name)

        assert resp.status_code == HTTPStatus.CREATED
        data = resp.json()
        assert data["name"] == pet_name
        assert "id" in data

        assert Pet.objects.filter(id=data["id"]).exists()
        assert Pet.objects.get(id=data["id"]).name == pet_name

    def test_create_pet_with_description(self, faker: Faker, pet_api_create_factory: PetApiGeneratorProtocol):
        pet_name = faker.name()
        description = faker.sentence()
        resp = pet_api_create_factory(pet_name, description)

        assert resp.status_code == HTTPStatus.CREATED
        data = resp.json()
        assert data["name"] == pet_name
        assert "id" in data

        assert Pet.objects.filter(id=data["id"]).exists()
        assert Pet.objects.get(id=data["id"]).name == pet_name
        assert Pet.objects.get(id=data["id"]).description == description

    def test_create_multiple_pet(self, faker: Faker, pet_api_create_factory: PetApiGeneratorProtocol):
        count = 5

        for _ in range(count):
            pet_name = faker.name()
            resp = pet_api_create_factory(pet_name)

            assert resp.status_code == HTTPStatus.CREATED
            data = resp.json()
            assert data["name"] == pet_name
            assert "id" in data

            assert Pet.objects.filter(id=data["id"]).exists()
            assert Pet.objects.get(id=data["id"]).name == pet_name

        assert Pet.objects.count() == count

    def test_create_pet_existing_name(self, faker: Faker, pet_api_create_factory: PetApiGeneratorProtocol):
        pet_name = faker.name()
        resp = pet_api_create_factory(pet_name)

        assert resp.status_code == HTTPStatus.CREATED

        resp = pet_api_create_factory(pet_name)
        assert resp.status_code == HTTPStatus.CONFLICT
        assert Pet.objects.count() == 1


@pytest.mark.django_db
class TestApiPetsUpdate:
    def test_update_pet_name(self, client: Client, faker: Faker, pet_db_factory: PetGeneratorProtocol):
        instance: Pet = Pet.objects.get(pk=pet_db_factory())

        new_name = faker.name()

        resp = client.patch(
            f"/api/pet/{instance.pk}/",
            content_type="application/json",
            data={"name": new_name},
        )

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["name"] == new_name
        assert "id" in data
        created_id = data["id"]
        assert Pet.objects.filter(id=created_id).exists()
        assert Pet.objects.get(id=created_id).name == new_name

    def test_update_pet_description(
        self,
        faker: Faker,
        client: Client,
        pet_db_factory: PetGeneratorProtocol,
    ):
        instance: Pet = Pet.objects.get(pk=pet_db_factory())

        new_desc = faker.sentence()

        resp = client.patch(
            f"/api/pet/{instance.pk}/",
            content_type="application/json",
            data={"description": new_desc},
        )

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["name"] == instance.name
        assert data["description"] == new_desc

    def test_update_pet_no_data(self, client: Client, pet_db_factory: PetGeneratorProtocol):
        instance: Pet = Pet.objects.get(pk=pet_db_factory())

        resp = client.patch(
            f"/api/pet/{instance.pk}/",
            content_type="application/json",
            data={},
        )

        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.django_db
class TestApiPetsDelete:
    def test_delete_pet(self, client: Client, pet_db_factory: PetGeneratorProtocol):
        instance: Pet = Pet.objects.get(pk=pet_db_factory())

        resp = client.delete(f"/api/pet/{instance.pk}/")

        assert resp.status_code == HTTPStatus.NO_CONTENT
