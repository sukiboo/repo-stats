from pathlib import PurePosixPath

from src.constants import BINARY_EXTENSIONS, EXTENSION_MAP


def _should_count(path: str) -> bool:
    ext = _get_ext(path)
    return ext in EXTENSION_MAP and ext not in BINARY_EXTENSIONS


def _get_ext(path: str) -> str:
    name = PurePosixPath(path).name.lower()
    if name == "makefile":
        return ".makefile"
    if name == "dockerfile" or name.startswith("dockerfile."):
        return ".dockerfile"
    if name == "cmakelists.txt":
        return ".cmake"
    return PurePosixPath(name).suffix
