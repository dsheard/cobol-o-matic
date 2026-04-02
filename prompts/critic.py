"""Critic prompt -- semantic cross-checks against source code.

Runs as a corrective pass after deterministic validation.  The critic
reads written artifacts, cross-references them against COBOL source,
and fixes issues in place using Write tools.
"""

from __future__ import annotations

from ._helpers import source_context


_INVENTORY_CHECKS = """\
### Inventory artifacts

Files to review:
- {output_dir}/inventory/programs.md
- {output_dir}/inventory/copybooks.md
- {output_dir}/inventory/jcl-jobs.md

Validation checklist:
- Program count in the Programs table matches the number of .cbl/.cob files
  in the source directories (use Glob to count)
- Each program's classification (online/batch/subprogram) is correct:
  - online: source contains EXEC CICS or EXEC DLI with DC calls
  - batch: no online exec statements and not called-only
  - subprogram: has LINKAGE SECTION, no online exec
- uses_copybooks for each program matches ALL COPY statements in source
  (use Grep for "COPY " on each source file to verify)
- Copybook used_by lists are consistent with program COPY statements
- Missing copybooks (COPY references that don't resolve) are flagged
"""

_FLOW_CHECKS = """\
### Flow artifacts

Files to review:
- {output_dir}/flows/program-call-graph.md
- {output_dir}/flows/batch-flows.md
- {output_dir}/flows/data-flows.md

Validation checklist:
- Call graph includes ALL CALL, EXEC CICS LINK, and EXEC CICS XCTL
  statements from source (Grep for "CALL ", "CICS LINK", "CICS XCTL"
  across all programs and compare against the call matrix)
- Entry point programs (never called) are correctly identified
- Leaf programs (never call others) are correctly identified
- Batch flows match JCL EXEC PGM= steps (if JCL is present)
- Data flows correctly identify producer-consumer relationships
  (programs that WRITE a file vs programs that READ it)
"""

_INTEGRATION_CHECKS = """\
### Integration artifacts

Files to review:
- {output_dir}/integration/interfaces.md
- {output_dir}/integration/io-map.md

Validation checklist:
- File interfaces match actual SELECT ... ASSIGN TO statements in source
- Database interfaces match EXEC SQL blocks in source
- CICS interfaces match EXEC CICS SEND MAP / RECEIVE MAP in source
- No false positives from dead-code literals (VALUE clauses in
  WORKING-STORAGE that are never referenced in PROCEDURE DIVISION I/O)
- Verify by Grep-ing for the file/dataset name in actual I/O statements
  (OPEN, READ, WRITE, EXEC CICS READ/WRITE FILE)
"""

_DATA_CHECKS = """\
### Data artifacts

Files to review:
- {output_dir}/data/data-dictionary.md
- {output_dir}/data/file-layouts.md
- {output_dir}/data/database-operations.md

Validation checklist:
- Key data structures cover the major 01-level groups from WORKING-STORAGE
  across programs (spot-check 3-5 programs by reading their DATA DIVISION)
- PIC clauses and field sizes are accurately transcribed
- File layouts match FD entries in source
- Database operations match EXEC SQL blocks (table names, operation types)
"""

_BUSINESS_RULES_CHECKS = """\
### Business-rules artifact

File to review:
- {output_dir}/business-rules/{program_slug}.md

Validation checklist:
- Rules reference paragraph names that actually exist in the source
  (Grep for the paragraph name in the source file)
- Validation rules include SPECIFIC constraints (ranges, formats, values),
  not just "field is validated"
- Error messages are quoted from the source, not paraphrased
- EVALUATE branches are fully enumerated (all WHEN clauses listed)
- Calculations include the actual formula, not just "value is computed"
- The control flow section accurately reflects PERFORM sequences
"""


_TEST_SPECS_CHECKS = """\
### Test specifications artifacts

Files to review:
- {output_dir}/test-specs/behavioral-tests.md
- {output_dir}/test-specs/data-contracts.md
- {output_dir}/test-specs/equivalence-matrix.md

Also read the business-rules files for cross-referencing:
- {output_dir}/business-rules/*.md

Validation checklist:
- Cross-artifact consistency: for each data-contract invariant that asserts
  a field "cannot" or "must not" take certain values, check if any behavioral
  test scenario demonstrates the opposite (e.g. a data contract claiming
  non-LOAN balances cannot be negative while a behavioral test confirms
  teller debits bypass balance checks). Fix the data contract if the
  behavioral test is correct per business rules.
- Equivalence matrix Source Rules column: flag any entry using "Capability-N"
  format instead of "BR-PROGRAM-N". Look up the actual rule in the
  corresponding business-rules file and fix the reference.
- Equivalence matrix Source Paragraphs: flag any entry that says "main section"
  or "Multiple paragraphs" without specific paragraph names and line numbers.
  Look up the actual paragraphs in the source program and fix.
- PROCTRAN type codes: verify that every transaction type code referenced in
  data-contracts.md is a specific literal value, not a description like
  "transfer type". Look up the actual code in the business-rules file for
  the program that writes it.
- Untested Rules completeness: check that known error-handling paths
  (SYNCPOINT ROLLBACK failure, Storm Drain SQLCODE 923, SYSIDERR retries
  in DELCUS) are documented in the Untested Rules table if not covered by
  tests.
"""


