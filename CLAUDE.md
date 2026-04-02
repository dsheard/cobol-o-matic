# COBOL Reverse Engineering Tool

An agentic tool that reverse-engineers COBOL applications into structured markdown artifacts. Uses the Claude Agent SDK to spawn specialised subagents.

## Directory Layout

```text
analyse.py       # Thin CLI entry point
orchestrator/                   # Core Python package
├── __init__.py                 #   Shared constants and utilities
├── models.py                   #   Dataclasses (Discovery, Paragraph, Chunk, Manifest)
├── state.py                    #   State persistence and convergence tracking
├── parser.py                   #   Deterministic COBOL structural parser
├── stager.py                   #   Chunk staging pipeline
├── validator.py                #   Deterministic artifact validation
├── tracing.py                  #   JSONL event logging and optional OTEL tracing
├── config.py                   #   Config loading, defaults, workspace scaffolding
├── agents.py                   #   Agent construction, SDK interaction, critic
├── runner.py                   #   Run strategies, phased execution, sweep
└── cli.py                      #   CLI argument parsing, command handlers, main()
prompts/                        # Agent prompt builders (one per worker)
├── _helpers.py                 #   Shared helpers (_source_context, _read_template, etc.)
├── inventory.py                #   Inventory worker prompt
├── data.py                     #   Data worker prompt
├── business_rules.py           #   Business rules worker prompt (+ chunked variant)
├── flow.py                     #   Flow worker prompt
├── integration.py              #   Integration worker prompt
├── requirements.py             #   Requirements-deriver prompt
├── test_specs.py               #   Test-specs-deriver prompt
├── implementation.py           #   Implementation-plan-deriver prompt
├── critic.py                   #   LLM critic prompt for corrective passes
└── orchestrator.py             #   Orchestrator prompt and helpers
templates/                      # Output artifact templates (frontmatter schema + sections)
examples/                       # Reference configs for open-source COBOL apps
workspace/                      # Analysis workspace (agents run here)
├── config.yaml                 #   Config: source paths, output dir, settings
├── CLAUDE.md                   #   Agent-focused output conventions
├── source/                     #   COBOL input files
├── output/                     #   Generated markdown artifacts
├── staging/                    #   Chunked files for large programs
├── state/                      #   Run state JSON files (convergence tracking)
└── logs/                       #   JSONL event logs and agent transcripts
```

## Design Principles

- **Platform-agnostic**: the tool works with any COBOL codebase -- CICS, IMS, batch-only, DB2, VSAM, MQ, or any combination. Never hardcode assumptions about a specific application (e.g., CardDemo) or middleware. Variable naming conventions, transaction ID patterns, and file I/O styles vary across codebases; code and prompts must handle them generically.
- **Prompts are self-contained**: each prompt builder contains the full workflow, domain knowledge, and output templates -- agents need no external file reads for reference material
- **Templates are embedded at runtime**: `templates/` files define frontmatter schema and section structure; the orchestrator reads them in Python and injects content into prompts via `_read_template()`
- **Parser/stager are deterministic**: all structural discovery (divisions, paragraphs, chunking) is Python, not LLM -- agents only do semantic interpretation
- **Workspace is data, tool is code**: `workspace/` contains config and I/O; the tool resolves its own assets (templates) by absolute path from `SCRIPT_DIR`

## Key Files When Editing

| File                        | Purpose                                                                                          |
| --------------------------- | ------------------------------------------------------------------------------------------------ |
| `analyse.py`                | Thin entry point (delegates to `orchestrator.cli`)                                               |
| `orchestrator/cli.py`       | CLI argument parsing, command handlers, main()                                                   |
| `orchestrator/config.py`    | Config loading, defaults, workspace scaffolding                                                  |
| `orchestrator/agents.py`    | Agent construction, SDK interaction, worker maps, critic                                         |
| `orchestrator/runner.py`    | Run strategies, phased execution, sweep, analysis loop                                           |
| `orchestrator/parser.py`    | COBOL paragraph extraction, classification, chunk building                                       |
| `orchestrator/stager.py`    | Writes chunk files and manifest.yaml                                                             |
| `orchestrator/models.py`    | `Paragraph`, `Chunk`, `ProgramManifest` dataclasses                                              |
| `orchestrator/validator.py` | Deterministic validation of output artifacts (frontmatter, sections, strays)                     |
| `orchestrator/tracing.py`   | JSONL event logging and optional OTEL tracing                                                    |
| `prompts/*.py`              | Agent prompt builders -- one file per worker, plus orchestrator and helpers                      |
| `prompts/critic.py`         | LLM critic prompt builder for post-analysis corrective pass                                      |
| `templates/*.md`            | Frontmatter schema and section structure for each artifact type (embedded in prompts at runtime) |

