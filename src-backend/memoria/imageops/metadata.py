from datetime import date
from typing import TYPE_CHECKING
from typing import Final

from exifmwg import ImageMetadata
from exifmwg import Keyword as KeywordStruct
from exifmwg import Region as RegionStruct

from memoria.models import Image as ImageModel
from memoria.models import ImageFolder
from memoria.models import Person
from memoria.models import PersonInImage
from memoria.models import Pet
from memoria.models import PetInImage
from memoria.models import RoughDate
from memoria.models import RoughLocation
from memoria.models import Tag
from memoria.models import TagOnImage
from memoria.models.abstract import ObjectPermissionModelMixin
from memoria.tasks.models import ImageIndexTaskModel
from memoria.tasks.models import ImageMovedTaskModel
from memoria.tasks.models import ImageReplaceTaskModel
from memoria.utils.constants import DATE_KEYWORD
from memoria.utils.constants import LOCATION_KEYWORD
from memoria.utils.constants import PEOPLE_KEYWORD
from memoria.utils.constants import PET_KEYWORD
from memoria.utils.geo import get_country_code_from_name
from memoria.utils.geo import get_subdivision_code_from_name


def handle_view_edit_groups(
    pkg: ImageIndexTaskModel | ImageMovedTaskModel | ImageReplaceTaskModel,
    db_object: ObjectPermissionModelMixin,
    *,
    was_created: bool,
):
    """
    Handles the adding or setting of edit and view groups on created or existing models with permission groups
    """
    if pkg.view_groups:
        if was_created:
            db_object.view_groups.set(pkg.view_groups.all())
        else:
            db_object.view_groups.add(*pkg.view_groups.all())
    if pkg.edit_groups:
        if was_created:
            db_object.edit_groups.set(pkg.edit_groups.all())
        else:
            db_object.edit_groups.add(*pkg.edit_groups.all())


def update_image_people_and_pets(
    pkg: ImageIndexTaskModel | ImageMovedTaskModel | ImageReplaceTaskModel,
    image_to_update: ImageModel,
    metadata: ImageMetadata,
):
    """
    Parses MWG regions into people and pets.

    Processes each region in the metadata and creates corresponding database records
    for people and pets identified in the image with their position information.
    """
    if TYPE_CHECKING:
        assert pkg.logger is not None

    pkg.logger.info("  Parsing regions")

    def _process_person_region(region: RegionStruct):
        """
        Helper function to process a person/face region
        """
        if TYPE_CHECKING:
            assert pkg.logger is not None
        person, created = Person.objects.get_or_create(name=region.name.strip())

        handle_view_edit_groups(pkg, person, was_created=created)

        # TODO: This should be on the PersonInImage, as it might differ between pictures, but currently nothing sets this
        if region.description:
            person.description = region.description
            person.save()

        pkg.logger.info(f"      Found face for person {person.name}")
        if created:
            pkg.logger.debug("      Created new Person")

        PersonInImage.objects.create(
            person=person,
            image=image_to_update,
            center_x=region.area.x,
            center_y=region.area.y,
            height=region.area.h,
            width=region.area.w,
        )

    def _process_pet_region(region: RegionStruct):
        """
        Helper function to process a pet region
        """
        if TYPE_CHECKING:
            assert pkg.logger is not None
        pet, created = Pet.objects.get_or_create(name=region.name)

        handle_view_edit_groups(pkg, pet, was_created=created)

        if region.description:
            pet.description = region.description
            pet.save()

        pkg.logger.info(f"      Found box for pet {pet.name}")
        if created:
            pkg.logger.debug("      Created new Pet")

        PetInImage.objects.create(
            pet=pet,
            image=image_to_update,
            center_x=region.area.x,
            center_y=region.area.y,
            height=region.area.h,
            width=region.area.w,
        )

    if not metadata.region_info or not metadata.region_info.region_list:
        pkg.logger.debug("    No regions found in metadata")
        return

    for region in metadata.region_info.region_list:
        if not region.name:
            pkg.logger.warning("    Skipping region with empty Name")
            continue

        match region.type:
            case "Face":
                _process_person_region(region)
            case "Pet":
                _process_pet_region(region)
            case _:
                pkg.logger.warning(f"    Skipping region of type {region.type}")


