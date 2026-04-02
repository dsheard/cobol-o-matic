---
type: overview
status: draft
confidence: high
last_pass: 5
---

# CardDemo Credit Card Management System

## Overview

CardDemo is a credit card management application written in IBM Enterprise COBOL targeting the z/OS platform. It provides a full-lifecycle credit card servicing capability: cardholder authentication and session management, account and customer record maintenance, credit card management, online transaction entry and bill payment, user administration, batch transaction posting, monthly interest calculation, account statement generation, and transaction reporting.

The application serves two user roles: regular users access account, card, and transaction functions through the main menu (COMEN01C); admin users access user security management and transaction type administration through the admin menu (COADM01C). A signon program (COSGN00C) authenticates both roles against a VSAM user security file and routes accordingly.

The core application (app/cbl) comprises 31 programs (~19,600 LOC) across 17 CICS online transactions and 11 batch jobs. Three optional extension modules extend the platform with IBM MQ messaging (VSAM-MQ account and date inquiry services), DB2 transaction type administration, and IMS-based pending authorization management with MQ integration.

The application is structured on AWS Mainframe Modernization (AWS M2) datasets, with all VSAM dataset names prefixed `AWS.M2.CARDDEMO.*`.

## Technology Stack

| Component       | Technology               |
| --------------- | ------------------------ |
| Language        | IBM Enterprise COBOL (z/OS dialect; EXEC CICS, EXEC SQL, EXEC DLI) |
| Runtime         | z/OS (MVS); Language Environment (LE/370) |
| Database        | VSAM KSDS (primary, 10 core files); DB2 (extension: transaction types); IMS/DL-I (extension: pending authorization) |
| Transaction Mgr | CICS (online programs); IMS/TM (extension: authorization module) |
| Messaging       | IBM MQ Series (extension: VSAM-MQ module); JES internal reader (CORPT00C report submission via JOBS TDQ) |
| Batch Scheduler | JES2 (z/OS job entry subsystem); DFSORT / SYNCSORT (sort utility) |
| Screen I/O      | BMS (Basic Mapping Support); 17 mapsets compiled into CICS load library; BMS source (.bms) files not present in source set |
| Auxiliary Tools | IDCAMS (VSAM management), IEBGENER (data copy), DFHCSDUP (CSD maintenance), FTP, REXX TXT2PDF |

## Entry Points

- **Online (CICS)**: Transaction CC00 / program COSGN00C is the primary entry point for all online users. From signon, users are routed to either the admin menu (CA00 / COADM01C) or the regular-user main menu (CM00 / COMEN01C). All 17 core CICS transactions are accessible only after authentication.
- **Batch**: Key batch entry points are POSTTRAN (CBTRN02C -- daily transaction posting), INTCALC (CBACT04C -- interest calculation), CREASTMT (CBSTM03A -- statement generation), TRANREPT (CBTRN03C -- transaction reporting), CBEXPORT/CBIMPORT (data migration), and READACCT/READCARD/READCUST/READXREF/WAITSTEP (diagnostic and utility jobs).
- **Subprograms**: CSUTLDTC (date validation utility, called by CORPT00C and COTRN02C) and CBSTM03B (VSAM file I/O subprogram, called by CBSTM03A).
- **MQ-triggered (extension)**: CICS transactions CDRA (COACCT01, account inquiry) and CDRD (CODATE01, date inquiry) are triggered via MQ bridge; CICS transaction CP00 (COPAUA0C, authorization processor) is triggered by authorization events on an MQ queue.

## Application Boundary

**In scope**: All programs in `/app/cbl` (31 programs), copybooks in `/app/cpy` and `/app/cpy-bms` (44 copybooks), JCL in `/app/jcl` and `/app/proc` (35 jobs, 2 procs), and the CICS CSD definition job (CBADMCDJ).

**Extension modules (analysed but separately deployed)**:
- `app-vsam-mq/`: COACCT01, CODATE01 (MQ account and date inquiry services)
- `app-transaction-type-db2/`: COTRTLIC, COTRTUPC, COBTUPDT (DB2 transaction type maintenance)
- `app-authorization-ims-db2-mq/`: COPAUS0C, COPAUS1C, COPAUS2C, COPAUA0C, CBPAUP0C (IMS pending authorization)

**External systems referenced but not in scope**:
- CEE3ABD, CEEDAYS (z/OS Language Environment system routines)
- MVSWAIT (MVS sleep service)
- COBDATFT (date conversion utility; source not found)
- COCRDSEC (CDV1 developer transaction; source not found)
- IBM MQ broker (queues: CARDDEMO.REQUEST.QUEUE, CARD.DEMO.REPLY.ACCT/DATE/ERROR)
- IMS subsystem (PSB PSBPAUTB, segments PAUTSUM0/PAUTDTL1)
- DB2 subsystem (plan AWS01PLN/CARDDEMO; table CARDDEMO.TRANSACTION_TYPE)
- JES internal reader (job submission from CORPT00C via JOBS TDQ)
- DFSORT/SYNCSORT, IDCAMS, IEBGENER (system utilities)

## Key Observations

