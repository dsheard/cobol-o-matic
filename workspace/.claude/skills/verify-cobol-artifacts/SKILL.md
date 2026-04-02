---
name: verify-cobol-artifacts
description: >-
  Cross-reference and verify claims in COBOL analysis artifacts against
  source code and other artifacts. Use when validating frontmatter fields,
  checking call relationships, confirming transaction IDs, or reviewing
  artifact consistency.
---

# COBOL Artifact Verification Recipes

Use these recipes to verify that analysis artifacts accurately reflect the
source code. Each recipe specifies what to check, where to check it, and
what constitutes a pass or fail.

## Verify Transaction IDs (transactions)

**Claim:** Business-rules frontmatter says `transactions: ["XXXX"]`

**Verification steps:**

1. Grep the source for any variable with TRANID or TRANSID in its name:
   ```
   Grep pattern: "TRANID|TRANSID" on the program source
   ```
2. Read the VALUE clause -- it must match the frontmatter value exactly.
3. Cross-check: grep for `EXEC CICS RETURN.*TRANSID` -- the TRANSID
   variable should resolve to the same value.
4. Cross-check: if CSD files exist, grep for `DEFINE TRANSACTION` to
   confirm the mapping.

**Pass:** VALUE matches frontmatter. All cross-references agree.
**Fail:** VALUE differs from frontmatter, or no TRANSID found but
frontmatter claims one. Log as `correction_needed`.

## Verify Call Relationships (calls, called_by)

**Claim:** Frontmatter says `calls: ["PROGNAME"]`

**Verification steps:**

1. Grep the source for `CALL '`:
   ```
   Grep pattern: "CALL '" on the program source
   ```
2. Every literal in CALL statements should appear in the `calls` list.
3. For `called_by`: check the caller's source for `CALL 'THIS-PROGRAM'`.

**Pass:** All CALL targets match. `called_by` is consistent with callers'
`calls` lists.
**Fail:** Missing CALL target in frontmatter, or `called_by` references a
program that doesn't actually CALL this one. Also check XCTL and LINK.

## Verify File I/O (reads, writes)

**Claim:** Frontmatter says `reads: ["ACCTDAT", "CUSTDAT"]`

**Verification steps:**

1. Grep for actual I/O operations:
   ```
   Grep pattern: "EXEC CICS.*(READ|WRITE|REWRITE|DELETE)|OPEN.*(INPUT|OUTPUT|I-O|EXTEND)" on the source
   ```
2. For CICS: extract `FILE(x)` or `DATASET(x)` from each match.
   For batch: extract file names from OPEN statements and cross-reference with SELECT...ASSIGN.
3. Resolve variable names against DATA DIVISION VALUE clauses.
4. Compare resolved names against frontmatter `reads` and `writes`.

**Pass:** Every file in an I/O statement appears in frontmatter. No
phantom files listed that aren't actually accessed.
**Fail:** File name mismatch (e.g., data item name instead of resolved
VALUE), or file listed but never accessed in an I/O statement.

## Verify Copybooks (uses_copybooks)

**Claim:** Frontmatter says `uses_copybooks: ["COPYNAME1", "COPYNAME2"]`

**Verification steps:**

1. Grep for all COPY statements:
   ```
   Grep pattern: "COPY " on the program source
   ```
2. Also check for DB2 includes:
   ```
   Grep pattern: "EXEC SQL INCLUDE" on the program source
   ```
3. Every copybook name should appear in the frontmatter list.

**Pass:** Complete match between source COPY statements and frontmatter.
**Fail:** Missing copybook or extra copybook not in source.

## Verify Program Count (inventory)

**Claim:** `inventory/programs.md` lists N programs.

**Verification steps:**

1. Glob for source files:
   ```
   Glob pattern: "*.cbl" in each program source directory
   ```
2. Count the files. Compare to the table row count in programs.md.

**Pass:** Counts match exactly.
**Fail:** Mismatch -- programs missing from inventory or extra entries.

## Verify Paragraph Names

**Claim:** Business rules reference paragraph `1000-VALIDATE-INPUT`.

**Verification steps:**

1. Grep the source for the exact paragraph name:
   ```
   Grep pattern: "1000-VALIDATE-INPUT\." on the program source
   ```
   (Include the trailing period -- COBOL paragraph headers end with a period.)
2. The paragraph must exist at column 8 (standard COBOL Area A).

**Pass:** Paragraph found in source at the expected location.
**Fail:** Paragraph name doesn't exist in source -- likely a hallucinated
or misspelled name. Check for similar names.

## Verify Record Lengths

**Claim:** `data/file-layouts.md` says record length is 200 bytes.

**Verification steps:**

1. Read the FD entry and record description in the source.
2. Sum all PIC clause byte sizes (see byte size rules in
   cobol-source-lookup skill).
3. Account for REDEFINES (no extra bytes), OCCURS (multiply), and
   COMP/COMP-3 (packed sizes).

**Pass:** Computed length matches claimed length.
**Fail:** Arithmetic error -- recalculate and report correct value.

## Cross-Artifact Consistency

Check that the same fact is consistent across all artifacts that mention it:

| Fact | Must agree across |
| ---- | ----------------- |
| Transaction ID | business-rules frontmatter, interfaces.md transaction table, call-graph entry points |
| File names | business-rules reads/writes, interfaces.md file table, data file-layouts |
| Call targets | business-rules calls, call-graph edges, flow data-flows |
| Program type | business-rules program_type, inventory programs.md type column |
| Copybooks | business-rules uses_copybooks, inventory copybooks.md used_by |

For each fact type, grep across the relevant artifacts and flag any
disagreements as `correction_needed` discoveries.
