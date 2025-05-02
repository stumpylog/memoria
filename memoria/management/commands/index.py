import logging
from pathlib import Path
from typing import Annotated
from typing import Final
from typing import Optional

from django.contrib.auth.models import Group
from django.db.models.functions import Lower
from django_typer.management import TyperCommand
from rich.progress import track
from typer import Argument
from typer import Option

from memoria.models import Image
from memoria.models import ImageSource
from memoria.tasks.images import index_image_batch
from memoria.tasks.images import index_update_existing_images
from memoria.tasks.models import ImageIndexTaskModel
from memoria.tasks.models import ImageUpdateTaskModel
from memoria.utils import calculate_blake3_hash


def get_or_create_groups(group_names: list[str]):
    # Convert all names to lowercase for case-insensitive comparison
    lowercase_names = [name.lower().strip() for name in group_names]

    # Get existing groups with case-insensitive query
    existing_groups = {
        group.name.lower(): group
        for group in Group.objects.annotate(
            lower_name=Lower("name"),
        ).filter(
            lower_name__in=lowercase_names,
        )
    }

    # Create groups that don't exist
    groups_to_create = []
    for name in group_names:
        if name.lower() not in existing_groups:
            groups_to_create.append(Group(name=name))  # noqa: PERF401

    # Bulk create new groups
    if groups_to_create:
        Group.objects.bulk_create(groups_to_create)

    # Return all groups (both existing and newly created)
    return Group.objects.annotate(lower_name=Lower("name")).filter(lower_name__in=lowercase_names)


class Command(TyperCommand):
    help = "Indexes the given path(s) for new Images"

    IMAGE_EXTENSIONS: Final[set[str]] = {
        ".jpg",
        ".jpeg",
        ".png",
        ".tiff",
        ".tif",
        ".webp",
    }

    def handle(
        self,
        paths: Annotated[list[Path], Argument(help="The paths to index for new images")],
        hash_threads: Annotated[int, Option(help="Number of threads to use for hashing")] = 4,
        source: Annotated[
            Optional[str],  # noqa: UP007
            Option(help="The source of the images to attach to the image"),
        ] = None,
        view_group: Annotated[Optional[list[str]], Option("--view-group", help="Specify view groups")] = None,  # noqa: UP007
        edit_group: Annotated[Optional[list[str]], Option("--edit-group", help="Specify edit groups")] = None,  # noqa: UP007
        *,
        synchronous: Annotated[bool, Option(help="If True, run the indexing in the same process")] = True,
    ) -> None:
        logger = logging.getLogger("memoria.index")

        if source:
            img_src, created = ImageSource.objects.get_or_create(name=source)
            if created:
                logger.info(f"Created new source {source}")
            else:
                logger.info(f"Using existing source {source} (#{img_src.pk})")
        else:
            img_src = None

        view_groups = None
        if view_group:
            view_groups = get_or_create_groups(view_group)

        edit_groups = None
        if edit_group:
            edit_groups = get_or_create_groups(edit_group)

        hash_to_path: dict[str, Path] = {}

        all_image_paths: list[Path] = []
        for path in paths:
            for extension in self.IMAGE_EXTENSIONS:
                all_image_paths.extend(path.glob(f"**/*{extension}"))

        all_image_paths = [p.resolve() for p in all_image_paths]

        logger.info(f"Found {len(all_image_paths)} images to consider")

        for image_path in track(all_image_paths, description="Hashing..."):
            image_hash = calculate_blake3_hash(image_path, hash_threads=hash_threads)
            hash_to_path[image_hash] = image_path.resolve()

        existing_images_map = {
            img.original_checksum: img for img in Image.objects.filter(original_checksum__in=hash_to_path.keys())
        }

        self.new_image_paths: dict[str, Path] = {}
        self.existing_images: dict[Path, Image] = {}

        for image_hash, file_path in hash_to_path.items():
            if image_hash in existing_images_map:
                self.existing_images[file_path] = existing_images_map[image_hash]
            else:
                self.new_image_paths[image_hash] = file_path

        logger.info(f"Found {len(self.new_image_paths)} images to index")
        logger.info(f"Found {len(self.existing_images)} images to check for modifications")

        # Process new images in batches of 10
        new_image_hashes = list(self.new_image_paths.keys())
        new_image_paths = list(self.new_image_paths.values())
        for i in range(0, len(self.new_image_paths), 10):
            batch = zip(new_image_hashes[i : i + 10], new_image_paths[i : i + 10], strict=True)
            batch_packages = []

            for image_hash, image_path in sorted(batch, key=lambda x: x[1]):
                pkg = ImageIndexTaskModel(
                    image_path=image_path,
                    original_hash=image_hash,
                    logger=logger,
                    source=img_src,
                    view_groups=view_groups,
                    edit_groups=edit_groups,
                    hash_threads=hash_threads,
                )
                batch_packages.append(pkg)

            if synchronous:
                index_image_batch.call_local(batch_packages)
            else:  # pragma: no cover
                index_image_batch(batch_packages)

        image_paths = list(self.existing_images.keys())
        images = list(self.existing_images.values())
        for i in range(0, len(self.existing_images), 10):
            batch = zip(images[i : i + 10], image_paths[i : i + 10], strict=True)
            batch_packages = []

            for existing_image, image_path in batch:
                pkg = ImageUpdateTaskModel(
                    image_path=image_path,
                    image=existing_image,
                    logger=logger,
                    source=img_src,
                    view_groups=view_groups,
                    edit_groups=edit_groups,
                )
                batch_packages.append(pkg)

            if synchronous:
                index_update_existing_images.call_local(batch_packages)
            else:  # pragma: no cover
                index_update_existing_images(batch_packages)
