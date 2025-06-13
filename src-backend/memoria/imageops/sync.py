from typing import TYPE_CHECKING

from exifmwg import Dimensions as DimensionsStruct
from exifmwg import ImageMetadata
from exifmwg import Keyword as KeywordStruct
from exifmwg import KeywordInfo as KeywordInfoModel
from exifmwg import Region as RegionStruct
from exifmwg import RegionInfo as RegionInfoStruct
from exifmwg import XmpArea as XmpAreaStruct

from memoria.models import Image as ImageModel
from memoria.models import PersonInImage
from memoria.models import PetInImage
from memoria.models import RoughDate
from memoria.models import RoughLocation
from memoria.utils.constants import DATE_KEYWORD

if TYPE_CHECKING:
    import datetime


def fill_image_metadata_from_db(image: ImageModel, image_metadata: ImageMetadata) -> bool:
    """
    Given a dirty image, constructs a new ImageMetadata object and populates it with the data from the database.

    For use in syncing the database into the image file.
    """

    def _update_title() -> bool:
        if image.title is not None:
            image_metadata.title = image.title
            return True
        return False

    def _update_description() -> bool:
        if image.description is not None:
            image_metadata.description = image.description
            return True
        return False

    def _update_orientation() -> bool:
        image_metadata.orientation = image.orientation
        return True

    def _update_region_info() -> bool:
        def _add_people_regions() -> None:
            for person in image.people.all():
                person_box = PersonInImage.objects.filter(image=image, person=person).get()
                region_info.region_list.append(
                    RegionStruct(
                        name=person.name,
                        type_="Face",
                        area=XmpAreaStruct(
                            h=person_box.height,
                            w=person_box.width,
                            x=person_box.center_x,
                            y=person_box.center_y,
                            unit="normalized",
                        ),
                        description=person.description,
                    ),
                )

        def _add_pets_regions() -> None:
            for pet in image.pets.all():
                pet_box = PetInImage.objects.filter(image=image, pet=pet).get()
                region_info.region_list.append(
                    RegionStruct(
                        name=pet.name,
                        type_="Pet",
                        area=XmpAreaStruct(
                            h=pet_box.height,
                            w=pet_box.width,
                            x=pet_box.center_x,
                            y=pet_box.center_y,
                            unit="normalized",
                        ),
                        description=pet_box.description,
                    ),
                )

        if image.people.count() > 0 or image.pets.count() > 0:
            region_info = RegionInfoStruct(
                applied_to_dimensions=DimensionsStruct(
                    h=float(image.original_height),
                    w=float(image.original_width),
                    unit="pixel",
                ),
                region_list=[],
            )
            _add_people_regions()
            _add_pets_regions()
            image_metadata.region_info = region_info
            return True
        return False

    def _update_location() -> bool:
        if image.location is not None:
            if TYPE_CHECKING:
                assert isinstance(image.location, RoughLocation)
            image_metadata.country = image.location.country_name
            if image.location.city is not None:
                image_metadata.city = image.location.city
            if image.location.subdivision_name is not None:
                image_metadata.state = image.location.subdivision_name
            if image.location.sub_location is not None:
                image_metadata.location = image.location.sub_location
            return True
        return False

    def _update_date() -> bool:
        # TODO: Need to update this for the new format
        if image.date is not None:
            if TYPE_CHECKING:
                assert isinstance(image.date, RoughDate)
                assert isinstance(image.date.date, datetime.date)
            year_keyword = KeywordStruct(keyword=str(image.date.date.year), children=[])
            month_keyword = None
            if image.date.month_valid:
                month_keyword = KeywordStruct(Keyword=f"{image.date.date.month} - {image.date.date.strftime('%B')}")
                year_keyword.Children.append(month_keyword)
            if image.date.day_valid and month_keyword:
                month_keyword.Children.append(KeywordStruct(Keyword=str(image.date.date.day)))
            image_metadata.keyword_info = KeywordInfoModel(
                hierarchy=[
                    KeywordStruct(
                        keyword=DATE_KEYWORD,
                        applied=False,
                        children=[year_keyword],
                    ),
                ],
            )
            return True
        return False

    def _update_tags() -> bool:
        # TODO: Construct the keywords
        return False

    updated = _update_title()
    updated = _update_description() or updated
    updated = _update_orientation() or updated
    updated = _update_region_info() or updated
    updated = _update_location() or updated
    updated = _update_date() or updated
    return _update_tags() or updated
