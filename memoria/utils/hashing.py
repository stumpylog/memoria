from pathlib import Path

from blake3 import blake3
from imagehash import phash
from PIL import Image


def calculate_blake3_hash(file_path: Path, *, chunk_size: int = 1_048_576, hash_threads: int = 4) -> str:
    """
    Calculate the BLAKE3 hash of a file by reading it in chunks.

    :param file_path: Path to the file (str or Path object)
    :param chunk_size: Size of chunks to read (default is 1MB)
    :return: Hexadecimal representation of the BLAKE3 hash
    """
    hasher = blake3(max_threads=hash_threads)

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(chunk_size), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def calculate_image_phash(file_path: Path) -> str:
    with Image.open(file_path) as im_file:
        return str(phash(im_file))
