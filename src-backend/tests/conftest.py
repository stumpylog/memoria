import logging
import random
import shutil
from pathlib import Path

import pytest
from django.core.management import call_command
from django.db import models

from memoria.models import Image
from memoria.models import Person
from memoria.models import Pet
from memoria.models import RoughDate
from memoria.models import RoughLocation
from memoria.signals.handlers import mark_image_as_dirty
from memoria.signals.handlers import mark_images_as_dirty_on_fk_change
from memoria.signals.handlers import mark_images_as_dirty_on_m2m_change
from tests.types import DjangoDirectories
from tests.types import SampleFile
from tests.utils import disable_signal

logging.getLogger("faker").setLevel(logging.ERROR)
logging.getLogger("factory.generate").setLevel(logging.ERROR)


@pytest.fixture(scope="session", autouse=True)
def faker_seed():
    return 0


@pytest.fixture(scope="session", autouse=True)
def _seed_random():
    random.seed(0)


@pytest.fixture(scope="session")
def api_base_url() -> str:
    return "/api/"


@pytest.fixture(scope="session")
def album_base_url(api_base_url: str) -> str:
    return api_base_url + "album/"


@pytest.fixture(scope="session")
def users_base_url(api_base_url: str) -> str:
    return api_base_url + "user/"


@pytest.fixture(scope="session")
def fixture_directory() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_db_fixture_file(fixture_directory: Path) -> Path:
    return fixture_directory / "indexed_sample_database.json"


@pytest.fixture(scope="session")
def sample_directory() -> Path:
    return Path(__file__).parent / "samples"


@pytest.fixture(scope="session")
def image_sample_directory(sample_directory: Path) -> Path:
    return sample_directory / "images"


@pytest.fixture(scope="session")
def image_originals_directory(image_sample_directory: Path) -> Path:
    return image_sample_directory / "originals"


@pytest.fixture(scope="session")
def image_full_size_directory(image_sample_directory: Path) -> Path:
    return image_sample_directory / "fullsize"


@pytest.fixture(scope="session")
def image_thumbnail_directory(image_sample_directory: Path) -> Path:
    return image_sample_directory / "thumbnails"


@pytest.fixture(scope="session")
def sample_one_original_file(image_originals_directory: Path) -> Path:
    return image_originals_directory / "sample1.jpg"


@pytest.fixture(scope="session")
def sample_one_full_size_file(image_full_size_directory: Path) -> Path:
    return image_full_size_directory / "0000000001.webp"


@pytest.fixture(scope="session")
def sample_one_thumbnail_file(image_thumbnail_directory: Path) -> Path:
    return image_thumbnail_directory / "0000000001.webp"


@pytest.fixture(scope="session")
def sample_one_info(
    sample_one_original_file: Path,
    sample_one_full_size_file: Path,
    sample_one_thumbnail_file: Path,
) -> SampleFile:
    return SampleFile(sample_one_original_file, sample_one_full_size_file, sample_one_thumbnail_file)


@pytest.fixture
def sample_one_original_copy(tmp_path: Path, sample_one_original_file: Path) -> Path:
    return Path(shutil.copy(sample_one_original_file, tmp_path))


@pytest.fixture(scope="session")
def sample_two_original_file(image_originals_directory: Path) -> Path:
    return image_originals_directory / "sample2.jpg"


@pytest.fixture(scope="session")
def sample_two_full_size_file(image_full_size_directory: Path) -> Path:
    return image_full_size_directory / "0000000002.webp"


@pytest.fixture(scope="session")
def sample_two_thumbnail_file(image_thumbnail_directory: Path) -> Path:
    return image_thumbnail_directory / "0000000002.webp"


@pytest.fixture(scope="session")
def sample_two_info(
    sample_two_original_file: Path,
    sample_two_full_size_file: Path,
    sample_two_thumbnail_file: Path,
) -> SampleFile:
    return SampleFile(sample_two_original_file, sample_two_full_size_file, sample_two_thumbnail_file)


@pytest.fixture
def sample_two_original_copy(tmp_path: Path, sample_two_original_file: Path) -> Path:
    return Path(shutil.copy(sample_two_original_file, tmp_path))


@pytest.fixture(scope="session")
def sample_three_original_file(image_originals_directory: Path) -> Path:
    return image_originals_directory / "sample3.jpg"


@pytest.fixture(scope="session")
def sample_three_full_size_file(image_full_size_directory: Path) -> Path:
    return image_full_size_directory / "0000000003.webp"


@pytest.fixture(scope="session")
def sample_three_thumbnail_file(image_thumbnail_directory: Path) -> Path:
    return image_thumbnail_directory / "0000000003.webp"


