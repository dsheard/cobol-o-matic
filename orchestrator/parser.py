"""Deterministic COBOL structural parser.

Pure Python -- no LLM calls.  Splits a COBOL source file into divisions,
extracts paragraph boundaries, classifies them, resolves PERFORM THRU
ranges, and groups paragraphs into semantic chunks for agent analysis.
"""

from __future__ import annotations

import re
from collections import defaultdict

from .models import Chunk, Paragraph, ProgramFacts, ProgramManifest

# ---------------------------------------------------------------------------
# Division parsing
# ---------------------------------------------------------------------------

_DIVISION_RE = re.compile(
    r"^\s+(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION",
    re.IGNORECASE,
)


def parse_divisions(lines: list[str]) -> dict[str, tuple[int, int]]:
    """Return 1-based (start, end) line ranges for each COBOL division.

    Keys are lowercase division names: identification, environment, data,
    procedure.  ``end`` is inclusive.
    """
    positions: list[tuple[str, int]] = []
    for idx, line in enumerate(lines):
        # Skip comment lines (indicator area column 7, 0-indexed col 6)
        if len(line) > 6 and line[6] in ("*", "/"):
            continue
        m = _DIVISION_RE.match(line)
        if m:
            positions.append((m.group(1).lower(), idx + 1))  # 1-based

    divisions: dict[str, tuple[int, int]] = {}
    for i, (name, start) in enumerate(positions):
        if i + 1 < len(positions):
            end = positions[i + 1][1] - 1
        else:
            end = len(lines)
        divisions[name] = (start, end)
    return divisions


# ---------------------------------------------------------------------------
# Paragraph parsing
# ---------------------------------------------------------------------------

_PARA_RE = re.compile(r"^ {7}([A-Z0-9][A-Z0-9][\w-]*)\.\s*$")


def parse_paragraphs(
    lines: list[str],
    proc_start: int,
    proc_end: int,
) -> list[Paragraph]:
    """Extract paragraph headers and their line ranges from the PROCEDURE DIVISION.

    ``proc_start`` and ``proc_end`` are 1-based inclusive line numbers.
    Returns paragraphs sorted by source order.
    """
    headers: list[tuple[str, int]] = []
    for idx in range(proc_start - 1, min(proc_end, len(lines))):
        line = lines[idx]
        if len(line) > 6 and line[6] in ("*", "/"):
            continue
        m = _PARA_RE.match(line)
        if m:
            name = m.group(1)
            # Skip the PROCEDURE DIVISION header line itself
            if name.upper().startswith("PROCEDURE"):
                continue
            headers.append((name, idx + 1))  # 1-based

    paragraphs: list[Paragraph] = []
    for i, (name, start) in enumerate(headers):
        end = headers[i + 1][1] - 1 if i + 1 < len(headers) else proc_end
        body = lines[start - 1 : end]  # 0-based slicing for body
        performs, perform_thru = extract_performs(body)
        classification, priority = classify_paragraph(name, body)
        paragraphs.append(
            Paragraph(
                name=name,
                start_line=start,
                end_line=end,
                classification=classification,
                priority=priority,
                performs=performs,
                perform_thru=perform_thru,
            )
        )
    return paragraphs


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

# Prefix pattern: matches numeric (0000-, A100-) or plain letter-led paragraph
# names.  Used only for diagnostics, not classification.
_NUM_PREFIX_RE = re.compile(r"^([A-Z0-9]{1,6})-(.+)", re.IGNORECASE)

# Allow any alphanumeric prefix before the keyword, not just \d{4}.
# E.g. "0000-MAIN", "A100-MAIN", "PROCESS-INPUTS", "READ-MASTER" all match.
_P = r"^[A-Z0-9]*-?"  # optional prefix before the keyword

