import shutil
from pathlib import Path

import pytest
from django.core.management import call_command

from memoria.imageops.metadata import read_image_metadata
from memoria.imageops.metadata import write_image_metadata
from memoria.models import Image
from memoria.models import Person
from memoria.models import PersonInImage
from memoria.models import Pet
from memoria.models import Tag
from memoria.models import TagOnImage


@pytest.mark.django_db
class TestIndexCommand:
    def test_call_command_no_files(self, tmp_path: Path):
        call_command("index", str(tmp_path))

    def test_call_command_single_file(self, sample_one_original_copy: Path):
        call_command("index", str(sample_one_original_copy.parent))

        assert Image.objects.count() == 1
        img = Image.objects.first()
        assert img is not None

        # Check the paths were read correctly
        assert img.original == str(sample_one_original_copy)

        assert img.original_path.exists()
        assert img.original_path.is_file()

        assert img.thumbnail_path.exists()
        assert img.thumbnail_path.is_file()

        assert img.full_size_path.exists()
        assert img.full_size_path.is_file()

        assert img.location is not None
        assert img.location.country_code == "US"
        assert img.location.subdivision_code == "US-DC"
        assert img.location.city == "WASHINGTON"
        assert img.location.sub_location is None

        # Check the person was read correctly
        assert img.people.count() == 1
        assert Image.objects.count() == 1
        person = img.people.first()
        assert person is not None
        assert person.name == "Barack Obama"
        assert person.description is None

        # Check the region box was read
        face_box = PersonInImage.objects.filter(person=person).first()
        assert face_box is not None
        assert face_box.center_x == pytest.approx(0.317383)
        assert face_box.center_y == pytest.approx(0.303075)
        assert face_box.height == pytest.approx(0.0585652)
        assert face_box.width == pytest.approx(0.0292969)

        assert img.tags.count() == 3
        assert Tag.objects.count() == 3
        # Check tag structure\
        # Pet tag tree
        pet_root = Tag.objects.filter(name="Pets").get()
        assert pet_root is not None
        dog_node = Tag.objects.filter(name="Dogs").get()
        assert dog_node is not None
        bo_node = Tag.objects.filter(name="Bo").get()
        assert bo_node is not None

        assert pet_root.parent is None
        assert dog_node.parent == pet_root
        assert bo_node.parent == dog_node

        pet_root_through = TagOnImage.objects.filter(image=img, tag=pet_root).get()
        dog_node_through = TagOnImage.objects.filter(image=img, tag=pet_root).get()
        bo_node_through = TagOnImage.objects.filter(image=img, tag=bo_node).get()
        assert pet_root_through is not None
        assert not pet_root_through.applied
        assert dog_node_through is not None
        assert not dog_node_through.applied
        assert bo_node_through is not None
        assert bo_node_through.applied

    def test_index_command_file_moved(self, sample_one_original_copy: Path, tmp_path_factory: pytest.TempPathFactory):
        call_command("index", str(sample_one_original_copy.parent))

        assert Image.objects.count() == 1
        img = Image.objects.first()
        assert img is not None

        assert img.original == str(sample_one_original_copy)

        new_tmp_path = tmp_path_factory.mktemp("new")

        new_result = shutil.copy(sample_one_original_copy, new_tmp_path / sample_one_original_copy.name)

        call_command("index", str(new_tmp_path))

        assert Image.objects.count() == 1
        img = Image.objects.first()
        assert img is not None

        assert img.original == str(new_result)

    def test_index_command_multiple_files(self, all_samples_copy: tuple[Path, list[Path]]):
        base_dir, sample_images = all_samples_copy

        call_command("index", str(base_dir))

        # 4 images expected
        assert Image.objects.count() == len(sample_images)
        # No duplicated people
        assert Person.objects.count() == 4
        assert Person.objects.filter(name="Barack Obama").exists()
        assert Person.objects.filter(name="Joseph R Biden").exists()
        assert Person.objects.filter(name="Hillary Clinton").exists()
        assert Person.objects.filter(name="Denis McDonough").exists()
        # Present in 4 images
        assert Person.objects.filter(name="Barack Obama").first().images.count() == 4
        # Only in 1 image
        assert Person.objects.filter(name="Hillary Clinton").first().images.count() == 1

    def test_index_command_with_region_description(self, sample_one_original_copy: Path):
        metadata = read_image_metadata(sample_one_original_copy)

        metadata.RegionInfo.RegionList[0].Description = "This is a description of a region"

        write_image_metadata(metadata)

        call_command("index", str(sample_one_original_copy.parent))

        assert Image.objects.count() == 1
        img = Image.objects.first()
        assert img is not None

        # Check the person was read correctly
        assert img.people.count() == 1
        assert Image.objects.count() == 1
        person = img.people.first()
        assert person is not None
        assert person.name == "Barack Obama"
        assert person.description == "This is a description of a region"

    def test_index_command_with_pets(self, sample_one_original_copy: Path):
        call_command("index", str(sample_one_original_copy.parent))

        assert Pet.objects.count() == 1
        instance = Pet.objects.filter(name="Bo").first()
        assert instance is not None
        assert instance.name == "Bo"
        assert instance.description == "Bo was a pet dog of the Obama family"
