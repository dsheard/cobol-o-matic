"""COBOL Reverse Engineering Orchestrator -- shared constants and utilities."""

from __future__ import annotations

from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent.parent

SOURCE_TYPES = ("programs", "copybooks", "jcl", "bms", "csd", "sql")

DEFAULT_LARGE_FILE_THRESHOLD = 400
DEFAULT_CHUNK_THRESHOLD = 2000


def read_template(name: str) -> str:
    """Read a template file from the templates/ directory."""
    path = SCRIPT_DIR / "templates" / name
    return path.read_text(encoding="utf-8")


def split_frontmatter(content: str) -> tuple[dict, str]:
    """Split markdown content into a frontmatter dict and body string.

    Returns ({}, content) if no valid frontmatter block is found.
    """
    if not content.startswith("---"):
        return {}, content
    try:
        end = content.index("---", 3)
    except ValueError:
        return {}, content
    fm_text = content[3:end].strip()
    body = content[end + 3:].lstrip("\n")
    fm = yaml.safe_load(fm_text) or {}
    return fm, body


def discover_program_files(config: dict) -> list[Path]:
    """Scan configured source directories for COBOL program files.

    Returns a sorted, deduplicated list of Path objects.
    """
    program_dirs = config["source"].get("programs", [])
    recursive = config["source"].get("recursive", True)
    extensions = config["source"].get("extensions", {}).get(
        "programs", [".cbl", ".cob", ".CBL", ".COB"]
    )

    files: list[Path] = []
    for dir_path in program_dirs:
        d = Path(dir_path)
        if not d.is_dir():
            continue
        for ext in extensions:
            if recursive:
                files.extend(d.rglob(f"*{ext}"))
            else:
                files.extend(d.glob(f"*{ext}"))

    seen: set[str] = set()
    unique: list[Path] = []
    for f in sorted(files, key=lambda p: p.stem.upper()):
        key = f.stem.upper()
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique
