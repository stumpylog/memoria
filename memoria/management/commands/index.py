import dataclasses
import logging
from pathlib import Path
from typing import Annotated
from typing import Optional

from django.contrib.auth.models import Group
from django.db.models import QuerySet
from django.db.models.functions import Lower
from django_typer.management import TyperCommand
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn
from rich.progress import TimeElapsedColumn
from typer import Argument
from typer import Option

from memoria.models import Image
from memoria.tasks.images import index_image_batch
from memoria.tasks.images import index_update_existing_images
from memoria.tasks.models import ImageIndexTaskModel
from memoria.tasks.models import ImageUpdateTaskModel
from memoria.utils.constants import BATCH_SIZE
from memoria.utils.constants import IMAGE_EXTENSIONS
from memoria.utils.hashing import calculate_blake3_hash


@dataclasses.dataclass(slots=True, frozen=True, order=True)
class FoundImage:
    original_path: Path
    image_path: Path
    checksum: str


logger = logging.getLogger("memoria.index")


def get_or_create_groups(group_names: list[str]) -> QuerySet[Group]:
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
        logger.info(f"Creating groups: {','.join(x.name for x in groups_to_create)}")
        Group.objects.bulk_create(groups_to_create)

    # Return all groups (both existing and newly created)
    return Group.objects.annotate(lower_name=Lower("name")).filter(lower_name__in=lowercase_names)


class Command(TyperCommand):
    help = "Indexes the given path(s) for new Images"

    def handle(
        self,
        top_level_dir: Annotated[
            Path,
            Option("--top-lvl-dir", help="Set the top level directory for folder structure"),
        ],
        paths: Annotated[list[Path], Argument(help="The paths to index for new images")],
        hash_threads: Annotated[int, Option(help="Number of threads to use for hashing")] = 4,
        view_group: Annotated[Optional[list[str]], Option("--view-group", help="Specify view groups")] = None,  # noqa: UP007
        edit_group: Annotated[Optional[list[str]], Option("--edit-group", help="Specify edit groups")] = None,  # noqa: UP007
        *,
        synchronous: Annotated[bool, Option(help="If True, run the indexing in the same process")] = True,
        overwrite: Annotated[
            bool,
            Option(help="If True, overwrite values on existing images with the new ones"),
        ] = False,
    ) -> None:
        view_groups = None
        if view_group:
            view_groups = get_or_create_groups(view_group)

        edit_groups = None
        if edit_group:
            edit_groups = get_or_create_groups(edit_group)

        found_images: list[FoundImage] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
        ) as progress:
            file_task_id = progress.add_task("", total=None, visible=False)
            for path in [x.resolve() for x in paths]:
                for extension in IMAGE_EXTENSIONS:
                    for image_path in path.rglob(f"*{extension}"):
                        progress.update(
                            file_task_id,
                            description=f"Processing: [green]{image_path.name}[/green]",
                            visible=True,
                        )
                        found_images.append(
                            FoundImage(
                                path,
                                image_path.resolve(),
                                calculate_blake3_hash(image_path, hash_threads=hash_threads),
                            ),
                        )

        hash_to_path: dict[str, FoundImage] = {}
        for image in found_images:
            hash_to_path[image.checksum] = image

        existing_images_map = {
            img.original_checksum: img for img in Image.objects.filter(original_checksum__in=hash_to_path.keys())
        }

        self.new_images: list[FoundImage] = []
        self.existing_images: dict[FoundImage, Image] = {}

        for image_hash, found_image in hash_to_path.items():
            if image_hash in existing_images_map:
                self.existing_images[found_image] = existing_images_map[image_hash]
            else:
                self.new_images.append(found_image)

        logger.info(f"Found {len(self.new_images)} images to index")
        logger.info(f"Found {len(self.existing_images)} images to check for modifications")

        # Process new images in batches
        for i in range(0, len(self.new_images), BATCH_SIZE):
            batch = self.new_images[i : i + BATCH_SIZE]
            batch_packages = []

            for found_image in sorted(batch):
                pkg = ImageIndexTaskModel(
                    root_dir=top_level_dir.resolve(),
                    image_path=found_image.image_path,
                    original_hash=found_image.checksum,
                    logger=logger,
                    view_groups=view_groups,
                    edit_groups=edit_groups,
                    hash_threads=hash_threads,
                )
                batch_packages.append(pkg)

            if synchronous:
                index_image_batch.call_local(batch_packages)
            else:  # pragma: no cover
                index_image_batch(batch_packages)

        images = list(self.existing_images.items())
        for i in range(0, len(self.existing_images), BATCH_SIZE):
            batch = images[i : i + BATCH_SIZE]
            batch_packages = []

            for found_image, existing_image in batch:
                pkg = ImageUpdateTaskModel(
                    root_dir=top_level_dir.resolve(),
                    image_path=found_image.image_path,
                    image=existing_image,
                    logger=logger,
                    view_groups=view_groups,
                    edit_groups=edit_groups,
                    overwrite=overwrite,
                )
                batch_packages.append(pkg)

            if synchronous:
                index_update_existing_images.call_local(batch_packages)
            else:  # pragma: no cover
                index_update_existing_images(batch_packages)
