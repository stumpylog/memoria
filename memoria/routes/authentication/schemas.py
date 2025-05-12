from ninja import Field
from ninja import Schema
from pydantic import EmailStr
from pydantic_extra_types.timezone_name import TimeZoneName

from memoria.models import UserProfile


class CsrfTokenOutSchema(Schema):
    csrf_token: str


class UserProfileOutSchema(Schema):
    items_per_page: int = UserProfile.ImagesPerPageChoices.THIRTY
    bio: str | None

    timezone: TimeZoneName


class UserOutSchema(Schema):
    id: int
    username: str
    email: EmailStr | None
    is_staff: bool
    is_superuser: bool
    profile: UserProfileOutSchema


class TokenCreateInSchema(Schema):
    name: str | None = None
    expires_in_days: int | None = Field(default=None, gt=0)
