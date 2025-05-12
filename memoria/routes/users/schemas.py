from ninja import Schema
from pydantic import EmailStr
from pydantic import SecretStr
from pydantic_extra_types.timezone_name import TimeZoneName

from memoria.models import UserProfile


class UserUpdateInScheme(Schema):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None

    items_per_page: int | None = None
    bio: str | None = None

    timezone: TimeZoneName | None = None


class UserInCreateSchema(Schema):
    first_name: str
    last_name: str
    username: str
    password: SecretStr
    email: EmailStr | None = None
    is_staff: bool = False
    is_superuser: bool = False


class UserProfileOutSchema(Schema):
    items_per_page: int = UserProfile.ImagesPerPageChoices.THIRTY
    bio: str | None

    timezone: TimeZoneName


class UserOutSchema(Schema):
    id: int
    username: str
    email: EmailStr | str | None
    is_staff: bool
    is_superuser: bool
    profile: UserProfileOutSchema
