import logging
from pathlib import Path
from typing import Annotated
from typing import Final
from typing import Optional

from django.contrib.auth.models import Group
from django.db.models.functions import Lower
from django_typer.management import TyperCommand
from typer import Argument
from typer import Option

from memoria.models import ImageSource
from memoria.tasks.images import index_single_image
from memoria.tasks.models import ImageIndexTaskModel


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
    return Group.objects.filter(name__in=lowercase_names)


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
        logger = logging.getLogger(__name__)

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
            edit_groups = view_groups = get_or_create_groups(edit_group)

        self.image_paths: list[Path] = []

        for path in paths:
            for extension in self.IMAGE_EXTENSIONS:
                for filename in path.glob(f"**/*{extension}"):
                    self.image_paths.append(filename.resolve())

        logger.info(f"Found {len(self.image_paths)} images to index")

        for image_path in sorted(self.image_paths):
            pkg = ImageIndexTaskModel(
                image_path,
                hash_threads,
                source=img_src,
                view_groups=view_groups,
                edit_groups=edit_groups,
                logger=logger,
            )
            if synchronous:
                index_single_image.call_local(pkg)
            else:  # pragma: no cover
                index_single_image(pkg)
