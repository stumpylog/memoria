from ninja import Schema


class CsrfTokenOutSchema(Schema):
    csrf_token: str
