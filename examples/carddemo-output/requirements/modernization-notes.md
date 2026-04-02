---
type: requirements
subtype: modernization-notes
status: draft
confidence: high
last_pass: 5
---

# Modernization Notes

Observations relevant to migrating or modernizing this COBOL application, derived from the reverse-engineering analysis.

## Complexity Assessment

| Metric                    | Value |
| ------------------------- | ----- |
| Total programs            | 31 (core); 8 additional in extension modules |
| Total copybooks           | 27 (cpy/) + 17 (cpy-bms/) = 44 total |
| Total LOC                 | ~19,600 (core 31 programs); largest single program COACTUPC at 3,860 LOC. Previous estimate of ~15,900 was an undercount; exact sum from program inventory is 19,609 LOC. |
| Avg cyclomatic complexity | TBD (estimated medium-high; COACTUPC at 3,860 LOC and COCRDLIC at 1,458 LOC and COCRDUPC at 1,560 LOC are the most complex online programs; CBTRN02C at 731 LOC is the most complex batch program) |
| External integrations     | 9 (CEE3ABD, MVSWAIT, COBDATFT, CEEDAYS, DFHCSDUP, SORT, IDCAMS, JES internal reader, IBM MQ in extensions) |
| Database tables           | 0 (core VSAM only); 2 DB2 tables in extension module; 1 IMS database in extension module |
| VSAM files                | 10 core KSDS files; 3 VSAM AIX paths; multiple GDG datasets |
| CICS transactions         | 17 core (CC00, CM00, CA00, CB00, CCLI, CCDL, CCUP, CAVW, CAUP, CR00, CT00, CT01, CT02, CU00, CU01, CU02, CU03); 4 in extension modules (CDRA, CDRD, CP00, CPVS/CPVD) |
| JCL jobs                  | 35 (jcl/ + proc/) |

## Technical Debt