@pytest.fixture(scope="session")
def sample_three_info(
    sample_three_original_file: Path,
    sample_three_full_size_file: Path,
    sample_three_thumbnail_file: Path,
) -> SampleFile:
    return SampleFile(sample_three_original_file, sample_three_full_size_file, sample_three_thumbnail_file)


@pytest.fixture
def sample_three_original_copy(tmp_path: Path, sample_three_original_file: Path) -> Path:
    return Path(shutil.copy(sample_three_original_file, tmp_path))


@pytest.fixture(scope="session")
def sample_four_original_file(image_originals_directory: Path) -> Path:
    return image_originals_directory / "sample4.jpg"


@pytest.fixture(scope="session")
def sample_four_full_size_file(image_full_size_directory: Path) -> Path:
    return image_full_size_directory / "0000000004.webp"


@pytest.fixture(scope="session")
def sample_four_thumbnail_file(image_thumbnail_directory: Path) -> Path:
    return image_thumbnail_directory / "0000000004.webp"


@pytest.fixture(scope="session")
def sample_four_info(
    sample_four_original_file: Path,
    sample_four_full_size_file: Path,
    sample_four_thumbnail_file: Path,
) -> SampleFile:
    return SampleFile(sample_four_original_file, sample_four_full_size_file, sample_four_thumbnail_file)


@pytest.fixture
def sample_four_original_copy(tmp_path: Path, sample_four_original_file: Path) -> Path:
    return Path(shutil.copy(sample_four_original_file, tmp_path))


@pytest.fixture
def all_samples_copy(
    tmp_path: Path,
    sample_one_original_file: Path,
    sample_two_original_file: Path,
    sample_three_original_file: Path,
    sample_four_original_file: Path,
) -> tuple[Path, list[Path]]:
    return tmp_path, [
        shutil.copy(sample_one_original_file, tmp_path),
        shutil.copy(sample_two_original_file, tmp_path),
        shutil.copy(sample_three_original_file, tmp_path),
        shutil.copy(sample_four_original_file, tmp_path),
    ]


@pytest.fixture
def django_directories(tmp_path: Path) -> DjangoDirectories:
    """
    Configures an object with the directories used by Django for testing purposes.

    Child directories will be created automatically if they do not exist.
    """
    return DjangoDirectories(base_dir=tmp_path)


@pytest.fixture(name="django_directories_override")
def _django_directories_settings_override(django_directories: DjangoDirectories, settings):
    """
    Configures Django settings for testing purposes
    """
    settings.BASE_DIR = django_directories.base_dir
    settings.DATA_DIR = django_directories.data_dir
    settings.LOGGING_DIR = django_directories.logs_dir
    settings.MEDIA_ROOT = django_directories.media_dir
    settings.THUMBNAIL_DIR = django_directories.thumbnail_dir
    settings.FULL_SIZE_DIR = django_directories.full_size_dir


@pytest.fixture(name="sample_image_database")
def _sample_image_database(sample_db_fixture_file: Path) -> None:
    """
    Configures a partial environment of samples, including only the database loaded from fixture
    """
    with (
        disable_signal(models.signals.post_save, mark_image_as_dirty, Image),
        disable_signal(models.signals.post_save, mark_images_as_dirty_on_m2m_change, Pet),
        disable_signal(models.signals.post_save, mark_images_as_dirty_on_m2m_change, Person),
        disable_signal(models.signals.post_save, mark_images_as_dirty_on_fk_change, RoughLocation),
        disable_signal(models.signals.post_save, mark_images_as_dirty_on_fk_change, RoughDate),
    ):
        call_command("loaddata", "--verbosity", "0", "--skip-checks", sample_db_fixture_file)


@pytest.fixture(name="sample_image_environment")
def _sample_image_environment(
    sample_image_database,
    django_directories_override,
    django_directories: DjangoDirectories,
    sample_one_info: SampleFile,
    sample_two_info: SampleFile,
    sample_three_info: SampleFile,
    sample_four_info: SampleFile,
) -> None:
    """
    Configures a full environment of samples, include data base and image files in the proper directories.
    """

    pk_to_image = {
        1: sample_one_info,
        2: sample_two_info,
        3: sample_three_info,
        4: sample_four_info,
    }

    for img in Image.objects.order_by("pk").all():
        sample_info = pk_to_image[img.pk]

        # The original needs to be updated
        img.original_path = shutil.copy(sample_info.original, django_directories.base_dir)
        img.save()
        img.mark_as_clean()

        shutil.copy(sample_info.full_size, django_directories.full_size_dir)
        shutil.copy(sample_info.thumbnail, django_directories.thumbnail_dir)
