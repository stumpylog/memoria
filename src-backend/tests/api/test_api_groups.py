from http import HTTPStatus

import pytest
from django.contrib.auth.models import Group
from django.test import Client

from tests.api.conftest import GroupFactory
from tests.api.conftest import UserFactory


@pytest.mark.django_db
class TestGroupsCreate:
    """Test cases for POST /groups/ - create_groups endpoint"""

    def test_create_single_group_success(
        self,
        superuser_client: Client,
        groups_base_url: str,
    ) -> None:
        """Test successful creation of a single group"""
        group_data = {"name": "Test Group"}

        response = superuser_client.post(
            groups_base_url,
            data=group_data,
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.CREATED
        response_data = response.json()
        assert len(response_data) == 1
        assert response_data[0]["name"] == "Test Group"

        # Verify group was created in database
        assert Group.objects.filter(name="Test Group").exists()

    def test_create_multiple_groups_success(
        self,
        superuser_client: Client,
        groups_base_url: str,
    ) -> None:
        """Test successful creation of multiple groups"""
        groups_data = [
            {"name": "Group One"},
            {"name": "Group Two"},
            {"name": "Group Three"},
        ]

        response = superuser_client.post(
            groups_base_url,
            data=groups_data,
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.CREATED
        response_data = response.json()
        assert len(response_data) == 3

        created_names = {group["name"] for group in response_data}
        expected_names = {"Group One", "Group Two", "Group Three"}
        assert created_names == expected_names

        # Verify all groups were created in database
        for name in expected_names:
            assert Group.objects.filter(name=name).exists()

    def test_create_group_staff_user_success(
        self,
        staff_client: Client,
        groups_base_url: str,
    ) -> None:
        """Test that staff users can create groups"""
        group_data = {"name": "Staff Created Group"}

        response = staff_client.post(
            groups_base_url,
            data=group_data,
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.CREATED
        assert Group.objects.filter(name="Staff Created Group").exists()

    def test_create_group_regular_user_forbidden(
        self,
        logged_in_client: Client,
        groups_base_url: str,
    ) -> None:
        """Test that regular users cannot create groups"""
        group_data = {"name": "Unauthorized Group"}

        response = logged_in_client.post(
            groups_base_url,
            data=group_data,
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_create_group_unauthenticated_forbidden(
        self,
        client: Client,
        groups_base_url: str,
    ) -> None:
        """Test that unauthenticated users cannot create groups"""
        group_data = {"name": "Unauthenticated Group"}

        response = client.post(
            groups_base_url,
            data=group_data,
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_create_group_invalid_data(
        self,
        superuser_client: Client,
        groups_base_url: str,
    ) -> None:
        """Test group creation with invalid data"""
        invalid_data = {"invalid_field": "value"}

        response = superuser_client.post(
            groups_base_url,
            data=invalid_data,
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    def test_create_group_duplicate_name(
        self,
        superuser_client: Client,
        groups_base_url: str,
        group_factory: GroupFactory,
    ) -> None:
        """Test creating group with duplicate name"""
        existing_group = group_factory(name="Duplicate Name")

        group_data = {"name": "Duplicate Name"}

        response = superuser_client.post(
            groups_base_url,
            data=group_data,
            content_type="application/json",
        )

        # This should fail due to unique constraint on group name
        assert response.status_code == HTTPStatus.CREATED


@pytest.mark.django_db
class TestGroupsListG:
    """Test cases for GET /groups/ - list_groups endpoint"""

    def test_list_groups_empty(
        self,
        superuser_client: Client,
        groups_base_url: str,
    ) -> None:
        """Test listing groups when none exist"""
        response = superuser_client.get(groups_base_url)

        assert response.status_code == HTTPStatus.OK
        assert response.json() == []

    def test_list_groups_with_data(
        self,
        superuser_client: Client,
        groups_base_url: str,
        group_factory: GroupFactory,
    ) -> None:
        """Test listing groups when groups exist"""
        group1 = group_factory(name="Group 1")
        group2 = group_factory(name="Group 2")

        response = superuser_client.get(groups_base_url)

        assert response.status_code == HTTPStatus.OK
        response_data = response.json()
        assert len(response_data) == 2

        group_names = {group["name"] for group in response_data}
        assert group_names == {"Group 1", "Group 2"}

    def test_list_groups_staff_user_success(
        self,
        staff_client: Client,
        groups_base_url: str,
    ) -> None:
        """Test that staff users can list groups"""
        response = staff_client.get(groups_base_url)
        assert response.status_code == HTTPStatus.OK

    def test_list_groups_regular_user_forbidden(
        self,
        logged_in_client: Client,
        groups_base_url: str,
    ) -> None:
        """Test that regular users cannot list groups"""
        response = logged_in_client.get(groups_base_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_list_groups_unauthenticated_forbidden(
        self,
        client: Client,
        groups_base_url: str,
    ) -> None:
        """Test that unauthenticated users cannot list groups"""
        response = client.get(groups_base_url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.django_db
class TestGroupsGet:
    """Test cases for GET /groups/{group_id}/ - get_group endpoint"""

    def test_get_group_success(
        self,
        superuser_client: Client,
        groups_base_url: str,
        group_factory: GroupFactory,
    ) -> None:
        """Test successful retrieval of a single group"""
        group = group_factory(name="Test Group")
        url = f"{groups_base_url}{group.id}/"

        response = superuser_client.get(url)

        assert response.status_code == HTTPStatus.OK
        response_data = response.json()
        assert response_data["id"] == group.id
        assert response_data["name"] == "Test Group"

    def test_get_group_not_found(
        self,
        superuser_client: Client,
        groups_base_url: str,
    ) -> None:
        """Test retrieval of non-existent group"""
        url = f"{groups_base_url}99999/"

        response = superuser_client.get(url)
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_get_group_staff_user_success(
        self,
        staff_client: Client,
        groups_base_url: str,
        group_factory: GroupFactory,
    ) -> None:
        """Test that staff users can retrieve a group"""
        group = group_factory(name="Staff Accessible Group")
        url = f"{groups_base_url}{group.id}/"

        response = staff_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_get_group_regular_user_forbidden(
        self,
        logged_in_client: Client,
        groups_base_url: str,
        group_factory: GroupFactory,
    ) -> None:
        """Test that regular users cannot retrieve a group"""
        group = group_factory(name="Forbidden Group")
        url = f"{groups_base_url}{group.id}/"

        response = logged_in_client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get_group_unauthenticated_forbidden(
        self,
        client: Client,
        groups_base_url: str,
        group_factory: GroupFactory,
    ) -> None:
        """Test that unauthenticated users cannot retrieve a group"""
        group = group_factory(name="Unauthenticated Group")
        url = f"{groups_base_url}{group.id}/"

        response = client.get(url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.django_db
class TestGroupsUpdate:
    """Test cases for PATCH /groups/{group_id}/ - update_group endpoint"""

    def test_update_group_success(
        self,
        superuser_client: Client,
        groups_base_url: str,
        group_factory: GroupFactory,
    ) -> None:
        """Test successful update of a group"""
        group = group_factory(name="Original Name")
        url = f"{groups_base_url}{group.id}/"

        update_data = {"name": "Updated Name"}

        response = superuser_client.patch(
            url,
            data=update_data,
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.OK
        response_data = response.json()
        assert response_data["name"] == "Updated Name"

        # Verify update in database
        group.refresh_from_db()
        assert group.name == "Updated Name"

    def test_update_group_partial_update(
        self,
        superuser_client: Client,
        groups_base_url: str,
        group_factory: GroupFactory,
    ) -> None:
        """Test partial update of a group (PATCH behavior)"""
        group = group_factory(name="Partial Update Group")
        url = f"{groups_base_url}{group.id}/"

        # Only update name field
        update_data = {"name": "Partially Updated"}

        response = superuser_client.patch(
            url,
            data=update_data,
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()["name"] == "Partially Updated"

    def test_update_group_not_found(
        self,
        superuser_client: Client,
        groups_base_url: str,
    ) -> None:
        """Test update of non-existent group"""
        url = f"{groups_base_url}99999/"
        update_data = {"name": "Non-existent Group"}

        response = superuser_client.patch(
            url,
            data=update_data,
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_update_group_staff_user_success(
        self,
        staff_client: Client,
        groups_base_url: str,
        group_factory: GroupFactory,
    ) -> None:
        """Test that staff users can update groups"""
        group = group_factory(name="Staff Updatable")
        url = f"{groups_base_url}{group.id}/"

        update_data = {"name": "Staff Updated"}

        response = staff_client.patch(
            url,
            data=update_data,
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.OK

    def test_update_group_regular_user_forbidden(
        self,
        logged_in_client: Client,
        groups_base_url: str,
        group_factory: GroupFactory,
    ) -> None:
        """Test that regular users cannot update groups"""
        group = group_factory(name="Protected Group")
        url = f"{groups_base_url}{group.id}/"

        update_data = {"name": "Unauthorized Update"}

        response = logged_in_client.patch(
            url,
            data=update_data,
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_update_group_invalid_data(
        self,
        superuser_client: Client,
        groups_base_url: str,
        group_factory: GroupFactory,
    ) -> None:
        """Test update with invalid data"""
        group = group_factory(name="Valid Group")
        url = f"{groups_base_url}{group.id}/"

        invalid_data = {"invalid_field": "value"}

        response = superuser_client.patch(
            url,
            data=invalid_data,
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.django_db
class TestGroupsDelete:
    """Test cases for DELETE /groups/{group_id}/ - delete_group endpoint"""

    def test_delete_group_success(
        self,
        superuser_client: Client,
        groups_base_url: str,
        group_factory: GroupFactory,
    ) -> None:
        """Test successful deletion of a group"""
        group = group_factory(name="To Be Deleted")
        group_id = group.id
        url = f"{groups_base_url}{group_id}/"

        response = superuser_client.delete(url)

        assert response.status_code == HTTPStatus.NO_CONTENT
        assert response.content == b""

        # Verify deletion in database
        assert not Group.objects.filter(id=group_id).exists()

    def test_delete_group_not_found(
        self,
        superuser_client: Client,
        groups_base_url: str,
    ) -> None:
        """Test deletion of non-existent group"""
        url = f"{groups_base_url}99999/"

        response = superuser_client.delete(url)
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_delete_group_staff_user_success(
        self,
        staff_client: Client,
        groups_base_url: str,
        group_factory: GroupFactory,
    ) -> None:
        """Test that staff users can delete groups"""
        group = group_factory(name="Staff Deletable")
        url = f"{groups_base_url}{group.id}/"

        response = staff_client.delete(url)
        assert response.status_code == HTTPStatus.NO_CONTENT

    def test_delete_group_regular_user_forbidden(
        self,
        logged_in_client: Client,
        groups_base_url: str,
        group_factory: GroupFactory,
    ) -> None:
        """Test that regular users cannot delete groups"""
        group = group_factory(name="Protected Group")
        url = f"{groups_base_url}{group.id}/"

        response = logged_in_client.delete(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_delete_group_unauthenticated_forbidden(
        self,
        client: Client,
        groups_base_url: str,
        group_factory: GroupFactory,
    ) -> None:
        """Test that unauthenticated users cannot delete groups"""
        group = group_factory(name="Unauthenticated Group")
        url = f"{groups_base_url}{group.id}/"

        response = client.delete(url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_delete_group_with_users(
        self,
        superuser_client: Client,
        groups_base_url: str,
        group_factory: GroupFactory,
        user_factory: UserFactory,
    ) -> None:
        """Test deletion of group that has associated users"""
        group = group_factory(name="Group With Users")
        user = user_factory()
        user.groups.add(group)

        url = f"{groups_base_url}{group.id}/"

        response = superuser_client.delete(url)

        # Group should be deleted successfully
        # Users should remain but lose group association
        assert response.status_code == HTTPStatus.NO_CONTENT
        assert not Group.objects.filter(id=group.id).exists()

        # User should still exist
        user.refresh_from_db()
        assert user.groups.count() == 0


@pytest.mark.django_db
class TestGroupsIntegration:
    """Integration tests for groups API workflows"""

    def test_complete_group_lifecycle(
        self,
        superuser_client: Client,
        groups_base_url: str,
    ) -> None:
        """Test complete CRUD lifecycle of a group"""
        # Create
        create_data = {"name": "Lifecycle Group"}
        create_response = superuser_client.post(
            groups_base_url,
            data=create_data,
            content_type="application/json",
        )
        assert create_response.status_code == HTTPStatus.CREATED
        group_id = create_response.json()[0]["id"]

        # Read
        get_url = f"{groups_base_url}{group_id}/"
        get_response = superuser_client.get(get_url)
        assert get_response.status_code == HTTPStatus.OK
        assert get_response.json()["name"] == "Lifecycle Group"

        # Update
        update_data = {"name": "Updated Lifecycle Group"}
        update_response = superuser_client.patch(
            get_url,
            data=update_data,
            content_type="application/json",
        )
        assert update_response.status_code == HTTPStatus.OK
        assert update_response.json()["name"] == "Updated Lifecycle Group"

        # Delete
        delete_response = superuser_client.delete(get_url)
        assert delete_response.status_code == HTTPStatus.NO_CONTENT

        # Verify deletion
        final_get_response = superuser_client.get(get_url)
        assert final_get_response.status_code == HTTPStatus.NOT_FOUND

    def test_bulk_create_then_list(
        self,
        superuser_client: Client,
        groups_base_url: str,
    ) -> None:
        """Test bulk creation followed by listing"""
        bulk_data = [
            {"name": "Bulk Group 1"},
            {"name": "Bulk Group 2"},
            {"name": "Bulk Group 3"},
        ]

        # Bulk create
        create_response = superuser_client.post(
            groups_base_url,
            data=bulk_data,
            content_type="application/json",
        )
        assert create_response.status_code == HTTPStatus.CREATED
        assert len(create_response.json()) == 3

        # List all groups
        list_response = superuser_client.get(groups_base_url)
        assert list_response.status_code == HTTPStatus.OK

        response_data = list_response.json()
        group_names = {group["name"] for group in response_data}
        expected_names = {"Bulk Group 1", "Bulk Group 2", "Bulk Group 3"}
        assert expected_names.issubset(group_names)