def update_image_keyword_tree(
    pkg: ImageIndexTaskModel | ImageMovedTaskModel | ImageReplaceTaskModel,
    image_to_update: ImageModel,
    metadata: ImageMetadata,
):
    """
    Creates database Tags from the MWG keyword struct
    """
    if TYPE_CHECKING:
        assert pkg.logger is not None

    pkg.logger.info("  Parsing keywords")

    def maybe_create_tag_tree(
        image_instance: ImageModel,
        parent: Tag,
        tree_node: KeywordStruct,
    ):
        existing_node, _ = Tag.objects.get_or_create(
            name=tree_node.keyword,
            tn_parent=parent,
        )

        applied_value = False
        # If the keyword is applied, then it is applied
        if tree_node.applied is not None and tree_node.applied:
            applied_value = True
        # If the keyword is not applied, but this is a leaf, it is applied
        if not applied_value and not len(tree_node.children):
            applied_value = True

        TagOnImage.objects.create(tag=existing_node, image=image_to_update, applied=applied_value)

        # Process children
        for node_child in tree_node.children:
            maybe_create_tag_tree(image_instance, existing_node, node_child)

    if metadata.keyword_info:
        for keyword in metadata.keyword_info.hierarchy:
            # Skip keywords with dedicated processing
            if keyword.keyword.lower() in {
                PEOPLE_KEYWORD.lower(),
                DATE_KEYWORD.lower(),
                LOCATION_KEYWORD.lower(),
                PET_KEYWORD.lower(),
            }:
                continue
            existing_root_tag, _ = Tag.objects.get_or_create(name=keyword.keyword, tn_parent=None)
            applied_value = False
            # If the keyword is applied, then it is applied
            if keyword.applied is not None and keyword.applied:
                applied_value = True
            # If the keyword is not applied, but this is a leaf, it is applied
            if not applied_value and not len(keyword.children):
                applied_value = True
            TagOnImage.objects.create(tag=existing_root_tag, image=image_to_update, applied=applied_value)

            # Process any children
            for child in keyword.children:
                maybe_create_tag_tree(image_to_update, existing_root_tag, child)
    else:  # pragma: no cover
        pkg.logger.info("    No keywords")


def update_image_location_from_mwg(
    pkg: ImageIndexTaskModel | ImageMovedTaskModel | ImageReplaceTaskModel,
    image_to_update: ImageModel,
    metadata: ImageMetadata,
):
    """
    Creates a RoughLocation from ImageMetadata and associates it with the image.

    Processes country, subdivision (state), city, and sub-location data from metadata.
    Attempts to resolve standard codes for countries and subdivisions.
    """

    if TYPE_CHECKING:
        assert pkg.logger is not None

    if not metadata.country:
        pkg.logger.info("    No country set, will try keywords")
        return

    if "-" in metadata.country:
        country_alpha_2, _ = metadata.country.split("-")
        country_alpha_2 = country_alpha_2.strip()
    else:
        country_alpha_2 = get_country_code_from_name(metadata.country)
    if not country_alpha_2:
        pkg.logger.warning(f"    No country code found for: {metadata.country}")
        return

    pkg.logger.info(f"    Got country {country_alpha_2} from {metadata.country}")

    # Process subdivision (state) if available
    subdivision_code = None
    if metadata.state:
        # We expect Code - Name, ie: US-HI - Hawaii, even though this isn't quite the standard, which requires just Code
        if "-" in metadata.state:
            subdivision_code, _ = metadata.state.split("-")
            subdivision_code = subdivision_code.strip()
            pkg.logger.info(f"    Got subdivision code {subdivision_code} from {metadata.state}")
        else:
            pkg.logger.warning(f"    No subdivision code found for: {metadata.state}")

    # Create or retrieve location record
    location, created = RoughLocation.objects.get_or_create(
        country_code=country_alpha_2,
        subdivision_code=subdivision_code,
        city=metadata.city.strip() if metadata.city else metadata.city,
        sub_location=metadata.location.strip() if metadata.location else metadata.location,
    )

    # Update image with location
    image_to_update.location = location
    image_to_update.save()

    if created:
        pkg.logger.debug(f"    Created new RoughLocation: {location}")
    else:
        pkg.logger.debug(f"    Using existing RoughLocation: {location}")
    pkg.logger.info(f"    Location is {location}")


def update_image_location_from_keywords(
    pkg: ImageIndexTaskModel | ImageMovedTaskModel | ImageReplaceTaskModel,
    image_to_update: ImageModel,
    metadata: ImageMetadata,
):
    """
    Parses location information from metadata keywords when MWG location is not set.

    Expects keyword hierarchy:
    - Locations
        - Country Name
        - Subdivision Name
            - City Name
                - Sub-location Name

    If subdivision doesn't match a known region within the country, it's treated as a city.
    """
    if TYPE_CHECKING:
        assert pkg.logger is not None

    if not metadata.keyword_info:
        return

    location_tree = None
    for root in metadata.keyword_info.hierarchy:
        if root.keyword == LOCATION_KEYWORD:
            location_tree = root
            break

    if not location_tree or not location_tree.children:
        return

    # Extract country information
    country_node = location_tree.children[0]
    country_alpha2 = get_country_code_from_name(country_node.keyword)
    if not country_alpha2:
        pkg.logger.debug(f"    Could not find country code for: {country_node.keyword}")
        return

    # Initialize location components
    subdivision_code = None
    city = None
    sub_location = None

    # Process subdivision/city information
    if country_node.children:
        subdivision_node = country_node.children[0]
        subdivision_code = get_subdivision_code_from_name(
            country_alpha2,
            subdivision_node.keyword,
        )

        if not subdivision_code:
            # No matching subdivision - treat as city
            city = subdivision_node.keyword.strip()
        elif subdivision_node.children:
            # Use first child as city
            city_node = subdivision_node.children[0]
            city = city_node.keyword.strip()

            # Extract sub-location if present
            if city_node.children:
                sub_location = city_node.children[0].keyword.strip()

    pkg.logger.info(f"    Setting {country_alpha2} - {subdivision_code} - {city} - {sub_location}")

    # Create or retrieve location record
    location, created = RoughLocation.objects.get_or_create(
        country_code=country_alpha2,
        subdivision_code=subdivision_code,
        city=city,
        sub_location=sub_location,
    )

    image_to_update.location = location
    image_to_update.save()

    if created:
        pkg.logger.debug(f"    Created new RoughLocation: {location}")
    else:
        pkg.logger.debug(f"    Using existing RoughLocation: {location}")
    pkg.logger.info(f"    Set location as {location}")


