from ninja import Schema
from pydantic import Field
from pydantic import SecretStr


class CsrfTokenOutSchema(Schema):
    csrf_token: str = Field(..., description="The CSRF token used for session verification.")


class AuthLoginSchema(Schema):
    username: str = Field(..., description="The user's login name.")
    password: SecretStr = Field(..., description="The user's password (treated as a secret).")
