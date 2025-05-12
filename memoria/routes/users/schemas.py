import enum
from datetime import datetime

from ninja import Schema
from pydantic import EmailStr
from pydantic import SecretStr


class UserType(enum.Enum):
    Regular = "regular"
    Staff = "staff"
    Superuser = "superuser"


class UserOutProfileResponse(Schema):
    username: str
    last_login: datetime | None = None


class UserInCreateSchema(Schema):
    first_name: str
    last_name: str
    username: str
    password: SecretStr
    email: EmailStr | None = None
    user_type: UserType = UserType.Regular


class UserOutCreateResponse(Schema):
    id_: int
