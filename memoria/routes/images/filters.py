from typing import Annotated
from typing import TypeVar

from pydantic import BeforeValidator

T = TypeVar("T")

CommaSepIntList = Annotated[
    list[T],
    BeforeValidator(lambda x: [int(v) for v in (v.strip() for v in x.split(",")) if v]),
]
