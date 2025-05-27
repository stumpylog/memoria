from http import HTTPStatus
from random import choice

import pytest
from django.test.client import Client
from faker import Faker

from memoria.models import Person
from memoria.tests.api.types import PersonGeneratorProtocol


@pytest.mark.django_db
class TestApiPeopleRead:
    def test_get_people_with_no_people(self, client: Client):
        Person.objects.all().delete()
        resp = client.get(
            "/api/person/",
        )

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data["count"] == 0
        assert len(data["items"]) == 0

    def test_get_person_does_not_exist(self, client: Client):
        resp = client.get(
            "/api/person/1/",
        )

        assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_get_person_does_exist(self, client: Client, person_db_factory: PersonGeneratorProtocol):
        person_db_factory()
        resp = client.get(
            "/api/person/1/",
        )

        assert resp.status_code == HTTPStatus.OK
        instance = Person.objects.get(pk=1)
        data = resp.json()
        assert "id" in data
        assert data["id"] == instance.pk
        assert "name" in data
        assert data["name"] == instance.name

    def test_list_people(self, client: Client, person_db_factory: PersonGeneratorProtocol):
        count = 5
        for _ in range(count):
            person_db_factory()

        resp = client.get(
            "/api/person/",
        )

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data["count"] == count
        assert len(data["items"]) == count

    def test_list_people_limit_offset(self, client: Client, person_db_factory: PersonGeneratorProtocol):
        count = 5
        for _ in range(count):
            person_db_factory()

        page = 1
        resp = client.get(
            f"/api/person/?page={page}",
        )

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data["count"] == count
        assert len(data["items"]) == count

        page = 10
        resp = client.get(
            f"/api/person/?page={page}",
        )

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data["count"] == count
        assert len(data["items"]) == 0

    def test_list_people_name_like(self, client: Client, person_db_factory: PersonGeneratorProtocol):
        count = 5
        ids = []
        for _ in range(count):
            ids.append(person_db_factory())  # noqa: PERF401

        check_id = choice(ids)  # noqa: S311
        name = Person.objects.get(pk=check_id).name

        resp = client.get(
            "/api/person/",
            data={"name_like": name},
        )

        data = resp.json()

        assert data["count"] == 1
        assert data["items"][0]["name"] == name


@pytest.mark.django_db
class TestApiPeopleCreate:
    def test_create_person(self, client: Client, faker: Faker):
        person_name = faker.name()

        resp = client.post(
            "/api/person/",
            content_type="application/json",
            data={"name": person_name},
        )

        assert resp.status_code == HTTPStatus.CREATED
        data = resp.json()
        assert data["name"] == person_name
        assert "id" in data

        assert Person.objects.filter(id=data["id"]).exists()
        assert Person.objects.get(id=data["id"]).name == person_name

    def test_create_person_with_description(self, client: Client, faker: Faker):
        person_name = faker.name()
        description = faker.sentence()

        resp = client.post(
            "/api/person/",
            content_type="application/json",
            data={"name": person_name, "description": description},
        )

        assert resp.status_code == HTTPStatus.CREATED
        data = resp.json()
        assert data["name"] == person_name
        assert "id" in data

        assert Person.objects.filter(id=data["id"]).exists()
        assert Person.objects.get(id=data["id"]).name == person_name
        assert Person.objects.get(id=data["id"]).description == description

    def test_create_multiple_person(self, client: Client, faker: Faker):
        count = 5

        for _ in range(count):
            person_name = faker.name()
            resp = client.post(
                "/api/person/",
                content_type="application/json",
                data={"name": person_name},
            )

            assert resp.status_code == HTTPStatus.CREATED
            data = resp.json()
            assert data["name"] == person_name
            assert "id" in data

            assert Person.objects.filter(id=data["id"]).exists()
            assert Person.objects.get(id=data["id"]).name == person_name

        assert Person.objects.count() == count

    def test_create_person_existing_name(self, client: Client, faker: Faker):
        person_name = faker.name()
        resp = client.post(
            "/api/person/",
            content_type="application/json",
            data={"name": person_name},
        )

        assert resp.status_code == HTTPStatus.CREATED

        resp = client.post(
            "/api/person/",
            content_type="application/json",
            data={"name": person_name},
        )
        assert resp.status_code == HTTPStatus.CONFLICT
        assert Person.objects.count() == 1


@pytest.mark.django_db
class TestApiPeopleUpdate:
    def test_update_person_name(self, client: Client, faker: Faker, person_db_factory: PersonGeneratorProtocol):
        person_db_factory()

        instance = Person.objects.get(pk=1)
        assert instance is not None

        new_name = faker.name()

        resp = client.patch(
            f"/api/person/{instance.pk}/",
            content_type="application/json",
            data={"name": new_name},
        )

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["name"] == new_name
        assert "id" in data
        created_id = data["id"]
        assert Person.objects.filter(id=created_id).exists()
        assert Person.objects.get(id=created_id).name == new_name

    def test_update_person_description(self, client: Client, faker: Faker, person_db_factory: PersonGeneratorProtocol):
        instance = Person.objects.get(pk=person_db_factory())
        assert instance is not None

        new_desc = faker.sentence()

        resp = client.patch(
            f"/api/person/{instance.pk}/",
            content_type="application/json",
            data={"description": new_desc},
        )

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["name"] == instance.name
        assert data["description"] == new_desc

    def test_update_person_no_data(self, client: Client, person_db_factory: PersonGeneratorProtocol):
        instance = Person.objects.get(pk=person_db_factory())

        resp = client.patch(
            f"/api/person/{instance.pk}/",
            content_type="application/json",
            data={},
        )

        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.django_db
class TestApiPeopleDelete:
    def test_delete_person(self, client: Client, person_db_factory: PersonGeneratorProtocol):
        person_db_factory()

        instance = Person.objects.get(pk=1)
        assert instance is not None

        resp = client.delete(f"/api/person/{instance.pk}/")

        assert resp.status_code == HTTPStatus.NO_CONTENT