_CLASSIFICATION_RULES: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"-EXIT$", re.IGNORECASE), "exit", "SKIP"),
    # Dispatch: 0xxx- prefixed or names containing MAIN/DISPATCH/DRIVER
    (re.compile(r"^0\d{2,4}-", re.IGNORECASE), "dispatch", "HIGH"),
    (re.compile(r"MAIN|DISPATCH|DRIVER", re.IGNORECASE), "dispatch", "HIGH"),
    # Validation: any prefix + EDIT/VALIDATE/COMPARE/PROCESS
    (re.compile(_P + r"EDIT", re.IGNORECASE), "validation", "HIGH"),
    (re.compile(_P + r"VALIDATE", re.IGNORECASE), "validation", "HIGH"),
    (re.compile(_P + r"COMPARE", re.IGNORECASE), "validation", "HIGH"),
    (re.compile(_P + r"PROCESS", re.IGNORECASE), "validation", "HIGH"),
    # Decision
    (re.compile(_P + r"DECIDE", re.IGNORECASE), "decision", "HIGH"),
    (re.compile(_P + r"ACTION", re.IGNORECASE), "decision", "HIGH"),
    # Screen / UI
    (re.compile(_P + r"SEND", re.IGNORECASE), "screen", "LOW"),
    (re.compile(_P + r"SCREEN", re.IGNORECASE), "screen", "LOW"),
    (re.compile(_P + r"SETUP", re.IGNORECASE), "screen", "LOW"),
    (re.compile(_P + r"SHOW", re.IGNORECASE), "screen", "LOW"),
    (re.compile(_P + r"PROTECT", re.IGNORECASE), "screen", "LOW"),
    (re.compile(_P + r"UNPROTECT", re.IGNORECASE), "screen", "LOW"),
    (re.compile(_P + r"DISPLAY", re.IGNORECASE), "screen", "LOW"),
    (re.compile(_P + r"FORMAT", re.IGNORECASE), "screen", "LOW"),
    # I/O
    (re.compile(_P + r"READ", re.IGNORECASE), "io", "HIGH"),
    (re.compile(_P + r"WRITE", re.IGNORECASE), "io", "HIGH"),
    (re.compile(_P + r"GET", re.IGNORECASE), "io", "HIGH"),
    (re.compile(_P + r"STORE", re.IGNORECASE), "io", "HIGH"),
    (re.compile(_P + r"CHECK", re.IGNORECASE), "io", "HIGH"),
    (re.compile(_P + r"VERIFY", re.IGNORECASE), "io", "HIGH"),
    (re.compile(_P + r"OPEN", re.IGNORECASE), "io", "HIGH"),
    (re.compile(_P + r"CLOSE", re.IGNORECASE), "io", "HIGH"),
    (re.compile(_P + r"DELETE", re.IGNORECASE), "io", "HIGH"),
    (re.compile(_P + r"INSERT", re.IGNORECASE), "io", "HIGH"),
    (re.compile(_P + r"UPDATE", re.IGNORECASE), "io", "HIGH"),
    (re.compile(_P + r"SELECT", re.IGNORECASE), "io", "HIGH"),
    (re.compile(_P + r"FETCH", re.IGNORECASE), "io", "HIGH"),
]


def classify_paragraph(
    name: str,
    body_lines: list[str],
) -> tuple[str, str]:
    """Return (classification, priority) for a paragraph.

    Tries name-based rules first, then falls back to scanning the body.
    """
    for pattern, classification, priority in _CLASSIFICATION_RULES:
        if pattern.search(name):
            return classification, priority

    body_text = "\n".join(body_lines).upper()
    if "EXEC CICS" in body_text or "EXEC SQL" in body_text or "EXEC DLI" in body_text:
        return "io", "HIGH"
    if "COMPUTE " in body_text or "CALCULATE" in body_text:
        return "calculation", "HIGH"
    if re.search(r"\bIF\b", body_text) or "EVALUATE " in body_text:
        return "decision", "HIGH"
    return "other", "HIGH"


# ---------------------------------------------------------------------------
# PERFORM / PERFORM THRU extraction
# ---------------------------------------------------------------------------

