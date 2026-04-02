# Output Conventions

## Directory Structure

All output files MUST be written to subdirectories -- NEVER to the output root.
Do NOT create summary or index files at the output root level.

```text
output/
├── inventory/
│   ├── programs.md
│   ├── copybooks.md
│   └── jcl-jobs.md
├── flows/
│   ├── program-call-graph.md
│   ├── batch-flows.md
│   └── data-flows.md
├── integration/
│   ├── interfaces.md
│   └── io-map.md
├── data/
│   ├── data-dictionary.md
│   ├── file-layouts.md
│   └── database-operations.md
├── business-rules/
│   └── {program-slug}.md   (one per program)
├── requirements/
│   ├── capabilities.md
│   ├── non-functional.md
│   ├── modernization-notes.md
│   └── implementation-plan.md
└── test-specs/
    ├── behavioral-tests.md
    ├── data-contracts.md
    └── equivalence-matrix.md
```

## File Naming

- Lowercase with hyphens for artifact files: `program-call-graph.md`
- UPPERCASE for COBOL program names in frontmatter: `program: ACCT0100`
- Slug form for per-program files: `business-rules/acct0100.md`

## Frontmatter

Every output artifact has YAML frontmatter with:

- `type` -- artifact type (inventory, data, business-rules, flow, integration, requirements, test-specifications)
- `subtype` -- specific artifact (e.g. programs, call-graph, data-dictionary)
- `status` -- draft | reviewed
- `confidence` -- high | medium | low
- `last_pass` -- iteration number that last updated this artifact

Per-program files (`business-rules/{program}.md`) also carry dependency fields:

- `calls`, `called_by`, `uses_copybooks`, `reads`, `writes`, `db_tables`, `transactions`, `mq_queues`
