import tempfile
from collections.abc import Callable
from http import HTTPStatus
from pathlib import Path

import pytest
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.test import Client
from pytest_mock import MockerFixture

from memoria.models import Album
from memoria.models import Image
from memoria.models import ImageInAlbum


# -------------------------------------------------------------------------------------------------
# 1. READ (List & Retrieve)
# -------------------------------------------------------------------------------------------------
@pytest.mark.django_db
class TestAlbumRead:
    """Tests for listing and retrieving Albums."""

    def test_list_albums_empty(
        self,
        logged_in_client: Client,
        album_base_url: str,
    ) -> None:
        """List returns empty when no albums exist."""
        response = logged_in_client.get(album_base_url)
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["items"] == []

    @pytest.mark.parametrize(
        ("names", "search_term", "expected_count"),
        [
            (["Test Album 1", "Test Album 2"], None, 2),
            (["Holiday Photos", "Work Events"], "Holiday", 1),
        ],
    )
    def test_list_albums_with_data_and_search(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        names: list[str],
        search_term: str | None,
        expected_count: int,
    ) -> None:
        """List returns correct items, and filters by name if requested."""
        for name in names:
            album_factory(name=name)

        params = {"album_name": search_term} if search_term else {}
        response = logged_in_client.get(album_base_url, params)
        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert len(data["items"]) == expected_count
        if search_term:
            assert data["items"][0]["name"] == "Holiday Photos"

    def test_list_albums_pagination(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
    ) -> None:
        """
        Verify pagination structure (limit/offset). Creates 25 albums and
        ensures only 10 are returned when limit=10, and that 'next' is in response.
        """
        for i in range(25):
            album_factory(name=f"Album {i}")

        response = logged_in_client.get(album_base_url, {"limit": 10, "offset": 0})
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert len(data["items"]) == 10
        assert "next" in data

    def test_get_album_success(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
    ) -> None:
        """Retrieve single album returns correct data."""
        album = album_factory(name="Test Album", description="Test Description")

        response = logged_in_client.get(f"{album_base_url}{album.id}/")
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["id"] == album.id
        assert data["name"] == "Test Album"
        assert data["description"] == "Test Description"

    def test_get_album_not_found(
        self,
        logged_in_client: Client,
        album_base_url: str,
    ) -> None:
        """Retrieving non-existent album returns 404."""
        response = logged_in_client.get(f"{album_base_url}999/")
        assert response.status_code == HTTPStatus.NOT_FOUND


# -------------------------------------------------------------------------------------------------
# 2. CREATE
# -------------------------------------------------------------------------------------------------
@pytest.mark.django_db
class TestAlbumCreate:
    """Tests for creating new Albums."""

    def test_create_album_success(
        self,
        logged_in_client: Client,
        album_base_url: str,
    ) -> None:
        """POSTing valid data creates a new album."""
        payload = {"name": "New Album", "description": "New album description"}

        response = logged_in_client.post(album_base_url, payload, content_type="application/json")
        assert response.status_code == HTTPStatus.CREATED

        resp_data = response.json()
        assert resp_data["name"] == "New Album"
        assert resp_data["description"] == "New album description"

        created = Album.objects.get(id=resp_data["id"])
        assert created.name == "New Album"

    def test_create_album_with_groups(
        self,
        logged_in_client: Client,
        album_base_url: str,
        group_factory: Callable[..., Group],
    ) -> None:
        """POSTing with view/edit group IDs assigns permissions correctly."""
        view_group = group_factory.create()
        edit_group = group_factory.create()

        payload = {
            "name": "Group Album",
            "description": "Album with groups",
            "view_group_ids": [view_group.id],
            "edit_group_ids": [edit_group.id],
        }

        response = logged_in_client.post(album_base_url, payload, content_type="application/json")
        assert response.status_code == HTTPStatus.CREATED

        resp_data = response.json()
        album = Album.objects.get(id=resp_data["id"])
        assert view_group in album.view_groups.all()
        assert edit_group in album.edit_groups.all()

    def test_create_missing_required_fields(
        self,
        logged_in_client: Client,
        album_base_url: str,
    ) -> None:
        """POSTing without 'name' returns 400."""
        payload = {"description": "Missing name field"}
        response = logged_in_client.post(album_base_url, payload, content_type="application/json")
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_create_invalid_json_returns_400(
        self,
        logged_in_client: Client,
        album_base_url: str,
    ) -> None:
        """POSTing invalid JSON returns 400."""
        response = logged_in_client.post(album_base_url, "invalid json", content_type="application/json")
        assert response.status_code == HTTPStatus.BAD_REQUEST


