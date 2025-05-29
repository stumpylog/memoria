from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from tests.api.conftest import GroupFactory
from tests.api.conftest import UserFactory

UserModel = get_user_model()


@pytest.mark.django_db
class TestUsersCreate:
    """Test user creation endpoint."""

    def test_create_regular_user_as_staff(self, staff_client: Client, users_base_url: str) -> None:
        """Staff can create regular users."""
        payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
            "first_name": "John",
            "last_name": "Doe",
            "is_staff": False,
            "is_superuser": False,
        }
        response = staff_client.post(users_base_url, content_type="application/json", data=payload)

        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["is_staff"] is False
        assert data["is_superuser"] is False

        # Verify user was created in database
        user = UserModel.objects.get(username="newuser")
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.check_password("securepassword123")

    def test_create_staff_user_as_staff(self, staff_client: Client, users_base_url: str) -> None:
        """Staff can create other staff users."""
        payload = {
            "username": "staffuser",
            "email": "staff@example.com",
            "password": "securepassword123",
            "is_staff": True,
            "is_superuser": False,
        }
        response = staff_client.post(users_base_url, content_type="application/json", data=payload)

        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        assert data["is_staff"] is True
        assert data["is_superuser"] is False

    def test_create_superuser_as_superuser(self, superuser_client: Client, users_base_url: str) -> None:
        """Superusers can create other superusers."""
        payload = {
            "username": "superuser",
            "email": "super@example.com",
            "password": "securepassword123",
            "is_staff": True,
            "is_superuser": True,
        }
        response = superuser_client.post(users_base_url, content_type="application/json", data=payload)

        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        assert data["is_staff"] is True
        assert data["is_superuser"] is True

    def test_create_superuser_without_staff_flag_sets_staff(
        self,
        superuser_client: Client,
        users_base_url: str,
    ) -> None:
        """Creating superuser without is_staff=True automatically sets is_staff=True."""
        payload = {
            "username": "superuser2",
            "email": "super2@example.com",
            "password": "securepassword123",
            "is_staff": False,
            "is_superuser": True,
        }
        response = superuser_client.post(users_base_url, content_type="application/json", data=payload)

        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        assert data["is_staff"] is True  # Should be set to True automatically
        assert data["is_superuser"] is True

    def test_create_staff_user_as_regular_user_forbidden(self, logged_in_client: Client, users_base_url: str) -> None:
        """Regular users cannot create staff users."""
        payload = {
            "username": "staffuser",
            "email": "staff@example.com",
            "password": "securepassword123",
            "is_staff": True,
            "is_superuser": False,
        }
        response = logged_in_client.post(users_base_url, content_type="application/json", data=payload)

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_create_superuser_as_staff_forbidden(self, staff_client: Client, users_base_url: str) -> None:
        """Staff users cannot create superusers."""
        payload = {
            "username": "superuser",
            "email": "super@example.com",
            "password": "securepassword123",
            "is_staff": True,
            "is_superuser": True,
        }
        response = staff_client.post(users_base_url, content_type="application/json", data=payload)

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_create_user_unauthenticated_forbidden(self, client: Client, users_base_url: str) -> None:
        """Unauthenticated users cannot create users."""
        payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
        }
        response = client.post(users_base_url, content_type="application/json", data=payload)

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_create_user_minimal_fields(self, staff_client: Client, users_base_url: str) -> None:
        """User creation with only required fields."""
        payload = {
            "username": "minimaluser",
            "email": "minimal@example.com",
            "password": "securepassword123",
        }
        response = staff_client.post(users_base_url, content_type="application/json", data=payload)

        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        assert data["username"] == "minimaluser"
        assert data["first_name"] == ""
        assert data["last_name"] == ""