_PERFORM_RE = re.compile(
    r"PERFORM\s+([A-Z0-9][A-Z0-9][\w-]*)",
    re.IGNORECASE,
)
_THRU_SAME_LINE_RE = re.compile(
    r"PERFORM\s+([A-Z0-9][A-Z0-9][\w-]*)\s+THRU\s+([A-Z0-9][A-Z0-9][\w-]*)",
    re.IGNORECASE,
)
_THRU_NEXT_LINE_RE = re.compile(
    r"^\s+THRU\s+([A-Z0-9][A-Z0-9][\w-]*)",
    re.IGNORECASE,
)
_PERFORM_LINE_RE = re.compile(
    r"PERFORM\s+([A-Z0-9][A-Z0-9][\w-]*)\s*$",
    re.IGNORECASE,
)


def extract_performs(
    body_lines: list[str],
) -> tuple[list[str], list[tuple[str, str]]]:
    """Scan paragraph body for PERFORM targets and PERFORM THRU ranges.

    Handles both single-line ``PERFORM A THRU B`` and multi-line where
    ``THRU B`` is on the following line.

    Returns ``(performs, perform_thru)`` where *performs* is a deduplicated
    list of paragraph names and *perform_thru* is a list of (start, end)
    tuples.
    """
    performs: list[str] = []
    perform_thru: list[tuple[str, str]] = []
    seen_performs: set[str] = set()
    seen_thru: set[tuple[str, str]] = set()

    for i, raw_line in enumerate(body_lines):
        # Skip comment lines
        if len(raw_line) > 6 and raw_line[6] in ("*", "/"):
            continue
        line = raw_line.rstrip()

        # --- Same-line THRU ---
        m_thru = _THRU_SAME_LINE_RE.search(line)
        if m_thru:
            start_para = m_thru.group(1)
            end_para = m_thru.group(2)
            key = (start_para, end_para)
            if key not in seen_thru:
                seen_thru.add(key)
                perform_thru.append(key)
            if start_para not in seen_performs:
                seen_performs.add(start_para)
                performs.append(start_para)
            continue

        # --- PERFORM on this line, THRU on next ---
        m_perf_end = _PERFORM_LINE_RE.search(line)
        if not m_perf_end:
            # Also check: PERFORM NAME THRU\n  (THRU at end of same line, target on next)
            m_thru_eol = re.search(
                r"PERFORM\s+([A-Z0-9][A-Z0-9][\w-]*)\s+THRU\s*$",
                line,
                re.IGNORECASE,
            )
            if m_thru_eol:
                start_para = m_thru_eol.group(1)
                # Look at next non-blank, non-comment line for the target
                for j in range(i + 1, len(body_lines)):
                    nxt = body_lines[j].rstrip()
                    if not nxt.strip():
                        continue
                    if len(nxt) > 6 and nxt[6] in ("*", "/"):
                        continue
                    m_target = re.search(r"([A-Z0-9][A-Z0-9][\w-]*)", nxt, re.IGNORECASE)
                    if m_target:
                        end_para = m_target.group(1)
                        key = (start_para, end_para)
                        if key not in seen_thru:
                            seen_thru.add(key)
                            perform_thru.append(key)
                    break
                if start_para not in seen_performs:
                    seen_performs.add(start_para)
                    performs.append(start_para)
                continue

        if m_perf_end:
            perf_name = m_perf_end.group(1)
            # Check next non-blank line for THRU
            for j in range(i + 1, len(body_lines)):
                nxt = body_lines[j].rstrip()
                if not nxt.strip():
                    continue
                if len(nxt) > 6 and nxt[6] in ("*", "/"):
                    continue
                m_nxt = _THRU_NEXT_LINE_RE.match(nxt)
                if m_nxt:
                    end_para = m_nxt.group(1)
                    key = (perf_name, end_para)
                    if key not in seen_thru:
                        seen_thru.add(key)
                        perform_thru.append(key)
                break

            if perf_name not in seen_performs:
                seen_performs.add(perf_name)
                performs.append(perf_name)
            continue  # noqa: used for clarity in multi-branch parsing

        # --- Plain PERFORM (no THRU) ---
        for m in _PERFORM_RE.finditer(line):
            pname = m.group(1)
            # Filter out PERFORM ... TIMES / PERFORM ... UNTIL
            if pname.upper() in ("UNTIL", "TIMES", "VARYING", "WITH", "TEST"):
                continue
            if pname not in seen_performs:
                seen_performs.add(pname)
                performs.append(pname)

    return performs, perform_thru