## Platform-Agnostic Rules

When editing parser, stager, prompts, templates, or skills:

- Do NOT reference specific application names (CardDemo, GenApp, zBANK, etc.) outside of `examples/`
- Do NOT hardcode COBOL variable naming conventions from a single codebase (e.g., `LIT-THISTRANID` as the only transaction ID pattern). Use regex patterns broad enough to match common conventions.
- Transaction IDs: match any variable with TRANID/TRANSID in its name, not specific variable names
- File I/O: use the unified `file_reads` field in `ProgramFacts`, not separate CICS/batch fields
- Program type: detect online programs via both `EXEC CICS` and `EXEC DLI` / `CALL 'CBLTDLI'`
- Frontmatter uses `transactions` (not `cics_transactions`) for transaction ID lists
- Examples in skills/docs should use generic placeholders (`[PROG-NAME]`, `[TRAN-ID]`) rather than names from a specific codebase

## Running

```bash
python analyse.py init                    # scaffold workspace/
python analyse.py run                     # auto-strategy
python analyse.py stage --program PROG    # stage one program
python analyse.py run --program PROG      # analyse one program
python analyse.py run --resume            # continue a killed/failed run
```

## Debugging and Observability

Every run writes structured events to `workspace/logs/run-{timestamp}.jsonl`. No extra dependencies required.

### JSONL Event Log

The log captures agent lifecycle events, subagent start/stop, tool calls, errors, and span timing:

```bash
# Watch events in real time
tail -f workspace/logs/run-*.jsonl

# Find errors
jq 'select(.event == "sdk_error")' workspace/logs/run-*.jsonl

# See subagent durations
jq 'select(.event == "span_end")' workspace/logs/run-*.jsonl

# Find which subagents ran for a specific program
jq 'select(.iteration | test("COACTUPC"))' workspace/logs/run-*.jsonl
```

Event types: `session_init`, `subagent_started`, `subagent_completed`, `tool_use`, `sdk_error`, `span_start`, `span_end`, `phase_skipped`, `critic_init`, `critic_success`, `transcript_captured`.

### Agent Transcripts

When subagents complete, their SDK transcript files are automatically copied to `workspace/logs/transcript-{label}-{id}`. These contain the full agent conversation including all tool calls and responses -- useful for diagnosing incorrect output or understanding agent reasoning.

### OpenTelemetry Tracing (Optional)

For distributed tracing with spans, configure an OTLP endpoint:

```yaml
# In config.yaml
settings:
  otel_endpoint: http://localhost:4318
  otel_service_name: cobol-reverse-engineer # optional, this is the default
```

Or via environment variable:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

Install the optional dependencies:

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
```

This produces parent-child spans for each phase, program batch, chunk, and iteration -- viewable in Jaeger, Grafana Tempo, or any OTEL-compatible backend.

### Run State Files

Per-phase and per-program state is persisted in `workspace/state/` as JSON. These track iterations, discoveries, artifacts written, and completion status. The `--resume` flag uses these to skip completed work:

```bash
# Check what's completed
jq '.completed_at' workspace/state/.cobol-re-state-phase1.json
jq '.completed_at' workspace/state/.cobol-re-state-*.json
```

## Allowed File Types

| Allowed | Extensions                                |
| ------- | ----------------------------------------- |
| Yes     | `.md`, `.yaml`, `.yml`, `.json`, `.py`    |
| Yes     | `.cbl`, `.cob`, `.cpy`, `.copy`, `.jcl`   |
| Yes     | `.bms`, `.csd`, `.sql`, `.prc`            |
| No      | `.txt`, `.xlsx`, `.csv`, `.docx`, `.pptx` |