| Issue        | Programs Affected | Severity          | Description   |
| ------------ | ----------------- | ----------------- | ------------- |
| ALTER/GO TO dispatch | CBSTM03A | High | CBSTM03A uses ALTER statements to dynamically redirect a single GO TO target at runtime for file-open dispatch. ALTER is a deprecated COBOL verb with no direct equivalent in modern languages and obscures control flow entirely. |
| Silent data loss on account REWRITE failure | CBTRN02C | High | When REWRITE FD-ACCTFILE-REC INVALID KEY fires in 2800-UPDATE-ACCOUNT-REC, reason code 109 is set but no reject record is written and no abend occurs. The transaction is written to TRANSACT-FILE as if it succeeded, creating a permanent inconsistency between account master and transaction file. |
| Account balance reduced after failed TRANSACT write | COBIL00C | High | In PROCESS-ENTER-KEY, the COMPUTE ACCT-CURR-BAL and PERFORM UPDATE-ACCTDAT-FILE execute unconditionally after WRITE-TRANSACT-FILE, regardless of whether the write succeeded or failed. A DUPKEY or other write error produces a zero-balance account with no payment record. |
| First-ever bill payment fails on empty TRANSACT | COBIL00C | High | When TRANSACT contains no records, EXEC CICS STARTBR with RIDFLD(HIGH-VALUES) returns DFHRESP(NOTFND), blocking the payment. The READPREV ENDFILE seed path (intended to initialise transaction ID = 1) is unreachable in this case. The program cannot process the very first bill payment to an empty transaction file. |
| Unconditional debug DISPLAY in production | CBACT04C | High | Line 193 issues DISPLAY TRAN-CAT-BAL-RECORD unconditionally for every TCATBAL record processed. On a large file this produces high-volume SYSOUT output with no guard condition. This is a debug artifact left in production code. |
| Plaintext password storage | COSGN00C, COUSR01C, CSUSR01Y | High | SEC-USR-PWD is stored as PIC X(08) in USRSEC VSAM. No encryption, hashing, or salting is applied. Passwords are compared with direct character equality. |
| No transaction boundaries in batch | CBTRN02C, CBACT04C | High | Neither CBTRN02C nor CBACT04C uses SYNCPOINT or any equivalent commit/rollback mechanism. Multi-file updates are not atomic. Mid-job failures produce partially updated data with no way to roll back. |
| COACTUPC partial dual-VSAM write risk | COACTUPC | High | 9600-WRITE-PROCESSING rewrites ACCTDAT and then CUSTDAT sequentially. If ACCTDAT succeeds but CUSTDAT fails the account and customer records are left inconsistent. No SYNCPOINT or rollback is issued between the two writes. This is distinct from the CICS task-level commit which occurs on RETURN. |
| No account lockout | COSGN00C | Medium | There is no failed-attempt counter, lockout policy, or throttling mechanism in the authentication logic. Brute-force attacks against the 8-character password space are not mitigated. |
| Transaction ID generation race condition | COBIL00C, COTRN02C | Medium | Both programs generate the next transaction ID by performing a backwards STARTBR/READPREV on TRANSACT to find the current maximum. No locking is held during the generation; concurrent online sessions could generate duplicate IDs. |
| Destructive OPEN OUTPUT on TRANSACT-FILE | CBTRN02C | Medium | CBTRN02C opens TRANSACT-FILE OUTPUT (truncating all prior content) before processing begins. A mid-job abend leaves the TRANSACT VSAM empty. The TRANBKP job must be run before POSTTRAN to protect against data loss. |
| Last-failing-check-wins in validation | CBTRN02C | Medium | Both the overlimit check (reason 102) and the expiration check (reason 103) run without a short-circuit in 1500-B-LOOKUP-ACCT. If both conditions fail, only reason 103 is recorded in the reject record. |
| Overlimit check excludes prior-cycle balance | CBTRN02C | Medium | WS-TEMP-BAL uses only ACCT-CURR-CYC-CREDIT and ACCT-CURR-CYC-DEBIT; prior-cycle carry-forward in ACCT-CURR-BAL is excluded. A customer with large prior-cycle balance could exceed the limit undetected until cycle reset. |
| Missing account ID in TRAN-RECORD | CBTRN02C, CVTRA05Y, all TRANSACT writers | Medium | TRAN-RECORD (CVTRA05Y) has no TRAN-ACCT-ID field. Any query of TRANSACT that needs account context requires a join through CARDXREF on TRAN-CARD-NUM. This is an architectural data model gap. |
| TIOT control block addressing in CBSTM03A | CBSTM03A | Medium | CBSTM03A intentionally accesses the MVS Task I/O Table (TIOT) via POINTER arithmetic to enumerate DD names at runtime. This z/OS-specific technique has no equivalent in Linux or cloud runtimes and would require significant redesign. |
| No audit trail for online updates | COACTUPC, COCRDUPC, COUSR02C, COUSR03C | Medium | Online COACTUPC and COCRDUPC perform direct VSAM REWRITE operations without writing any before/after audit record. COACTUPC's 29-field compare detects what changed but does not persist the change log. COUSR02C and COUSR03C similarly write no record of user account changes or deletions. A modernized system will need to add audit logging at the service layer for all write operations. |
| COUSR02C PF3 ignores update outcome | COUSR02C | Medium | When the operator presses PF3, MAIN-PARA calls UPDATE-USER-INFO then unconditionally XCTLs away without checking WS-ERR-FLG. If a mandatory field is blank or a CICS I/O error occurs, an error screen is briefly sent but the program transfers control immediately. PF5 does not have this defect. |
| COUSR03C DELETE after failed READ | COUSR03C | Medium | DELETE-USER-INFO evaluates NOT ERR-FLG-ON once before calling both READ-USER-SEC-FILE and DELETE-USER-SEC-FILE. If READ sets ERR-FLG-ON (NOTFND or unexpected error), DELETE still executes on the CICS file position. The DELETE returns NOTFND (no data corruption), but an unnecessary CICS call is issued on every failed user lookup. |
| COUSR02C / COUSR03C redundant BMS SEND operations | COUSR02C, COUSR03C | Low | READ-USER-SEC-FILE unconditionally sends the screen on NORMAL response. When called from UPDATE-USER-INFO or PROCESS-ENTER-KEY, the subsequent paragraphs also send the screen, resulting in 2-3 SEND MAP calls per interaction. The final send overwrites the earlier ones; no visible defect but unnecessary BMS I/O. |
| Shared template defects in user admin programs | COUSR01C, COUSR02C, COUSR03C | Low | COUSR01C, COUSR02C, and COUSR03C share multiple defects originating from a common program template: unchecked CICS RECEIVE RESP codes (BMS receive errors silently ignored and processing continues with stale input), dead CONTINUE statements in EVALUATE WHEN branches (COUSR02C line 335, COUSR03C line 282), and double BMS SEND on normal read path. COUSR01C additionally has commented-out commarea propagation (user ID and user type are not forwarded on navigation away). COUSR00C should be reviewed for the same class of defects. |
| CSUTLDTC date-echo corruption in LS-RESULT | CSUTLDTC | Low | MOVE WS-DATE-TO-TEST TO WS-DATE at line 122 corrupts the TstDate sub-field of LS-RESULT with binary VString length bytes. Current callers (CORPT00C, COTRN02C) do not parse that field, so there is no functional impact; but any future consumer reading the date echo from LS-RESULT will receive garbled data in positions 1-2. |
| DISCGRP error message mislabel | CBACT04C | Low | The error message for DISCGRP-FILE open failure reads 'ERROR OPENING DALY REJECTS FILE'. This is a copy-paste error; the file is the Disclosure Group interest rate file. |
| Copy-paste error in DALYREJS close | CBTRN02C | Low | 9300-DALYREJS-CLOSE moves XREFFILE-STATUS to IO-STATUS instead of DALYREJS-STATUS. DALYREJS close failure diagnostics show the XREF file status. |
| Typo in field name ACCT-EXPIRAION-DATE | CBTRN02C, CVACT01Y | Low | Field name is missing the 'T' in EXPIRATION. No functional impact but affects search, tooling, and maintenance. |
| Dead/stub paragraph 1400-COMPUTE-FEES | CBACT04C | Low | The fee computation paragraph contains only EXIT. Fees are never calculated. Whether this was intentional deferral or an omission is unknown. |
| CARDOUT DD missing from CBIMPORT.jcl | CBIMPORT | Low | CBIMPORT.cbl declares SELECT CARD-OUTPUT ASSIGN TO CARDOUT but no matching DD statement exists in CBIMPORT.jcl. Card import output may fail silently or abend depending on the COBOL runtime's handling of missing DD names. |
| Unused copybook UNUSED1Y | (none) | Low | UNUSED1Y.cpy defines a user data record layout but is not referenced by any analysed program. It is dead code at the copybook level. |
| Programs defined in CSD but absent from source | COCRDSEC, COACT00C, COACTDEC, COTRNVWC, COTRNVDC, COTRNATC, COTSTP1C-4C, COADM00C | Medium | These programs are referenced in the CSD definition file but no matching .cbl source was found. They may represent superseded, removed, or separately maintained programs. Their absence creates gaps in the recoverable application model. |
| CBTRN01C has no JCL entry point | CBTRN01C | Low | CBTRN01C is a full batch validation program (495 LOC) but no JCL job was found that invokes it. It may be a development/test artifact or the JCL may be maintained elsewhere. |
| Double-space in bill payment success message | COBIL00C | Low | The STRING statement in WRITE-TRANSACT-FILE produces 'Payment successful.  Your Transaction ID is...' with two adjacent spaces between "successful." and "Your" due to two consecutive literal strings. |
| Dead CONTINUE statements in user admin programs | COUSR02C, COUSR03C | Low | Multiple dead CONTINUE statements appear in WHEN branches of EVALUATE structures in COUSR02C (lines 335, 154, 212) and COUSR03C (line 282). These are syntactically valid no-ops indicating copy-paste template residue or removed code; no functional impact. |
| Unused WS-USR-MODIFIED flag in COUSR03C | COUSR03C | Low | WS-USR-MODIFIED is initialised to USR-MODIFIED-NO at line 85 but is never set to USR-MODIFIED-YES in the PROCEDURE DIVISION. The flag has no effect on program behavior and is dead code from a shared template. |
| COBSWAIT has no input validation or error handling | COBSWAIT | Low | Non-numeric SYSIN value, missing SYSIN, or MVSWAIT failure are all silently ignored or produce undefined behavior. As a utility program with no file or database I/O this is low operational risk, but makes the program fragile in automated pipelines. |

