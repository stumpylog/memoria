from http import HTTPStatus

import pytest
from django.contrib.auth.models import User
from django.test.client import Client
from django.utils import timezone

from memoria.models import Token


@pytest.mark.django_db
class TestApiTokenCreate:
    def test_api_token_create_no_expire(self, client: Client):
        instance = User.objects.create_user(username="testuser", email="test@example.com")
        client.force_login(instance)

        resp = client.post(
            "/api/auth/token/create/",
            content_type="application/json",
            data={"name": "test token"},
        )

        assert resp.status_code == HTTPStatus.CREATED

        assert Token.objects.count() == 1
        token = Token.objects.first()
        assert token is not None
        assert token.name == "test token"
        assert token.expires_at is None

    def test_api_token_create_with_expire(self, client: Client):
        instance = User.objects.create_user(username="testuser", email="test@example.com")
        client.force_login(instance)

        resp = client.post(
            "/api/auth/token/create/",
            content_type="application/json",
            data={"name": "test token", "expires_in_days": 10},
        )

        assert resp.status_code == HTTPStatus.CREATED

        assert Token.objects.count() == 1
        token = Token.objects.first()
        assert token is not None
        assert token.name == "test token"
        assert token.expires_at is not None
        assert token.expires_at.date() == timezone.now().date() + timezone.timedelta(days=10)


@pytest.mark.django_db
class TestApiTokenRead:
    def test_list_no_auth(self, client: Client):
        resp = client.get("/api/auth/token/")

        assert resp.status_code == HTTPStatus.UNAUTHORIZED

    def test_list_with_auth(self, client: Client):
        user1 = User.objects.create_user(username="testuser", email="test@example.com")
        user2 = User.objects.create_user(username="someone else", email="test@example.com")

        client.force_login(user1)

        resp = client.post(
            "/api/auth/token/create/",
            content_type="application/json",
            data={"name": "user1 token"},
        )

        assert resp.status_code == HTTPStatus.CREATED
        user1_token_val = resp.json()["key"]

        client.force_login(user2)

        resp = client.post(
            "/api/auth/token/create/",
            content_type="application/json",
            data={"name": "user2 token"},
        )

        assert resp.status_code == HTTPStatus.CREATED
        user2_token_val = resp.json()["key"]

        client.logout()

        resp = client.get("/api/auth/token/", headers={"X-API-Key": user1_token_val})

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()

        assert len(data) == 1
        assert data[0]["key"] == user1_token_val
        assert data[0]["name"] == "user1 token"

        resp = client.get("/api/auth/token/", headers={"X-API-Key": user2_token_val})

        assert resp.status_code == HTTPStatus.OK
        data = resp.json()

        assert len(data) == 1
        assert data[0]["key"] == user2_token_val
        assert data[0]["name"] == "user2 token"