# ---------------------------------------------------------------------------
# PERFORM THRU range resolution
# ---------------------------------------------------------------------------


def resolve_thru_ranges(
    paragraphs: list[Paragraph],
) -> list[tuple[str, set[str]]]:
    """For each PERFORM THRU range, compute the full set of paragraphs
    (inclusive) that fall within the range.

    Returns a list of ``(range_start, members)`` tuples.  ``range_start``
    is the first paragraph of the THRU range (not the caller), and
    ``members`` is the set of all paragraphs between start and end.  This
    allows the chunk builder to keep members in the same chunk as the
    range start, rather than pulling them into the caller's chunk.
    """
    name_order = {p.name: i for i, p in enumerate(paragraphs)}
    seen_ranges: set[tuple[str, str]] = set()
    results: list[tuple[str, set[str]]] = []

    for para in paragraphs:
        for start_name, end_name in para.perform_thru:
            key = (start_name, end_name)
            if key in seen_ranges:
                continue
            seen_ranges.add(key)

            start_idx = name_order.get(start_name)
            end_idx = name_order.get(end_name)
            if start_idx is None or end_idx is None:
                continue
            lo, hi = min(start_idx, end_idx), max(start_idx, end_idx)
            members = {paragraphs[k].name for k in range(lo, hi + 1)}
            results.append((start_name, members))

    return results


# ---------------------------------------------------------------------------
# Chunk building
# ---------------------------------------------------------------------------

_CLASSIFICATION_ORDER = [
    "dispatch",
    "validation",
    "decision",
    "calculation",
    "io",
    "other",
    "screen",
    "exit",
]


def build_chunks(
    paragraphs: list[Paragraph],
    chunk_threshold: int = 2000,
) -> list[Chunk]:
    """Group paragraphs into semantic chunks.

    1. Group HIGH-priority paragraphs by classification.
    2. Pull dispatcher targets into the dispatcher's chunk.
    3. Merge PERFORM THRU ranges into the same chunk.
    4. Attach EXIT paragraphs to their entry paragraph's chunk.
    5. Collect LOW-priority paragraphs into a ``screen`` chunk.
    6. Split oversized chunks at sub-classification boundaries.
    """
    name_to_para = {p.name: p for p in paragraphs}
    name_order = {p.name: i for i, p in enumerate(paragraphs)}
    thru_groups = resolve_thru_ranges(paragraphs)

    # Track which paragraphs have been assigned to a chunk
    assigned: set[str] = set()
    chunk_members: dict[str, list[str]] = defaultdict(list)

    # --- Step 1: seed chunks by classification (HIGH only) ---
    for para in paragraphs:
        if para.priority == "SKIP" or para.priority == "LOW":
            continue
        cls = para.classification
        if para.name not in assigned:
            chunk_members[cls].append(para.name)
            assigned.add(para.name)

    # --- Step 2: pull dispatcher PERFORM targets into the same chunk ---
    for para in paragraphs:
        if para.classification != "dispatch":
            continue
        for target_name in para.performs:
            target = name_to_para.get(target_name)
            if target and target.name not in assigned:
                cls = para.classification
                chunk_members[cls].append(target.name)
                assigned.add(target.name)

    # --- Step 3: merge PERFORM THRU ranges ---
    # Each THRU range keeps its members in the same chunk as the range's
    # start paragraph (NOT the caller's chunk).
    for range_start, linked_names in thru_groups:
        owner_chunk = None
        for cls, members in chunk_members.items():
            if range_start in members:
                owner_chunk = cls
                break
        if not owner_chunk:
            owner_chunk = "other"
        for ln in linked_names:
            if ln not in assigned:
                chunk_members[owner_chunk].append(ln)
                assigned.add(ln)
            elif ln != range_start:
                for cls, members in chunk_members.items():
                    if ln in members and cls != owner_chunk:
                        members.remove(ln)
                        chunk_members[owner_chunk].append(ln)
                        break

    # --- Step 4: attach EXIT paragraphs to their entry's chunk ---
    for para in paragraphs:
        if para.classification != "exit":
            continue
        if para.name in assigned:
            continue
        # Match entry paragraph: strip "-EXIT" suffix
        entry_name = para.name
        if entry_name.endswith("-EXIT"):
            entry_name = entry_name[: -len("-EXIT")]
        target_chunk = None
        for cls, members in chunk_members.items():
            if entry_name in members:
                target_chunk = cls
                break
        if target_chunk:
            chunk_members[target_chunk].append(para.name)
        else:
            chunk_members["other"].append(para.name)
        assigned.add(para.name)

    # --- Step 5: LOW-priority paragraphs into screen chunk ---
    for para in paragraphs:
        if para.priority == "LOW" and para.name not in assigned:
            chunk_members["screen"].append(para.name)
            assigned.add(para.name)

    # --- Step 6: any remaining unassigned ---
    for para in paragraphs:
        if para.name not in assigned:
            chunk_members["other"].append(para.name)
            assigned.add(para.name)

    # --- Build Chunk objects in canonical order ---
    chunks: list[Chunk] = []
    for cls in _CLASSIFICATION_ORDER:
        members = chunk_members.get(cls)
        if not members:
            continue
        # Sort members by source order
        members.sort(key=lambda n: name_order.get(n, 0))
        paras = [name_to_para[n] for n in members if n in name_to_para]
        if not paras:
            continue

        start = min(p.start_line for p in paras)
        end = max(p.end_line for p in paras)
        total_lines = sum(p.end_line - p.start_line + 1 for p in paras)

        if total_lines > chunk_threshold and len(paras) > 1:
            # Split into sub-chunks
            sub_chunks = _split_chunk(cls, paras, chunk_threshold, name_order)
            chunks.extend(sub_chunks)
        else:
            chunks.append(
                Chunk(
                    chunk_id=cls,
                    paragraphs=members,
                    start_line=start,
                    end_line=end,
                    classification=cls,
                )
            )

    return chunks


