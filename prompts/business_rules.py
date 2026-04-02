"""Business rules worker prompt -- extracts rules from PROCEDURE DIVISION."""

from __future__ import annotations

from pathlib import Path

from ._helpers import source_context, _program_scope_note, _target_file_instruction, _template_section, _draft_status

from orchestrator import read_template, split_frontmatter

_BR_SCAFFOLD_THRESHOLD: int | None = None


def _get_br_scaffold_threshold() -> int:
    """Compute the byte size of a freshly scaffolded business-rules file.

    Files at or below this size are just frontmatter + empty section headers
    written by ``prepopulate_business_rules`` and should not be treated as
    drafts containing real analysis content.
    """
    global _BR_SCAFFOLD_THRESHOLD
    if _BR_SCAFFOLD_THRESHOLD is None:
        template = read_template("business-rules.md")
        _, body = split_frontmatter(template)
        _BR_SCAFFOLD_THRESHOLD = len(body.encode("utf-8")) + 512
    return _BR_SCAFFOLD_THRESHOLD


def build_business_rules_worker_prompt(
    config: dict,
    program: str | None = None,
    *,
    chunk_path: str | None = None,
    chunk_id: str | None = None,
    data_div_path: str | None = None,
    manifest_path: str | None = None,
    source_path: str | None = None,
    output_file_path: str | None = None,
    workspace: Path | None = None,
) -> str:
    output_dir = config.get("output", "./output")
    if chunk_path:
        return _build_chunked_br_prompt(
            config, program,
            chunk_path=chunk_path,
            chunk_id=chunk_id or "unknown",
            data_div_path=data_div_path or "",
            manifest_path=manifest_path or "",
            source_path=source_path or "",
            output_file_path=output_file_path,
            workspace=workspace,
        )
    target = output_file_path or f"{output_dir}/business-rules/{{program-slug}}.md"
    draft_section = ""
    if workspace:
        draft_section = _draft_status(
            [target], workspace,
            scaffold_threshold=_get_br_scaffold_threshold(),
        )
    return f"""\
You are a COBOL business logic analyst. Your job is to extract business rules,
calculations, validations, and error handling from PROCEDURE DIVISION.

{source_context(config)}

## Rule Extraction Patterns

| COBOL Pattern                    | Rule Type            | What to Extract                       |
| -------------------------------- | -------------------- | ------------------------------------- |
| `IF field = value`               | Validation / Routing | Condition and both branches           |
| `EVALUATE field`                 | Multi-way branch     | All WHEN clauses and actions          |
| `COMPUTE x = ...`               | Calculation          | Formula, inputs, output               |
| `IF SQLCODE NOT = 0`            | Error handling       | Error condition and response          |
| `IF file-status NOT = '00'`     | Error handling       | I/O error and response                |
| `IF DFHRESP(...)`               | CICS error handling  | CICS response check and recovery      |
| `PERFORM ... UNTIL`             | Iteration            | Loop condition and body purpose       |
| `CALL 'PROG' USING`            | Integration          | Called program and parameters         |
| `READ ... UPDATE` then `REWRITE`| Locked update        | Record locking pattern                |
| Compare-all-fields before write  | Optimistic locking   | Concurrent modification detection     |
| `STRING ... DELIMITED BY`       | Format validation    | Input format rules (phone, SSN, date) |
| `88 VALID-xxx`                  | Domain constraint    | Lookup table / valid values list      |

## Paragraph Classification Reference

Paragraph naming conventions vary across COBOL shops. The keyword in the name
(after any numeric or letter prefix) determines its purpose:

| Keyword(s) in name           | Typical purpose                                 | Priority |
| ---------------------------- | ----------------------------------------------- | -------- |
| MAIN, DISPATCH, DRIVER       | Main dispatch, entry point                      | HIGH     |
| EDIT, VALIDATE, COMPARE      | Input validation, field edits                   | HIGH     |
| PROCESS                      | Input processing                                | HIGH     |
| DECIDE, ACTION               | Decision logic                                  | HIGH     |
| SEND, SCREEN, SETUP, SHOW    | Screen management, UI attributes                | LOW      |
| READ, WRITE, GET, STORE      | Data access, file I/O                           | HIGH     |
| CHECK, VERIFY                | Data integrity checks (e.g. optimistic locking) | HIGH     |
| OPEN, CLOSE, DELETE, INSERT  | File or database operations                     | HIGH     |
| *-EXIT                       | Exit paragraphs                                 | SKIP     |

These keywords may appear with any prefix style: `0000-MAIN`, `A100-MAIN`,
`MAIN-PARA`, `PROCESS-FILE`, `READ-MASTER`, etc. Do NOT assume 4-digit numeric
prefixes -- adapt to whatever convention the codebase uses.

## What to Extract Per Paragraph

**Validation rules:** Every IF and EVALUATE that tests a user input or data
field. The specific constraint (e.g., "FICO must be 300-850", not just "FICO
is validated"). The error message text. Whether the field is mandatory or
optional.

**Calculations:** COMPUTE, ADD, SUBTRACT, MULTIPLY, DIVIDE statements.
Document input fields, output field, and the formula/logic. Note any rounding
(ROUNDED) or overflow handling (ON SIZE ERROR).

**Data integrity patterns:** Optimistic locking (compare-before-write
patterns), SYNCPOINT / COMMIT placement, record locking (READ ... UPDATE).

**Error handling:** FILE STATUS checks after I/O, SQLCODE / SQLSTATE checks
after EXEC SQL, DFHRESP checks after EXEC CICS, error messages and ABEND calls.

**Control flow:** PERFORM sequence within the paragraph, PERFORM ... UNTIL
loops, CALL statements with USING parameters, STOP RUN / GOBACK exit points.

**IMPORTANT: Enumerate, don't summarise.** Each validation field, each
constraint value, each error condition must be a separate business rule entry.
"Fields are validated" is not acceptable. "SSN part 1 must be 3 digits, cannot
be 000, 666, or 900-999 per IRS rules" is the level of detail required.

## Common Pitfalls

- **ALTER statements**: rare but can change GOTO targets dynamically -- flag these prominently
- **Copybook PROCEDURE DIVISION includes**: some programs COPY paragraphs -- follow these
- **88-level conditions**: translate to human-readable rule names (e.g., `88 ACCOUNT-ACTIVE VALUE 'A'` means "account status is active")
- **PERFORM THRU**: the range may include paragraphs with fall-through logic
- **Nested IF without END-IF**: older COBOL uses period to end IF scope -- be careful with scope
- **Validation dispatchers**: large programs often have a master paragraph that PERFORMs 15-25 individual validators in sequence. Each validator is a separate business rule -- do NOT collapse them into "inputs are validated"
- **Dead-code literals**: VALUE clauses in WORKING-STORAGE may define file/program names that are never referenced in the PROCEDURE DIVISION. Verify usage before documenting as a dependency

## Quality Checklist

Before writing the business-rules file, verify:

- Every paragraph in your scope has at least one corresponding rule entry
- Validation rules include the **specific constraint** (range, format, valid values), not just "field is validated"
- Error messages from the source are quoted -- they define requirements in business language
- Data integrity patterns (locking, SYNCPOINT, compare-before-write) are documented
- The validation dispatcher paragraph (if present) is fully enumerated -- list every field it validates and which sub-paragraph handles it
- Cross-field validations are documented separately from single-field validations

## Instructions

1. **Read existing inventory and data artifacts** for context:
   - {output_dir}/inventory/programs.md for program list and types
   - {output_dir}/inventory/copybooks.md for copybook cross-references
   - {output_dir}/data/data-dictionary.md for field meanings and data types

2. **For each program**, read the source file. Before reading, check file size.

   **Small files (<=400 lines):** Read the entire file and extract rules directly.

   **Large files (>400 lines):** Use a structure-first, targeted-read strategy.
   Do NOT read sequentially in fixed 200-line ranges -- this causes context
   overflow and forces summarisation instead of detailed extraction.

   **Step 2a: Structural scan (cheap, do this first)**
   Run these Grep calls to build a map of the program before reading any code:
   - Grep pattern: "^\\s{{7}}[A-Z0-9][A-Z0-9][\\w-]*\\."  -> all paragraph names with line numbers
   - Grep pattern: "PROCEDURE DIVISION"       -> start of procedure code
   - Grep pattern: "DATA DIVISION"            -> start of data definitions
   - Grep pattern: "PERFORM "                 -> all PERFORM calls (shows call hierarchy)
   - Grep pattern: "EXEC CICS|EXEC SQL|EXEC DLI"  -> all external operations

   **Step 2b: Read targeted paragraphs**
   For each HIGH-priority paragraph (see the Paragraph Classification table):
   1. Calculate the line range from the paragraph name to its EXIT paragraph
   2. Read that specific line range using Read with offset/limit
   3. Extract rules from that paragraph before moving to the next

   **Step 2c: Read DATA DIVISION for context**
   Read the DATA DIVISION section to understand data structures, 88-level
   condition names, and field definitions. Focus on:
   - 88-level conditions (business-meaningful states)
   - WORKING-STORAGE literals with VALUE clauses that define file names,
     program names, transaction IDs, and other constants used in the
     PROCEDURE DIVISION (these may use any naming convention, not just LIT-*)
   - Fields referenced by the HIGH-priority paragraphs you already read
   - **Literal resolution**: when the procedure code references a data item
     by name (e.g. in `EXEC CICS RETURN TRANSID(some-name)` or
     `EXEC CICS READ FILE(some-name)`), look up the VALUE clause for that
     data item in the DATA DIVISION to find the actual literal value

3. **Build dependency frontmatter** for each program:
   - calls: programs referenced in CALL statements
   - called_by: cross-reference from other programs' CALL statements (use inventory)
   - uses_copybooks: use **Grep** for "COPY " on the source file to find ALL
     copybook references (both COPY NAME and COPY 'NAME' syntax)
   - reads: files with actual I/O statements (not just VALUE clauses)
   - writes: files opened for OUTPUT, EXTEND, or I-O
   - db_tables: tables in EXEC SQL statements
   - transactions: pre-populated in output file -- do not modify
   - mq_queues: queue names in MQ CALL parameters

4. **Write artifacts** to the pre-populated output file:
   - One file per program: {output_dir}/business-rules/{{program-slug}}.md
   - The output file already exists with verified frontmatter and section headers.
     Read it first, then fill in each section with your analysis.
   - Do NOT modify frontmatter values -- they have been verified against source.
   - Set confidence based on complexity:
     - high: straightforward logic, clear conditions
     - medium: nested conditions or complex EVALUATE, reasonable interpretation
     - low: deeply nested logic, GOTO-heavy flow, or unclear intent

{_target_file_instruction(target)}

## Output Structure Reference

Follow these canonical section headers and table columns:

{_template_section("business-rules.md", f"{output_dir}/business-rules/{{program-slug}}.md")}

{draft_section}

5. **Return discoveries** as JSON array.

{_program_scope_note(program)}

Return ONLY a JSON array (no markdown fences) of discovery objects with:
discovery_type, artifact_type, artifact_path, summary, confidence"""


