import datetime

import factory
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from factory.django import DjangoModelFactory
from pytest_factoryboy import register

from memoria.models import Album
from memoria.models import Person
from memoria.models import Pet
from memoria.models import RoughDate
from memoria.models import RoughLocation
from memoria.models import Tag

User = get_user_model()


@pytest.fixture(scope="session")
def client():
    """Django-Ninja TestClient for API routes."""
    return Client()


# --- FactoryBoy model factories ---
class AlbumFactory(DjangoModelFactory):
    class Meta:
        model = Album
        skip_postgeneration_save = True

    name = factory.Faker("word")
    description = factory.Faker("sentence")

    @factory.post_generation
    def view_groups(self, create, extracted, **kwargs):
        """Assign view groups (list of Group instances)"""
        if not create or not extracted:
            return
        for group in extracted:
            self.view_groups.add(group)

    @factory.post_generation
    def edit_groups(self, create, extracted, **kwargs):
        """Assign edit groups (list of Group instances)"""
        if not create or not extracted:
            return
        for group in extracted:
            self.edit_groups.add(group)


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


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = Group

    name = factory.Faker("word")


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Faker("user_name")
    email = factory.Faker("email")
    is_active = True
    is_staff = False
    is_superuser = False
    password = factory.django.Password("password123")

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        """Assign groups (list of Group instances or names)"""
        if not create or not extracted:
            return
        for g in extracted:
            if isinstance(g, Group):
                self.groups.add(g)
            else:
                group_obj, _ = Group.objects.get_or_create(name=g)
                self.groups.add(group_obj)


class StaffUserFactory(UserFactory):
    is_staff = True


class SuperUserFactory(UserFactory):
    is_staff = True
    is_superuser = True


# Register factories as pytest fixtures
register(AlbumFactory)
register(PersonFactory)
register(PetFactory)
register(RoughDateFactory)
register(RoughLocationFactory)
register(TagFactory)
register(UserFactory)
register(StaffUserFactory)
register(SuperUserFactory)
register(GroupFactory)


@pytest.fixture(scope="session")
def date_today_utc() -> datetime.date:
    return datetime.datetime.now(tz=datetime.UTC).date()


@pytest.fixture
def logged_in_client(client: Client, user_factory: UserFactory):
    """
    TestClient logged in as regular user via session auth.
    """
    user = user_factory.create()
    client.login(username=user.username, password="password123")
    return client


@pytest.fixture
def staff_client(client, staff_user_factory: StaffUserFactory):
    """
    TestClient logged in as staff user via session auth.
    """
    user = staff_user_factory.create()
    client.client.login(username=user.username, password="password123")
    return client


@pytest.fixture
def superuser_client(client, super_user_factory: SuperUserFactory):
    """
    TestClient logged in as superuser via session auth.
    """
    user = super_user_factory.create()
    client.client.login(username=user.username, password="password123")
    return client
