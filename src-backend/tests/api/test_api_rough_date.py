import datetime
from http import HTTPStatus

import pytest
from django.test.client import Client

from memoria.models import RoughDate
from memoria.tests.api.types import DateGeneratorProtocol


@pytest.mark.django_db
class TestApiRoughDateCreate:
    def test_create_rough_date_all_valid(self, client: Client, date_today_utc: datetime.date):
        resp = client.post(
            "/api/date/",
            content_type="application/json",
            data={
                "date": date_today_utc.isoformat(),
                "month_valid": True,
                "day_valid": True,
            },
        )
        assert resp.status_code == HTTPStatus.CREATED

        obj = RoughDate.objects.get(id=resp.json()["id"])

        assert obj is not None
        assert obj.date == date_today_utc
        assert obj.month_valid
        assert obj.day_valid

    def test_create_rough_date_valid_month(self, client: Client, date_today_utc: datetime.date):
        resp = client.post(
            "/api/date/",
            content_type="application/json",
            data={
                "date": date_today_utc.isoformat(),
                "month_valid": True,
                "day_valid": False,
            },
        )
        assert resp.status_code == HTTPStatus.CREATED

        obj = RoughDate.objects.get(id=resp.json()["id"])

        assert obj is not None
        assert obj.date == date_today_utc
        assert obj.month_valid
        assert not obj.day_valid

    def test_create_rough_date_invalid_month_valid_date(self, client: Client, date_today_utc: datetime.date):
        resp = client.post(
            "/api/date/",
            content_type="application/json",
            data={
                "date": date_today_utc.isoformat(),
                "month_valid": False,
                "day_valid": True,
            },
        )
        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

        assert RoughDate.objects.count() == 0

    def test_create_date_already_exists(self, client: Client, date_today_utc: datetime.date):
        resp = client.post(
            "/api/date/",
            content_type="application/json",
            data={
                "date": date_today_utc.isoformat(),
                "month_valid": True,
                "day_valid": False,
            },
        )
        assert resp.status_code == HTTPStatus.CREATED

        resp = client.post(
            "/api/date/",
            content_type="application/json",
            data={
                "date": date_today_utc.isoformat(),
                "month_valid": True,
                "day_valid": False,
            },
        )
        assert resp.status_code == HTTPStatus.CONFLICT


@pytest.mark.django_db
class TestApiRoughDateRead:
    def test_read_no_dates(self, client: Client):
        resp = client.get(
            "/api/date/",
            content_type="application/json",
        )

        assert resp.status_code == HTTPStatus.OK

        assert resp.json()["count"] == 0
        assert len(resp.json()["items"]) == 0

    def test_read_dates(self, client: Client, date_db_factory: DateGeneratorProtocol):
        count = 2
        for _ in range(count):
            date_db_factory()

        resp = client.get(
            "/api/date/",
            content_type="application/json",
        )

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data["count"] == count
        assert len(data["items"]) == count
        for date in RoughDate.objects.order_by("pk").all():
            assert {
                "id": date.pk,
                "date": date.date.isoformat(),
                "month_valid": date.month_valid,
                "day_valid": date.day_valid,
            } in data["items"]

    def test_read_single_date(self, client: Client, date_db_factory: DateGeneratorProtocol):
        date = RoughDate.objects.get(pk=date_db_factory())

        resp = client.get(
            f"/api/date/{date.pk}/",
            content_type="application/json",
        )

        assert resp.status_code == HTTPStatus.OK

        data = resp.json()

        assert data == {
            "id": date.pk,
            "date": date.date.isoformat(),
            "month_valid": date.month_valid,
            "day_valid": date.day_valid,
        }


@pytest.mark.django_db
class TestApiRoughDateUpdate:
    def test_update_rough_date_date(
        self,
        client: Client,
        date_db_factory: DateGeneratorProtocol,
        date_today_utc: datetime.date,
    ):
        date = RoughDate.objects.get(pk=date_db_factory())

        new_date = date_today_utc + datetime.timedelta(days=1)
        resp = client.patch(
            f"/api/date/{date.pk}/",
            content_type="application/json",
            data={"date": new_date.isoformat()},
        )

        assert resp.status_code == HTTPStatus.OK

        date.refresh_from_db()

        assert date.date == new_date

    def test_update_rough_date_month_valid(self, client: Client, date_db_factory: DateGeneratorProtocol):
        date = RoughDate.objects.get(pk=date_db_factory())

        date.month_valid = False
        date.day_valid = False
        date.save()

        resp = client.patch(
            f"/api/date/{date.pk}/",
            content_type="application/json",
            data={"month_valid": True},
        )

        assert resp.status_code == HTTPStatus.OK

        date.refresh_from_db()

        assert date.month_valid

    def test_update_rough_date_day_valid(self, client: Client, date_db_factory: DateGeneratorProtocol):
        date = RoughDate.objects.get(pk=date_db_factory())

        date.month_valid = True
        date.day_valid = False
        date.save()

        resp = client.patch(
            f"/api/date/{date.pk}/",
            content_type="application/json",
            data={"day_valid": True},
        )

        assert resp.status_code == HTTPStatus.OK

        date.refresh_from_db()

        assert date.day_valid

    def test_update_rough_date_invalid_combo(self, client: Client, date_db_factory: DateGeneratorProtocol):
        date = RoughDate.objects.get(pk=date_db_factory())

        date.month_valid = False
        date.day_valid = False
        date.save()

        resp = client.patch(
            f"/api/date/{date.pk}/",
            content_type="application/json",
            data={"day_valid": True},
        )

        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

        date.refresh_from_db()

        assert not date.day_valid

    def test_update_rough_date_empty_data(self, client: Client, date_db_factory: DateGeneratorProtocol):
        date = RoughDate.objects.get(pk=date_db_factory())

        date.month_valid = False
        date.day_valid = False
        date.save()

        resp = client.patch(
            f"/api/date/{date.pk}/",
            content_type="application/json",
            data={},
        )

        assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.django_db
class TestApiRoughDateDelete:
    def test_delete_rough_date(self, client: Client, date_db_factory: DateGeneratorProtocol):
        date = RoughDate.objects.get(pk=date_db_factory())

        resp = client.delete(f"/api/date/{date.pk}/")

        assert resp.status_code == HTTPStatus.NO_CONTENT
        assert RoughDate.objects.count() == 0

    def test_delete_rough_date_not_found(self, client: Client, date_db_factory: DateGeneratorProtocol):
        date = RoughDate.objects.get(pk=date_db_factory())

        resp = client.delete(f"/api/date/{date.pk + 2}/")

        assert resp.status_code == HTTPStatus.NOT_FOUND