## Modernization Risks

| Risk               | Impact            | Likelihood        | Mitigation             |
| ------------------ | ----------------- | ----------------- | ---------------------- |
| COCOM01Y ultra-wide coupling | High | High | COCOM01Y (CARDDEMO-COMMAREA) is used by all 17 online programs as the primary inter-program communication mechanism. Any schema change ripples to every online program. Map this to a structured API contract before refactoring. |
| CVACT01Y shared by 11 programs | High | High | The account record copybook (CVACT01Y, 300-byte KSDS layout) is used by 11 programs. Changes to the account schema require coordinated updates across the entire application. Version the schema and introduce an adapter layer. |
| CVTRA05Y shared by 11 programs | High | High | The transaction master record copybook is used by 11 programs spanning both online and batch. Same risk as CVACT01Y. Missing TRAN-ACCT-ID must be added during migration, requiring changes to all 11 consumers. |
| ALTER/GO TO in CBSTM03A | High | High | The ALTER verb is not supported in many modern COBOL compilers and has no equivalent in Java, Python, or Go. CBSTM03A must be fully redesigned, not translated. |
| TIOT addressing in CBSTM03A | High | High | Accessing MVS control blocks via POINTER arithmetic is entirely z/OS-specific. Replacing this with a configurable file name list or environment variables is required for any non-mainframe target. |
| No transaction atomicity in batch | High | Medium | The batch posting chain (POSTTRAN, INTCALC, COMBTRAN) relies on successful sequential execution with no rollback. Modernization to a database-backed system must introduce explicit transaction management. |
| Pseudoconversational CICS navigation model | High | High | All 17 online programs use a CICS XCTL model with CARDDEMO-COMMAREA for state propagation. This is not directly portable to REST APIs or web frameworks. Each XCTL hop must be decomposed into a service boundary with stateless API design. |
| Existing data integrity defects in COBIL00C and CBTRN02C | High | High | Three production defects (COBIL00C balance-after-failed-write, COBIL00C first-payment, CBTRN02C silent account update loss) may have already produced corrupted data in production VSAM files. Data migration must include a reconciliation pass to detect and repair these inconsistencies before cutover. |
| COACTUPC dual-VSAM write without spanning transaction | High | Medium | 9600-WRITE-PROCESSING rewrites ACCTDAT and then CUSTDAT sequentially without a SYNCPOINT between the two writes. The account and customer records can diverge if the second write fails. The modernized account update endpoint must wrap both writes in a single database transaction. |
| REDEFINES chains in CVEXPORT | Medium | Medium | CVEXPORT uses a multi-level REDEFINES structure for the 5-record-type export file (C/A/X/T/D). Modern languages do not support REDEFINES semantics natively; explicit union/discriminated union types are required. |
| BMS mapset dependency | Medium | High | All online screens are defined as BMS mapsets compiled into load modules. No source BMS files are present in the source set; only the compiled copybooks (cpy-bms/) exist. Reconstructing the screen layouts requires either regenerating BMS from the copybooks or screen-scraping. |
| Missing source for CSD-referenced programs | Medium | Medium | COCRDSEC (CDV1 transaction) and several older-generation programs are in the CSD but not in the source. The application cannot be fully rebuilt without these programs. Assess whether they are still active. |
| CEE3ABD dependency | Low | High | All 11 batch programs call CEE3ABD (LE abend handler). This is a z/OS Language Environment routine. On non-z/OS targets, abend handling must be replaced with structured exception handling. |
| GDG datasets | Low | Medium | Several output datasets use GDG (Generation Data Group) patterns for version management. Cloud or Linux environments do not have native GDG support; a file naming convention with rotation logic must be implemented. |
| Tight coupling between CBTRN02C and TRANSACT-FILE | High | High | CBTRN02C performs a destructive OPEN OUTPUT on TRANSACT-FILE at the start of every run. Any modernization that introduces incremental or idempotent processing must change this fundamental design. |
| Plaintext credentials in USRSEC | High | High | All password migration and authentication modernization must include hashing/encryption of credentials. The 8-character plaintext password is a security liability. Existing USRSEC data must be re-hashed before or during migration. |
| Shared control flow template defects in user admin programs | Low | Medium | COUSR01C, COUSR02C, and COUSR03C share defects originating from a shared program template (dead CONTINUE statements, double SEND, unchecked RECEIVE RESP, dead modifier flags, commented-out commarea field propagation). Any modernization that auto-translates these programs from COBOL will carry the same defects into the target system unless the behavioral anomalies are explicitly corrected during translation. COUSR00C should also be reviewed for the same class of defects before translation. |

