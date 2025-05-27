import dataclasses
from pathlib import Path


@dataclasses.dataclass(slots=True)
class DjangoDirectories:
    base_dir: Path
    data_dir: Path = dataclasses.field(init=False)
    logs_dir: Path = dataclasses.field(init=False)
    media_dir: Path = dataclasses.field(init=False)
    thumbnail_dir: Path = dataclasses.field(init=False)
    full_size_dir: Path = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.data_dir / "logs"
        self.media_dir = self.base_dir / "media"
        self.thumbnail_dir = self.media_dir / "thumbnails"
        self.full_size_dir = self.media_dir / "fullsize"

        for x in [self.data_dir, self.logs_dir, self.media_dir, self.thumbnail_dir, self.full_size_dir]:
            x.mkdir(parents=True, exist_ok=True)


@dataclasses.dataclass(slots=True)
class SampleFile:
    original: Path
    full_size: Path
    thumbnail: Path