def _split_chunk(
    base_id: str,
    paras: list[Paragraph],
    threshold: int,
    name_order: dict[str, int],
) -> list[Chunk]:
    """Split an oversized chunk into numbered sub-chunks."""
    sub_chunks: list[Chunk] = []
    current: list[Paragraph] = []
    current_lines = 0
    part = 1

    for p in paras:
        p_lines = p.end_line - p.start_line + 1
        if current and current_lines + p_lines > threshold:
            sub_chunks.append(_make_sub_chunk(base_id, part, current, name_order))
            part += 1
            current = []
            current_lines = 0
        current.append(p)
        current_lines += p_lines

    if current:
        if part == 1:
            # Didn't actually split -- keep original id
            sub_chunks.append(_make_sub_chunk(base_id, None, current, name_order))
        else:
            sub_chunks.append(_make_sub_chunk(base_id, part, current, name_order))

    return sub_chunks


def _make_sub_chunk(
    base_id: str,
    part: int | None,
    paras: list[Paragraph],
    name_order: dict[str, int],
) -> Chunk:
    chunk_id = f"{base_id}-{part}" if part is not None else base_id
    members = sorted([p.name for p in paras], key=lambda n: name_order.get(n, 0))
    return Chunk(
        chunk_id=chunk_id,
        paragraphs=members,
        start_line=min(p.start_line for p in paras),
        end_line=max(p.end_line for p in paras),
        classification=paras[0].classification if paras else "other",
    )


# ---------------------------------------------------------------------------
# Manifest builder
# ---------------------------------------------------------------------------


def build_manifest(
    program: str,
    source_path: str,
    lines: list[str],
    divisions: dict[str, tuple[int, int]],
    paragraphs: list[Paragraph],
    chunks: list[Chunk],
) -> ProgramManifest:
    """Assemble the full program manifest."""
    dd = divisions.get("data", (0, 0))
    pd_ = divisions.get("procedure", (0, 0))
    return ProgramManifest(
        program=program.upper(),
        source_path=source_path,
        loc=len(lines),
        data_division_range=dd,
        procedure_division_range=pd_,
        paragraphs=paragraphs,
        chunks=chunks,
        staged=True,
    )


