from __future__ import annotations

import shutil
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Final


@lru_cache(8)
def get_exiftool_location() -> str:
    for possible in [
        shutil.which("exiftool"),
        "C:\\Users\\Trenton\\Portable\\cmder_mini\\bin\\exiftool.exe",
        "C:\\Users\\tholmes\\Portable\\cmder_mini\\bin\\exiftool.exe",
    ]:
        if possible and Path(possible).is_file():
            return possible
    raise ValueError("Unable to locate exiftool")


EXIF_TOOL_EXE = get_exiftool_location()
if TYPE_CHECKING:
    assert EXIF_TOOL_EXE is not None


DATE_KEYWORD: Final[str] = "Dates"
PEOPLE_KEYWORD: Final[str] = "People"
LOCATION_KEYWORD: Final[str] = "Locations"

MIN_IMAGES_PER_PAGE = 1
MAX_IMAGES_PER_PAGE = 200
