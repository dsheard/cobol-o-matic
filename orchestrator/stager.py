"""Staging pipeline -- writes chunk files, data-division context, and manifests.

Reads COBOL source files, runs the deterministic parser, and writes the
results to a staging directory so that agents receive focused, right-sized
chunks with full DATA DIVISION context.  Also pre-populates output files
with deterministic frontmatter from extracted ProgramFacts.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import yaml

from . import DEFAULT_CHUNK_THRESHOLD, discover_program_files, read_template, split_frontmatter
from .models import ProgramFacts, ProgramManifest
from .parser import parse_program

logger = logging.getLogger(__name__)

MANIFEST_FILENAME = "manifest.yaml"


def stage_program(
    source_path: str | Path,
    staging_dir: str | Path,
    chunk_threshold: int = DEFAULT_CHUNK_THRESHOLD,
) -> ProgramManifest:
    """Parse and stage a single COBOL program.

    Creates:
      staging/{prog_slug}/manifest.yaml
      staging/{prog_slug}/data-division.cbl
      staging/{prog_slug}/chunk-{id}.cbl   (one per chunk)

    Returns the populated ProgramManifest.
    """
    source_path = Path(source_path)
    staging_dir = Path(staging_dir)
    lines = source_path.read_text(encoding="utf-8", errors="replace").splitlines(
        keepends=True
    )

    manifest = parse_program(str(source_path), lines, chunk_threshold)

    prog_slug = manifest.program.lower()
    prog_dir = staging_dir / prog_slug
    prog_dir.mkdir(parents=True, exist_ok=True)

    # --- Clean up stale chunk files ---
    for old_file in prog_dir.glob("chunk-*.cbl"):
        old_file.unlink()

    # --- Write DATA DIVISION context ---
    dd_start, dd_end = manifest.data_division_range
    if dd_start and dd_end:
        dd_lines = lines[dd_start - 1 : dd_end]
        dd_path = prog_dir / "data-division.cbl"
        dd_path.write_text("".join(dd_lines), encoding="utf-8")
        logger.info(
            "  Wrote %s (%d lines)", dd_path.name, dd_end - dd_start + 1
        )

    # --- Build context header from DATA DIVISION literals ---
    context_header = _build_context_header(manifest.program, dd_lines if dd_start else [])

    # --- Write chunk files ---
    name_to_para = {p.name: p for p in manifest.paragraphs}
    for chunk in manifest.chunks:
        chunk_lines: list[str] = []
        for para_name in chunk.paragraphs:
            para = name_to_para.get(para_name)
            if not para:
                continue
            chunk_lines.extend(lines[para.start_line - 1 : para.end_line])

        chunk_path = prog_dir / f"chunk-{chunk.chunk_id}.cbl"
        chunk_content = context_header + "".join(chunk_lines)
        chunk_path.write_text(chunk_content, encoding="utf-8")
        logger.info(
            "  Wrote %s (%d paragraphs, %d lines)",
            chunk_path.name,
            len(chunk.paragraphs),
            len(chunk_lines),
        )

    # --- Write manifest (now includes facts) ---
    manifest_path = prog_dir / MANIFEST_FILENAME
    manifest_path.write_text(
        yaml.dump(manifest.to_dict(), default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    logger.info("  Wrote %s", MANIFEST_FILENAME)

    return manifest


def prepopulate_outputs(
    manifests: list[ProgramManifest],
    output_dir: str | Path,
) -> None:
    """Pre-populate all output files from extracted ProgramFacts.

    Builds the cross-program called_by map, then writes per-program
    business-rules stubs with correct frontmatter.  For chunked programs,
    writes one stub per chunk.
    """
    output_dir = Path(output_dir)

    # Build inverted call graph for called_by
    called_by_map: dict[str, list[str]] = {}
    for m in manifests:
        if not m.facts:
            continue
        for target in m.facts.call_targets + m.facts.xctl_targets:
            called_by_map.setdefault(target, []).append(m.program)

    for m in manifests:
        if not m.facts:
            continue
        called_by = sorted(set(called_by_map.get(m.program, [])))
        prepopulate_business_rules(
            m.facts, output_dir,
            called_by=called_by,
        )


def stage_all(
    config: dict,
    staging_dir: str | Path,
    chunk_threshold: int | None = None,
) -> list[ProgramManifest]:
    """Stage all programs that exceed the chunk threshold.

    Programs smaller than the threshold are skipped (agents read them
    directly).  Returns the list of manifests for staged programs.
    """
    staging_dir = Path(staging_dir)
    if chunk_threshold is None:
        chunk_threshold = (
            config.get("settings", {}).get("chunk_threshold", DEFAULT_CHUNK_THRESHOLD)
        )

    source_files = discover_program_files(config)

    manifests: list[ProgramManifest] = []
    all_manifests: list[ProgramManifest] = []
    staged_count = 0
    skipped_count = 0

    for src in source_files:
        loc = _count_lines(src)

        if loc <= chunk_threshold:
            # Still extract facts for small programs (no chunking needed)
            lines = src.read_text(encoding="utf-8", errors="replace").splitlines(
                keepends=True
            )
            small_manifest = parse_program(str(src), lines, chunk_threshold)
            all_manifests.append(small_manifest)
            skipped_count += 1
            continue

        prog_slug = src.stem.upper()
        manifest_path = staging_dir / prog_slug.lower() / MANIFEST_FILENAME

        if not needs_restaging(src, manifest_path):
            logger.info("Skipping %s (staging is current)", prog_slug)
            existing = _load_manifest(manifest_path)
            if existing:
                manifests.append(existing)
                all_manifests.append(existing)
            skipped_count += 1
            continue

        logger.info("Staging %s (%d lines)", prog_slug, loc)
        manifest = stage_program(src, staging_dir, chunk_threshold)
        manifests.append(manifest)
        all_manifests.append(manifest)
        staged_count += 1

    logger.info(
        "Staging complete: %d staged, %d skipped (below %d-line threshold or current)",
        staged_count,
        skipped_count,
        chunk_threshold,
    )

    # Build cross-program facts and pre-populate output files
    output_dir = config.get("output", "./output")
    build_cross_program_facts(all_manifests, staging_dir)
    prepopulate_outputs(all_manifests, output_dir)
    logger.info("Pre-populated output files for %d programs", len(all_manifests))

    return manifests


def needs_restaging(source_path: str | Path, manifest_path: str | Path) -> bool:
    """Check whether a program needs (re-)staging.

    Returns True if the manifest does not exist or is older than the source.
    """
    source_path = Path(source_path)
    manifest_path = Path(manifest_path)

    if not manifest_path.is_file():
        return True

    src_mtime = source_path.stat().st_mtime
    man_mtime = manifest_path.stat().st_mtime
    return src_mtime > man_mtime


def get_manifest(staging_dir: str | Path, program: str) -> ProgramManifest | None:
    """Load a program manifest from staging if it exists."""
    manifest_path = Path(staging_dir) / program.lower() / MANIFEST_FILENAME
    return _load_manifest(manifest_path)


# ---------------------------------------------------------------------------
# Cross-program facts
# ---------------------------------------------------------------------------


def build_cross_program_facts(
    manifests: list[ProgramManifest],
    staging_dir: str | Path,
) -> Path:
    """Aggregate per-program facts into a cross-program facts file.

    Builds an inverted call graph (called_by), program-to-transid mapping,
    program-to-files mapping, and writes staging/program-facts.yaml.
    """
    staging_dir = Path(staging_dir)

    # Forward maps
    program_transids: dict[str, str] = {}
    program_files: dict[str, list[str]] = {}
    program_copybooks: dict[str, list[str]] = {}
    program_types: dict[str, str] = {}
    call_graph: dict[str, list[str]] = {}
    xctl_graph: dict[str, list[str]] = {}

    # Inverted map
    called_by: dict[str, list[str]] = {}

    for m in manifests:
        if not m.facts:
            continue
        f = m.facts
        if f.transid:
            program_transids[f.program] = f.transid
        program_files[f.program] = sorted(f.file_reads)
        program_copybooks[f.program] = sorted(f.copybooks)
        program_types[f.program] = f.program_type
        call_graph[f.program] = sorted(f.call_targets)
        xctl_graph[f.program] = sorted(f.xctl_targets)

        for target in f.call_targets + f.xctl_targets:
            called_by.setdefault(target, []).append(f.program)

    # Deduplicate and sort called_by
    for target in called_by:
        called_by[target] = sorted(set(called_by[target]))

    cross_facts = {
        "program_types": program_types,
        "transids": program_transids,
        "files": program_files,
        "copybooks": program_copybooks,
        "call_graph": call_graph,
        "xctl_graph": xctl_graph,
        "called_by": called_by,
    }

    staging_dir.mkdir(parents=True, exist_ok=True)
    facts_path = staging_dir / "program-facts.yaml"
    facts_path.write_text(
        yaml.dump(cross_facts, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    logger.info("Wrote cross-program facts: %s", facts_path)
    return facts_path


# ---------------------------------------------------------------------------
# Output pre-population
# ---------------------------------------------------------------------------

_PLACEHOLDER_RE = re.compile(r"\[[\w\s/\-.:,()]+\]")




def _strip_placeholder_rows(body: str) -> str:
    """Remove example/placeholder rows from template body.

    Keeps section headers (##), table header rows (| --- |), and table
    column headers.  Removes rows containing [PLACEHOLDER] patterns and
    descriptive text like "Brief description..." or "Key PERFORM...".
    """
    out: list[str] = []
    for line in body.splitlines(keepends=True):
        stripped = line.strip()
        if not stripped:
            out.append(line)
            continue
        if stripped.startswith("#"):
            out.append(line)
            continue
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")]
            is_separator = all(c == "" or set(c) <= {"-", " "} for c in cells)
            is_header = not _PLACEHOLDER_RE.search(stripped)
            if is_separator or is_header:
                out.append(line)
            continue
        if stripped.startswith("```"):
            out.append(line)
    return "".join(out)


def _build_br_frontmatter(
    facts: ProgramFacts,
    called_by: list[str] | None = None,
) -> dict:
    """Build business-rules frontmatter from ProgramFacts."""
    return {
        "type": "business-rules",
        "program": facts.program,
        "program_type": facts.program_type,
        "status": "draft",
        "confidence": "medium",
        "last_pass": 1,
        "calls": sorted(facts.call_targets),
        "called_by": sorted(called_by or []),
        "uses_copybooks": sorted(facts.copybooks),
        "reads": sorted(facts.file_reads),
        "writes": [],
        "db_tables": sorted(facts.db_tables),
        "transactions": [facts.transid] if facts.transid else [],
        "mq_queues": [],
    }


def _render_prepopulated(frontmatter: dict, body: str) -> str:
    """Render a pre-populated output file from frontmatter and body."""
    fm_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False).strip()
    return f"---\n{fm_yaml}\n---\n\n{body}"


def prepopulate_business_rules(
    facts: ProgramFacts,
    output_dir: Path,
    *,
    called_by: list[str] | None = None,
) -> Path:
    """Write a pre-populated business-rules output file for one program.

    Reads the business-rules template, fills frontmatter from ProgramFacts,
    strips placeholder body rows, writes the file.  Always creates a single
    file per program -- chunked programs share the same output file.
    """
    template = read_template("business-rules.md")
    _, body = split_frontmatter(template)
    clean_body = _strip_placeholder_rows(body)

    prog_slug = facts.program.lower()
    filename = f"{prog_slug}.md"
    title = f"# {facts.program} -- Business Rules\n"

    if clean_body.startswith("#"):
        first_nl = clean_body.index("\n")
        clean_body = title + clean_body[first_nl + 1:]
    else:
        clean_body = title + "\n" + clean_body

    fm = _build_br_frontmatter(facts, called_by=called_by)
    br_dir = output_dir / "business-rules"
    br_dir.mkdir(parents=True, exist_ok=True)
    out_path = br_dir / filename

    template_size = len(_render_prepopulated(fm, clean_body).encode("utf-8"))
    if out_path.is_file() and out_path.stat().st_size > template_size:
        logger.info("  Skipping %s (already has content)", out_path)
        return out_path

    out_path.write_text(_render_prepopulated(fm, clean_body), encoding="utf-8")
    logger.info("  Pre-populated %s", out_path)
    return out_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _count_lines(path: Path) -> int:
    try:
        return sum(1 for _ in path.open(encoding="utf-8", errors="replace"))
    except OSError:
        return 0


def _load_manifest(manifest_path: Path) -> ProgramManifest | None:
    if not manifest_path.is_file():
        return None
    try:
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        return ProgramManifest.from_dict(data)
    except (yaml.YAMLError, KeyError, OSError) as e:
        logger.warning("Could not load manifest %s: %s", manifest_path, e)
        return None


# Matches "05 LIT-xxx PIC X(n) VALUE 'yyy'." or any *TRANID/*TRANSID variable
# within a 2-line window.  Group 1 = data item name, group 2 = literal value.
_LIT_VALUE_RE = re.compile(
    r"(\bLIT-[\w-]+|\b[\w-]*TRANS?ID[\w-]*)\b"  # data item name
    r"[^.]*?"                                     # PIC clause (stop at period)
    r"VALUE\s+'([^']+)'",                         # VALUE 'literal'
    re.IGNORECASE,
)

# Categories of interest for the context header.
_LIT_CATEGORIES: list[tuple[str, list[str]]] = [
    ("Transaction", ["TRANID"]),
    ("Program", ["THISPGM", "MENUPGM", "LISTPGM", "DTLPGM", "UPDATEPGM"]),
    ("File", ["FILENAME", "FILNAM", "XREFNAME"]),
    ("Map", ["MAPSET", "THISMAP"]),
]


def _categorise_literal(name: str) -> str | None:
    """Return a category string if the literal is useful context, else None."""
    name_upper = name.upper()
    for category, keywords in _LIT_CATEGORIES:
        if any(kw in name_upper for kw in keywords):
            return category
    return None


def _extract_literals(dd_lines: list[str]) -> dict[str, list[tuple[str, str]]]:
    """Scan DATA DIVISION lines (as 2-line windows) for LIT-* and *TRANID* VALUE clauses."""
    literals: dict[str, list[tuple[str, str]]] = {}
    for i in range(len(dd_lines)):
        window = dd_lines[i] if i + 1 >= len(dd_lines) else dd_lines[i] + dd_lines[i + 1]
        for match in _LIT_VALUE_RE.finditer(window):
            name = match.group(1).strip()
            value = match.group(2).strip()
            cat = _categorise_literal(name)
            if cat is None:
                continue
            existing = literals.setdefault(cat, [])
            if not any(n == name for n, _ in existing):
                existing.append((name, value))
    return literals


def _build_context_header(program: str, dd_lines: list[str]) -> str:
    """Extract key literals from DATA DIVISION and format as a COBOL comment block.

    Prepended to each chunk file so the agent has transaction IDs, file names,
    and program names without needing to cross-reference the data-division file.
    """
    if not dd_lines:
        return ""

    literals = _extract_literals(dd_lines)
    if not literals:
        return ""

    header_lines = [
        f"      *{'=' * 62}\n",
        f"      * PROGRAM CONTEXT -- {program}\n",
        "      * (extracted from DATA DIVISION by stager)\n",
    ]

    display_order = ["Transaction", "Program", "File", "Map"]
    for cat in display_order:
        items = literals.get(cat)
        if not items:
            continue
        pairs = ", ".join(f"{v} ({n})" for n, v in items)
        header_lines.append(f"      * {cat}: {pairs}\n")

    header_lines.append(f"      *{'=' * 62}\n")
    return "".join(header_lines)
