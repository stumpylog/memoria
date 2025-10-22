import dataclasses
import logging
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Annotated

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
from memoria.models import SiteSettings
from memoria.tasks.images import index_changed_image
from memoria.tasks.images import index_moved_image
from memoria.tasks.images import index_new_images
from memoria.tasks.models import ImageIndexTaskModel
from memoria.tasks.models import ImageMovedTaskModel
from memoria.tasks.models import ImageReplaceTaskModel
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
        root_dir: Annotated[
            Path,
            Option("--root-dir", help="Set the root directory for folder structure"),
        ],
        paths: Annotated[list[Path], Argument(help="The paths to index for new images")],
        hash_threads: Annotated[int, Option(help="Number of threads to use for hashing")] = 4,
        view_group: Annotated[list[str] | None, Option("--view-group", help="Specify view groups")] = None,
        edit_group: Annotated[list[str] | None, Option("--edit-group", help="Specify edit groups")] = None,
        *,
        synchronous: Annotated[bool, Option(help="If True, run the indexing in the same process")] = True,
        overwrite: Annotated[
            bool,
            Option(help="If True, overwrite values on existing images with the new ones"),
        ] = False,
    ) -> None:
        # TODO: Configure BATCH_SIZE via SiteSettings
        # TODO: Config root-dir via SiteSettings

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

        found_images.sort()

        # Get all existing images for comparison
        existing_images = Image.objects.all()
        existing_by_hash: dict[str, Image] = {}
        existing_by_path: dict[Path, Image] = {}

        for img in existing_images:
            if TYPE_CHECKING:
                assert isinstance(img, Image)
            if img.original_checksum:
                existing_by_hash[img.original_checksum] = img
            if img.original_path:
                existing_by_path[img.original_path] = img

        # Categorize images based on the four scenarios
        new_images: list[FoundImage] = []  # Scenario 3: Unknown checksum and path
        moved_images: list[tuple[FoundImage, Image]] = []  # Scenario 2: Checksum changed, path known
        changed_images: list[tuple[FoundImage, Image]] = []  # Scenario 1: Path known, checksum changed
        unchanged_images: list[tuple[FoundImage, Image]] = []  # Scenario 4: No action needed

        for found_image in found_images:
            checksum_match = existing_by_hash.get(found_image.checksum)
            path_match = existing_by_path.get(found_image.image_path)

            if checksum_match and path_match and checksum_match == path_match:
                # Both checksum and path match the same image - no changes needed
                unchanged_images.append((found_image, checksum_match))
            elif path_match and not checksum_match:
                # Path exists but checksum is different - image content changed
                changed_images.append((found_image, path_match))
            elif checksum_match and not path_match:
                # Checksum exists but path is different - image moved
                moved_images.append((found_image, checksum_match))
            else:
                # Neither checksum nor path match - new image
                new_images.append(found_image)

        # Log what we found
        logger.info(f"Found {len(new_images)} new images to index")
        logger.info(f"Found {len(changed_images)} images with changed content")
        logger.info(f"Found {len(moved_images)} images that have moved")
        logger.info(f"Found {len(unchanged_images)} images with no changes")

        site_settings = SiteSettings.objects.first()
        if TYPE_CHECKING:
            assert site_settings is not None

        # Process new images (Scenario 3)
        if new_images:
            if not synchronous:
                logger.info("Starting async task for new images")
            self._process_new_images(
                new_images,
                root_dir,
                view_groups,
                edit_groups,
                hash_threads,
                site_settings,
                synchronous=synchronous,
            )

        # Process changed images (Scenario 1)
        if changed_images:
            if not synchronous:
                logger.info("Starting async task for changed images")
            self._process_changed_images(
                changed_images,
                root_dir,
                view_groups,
                edit_groups,
                site_settings,
                synchronous=synchronous,
            )

        # Process moved images (Scenario 2)
        if moved_images:
            if not synchronous:
                logger.info("Starting async task for moved images")
            self._process_moved_images(
                moved_images,
                root_dir,
                view_groups,
                edit_groups,
                overwrite=overwrite,
                synchronous=synchronous,
            )

    def _process_new_images(
        self,
        new_images: list[FoundImage],
        root_dir: Path,
        view_groups: QuerySet[Group] | None,
        edit_groups: QuerySet[Group] | None,
        hash_threads: int,
        site_settings: SiteSettings,
        *,
        synchronous: bool,
    ) -> None:
        """
        Process completely new images.
        """
        for i in range(0, len(new_images), BATCH_SIZE):
            batch = new_images[i : i + BATCH_SIZE]
            batch_packages = []

            for found_image in sorted(batch):
                pkg = ImageIndexTaskModel(
                    root_dir=root_dir.resolve(),
                    image_path=found_image.image_path,
                    original_hash=found_image.checksum,
                    logger=logger,
                    view_groups=view_groups,
                    edit_groups=edit_groups,
                    hash_threads=hash_threads,
                    synchronous=synchronous,
                    thumbnail_size=site_settings.thumbnail_max_size,
                    large_image_size=site_settings.large_image_max_size,
                    large_image_quality=site_settings.large_image_quality,
                )
                batch_packages.append(pkg)

            if synchronous:
                index_new_images.call_local(batch_packages)
            else:  # pragma: no cover
                index_new_images(batch_packages)

    def _process_changed_images(
        self,
        changed_images: list[tuple[FoundImage, Image]],
        root_dir: Path,
        view_groups: QuerySet[Group] | None,
        edit_groups: QuerySet[Group] | None,
        site_settings: SiteSettings,
        *,
        synchronous: bool,
    ) -> None:
        """
        Process images where the path is known but checksum has changed.
        """
        for i in range(0, len(changed_images), BATCH_SIZE):
            batch = changed_images[i : i + BATCH_SIZE]
            batch_packages = []

            for found_image, existing_image in batch:
                pkg = ImageReplaceTaskModel(
                    root_dir=root_dir.resolve(),
                    image_id=existing_image.pk,
                    image_path=found_image.image_path,
                    logger=logger,
                    view_groups=view_groups,
                    edit_groups=edit_groups,
                    thumbnail_size=site_settings.thumbnail_max_size,
                    large_image_size=site_settings.large_image_max_size,
                    large_image_quality=site_settings.large_image_quality,
                )
                batch_packages.append(pkg)

            if synchronous:
                index_changed_image.call_local(batch_packages)
            else:  # pragma: no cover
                index_changed_image(batch_packages)

    def _process_moved_images(
        self,
        moved_images: list[tuple[FoundImage, Image]],
        root_dir: Path,
        view_groups: QuerySet[Group] | None,
        edit_groups: QuerySet[Group] | None,
        *,
        overwrite: bool,
        synchronous: bool,
    ) -> None:
        """
        Process images where the checksum is known but path has changed.
        """
        for i in range(0, len(moved_images), BATCH_SIZE):
            batch = moved_images[i : i + BATCH_SIZE]
            batch_packages = []

            for found_image, existing_image in batch:
                pkg = ImageMovedTaskModel(
                    root_dir=root_dir.resolve(),
                    image_path=found_image.image_path,
                    image_id=existing_image.pk,
                    logger=logger,
                    view_groups=view_groups,
                    edit_groups=edit_groups,
                    overwrite=overwrite,
                )
                batch_packages.append(pkg)

            if synchronous:
                index_moved_image.call_local(batch_packages)
            else:  # pragma: no cover
                index_moved_image(batch_packages)
