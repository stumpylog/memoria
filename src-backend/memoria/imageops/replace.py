from exifmwg import ExifTool

from memoria.imageops.metadata import update_image_date_from_keywords
from memoria.imageops.metadata import update_image_folder_structure
from memoria.imageops.metadata import update_image_keyword_tree
from memoria.imageops.metadata import update_image_location_from_keywords
from memoria.imageops.metadata import update_image_location_from_mwg
from memoria.imageops.metadata import update_image_people_and_pets
from memoria.tasks.models import ImageReplaceTaskModel


def replace_image_via_path(pkg: ImageReplaceTaskModel, tool: ExifTool) -> None:
    """
    Clears, then maybe replace image metadata
    """

    metadata = tool.read_image_metadata(pkg.image.original_path)

    pkg.image.tags.clear()
    update_image_keyword_tree(pkg, pkg.image, metadata)

    pkg.image.people.clear()
    pkg.image.pets.clear()
    update_image_people_and_pets(pkg, pkg.image, metadata)

    pkg.image.location = None
    update_image_location_from_mwg(pkg, pkg.image, metadata)
    if pkg.image.location is None:
        update_image_location_from_keywords(pkg, pkg.image, metadata)

    pkg.image.folder = update_image_folder_structure(pkg)
    pkg.image.date = None
    update_image_date_from_keywords(pkg, pkg.image, metadata)

    pkg.image.save()
    pkg.image.mark_as_clean()
