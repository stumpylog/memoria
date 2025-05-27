from typing import Protocol

from django.http import HttpResponse


class _BaseNamedItemGeneratorProtocol(Protocol):
    def __call__(self, *, with_description: bool = False) -> int:
        pass


class PersonGeneratorProtocol(_BaseNamedItemGeneratorProtocol):
    pass


class PetGeneratorProtocol(_BaseNamedItemGeneratorProtocol):
    pass


class AlbumGeneratorProtocol(_BaseNamedItemGeneratorProtocol):
    pass


class TagGeneratorProtocol(_BaseNamedItemGeneratorProtocol):
    pass


class ChildTagGeneratorProtocol(Protocol):
    def __call__(self, parent_id: int, *, with_description: bool = False) -> int:
        pass


class _BaseNamedApiGeneratorProtocol(Protocol):
    def __call__(self, name: str | None = None, description: str | None = None) -> HttpResponse:
        pass


class AlbumApiGeneratorProtocol(_BaseNamedApiGeneratorProtocol):
    pass


class PetApiGeneratorProtocol(_BaseNamedApiGeneratorProtocol):
    pass


class LocationGeneratorProtocol(Protocol):
    def __call__(
        self,
        country: str,
        subdivision: str | None = None,
        city: str | None = None,
        location: str | None = None,
    ) -> int:
        pass


class DateGeneratorProtocol(Protocol):
    def __call__(self) -> int:
        pass