## Decomposition Candidates

Programs or program groups that could be extracted as independent services or modules:

| Candidate | Programs   | Rationale                     | Dependencies         |
| --------- | ---------- | ----------------------------- | -------------------- |
| Authentication Service | COSGN00C | Self-contained: reads only USRSEC, produces only a session token equivalent (COMMAREA fields). No other program writes login logic. | USRSEC VSAM; COCOM01Y for session fields |
| User Management Service | COUSR00C, COUSR01C, COUSR02C, COUSR03C | Tightly grouped by shared USRSEC file and CSUSR01Y copybook. Only accessible from COADM01C. All four programs form a clean CRUD boundary. Behavioral anomalies in COUSR01C, COUSR02C, and COUSR03C should be corrected in the target implementation. | USRSEC VSAM; CSUSR01Y; COADM01C navigation |
| Account Inquiry/Update Service | COACTVWC, COACTUPC | Both operate on ACCTDAT + CUSTDAT + CARDXREF. COACTUPC is the largest and most complex online program (3,860 LOC) but its data model is well-defined. The 29-field compare-before-write and 7-state machine logic should be preserved as an optimistic-concurrency update pattern in the replacement service. The dual-VSAM write without a spanning SYNCPOINT must be corrected to a single database transaction. | CVACT01Y, CVCUS01Y, CVACT03Y; COCOM01Y |
| Credit Card Service | COCRDLIC, COCRDSLC, COCRDUPC | All three share CVCRD01Y, CVACT02Y, and CXACAIX/CARDAIX/CARDDAT. They form a self-contained card management subsystem with clear in/out navigation via COCRDLIC as hub. | CVACT02Y, CVCRD01Y, CARDDAT; COCOM01Y |
| Transaction Management Service | COTRN00C, COTRN01C, COTRN02C | All three operate on TRANSACT VSAM and share CVTRA05Y. COTRN02C additionally validates via CSUTLDTC. Natural bounded context for transaction entry and view. | CVTRA05Y, CVACT01Y, CVACT03Y, CSUTLDTC |
| Bill Payment Service | COBIL00C | Single-purpose payment processor. Clear inputs (account, card lookup) and outputs (TRANSACT write + ACCTDAT update). Could be exposed as a payment API. Data integrity defects must be resolved before extraction. | CVACT01Y, CVTRA05Y, CVACT03Y; COCOM01Y |
| Daily Transaction Posting Pipeline | CBTRN02C | Self-contained batch pipeline. Consumes DALYTRAN, produces updates to TRANSACT/TCATBALF/ACCTDAT and rejects to DALYREJS. Natural microservice or scheduled job boundary. | CVTRA06Y, CVTRA05Y, CVACT01Y, CVACT03Y, CVTRA01Y |
| Interest Calculation Service | CBACT04C | Self-contained batch: reads TCATBALF, DISCGRP, XREF, ACCTDAT; produces SYSTRAN and updates ACCTDAT. No shared state with other batch programs during execution. | CVTRA01Y/02Y, CVACT01Y, CVACT03Y; DISCGRP reference data |
| Statement Generation Pipeline | CBSTM03A, CBSTM03B | The statement generation pipeline (CREASTMT JCL + CBSTM03A + CBSTM03B) is end-to-end self-contained. Output is STATEMNT.PS and STATEMNT.HTML. However CBSTM03A requires significant refactoring due to ALTER and TIOT. | COSTM01, CUSTREC, CVACT01Y, CVACT03Y |
| Date Validation Utility | CSUTLDTC | Already a standalone subprogram. Maps directly to a utility function in any modern language. Only dependency is CEEDAYS LE API (replaceable with a standard date library). The VString post-call overwrite defect (LS-RESULT date echo corruption) should be corrected in the replacement. | CEEDAYS; called by CORPT00C, COTRN02C |
| Data Migration Pipeline | CBEXPORT, CBIMPORT | Loosely coupled to operational system (reads only; no shared transaction boundary with other programs). Good candidate for a one-time migration service. CARDOUT JCL omission must be fixed. | CVEXPORT REDEFINES layout; all master VSAM files |

