---
type: overview
status: draft
confidence: high
last_pass: 1
---

# CICS Banking Sample Application (CBSA)

## Overview

The CICS Banking Sample Application (CBSA) is an IBM-provided reference implementation of a retail banking system running on CICS with DB2 and VSAM. It is a teaching and demonstration application showcasing CICS pseudo-conversational 3270 BMS programming, CICS-to-DB2 integration, VSAM file I/O, CICS Async API usage, and CICS-to-Java connectivity patterns.

The application supports the core operations of a simplified bank branch: customer lifecycle management (create, enquire, update, delete), account lifecycle management (create, enquire, update, delete), and financial transactions (debit, credit, fund transfer). All teller and CSR functions are accessible from a BMS 3270 menu-driven terminal interface. A separate batch program (BANKDATA) provides destructive test-data initialisation.

Two lightweight utility services (GETCOMPY, GETSCODE) are registered in the CICS CSD and intended for consumption by an external Java web UI or REST API layer not included in this source analysis.

---

## Technology Stack

| Component       | Technology                                                 |
| --------------- | ---------------------------------------------------------- |
| Language        | COBOL (Enterprise COBOL for z/OS; CBL options include CICS, SP, EDF) |
| Runtime         | z/OS CICS TS (CICS Transaction Server)                     |
| Database        | DB2 for z/OS (tables: ACCOUNT, PROCTRAN, CONTROL)          |
| File System     | VSAM KSDS (files: CUSTOMER, ABNDFILE)                      |
| Transaction Mgr | CICS (pseudo-conversational 3270 BMS; CICS Async API)      |
| Messaging       | CICS channels/containers (Async API; not MQ)               |
| Batch Scheduler | JES2 (JCL jobs: BANKDATA, COMPALL, DB2 schema jobs)        |
| Build           | IGYCRCTL (Enterprise COBOL compiler), DFHMASP (BMS map generator), DFHCSDUP (CSD utility) |

---

## Entry Points

- **Batch**: BANKDATA.jcl (BANKDAT0 + BANKDAT1 IDCAMS steps + BANKDAT5 IKJEFT01/DSN step); standalone destructive data-initialisation run
- **Online (CICS transactions)**:
  - OMEN -- BNKMENU: main menu, first screen for every teller session
  - ODCS -- BNK1DCS: display / update / delete customer
  - ODAC -- BNK1DAC: display / delete account
  - OCCS -- BNK1CCS: create customer
  - OCAC -- BNK1CAC: create account
  - OUAC -- BNK1UAC: update account
  - OCRA -- BNK1CRA: credit / debit funds
  - OTFN -- BNK1TFN: transfer funds between accounts
  - OCCA -- BNK1CCA: list all accounts for a customer
  - OCR1-OCR5 -- CRDTAGY1-5: async credit-agency stubs (invoked by CRECUST only)
- **Subprograms** (CICS LINK targets, no direct transaction): CREACC, CRECUST, DBCRFUN, DELACC, DELCUS, INQACC, INQACCCU, INQCUST, UPDACC, UPDCUST, XFRFUN, ABNDPROC, GETCOMPY, GETSCODE

---

## Application Boundary

**In scope (analysed):**
- 29 COBOL programs in `/cbsa/src/base/cobol_src`
- 35 copybooks in `/cbsa/src/base/cobol_copy`
- JCL in `/cbsa/etc/install/base/` (installjcl, db2jcl, buildjcl)
- BMS map sources in `/cbsa/src/base/bms_src`

**External / referenced but not in scope:**
- Java web UI layer (`CompanyNameResource.java`) that calls GETCOMPY via CICS LINK
- CICS CSD content (BANK group) loaded by DFHCSDUP; transaction-to-program mappings held externally
- IBM Language Environment routines CEEDAYS, CEELOCT (date validation), CEEGMT, CEEDATM (GMT timestamp) called by CRECUST and BANKDATA
- DB2 subsystem and VSAM file system infrastructure
- Any z/OS Connect or RESTful API layer consuming PROCTRAN or calling GETSCODE
- Programs CEEGMT and CEEDATM referenced by BANKDATA but not present in the analysed source

---

## Key Observations

**Architecture**: The application uses a clean two-tier CICS architecture. BMS screen programs (BNK1xxx) handle presentation and basic field validation; backend service programs (CREACC, CRECUST, DBCRFUN, XFRFUN, etc.) encapsulate business logic and data access. CICS LINK with COMMAREA acts as the service contract. The COMMAREA copybooks (CREACC.cpy, CRECUST.cpy, PAYDBCR.cpy, etc.) are the closest analogue to modern API interface definitions.

**Abend handling**: A centralised abend-logging pattern is implemented across all 23 online programs. Every unrecoverable error path populates an ABNDINFO record and links to ABNDPROC, which writes the record to ABNDFILE VSAM. This provides a single-pane-of-glass for post-incident diagnosis. However, the ABND-TIME field in every record is defective: a pervasive copy-paste bug causes all abend timestamps to display minutes in the seconds position (HH:MM:MM instead of HH:MM:SS).

**Data integrity**: Financial operations (DBCRFUN, XFRFUN) use CICS unit-of-work with explicit SYNCPOINT ROLLBACK to maintain atomicity between ACCOUNT updates and PROCTRAN inserts. XFRFUN implements a deadlock-safe update order (lower account number first) with up to 5 retries on DB2 deadlock. DELCUS uses CICS token-based optimistic locking on CUSTOMER VSAM records.

**Async credit scoring**: CRECUST uses the CICS Async API (RUN TRANSID, channels, containers) to fan out five parallel credit-agency calls (CRDTAGY1-5), waits 3 seconds, then aggregates available scores. The agencies are dummy stubs with random 1-3 second delays, emulating unreliable third-party responses. This is a notable use of the CICS Async API in a COBOL application.

**Sequence number generation**: Both customer and account number allocation use CICS ENQ/DEQ on a sort-code-scoped resource name to serialise access to a VSAM control record (CRECUST) or DB2 CONTROL table row (CREACC). A critical defect exists in CRECUST: if all 100 SYSIDERR retries are exhausted, the retry loop falls through silently to ADD 1 on unread data, which can produce corrupted counter values.

**Technical debt**: Significant dead code exists across the codebase, including IMS PCB pointer artefacts in CICS-only programs, multi-datastore type flags (DLI/DB2/VSAM), unused retry scaffolding, and an entire unreachable CALC-DAY-OF-WEEK section in BANKDATA. The SORTCODE value (987654) is hardcoded as a compile-time literal shared by 18 programs, making it an operational configuration value embedded in binaries.

**Orphan copybooks**: 16 copybooks (including NEWACCNO, NEWCUSNO, PROCISRT, INQACCCZ, INQCUSTZ, DELACCZ) are not referenced by any analysed program. Several appear to define IMS/DL-I compatible variants (z-variants with PIC X(4) instead of POINTER for PCB fields) of active interfaces, suggesting a prior dual-runtime design.

**PROCTRAN as audit trail**: The PROCTRAN DB2 table receives an INSERT for every significant financial and customer lifecycle event (account create, delete; customer create, delete; debit, credit, transfer). No COBOL reader of PROCTRAN was identified; it is almost certainly consumed by an external reporting, reconciliation, or REST API layer.
