# Agentic workflow for COBOL Reverse Engineering

An agentic tool that extracts structured requirements, business rules, and dependency information from any COBOL application. It uses the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python) to spawn specialised subagents that analyse COBOL source files, and produces markdown artifacts with consistent structure and machine-readable frontmatter.

Designed for **large mainframe codebases** -- it auto-selects the optimal run strategy based on codebase size, supports flexible source directory layouts, and handles programs up to thousands of lines via chunked analysis.

For the design rationale and architecture behind this tool, see the companion blog post: [Feeding the SDLC factory: extracting requirements from legacy COBOL with agentic workflows](docs/feeding-the-factory.md). For example output from a real COBOL application, see [`examples/cbsa-output/`](examples/cbsa-output/).

## How It Works

The orchestrator auto-selects a **five-phase workflow** for codebases with 10+ programs (the most common real-world scenario):

```text
┌──────────────────────────────┐
│  Phase 1: Cross-cutting      │
│                              │
│  ┌──────────┐  ┌──────────┐  │
│  │Inventory │  │   Flow   │  │
│  │  Worker  │  │  Worker  │  │
│  └────┬─────┘  └────┬─────┘  │
│  ┌────┴─────────────┴─────┐  │
│  │  Integration Worker    │  │
│  └────────────┬───────────┘  │
│         Critic validates     │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│  Phase 2: Per-program sweep  │
│                              │
│  For each program (or batch) │
│  ┌──────────┐  ┌──────────┐  │
│  │ Business │  │   Data   │  │
│  │  Rules   │  │  Worker  │  │
│  │  Worker  │  │          │  │
│  └────┬─────┘  └────┬─────┘  │
│       └──────┬───────┘       │
│        Critic validates      │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Phase 3: Synthesis          │
│                              │
│  Requirements Deriver        │
│  (capabilities, NFRs,        │
│   modernization notes)       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Phase 4: Test Specs         │
│                              │
│  Test Specs Worker           │
│  (behavioral, data           │
│   contracts, equivalence     │
│   matrix)                    │
│  Validator + Critic pass     │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Phase 5: Implementation     │
│                              │
│  Implementation Plan Deriver │
│  (strategy evaluation,       │
│   migration phases,          │
│   risk assessment)           │
└──────────────────────────────┘
```

For small codebases (1-10 programs), all workers run in a single session instead.

### Workers

| Worker                  | What it analyses                                                                 |
| ----------------------- | -------------------------------------------------------------------------------- |
| **inventory**           | Programs, copybooks, JCL, BMS maps, CSD definitions                              |
| **data**                | DATA DIVISION, copybook structures, file layouts, DB operations                  |
| **business-rules**      | PROCEDURE DIVISION logic: conditions, calculations, error handling               |
| **flow**                | CALL chains, PERFORM hierarchies, JCL sequences, BMS screen flows                |
| **integration**         | File I/O, DB, MQ, CICS, CSD mappings, external system boundaries                 |
| **test-specs**          | Stack-agnostic behavioural tests, data contracts, traceability matrix            |
| **implementation-plan** | Strategy evaluation and phased migration plan from capabilities and dependencies |

### Critic

After workers report findings, the **critic subagent** validates consistency: verifying CALL targets exist in the inventory, copybook references resolve, and dependency frontmatter is bidirectionally consistent.

### Requirements Deriver

Synthesises all worker outputs into high-level functional capabilities, non-functional requirements, and modernization notes.

### Test Specifications

Derives stack-agnostic test specifications from all prior artifacts. Produces behavioural test scenarios grouped by capability, data contract tests (format invariants, boundary checks), and a traceability matrix linking every scenario back to business rules and source paragraphs. A deterministic validator auto-corrects coverage arithmetic and checks capability completeness, followed by an LLM critic pass for semantic consistency.

### Implementation Plan

Evaluates migration strategies (strangler fig, rewrite, branch-by-abstraction, parallel run, pipeline replacement) against the actual codebase characteristics, selects the best fit, and produces a phased migration plan grounded in the capabilities, dependency graph, and integration analysis. Identifies natural boundaries, sequences capabilities into migration phases based on dependency order and risk, and produces a concrete roadmap with risk assessments.

## Prerequisites