def parse_program(
    source_path: str,
    lines: list[str],
    chunk_threshold: int = 2000,
) -> ProgramManifest:
    """Full pipeline: parse, classify, chunk, and build manifest for one program.

    Convenience function that chains all parsing steps.
    """
    program = _extract_program_id(lines) or _filename_to_program(source_path)
    divisions = parse_divisions(lines)

    proc = divisions.get("procedure")
    if not proc:
        manifest = ProgramManifest(
            program=program,
            source_path=source_path,
            loc=len(lines),
            data_division_range=divisions.get("data", (0, 0)),
            procedure_division_range=(0, 0),
            paragraphs=[],
            chunks=[],
            staged=False,
        )
        manifest.facts = extract_facts(program, source_path, lines, divisions)
        return manifest

    paragraphs = parse_paragraphs(lines, proc[0], proc[1])
    chunks = build_chunks(paragraphs, chunk_threshold)
    manifest = build_manifest(program, source_path, lines, divisions, paragraphs, chunks)
    manifest.facts = extract_facts(program, source_path, lines, divisions)
    return manifest


# ---------------------------------------------------------------------------
# Fact extraction
# ---------------------------------------------------------------------------

_COPY_RE = re.compile(
    r"COPY\s+['\"]?([A-Z][\w-]+)['\"]?",
    re.IGNORECASE,
)
_SQL_INCLUDE_RE = re.compile(
    r"EXEC\s+SQL\s+INCLUDE\s+([A-Z][\w-]+)",
    re.IGNORECASE,
)
_WS_PIC_VALUE_RE = re.compile(
    r"(\d{2})\s+([\w-]+)\s+PIC\s+",
    re.IGNORECASE,
)
_VALUE_CLAUSE_RE = re.compile(
    r"VALUE\s+'([^']+)'",
    re.IGNORECASE,
)
_EXEC_CICS_IO_RE = re.compile(
    r"EXEC\s+CICS\s+(READ|WRITE|REWRITE|DELETE)\b",
    re.IGNORECASE,
)
_FILE_DATASET_RE = re.compile(
    r"(?:FILE|DATASET)\s*\(\s*([^)]+?)\s*\)",
    re.IGNORECASE,
)
_CALL_STATIC_RE = re.compile(
    r"CALL\s+'([A-Z][\w-]*)'",
    re.IGNORECASE,
)
_XCTL_RE = re.compile(
    r"EXEC\s+CICS\s+XCTL\s+PROGRAM\s*\(\s*([^)]+?)\s*\)",
    re.IGNORECASE,
)
_LINK_RE = re.compile(
    r"EXEC\s+CICS\s+LINK\s+PROGRAM\s*\(\s*([^)]+?)\s*\)",
    re.IGNORECASE,
)
_RETURN_TRANSID_RE = re.compile(
    r"EXEC\s+CICS\s+RETURN.*?TRANSID\s*\(\s*([^)]+?)\s*\)",
    re.IGNORECASE,
)
_EXEC_SQL_BLOCK_RE = re.compile(
    r"EXEC\s+SQL\b(.*?)END-EXEC",
    re.IGNORECASE | re.DOTALL,
)
_SQL_TABLE_RE = re.compile(
    r"(?:FROM|INTO|UPDATE|DELETE\s+FROM|INSERT\s+INTO)\s+([A-Z][\w]*)",
    re.IGNORECASE,
)
_BATCH_OPEN_RE = re.compile(
    r"OPEN\s+(?:INPUT|OUTPUT|I-O|EXTEND)\s+([A-Z][\w-]+)",
    re.IGNORECASE,
)
_SELECT_ASSIGN_RE = re.compile(
    r"SELECT\s+([A-Z][\w-]+)\s+ASSIGN",
    re.IGNORECASE,
)
_MOVE_LITERAL_RE = re.compile(
    r"MOVE\s+'([A-Z][\w-]*)'\s+TO\s+([\w-]+)",
    re.IGNORECASE,
)

