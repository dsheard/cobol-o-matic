---
name: run-analysis
description: Run the COBOL reverse-engineering tool. Covers init, stage, and run commands with all CLI options, strategies, and worker selection. Use when asked to run, execute, or operate the analysis tool, or when troubleshooting a run.
---

# Running the Analysis Tool

## Prerequisites

- Python 3.10+
- `pip install -r requirements.txt` (claude-agent-sdk, pyyaml, python-dotenv)
- `ANTHROPIC_API_KEY` env var (direct API) or `ANTHROPIC_BASE_URL` + `ANTHROPIC_API_KEY` (AI gateway)

## Commands

### init -- Scaffold a Workspace

```bash
python analyse.py init
python analyse.py init --workspace /path/to/workspace
```

Creates `workspace/` with `config.yaml`, `CLAUDE.md`, `source/`, `output/` subdirectories. After init, edit `config.yaml` to point at your COBOL source files.

### stage -- Pre-chunk Large Programs

```bash
python analyse.py stage                          # stage all programs
python analyse.py stage --program COACTUPC       # stage one program
python analyse.py stage --chunk-threshold 600    # override line threshold
```

Deterministically splits programs exceeding `chunk_threshold` lines into paragraph-grouped chunks in `staging/`. The `run` command auto-stages, so explicit staging is only needed for inspection or custom thresholds.

### run -- Execute Analysis

```bash
python analyse.py run                            # auto-strategy (recommended)
python analyse.py run --program ACCT0100         # single program
python analyse.py run --workers inventory,flow   # specific workers only
python analyse.py run --dry-run                  # report without writing files
python analyse.py run --resume                   # continue a failed run
python analyse.py run --verbose                  # debug logging
python analyse.py run --workspace /path/to/ws    # explicit workspace path
```

## Run Strategies

The `strategy` setting in `config.yaml` (or auto-detected) controls the workflow:

| Programs | Auto Strategy | Behaviour                                                                          |
| -------- | ------------- | ---------------------------------------------------------------------------------- |
| 1-10     | `default`     | All workers in a single session, multi-iteration convergence                       |
| 11+      | `phased`      | Phase 1-5: cross-cutting -> per-program sweep -> synthesis -> tests -> impl plan   |

Override in config: `settings.strategy: default | phased | auto`

### Phased Workflow

- **Phase 1**: inventory, flow, integration, data workers (full codebase view)
- **Phase 2**: business-rules worker (per-program, batched)
- **Phase 3**: requirements deriver (synthesises all outputs)
- **Phase 4**: test-specs deriver (stack-agnostic test specifications from business rules and requirements)
- **Phase 5**: implementation-plan deriver (evaluates migration strategies and creates a phased migration plan from capabilities and dependencies)

## Workers

| Worker                | Scope         | What it produces                                                                                        |
| --------------------- | ------------- | ------------------------------------------------------------------------------------------------------- |
| `inventory`           | Cross-cutting | `inventory/programs.md`, `inventory/copybooks.md`, `inventory/jcl-jobs.md`                              |
| `flow`                | Cross-cutting | `flows/program-call-graph.md`, `flows/batch-flows.md`, `flows/data-flows.md`                            |
| `integration`         | Cross-cutting | `integration/interfaces.md`, `integration/io-map.md`                                                    |
| `data`                | Cross-cutting | `data/data-dictionary.md`, `data/file-layouts.md`, `data/database-operations.md`                        |
| `business-rules`      | Per-program   | `business-rules/{program-slug}.md`                                                                      |
| `requirements`        | Synthesis     | `requirements/capabilities.md`, `requirements/modernization-notes.md`                                   |
| `test-specs`          | Synthesis     | `test-specs/behavioral-tests.md`, `test-specs/data-contracts.md`, `test-specs/equivalence-matrix.md`    |
| `implementation-plan` | Synthesis     | `requirements/implementation-plan.md`                                                                   |

Select specific workers: `--workers inventory,data,business-rules`

## CLI Flags

| Flag               | Default     | Description                                      |
| ------------------ | ----------- | ------------------------------------------------ |
| `--program`        | all         | Analyse a single program                         |
| `--workers`        | all         | Comma-separated worker list                      |
| `--batch-size`     | 3           | Programs per batch in phased mode                |
| `--dry-run`        | false       | Report discoveries without writing files         |
| `--max-iterations` | 5           | Maximum convergence iterations                   |
| `--n-stable`       | 2           | Stop after N empty iterations                    |
| `--resume`         | false       | Resume from state files, skip completed programs |
| `--verbose`        | false       | Debug-level logging                              |
| `--workspace`      | auto-detect | Path to workspace root                           |

## Workspace Auto-detection

The tool searches for `config.yaml` in this order:

1. `./workspace/` subdirectory of cwd
2. cwd itself
3. `./workspace/` subdirectory of the script directory
4. Script directory itself

## Convergence

Each iteration spawns workers, then a critic validates findings. The loop stops when either:

- `max_iterations` is reached, or
- `n_stable` consecutive iterations produce zero new discoveries

## Chunked Programs

Programs exceeding `chunk_threshold` lines are automatically staged into paragraph-grouped `.cbl` chunk files. The business-rules worker runs once per chunk, with each chunk agent contributing to a single `{program-slug}.md` output file (appending to existing content from prior chunks). After all chunks complete, coverage is validated against high-priority paragraphs.

## Typical Workflows

**First run on a new codebase:**

```bash
python analyse.py init
# Edit workspace/config.yaml (see configure-workspace skill)
export ANTHROPIC_API_KEY=sk-ant-...
python analyse.py run
```

**Re-run a single program after source changes:**

```bash
python analyse.py run --program ACCT0100
```

**Resume a failed multi-program run:**

```bash
python analyse.py run --resume
```

**Preview what the tool would do:**

```bash
python analyse.py run --dry-run
```