- Python 3.10+
- An Anthropic API key or AI Gateway endpoint

```bash
pip install -r requirements.txt
```

## Environment Variables

| Variable             | Required | Description                                          |
| -------------------- | -------- | ---------------------------------------------------- |
| `ANTHROPIC_API_KEY`  | Yes      | API key (direct Anthropic) or JWT token (AI Gateway) |
| `ANTHROPIC_BASE_URL` | No       | AI Gateway proxy URL. Omit for direct Anthropic API  |

## Quick Start

```bash
# 1. Initialize a workspace (or clone this repo)
python analyse.py init

# 2. Edit config.yaml -- point source paths at your COBOL files
#    (no need to copy files into prescribed subdirectories)

# 3. Run the analysis (auto-selects optimal strategy)
export ANTHROPIC_API_KEY=sk-ant-...
python analyse.py run
```

The tool scans the configured source directories, counts programs, and automatically runs the best strategy. For a 30+ program codebase like CardDemo, it will run the five-phase workflow without any flags needed.

## Usage

### Default Mode (recommended)

Just run with no flags. The orchestrator sizes the codebase and picks the optimal strategy automatically:

```bash
python analyse.py run
```

For 1-10 programs it runs all workers in a single session. For 11+ programs it auto-selects the five-phase workflow (cross-cutting, per-program sweep, synthesis, test specifications, implementation plan).

### Single Program Mode

```bash
python analyse.py run --program ACCT0100
```

### Worker Selection

Run specific workers only (useful for phased manual runs):

```bash
# Cross-cutting only
python analyse.py run --workers inventory,flow,integration --max-iterations 1

# Per-program depth only
python analyse.py run --workers business-rules,data

# Synthesis only
python analyse.py run --workers requirements --max-iterations 1
```

### Resuming

If a run fails partway through, resume it. Completed programs are skipped:

```bash
python analyse.py run --resume
```

### Staging

Pre-stage large programs into chunks before running analysis:

```bash
python analyse.py stage                     # stage all large programs
python analyse.py stage --program ACCT0100  # stage one program
python analyse.py stage --chunk-threshold 600
```

### Validation

Validate output artifacts against deterministically extracted facts:

```bash
python analyse.py validate
```

### Common Options

```bash
python analyse.py run --dry-run            # report without writing files
python analyse.py run --max-iterations 3   # limit iterations
python analyse.py run --batch-size 5       # parallel programs per window
python analyse.py run --verbose            # debug logging
python analyse.py run --workspace /path    # different workspace
```

## CLI Reference

### `run` -- Run the analysis

| Flag               | Default     | Description                                                                                                              |
| ------------------ | ----------- | ------------------------------------------------------------------------------------------------------------------------ |
| `--program`        | all         | Analyse a single program (e.g. `ACCT0100`)                                                                               |
| `--workers`        | all         | Comma-separated worker list (inventory,data,business-rules,flow,integration,requirements,test-specs,implementation-plan) |
| `--batch-size`     | `3`         | Programs per parallel window in phased mode                                                                              |
| `--dry-run`        | `false`     | Report discoveries without writing files                                                                                 |
| `--max-iterations` | `5`         | Maximum iterations per analysis loop                                                                                     |
| `--n-stable`       | `2`         | Stop after N consecutive iterations with 0 discoveries                                                                   |
| `--resume`         | `false`     | Resume from state files (skips completed programs)                                                                       |
| `--verbose`        | `false`     | Enable debug-level logging                                                                                               |
| `--workspace`      | auto-detect | Path to workspace root                                                                                                   |

### `stage` -- Stage large programs into chunks

| Flag                | Default | Description                                   |
| ------------------- | ------- | --------------------------------------------- |
| `--program`         | all     | Stage a single program                        |
| `--chunk-threshold` | `2000`  | Line count above which a program gets chunked |
| `--workspace`       | auto    | Path to workspace directory                   |
| `--verbose`         | `false` | Enable debug logging                          |

### `validate` -- Validate output artifacts

| Flag          | Default | Description                 |
| ------------- | ------- | --------------------------- |
| `--workspace` | auto    | Path to workspace directory |
| `--verbose`   | `false` | Enable debug logging        |

## Run Strategies

The orchestrator auto-selects based on program count, or you can override explicitly:

