from http import HTTPStatus

import pytest
from django.test.client import Client

from memoria.models import RoughLocation
from memoria.tests.api.types import LocationGeneratorProtocol


@pytest.mark.django_db
class TestCreateLocation:
    def test_location_create_country_only(self, client: Client):
        resp = client.post(
            "/api/location/",
            content_type="application/json",
            data={"country_code": "US"},
        )

        assert resp.status_code == HTTPStatus.CREATED
        data = resp.json()

        assert RoughLocation.objects.count() == 1
        assert RoughLocation.objects.get(pk=data["id"]).country_code == "US"

    def test_location_create_country_and_state(self, client: Client):
        resp = client.post(
            "/api/location/",
            content_type="application/json",
            data={"country_code": "US", "subdivision_code": "US-CA"},
        )

        assert resp.status_code == HTTPStatus.CREATED
        data = resp.json()
        assert RoughLocation.objects.count() == 1
        assert RoughLocation.objects.get(pk=data["id"]).country_code == "US"
        assert RoughLocation.objects.get(pk=data["id"]).subdivision_code == "US-CA"

    def test_location_create_country_and_state_and_city(self, client: Client):
        resp = client.post(
            "/api/location/",
            content_type="application/json",
            data={
                "country_code": "US",
                "subdivision_code": "US-CA",
                "city": "San Francisco",
            },
        )

        assert resp.status_code == HTTPStatus.CREATED
        data = resp.json()
        assert RoughLocation.objects.count() == 1
        assert RoughLocation.objects.get(pk=data["id"]).country_code == "US"
        assert RoughLocation.objects.get(pk=data["id"]).subdivision_code == "US-CA"
        assert RoughLocation.objects.get(pk=data["id"]).city == "San Francisco"

    def test_location_create_country_and_state_and_city_and_sublocation(self, client: Client):
        resp = client.post(
            "/api/location/",
            content_type="application/json",
            data={
                "country_code": "US",
                "subdivision_code": "US-CA",
                "city": "San Francisco",
                "sub_location": "Fisherman's Wharf",
            },
        )

        assert resp.status_code == HTTPStatus.CREATED
        data = resp.json()
        assert RoughLocation.objects.count() == 1
        assert RoughLocation.objects.get(pk=data["id"]).country_code == "US"
        assert RoughLocation.objects.get(pk=data["id"]).subdivision_code == "US-CA"
        assert RoughLocation.objects.get(pk=data["id"]).city == "San Francisco"
        assert RoughLocation.objects.get(pk=data["id"]).sub_location == "Fisherman's Wharf"

    def test_location_create_country_and_state_invalid(self, client: Client):
        resp = client.post(
            "/api/location/",
            content_type="application/json",
            data={"country_code": "US", "subdivision_code": "DE-HM"},
        )

        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert RoughLocation.objects.count() == 0

    def test_location_create_invalid_country(self, client: Client):
        resp = client.post(
            "/api/location/",
            content_type="application/json",
            data={"country_code": "XX"},
        )

        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert RoughLocation.objects.count() == 0

    def test_location_already_exists(self, client: Client):
        resp = client.post(
            "/api/location/",
            content_type="application/json",
            data={"country_code": "US", "subdivision_code": "US-CA"},
        )
        assert resp.status_code == HTTPStatus.CREATED

        resp = client.post(
            "/api/location/",
            content_type="application/json",
            data={"country_code": "US", "subdivision_code": "US-CA"},
        )
        assert resp.status_code == HTTPStatus.CONFLICT


@pytest.mark.django_db
class TestReadLocation:
    def test_read_single_location(self, client: Client, location_db_factory: LocationGeneratorProtocol):
        id_ = location_db_factory(
            "US",
            "US-CA",
            "San Francisco",
            "Golden Gate Bridge",
        )

        resp = client.get(f"/api/location/{id_}/")

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data["id"] == id_
        assert data["country_code"] == "US"
        assert data["subdivision_code"] == "US-CA"
        assert data["city"] == "San Francisco"
        assert data["sub_location"] == "Golden Gate Bridge"

    def test_read_single_location_not_found(self, client: Client):
        resp = client.get("/api/location/5/")

        assert resp.status_code == HTTPStatus.NOT_FOUND

    def test_read_all_locations(self, client: Client, location_db_factory: LocationGeneratorProtocol):
        id1 = location_db_factory(
            "US",
            "US-CA",
            "San Francisco",
            "Golden Gate Bridge",
        )
        id2 = location_db_factory(
            "US",
            "US-CA",
            "Los Angeles",
            "Grand Central Market",
        )

        resp = client.get("/api/location/")

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert len(data) == 2
        # Checks ordering as well
        assert data["items"][1]["id"] == id1
        assert data["items"][0]["id"] == id2

    def test_read_locations_filtered(self, client: Client, location_db_factory: LocationGeneratorProtocol):
        id1 = location_db_factory(
            "US",
            "US-CA",
            "San Francisco",
            "Golden Gate Bridge",
        )
        id2 = location_db_factory(
            "US",
            "US-CA",
            "Los Angeles",
            "Grand Central Market",
        )

        resp = client.get("/api/location/", data={"country_code": "US"})

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data["count"] == 2
        # Checks ordering as well
        assert data["items"][1]["id"] == id1
        assert data["items"][0]["id"] == id2

        # TODO: Parameterize this or split it

        resp = client.get("/api/location/", data={"subdivision_code": "US-CA"})

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data["count"] == 2
        assert data["items"][1]["id"] == id1
        assert data["items"][0]["id"] == id2

        resp = client.get("/api/location/", data={"city": "US-CA"})

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data["count"] == 2
        assert data["items"][1]["id"] == id1
        assert data["items"][0]["id"] == id2

        resp = client.get("/api/location/", data={"city_like": "San Fran"})

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data["count"] == 1
        assert data["items"][0]["id"] == id1

        resp = client.get("/api/location/", data={"shown_location_like": "grand"})

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data["count"] == 1
        assert data["items"][0]["id"] == id2