@pytest.mark.django_db
class TestUsersList:
    """
    Test users list endpoint.
    """

    def test_list_users_as_staff(self, staff_client: Client, users_base_url: str, user_factory: UserFactory) -> None:
        """Staff can list all users."""
        # Create some test users
        user_factory.create_batch(3)

        response = staff_client.get(users_base_url)

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert len(data["items"]) >= 3  # At least our created users + staff user

    def test_list_users_as_regular_user_forbidden(self, logged_in_client: Client, users_base_url: str) -> None:
        """
        Regular users cannot list all users.
        """
        response = logged_in_client.get(users_base_url)

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_list_users_with_filters(
        self,
        staff_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
    ) -> None:
        """
        Test user listing with filters.
        """
        # Create users with specific attributes for filtering
        active_user = user_factory.create(is_active=True, username="activeuser")
        inactive_user = user_factory.create(is_active=False, username="inactiveuser")

        # Test filtering by is_active
        response = staff_client.get(users_base_url, query_params={"is_active": True})
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["count"] == 2

        assert any(
            user["id"] == active_user.pk and user["username"] == active_user.username for user in data["items"]
        ), f"No user found with ID {active_user.pk} and username '{active_user.username}'"

        response = staff_client.get(users_base_url, query_params={"is_active": False})
        assert response.status_code == HTTPStatus.OK

        data = response.json()

        assert data["count"] == 1
        assert any(
            user["id"] == inactive_user.pk and user["username"] == inactive_user.username for user in data["items"]
        ), f"No user found with ID {inactive_user.pk} and username '{inactive_user.username}'"


@pytest.mark.django_db
class TestUsersGetCurrent:
    """
    Test current user endpoint.
    """

    def test_get_current_user(self, logged_in_client: Client, users_base_url: str) -> None:
        """
        Users can get their own information.
        """
        response = logged_in_client.get(f"{users_base_url}me/")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert "username" in data
        assert "email" in data

    def test_get_current_user_unauthenticated(self, client: Client, users_base_url: str) -> None:
        """
        Unauthenticated users cannot get current user info.
        """
        response = client.get(f"{users_base_url}me/")

        assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.django_db
class TestUsersGetById:
    """Test get user by ID endpoint."""

    def test_get_own_user_info(self, logged_in_client: Client, users_base_url: str) -> None:
        """Users can get their own information by ID."""
        # Get current user ID from the logged_in_client
        me_response = logged_in_client.get(f"{users_base_url}me/")
        user_id = me_response.json()["id"]

        response = logged_in_client.get(f"{users_base_url}{user_id}/info/")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["id"] == user_id

    def test_get_other_user_info_as_regular_user_forbidden(
        self,
        logged_in_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
    ) -> None:
        """Regular users cannot get other users' information."""
        other_user = user_factory()

        response = logged_in_client.get(f"{users_base_url}{other_user.id}/info/")

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get_other_user_info_as_staff(
        self,
        staff_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
    ) -> None:
        """Staff can get any user's information."""
        other_user = user_factory()

        response = staff_client.get(f"{users_base_url}{other_user.id}/info/")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["id"] == other_user.id

    def test_get_nonexistent_user_returns_404(self, staff_client: Client, users_base_url: str) -> None:
        """Getting non-existent user returns 404."""
        response = staff_client.get(f"{users_base_url}99999/info/")

        assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
class TestUsersProfileGetCurrent:
    """Test current user profile endpoint."""

    def test_get_current_user_profile(self, logged_in_client: Client, users_base_url: str) -> None:
        """Users can get their own profile."""
        response = logged_in_client.get(f"{users_base_url}me/profile/")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert "bio" in data
        assert "timezone_name" in data
        assert "items_per_page" in data


@pytest.mark.django_db
class TestUsersProfileGetById:
    """Test get user profile by ID endpoint."""

    def test_get_own_profile_by_id(self, logged_in_client: Client, users_base_url: str) -> None:
        """Users can get their own profile by ID."""
        me_response = logged_in_client.get(f"{users_base_url}me/")
        user_id = me_response.json()["id"]

        response = logged_in_client.get(f"{users_base_url}{user_id}/profile/")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert "bio" in data

    def test_get_other_user_profile_as_regular_user_forbidden(
        self,
        logged_in_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
    ) -> None:
        """Regular users cannot get other users' profiles."""
        other_user = user_factory()

        response = logged_in_client.get(f"{users_base_url}{other_user.id}/profile/")

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get_other_user_profile_as_staff(
        self,
        staff_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
    ) -> None:
        """Staff can get any user's profile."""
        other_user = user_factory()

        response = staff_client.get(f"{users_base_url}{other_user.id}/profile/")

        assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