| Programs | Auto Strategy | Behaviour                                                                    |
| -------- | ------------- | ---------------------------------------------------------------------------- |
| 1-10     | `default`     | All workers in single session, 2 iterations                                  |
| 11-30    | `phased`      | Cross-cutting → batched sweep (3/batch) → synthesis → test specs → impl plan |
| 30+      | `phased`      | Cross-cutting → per-program sweep → synthesis → test specs → impl plan       |

### Why Phased?

- **Phase 1** (cross-cutting) gives workers the full application view needed for call graphs, integration maps, and inventory
- **Phase 2** (per-program) gives each program focused attention for business rules and data extraction -- large programs don't get lost in the noise
- **Phase 3** (synthesis) reads all artifacts to derive requirements and modernization notes
- **Phase 4** (test specifications) derives stack-agnostic test scenarios from all prior outputs, then validates coverage arithmetic and cross-artifact consistency deterministically before a critic pass
- **Phase 5** (implementation plan) evaluates migration strategies against codebase characteristics and produces a phased migration plan grounded in the capabilities, dependency graph, and risk analysis from all prior phases

## Configuration

`config.yaml` defines source paths (as lists of directories), output location, and analysis settings:

```yaml
application: CardDemo - Credit Card Management System

source:
  programs:
    - ./app/cbl
  copybooks:
    - ./app/cpy
    - ./app/cpy-bms
  jcl:
    - ./app/jcl
    - ./app/proc
  bms:
    - ./app/bms
  csd:
    - ./app/csd
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
```

### Source Types

| Type        | Required | Extensions      | Purpose                                                    |
| ----------- | -------- | --------------- | ---------------------------------------------------------- |
| `programs`  | Yes      | `.cbl`, `.cob`  | COBOL program source                                       |
| `copybooks` | Yes      | `.cpy`, `.copy` | Copybook includes                                          |
| `jcl`       | No       | `.jcl`, `.prc`  | JCL jobs and procedures                                    |
| `bms`       | No       | `.bms`          | CICS BMS screen definitions                                |
| `csd`       | No       | `.csd`          | CICS resource definitions (transaction-to-program mapping) |
| `sql`       | No       | `.sql`          | SQL/DDL definitions                                        |

### Flexible Layouts

The tool works with any directory structure. Programs and copybooks can be in the same directory, different directories, or nested subdirectories. The extension filter separates file types. See `examples/` for configs targeting common open-source COBOL repos.

## Example Configs

Pre-built configs for popular open-source COBOL applications:

| File                            | Application            | Programs | Layout                   |
| ------------------------------- | ---------------------- | -------- | ------------------------ |
| `examples/carddemo.yaml`        | AWS CardDemo           | 31       | Flat, multi-dir, BMS+CSD |
| `examples/cbsa.yaml`            | CICS Banking (CBSA)    | 29       | Flat, 3 JCL dirs, BMS    |
| `examples/benchmark-suite.yaml` | COBOL Legacy Benchmark | 42       | Nested subdirs by role   |
| `examples/genapp.yaml`          | GenApp Insurance       | 31       | Mixed programs+copybooks |
| `examples/cash-account.yaml`    | Cash Account           | 1        | Minimal, mixed dir       |
| `examples/zbank.yaml`           | zBANK                  | 7        | Repo root, no copybooks  |

## Example Output