def build_critic_prompt(
    config: dict,
    *,
    phase: str,
    program: str | None = None,
) -> str:
    """Build the critic prompt for a given phase.

    phase="phase1": reviews cross-cutting artifacts (inventory, flow,
    integration, data).
    phase="phase2": reviews a single program's business-rules artifact.
    phase="phase4": reviews test-specification artifacts for consistency.
    """
    output_dir = config.get("output", "./output")

    if phase == "phase2" and program:
        return _build_phase2_critic(config, output_dir, program)
    if phase == "phase4":
        return _build_phase4_critic(config, output_dir)
    return _build_phase1_critic(config, output_dir)


def _build_phase1_critic(config: dict, output_dir: str) -> str:
    checks = "\n".join(
        section.format(output_dir=output_dir)
        for section in [
            _INVENTORY_CHECKS,
            _FLOW_CHECKS,
            _INTEGRATION_CHECKS,
            _DATA_CHECKS,
        ]
    )

    return f"""\
You are a senior COBOL architect reviewing analysis artifacts for accuracy.

{source_context(config)}

## Your task

Review the cross-cutting analysis artifacts and fix any errors you find.
You have Write access -- correct issues directly in the output files.

For each artifact, read the output file, then spot-check claims against
the actual COBOL source code using Grep and Read.  Focus on verifiable
facts, not subjective quality.

**Do NOT rewrite entire files.** Only fix specific errors:
- Wrong program classification -> fix the row in the table
- Missing CALL in call graph -> add the missing row
- Wrong file interface direction -> correct it
- Incorrect PIC clause -> fix it

{checks}

## Process

1. Read each artifact file listed above
2. For each checklist item, spot-check by Grep-ing or reading relevant source
3. If you find an error, fix it directly in the artifact using Write
4. After all checks, return a JSON summary:

Return ONLY a JSON array (no markdown fences):
[{{"file": "path", "correction": "description of what was fixed"}}]

If no corrections were needed, return an empty array: []"""



def _build_phase2_critic(config: dict, output_dir: str, program: str) -> str:
    program_slug = program.lower()
    checks = _BUSINESS_RULES_CHECKS.format(
        output_dir=output_dir,
        program_slug=program_slug,
    )

    return f"""\
You are a senior COBOL architect reviewing business-rules analysis for
program **{program}**.

{source_context(config)}

## Your task

Review the business-rules artifact and fix any errors you find.
You have Write access -- correct issues directly in the output file.

Read the artifact, then cross-check claims against the actual source code.

**Do NOT rewrite the entire file.** Only fix specific errors:
- Rule references a paragraph that doesn't exist -> remove or correct it
- Validation rule says "field is validated" without specifics -> add the
  actual constraint from the source code
- Error message is paraphrased instead of quoted -> fix with actual text
- Missing EVALUATE WHEN clause -> add it

{checks}

## Process

1. Read the business-rules file
2. Read the program source (use targeted reads for large files)
3. For each rule, verify the paragraph exists and the logic matches
4. Fix any errors directly in the artifact
5. Return a JSON summary:

Return ONLY a JSON array (no markdown fences):
[{{"file": "path", "correction": "description of what was fixed"}}]

If no corrections were needed, return an empty array: []"""


def _build_phase4_critic(config: dict, output_dir: str) -> str:
    checks = _TEST_SPECS_CHECKS.format(output_dir=output_dir)

    return f"""\
You are a senior COBOL architect reviewing test-specification artifacts
for accuracy and internal consistency.

{source_context(config)}

## Your task

Review the test-specification artifacts and fix any errors you find.
You have Write access -- correct issues directly in the output files.

Read all three test-spec artifacts, then cross-check claims against the
business-rules artifacts and each other.  Focus on verifiable facts and
internal consistency, not subjective quality.

**Do NOT rewrite entire files.** Only fix specific errors:
- Data-contract invariant contradicts a behavioral test -> fix the invariant
- "Capability-N" source rule reference -> replace with actual BR-PROGRAM-N ID
- Vague paragraph reference ("main section") -> replace with specific paragraph
- Descriptive type code ("transfer type") -> replace with actual literal value
- Missing untested-rule entry -> add it to the Untested Rules table

{checks}

## Process

1. Read all three test-spec artifacts
2. Read the business-rules files referenced by the equivalence matrix
3. For each checklist item, verify by reading the relevant business-rules file
4. If you find an error, fix it directly in the artifact using Write
5. After all checks, return a JSON summary:

Return ONLY a JSON array (no markdown fences):
[{{"file": "path", "correction": "description of what was fixed"}}]

If no corrections were needed, return an empty array: []"""
