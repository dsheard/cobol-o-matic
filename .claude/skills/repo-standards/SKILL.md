---
name: repo-standards
description: Understand the COBOL reverse-engineering tool structure, workspace layout, and conventions. Use this when asked about how the repository is organized or how to work with it.
---

# Repository Standards

## Tool / Workspace Separation

The tool (code, skills, templates) lives at the repository root. Analysis workspaces live in subdirectories or external paths.

```text
cobol/                              # Tool (code lives here)
├── analyse.py       # Thin CLI entry point
├── orchestrator/                   # Core Python package (config, agents, runner, cli, models, state, parser, stager)
├── prompts/                        # Agent prompt builders (one per worker)
├── templates/                      # Output artifact templates (frontmatter + sections)
├── examples/                       # Reference configs for open-source COBOL apps
├── CLAUDE.md                       # Dev-focused (for IDE agent editing the tool)
└── README.md

workspace/                          # Analysis workspace (agents run here)
├── config.yaml                     # Config: source paths, output dir, settings
├── CLAUDE.md                       # Agent-focused (output conventions)
├── source/                         # COBOL input files
├── output/                         # Generated markdown artifacts
├── staging/                        # Chunked files for large programs
└── .cobol-re-state*.json           # Orchestrator state files (auto-managed)
```

The orchestrator sets `cwd` to the workspace directory when spawning agents. Domain knowledge and template content are embedded directly in prompts by the orchestrator -- agents do not need to read external reference files.

## Source Directory Configuration

Source paths are **lists of directories** in `config.yaml`, relative to the workspace. The tool scans all listed directories for files matching configured extensions.

| Type | Required | Extensions | Purpose |
| --- | --- | --- | --- |
| `programs` | Yes | `.cbl`, `.cob`, `.CBL`, `.COB` | COBOL program source files |
| `copybooks` | Yes | `.cpy`, `.copy`, `.CPY`, `.COPY` | Copybook include files |
| `jcl` | No | `.jcl`, `.JCL`, `.prc`, `.PRC` | JCL jobs and procedures |
| `bms` | No | `.bms`, `.BMS` | CICS BMS screen map definitions |
| `csd` | No | `.csd`, `.CSD` | CICS CSD resource definitions |
| `sql` | No | `.sql`, `.SQL` | SQL/DDL definitions |

## Naming Conventions

- **Artifact files**: lowercase with hyphens: `program-call-graph.md`, `data-dictionary.md`
- **Per-program files**: lowercase slug of program name: `business-rules/acct0100.md`
- **COBOL program names**: UPPERCASE in frontmatter: `program: ACCT0100`
- **Source files**: preserve original casing from mainframe extract

## Design Principles

1. **Prompts are self-contained**: each prompt builder contains the full workflow, domain knowledge, and output templates -- agents need no external file reads
2. **Templates are embedded at runtime**: `templates/` files define frontmatter schema; the orchestrator reads and injects them into prompts
3. **Parser/stager are deterministic**: structural discovery (divisions, paragraphs, chunking) is Python, not LLM
4. **Workspace is data, tool is code**: `workspace/` contains config and I/O; the tool resolves templates by absolute path from `SCRIPT_DIR`

## Key Rules

1. **Read source from configured directories**, write artifacts to `output/`
2. **Use templates** (embedded in prompts) when creating new artifacts
3. **Preserve COBOL program names** in UPPERCASE in frontmatter and references
4. **Use lowercase-hyphen slugs** for filenames
5. **Update `last_pass`** in frontmatter when modifying an existing artifact
6. **Set `confidence`** based on source evidence: `high` = directly observed, `medium` = inferred, `low` = assumption
7. **Use line-range reads** for source files exceeding 400 lines