class TestUsersGroupsList:
    """Test user groups list endpoint."""

    def test_get_own_groups(self, logged_in_client: Client, users_base_url: str, group_factory: GroupFactory) -> None:
        """Users can get their own groups."""
        me_response = logged_in_client.get(f"{users_base_url}me/")
        user_id = me_response.json()["id"]

        # Add user to some groups
        group1 = group_factory(name="Group1")
        group2 = group_factory(name="Group2")
        user = UserModel.objects.get(id=user_id)
        user.groups.add(group1, group2)

        response = logged_in_client.get(f"{users_base_url}{user_id}/groups/")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert len(data) == 2
        group_names = [group["name"] for group in data]
        assert "Group1" in group_names
        assert "Group2" in group_names

    def test_get_other_user_groups_as_regular_user_forbidden(
        self,
        logged_in_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
    ) -> None:
        """Regular users cannot get other users' groups."""
        other_user = user_factory()

        response = logged_in_client.get(f"{users_base_url}{other_user.id}/groups/")

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get_other_user_groups_as_staff(
        self,
        staff_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
        group_factory: GroupFactory,
    ) -> None:
        """Staff can get any user's groups."""
        other_user = user_factory()
        group = group_factory()
        other_user.groups.add(group)

        response = staff_client.get(f"{users_base_url}{other_user.id}/groups/")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == group.name


