---
name: configure-workspace
description: Configure a COBOL reverse-engineering workspace. Covers config.yaml structure, source directory paths, extensions, settings, and using example configs. Use when setting up a new workspace, changing source paths, adjusting analysis settings, or adapting an example config.
---

# Configuring a Workspace

## config.yaml Structure

The workspace config file has three sections: application name, source paths, and settings.

```yaml
application: CardDemo - Credit Card Management System

source:
  programs:
    - ./source/cbl
  copybooks:
    - ./source/cpy
  jcl: []
  bms: []
  csd: []
  sql: []
  recursive: true
  extensions:
    programs: [.cbl, .cob, .CBL, .COB]
    copybooks: [.cpy, .copy, .CPY, .COPY]
    jcl: [.jcl, .JCL, .prc, .PRC]
    bms: [.bms, .BMS]
    csd: [.csd, .CSD]
    sql: [.sql, .SQL]

output: ./output

settings:
  model: claude-sonnet-4-6
  max_iterations: 5
  n_stable: 2
  confidence_threshold: medium
  strategy: auto
  batch_size: 3
  large_file_threshold: 400
  chunk_threshold: 2000
  staging_dir: ./staging
```

## Source Types

| Type | Required | Purpose |
| --- | --- | --- |
| `programs` | Yes | COBOL program source files |
| `copybooks` | Yes | Copybook include files |
| `jcl` | No | JCL jobs and procedures |
| `bms` | No | CICS BMS screen map definitions |
| `csd` | No | CICS CSD resource definitions |
| `sql` | No | SQL/DDL definitions |

Each type takes a **list of directories** (not individual files). Paths are relative to the workspace root. Set `recursive: true` to scan subdirectories.

Programs and copybooks can share the same directory -- the extension filter separates them.

## Settings Reference

| Setting | Default | Description |
| --- | --- | --- |
| `model` | (none) | Claude model to use (e.g. `claude-sonnet-4-6`) |
| `max_iterations` | 5 | Maximum convergence loop iterations |
| `n_stable` | 2 | Stop after N consecutive empty iterations |
| `confidence_threshold` | medium | Minimum confidence for accepted discoveries |
| `strategy` | auto | Run strategy: `auto`, `default`, `phased` |
| `batch_size` | 3 | Programs per batch in phased mode |
| `large_file_threshold` | 400 | Lines above which agents use line-range reads |
| `chunk_threshold` | 2000 | Lines above which programs are chunked for analysis |
| `staging_dir` | ./staging | Where chunk files are written |

## Using Example Configs

Pre-built configs live in `examples/`. To use one:

```bash
cp examples/carddemo.yaml workspace/config.yaml
```

Then adjust `source` paths to match where you cloned the COBOL repo relative to the workspace.

| Example | Application | Programs | Layout Notes |
| --- | --- | --- | --- |
| `carddemo.yaml` | AWS CardDemo | 31 | Multi-dir, BMS+CSD |
| `cbsa.yaml` | CICS Banking | 29 | 3 JCL dirs, BMS |
| `benchmark-suite.yaml` | COBOL Legacy Benchmark | 42 | Nested subdirs by role |
| `genapp.yaml` | GenApp Insurance | 31 | Mixed programs+copybooks in same dir |
| `cash-account.yaml` | Cash Account | 1 | Minimal, single directory |
| `zbank.yaml` | zBANK | 7 | Repo root, no copybooks |

## Common Configurations

**Minimal (programs + copybooks only):**
```yaml
application: My COBOL App
source:
  programs: [./source]
  copybooks: [./source]
  jcl: []
  bms: []
  csd: []
  sql: []
  recursive: true
output: ./output
settings:
  model: claude-sonnet-4-6
```

**Mixed directory (programs and copybooks co-located):**
```yaml
source:
  programs: [./src]
  copybooks: [./src]
```

**Multiple source directories:**
```yaml
source:
  programs:
    - ./app/online
    - ./app/batch
  copybooks:
    - ./app/copy
    - ./app/copy-bms
```

**External source (absolute path):**
```yaml
source:
  programs:
    - /opt/mainframe/extract/programs
  copybooks:
    - /opt/mainframe/extract/copybooks
```

## Output Directory

Default: `./output` (relative to workspace). Contains subdirectories for each artifact type:

```
output/
├── inventory/       # programs.md, copybooks.md, jcl-jobs.md
├── data/            # data-dictionary.md, file-layouts.md, database-operations.md
├── business-rules/  # {program-slug}.md per program
├── flows/           # program-call-graph.md, batch-flows.md, data-flows.md
├── integration/     # interfaces.md, io-map.md
├── requirements/    # capabilities.md, modernization-notes.md, implementation-plan.md
└── test-specs/      # behavioral-tests.md, data-contracts.md, equivalence-matrix.md
```

## Workspace Directory Structure

After `init` and a run, a workspace contains:

```
workspace/
├── config.yaml             # Config (you edit this)
├── CLAUDE.md               # Agent output conventions (auto-generated)
├── source/                 # Your COBOL files (or symlinks/paths to them)
├── output/                 # Generated artifacts
├── staging/                # Chunked files (auto-managed)
└── .cobol-re-state*.json   # Run state files (auto-managed)
```
