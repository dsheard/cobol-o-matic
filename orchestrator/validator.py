"""Post-agent validation of output artifacts.

Two validation layers:
1. Deterministic (Python): frontmatter schema, required sections, stray file
   cleanup.  Runs after each phase in the orchestrator.
2. LLM critic: semantic cross-checks against source code.  Runs as a
   corrective pass after deterministic validation (see prompts/critic.py).

This module implements layer 1.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import read_template, split_frontmatter
from .models import ProgramFacts

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validating a single artifact file."""

    path: str
    frontmatter_repairs: list[str] = field(default_factory=list)
    incomplete_sections: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.frontmatter_repairs and not self.incomplete_sections


# ---------------------------------------------------------------------------
# Cross-cutting artifact validation (Phase 1)
# ---------------------------------------------------------------------------

_TEMPLATE_TO_PATH: dict[str, str] = {
    "program-inventory.md": "inventory/programs.md",
    "copybook-inventory.md": "inventory/copybooks.md",
    "jcl-jobs.md": "inventory/jcl-jobs.md",
    "program-call-graph.md": "flows/program-call-graph.md",
    "batch-flows.md": "flows/batch-flows.md",
    "data-flows.md": "flows/data-flows.md",
    "interfaces.md": "integration/interfaces.md",
    "io-map.md": "integration/io-map.md",
    "data-dictionary.md": "data/data-dictionary.md",
    "file-layouts.md": "data/file-layouts.md",
    "database-operations.md": "data/database-operations.md",
    "behavioral-tests.md": "test-specs/behavioral-tests.md",
    "data-contracts.md": "test-specs/data-contracts.md",
    "equivalence-matrix.md": "test-specs/equivalence-matrix.md",
    "implementation-plan.md": "requirements/implementation-plan.md",
}

_SECTION_HEADING_RE = re.compile(r"^## .+", re.MULTILINE)


def _build_schemas_from_templates() -> dict[str, dict]:
    """Derive ARTIFACT_SCHEMAS from template files (single source of truth)."""
    schemas: dict[str, dict] = {}
    for template_name, rel_path in _TEMPLATE_TO_PATH.items():
        raw = read_template(template_name)
        fm, body = split_frontmatter(raw)

        frontmatter_check: dict[str, str] = {}
        if fm.get("type"):
            frontmatter_check["type"] = fm["type"]
        if fm.get("subtype"):
            frontmatter_check["subtype"] = fm["subtype"]

        sections = _SECTION_HEADING_RE.findall(body)

        schemas[rel_path] = {
            "frontmatter": frontmatter_check,
            "sections": sections,
        }
    return schemas


ARTIFACT_SCHEMAS: dict[str, dict] = _build_schemas_from_templates()


def _build_br_expected_sections() -> list[str]:
    """Derive business-rules expected sections from the template."""
    raw = read_template("business-rules.md")
    _, body = split_frontmatter(raw)
    return _SECTION_HEADING_RE.findall(body)


_BR_EXPECTED_SECTIONS: list[str] = _build_br_expected_sections()


def validate_cross_cutting_artifact(
    artifact_path: Path,
    rel_path: str,
) -> ValidationResult:
    """Validate a cross-cutting (Phase 1) artifact for structure and content.

    Checks frontmatter schema against ARTIFACT_SCHEMAS and verifies that
    required sections exist and have content.  Repairs frontmatter type/subtype
    if incorrect.
    """
    result = ValidationResult(path=str(artifact_path))
    schema = ARTIFACT_SCHEMAS.get(rel_path)

    if not schema:
        return result

    if not artifact_path.is_file():
        result.incomplete_sections.append("FILE_MISSING")
        return result

    content = artifact_path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(content)

    if not fm:
        result.incomplete_sections.append("NO_FRONTMATTER")
        return result

    repairs: list[tuple[str, object]] = []
    for key, expected_val in schema["frontmatter"].items():
        if fm.get(key) != expected_val:
            repairs.append((key, expected_val))
            result.frontmatter_repairs.append(
                f"{key}: was {fm.get(key)!r}, restored to {expected_val!r}"
            )

    for section in schema["sections"]:
        if not _section_has_content(body, section):
            result.incomplete_sections.append(section)

    if repairs:
        for key, val in repairs:
            fm[key] = val
        _rewrite_with_frontmatter(artifact_path, fm, body)
        logger.warning(
            "Restored %d frontmatter fields in %s: %s",
            len(repairs),
            artifact_path.name,
            ", ".join(k for k, _ in repairs),
        )

    if result.incomplete_sections:
        logger.warning(
            "Incomplete sections in %s: %s",
            artifact_path.name,
            ", ".join(result.incomplete_sections),
        )

    return result