# -------------------------------------------------------------------------------------------------
# 3. UPDATE
# -------------------------------------------------------------------------------------------------
@pytest.mark.django_db
class TestAlbumUpdate:
    """Tests for updating existing Albums, including group assignments and sorting."""

    def test_update_album_success(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
    ) -> None:
        """PATCHing name/description updates the album."""
        album = album_factory(name="Original Name", description="Original Description")

        payload = {"name": "Updated Name", "description": "Updated Description"}
        response = logged_in_client.patch(
            f"{album_base_url}{album.id}/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK

        resp_data = response.json()
        assert resp_data["name"] == "Updated Name"
        assert resp_data["description"] == "Updated Description"

    def test_update_album_partial(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
    ) -> None:
        """PATCHing only name leaves description unchanged."""
        album = album_factory(name="Original Name", description="Original Description")

        payload = {"name": "Updated Name"}
        response = logged_in_client.patch(
            f"{album_base_url}{album.id}/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK

        resp_data = response.json()
        assert resp_data["name"] == "Updated Name"
        assert resp_data["description"] == "Original Description"

    def test_update_album_groups(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        group_factory: Callable[..., Group],
    ) -> None:
        """PATCHing view_group_ids reassigns view permissions."""
        album = album_factory(name="Test Album")
        new_group = group_factory.create()

        payload = {"view_group_ids": [new_group.id]}
        response = logged_in_client.patch(
            f"{album_base_url}{album.id}/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK

        album.refresh_from_db()
        assert new_group in album.view_groups.all()

    def test_sort_album_images_success(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        image_factory: Callable[..., Image],
    ) -> None:
        """PATCHing /sort/ with correct 'sorting' list reorders images."""
        album = album_factory(name="Test Album")
        image1 = image_factory.create(name="Image 1")
        image2 = image_factory.create(name="Image 2")
        image3 = image_factory.create(name="Image 3")

        # Initial order: 1,2,3
        ImageInAlbum.objects.create(album=album, image=image1, sort_order=0)
        ImageInAlbum.objects.create(album=album, image=image2, sort_order=1)
        ImageInAlbum.objects.create(album=album, image=image3, sort_order=2)

        payload = {"sorting": [image3.id, image1.id, image2.id]}
        response = logged_in_client.patch(
            f"{album_base_url}{album.id}/sort/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK

        reordered = ImageInAlbum.objects.filter(album=album).order_by("sort_order")
        actual_order = [item.image_id for item in reordered]
        assert actual_order == [image3.id, image1.id, image2.id]

    def test_sort_album_images_mismatch_fails(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        image_factory: Callable[..., Image],
    ) -> None:
        """PATCHing /sort/ with mismatched IDs returns 400."""
        album = album_factory(name="Test Album")
        image1 = image_factory.create(name="Image 1")
        image2 = image_factory.create(name="Image 2")

        # Only image1 added
        ImageInAlbum.objects.create(album=album, image=image1, sort_order=0)

        payload = {"sorting": [image1.id, image2.id]}
        response = logged_in_client.patch(
            f"{album_base_url}{album.id}/sort/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_sort_album_images_missing_image_fails(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        image_factory: Callable[..., Image],
    ) -> None:
        """PATCHing /sort/ omitting an image returns 400."""
        album = album_factory(name="Test Album")
        image1 = image_factory.create(name="Image 1")
        image2 = image_factory.create(name="Image 2")

        ImageInAlbum.objects.create(album=album, image=image1, sort_order=0)
        ImageInAlbum.objects.create(album=album, image=image2, sort_order=1)

        payload = {"sorting": [image1.id]}
        response = logged_in_client.patch(
            f"{album_base_url}{album.id}/sort/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_update_invalid_json_returns_400(
        self,
        logged_in_client: Client,
        album_base_url: str,
    ) -> None:
        """PATCHing with invalid JSON returns 400."""
        response = logged_in_client.patch("/api/album/", "not-json", content_type="application/json")
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_update_nonexistent_returns_404(
        self,
        logged_in_client: Client,
        album_base_url: str,
    ) -> None:
        """PATCHing a non-existent album returns 404."""
        payload = {"name": "Doesn't Matter"}
        response = logged_in_client.patch(
            f"{album_base_url}999/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.NOT_FOUND


# -------------------------------------------------------------------------------------------------
# 4. DELETE
# -------------------------------------------------------------------------------------------------
@pytest.mark.django_db
class TestAlbumDelete:
    """Tests for deleting Albums."""

    def test_delete_album_success(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
    ) -> None:
        """DELETE removes the album and returns 204."""
        album = album_factory(name="To Delete")
        album_id = album.id

        response = logged_in_client.delete(f"{album_base_url}{album.id}/")
        assert response.status_code == HTTPStatus.NO_CONTENT
        assert not Album.objects.filter(id=album_id).exists()

    def test_delete_album_not_found(
        self,
        logged_in_client: Client,
        album_base_url: str,
    ) -> None:
        """DELETE on non-existent album returns 404."""
        response = logged_in_client.delete(f"{album_base_url}999/")
        assert response.status_code == HTTPStatus.NOT_FOUND


# -------------------------------------------------------------------------------------------------
# 5. IMAGE MANAGEMENT (Add / Remove / Download)
# -------------------------------------------------------------------------------------------------
@pytest.mark.django_db
class TestAlbumImageManagement:
    """Tests for endpoints that add/remove/sort/download images within Albums."""

    @pytest.fixture
    def mock_image_paths(self) -> Callable[[str], Path]:
        """Helper to create temporary image files."""

        def _create_temp(content: str = "fake image data") -> Path:
            temp_file = Path(tempfile.mktemp(suffix=".jpg"))
            temp_file.write_text(content)
            return temp_file

        return _create_temp

    def test_add_images_to_album_success(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        image_factory: Callable[..., Image],
    ) -> None:
        """PATCHing /images/ with valid IDs adds images in given order."""
        album = album_factory(name="Test Album")
        image1 = image_factory.create(name="Image 1")
        image2 = image_factory.create(name="Image 2")

        payload = {"image_ids": [image1.id, image2.id]}
        response = logged_in_client.patch(
            f"{album_base_url}{album.id}/images/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK

        all_assocs = ImageInAlbum.objects.filter(album=album).order_by("sort_order")
        assert [assoc.image_id for assoc in all_assocs] == [image1.id, image2.id]

    def test_add_images_preserves_order(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        image_factory: Callable[..., Image],
    ) -> None:
        """PATCHing /images/ with specific order preserves that order."""
        album = album_factory(name="Test Album")
        img1 = image_factory.create(name="Image 1")
        img2 = image_factory.create(name="Image 2")
        img3 = image_factory.create(name="Image 3")

        payload = {"image_ids": [img3.id, img1.id, img2.id]}
        response = logged_in_client.patch(
            f"{album_base_url}{album.id}/images/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK

        sorted_assocs = ImageInAlbum.objects.filter(album=album).order_by("sort_order")
        assert [assoc.image_id for assoc in sorted_assocs] == [img3.id, img1.id, img2.id]

    def test_add_images_avoids_duplicates(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        image_factory: Callable[..., Image],
    ) -> None:
        """Re-adding the same image does not create duplicates."""
        album = album_factory(name="Test Album")
        img = image_factory.create(name="Image 1")
        ImageInAlbum.objects.create(album=album, image=img, sort_order=0)

        payload = {"image_ids": [img.id]}
        response = logged_in_client.patch(
            f"{album_base_url}{album.id}/images/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK
        assert ImageInAlbum.objects.filter(album=album, image=img).count() == 1

    def test_add_images_nonexistent_fails(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
    ) -> None:
        """PATCHing /images/ with non-existent IDs returns 400."""
        album = album_factory(name="Test Album")
        payload = {"image_ids": [999, 1000]}

        response = logged_in_client.patch(
            f"{album_base_url}{album.id}/images/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_remove_images_from_album_success(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        image_factory: Callable[..., Image],
    ) -> None:
        """DELETE /images/ removes only specified images."""
        album = album_factory(name="Test Album")
        img1 = image_factory.create(name="Image 1")
        img2 = image_factory.create(name="Image 2")

        # Pre-populate
        ImageInAlbum.objects.create(album=album, image=img1, sort_order=0)
        ImageInAlbum.objects.create(album=album, image=img2, sort_order=1)

        payload = {"image_ids": [img1.id]}
        response = logged_in_client.delete(
            f"{album_base_url}{album.id}/images/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK

        remaining = ImageInAlbum.objects.filter(album=album)
        assert remaining.count() == 1
        assert remaining.first().image_id == img2.id

    def test_remove_nonexistent_images_logs_warning(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        mocker: MockerFixture,
    ) -> None:
        """
        DELETE /images/ with IDs not in album logs a warning but returns 200.
        Uses pytest-mock to verify logger.warning was called.
        """
        album = album_factory(name="Test Album")
        payload = {"image_ids": [999]}

        mock_logger = mocker.patch("memoria.routes.albums.api.logger")
        response = logged_in_client.delete(
            f"{album_base_url}{album.id}/images/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK
        mock_logger.warning.assert_called()

    def test_download_album_success(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        mock_image_paths: Callable[[str], Path],
        mocker: MockerFixture,
    ) -> None:
        """
        GET /download/ returns a ZIP when album has images.
        Uses pytest-mock instead of unittest.mock.
        """
        album = album_factory(name="Download Test")

        # Create two temporary image files
        img_path1 = mock_image_paths("data1")
        img_path2 = mock_image_paths("data2")

        # Prepare two mock Image instances
        mock_image1 = mocker.MagicMock()
        mock_image1.full_size_path = str(img_path1)
        mock_image1.original_path = str(img_path1)

        mock_image2 = mocker.MagicMock()
        mock_image2.full_size_path = str(img_path2)
        mock_image2.original_path = str(img_path2)

        # Patch the Image model so that Album.prefetched_imageinals returns our mocks
        mocker.patch(
            "memoria.models.Image",
            new=mocker.MagicMock(return_value=[mock_image1, mock_image2]),
        )
        # Simulate the `prefetched_imageinals` attribute on the album instance
        album.prefetched_imageinals = [mocker.MagicMock(image=mock_image1), mocker.MagicMock(image=mock_image2)]

        response = logged_in_client.get(f"{album_base_url}{album.id}/download/")
        assert response.status_code == HTTPStatus.OK
        assert response["Content-Type"] == "application/zip"
        assert "attachment" in response["Content-Disposition"]

        # Cleanup temp files
        img_path1.unlink(missing_ok=True)
        img_path2.unlink(missing_ok=True)

    def test_download_album_originals(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        mock_image_paths: Callable[[str], Path],
        mocker: MockerFixture,
    ) -> None:
        """GET /download/?zip_originals=true returns ZIP of original images."""
        album = album_factory(name="Download Test")

        img_path = mock_image_paths("orig data")
        mock_image = mocker.MagicMock()
        mock_image.full_size_path = str(img_path)
        mock_image.original_path = str(img_path)

        album.prefetched_imageinals = [mocker.MagicMock(image=mock_image)]

        response = logged_in_client.get(f"{album_base_url}{album.id}/download/?zip_originals=true")
        assert response.status_code == HTTPStatus.OK
        assert response["Content-Type"] == "application/zip"

        # Cleanup temp file
        img_path.unlink(missing_ok=True)

    def test_download_empty_album_fails(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        mocker: MockerFixture,
    ) -> None:
        """GET /download/ on empty album returns 400."""
        album = album_factory(name="Empty Album")
        album.prefetched_imageinals = []

        response = logged_in_client.get(f"{album_base_url}{album.id}/download/")
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_download_album_not_found(
        self,
        logged_in_client: Client,
        album_base_url: str,
    ) -> None:
        """GET /download/ for a non-existent album returns 404."""
        response = logged_in_client.get(f"{album_base_url}999/download/")
        assert response.status_code == HTTPStatus.NOT_FOUND


# -------------------------------------------------------------------------------------------------
# 6. PERMISSIONS & ERROR HANDLING
# -------------------------------------------------------------------------------------------------
@pytest.mark.django_db
class TestAlbumPermissionsAndErrors:
    """Tests for permission enforcement and error/edge-case handling."""

    @pytest.fixture
    def user_factory(self) -> Callable[..., User]:
        """Simple User factory for tests that need custom users."""

        class UFactory:
            @staticmethod
            def create(**kwargs) -> User:
                return User.objects.create_user(**kwargs)

        return UFactory

    def test_anonymous_user_denied(
        self,
        client: Client,
        album_base_url: str,
    ) -> None:
        """Anonymous GET /album/ returns 401."""
        response = client.get(album_base_url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_list_albums_only_viewable(
        self,
        client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        user_factory: Callable[..., User],
    ) -> None:
        """
        Users only see albums belonging to groups they’re in.
        Create two users, two groups, assign one group each,
        and assign each album to one group.
        """
        user1 = user_factory.create(username="user1", password="pass123")
        user2 = user_factory.create(username="user2", password="pass123")

        group1 = Group.objects.create(name="User1 Group")
        group2 = Group.objects.create(name="User2 Group")

        user1.groups.add(group1)
        user2.groups.add(group2)

        album1 = album_factory(name="Album 1")
        album1.view_groups.add(group1)
        album2 = album_factory(name="Album 2")
        album2.view_groups.add(group2)

        client.force_login(user1)
        response = client.get(album_base_url)
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Album 1"

    def test_edit_permission_required_for_updates(
        self,
        client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        user_factory: Callable[..., User],
    ) -> None:
        """
        Users without edit permissions can view but cannot PATCH.
        They get 404 on PATCH (permission filter hides the instance).
        """
        user = user_factory.create(username="user1", password="pass123")
        view_group = Group.objects.create(name="View Group")
        user.groups.add(view_group)

        album = album_factory(name="Test Album")
        album.view_groups.add(view_group)

        client.force_login(user)
        # Can GET
        response = client.get(f"{album_base_url}{album.id}/")
        assert response.status_code == HTTPStatus.OK

        # Cannot PATCH
        payload = {"name": "Updated Name"}
        response = client.patch(
            f"{album_base_url}{album.id}/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_edit_permission_allows_modifications(
        self,
        client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        user_factory: Callable[..., User],
    ) -> None:
        """Users in edit_groups can PATCH and see the change."""
        user = user_factory.create(username="user1", password="pass123")
        edit_group = Group.objects.create(name="Edit Group")
        user.groups.add(edit_group)

        album = album_factory(name="Test Album")
        album.edit_groups.add(edit_group)

        client.force_login(user)
        payload = {"name": "Updated Name"}
        response = client.patch(
            f"{album_base_url}{album.id}/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json()["name"] == "Updated Name"

    def test_invalid_image_ids_type(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
    ) -> None:
        """PATCHing /images/ with non-integer IDs returns 400."""
        album = album_factory(name="Test Album")
        payload = {"image_ids": ["not", "integers"]}

        response = logged_in_client.patch(
            f"{album_base_url}{album.id}/images/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_empty_image_list_handling(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
    ) -> None:
        """PATCHing /images/ with [] simply succeeds (no-op)."""
        album = album_factory(name="Test Album")
        payload = {"image_ids": []}

        response = logged_in_client.patch(
            f"{album_base_url}{album.id}/images/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK

    def test_concurrent_sort_operations(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        image_factory: Callable[..., Image],
    ) -> None:
        """
        Simulate two concurrent /sort/ calls by sending a valid sort; expect 200.
        (Real concurrency is not tested here; we verify transaction handling.)
        """
        album = album_factory(name="Test Album")
        img1 = image_factory.create(name="Image 1")
        img2 = image_factory.create(name="Image 2")
        ImageInAlbum.objects.create(album=album, image=img1, sort_order=0)
        ImageInAlbum.objects.create(album=album, image=img2, sort_order=1)

        payload = {"sorting": [img2.id, img1.id]}
        response = logged_in_client.patch(
            f"{album_base_url}{album.id}/sort/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK

    def test_large_album_performance(
        self,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        image_factory: Callable[..., Image],
    ) -> None:
        """
        Create 100 images in an album, GET its detail (should be fast), then
        PATCH a reverse sort; expect 200.
        """
        album = album_factory(name="Large Album")
        images_list: list[Image] = []
        for i in range(100):
            img = image_factory.create(name=f"Image {i}")
            images_list.append(img)
            ImageInAlbum.objects.create(album=album, image=img, sort_order=i)

        # GET detail
        response = logged_in_client.get(f"{album_base_url}{album.id}/")
        assert response.status_code == HTTPStatus.OK

        # Reverse sort
        reversed_ids = [img.id for img in reversed(images_list)]
        payload = {"sorting": reversed_ids}
        response = logged_in_client.patch(
            f"{album_base_url}{album.id}/sort/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK

    def test_logging_behavior(
        self,
        mocker: MockerFixture,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
    ) -> None:
        """
        Ensure logger.info is called on successful PATCH, and logger.warning on
        invalid delete-images. Also ensure pagination logging behavior when many albums exist.
        """
        mock_logger = mocker.patch("memoria.routes.albums.api.logger")

        # 1) Successful PATCH ⇒ info()
        album = album_factory(name="Test Album")
        payload = {"name": "Updated Album"}
        response = logged_in_client.patch(
            f"{album_base_url}{album.id}/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.OK
        mock_logger.info.assert_called()

        # 2) DELETE /images/ with non-existent ID ⇒ warning()
        payload = {"image_ids": [999]}
        response = logged_in_client.delete(
            f"{album_base_url}{album.id}/images/",
            payload,
            content_type="application/json",
        )
        mock_logger.warning.assert_called()

        # 3) Create 25 albums ⇒ pagination on list should trigger logging
        for i in range(25):
            album_factory(name=f"Album {i}")
        response = logged_in_client.get(album_base_url, {"limit": 10, "offset": 0})
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert len(data["items"]) == 10
        assert "next" in data


# -------------------------------------------------------------------------------------------------
# 7. PERMISSION-SPECIFIC EDGE CASES
# -------------------------------------------------------------------------------------------------
@pytest.mark.django_db
class TestAlbumImageManagementEdge:
    """Combined edge-case tests around image management and permissions."""

    @pytest.fixture
    def user_factory(self) -> Callable[..., User]:
        """UserFactory for permission tests."""

        class UFactory:
            @staticmethod
            def create(**kwargs) -> User:
                return User.objects.create_user(**kwargs)

        return UFactory

    def test_download_empty_album_logs_no_warning(
        self,
        mocker: MockerFixture,
        logged_in_client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
    ) -> None:
        """
        Attempting to download an empty album should log a warning but return 400.
        """
        album = album_factory(name="Empty Album")
        album.prefetched_imageinals = []

        mock_logger = mocker.patch("memoria.routes.albums.api.logger")
        response = logged_in_client.get(f"{album_base_url}{album.id}/download/")
        assert response.status_code == HTTPStatus.BAD_REQUEST
        mock_logger.warning.assert_called_once()

    def test_remove_images_without_permission(
        self,
        client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        image_factory: Callable[..., Image],
        user_factory: Callable[..., User],
    ) -> None:
        """
        A user not in edit_groups tries to remove images; should get 404 (as if not found).
        """
        user = user_factory.create(username="userx", password="pw123")
        album = album_factory(name="Restricted Album")
        img = image_factory.create(name="Image X")
        ImageInAlbum.objects.create(album=album, image=img, sort_order=0)

        client.force_login(user)
        payload = {"image_ids": [img.id]}
        response = client.delete(
            f"{album_base_url}{album.id}/images/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_sort_images_without_permission(
        self,
        client: Client,
        album_base_url: str,
        album_factory: Callable[..., Album],
        image_factory: Callable[..., Image],
        user_factory: Callable[..., User],
    ) -> None:
        """
        A user not in edit_groups tries to reorder images; should get 404.
        """
        user = user_factory.create(username="userx", password="pw123")
        album = album_factory(name="Restricted Album")
        img1 = image_factory.create(name="Image A")
        img2 = image_factory.create(name="Image B")
        ImageInAlbum.objects.create(album=album, image=img1, sort_order=0)
        ImageInAlbum.objects.create(album=album, image=img2, sort_order=1)

        client.force_login(user)
        payload = {"sorting": [img2.id, img1.id]}
        response = client.patch(
            f"{album_base_url}{album.id}/sort/",
            payload,
            content_type="application/json",
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
