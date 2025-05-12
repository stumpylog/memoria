from ninja import Schema
from pydantic import EmailStr
from pydantic import SecretStr


class UserInCreateSchema(Schema):
    first_name: str
    last_name: str
    username: str
    password: SecretStr
    email: EmailStr | None = None
    is_staff: bool = False
    is_superuser: bool = False