def cleanup_stray_files(output_dir: Path) -> list[str]:
    """Delete .md files at the output root that should be in subdirectories."""
    deleted: list[str] = []
    for path in sorted(output_dir.iterdir()):
        if path.is_file() and path.suffix == ".md":
            logger.warning("Deleting stray file: %s", path.name)
            path.unlink()
            deleted.append(path.name)
    return deleted


def validate_phase1_outputs(output_dir: Path) -> list[ValidationResult]:
    """Validate all Phase 1 cross-cutting artifacts and clean up strays."""
    results: list[ValidationResult] = []

    for rel_path in ARTIFACT_SCHEMAS:
        full_path = output_dir / rel_path
        vr = validate_cross_cutting_artifact(full_path, rel_path)
        results.append(vr)
        if vr.passed:
            logger.info("PASS: %s", rel_path)

    return results


# ---------------------------------------------------------------------------
# Business-rules artifact validation (Phase 2)
# ---------------------------------------------------------------------------

def validate_business_rules(
    artifact_path: Path,
    facts: ProgramFacts,
    *,
    called_by: list[str] | None = None,
) -> ValidationResult:
    """Validate a business-rules artifact against ProgramFacts.

    Checks frontmatter integrity and section completeness.  If frontmatter
    fields were corrupted by the agent, restores them from facts and
    rewrites the file.
    """
    result = ValidationResult(path=str(artifact_path))

    if not artifact_path.is_file():
        result.incomplete_sections.append("FILE_MISSING")
        return result

    content = artifact_path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(content)

    if not fm:
        result.incomplete_sections.append("NO_FRONTMATTER")
        return result

    # --- Frontmatter integrity ---
    repairs: list[tuple[str, object]] = []

    expected = {
        "transactions": [facts.transid] if facts.transid else [],
        "reads": sorted(facts.file_reads),
        "uses_copybooks": sorted(facts.copybooks),
        "calls": sorted(facts.call_targets),
        "program_type": facts.program_type,
    }
    if called_by is not None:
        expected["called_by"] = sorted(called_by)

    for key, expected_val in expected.items():
        actual = fm.get(key)
        if isinstance(expected_val, list):
            actual_sorted = sorted(actual) if isinstance(actual, list) else actual
            if actual_sorted != expected_val:
                repairs.append((key, expected_val))
                result.frontmatter_repairs.append(
                    f"{key}: was {actual!r}, restored to {expected_val!r}"
                )
        elif actual != expected_val:
            repairs.append((key, expected_val))
            result.frontmatter_repairs.append(
                f"{key}: was {actual!r}, restored to {expected_val!r}"
            )

    # --- Section completeness (derived from template) ---
    expected_sections = _BR_EXPECTED_SECTIONS
    for section in expected_sections:
        if not _section_has_content(body, section):
            result.incomplete_sections.append(section)

    # --- Apply repairs if needed ---
    if repairs:
        for key, val in repairs:
            fm[key] = val
        _rewrite_with_frontmatter(artifact_path, fm, body)
        logger.warning(
            "Restored %d frontmatter fields in %s: %s",
            len(repairs),
            artifact_path.name,
            ", ".join(k for k, _ in repairs),
        )

    if result.incomplete_sections:
        logger.warning(
            "Incomplete sections in %s: %s",
            artifact_path.name,
            ", ".join(result.incomplete_sections),
        )

    return result


def validate_all_business_rules(
    output_dir: Path,
    facts_by_program: dict[str, ProgramFacts],
    called_by_map: dict[str, list[str]] | None = None,
) -> list[ValidationResult]:
    """Validate all business-rules artifacts in the output directory."""
    br_dir = output_dir / "business-rules"
    results: list[ValidationResult] = []

    if not br_dir.is_dir():
        return results

    for md_file in sorted(br_dir.glob("*.md")):
        prog = md_file.stem.upper()
        facts = facts_by_program.get(prog)
        if not facts:
            continue

        called_by = (called_by_map or {}).get(prog, [])
        result = validate_business_rules(md_file, facts, called_by=called_by)
        results.append(result)

        if result.passed:
            logger.info("PASS: %s", md_file.name)

    return results


# ---------------------------------------------------------------------------
# Test-specs artifact validation (Phase 4)
# ---------------------------------------------------------------------------

_TEST_SPECS_PATHS = [
    "test-specs/behavioral-tests.md",
    "test-specs/data-contracts.md",
    "test-specs/equivalence-matrix.md",
]

_CAPABILITY_SECTION_RE = re.compile(r"^## (.+)", re.MULTILINE)
_H3_SECTION_RE = re.compile(r"^### (.+)", re.MULTILINE)

_NON_CAPABILITY_SECTIONS = {
    "Test Design Principles",
    "Cross-Capability Scenarios",
}