_SYSTEM_COPYBOOKS = frozenset({
    "DFHAID", "DFHBMSCA", "DFHEIBLK", "SQLCA", "SQLDA",
})
_COPY_CLAUSE_KEYWORDS = frozenset({
    "OF", "IN", "REPLACING", "SUPPRESS", "PRINTING",
})


def _strip_cobol_comments(lines: list[str]) -> str:
    """Join lines, excluding COBOL comment lines (col 7 = * or /)."""
    out = []
    for line in lines:
        if len(line) > 6 and line[6] in ("*", "/"):
            continue
        out.append(line)
    return "".join(out)


def _build_ws_literals(lines: list[str], divisions: dict[str, tuple[int, int]]) -> dict[str, str]:
    """Extract all working-storage variables that have VALUE 'literal' clauses.

    Uses a 2-line sliding window to handle multi-line declarations.
    Captures any level-number variable with a PIC clause and a VALUE,
    not just LIT-* prefixed names (platform-agnostic per CLAUDE.md).
    """
    literals: dict[str, str] = {}
    dd = divisions.get("data")
    dd_lines = lines[dd[0] - 1 : dd[1]] if dd and dd[0] else lines
    for i in range(len(dd_lines)):
        window = dd_lines[i]
        if i + 1 < len(dd_lines):
            window += dd_lines[i + 1]
        m_name = _WS_PIC_VALUE_RE.search(window)
        if m_name:
            m_val = _VALUE_CLAUSE_RE.search(window)
            if m_val:
                literals[m_name.group(2).upper()] = m_val.group(1).strip()
    return literals


def _resolve_move_targets(
    full_text: str, variable: str,
) -> list[str]:
    """Find all MOVE 'LITERAL' TO <variable> and return the literal values."""
    pat = re.compile(
        rf"MOVE\s+'([A-Z][\w-]*)'\s+TO\s+{re.escape(variable)}\b",
        re.IGNORECASE,
    )
    return sorted({m.group(1).upper() for m in pat.finditer(full_text)})