## Data Migration Considerations

| Data Store | Type                | Volume Indicators    | Migration Notes  |
| ---------- | ------------------- | -------------------- | ---------------- |
| ACCTDATA (ACCTDAT) | VSAM KSDS | 300-byte records; no volume indicator in source | Primary account master; key is ACCT-ID PIC 9(11). Alternate index path (CXACAIX) must be migrated or rebuilt. 12 fields including credit limit, balance, cycle credit/debit, expiry date, group ID. Add ACCT-ID as foreign key on all transaction records during migration. |
| CUSTDATA (CUSTDAT) | VSAM KSDS | 500-byte records; no volume indicator | Customer master; key is CUST-ID PIC 9(09). Contains SSN (PIC 9(09)), date of birth, FICO score; data classification considerations for migration. PII fields require encryption at rest in target system. |
| CARDDATA (CARDDAT) | VSAM KSDS | 150-byte records; no volume indicator | Card master; key is CARD-NUM PIC X(16). Has AIX by account (CARDAIX). Card number is a PAN (Primary Account Number); PCI DSS compliance considerations apply. |
| CARDXREF | VSAM KSDS | 50-byte records; shared by 11 programs | Card-to-account cross-reference; key is XREF-CARD-NUM. Also has alternate index (CXACAIX) keyed by account. Critical join table. Denormalize into CARD or TRANSACTION table in target to eliminate runtime joins. |
| TRANSACT | VSAM KSDS | 350-byte records; truncated and rebuilt each POSTTRAN run | Transaction master; key is TRAN-ID PIC X(16). No TRAN-ACCT-ID field; account linkage requires join via CARDXREF. GDG backup pattern used in batch pipeline. Add ACCT-ID column during migration. Pre-migration data reconciliation needed to detect balance/transaction inconsistencies from known CBTRN02C and COBIL00C defects. |
| TCATBALF | VSAM KSDS | 50-byte records; composite key (account + type + category) | Transaction category balance; acts as a pre-aggregated summary table. Content is ephemeral (cleared on interest calculation). Can be replaced by a database view or computed field in the target schema. |
| USRSEC | VSAM KSDS | 8-char key; no volume indicator | User security file. Passwords are plaintext PIC X(08); must be re-hashed (bcrypt or Argon2) before or during migration. User type domain is single character ('A'/'U'). Note: COUSR01C does not forward user ID and user type on commarea navigation (commented-out code at RETURN-TO-PREV-SCREEN lines 172-173); this is a source-level anomaly only and does not affect the VSAM record itself. |
| DISCGRP | VSAM KSDS | Interest rate lookup; static reference data | Disclosure group interest rates. Key is group ID + type code + category code. Must include a 'DEFAULT' record for each type/category combination used in TCATBALF. Default records are not documented; required set must be catalogued before migration. |
| TRANTYPE / TRANCATG | VSAM KSDS | Small reference tables; loaded from DB2 extract (extension) | Transaction type and category description lookup tables. In the extension module these are mastered in DB2 (CARDDEMO.TRANSACTION_TYPE) and extracted to VSAM for batch. If migrating to a single database, these can be normalised as lookup tables. |
| GDG datasets (DALYREJS, TRANREPT, SYSTRAN, TRANSACT.BKUP) | Sequential GDG | Generation-managed | GDG semantics (versioned generations) must be replaced with a rotation or partitioned file naming scheme. Each GDG consumer depends on a specific generation offset (+1 or 0). |
| EXPORT.DATA | VSAM KSDS | 500-byte multi-record; 5 record types via REDEFINES | Used for branch migration only. The REDEFINES layout (CVEXPORT) must be decoded into a discriminated union or typed message format for any non-COBOL consumer. |
| DB2 TRANSACTION_TYPE | DB2 table | Small reference table | Extension module only. Schema is partially recoverable from SQL in COTRTLIC/COTRTUPC/COBTUPDT. Primary key is TR_TYPE. |
| IMS DBPAUTP0 | IMS hierarchical DB | Variable; pending auth records | Extension module only. Root segment PAUTSUM0 (keyed by account ID) with child segment PAUTDTL1. Must be migrated to a relational or document store with parent-child relationship preserved. |

