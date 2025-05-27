#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

import toml


def update_toml_version(file_path: Path, new_version: str) -> None:
    """Updates the project version in a pyproject.toml file."""
    if not file_path.is_file():
        print(f"Warning: pyproject.toml not found at {file_path}", file=sys.stderr)
        return

    data = toml.loads(file_path.read_text())
    if "project" in data and "version" in data["project"]:
        old_version = data["project"]["version"]
        data["project"]["version"] = new_version
        file_path.write_text(toml.dumps(data))
        print(f"Updated {file_path} from {old_version} to {new_version}")
    else:
        print(
            f"Warning: 'project' or 'version' key not found in {file_path}",
            file=sys.stderr,
        )


def update_package_json_version(file_path: Path, new_version: str) -> None:
    """Updates the version in a package.json file."""
    if not file_path.is_file():
        print(f"Warning: package.json not found at {file_path}", file=sys.stderr)
        return

    data = json.loads(file_path.read_text())
    old_version = data.get("version", "N/A")
    data["version"] = new_version
    file_path.write_text(json.dumps(data, indent=2))
    print(f"Updated {file_path} from {old_version} to {new_version}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Synchronize project version across pyproject.toml and package.json files.",
    )
    parser.add_argument(
        "--backend-toml",
        type=Path,
        default=Path("src-backend/pyproject.toml"),
        help="Path to the backend's pyproject.toml",
    )
    parser.add_argument(
        "--docs-toml",
        type=Path,
        default=Path("src-docs/pyproject.toml"),
        help="Path to the docs' pyproject.toml",
    )
    parser.add_argument(
        "--frontend-package-json",
        type=Path,
        default=Path("src-frontend/package.json"),
        help="Path to the frontend's package.json",
    )
    parser.add_argument("version", type=str, help="The version to set all items to")
    args = parser.parse_args()

    new_version = args.version

    print(f"Syncing version: {new_version}")

    update_toml_version(args.backend_toml, new_version)
    update_toml_version(args.docs_toml, new_version)
    update_package_json_version(args.frontend_package_json, new_version)

    print("Version synchronization complete.")


if __name__ == "__main__":
    main()