def update_image_date_from_keywords(
    pkg: ImageIndexTaskModel | ImageMovedTaskModel | ImageReplaceTaskModel,
    image_to_update: ImageModel,
    metadata: ImageMetadata,
):
    """
    Extracts date information from image metadata keywords with a hierarchical structure.

    Structure format:
    - Dates and Times
        - 1980          # Year
        - 12 - December # Month
            - 25        # Day
    Raises:
        No exceptions raised - failures are logged
    """
    if TYPE_CHECKING:
        assert pkg.logger is not None

    # Early return if no keyword info available
    if not metadata.keyword_info:
        return

    # Get date and time tree
    date_and_time_tree = None
    for root in metadata.keyword_info.hierarchy:
        if root.keyword == DATE_KEYWORD:
            date_and_time_tree = root
            break

    if not date_and_time_tree or not date_and_time_tree.children:
        return

    year_node = date_and_time_tree.children[0]

    # Default values
    year = None
    month = None
    day = None

    # Try to parse year
    try:
        year = int(year_node.keyword)
    except ValueError:
        pkg.logger.warning(f"    Failed to parse year from keyword: {year_node.keyword}")
        return

    # Try to parse month if available
    if year_node.children:
        month_node = year_node.children[0]
        try:
            # Extract first part before dash if present
            month_parts = month_node.keyword.split("-")
            month = int(month_parts[0].strip())
        except (ValueError, IndexError):
            pkg.logger.warning(f"    Could not parse month from: {month_node.keyword}")

        # Try to parse day if month is valid and day node exists
        if month is not None and month_node.children:
            day_node = month_node.children[0]
            try:
                day = int(day_node.keyword)
            except ValueError:
                pkg.logger.warning(f"    Could not parse day from: {day_node.keyword}")

    # Validate date ranges
    if month is not None and not (1 <= month <= 12):
        pkg.logger.warning(f"    Invalid month value: {month}")
        month = None

    max_days: Final[dict[int, int]] = {
        1: 31,
        2: 29,
        3: 31,
        4: 30,
        5: 31,
        6: 30,
        7: 31,
        8: 31,
        9: 30,
        10: 31,
        11: 30,
        12: 31,
    }
    if day is not None and month is not None and not (1 <= day <= max_days.get(month, 31)):
        pkg.logger.warning(f"    Invalid day value: {day}")
        day = None
    rough_date, created = RoughDate.objects.get_or_create(
        year=year,
        month=month,
        day=day,
        comparison_date=date(year, month or 1, day or 1),
    )
    if created:
        pkg.logger.debug(f"    Created new RoughDate: {rough_date}")
    else:
        pkg.logger.debug(f"    Using existing RoughDate: {rough_date}")
    pkg.logger.info(f"    Set rough date of {rough_date}")
    image_to_update.date = rough_date
    image_to_update.save()


def update_image_folder_structure(pkg: ImageIndexTaskModel | ImageMovedTaskModel | ImageReplaceTaskModel):
    """
    Builds a folder structure, according to the relation from the image, to the top level directory

    Returns the ImageFolder containing the image
    """
    if TYPE_CHECKING:
        assert pkg.logger is not None

    # TODO: Handle a replace/move better here
    path_from_parent = pkg.image_path.relative_to(pkg.root_dir).parent
    parent, created = ImageFolder.objects.get_or_create(name=path_from_parent.parts[0], tn_parent=None)
    handle_view_edit_groups(pkg, parent, was_created=created)
    if created:
        pkg.logger.info(f"  Created new parent folder: {parent.name}")
    else:
        pkg.logger.info(f"  Using existing parent folder: {parent.name}")
    for depth, child_name in enumerate(path_from_parent.parts[1:]):
        child, created = ImageFolder.objects.get_or_create(name=child_name, tn_parent=parent)
        handle_view_edit_groups(pkg, child, was_created=created)
        if created:
            pkg.logger.info(f"  {' ' * (depth + 2)}Created new child folder: {child.name}")
        else:
            pkg.logger.info(f"  {' ' * (depth + 2)}Using existing child folder: {child.name}")
        parent = child
    return parent
