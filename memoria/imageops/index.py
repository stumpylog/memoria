from datetime import date
from logging import Logger
from typing import TYPE_CHECKING
from typing import Final
from typing import cast

from exifmwg import ExifTool
from exifmwg.models import ImageMetadata
from exifmwg.models import KeywordStruct
from exifmwg.models import RegionStruct

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
from memoria.tasks.models import ImageIndexTaskModel
from memoria.tasks.models import ImageUpdateTaskModel
from memoria.utils import calculate_blake3_hash
from memoria.utils import calculate_image_phash
from memoria.utils import get_country_code_from_name
from memoria.utils import get_subdivision_code_from_name
from memoria.utils.constants import DATE_KEYWORD
from memoria.utils.constants import LOCATION_KEYWORD
from memoria.utils.constants import PEOPLE_KEYWORD
from memoria.utils.photos import generate_image_versions_pyvips


def handle_existing_image(
    pkg: ImageUpdateTaskModel,
) -> None:
    """
    Handles an image that has already been indexed, either updating its source or changing the location
    """
    pkg.logger = cast("Logger", pkg.logger)

    pkg.logger.info("  Image already indexed")
    # Set the source if requested
    # TODO: Set the permissions again??
    # Check for an updated location
    if pkg.image_path.resolve() != pkg.image.original_path:
        pkg.logger.info(f"  Updating path from {pkg.image.original_path.resolve()} to {pkg.image_path.resolve()}")
        pkg.image.original_path = pkg.image_path.resolve()
        pkg.image.save()
    if pkg.image_path.stem != pkg.image.original:
        pkg.image.original = pkg.image_path.stem
        pkg.image.save()

    if pkg.view_groups:
        if pkg.overwrite:
            pkg.image.view_groups.set(pkg.view_groups.all())
        else:
            pkg.image.view_groups.add(*pkg.view_groups.all())
    if pkg.edit_groups:
        if pkg.overwrite:
            pkg.image.edit_groups.set(pkg.edit_groups.all())
        else:
            pkg.image.edit_groups.add(*pkg.edit_groups.all())

    pkg.logger.info(f"  {pkg.image_path.name} indexing completed")


