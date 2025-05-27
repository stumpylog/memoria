import logging
from typing import Annotated

from django.core.paginator import Paginator
from django_typer.management import TyperCommand
from typer import Option

from memoria.models import Image as ImageModel
from memoria.tasks.images import sync_metadata_to_files
from memoria.utils.constants import BATCH_SIZE

logger = logging.getLogger("memoria.sync")


class Command(TyperCommand):
    help = "Syncs dirty image metadata to the file system"

    def handle(
        self,
        *,
        synchronous: Annotated[bool, Option(help="If True, run the writing in the same process")] = True,
    ):
        paginator = Paginator(
            ImageModel.objects.filter(is_dirty=True)
            .filter(deleted_at__isnull=True)
            .order_by("pk")
            .prefetch_related("location", "date", "people", "pets", "tags")
            .all(),
            BATCH_SIZE,
        )

        for i in paginator.page_range:
            data_chunk: list[ImageModel] = list(paginator.page(i).object_list)
            if synchronous:
                sync_metadata_to_files.call_local(data_chunk)
            else:  # pragma: no cover
                sync_metadata_to_files(data_chunk)
