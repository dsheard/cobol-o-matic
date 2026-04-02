# CBSA -- CICS Banking Sample Application

Example output from the COBOL reverse-engineering tool, generated from the
[CICS Banking Sample Application (CBSA)](https://github.com/cicsdev/cics-banking-sample-application-cbsa).

## Source Application

| Metric | Value |
| --- | --- |
| Programs | 29 COBOL programs |
| Copybooks | 37 |
| JCL jobs | ~100 (across 3 directories) |
| BMS maps | 10 |
| Platform | z/OS, CICS TS, DB2, VSAM |
| Domain | Retail banking (customer/account CRUD, debit/credit/transfer) |

CBSA is an IBM-provided reference implementation of a retail banking system.
It demonstrates CICS pseudo-conversational BMS programming, CICS-to-DB2
integration, VSAM file I/O, CICS Async API (parallel credit-agency scoring),
and CICS-to-Java connectivity patterns.

## Generated Artifacts

48 markdown files across 8 artifact categories:

```
├── application.md                  Application overview and key observations
├── inventory/
│   ├── programs.md                 Program inventory with LOC, type, dependencies
│   ├── copybooks.md                Copybook inventory and usage matrix
│   └── jcl-jobs.md                 JCL job inventory and step analysis
├── data/
│   ├── data-dictionary.md          Data structure definitions from copybooks
│   ├── database-operations.md      DB2/VSAM CRUD operation catalogue
│   └── file-layouts.md             VSAM/DB2 file and table layouts
├── flows/
│   ├── program-call-graph.md       CICS LINK/XCTL/CALL dependency graph
│   ├── data-flows.md               Data movement between programs and stores
│   └── batch-flows.md              JCL job step sequences and data flows
├── integration/
│   ├── interfaces.md               External system interfaces and contracts
│   └── io-map.md                   Screen/file/DB I/O per program
├── business-rules/                 29 per-program business rule extractions
│   ├── bnkmenu.md                  Main menu navigation
│   ├── bnk1cac.md                  Create account
│   ├── crecust.md                  Create customer (with async credit scoring)
│   ├── dbcrfun.md                  Debit/credit funds
│   ├── xfrfun.md                   Fund transfer (deadlock-safe)
│   └── ... (24 more)
├── requirements/
│   ├── capabilities.md             Functional capabilities catalogue
│   ├── non-functional.md           NFR analysis (performance, security, etc.)
│   ├── modernization-notes.md      Technical debt and modernization concerns
│   └── implementation-plan.md      Strangler fig migration plan
└── test-specs/
    ├── behavioral-tests.md         BDD-style test specifications
    ├── data-contracts.md           Data contract definitions for testing
    └── equivalence-matrix.md       Old-vs-new equivalence verification matrix
```

## Configuration

Generated using [`examples/cbsa.yaml`](../cbsa.yaml). Key settings:

- **Model**: claude-sonnet-4-6
- **Strategy**: auto (phased, selected for 29 programs)
- **Max iterations**: 5 per phase
- **Convergence**: 2 consecutive stable iterations

## Notable Findings

The analysis surfaced several significant observations:

- **Centralised abend logging** via ABNDPROC/ABNDFILE -- but with a pervasive
  timestamp bug (HH:MM:MM instead of HH:MM:SS) across all 23 online programs
- **CICS Async API** usage for parallel credit-agency fan-out in CRECUST
- **Deadlock-safe fund transfer** in XFRFUN (ordered updates with retry)
- **Critical sequence-number defect** in CRECUST where exhausted retries
  silently corrupt the counter
- **16 orphan copybooks** suggesting a prior IMS/DL-I dual-runtime design
- **SORTCODE hardcoded** as a compile-time literal in 18 programs
