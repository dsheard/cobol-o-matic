"""Shared helpers used across prompt modules."""

from __future__ import annotations

from pathlib import Path

from orchestrator import (
    DEFAULT_LARGE_FILE_THRESHOLD,
    SOURCE_TYPES,
    read_template,
    split_frontmatter,
)


def source_context(config: dict) -> str:
    """Build a context string describing source locations for subagent prompts."""
    src = config["source"]
    recursive = src.get("recursive", True)
    lines = [
        "Source locations (read COBOL files from here):",
    ]

    type_labels = {
        "programs": "Programs",
        "copybooks": "Copybooks",
        "jcl": "JCL",
        "bms": "BMS Maps",
        "csd": "CSD Definitions",
        "sql": "SQL/DDL",
    }

    for key in SOURCE_TYPES:
        dirs = src.get(key, [])
        if dirs:
            label = type_labels.get(key, key.title())
            dirs_str = ", ".join(dirs)
            lines.append(f"  {label}: {dirs_str}")

    if recursive:
        lines.append("  Scanning: recursive (includes subdirectories)")

    exts = src.get("extensions", {})
    for key in SOURCE_TYPES:
        ext_list = exts.get(key, [])
        if ext_list and src.get(key):
            lines.append(f"  {key.title()} extensions: {', '.join(ext_list)}")

    lines.append(f"\nOutput directory (write markdown artifacts here): {config['output']}")

    threshold = config.get("settings", {}).get(
        "large_file_threshold", DEFAULT_LARGE_FILE_THRESHOLD
    )
    lines.append(
        f"\nLarge file threshold: {threshold} lines. "
        f"For files exceeding this, use line-range reads (offset/limit)."
    )

    return "\n".join(lines)


def _program_scope_note(program: str | None) -> str:
    if not program:
        return ""
    return (
        f"\n\nSCOPE: You are only analysing program **{program}**. "
        f"Only report discoveries related to {program}. "
        f"You may read other programs to understand call relationships."
    )


def _target_file_instruction(output_file_path: str, *, cross_cutting: bool = False) -> str:
    """Build the 'read target file first' instruction for worker prompts."""
    if cross_cutting:
        return (
            f"## Target Output File\n\n"
            f"Your output file is: {output_file_path}\n\n"
            f"**Read this file first.** The frontmatter and any pre-populated data rows\n"
            f"contain verified program metadata. Preserve the frontmatter values and table\n"
            f"structure. Add rows and content to each section based on your analysis."
        )
    return (
        f"## Target Output File\n\n"
        f"Your output file is: {output_file_path}\n\n"
        f"**Read this file first.** The frontmatter contains verified program metadata\n"
        f"(transaction IDs, file names, copybooks, call targets) -- do NOT modify any\n"
        f"frontmatter values. Keep all existing section headers and table column headers.\n"
        f"Fill in each section with your analysis of the source code."
    )


def _target_files_instruction(output_files: list[str]) -> str:
    """Build output file instruction for workers that write multiple files.

    Each path is listed explicitly. Agents must write ONLY to these paths
    and must NOT create files outside this list.
    """
    file_list = "\n".join(f"   - `{f}`" for f in output_files)
    return (
        f"## Target Output Files\n\n"
        f"Write your output to **exactly** these files (create them if they do not exist):\n"
        f"{file_list}\n\n"
        f"**Rules:**\n"
        f"- Do NOT create any files outside this list.\n"
        f"- Do NOT write summary or index files at the parent directory level.\n"
        f"- If a file already exists, read it first and preserve its frontmatter and structure.\n"
        f"- Each file should be self-contained with its own YAML frontmatter block."
    )


def _template_section(template_name: str, output_path: str) -> str:
    """Embed a template's section structure into a worker prompt.

    Reads the template, strips YAML frontmatter (agents don't need placeholder
    frontmatter), and wraps the body with instructions to follow the structure.
    """
    raw = read_template(template_name)
    _, body = split_frontmatter(raw)
    return (
        f"### Output structure for `{output_path}`\n\n"
        f"Use exactly these section headers and table columns:\n\n"
        f"{body}"
    )


def _draft_status(
    output_files: list[str],
    workspace: Path,
    *,
    scaffold_threshold: int = 0,
) -> str:
    """Build a prompt section indicating which output files already have content.

    Files whose size is at or below *scaffold_threshold* bytes are treated as
    empty scaffolds (frontmatter + blank sections) and excluded.  This prevents
    pre-populated business-rules files from being reported as drafts before any
    worker has actually written analysis content.
    """
    drafts: list[str] = []
    missing: list[str] = []
    for f in output_files:
        path = workspace / f
        if path.is_file() and path.stat().st_size > scaffold_threshold:
            drafts.append(f)
        else:
            missing.append(f)

    if not drafts:
        return ""

    lines = ["## Draft Status\n"]
    lines.append(
        "The following output files already contain analysis from a prior iteration:"
    )
    for f in drafts:
        lines.append(f"  - `{f}`")
    lines.append(
        "\n**Read each existing file first.** Focus on finding information that is "
        "missing, incomplete, or incorrect in the current draft. Do NOT recreate "
        "from scratch. If the draft is already comprehensive and accurate, report "
        "zero discoveries."
    )
    if missing:
        lines.append("\nThese files still need to be created:")
        for f in missing:
            lines.append(f"  - `{f}`")
    return "\n".join(lines)


def _batch_scope_note(programs: list[str]) -> str:
    if not programs or len(programs) <= 1:
        return ""
    names = ", ".join(programs)
    return (
        f"\n\nSCOPE: You are analysing these programs as a batch: **{names}**. "
        f"Report discoveries for all of them. They may have call relationships "
        f"with each other."
    )
