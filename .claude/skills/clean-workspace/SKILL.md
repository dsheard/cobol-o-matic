---
name: clean-workspace
description: Clean a COBOL reverse-engineering workspace for a fresh run. Removes all generated output artifacts, staging files, and run state. Use when asked to clean, reset, or prepare a workspace for a fresh analysis run.
---

# Cleaning a Workspace

Remove all generated artifacts so the workspace is ready for a fresh `run`.

## What to Clean

There are three categories of generated files. Clean all three for a full reset, or selectively clean specific categories.

### 1. Output Artifacts

Generated markdown files under the `output/` directory (path from `config.yaml`).

```
output/
├── business-rules/*.md    # Per-program business rules
├── inventory/*.md         # programs.md, copybooks.md, jcl-jobs.md
├── data/*.md              # data-dictionary.md, file-layouts.md, database-operations.md
├── flows/*.md             # program-call-graph.md, batch-flows.md, data-flows.md
├── integration/*.md       # interfaces.md, io-map.md
└── requirements/*.md      # capabilities.md, modernization-notes.md
```

Remove all `.md` files from each subdirectory. Preserve the empty directories.

### 2. Staging Files

Chunked source files and manifests under the `staging/` directory (path from `config.yaml`, default `./staging`).

```
staging/
├── program-facts.yaml          # Cross-program extracted facts
└── {program-slug}/             # One directory per staged program
    ├── manifest.yaml
    ├── data-division.cbl
    └── chunk-*.cbl
```

Remove everything under `staging/`. Preserve the empty `staging/` directory.

### 3. Run State Files

JSON state files under the `state/` directory that track convergence across iterations.

```
state/
├── .cobol-re-state.json                       # Default/single-program state
├── .cobol-re-state-{program}.json             # Per-program state
├── .cobol-re-state-{program}-{chunk}.json     # Per-chunk state
├── .cobol-re-state-phase1.json                # Phased run state
└── .cobol-re-state-phase3.json
```

Remove everything under `state/`. State files are **dotfiles** (`.cobol-re-state-*.json`), so a bare `state/*` glob will miss them. Use `rm -f state/.cobol-re-state*.json` to match them explicitly. Preserve the empty `state/` directory.

### 4. Lingering Agent Processes

When a run is interrupted (e.g. Ctrl-C, `kill` on the shell), child processes
from the Claude Agent SDK may survive as orphans and continue writing to
output files.  These **must** be killed before starting a fresh run, otherwise
ghost workers from the old run will race against the new run's workers.

Killing the parent shell or Python process is not enough -- you must also
kill the SDK CLI processes and any Python orchestrator children.

Find and kill all related processes:

```bash
ps aux | grep -E "cobol-reverse|claude.*stream-json" | grep -v grep
# Note the PIDs, then:
kill -9 <pid1> <pid2> ...
```

Verify none remain:

```bash
ps aux | grep -E "cobol-reverse|claude.*stream-json" | grep -v grep || echo "All clear"
```

## Steps

1. **Kill lingering processes** from any previous run (see section 4 above).
   Always do this before cleaning, even if you think no run is active.
2. Read `config.yaml` to find the `output` and `settings.staging_dir` paths.
3. Remove `.md` files from each output subdirectory:
   - `output/business-rules/*.md`
   - `output/inventory/*.md`
   - `output/data/*.md`
   - `output/flows/*.md`
   - `output/integration/*.md`
   - `output/requirements/*.md`
   - Any stray `.md` files at the `output/` root (e.g. `call-graph.md`)
4. Remove everything under `staging/` (use `rm -rf staging/*`).
5. Remove state dotfiles (use `rm -f state/.cobol-re-state*.json`).
6. Confirm the workspace is clean by listing the output and staging directories.

## What NOT to Clean

- `config.yaml` -- workspace configuration
- `CLAUDE.md` -- agent output conventions
- `source/` -- COBOL input files
- `.claude/skills/` -- agent skills
- Empty output subdirectories (preserve the directory structure)
