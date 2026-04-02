# CardDemo -- Credit Card Management System

Example output from the COBOL reverse-engineering tool, generated from the
[AWS CardDemo](https://github.com/aws-samples/aws-mainframe-modernization-carddemo)
sample application.

## Source Application

| Metric | Value |
| --- | --- |
| Programs | 31 COBOL programs (~19,600 LOC) |
| Copybooks | 44 |
| JCL jobs | 35 jobs + 2 procs |
| BMS maps | 17 mapsets |
| CSD definitions | Yes |
| Platform | z/OS, CICS, VSAM (primary), DB2/IMS/MQ (extensions) |
| Domain | Credit card management (accounts, cards, transactions, billing, user admin) |

CardDemo is an AWS-provided sample application for mainframe modernization
scenarios. It implements full credit card lifecycle management: cardholder
authentication, account and customer maintenance, credit card management,
online transaction entry and bill payment, user administration, batch
transaction posting, interest calculation, and statement generation.

The application serves two user roles (regular and admin) across 17 CICS
online transactions and 11 batch jobs, with optional extension modules for
MQ messaging, DB2 transaction types, and IMS pending authorization.

## Generated Artifacts

50 markdown files across 8 artifact categories:

```
├── application.md                  Application overview and 15 key observations
├── inventory/
│   ├── programs.md                 Program inventory with LOC, type, dependencies
│   ├── copybooks.md                Copybook inventory and usage matrix
│   └── jcl-jobs.md                 JCL job inventory and step analysis
├── data/
│   ├── data-dictionary.md          Data structure definitions from copybooks
│   ├── database-operations.md      VSAM/DB2 CRUD operation catalogue
│   └── file-layouts.md             VSAM file and DB2 table layouts
├── flows/
│   ├── program-call-graph.md       CICS XCTL/LINK/CALL dependency graph
│   ├── data-flows.md               Data movement between programs and stores
│   └── batch-flows.md              JCL job step sequences and data flows
├── integration/
│   ├── interfaces.md               External system interfaces and contracts
│   └── io-map.md                   Screen/file/DB I/O per program
├── business-rules/                 31 per-program business rule extractions
│   ├── cosgn00c.md                 Signon / authentication
│   ├── comen01c.md                 Main menu navigation
│   ├── coactupc.md                 Account update (3,860 LOC, 7-state workflow)
│   ├── cobil00c.md                 Bill payment
│   ├── cbtrn02c.md                 Batch transaction posting
│   ├── cbstm03a.md                 Statement generation (ALTER/GO TO)
│   └── ... (25 more)
├── requirements/
│   ├── capabilities.md             Functional capabilities catalogue
│   ├── non-functional.md           NFR analysis (performance, security, etc.)
│   ├── modernization-notes.md      Technical debt and modernization concerns
│   └── implementation-plan.md      9-wave strangler fig migration plan
└── test-specs/
    ├── behavioral-tests.md         BDD-style test specifications
    ├── data-contracts.md           Data contract definitions for testing
    └── equivalence-matrix.md       Old-vs-new equivalence verification matrix
```

## Configuration

Generated using [`examples/carddemo.yaml`](../carddemo.yaml). Key settings:

- **Model**: claude-sonnet-4-6
- **Strategy**: auto (phased, selected for 31 programs)
- **Max iterations**: 5 per phase
- **Convergence**: 2 consecutive stable iterations

## Notable Findings

The analysis surfaced several significant observations:

- **No batch transaction atomicity**: CBTRN02C and CBACT04C update multiple
  VSAM files without SYNCPOINT; CBTRN02C destructively empties the transaction
  master on startup via OPEN OUTPUT
- **Active data integrity defects** in COBIL00C (zero-balance on failed write)
  and CBTRN02C (silent account-update loss on INVALID KEY)
- **COACTUPC complexity**: 3,860 LOC with a 7-state update workflow,
  29-field comparison, concurrent modification detection, and the only
  program using explicit CICS SYNCPOINT -- but with a dual-VSAM partial-update
  risk
- **Plaintext passwords** in the USRSEC VSAM file with no encryption
- **ALTER/GO TO** in CBSTM03A with TIOT control block addressing -- highest
  modernization risk, requires full redesign
- **COCOM01Y ultra-wide coupling**: single COMMAREA structure used by all
  17 online programs as a global state object
- **Transaction ID race condition**: COBIL00C and COTRN02C both generate IDs
  by browsing VSAM backwards for the max value
- **User admin template defects**: shared bugs across COUSR01C-03C from a
  common program template
- **Fee computation stub**: CBACT04C calls 1400-COMPUTE-FEES but the paragraph
  contains only EXIT
- **9-wave strangler fig migration plan** covering 14 data stores,
  11 architectural seams, and a 20-item risk register