def extract_facts(
    program: str,
    source_path: str,
    lines: list[str],
    divisions: dict[str, tuple[int, int]],
) -> ProgramFacts:
    """Extract deterministic metadata from COBOL source via regex.

    Returns a ProgramFacts with copybooks, literals, file I/O targets,
    CALL/XCTL targets, DB tables, program type, and transaction ID.
    """
    code_text = _strip_cobol_comments(lines)
    full_text = "".join(lines)

    # --- Copybooks (from non-comment lines only) ---
    copybooks: list[str] = []
    seen_cb: set[str] = set()
    for pat in (_COPY_RE, _SQL_INCLUDE_RE):
        for m in pat.finditer(code_text):
            name = m.group(1).upper()
            if (name not in seen_cb
                    and name not in _SYSTEM_COPYBOOKS
                    and name not in _COPY_CLAUSE_KEYWORDS):
                seen_cb.add(name)
                copybooks.append(name)
    copybooks.sort()

    # --- Working-storage literals (all PIC+VALUE variables) ---
    literals = _build_ws_literals(lines, divisions)

    # --- File I/O (CICS + batch) ---
    file_reads: list[str] = []
    seen_fr: set[str] = set()
    for m_io in _EXEC_CICS_IO_RE.finditer(code_text):
        region = code_text[m_io.start() : m_io.start() + 200]
        m_file = _FILE_DATASET_RE.search(region)
        if m_file:
            raw = m_file.group(1).strip().strip("'\"")
            resolved = _resolve_literal(raw, literals)
            if resolved not in seen_fr:
                seen_fr.add(resolved)
                file_reads.append(resolved)
    for m in _BATCH_OPEN_RE.finditer(code_text):
        name = m.group(1).upper()
        if name not in seen_fr:
            seen_fr.add(name)
            file_reads.append(name)
    for m in _SELECT_ASSIGN_RE.finditer(code_text):
        name = m.group(1).upper()
        if name not in seen_fr:
            seen_fr.add(name)
            file_reads.append(name)
    file_reads.sort()

    # --- CALL targets ---
    call_targets: list[str] = []
    seen_ct: set[str] = set()
    for m in _CALL_STATIC_RE.finditer(code_text):
        name = m.group(1).upper()
        if name not in seen_ct:
            seen_ct.add(name)
            call_targets.append(name)
    call_targets.sort()

    # --- XCTL + LINK targets ---
    xctl_targets: list[str] = []
    seen_xt: set[str] = set()
    for pat in (_XCTL_RE, _LINK_RE):
        for m in pat.finditer(code_text):
            raw = m.group(1).strip().strip("'\"")
            if raw.upper() == raw.strip().upper() and "'" not in m.group(1):
                resolved = _resolve_literal(raw, literals)
                if resolved == raw.upper():
                    for lit_val in _resolve_move_targets(code_text, raw):
                        if lit_val not in seen_xt:
                            seen_xt.add(lit_val)
                            xctl_targets.append(lit_val)
                    continue
            else:
                resolved = _resolve_literal(raw, literals)
            if resolved not in seen_xt:
                seen_xt.add(resolved)
                xctl_targets.append(resolved)
    xctl_targets.sort()

    # --- DB tables (only from EXEC SQL blocks) ---
    db_tables: list[str] = []
    seen_db: set[str] = set()
    sql_noise = {"INTO", "FROM", "SET", "VALUES", "WHERE", "AND", "OR",
                 "NOT", "NULL", "SELECT", "INSERT", "UPDATE", "DELETE",
                 "TABLE", "CURSOR", "DECLARE", "END-EXEC", "JOIN",
                 "LEFT", "RIGHT", "INNER", "OUTER", "ORDER", "GROUP",
                 "HAVING", "BETWEEN", "LIKE", "EXISTS", "DISTINCT"}
    for m_block in _EXEC_SQL_BLOCK_RE.finditer(code_text):
        sql_body = m_block.group(1)
        for m in _SQL_TABLE_RE.finditer(sql_body):
            name = m.group(1).upper()
            if name not in seen_db and name not in sql_noise and len(name) > 2:
                seen_db.add(name)
                db_tables.append(name)
    db_tables.sort()

    # --- Program type ---
    upper_text = full_text.upper()
    has_cics = "EXEC CICS" in upper_text
    has_ims = "EXEC DLI" in upper_text or "CALL 'CBLTDLI'" in upper_text
    has_linkage = bool(divisions.get("data")) and "LINKAGE SECTION" in upper_text
    if has_cics or has_ims:
        program_type = "online"
    elif has_linkage:
        program_type = "subprogram"
    else:
        program_type = "batch"

    # --- Transaction ID ---
    transid: str | None = None
    tranid_keys = [k for k in literals if re.search(r"TRANS?ID", k, re.IGNORECASE)]
    this_keys = [k for k in tranid_keys if "THIS" in k.upper()]
    for key in this_keys or tranid_keys:
        transid = literals[key]
        break
    if not transid:
        m = _RETURN_TRANSID_RE.search(code_text)
        if m:
            raw = m.group(1).strip().strip("'\"")
            transid = _resolve_literal(raw, literals)

    return ProgramFacts(
        program=program.upper(),
        source_path=source_path,
        loc=len(lines),
        program_type=program_type,
        copybooks=copybooks,
        literals=literals,
        file_reads=file_reads,
        call_targets=call_targets,
        xctl_targets=xctl_targets,
        db_tables=db_tables,
        transid=transid,
    )


def _resolve_literal(raw: str, literals: dict[str, str]) -> str:
    """Resolve a variable reference against the literals dict.

    If *raw* is a known literal name (e.g. ``LIT-ACCTFILENAME``), return its
    VALUE.  Otherwise return *raw* uppercased and stripped of quotes.
    """
    key = raw.upper().strip()
    if key in literals:
        return literals[key]
    return key


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PROGRAM_ID_RE = re.compile(
    r"PROGRAM-ID\.\s+([A-Z][A-Z0-9-]+)",
    re.IGNORECASE,
)


def _extract_program_id(lines: list[str]) -> str | None:
    for line in lines[:50]:
        m = _PROGRAM_ID_RE.search(line)
        if m:
            return m.group(1).upper()
    return None


def _filename_to_program(path: str) -> str:
    from pathlib import Path

    return Path(path).stem.upper()