## Patterns Observed

Notable coding patterns, idioms, or anti-patterns that affect modernization strategy:

- **Pseudo-conversational CICS pattern**: All 17 online programs use EXEC CICS RETURN TRANSID(same-tranid) COMMAREA(CARDDEMO-COMMAREA) to maintain state between user interactions. Each screen interaction is a separate CICS task. This maps to a stateless REST API + session token pattern in a modernized system; the COMMAREA fields become JWT claims or a session object.

- **CDEMO-PGM-CONTEXT flag for first-entry detection**: All online programs test CDEMO-PGM-CONTEXT (88 CDEMO-PGM-ENTER VALUE 0, CDEMO-PGM-REENTER VALUE 1) to distinguish a fresh entry from a return visit. This is equivalent to initializing component state on mount versus resuming from existing state.

- **Dynamic XCTL routing via COMMAREA fields**: COMEN01C uses CDEMO-MENU-OPT-PGMNAME(WS-OPTION) as the XCTL target, making the navigation table data-driven. COCRDLIC uses CCARD-NEXT-PROG. This pattern is loosely equivalent to a router with a lookup table; it is moderately easy to modernize to URL routing but requires cataloguing all possible target program names.

- **CEE3ABD as batch termination handler**: All 11 batch programs call CEE3ABD USING ABCODE (999), TIMING (0) for unrecoverable errors. This produces a z/OS system abend dump. In a modernized environment this should be replaced with structured exception logging and process exit codes.

