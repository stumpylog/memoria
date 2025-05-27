import datetime

import factory
import pytest
from factory.django import DjangoModelFactory
from ninja.testing import TestClient
from pytest_factoryboy import register

from memoria.api import api
from memoria.models import Album
from memoria.models import Person
from memoria.models import Pet
from memoria.models import RoughDate
from memoria.models import RoughLocation
from memoria.models import Tag


@pytest.fixture(scope="session")
def client():
    """Django-Ninja TestClient for API routes."""
    return TestClient(api)


@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for all API routes."""
    return "/api/"


# --- FactoryBoy model factories ---
class AlbumFactory(DjangoModelFactory):
    class Meta:
        model = Album

    name = factory.Faker("word")
    description = factory.Faker("sentence")


class PersonFactory(DjangoModelFactory):
    class Meta:
        model = Person

    name = factory.Faker("name")
    description = factory.Faker("sentence")


class PetFactory(DjangoModelFactory):
    class Meta:
        model = Pet

    name = factory.Faker("first_name")
    description = factory.Faker("sentence")


class RoughDateFactory(DjangoModelFactory):
    class Meta:
        model = RoughDate

    date = factory.LazyFunction(lambda: factory.Faker().date_object())
    month_valid = True
    day_valid = True


class RoughLocationFactory(DjangoModelFactory):
    class Meta:
        model = RoughLocation

    country_code = factory.Faker("country_code")
    subdivision_code = factory.Maybe(
        factory.Faker("boolean", chance_of_getting_true=50),
        yes_declaration=factory.Faker("state_abbr"),
        no_declaration=None,
    )
    city = factory.Faker("city")
    sub_location = factory.Faker("street_address")


class TagFactory(DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Faker("word")
    description = factory.Faker("sentence")
    tn_parent = None


# Register factories as pytest fixtures
register(AlbumFactory)
register(PersonFactory)
register(PetFactory)
register(RoughDateFactory)
register(RoughLocationFactory)
register(TagFactory)


@pytest.fixture(scope="session")
def date_today_utc() -> datetime.date:
    return datetime.datetime.now(tz=datetime.UTC).date()
