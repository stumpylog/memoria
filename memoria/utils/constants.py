from __future__ import annotations

import shutil
from typing import TYPE_CHECKING
from typing import Final

EXIF_TOOL_EXE = shutil.which("exiftool") or "C:\\Users\\Trenton\\Portable\\cmder_mini\\bin\\exiftool.exe"
if TYPE_CHECKING:
    assert EXIF_TOOL_EXE is not None


DATE_KEYWORD: Final[str] = "Dates"
PEOPLE_KEYWORD: Final[str] = "People"
LOCATION_KEYWORD: Final[str] = "Locations"

MIN_IMAGES_PER_PAGE = 1
MAX_IMAGES_PER_PAGE = 200