- **DB2-format timestamp construction in COBOL**: Multiple programs (CBTRN02C, CBACT04C) manually construct YYYY-MM-DD-HH.MM.SS.CC0000 timestamp strings using STRING from FUNCTION CURRENT-DATE components. This is straightforward to replace with a standard library datetime formatter.

- **Backwards STARTBR/READPREV for max ID generation**: COBIL00C and COTRN02C both generate new transaction IDs by browsing TRANSACT backwards to find the current maximum. This is a fragile, race-prone pattern that must be replaced with a sequence generator or UUID in a modernized system. COBIL00C additionally cannot process the first-ever payment when the file is empty.

- **File status two-byte binary overlay**: CBTRN02C, CBACT04C, and other batch programs decode the VSAM file status code by overlaying the two status bytes as TWO-BYTES-BINARY (COMP) to produce a displayable four-digit status. This is a common mainframe idiom with no equivalent needed in modern databases.

- **PERFORM THRU with fall-through in CBSTM03A**: CBSTM03A uses PERFORM THRU patterns combined with ALTER/GO TO, creating implicit fall-through control flow. This is one of the hardest COBOL patterns to decompose because the effective entry and exit points of a paragraph can change at runtime.

- **REDEFINES for multi-record-type file processing**: CVEXPORT uses REDEFINES to overlay five different record type layouts at the same memory address, selected by a type code in the header. This maps to a discriminated union (sealed class hierarchy) in object-oriented or functional languages. Each record type must be explicitly modeled as a distinct type during migration.

