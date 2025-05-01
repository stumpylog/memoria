from datetime import date
from typing import TYPE_CHECKING

from exifmwg import ExifTool
from exifmwg.models import ImageMetadata
from exifmwg.models import KeywordStruct
from PIL import Image
from PIL import ImageOps

from memoria.models import Image as ImageModel
from memoria.models import Person
from memoria.models import PersonInImage
from memoria.models import Pet
from memoria.models import PetInImage
from memoria.models import RoughDate
from memoria.models import RoughLocation
from memoria.models import Tag
from memoria.models import TagOnImage
from memoria.tasks.models import ImageIndexTaskModel
from memoria.utils import calculate_blake3_hash
from memoria.utils import calculate_image_phash
from memoria.utils import get_country_code_from_name
from memoria.utils import get_subdivision_code_from_name
from memoria.utils.constants import DATE_KEYWORD
from memoria.utils.constants import EXIF_TOOL_EXE
from memoria.utils.constants import LOCATION_KEYWORD
from memoria.utils.constants import PEOPLE_KEYWORD


def handle_existing_image(
    existing_image: ImageModel,
    pkg: ImageIndexTaskModel,
) -> None:
    """
    Handles an image that has already been indexed, either updating its source or changing the location
    """
    if TYPE_CHECKING:
        assert pkg.logger is not None
    pkg.logger.info("  Image already indexed")
    # Set the source if requested
    if pkg.source is not None and (existing_image.source is None or existing_image.source != pkg.source):
        pkg.logger.info(f"  Updating source to {pkg.source}")
        existing_image.source = pkg.source
        existing_image.save()
    if pkg.view_groups is not None:
        existing_image.view_groups.set(pkg.view_groups)
    if pkg.edit_groups is not None:
        existing_image.edit_groups.set(pkg.edit_groups)
    # Check for an updated location
    if pkg.image_path.resolve() != existing_image.original_path:
        pkg.logger.info(f"  Updating path from {existing_image.original_path.resolve()} to {pkg.image_path.resolve()}")
        existing_image.original_path = pkg.image_path.resolve()
        existing_image.save()
    pkg.logger.info(f"  {pkg.image_path.name} indexing completed")


