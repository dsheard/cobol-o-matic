"""Data worker prompt -- extracts data structures, file layouts, and DB operations."""

from __future__ import annotations

from pathlib import Path

from ._helpers import source_context, _program_scope_note, _target_files_instruction, _template_section, _draft_status


def build_data_worker_prompt(config: dict, program: str | None = None, *, output_file_path: str | None = None, workspace: Path | None = None) -> str:
    output_dir = config.get("output", "./output")
    output_files = [
        f"{output_dir}/data/data-dictionary.md",
        f"{output_dir}/data/file-layouts.md",
        f"{output_dir}/data/database-operations.md",
    ]
    draft_section = _draft_status(output_files, workspace) if workspace else ""
    return f"""\
You are a COBOL data structure analyst. Your job is to extract all data
definitions from DATA DIVISION, copybooks, and database operations.

{source_context(config)}

## PIC Data Type Reference

| PIC Pattern | Meaning | Example |
| ----------- | ------- | ------- |
| `X(n)` | Alphanumeric, n chars | `PIC X(30)` = 30-char string |
| `9(n)` | Numeric, n digits | `PIC 9(5)` = 5-digit integer |
| `S9(n)` | Signed numeric | `PIC S9(7)` = signed 7-digit |
| `9(n)V9(m)` | Decimal (implied) | `PIC 9(5)V99` = 5.2 decimal |
| `Z(n)9` | Numeric edited | Zero-suppressed display |
| `A(n)` | Alphabetic only | `PIC A(20)` = 20-char alpha |

## Data Division Sections

| Section | Purpose | Key items |
| --- | --- | --- |
| FILE SECTION (FD/SD) | File record descriptions | SELECT/ASSIGN, organisation, access mode, keys |
| WORKING-STORAGE | Program-local data | Group items, PIC clauses, VALUE, 88-levels, REDEFINES, OCCURS |
| LINKAGE SECTION | Parameters from CALL ... USING | Interface contract between caller/callee |
| LOCAL-STORAGE | Thread-local data (rare) | Same as WORKING-STORAGE but per-invocation |

## Database Operation Patterns

| Pattern | Type | What to extract |
| --- | --- | --- |
| `EXEC SQL` blocks | DB2 | Table names, operation type (SELECT/INSERT/UPDATE/DELETE), key columns, host variables |
| `EXEC DLI` or `CALL 'CBLTDLI'` | IMS/DB | Segment names, operation codes (GU/GN/ISRT/REPL/DLET) |
| READ/WRITE/REWRITE/DELETE/START on indexed files | Indexed file (VSAM/ISAM) | File name, access pattern, key fields |

## Confidence Rules

- `high`: field directly observed in source with clear PIC clause
- `medium`: field inferred from REDEFINES or copybook inclusion
- `low`: field purpose guessed from name alone (no documentation in source)

## Instructions

1. **Read existing inventory** at {output_dir}/inventory/programs.md and
   {output_dir}/inventory/copybooks.md to know which programs and copybooks to analyse.

2. **For each program**, read the source file. Before reading, check file size.

   **Large file handling:** If a source file exceeds 400 lines, read only the
   DATA DIVISION sections (FILE SECTION, WORKING-STORAGE, LINKAGE SECTION,
   LOCAL-STORAGE). Use Grep to locate DIVISION boundaries (search for
   "DATA DIVISION", "PROCEDURE DIVISION"), then read each section with
   offset/limit rather than the full file. Skip the PROCEDURE DIVISION
   entirely -- it is handled by the business-rules worker.

   Extract from each section:

   **FILE SECTION (FD/SD entries):**
   - File name (SELECT ... ASSIGN TO)
   - Organisation (SEQUENTIAL, INDEXED, RELATIVE)
   - Access mode (SEQUENTIAL, RANDOM, DYNAMIC)
   - Record descriptions and field layouts
   - Key fields (for indexed files)

   **WORKING-STORAGE SECTION:**
   - Group items (01-level) and their child fields
   - PIC clauses with data types and sizes
   - VALUE clauses and 88-level condition names
   - REDEFINES relationships
   - OCCURS (array/table) definitions

   **LINKAGE SECTION:**
   - Parameter structures passed via CALL ... USING
   - Document the interface contract between caller and callee

   **LOCAL-STORAGE SECTION** (if present):
   - Thread-local data items

3. **For each copybook**, read the source file and extract:
   - All data item definitions (same analysis as WORKING-STORAGE)
   - Note which programs include this copybook (from inventory)

4. **Identify database operations:**
   - EXEC SQL blocks: extract table names, operation types
     (SELECT/INSERT/UPDATE/DELETE), key columns, host variables
   - EXEC DLI or CALL 'CBLTDLI': extract segment names, operation codes
     (GU/GN/ISRT/REPL/DLET)
   - Indexed file operations: READ/WRITE/REWRITE/DELETE/START (VSAM, ISAM, etc.)

5. **Write artifacts** -- one per file listed below. Do NOT consolidate into a
   single file. Do NOT create files at the parent output directory level.

{_target_files_instruction([
    f"{output_dir}/data/data-dictionary.md",
    f"{output_dir}/data/file-layouts.md",
    f"{output_dir}/data/database-operations.md",
])}

## Output Structure Reference

Follow these canonical section headers and table columns for each artifact:

{_template_section("data-dictionary.md", f"{output_dir}/data/data-dictionary.md")}

{_template_section("file-layouts.md", f"{output_dir}/data/file-layouts.md")}

{_template_section("database-operations.md", f"{output_dir}/data/database-operations.md")}

{draft_section}

6. **Return discoveries** as JSON array.

{_program_scope_note(program)}

Return ONLY a JSON array (no markdown fences) of discovery objects with:
discovery_type, artifact_type, artifact_path, summary, confidence"""