def _parse_table_rows(text: str) -> list[dict[str, str]]:
    """Parse a markdown table into a list of column-name -> value dicts.

    Expects the first row to be column headers and the second to be a
    separator row.  Returns one dict per data row.
    """
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    table_lines = [ln for ln in lines if ln.startswith("|")]

    if len(table_lines) < 3:
        return []

    header_cells = [c.strip() for c in table_lines[0].split("|")]
    header_cells = [c for c in header_cells if c]

    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c != ""]
        if _is_table_scaffolding(line):
            continue
        row = {}
        for i, header in enumerate(header_cells):
            row[header] = cells[i] if i < len(cells) else ""
        rows.append(row)
    return rows


def _extract_section_text(body: str, header: str, level: str = "##") -> str:
    """Extract text under a markdown section header up to the next same-level header."""
    pattern = rf"^{re.escape(level)} {re.escape(header)}\s*$"
    match = re.search(pattern, body, re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_header = re.search(rf"^{re.escape(level)} ", body[start:], re.MULTILINE)
    if next_header:
        return body[start:start + next_header.start()]
    return body[start:]


def compute_coverage_summary(output_dir: Path) -> list[str]:
    """Parse behavioral-tests.md scenario categories and rewrite the Coverage
    Summary table in equivalence-matrix.md with correct counts.

    Returns a list of corrections applied (empty if counts were already correct).
    """
    bt_path = output_dir / "test-specs" / "behavioral-tests.md"
    em_path = output_dir / "test-specs" / "equivalence-matrix.md"

    if not bt_path.is_file() or not em_path.is_file():
        return []

    bt_content = bt_path.read_text(encoding="utf-8")
    _, bt_body = split_frontmatter(bt_content)

    capability_counts: list[tuple[str, int, int, int, int]] = []

    h2_headers = _CAPABILITY_SECTION_RE.findall(bt_body)
    for cap_name in h2_headers:
        if cap_name.strip() in _NON_CAPABILITY_SECTIONS:
            continue

        section_text = _extract_section_text(bt_body, cap_name.strip())
        if not section_text:
            continue

        scenarios_text = _extract_section_text(
            f"### Scenarios\n{section_text.split('### Scenarios')[-1]}"
            if "### Scenarios" in section_text else "",
            "Scenarios",
            level="###",
        )
        if not scenarios_text:
            continue

        rows = _parse_table_rows(scenarios_text)
        happy = sum(1 for r in rows if r.get("Category", "").strip() == "happy-path")
        error = sum(1 for r in rows if r.get("Category", "").strip() == "error")
        boundary = sum(1 for r in rows if r.get("Category", "").strip() == "boundary")
        total = happy + error + boundary

        if total > 0:
            capability_counts.append((cap_name.strip(), total, happy, error, boundary))

    cc_text = _extract_section_text(bt_body, "Cross-Capability Scenarios")
    if cc_text:
        cc_rows = _parse_table_rows(cc_text)
        cc_total = len(cc_rows)
        if cc_total > 0:
            capability_counts.append(
                ("Cross-capability End-to-End", cc_total, cc_total, 0, 0)
            )

    if not capability_counts:
        return []

    grand_total = sum(c[1] for c in capability_counts)
    grand_happy = sum(c[2] for c in capability_counts)
    grand_error = sum(c[3] for c in capability_counts)
    grand_boundary = sum(c[4] for c in capability_counts)

    em_content = em_path.read_text(encoding="utf-8")
    em_fm, em_body = split_frontmatter(em_content)

    summary_match = re.search(r"^## Coverage Summary\s*$", em_body, re.MULTILINE)
    if not summary_match:
        return []

    summary_start = summary_match.end()
    next_section = re.search(r"^## ", em_body[summary_start:], re.MULTILINE)
    summary_end = summary_start + next_section.start() if next_section else len(em_body)

    old_summary = em_body[summary_start:summary_end]

    old_rows = _parse_table_rows(old_summary)
    old_by_cap = {}
    for row in old_rows:
        cap = row.get("Capability", "").strip().strip("*")
        if cap and cap != "Total":
            old_by_cap[cap] = (
                row.get("Total Tests", ""),
                row.get("Happy Path", ""),
                row.get("Error", ""),
                row.get("Boundary", ""),
            )

    corrections: list[str] = []

    lines = [
        "",
        "| Capability | Total Tests | Happy Path | Error | Boundary | Confidence |",
        "| ---------- | ----------- | ---------- | ----- | -------- | ---------- |",
    ]

    for cap_name, total, happy, error, boundary in capability_counts:
        old = old_by_cap.get(cap_name)
        old_confidence = "high"
        if old:
            old_vals = (str(total), str(happy), str(error), str(boundary))
            actual_old = (old[0].strip(), old[1].strip(), old[2].strip(), old[3].strip())
            if actual_old != old_vals:
                corrections.append(
                    f"{cap_name}: was {actual_old}, corrected to {old_vals}"
                )
            for row in old_rows:
                if row.get("Capability", "").strip().strip("*") == cap_name:
                    old_confidence = row.get("Confidence", "high").strip()
                    break

        cap_display = cap_name
        if cap_name == "Cross-capability End-to-End":
            old_confidence = "high"
        lines.append(
            f"| {cap_display} | {total} | {happy} | {error} | {boundary} | {old_confidence} |"
        )

    lines.append(
        f"| **Total** | **{grand_total}** | **{grand_happy}** | **{grand_error}** "
        f"| **{grand_boundary}** | **high** |"
    )
    lines.append("")

    new_summary = "\n".join(lines)
    new_body = em_body[:summary_start] + new_summary + em_body[summary_end:]
    _rewrite_with_frontmatter(em_path, em_fm, new_body)

    if corrections:
        logger.warning(
            "Coverage summary corrected in equivalence-matrix.md: %s",
            "; ".join(corrections),
        )

    return corrections


def check_capability_completeness(output_dir: Path) -> list[str]:
    """Check that every capability in capabilities.md has test coverage in
    behavioral-tests.md.  Returns a list of missing capability names."""
    caps_path = output_dir / "requirements" / "capabilities.md"
    bt_path = output_dir / "test-specs" / "behavioral-tests.md"

    if not caps_path.is_file() or not bt_path.is_file():
        return []

    caps_content = caps_path.read_text(encoding="utf-8")
    _, caps_body = split_frontmatter(caps_content)

    cap_names: list[str] = []
    for match in _H3_SECTION_RE.finditer(caps_body):
        name = match.group(1).strip()
        if name not in ("Gaps and Assumptions",):
            cap_names.append(name)

    bt_content = bt_path.read_text(encoding="utf-8")
    _, bt_body = split_frontmatter(bt_content)
    bt_sections = {m.strip() for m in _CAPABILITY_SECTION_RE.findall(bt_body)}

    missing: list[str] = []
    for cap in cap_names:
        if cap not in bt_sections:
            missing.append(cap)
            logger.warning(
                "Capability '%s' from capabilities.md has no test section "
                "in behavioral-tests.md",
                cap,
            )

    return missing


def validate_test_specs_outputs(output_dir: Path) -> list[ValidationResult]:
    """Validate all Phase 4 test-specification artifacts.

    Runs frontmatter/section checks, auto-computes the coverage summary,
    and checks capability completeness.
    """
    results: list[ValidationResult] = []

    for rel_path in _TEST_SPECS_PATHS:
        full_path = output_dir / rel_path
        vr = validate_cross_cutting_artifact(full_path, rel_path)
        results.append(vr)
        if vr.passed:
            logger.info("PASS: %s", rel_path)

    corrections = compute_coverage_summary(output_dir)
    if corrections:
        summary_result = ValidationResult(
            path=str(output_dir / "test-specs" / "equivalence-matrix.md"),
            frontmatter_repairs=[f"coverage_summary: {c}" for c in corrections],
        )
        results.append(summary_result)

    missing_caps = check_capability_completeness(output_dir)
    if missing_caps:
        bt_result = ValidationResult(
            path=str(output_dir / "test-specs" / "behavioral-tests.md"),
            incomplete_sections=[
                f"MISSING_CAPABILITY: {cap}" for cap in missing_caps
            ],
        )
        results.append(bt_result)

    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------




def _section_has_content(body: str, section_header: str) -> bool:
    """Check if a markdown section has substantive content beyond its header.

    Returns False if the section is missing, empty, or contains only
    table scaffolding (column header row + separator row with no data rows).
    """
    idx = body.find(section_header)
    if idx == -1:
        return False

    after = body[idx + len(section_header):]
    next_section = after.find("\n## ")
    section_text = after[:next_section] if next_section != -1 else after

    lines = [ln.strip() for ln in section_text.strip().splitlines() if ln.strip()]

    has_text = False
    table_rows = []
    for line in lines:
        if line.startswith("|"):
            table_rows.append(line)
        else:
            has_text = True
            break

    if has_text:
        return True

    data_rows = [r for r in table_rows if not _is_table_scaffolding(r)]
    return len(data_rows) > 1


def _is_table_scaffolding(line: str) -> bool:
    """True if line is a table separator row (| --- | --- |) or empty-cell row."""
    if not line.startswith("|"):
        return False
    cells = [c.strip() for c in line.split("|")]
    return all(c == "" or set(c) <= {"-", " "} for c in cells)


def _rewrite_with_frontmatter(path: Path, fm: dict, body: str) -> None:
    """Rewrite a markdown file with updated frontmatter."""
    fm_yaml = yaml.dump(fm, default_flow_style=False, sort_keys=False).strip()
    content = f"---\n{fm_yaml}\n---\n\n{body}"
    path.write_text(content, encoding="utf-8")