def handle_new_image(pkg: ImageIndexTaskModel) -> None:
    """
    Handles a completely new image
    """

    if TYPE_CHECKING:
        assert pkg.logger is not None

    def parse_region_info(new_image: ImageModel, metadata: ImageMetadata):
        """
        Parses the MWG regions into people and pets
        """

        if TYPE_CHECKING:
            assert pkg.logger is not None

        pkg.logger.info("  Parsing regions")
        if metadata.RegionInfo:
            for region in metadata.RegionInfo.RegionList:
                if region.Type == "Face" and region.Name:
                    person, _ = Person.objects.get_or_create(name=region.Name)
                    if region.Description:
                        person.description = region.Description
                        person.save()
                    pkg.logger.info(f"  Found face for person {person.name}")
                    _ = PersonInImage.objects.create(
                        person=person,
                        image=new_image,
                        center_x=region.Area.X,
                        center_y=region.Area.Y,
                        height=region.Area.H,
                        width=region.Area.W,
                    )
                elif region.Type == "Pet" and region.Name:
                    pet, _ = Pet.objects.get_or_create(name=region.Name)
                    if region.Description:
                        pet.description = region.Description
                        pet.save()

                    pkg.logger.info(f"  Found box for pet {pet.name}")
                    _ = PetInImage.objects.create(
                        pet=pet,
                        image=new_image,
                        center_x=region.Area.X,
                        center_y=region.Area.Y,
                        height=region.Area.H,
                        width=region.Area.W,
                    )
                elif not region.Name:  # pragma: no cover
                    pkg.logger.warning("  Skipping region with empty Name")
                elif region.Type not in {"Face", "Pet"}:  # pragma: no cover
                    pkg.logger.warning(f"  Skipping region of type {region.Type}")

    def parse_keywords(new_image: ImageModel, metadata: ImageMetadata):
        """
        Creates database Tags from the MWG keyword struct
        """
        if TYPE_CHECKING:
            assert pkg.logger is not None

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

        pkg.logger.info("  Parsing keywords")
        if metadata.KeywordInfo:
            for keyword in metadata.KeywordInfo.Hierarchy:
                # Skip keywords with dedicated processing
                if keyword.Keyword.lower() in {
                    PEOPLE_KEYWORD.lower(),
                    DATE_KEYWORD.lower(),
                    LOCATION_KEYWORD.lower(),
                }:
                    continue
                existing_root_tag, _ = Tag.objects.get_or_create(name=keyword.Keyword)
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
            pkg.logger.info("  No keywords")

    def parse_location(new_image: ImageModel, metadata: ImageMetadata):
        """
        Creates a RoughLocation from a given ImageMetadata object and adds it to the given image.
        """
        if TYPE_CHECKING:
            assert pkg.logger is not None
        if metadata.Country:
            country_alpha_2 = get_country_code_from_name(metadata.Country)
            if country_alpha_2:
                pkg.logger.info(f"  Got country {country_alpha_2} from {metadata.Country}")
                subdivision_code = None
                if metadata.State:
                    subdivision_code = get_subdivision_code_from_name(
                        country_alpha_2,
                        metadata.State,
                    )
                    if not subdivision_code:
                        pkg.logger.warning(f"  No subdivision code found from {metadata.State}")
                    else:
                        pkg.logger.info(f"  Got subdivision code {subdivision_code} from {metadata.State}")
                location, _ = RoughLocation.objects.get_or_create(
                    country_code=country_alpha_2,
                    subdivision_code=subdivision_code,
                    city=metadata.City,
                    sub_location=metadata.Location,
                )
                new_image.location = location
                new_image.save()
                pkg.logger.info(f"  Location is {location}")
            else:
                pkg.logger.warning(f"  No country code found from {metadata.Country}")
        else:  # pragma: no cover
            pkg.logger.info("  No country set, will try keywords")

    def parse_location_from_keywords(new_image: ImageModel, metadata: ImageMetadata):
        """
        If the MWG location information is not set, attempts to parse from the keywords

        Looks for a keyword structure like:
        - Locations
            - Country Name
            - Subdivision Name
                - City Name
                    - Sub-location Name

        If the subdivison doesn't match anything within the country, it is assumed to be a city instead

        """
        if TYPE_CHECKING:
            assert pkg.logger is not None
        if (
            metadata.KeywordInfo
            and (location_tree := metadata.KeywordInfo.get_root_by_name(LOCATION_KEYWORD))
            and location_tree
            and location_tree.Children
        ):
            country_node = location_tree.Children[0]
            country_alpha2 = get_country_code_from_name(country_node.Keyword)
            if country_alpha2:
                subdivision_code = None
                city = None
                location = None
                if len(country_node.Children) > 0:
                    subdivision_node = country_node.Children[0]
                    subdivision_code = get_subdivision_code_from_name(
                        country_alpha2,
                        subdivision_node.Keyword,
                    )
                    if not subdivision_code:
                        # Assume this is a city instead
                        city = subdivision_node.Keyword
                    elif len(subdivision_node.Children) > 0:
                        # If possible, use the first child as the city
                        city_node = subdivision_node.Children[0]
                        city = city_node.Keyword
                        if len(city_node.Children) > 0:
                            location = city_node.Children[0].Keyword

                location, _ = RoughLocation.objects.get_or_create(
                    country_code=country_alpha2,
                    subdivision_code=subdivision_code,
                    city=city,
                    sub_location=location,
                )
                new_image.location = location
                new_image.save()
                pkg.logger.info(f"  RoughLocation is {location}")

    def parse_dates_from_keywords(new_image: ImageModel, metadata: ImageMetadata):
        """
        Looks for a keyword structure like:
        - Dates and Times
            - 1980
            - 12 - December
                - 25

        Which will convert into a date like: 1980-12-25

        If no month is found, no day will be looked for.  It is possible to have a rough date of just a year,
        just a month and year or a year, month, day fully built
        """
        if TYPE_CHECKING:
            assert pkg.logger is not None
        if (
            metadata.KeywordInfo
            and metadata.KeywordInfo
            and (date_and_time_tree := metadata.KeywordInfo.get_root_by_name(DATE_KEYWORD))
            and len(date_and_time_tree.Children) > 0
        ):
            year_node = date_and_time_tree.Children[0]
            month = 1
            month_valid = False
            day = 1
            day_valid = False
            if len(year_node.Children) > 0:
                month_node = year_node.Children[0]
                day = 1
                day_valid = False
                if len(month_node.Children) > 0:
                    day_node = month_node.Children[0]
                    try:
                        day = int(day_node.Keyword)
                        day_valid = True
                    except ValueError:
                        pass
                try:
                    month = int(month_node.Keyword.split("-")[0])
                    month_valid = True
                except ValueError:
                    pass
            try:
                year = int(year_node.Keyword)

                rough_date, _ = RoughDate.objects.get_or_create(
                    date=date(year=year, month=month, day=day),
                    month_valid=month_valid,
                    day_valid=day_valid,
                )
                pkg.logger.info(f"  Set rough date of {rough_date}")
                new_image.date = rough_date
                new_image.save()
            except ValueError:
                pass

    with ExifTool(EXIF_TOOL_EXE, encoding="utf8") as tool:
        metadata = tool.read_image_metadata(pkg.image_path)

    new_img = ImageModel.objects.create(
        file_size=pkg.image_path.stat().st_size,
        original=str(pkg.image_path.resolve()),
        source=pkg.source,
        orientation=metadata.Orientation or ImageModel.OrientationChoices.HORIZONTAL,
        description=metadata.Description,
        height=metadata.ImageHeight,
        width=metadata.ImageWidth,
        original_checksum=calculate_blake3_hash(pkg.image_path, hash_threads=pkg.hash_threads),
        phash=calculate_image_phash(pkg.image_path),
        # These are placeholders, the files do not exist yet
        thumbnail_checksum="A",
        full_size_checksum="B",
        # This time cannot be dirty
        is_dirty=False,
    )
    if pkg.view_groups:
        new_img.view_groups.set(pkg.view_groups)
    if pkg.edit_groups:
        new_img.edit_groups.set(pkg.edit_groups)

    pkg.logger.info("  Creating thumbnail")
    with Image.open(pkg.image_path) as im_file:
        img_copy = ImageOps.exif_transpose(im_file)
        if TYPE_CHECKING:
            assert img_copy is not None
        img_copy.thumbnail((500, 500))
        img_copy.save(new_img.thumbnail_path)

    pkg.logger.info("  Creating WebP version")
    with Image.open(pkg.image_path) as im_file:
        img_copy = ImageOps.exif_transpose(im_file)
        if TYPE_CHECKING:
            assert img_copy is not None
        img_copy.save(new_img.full_size_path, quality=90)

    del img_copy, im_file

    # Update the file hashes, now that the files exist
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
    pkg.logger.info("  indexing completed")