@pytest.mark.django_db
class TestUsersUpdate:
    """Test user update endpoint."""

    def test_update_own_basic_info(self, logged_in_client: Client, users_base_url: str) -> None:
        """Users can update their own basic information."""
        me_response = logged_in_client.get(f"{users_base_url}me/")
        user_id = me_response.json()["id"]

        payload = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
        }
        response = logged_in_client.patch(
            f"{users_base_url}{user_id}/info/",
            content_type="application/json",
            data=payload,
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["email"] == "updated@example.com"

    def test_update_own_password(self, logged_in_client: Client, users_base_url: str) -> None:
        """Users can update their own password."""
        me_response = logged_in_client.get(f"{users_base_url}me/")
        user_id = me_response.json()["id"]

        payload = {"password": "newpassword123"}
        response = logged_in_client.patch(
            f"{users_base_url}{user_id}/info/",
            content_type="application/json",
            data=payload,
        )

        assert response.status_code == HTTPStatus.OK

        # Verify password was changed
        user = UserModel.objects.get(id=user_id)
        assert user.check_password("newpassword123")

    def test_regular_user_cannot_set_staff_status(self, logged_in_client: Client, users_base_url: str) -> None:
        """Regular users cannot set staff status."""
        me_response = logged_in_client.get(f"{users_base_url}me/")
        user_id = me_response.json()["id"]

        payload = {"is_staff": True}
        response = logged_in_client.patch(
            f"{users_base_url}{user_id}/info/",
            content_type="application/json",
            data=payload,
        )

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_regular_user_cannot_set_superuser_status(self, logged_in_client: Client, users_base_url: str) -> None:
        """Regular users cannot set superuser status."""
        me_response = logged_in_client.get(f"{users_base_url}me/")
        user_id = me_response.json()["id"]

        payload = {"is_superuser": True}
        response = logged_in_client.patch(
            f"{users_base_url}{user_id}/info/",
            content_type="application/json",
            data=payload,
        )

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_staff_can_set_staff_status(
        self,
        staff_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
    ) -> None:
        """Staff can set staff status on other users."""
        user = user_factory()

        payload = {"is_staff": True}
        response = staff_client.patch(f"{users_base_url}{user.id}/info/", content_type="application/json", data=payload)

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["is_staff"] is True

    def test_staff_cannot_set_superuser_status(
        self,
        staff_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
    ) -> None:
        """Staff cannot set superuser status."""
        user = user_factory()

        payload = {"is_superuser": True}
        response = staff_client.patch(f"{users_base_url}{user.id}/info/", content_type="application/json", data=payload)

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_superuser_can_set_superuser_status(
        self,
        superuser_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
    ) -> None:
        """Superusers can set superuser status."""
        user = user_factory()

        payload = {"is_superuser": True}
        response = superuser_client.patch(
            f"{users_base_url}{user.id}/info/",
            content_type="application/json",
            data=payload,
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["is_superuser"] is True
        assert data["is_staff"] is True  # Should also be set to staff

    def test_update_other_user_as_regular_user_forbidden(
        self,
        logged_in_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
    ) -> None:
        """Regular users cannot update other users."""
        other_user = user_factory()

        payload = {"first_name": "Hacked"}
        response = logged_in_client.patch(
            f"{users_base_url}{other_user.id}/info/",
            content_type="application/json",
            data=payload,
        )

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_partial_update(self, logged_in_client: Client, users_base_url: str) -> None:
        """Test partial updates with only some fields."""
        me_response = logged_in_client.get(f"{users_base_url}me/")
        user_id = me_response.json()["id"]
        original_email = me_response.json()["email"]

        payload = {"first_name": "OnlyFirst"}
        response = logged_in_client.patch(
            f"{users_base_url}{user_id}/info/",
            content_type="application/json",
            data=payload,
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["first_name"] == "OnlyFirst"
        assert data["email"] == original_email  # Should remain unchanged


@pytest.mark.django_db
class TestUsersProfileUpdate:
    """Test user profile update endpoint."""

    def test_update_own_profile(self, logged_in_client: Client, users_base_url: str) -> None:
        """Users can update their own profile."""
        me_response = logged_in_client.get(f"{users_base_url}me/")
        user_id = me_response.json()["id"]

        payload = {
            "bio": "Updated bio",
            "timezone_name": "America/New_York",
            "items_per_page": 50,
        }
        response = logged_in_client.patch(
            f"{users_base_url}{user_id}/profile/",
            content_type="application/json",
            data=payload,
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["bio"] == "Updated bio"
        assert data["timezone_name"] == "America/New_York"
        assert data["items_per_page"] == 50

    def test_update_other_user_profile_as_regular_user_forbidden(
        self,
        logged_in_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
    ) -> None:
        """Regular users cannot update other users' profiles."""
        other_user = user_factory()

        payload = {"bio": "Hacked bio"}
        response = logged_in_client.patch(
            f"{users_base_url}{other_user.id}/profile/",
            content_type="application/json",
            data=payload,
        )

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_update_other_user_profile_as_staff(
        self,
        staff_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
    ) -> None:
        """Staff can update other users' profiles."""
        other_user = user_factory()

        payload = {"bio": "Staff updated bio"}
        response = staff_client.patch(
            f"{users_base_url}{other_user.id}/profile/",
            content_type="application/json",
            data=payload,
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["bio"] == "Staff updated bio"

    def test_partial_profile_update(self, logged_in_client: Client, users_base_url: str) -> None:
        """Test partial profile updates."""
        me_response = logged_in_client.get(f"{users_base_url}me/")
        user_id = me_response.json()["id"]

        # Get original profile
        profile_response = logged_in_client.get(f"{users_base_url}{user_id}/profile/")
        original_timezone = profile_response.json()["timezone_name"]

        payload = {"bio": "Only bio updated"}
        response = logged_in_client.patch(
            f"{users_base_url}{user_id}/profile/",
            content_type="application/json",
            data=payload,
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["bio"] == "Only bio updated"
        assert data["timezone_name"] == original_timezone  # Should remain unchanged


@pytest.mark.django_db
class TestUsersGroupsUpdate:
    """Test user groups update endpoint."""

    def test_set_user_groups_as_staff(
        self,
        staff_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
        group_factory: GroupFactory,
    ) -> None:
        """Staff can set user groups."""
        user = user_factory()
        group1 = group_factory(name="Group1")
        group2 = group_factory(name="Group2")

        payload = [{"id": group1.id}, {"id": group2.id}]
        response = staff_client.patch(
            f"{users_base_url}{user.id}/groups/",
            content_type="application/json",
            data=payload,
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert len(data) == 2
        group_names = [group["name"] for group in data]
        assert "Group1" in group_names
        assert "Group2" in group_names

        # Verify in database
        user.refresh_from_db()
        assert user.groups.count() == 2

    def test_clear_user_groups(
        self,
        staff_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
        group_factory: GroupFactory,
    ) -> None:
        """Staff can clear all user groups by sending empty list."""
        user = user_factory()
        group = group_factory()
        user.groups.add(group)

        payload = []
        response = staff_client.patch(
            f"{users_base_url}{user.id}/groups/",
            content_type="application/json",
            data=payload,
        )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert len(data) == 0

        # Verify in database
        user.refresh_from_db()
        assert user.groups.count() == 0

    def test_set_user_groups_with_nonexistent_group_error(
        self,
        staff_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
        group_factory: GroupFactory,
    ) -> None:
        """Setting groups with non-existent group IDs returns error."""
        user = user_factory()
        existing_group = group_factory()

        payload = [{"id": existing_group.id}, {"id": 99999}]  # 99999 doesn't exist
        response = staff_client.patch(
            f"{users_base_url}{user.id}/groups/",
            content_type="application/json",
            data=payload,
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "99999" in response.json()["detail"]

    def test_set_user_groups_as_regular_user_forbidden(
        self,
        logged_in_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
        group_factory: GroupFactory,
    ) -> None:
        """Regular users cannot set user groups."""
        user = user_factory()
        group = group_factory()

        payload = [{"id": group.id}]
        response = logged_in_client.patch(
            f"{users_base_url}{user.id}/groups/",
            content_type="application/json",
            data=payload,
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_set_nonexistent_user_groups_returns_404(
        self,
        staff_client: Client,
        users_base_url: str,
        group_factory: GroupFactory,
    ) -> None:
        """Setting groups for non-existent user returns 404."""
        group = group_factory()

        payload = [{"id": group.id}]
        response = staff_client.patch(f"{users_base_url}99999/groups/", content_type="application/json", data=payload)

        assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
class TestUsersEdgeCases:
    """Test edge cases and error conditions."""

    def test_inactive_user_permissions(self, client: Client, users_base_url: str, user_factory: UserFactory) -> None:
        """Test that inactive users cannot access protected endpoints."""
        inactive_user = user_factory(is_active=False)
        client.login(username=inactive_user.username, password="password123")

        response = client.get(f"{users_base_url}me/")
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_update_user_with_invalid_data(self, logged_in_client: Client, users_base_url: str) -> None:
        """Test updating user with invalid data."""
        me_response = logged_in_client.get(f"{users_base_url}me/")
        user_id = me_response.json()["id"]

        # Test with invalid email
        payload = {"email": "invalid-email"}
        response = logged_in_client.patch(
            f"{users_base_url}{user_id}/info/",
            content_type="application/json",
            data=payload,
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["detail"][0]["ctx"]["reason"] == "An email address must have an @-sign."

    def test_create_user_with_duplicate_username(
        self,
        staff_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
    ) -> None:
        """Test creating user with duplicate username."""
        existing_user = user_factory(username="existinguser")

        payload = {
            "username": "existinguser",  # Duplicate
            "email": "new@example.com",
            "password": "password123",
        }
        response = staff_client.post(users_base_url, content_type="application/json", data=payload)
        assert response.status_code == HTTPStatus.CONFLICT

    def test_create_user_with_duplicate_email(
        self,
        staff_client: Client,
        users_base_url: str,
        user_factory: UserFactory,
    ) -> None:
        """Test creating user with duplicate email."""
        existing_user = user_factory(email="existing@example.com")

        payload = {
            "username": "newuser",
            "email": "existing@example.com",  # Duplicate
            "password": "password123",
        }
        response = staff_client.post(users_base_url, content_type="application/json", data=payload)
        assert response.status_code == HTTPStatus.CONFLICT
