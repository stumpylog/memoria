from http import HTTPStatus

import pytest
from django.test.client import Client
from faker import Faker

from memoria.models import Tag
from memoria.tests.api.types import ChildTagGeneratorProtocol
from memoria.tests.api.types import TagGeneratorProtocol


@pytest.mark.django_db
class TestApiTagRead:
    def test_get_single_tag_not_found(self, client: Client):
        resp = client.get("/api/tag/1/")

        assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_get_single_tag(self, client: Client, root_tag_db_factory: TagGeneratorProtocol):
        instance = Tag.objects.get(pk=root_tag_db_factory())

        resp = client.get(f"/api/tag/{instance.pk}/")

        assert resp.status_code == HTTPStatus.OK
        assert resp.json()["name"] == instance.name

    def test_list_tags(self, client: Client, root_tag_db_factory: TagGeneratorProtocol):
        count = 10
        for _ in range(count):
            root_tag_db_factory()

        resp = client.get("/api/tag/")

        assert resp.status_code == HTTPStatus.OK
        assert resp.json()["count"] == count
        assert len(resp.json()["items"]) == count

    def test_tag_paginate(self, client: Client, root_tag_db_factory: TagGeneratorProtocol):
        count = 110

        for _ in range(count):
            root_tag_db_factory()

        page = 1
        resp = client.get(f"/api/tag/?page={page}")

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["count"] == count
        assert len(data["items"]) == 50

        page = 2
        resp = client.get(f"/api/tag/?page={page}")

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["count"] == count
        assert len(data["items"]) == 50

        page = 3
        resp = client.get(f"/api/tag/?page={page}")

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["count"] == count
        assert len(data["items"]) == 10

    def test_tag_tree(
        self,
        client: Client,
        root_tag_db_factory: TagGeneratorProtocol,
        child_tag_db_factory: ChildTagGeneratorProtocol,
    ):
        root_count = 3
        child_count = 2
        for _ in range(root_count):
            root_tag_db_factory()

        for root in Tag.objects.filter(parent=None).all():
            for _ in range(child_count):
                child_tag_db_factory(root.pk)

        single_child = Tag.objects.exclude(parent=None).first()
        assert single_child is not None
        child_tag_db_factory(single_child.pk)

        resp = client.get("/api/tag/tree/")
        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        for root_item in data:
            assert "children" in root_item
            assert len(root_item["children"]) == child_count
            for child in root_item["children"]:
                assert "id" in child
                if child["id"] == single_child.pk:
                    assert len(child["children"]) == 1


@pytest.mark.django_db
class TestApiTagCreate:
    def test_create_tag_no_parent(self, client: Client, faker: Faker):
        tag_name = faker.country()
        resp = client.post(
            "/api/tag/",
            content_type="application/json",
            data={"name": tag_name},
        )

        assert resp.status_code == HTTPStatus.CREATED
        data = resp.json()

        assert data["name"] == tag_name
        assert "id" in data
        created_id = data["id"]

        instance = Tag.objects.get(id=created_id)
        assert instance.name == tag_name
        assert instance.description is None

    def test_create_tag_with_parent(self, client: Client, faker: Faker):
        parent = Tag.objects.create(name=faker.country())

        tag_name = faker.country()

        resp = client.post(
            "/api/tag/",
            content_type="application/json",
            data={"name": tag_name, "parent_id": parent.pk},
        )

        assert resp.status_code == HTTPStatus.CREATED
        data = resp.json()

        assert data["name"] == tag_name
        assert "id" in data
        assert "parent_id" in data
        assert data["parent_id"] == parent.pk
        created_id = data["id"]

        instance = Tag.objects.get(id=created_id)
        assert instance.name == tag_name
        assert instance.description is None
        assert instance.parent == parent

    def test_create_tag_exists(self, client: Client, faker: Faker):
        existing_name = faker.country()
        Tag.objects.create(name=existing_name)

        resp = client.post(
            "/api/tag/",
            content_type="application/json",
            data={"name": existing_name},
        )

        assert resp.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.django_db
class TestApiTagUpdate:
    def test_update_tag_name(self, client: Client, faker: Faker, root_tag_db_factory: TagGeneratorProtocol):
        instance: Tag = Tag.objects.get(pk=root_tag_db_factory())

        new_name = faker.unique.country()

        resp = client.patch(
            f"/api/tag/{instance.pk}/",
            content_type="application/json",
            data={"name": new_name},
        )

        assert resp.status_code == HTTPStatus.OK
        instance.refresh_from_db()
        assert instance.name == new_name

    def test_update_tag_parent(
        self,
        client: Client,
        root_tag_db_factory: TagGeneratorProtocol,
        child_tag_db_factory: ChildTagGeneratorProtocol,
    ):
        root_1: Tag = Tag.objects.get(pk=root_tag_db_factory())
        root_2: Tag = Tag.objects.get(pk=root_tag_db_factory())
        root_1: Tag = Tag.objects.get(pk=root_tag_db_factory())
        child_1: Tag = Tag.objects.get(pk=child_tag_db_factory(root_1.pk))
        child_2: Tag = Tag.objects.get(pk=child_tag_db_factory(root_2.pk))

        assert child_1.parent is not None
        assert child_1.parent.pk == root_1.pk

        resp = client.patch(
            f"/api/tag/{child_1.pk}/",
            content_type="application/json",
            data={"parent_id": child_2.pk},
        )
        assert resp.status_code == HTTPStatus.OK

        child_1.refresh_from_db()
        assert child_1.parent is not None
        assert child_1.parent.pk == child_2.pk

    def test_update_tag_add_description(self, client: Client, faker: Faker, root_tag_db_factory: TagGeneratorProtocol):
        root: Tag = Tag.objects.get(pk=root_tag_db_factory())

        assert root.description is None

        resp = client.patch(
            f"/api/tag/{root.pk}/",
            content_type="application/json",
            data={"description": faker.sentence()},
        )
        assert resp.status_code == HTTPStatus.OK

        root.refresh_from_db()
        assert root.description is not None


@pytest.mark.django_db
class TestApiTagDelete:
    def test_delete_single_tag(self, client: Client, root_tag_db_factory: TagGeneratorProtocol):
        root: Tag = Tag.objects.get(pk=root_tag_db_factory())
        resp = client.delete(
            f"/api/tag/{root.pk}/",
        )

        assert resp.status_code == HTTPStatus.NO_CONTENT

    def test_delete_single_tag_not_found(self, client: Client):
        resp = client.delete(
            "/api/tag/1/",
        )

        assert resp.status_code == HTTPStatus.NOT_FOUND