1. **No transaction atomicity in batch**: The two most critical batch programs (CBTRN02C and CBACT04C) update multiple VSAM files sequentially without SYNCPOINT or any rollback mechanism. A mid-job abend leaves data in a partially updated state. CBTRN02C also performs a destructive OPEN OUTPUT on TRANSACT-FILE at startup, meaning an abend leaves the transaction master empty.

2. **Active data integrity defect in CBTRN02C**: When an account REWRITE fails (INVALID KEY) in paragraph 2800-UPDATE-ACCOUNT-REC, reason code 109 is set but no reject record is written and no abend occurs. The corresponding transaction is written to TRANSACT-FILE as if it succeeded, permanently desynchronizing the account balance and the transaction record.

3. **Two active data integrity defects in COBIL00C**: (a) The account balance is reduced to zero unconditionally after a TRANSACT WRITE attempt, even if the write failed with DUPKEY or another error, producing a zero-balance account with no payment record. (b) The program cannot process the first-ever bill payment when the TRANSACT file is empty, because STARTBR NOTFND blocks the ID generation path before the empty-file seed logic can execute.

4. **Plaintext passwords**: User passwords are stored as 8-character PIC X fields in the USRSEC VSAM file with no encryption or hashing. This is a security liability that must be addressed before or during any data migration.

5. **ALTER/GO TO in CBSTM03A**: The statement generation program uses the deprecated ALTER verb to dynamically redirect a GO TO target at runtime. Combined with TIOT (Task I/O Table) control block addressing for DD enumeration, CBSTM03A is the highest-risk program for modernization and cannot be directly translated; it requires complete redesign.

6. **COCOM01Y ultra-wide coupling**: The CARDDEMO-COMMAREA structure (COCOM01Y) is used by all 17 online programs as the primary inter-program communication channel. It acts as a global state object carrying user identity, role, navigation context, and account context. Any schema change requires coordinated updates across the entire online application.

7. **Missing TRAN-ACCT-ID in transaction master**: TRAN-RECORD (CVTRA05Y) has no account ID field. Any query of TRANSACT that needs account context must re-join through CARDXREF using TRAN-CARD-NUM. This is an architectural data model constraint that must be corrected during migration.

8. **Fee computation not implemented**: CBACT04C contains a paragraph 1400-COMPUTE-FEES that is called after every interest calculation but contains only EXIT. No fee logic exists in the current codebase.

9. **Transaction ID generation race condition**: Both COBIL00C and COTRN02C generate new transaction IDs by browsing the TRANSACT VSAM backwards to find the current maximum ID. Concurrent online sessions could generate duplicate IDs.

10. **Overlimit check uses cycle-only balance**: CBTRN02C checks `ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + transaction_amount` against the credit limit, excluding any prior-cycle carry-forward balance in ACCT-CURR-BAL. This is either an intentional billing-cycle design or a defect depending on the product rules.

11. **No audit trail for online updates**: Online programs COACTUPC, COCRDUPC, COUSR02C, and COUSR03C perform direct VSAM REWRITE or DELETE operations with no before/after audit record. A modernized system must introduce audit logging at the service layer for all write and delete operations.

12. **Missing source programs**: COCRDSEC (CDV1 transaction) and several older-generation programs (COACT00C, COACTDEC, COTRNVWC, COTRNVDC, COTRNATC, COTSTP1C-4C, COADM00C) are defined in the CSD but have no corresponding .cbl source file in the analysed directory.

13. **User administration template defects**: COUSR01C, COUSR02C, and COUSR03C share multiple behavioral anomalies originating from a shared program template: unchecked CICS RECEIVE RESP codes (all three programs silently continue with stale BMS map input on receive failure), double BMS SEND on normal read path (COUSR02C and COUSR03C), dead CONTINUE statements in EVALUATE structures (COUSR02C and COUSR03C), and unused modifier flags (COUSR03C). Additionally, COUSR01C does not enforce the 'A'/'U' domain for user type at data entry, and has commented-out commarea field propagation (user ID and user type not forwarded on PF3 navigation). COUSR02C has a PF3 unconditional-XCTL defect where validation errors are ignored on exit. COUSR03C issues a DELETE call even when the preceding READ UPDATE fails. These defects should be reviewed in COUSR00C as well.

14. **CSUTLDTC date-echo corruption**: A post-call MOVE in CSUTLDTC (line 122) overwrites the WS-DATE PIC X(10) echo field with the binary VString group structure, corrupting bytes 1-2. Current callers are unaffected because they do not read the date echo from LS-RESULT, but any new consumer of CSUTLDTC that parses the TstDate sub-field will receive garbled data.

15. **COACTUPC is the most sophisticated online program**: At 3,860 LOC, COACTUPC implements a 7-state update workflow (ACUP-CHANGE-ACTION state machine) with 29-field old-vs-new comparison, concurrent modification detection, and US-specific validation rules (SSN, FICO score, state code, state/zip cross-validation, North America area code). It is the only online program that issues an explicit CICS SYNCPOINT (on PF3 exit). However, the dual-VSAM write in 9600-WRITE-PROCESSING (ACCTDAT then CUSTDAT) has no spanning commit, creating a partial-update risk if the second write fails.