def handle_new_image(pkg: ImageIndexTaskModel, tool: ExifTool) -> None:
    """
    Handles a completely new image
    """

    if TYPE_CHECKING:
        assert pkg.logger is not None

    pkg.logger.info("Processing new image")

    def parse_region_info(new_image: ImageModel, metadata: ImageMetadata):
        """
        Parses MWG regions into people and pets.

        Processes each region in the metadata and creates corresponding database records
        for people and pets identified in the image with their position information.
        """
        if TYPE_CHECKING:
            assert pkg.logger is not None

        pkg.logger.info("  Parsing regions")

        def _process_person_region(image: ImageModel, region: RegionStruct):
            """
            Helper function to process a person/face region
            """
            if TYPE_CHECKING:
                assert pkg.logger is not None
            person, created = Person.objects.get_or_create(name=region.Name)

            if region.Description:
                person.description = region.Description
                person.save()

            pkg.logger.info(f"      Found face for person {person.name}")
            if created:
                pkg.logger.debug("      Created new Person")

            PersonInImage.objects.create(
                person=person,
                image=image,
                center_x=region.Area.X,
                center_y=region.Area.Y,
                height=region.Area.H,
                width=region.Area.W,
            )

        def _process_pet_region(image: ImageModel, region: RegionStruct):
            """
            Helper function to process a pet region
            """
            if TYPE_CHECKING:
                assert pkg.logger is not None
            pet, created = Pet.objects.get_or_create(name=region.Name)

            if region.Description:
                pet.description = region.Description
                pet.save()

            pkg.logger.info(f"      Found box for pet {pet.name}")
            if created:
                pkg.logger.debug("      Created new Pet")

            PetInImage.objects.create(
                pet=pet,
                image=image,
                center_x=region.Area.X,
                center_y=region.Area.Y,
                height=region.Area.H,
                width=region.Area.W,
            )

        if not metadata.RegionInfo or not metadata.RegionInfo.RegionList:
            pkg.logger.debug("    No regions found in metadata")
            return

        for region in metadata.RegionInfo.RegionList:
            if not region.Name:
                pkg.logger.warning("    Skipping region with empty Name")
                continue

            try:
                match region.Type:
                    case "Face":
                        _process_person_region(new_image, region)
                    case "Pet":
                        _process_pet_region(new_image, region)
                    case _:
                        pkg.logger.warning(f"    Skipping region of type {region.Type}")
            except Exception:
                pkg.logger.exception(f"    Error processing region '{region.Name}'")

    def parse_keywords(new_image: ImageModel, metadata: ImageMetadata):
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
                name=tree_node.Keyword,
                tn_parent=parent,
            )

            applied_value = False
            # If the keyword is applied, then it is applied
            if tree_node.Applied is not None and tree_node.Applied:
                applied_value = True
            # If the keyword is not applied, but this is a leaf, it is applied
            if not applied_value and not len(tree_node.Children):
                applied_value = True

            TagOnImage.objects.create(tag=existing_node, image=new_image, applied=applied_value)

            # Process children
            for node_child in tree_node.Children:
                maybe_create_tag_tree(image_instance, existing_node, node_child)

        if metadata.KeywordInfo:
            for keyword in metadata.KeywordInfo.Hierarchy:
                # Skip keywords with dedicated processing
                if keyword.Keyword.lower() in {
                    PEOPLE_KEYWORD.lower(),
                    DATE_KEYWORD.lower(),
                    LOCATION_KEYWORD.lower(),
                }:
                    continue
                existing_root_tag, _ = Tag.objects.get_or_create(name=keyword.Keyword, tn_parent=None)
                applied_value = False
                # If the keyword is applied, then it is applied
                if keyword.Applied is not None and keyword.Applied:
                    applied_value = True
                # If the keyword is not applied, but this is a leaf, it is applied
                if not applied_value and not len(keyword.Children):
                    applied_value = True
                TagOnImage.objects.create(tag=existing_root_tag, image=new_image, applied=applied_value)

                # Process any children
                for child in keyword.Children:
                    maybe_create_tag_tree(new_image, existing_root_tag, child)
        else:  # pragma: no cover
            pkg.logger.info("    No keywords")

    def parse_location(new_image: ImageModel, metadata: ImageMetadata):
        """
        Creates a RoughLocation from ImageMetadata and associates it with the image.

        Processes country, subdivision (state), city, and sub-location data from metadata.
        Attempts to resolve standard codes for countries and subdivisions.
        """

        if TYPE_CHECKING:
            assert pkg.logger is not None

        if not metadata.Country:
            pkg.logger.info("    No country set, will try keywords")
            return

        country_alpha_2 = get_country_code_from_name(metadata.Country)
        if not country_alpha_2:
            pkg.logger.warning(f"    No country code found for: {metadata.Country}")
            return

        pkg.logger.info(f"    Got country {country_alpha_2} from {metadata.Country}")

        # Process subdivision (state) if available
        subdivision_code = None
        if metadata.State:
            subdivision_code = get_subdivision_code_from_name(
                country_alpha_2,
                metadata.State,
            )

            if subdivision_code:
                pkg.logger.info(f"    Got subdivision code {subdivision_code} from {metadata.State}")
            else:
                pkg.logger.warning(f"    No subdivision code found for: {metadata.State}")

        try:
            # Create or retrieve location record
            location, created = RoughLocation.objects.get_or_create(
                country_code=country_alpha_2,
                subdivision_code=subdivision_code,
                city=metadata.City,
                sub_location=metadata.Location,
            )

            # Update image with location
            new_image.location = location
            new_image.save()

            if created:
                pkg.logger.debug(f"    Created new RoughLocation: {location}")
            else:
                pkg.logger.debug(f"    Using existing RoughLocation: {location}")
            pkg.logger.info(f"    Location is {location}")

        except Exception:
            pkg.logger.exception("    Failed to set location")

    def parse_location_from_keywords(new_image: ImageModel, metadata: ImageMetadata):
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

        if not metadata.KeywordInfo:
            return

        location_tree = metadata.KeywordInfo.get_root_by_name(LOCATION_KEYWORD)
        if not location_tree or not location_tree.Children:
            return

        # Extract country information
        country_node = location_tree.Children[0]
        country_alpha2 = get_country_code_from_name(country_node.Keyword)
        if not country_alpha2:
            pkg.logger.debug(f"    Could not find country code for: {country_node.Keyword}")
            return

        # Initialize location components
        subdivision_code = None
        city = None
        sub_location = None

        # Process subdivision/city information
        if country_node.Children:
            subdivision_node = country_node.Children[0]
            subdivision_code = get_subdivision_code_from_name(
                country_alpha2,
                subdivision_node.Keyword,
            )

            if not subdivision_code:
                # No matching subdivision - treat as city
                city = subdivision_node.Keyword
            elif subdivision_node.Children:
                # Use first child as city
                city_node = subdivision_node.Children[0]
                city = city_node.Keyword

                # Extract sub-location if present
                if city_node.Children:
                    sub_location = city_node.Children[0].Keyword

        # Create or retrieve location record
        try:
            location, created = RoughLocation.objects.get_or_create(
                country_code=country_alpha2,
                subdivision_code=subdivision_code,
                city=city,
                sub_location=sub_location,
            )

            new_image.location = location
            new_image.save()

            if created:
                pkg.logger.info(f"    Created new RoughLocation: {location}")
            else:
                pkg.logger.debug(f"    Using existing RoughLocation: {location}")

        except Exception:
            pkg.logger.exception("    Failed to set location")

    def parse_dates_from_keywords(new_image: ImageModel, metadata: ImageMetadata):
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
        if not metadata.KeywordInfo:
            return

        # Get date and time tree
        date_and_time_tree = metadata.KeywordInfo.get_root_by_name(DATE_KEYWORD)
        if not date_and_time_tree or not date_and_time_tree.Children:
            return

        year_node = date_and_time_tree.Children[0]

        # Default values
        year = None
        month = 1
        month_valid = False
        day = 1
        day_valid = False

        # Try to parse year
        try:
            year = int(year_node.Keyword)
        except ValueError:
            pkg.logger.warning(f"    Failed to parse year from keyword: {year_node.Keyword}")
            return

        # Try to parse month if available
        if year_node.Children:
            month_node = year_node.Children[0]
            try:
                # Extract first part before dash if present
                month_parts = month_node.Keyword.split("-")
                month = int(month_parts[0].strip())
                month_valid = True
            except (ValueError, IndexError):
                pkg.logger.warning(f"    Could not parse month from: {month_node.Keyword}")

            # Try to parse day if month is valid and day node exists
            if month_valid and month_node.Children:
                day_node = month_node.Children[0]
                try:
                    day = int(day_node.Keyword)
                    day_valid = True
                except ValueError:
                    pkg.logger.warning(f"    Could not parse day from: {day_node.Keyword}")

        # Validate date ranges
        if not (1 <= month <= 12):
            pkg.logger.warning(f"    Invalid month value: {month}")
            month = 1
            month_valid = False

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
        if not (1 <= day <= max_days.get(month, 31)):
            pkg.logger.warning(f"    Invalid day value: {day}")
            day = 1
            day_valid = False

        try:
            rough_date, created = RoughDate.objects.get_or_create(
                date=date(year=year, month=month, day=day),
                month_valid=month_valid,
                day_valid=day_valid,
            )
            if created:
                pkg.logger.debug(f"    Created new RoughDate: {rough_date}")
            else:
                pkg.logger.debug(f"    Using existing RoughDate: {rough_date}")
            pkg.logger.info(f"    Set rough date of {rough_date}")
            new_image.date = rough_date
            new_image.save()
        except Exception:
            pkg.logger.exception("    Failed to create rough date")

    metadata = tool.read_image_metadata(pkg.image_path)

    path_from_parent = pkg.image_path.relative_to(pkg.parent_path).parent

    parent, created = ImageFolder.objects.get_or_create(name=path_from_parent.parts[0], tn_parent=None)
    if created:
        pkg.logger.info(f"  Created new parent folder: {parent.name}")
        if pkg.view_groups:
            if pkg.overwrite:
                parent.view_groups.set(pkg.view_groups.all())
            else:
                parent.view_groups.add(*pkg.view_groups.all())
        if pkg.edit_groups:
            if pkg.overwrite:
                parent.edit_groups.set(pkg.edit_groups.all())
            else:
                parent.edit_groups.add(*pkg.edit_groups.all())
    else:
        pkg.logger.info(f"  Using existing parent folder: {parent.name}")
    for depth, child_name in enumerate(path_from_parent.parts[1:]):
        child, created = ImageFolder.objects.get_or_create(name=child_name, tn_parent=parent)
        if created:
            pkg.logger.info(f"  {' ' * (depth + 2)}Created new child folder: {child.name}")
            if pkg.view_groups:
                if pkg.overwrite:
                    child.view_groups.set(pkg.view_groups.all())
                else:
                    child.view_groups.add(*pkg.view_groups.all())
            if pkg.edit_groups:
                if pkg.overwrite:
                    child.edit_groups.set(pkg.edit_groups.all())
                else:
                    child.edit_groups.add(*pkg.edit_groups.all())
        else:
            pkg.logger.info(f"  {' ' * (depth + 2)}Using existing child folder: {child.name}")
        parent = child

    containing_folder = parent

    new_img = ImageModel.objects.create(
        file_size=pkg.image_path.stat().st_size,
        original=str(pkg.image_path.resolve()),
        original_name=pkg.image_path.stem,
        orientation=metadata.Orientation or ImageModel.OrientationChoices.HORIZONTAL,
        description=metadata.Description,
        height=metadata.ImageHeight,
        width=metadata.ImageWidth,
        original_checksum=pkg.original_hash,
        phash=calculate_image_phash(pkg.image_path),
        # Relations
        folder=containing_folder,
        # These are placeholders, the files do not exist yet
        thumbnail_checksum="A",
        full_size_checksum="B",
        # This time cannot be dirty
        is_dirty=False,
    )

    # Add view/edit permissions
    if pkg.view_groups:
        new_img.view_groups.set(pkg.view_groups.all())
    if pkg.edit_groups:
        new_img.edit_groups.set(pkg.edit_groups.all())

    pkg.logger.info("  Processing image file")

    generate_image_versions_pyvips(
        pkg.image_path,
        new_img.thumbnail_path,
        new_img.full_size_path,
        pkg.logger,
        thumbnail_size=500,
        webp_quality=90,
    )

    # Update the file hashes, now that the files exist
    pkg.logger.info("    Hashing created files")
    new_img.thumbnail_checksum = calculate_blake3_hash(new_img.thumbnail_path, hash_threads=pkg.hash_threads)
    new_img.full_size_checksum = calculate_blake3_hash(new_img.full_size_path, hash_threads=pkg.hash_threads)
    new_img.save()

    # Parse Faces/pets/regions
    parse_region_info(new_img, metadata)

    # Parse Keywords
    parse_keywords(new_img, metadata)

    # Parse Location
    parse_location(new_img, metadata)
    if not new_img.location:
        parse_location_from_keywords(new_img, metadata)

    # Parse date information from keywords?
    parse_dates_from_keywords(new_img, metadata)

    # And done.  Image cannot be dirty, use update to avoid getting marked as such
    new_img.mark_as_clean()
    pkg.logger.info("  Indexing completed")