@pytest.mark.django_db
class TestUpdateLocation:
    def test_update_city(self, client: Client, location_db_factory: LocationGeneratorProtocol):
        id_ = location_db_factory(
            "US",
            "US-CA",
            "San Francisco",
            "Golden Gate Bridge",
        )

        resp = client.patch(
            f"/api/location/{id_}/",
            content_type="application/json",
            data={"city": "New York"},
        )

        assert resp.status_code == HTTPStatus.OK
        assert RoughLocation.objects.get(pk=id_).city == "New York"

    def test_update_subdivision_code_with_no_country(
        self,
        client: Client,
        location_db_factory: LocationGeneratorProtocol,
    ):
        id_ = location_db_factory(
            "US",
            "US-CA",
            "San Francisco",
            "Golden Gate Bridge",
        )

        resp = client.patch(
            f"/api/location/{id_}/",
            content_type="application/json",
            data={"subdivision_code": "US-NY"},
        )

        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        data = resp.json()
        assert "Subdivision must also include country code" in data["detail"][0]["msg"]
        assert RoughLocation.objects.get(pk=id_).subdivision_code == "US-CA"

    def test_update_subdivision_code_with_wrong_country(
        self,
        client: Client,
        location_db_factory: LocationGeneratorProtocol,
    ):
        id_ = location_db_factory(
            "US",
            "US-CA",
            "San Francisco",
            "Golden Gate Bridge",
        )

        resp = client.patch(
            f"/api/location/{id_}/",
            content_type="application/json",
            data={"country_code": "US", "subdivision_code": "AM-AG"},
        )

        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        data = resp.json()
        error = data["detail"][0]
        context = error["ctx"]
        assert "AM-AG is not a valid subdivision of US" in context["error"]
        assert RoughLocation.objects.get(pk=id_).subdivision_code == "US-CA"

    def test_update_no_data(self, client: Client, location_db_factory: LocationGeneratorProtocol):
        id_ = location_db_factory(
            "US",
            "US-CA",
            "San Francisco",
            "Golden Gate Bridge",
        )
        resp = client.patch(
            f"/api/location/{id_}/",
            content_type="application/json",
            data={},
        )

        assert resp.status_code == HTTPStatus.BAD_REQUEST

    def test_update_country_and_subdivision(self, client: Client, location_db_factory: LocationGeneratorProtocol):
        id_ = location_db_factory(
            "US",
            "US-CA",
            "San Francisco",
            "Golden Gate Bridge",
        )
        resp = client.patch(
            f"/api/location/{id_}/",
            content_type="application/json",
            data={"country_code": "FR", "subdivision_code": "FR-IDF"},
        )

        assert resp.status_code == HTTPStatus.OK
        assert RoughLocation.objects.get(pk=id_).country_code == "FR"
        assert RoughLocation.objects.get(pk=id_).subdivision_code == "FR-IDF"


@pytest.mark.django_db
class TestDeleteLocation:
    def test_delete_location(self, client: Client, location_db_factory: LocationGeneratorProtocol):
        id_ = location_db_factory(
            "US",
            "US-CA",
            "San Francisco",
            "Golden Gate Bridge",
        )
        resp = client.delete(f"/api/location/{id_}/")

        assert resp.status_code == HTTPStatus.NO_CONTENT
        assert RoughLocation.objects.filter(pk=id_).exists() is False

    def test_delete_location_not_found(self, client: Client, location_db_factory: LocationGeneratorProtocol):
        id_ = location_db_factory(
            "US",
            "US-CA",
            "San Francisco",
            "Golden Gate Bridge",
        )
        resp = client.delete(f"/api/location/{id_ + 1}/")
        assert resp.status_code == HTTPStatus.NOT_FOUND