[`examples/cbsa-output/`](examples/cbsa-output/) contains the full output from analysing [CICS Banking Sample Application (CBSA)](https://github.com/cicsdev/cics-banking-sample-application-cbsa) -- a 29-program CICS/DB2 online banking application. This gives a concrete picture of what the tool produces:

| Directory         | Contents                                                                                       |
| ----------------- | ---------------------------------------------------------------------------------------------- |
| `business-rules/` | 29 per-program business rule extractions with typed dependency frontmatter                     |
| `inventory/`      | Program catalog, copybook catalog, JCL job inventory                                           |
| `data/`           | Data dictionary, file layouts, database operations                                             |
| `flows/`          | Program call graph (with Mermaid diagram), batch flows, data flows                             |
| `integration/`    | Interface catalog and I/O map                                                                  |
| `requirements/`   | Functional capabilities, non-functional requirements, modernization notes, implementation plan |
| `test-specs/`     | Behavioural test scenarios, data contract tests, traceability matrix                           |

## Output Artifacts

| Artifact                              | Description                                   | Dependency Graph Role  |
| ------------------------------------- | --------------------------------------------- | ---------------------- |
| `application.md`                      | Top-level overview                            | Root node              |
| `inventory/programs.md`               | Program catalog                               | Index                  |
| `inventory/copybooks.md`              | Copybook catalog with `used_by`               | Reverse references     |
| `data/data-dictionary.md`             | Data items reference                          | --                     |
| `data/file-layouts.md`                | File descriptions with `read_by`/`written_by` | Reverse references     |
| `business-rules/{prog}.md`            | Per-program rules                             | **Primary graph node** |
| `flows/program-call-graph.md`         | Call topology with Mermaid diagram            | Derived                |
| `integration/interfaces.md`           | External touchpoints with `used_by_programs`  | Reverse references     |
| `requirements/capabilities.md`        | Derived functional capabilities               | Synthesised            |
| `requirements/modernization-notes.md` | Migration observations                        | Synthesised            |
| `test-specs/behavioral-tests.md`      | Stack-agnostic test scenarios by capability   | Derived from all above |
| `test-specs/data-contracts.md`        | Data format invariants & boundary checks      | Derived from all above |
| `test-specs/equivalence-matrix.md`    | Traceability: tests ↔ rules ↔ source          | Derived from all above |
| `requirements/implementation-plan.md` | Strategy evaluation and phased migration plan | Synthesised            |

### Dependency Graph

The per-program `business-rules/{program}.md` files carry typed relationship frontmatter:

```yaml
calls: [ACCT0200, DATE-UTIL]
called_by: [MAIN0100]
uses_copybooks: [ACCT-RECORD, COMMON-DATES]
reads: [ACCT-MASTER, TRANS-INPUT]
writes: [ACCT-REPORT, ERROR-LOG]
db_tables: [ACCOUNT, CUSTOMER]
```

This enables impact analysis, call graph traversal, and data lineage queries by scanning frontmatter across the output directory.

## File Structure

```text
analyse.py            # Thin entry point
orchestrator/
├── __init__.py                      # Shared constants and utilities
├── cli.py                           # CLI argument parsing, command handlers, main()
├── config.py                        # Config loading, defaults, workspace scaffolding
├── agents.py                        # Agent construction, SDK interaction, critic
├── runner.py                        # Run strategies, phased execution, sweep
├── models.py                        # Discovery, ProgramFacts, ProgramManifest dataclasses
├── parser.py                        # Deterministic COBOL structural parser
├── stager.py                        # Chunk staging pipeline and output pre-population
├── state.py                         # State persistence and reporting
├── tracing.py                       # JSONL event logging and optional OTEL tracing
└── validator.py                     # Deterministic artifact validation
prompts/
├── __init__.py
├── _helpers.py                      # Shared prompt builder helpers
├── inventory.py                     # Inventory worker prompt
├── data.py                          # Data worker prompt
├── business_rules.py                # Business rules worker prompt
├── flow.py                          # Flow worker prompt
├── integration.py                   # Integration worker prompt
├── requirements.py                  # Requirements deriver prompt
├── test_specs.py                    # Test specifications worker prompt
├── orchestrator.py                  # Orchestrator prompt and helpers
├── implementation.py                # Implementation plan deriver prompt
└── critic.py                        # LLM critic prompt for corrective passes
templates/
├── application.md
├── program-inventory.md
├── copybook-inventory.md
├── data-dictionary.md
├── file-layouts.md
├── business-rules.md
├── program-call-graph.md
├── interfaces.md
├── capabilities.md
├── modernization-notes.md
├── behavioral-tests.md
├── data-contracts.md
├── equivalence-matrix.md
└── implementation-plan.md
examples/
├── carddemo.yaml                    # AWS CardDemo config
├── cbsa.yaml                        # CICS Banking config
├── cbsa-output/                     # Full example output from CBSA analysis
├── benchmark-suite.yaml             # COBOL Legacy Benchmark config
├── genapp.yaml                      # GenApp Insurance config
├── cash-account.yaml                # Cash Account config
└── zbank.yaml                       # zBANK config
```

---

_Vibe coded with love._
