import pytest
from django.core.management import call_command

from memoria.models import Image
from memoria.models import RoughDate


@pytest.mark.usefixtures("sample_image_environment")
@pytest.mark.django_db
class TestSyncCommand:
    def test_sync_command(self):
        img = Image.objects.get(pk=1)

        assert img is not None
        assert not img.is_dirty

        img.description = "This is a new, changed, neat description"
        img.save()
        img.refresh_from_db()

        assert img.is_dirty

        call_command("sync")

        img.refresh_from_db()

        assert not img.is_dirty

    @pytest.mark.parametrize(
        ("subdivision", "city", "sublocation"),
        [
            ("US-DC", "Washington D.C.", "White House"),
            ("US-WA", None, None),
            (None, None, None),
        ],
    )
    def test_sync_less_location(self, subdivision: str | None, city: str | None, sublocation: str | None) -> None:
        img = Image.objects.get(pk=1)

        assert img is not None
        assert not img.is_dirty

        old_location = img.location

        assert old_location is not None
        old_location.subdivision_code = subdivision
        old_location.city = city
        old_location.sub_location = sublocation
        old_location.save()

        img.refresh_from_db()

        assert img.is_dirty

        call_command("sync")

        img.refresh_from_db()

        assert not img.is_dirty

    @pytest.mark.parametrize(
        ("month_valid", "day_valid"),
        [(True, True), (True, False), (False, False)],
    )
    def test_sync_less_date(self, *, month_valid: bool, day_valid: bool) -> None:
        img = Image.objects.get(pk=2)

        assert img is not None
        assert not img.is_dirty

        old_date = RoughDate.objects.get(pk=1)

        assert old_date is not None
        old_date.month_valid = month_valid
        old_date.day_valid = day_valid
        old_date.save()
        img.date = old_date
        img.save()

        img.refresh_from_db()

        assert img.is_dirty

        call_command("sync")

        img.refresh_from_db()

        assert not img.is_dirty
