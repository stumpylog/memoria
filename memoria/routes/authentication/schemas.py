from ninja import Schema
from pydantic import SecretStr


class CsrfTokenOutSchema(Schema):
    csrf_token: str


class AuthLoginSchema(Schema):
    username: str
    password: SecretStr