- **Shared 15-field COMMAREA as global state**: CARDDEMO-COMMAREA (COCOM01Y, ~15 fields) carries user ID, user type, customer ID, account ID, and navigation context for the entire session. All 17 online programs depend on this structure. It is a global mutable state object; its replacement requires careful API contract design to avoid over-broad coupling in the modernized system.

- **TIOT traversal for runtime DD enumeration**: CBSTM03A accesses the MVS Task I/O Table via POINTER ADDRESS OF arithmetic to enumerate DD names at runtime. This is an advanced z/OS-specific technique used as an alternative to a hardcoded file dispatch table. It must be replaced with a configuration-driven or environment-variable-driven approach in any non-z/OS runtime.

- **Unconditional post-write processing in COBIL00C**: The payment flow executes account balance reduction unconditionally after the TRANSACT WRITE call, without checking whether the write succeeded. This anti-pattern — where error-path and success-path diverge inside a called paragraph but the caller does not check a result flag before continuing — appears in COBIL00C and is a risk pattern to look for in any program that uses a similar flag-based error return convention (ERR-FLG-ON/OFF).

- **Input timestamp discarded on batch posting**: CBTRN02C discards DALYTRAN-PROC-TS from the input record and always overwrites TRAN-PROC-TS with the batch run time. Any upstream system that populates DALYTRAN-PROC-TS with the original transaction time loses that provenance on posting. The modernized system should propagate original timestamps explicitly.

- **Shared paragraph template defects propagated across programs**: COUSR01C, COUSR02C, and COUSR03C share multiple defects that originate from a common program template: unchecked CICS RECEIVE RESP codes (all three), dead CONTINUE statements (COUSR02C and COUSR03C), double BMS SEND on normal read (COUSR02C and COUSR03C), commented-out commarea user ID/type propagation (COUSR01C RETURN-TO-PREV-SCREEN lines 172-173), and unused modifier flags (COUSR03C). This pattern suggests the user administration programs were generated from a shared template without post-generation review. COUSR00C should be reviewed for the same class of defects before translation.

- **Compare-before-write optimistic update in COUSR02C**: COUSR02C reads the USRSEC record with UPDATE lock, compares each of the four editable fields to the stored values individually, and issues REWRITE only when at least one field has changed. This is a correct optimistic locking pattern and should be preserved as-is in the modernized service using an ETag or version token rather than a CICS file lock.

- **Full state machine with concurrent modification detection in COACTUPC**: COACTUPC implements a 7-state update workflow (ACUP-CHANGE-ACTION: not-fetched, show-details, changes-not-ok, changes-ok-not-confirmed, success, lock-error, write-failed) with 29-field old-vs-new comparison and concurrent modification detection. When another user modifies the record between the fetch and the PF5 confirmation, COACTUPC detects the discrepancy and forces a re-display before allowing a retry. This is the most sophisticated data integrity pattern in the application and maps directly to an optimistic concurrency update endpoint with ETag/version validation in a REST API.

- **Position-based CICS DELETE without RIDFLD in COUSR03C**: COUSR03C issues EXEC CICS DELETE without a RIDFLD clause, relying on the file position established by the prior READ UPDATE in the same task. This is a valid CICS idiom but has no direct equivalent in SQL or REST APIs. The modernized delete endpoint must explicitly pass the primary key to the delete operation.

- **SYNCPOINT as an explicit commit boundary**: COACTUPC is the only online program that issues an explicit EXEC CICS SYNCPOINT — on PF3 exit before XCTL. All other online programs commit implicitly on CICS RETURN. In the modernized system this maps to an explicit commit or close-of-transaction boundary at the end of a multi-step interaction, rather than a per-request autocommit.