def _build_chunked_br_prompt(
    config: dict,
    program: str | None,
    *,
    chunk_path: str,
    chunk_id: str,
    data_div_path: str,
    manifest_path: str,
    source_path: str,
    output_file_path: str | None = None,
    workspace: Path | None = None,
) -> str:
    output_dir = config.get("output", "./output")
    prog_slug = program.lower() if program else "unknown"
    output_file = output_file_path or f"{output_dir}/business-rules/{prog_slug}.md"
    draft_section = ""
    if workspace:
        draft_section = _draft_status(
            [output_file], workspace,
            scaffold_threshold=_get_br_scaffold_threshold(),
        )

    return f"""\
You are a COBOL business logic analyst performing CHUNK-LEVEL analysis.
You are analysing chunk **{chunk_id}** of program **{program}**.

## Your inputs

1. **Primary analysis target** (read this first):
   {chunk_path}
   This file contains the PROCEDURE DIVISION paragraphs assigned to this chunk.
   It begins with a PROGRAM CONTEXT comment block listing the program's
   transaction ID, file names, program names, and map names (extracted from
   the DATA DIVISION).  Use these resolved literal values for frontmatter.
   Extract every business rule from every paragraph in this file.

2. **DATA DIVISION context** (read this for field definitions):
   {data_div_path}
   Contains WORKING-STORAGE, 88-level conditions, file/program/transaction
   literals, and field definitions.  Use this to understand field meanings,
   valid values, and condition names referenced in the procedure code.

   **CRITICAL -- literal resolution**: When the procedure code references a
   data item by name (e.g. `TRANSID(WS-TRANID)`, `FILE(LIT-ACCTFILENAME)`,
   `DATASET(WS-FILE-NAME)`), you MUST look up the corresponding VALUE clause
   in this data-division file to find the actual literal string.  Do NOT guess
   or infer these values from naming patterns.  Report the VALUE, not the
   data item name.

3. **Program manifest** (reference only -- read if needed):
   {manifest_path}
   Lists all paragraphs with line numbers.  Use this to look up a paragraph
   referenced by PERFORM that is NOT in your chunk file.

4. **Full source file** (fallback -- targeted reads only):
   {source_path}
   If you encounter a PERFORM to a paragraph not in your chunk, use the manifest
   to find its line range and read just that range using Read with offset/limit.

## Rule Extraction Patterns

| COBOL Pattern                    | Rule Type            | What to Extract                       |
| -------------------------------- | -------------------- | ------------------------------------- |
| `IF field = value`               | Validation / Routing | Condition and both branches           |
| `EVALUATE field`                 | Multi-way branch     | All WHEN clauses and actions          |
| `COMPUTE x = ...`               | Calculation          | Formula, inputs, output               |
| `IF SQLCODE NOT = 0`            | Error handling       | Error condition and response          |
| `IF file-status NOT = '00'`     | Error handling       | I/O error and response                |
| `IF DFHRESP(...)`               | CICS error handling  | CICS response check and recovery      |
| `PERFORM ... UNTIL`             | Iteration            | Loop condition and body purpose       |
| `CALL 'PROG' USING`            | Integration          | Called program and parameters         |
| `READ ... UPDATE` then `REWRITE`| Locked update        | Record locking pattern                |
| Compare-all-fields before write  | Optimistic locking   | Concurrent modification detection     |
| `STRING ... DELIMITED BY`       | Format validation    | Input format rules (phone, SSN, date) |
| `88 VALID-xxx`                  | Domain constraint    | Lookup table / valid values list      |

## Common Pitfalls

- **ALTER statements**: rare but can change GOTO targets dynamically -- flag these prominently
- **88-level conditions**: translate to human-readable rule names (e.g., `88 ACCOUNT-ACTIVE VALUE 'A'` means "account status is active")
- **PERFORM THRU**: the range may include paragraphs with fall-through logic
- **Nested IF without END-IF**: older COBOL uses period to end IF scope -- be careful with scope
- **Validation dispatchers**: large programs often have a master paragraph that PERFORMs 15-25 individual validators in sequence. Each validator is a separate business rule -- do NOT collapse them into "inputs are validated"
- **Dead-code literals**: VALUE clauses in WORKING-STORAGE may define file/program names that are never referenced in the PROCEDURE DIVISION. Verify usage before documenting as a dependency

## Target Output File

Your output file is: {output_file}

This file is shared across all chunks of **{program}**. All chunk analyses
contribute to this single file.

**Read this file before writing.** Then follow these rules:
- The frontmatter contains verified program metadata (transaction IDs, file
  names, copybooks, call targets) -- do NOT modify any frontmatter values.
- The file may already contain analysis from previously processed chunks.
  **PRESERVE all existing content** -- do not remove or replace rows, sections,
  or text written by prior chunks.
- **ADD** your chunk's rules as new rows in the Business Rules, Calculations,
  and Error Handling tables. Append after existing rows; continue the row
  numbering from where the last chunk left off.
- If the Program Purpose section already has content, keep it. Add a note only
  if your chunk reveals something the existing description misses.
- If the Control Flow section already has content, keep it. Extend it only if
  your chunk adds steps not yet documented.

## Instructions

1. Read your chunk file ({chunk_path}) completely
2. Read the DATA DIVISION context ({data_div_path}) completely
3. Read the output file ({output_file}) to see any existing content from prior chunks
4. For every paragraph in your chunk, extract:
   - Validation rules with SPECIFIC constraints (ranges, formats, valid values)
   - Calculations with formulas
   - Error handling with conditions and responses
   - Data integrity patterns (locking, compare-before-write)
   - Control flow (PERFORM sequences, CALL statements)
5. **IMPORTANT: Enumerate, don't summarise.** Each validation field, each
   constraint value, each error condition must be a separate rule entry.
6. Write your analysis to the output file, following the Target Output File
   rules above. Extend existing sections -- do not replace them.

## Output Structure Reference

Follow these canonical section headers and table columns:

{_template_section("business-rules.md", output_file)}

{draft_section}

{_program_scope_note(program)}

Return ONLY a JSON array (no markdown fences) of discovery objects with:
discovery_type, artifact_type, artifact_path, summary, confidence"""
