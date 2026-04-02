"""Configuration loading, path resolution, and workspace scaffolding."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import yaml

from orchestrator import SOURCE_TYPES

logger = logging.getLogger("cobol-re")

SCRIPT_DIR = Path(__file__).resolve().parent.parent

CONFIG_FILENAME = "config.yaml"
DEFAULT_MAX_ITERATIONS = 5
DEFAULT_N_STABLE = 2
DEFAULT_BATCH_SIZE = 3
DEFAULT_LARGE_FILE_THRESHOLD = 400
DEFAULT_CHUNK_THRESHOLD = 2000
DEFAULT_STAGING_DIR = "./staging"

DEFAULT_CONFIG = {
    "application": "Unnamed COBOL Application",
    "source": {
        "programs": ["./source"],
        "copybooks": ["./source"],
        "jcl": [],
        "bms": [],
        "csd": [],
        "sql": [],
        "recursive": True,
        "extensions": {
            "programs": [".cbl", ".cob", ".CBL", ".COB"],
            "copybooks": [".cpy", ".copy", ".CPY", ".COPY"],
            "jcl": [".jcl", ".JCL", ".prc", ".PRC"],
            "bms": [".bms", ".BMS"],
            "csd": [".csd", ".CSD"],
            "sql": [".sql", ".SQL"],
        },
    },
    "output": "./output",
    "settings": {
        "max_iterations": DEFAULT_MAX_ITERATIONS,
        "n_stable": DEFAULT_N_STABLE,
        "confidence_threshold": "medium",
        "strategy": "auto",
        "batch_size": DEFAULT_BATCH_SIZE,
        "large_file_threshold": DEFAULT_LARGE_FILE_THRESHOLD,
        "chunk_threshold": DEFAULT_CHUNK_THRESHOLD,
        "staging_dir": DEFAULT_STAGING_DIR,
    },
}

INIT_DIRS = [
    "source",
    "state",
    "output/inventory",
    "output/data",
    "output/business-rules",
    "output/flows",
    "output/integration",
    "output/requirements",
    "output/test-specs",
]

BUNDLED_WORKSPACE = SCRIPT_DIR / "workspace"


def load_config(workspace: Path) -> dict:
    """Load config.yaml from the workspace root."""
    config_path = workspace / CONFIG_FILENAME
    if not config_path.is_file():
        print(f"ERROR: No {CONFIG_FILENAME} found in {workspace}", file=sys.stderr)
        print("  Run 'python analyse.py init' first.", file=sys.stderr)
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def resolve_paths(config: dict, workspace: Path) -> dict:
    """Resolve relative paths in config to absolute paths."""
    resolved = dict(config)
    source = dict(config.get("source", {}))

    for key in SOURCE_TYPES:
        paths = source.get(key, [])
        resolved_paths = []
        for p in paths:
            path = Path(p)
            if not path.is_absolute():
                resolved_paths.append(str((workspace / path).resolve()))
            else:
                resolved_paths.append(str(path))
        source[key] = resolved_paths

    resolved["source"] = source

    output = config.get("output", "./output")
    if not Path(output).is_absolute():
        resolved["output"] = str((workspace / output).resolve())

    settings = dict(resolved.get("settings", {}))
    staging = settings.get("staging_dir", DEFAULT_STAGING_DIR)
    if not Path(staging).is_absolute():
        settings["staging_dir"] = str((workspace / staging).resolve())
    resolved["settings"] = settings

    return resolved


def find_workspace() -> Path:
    """Locate the workspace directory containing config.yaml.

    Search order: workspace/ subdirectory of cwd, cwd itself, workspace/
    subdirectory of the script directory, script directory itself.
    """
    cwd = Path.cwd()
    for base in (cwd, SCRIPT_DIR):
        ws = base / "workspace"
        if (ws / CONFIG_FILENAME).is_file():
            return ws
        if (base / CONFIG_FILENAME).is_file():
            return base
    return cwd


def cmd_init(target: Path) -> None:
    """Scaffold a new COBOL reverse-engineering workspace.

    Creates a workspace/ subdirectory (or at the given target path) with
    config, source, output directories, CLAUDE.md, and agent skills.
    Copies bundled assets (CLAUDE.md, .claude/skills/) from the tool's
    own workspace/ directory.
    """
    ws = target / "workspace" if target == SCRIPT_DIR else target
    print(f"Initializing workspace at {ws}\n")

    for d in INIT_DIRS:
        (ws / d).mkdir(parents=True, exist_ok=True)
        print(f"  Created {d}/")

    config_path = ws / CONFIG_FILENAME
    if not config_path.exists():
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, sort_keys=False)
        print(f"  Created {CONFIG_FILENAME}")
    else:
        print(f"  {CONFIG_FILENAME} already exists (skipped)")

    _copy_bundled_assets(ws)

    print("\nWorkspace ready. Next steps:")
    print(f"  1. Edit {ws / CONFIG_FILENAME} -- set application name and source paths")
    print("  2. Point source.programs and source.copybooks at your COBOL files")
    print("  3. Run: python analyse.py run")


def _copy_bundled_assets(target_ws: Path) -> None:
    """Copy CLAUDE.md and .claude/skills/ from the bundled workspace."""
    import shutil

    bundled_claude = BUNDLED_WORKSPACE / "CLAUDE.md"
    target_claude = target_ws / "CLAUDE.md"
    if bundled_claude.is_file() and not target_claude.exists():
        shutil.copy2(bundled_claude, target_claude)
        print("  Created CLAUDE.md")
    elif target_claude.exists():
        print("  CLAUDE.md already exists (skipped)")

    bundled_skills = BUNDLED_WORKSPACE / ".claude" / "skills"
    target_skills = target_ws / ".claude" / "skills"
    if bundled_skills.is_dir():
        for skill_dir in bundled_skills.iterdir():
            if not skill_dir.is_dir():
                continue
            target_skill = target_skills / skill_dir.name
            target_skill.mkdir(parents=True, exist_ok=True)
            for f in skill_dir.iterdir():
                target_f = target_skill / f.name
                if not target_f.exists():
                    shutil.copy2(f, target_f)
                    print(f"  Created .claude/skills/{skill_dir.name}/{f.name}")
                else:
                    print(f"  .claude/skills/{skill_dir.name}/{f.name} already exists (skipped)")
