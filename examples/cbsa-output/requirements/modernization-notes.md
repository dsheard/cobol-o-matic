---
type: requirements
subtype: modernization-notes
status: draft
confidence: high
last_pass: 1
---

# Modernization Notes

Observations relevant to migrating or modernizing this COBOL application, derived from the reverse-engineering analysis.

---

## Complexity Assessment

| Metric                    | Value                                                                          |
| ------------------------- | ------------------------------------------------------------------------------ |
| Total programs            | 29 (28 CICS online, 1 batch)                                                   |
| Total copybooks           | 35 (19 actively used, 16 orphaned)                                             |
| Total LOC (approx)        | ~18,700 (sum of per-program LOC from program inventory)                        |
| Avg cyclomatic complexity | TBD (estimated High for CRECUST, XFRFUN, BANKDATA; Low for GETCOMPY, GETSCODE, ABNDPROC) |
| External integrations     | 6 (CUSTOMER VSAM, ABNDFILE VSAM, ACCOUNT DB2, PROCTRAN DB2, CONTROL DB2, CICS BMS 3270 terminal) |
| Database tables           | 3 (ACCOUNT, PROCTRAN, CONTROL)                                                 |
| CICS transactions         | 14 (OMEN, ODCS, ODAC, OCCS, OCAC, OUAC, OCRA, OTFN, OCCA, OCR1-OCR5)          |
| BMS mapsets               | 9 (BNK1MAI, BNK1CA, BNK1CC, BNK1CD, BNK1DA, BNK1DC, BNK1TF, BNK1UA, BNK1ACC) |

---

## Technical Debt

| Issue                                        | Programs Affected                                               | Severity | Description                                                                                                                                                                                                                                 |
| -------------------------------------------- | --------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ABND-TIME seconds always shows minutes (HH:MM:MM) | All 23 programs that populate ABNDINFO-REC (pervasive)         | Medium   | Every abend diagnostic record has an incorrect time: the STRING statement that builds ABND-TIME uses WS-TIME-NOW-GRP-MM twice, never referencing WS-TIME-NOW-GRP-SS. Affects post-incident analysis across the entire application.            |
| Customer counter not restored on failure      | CRECUST                                                         | High     | When CRECUST increments the customer number counter but then fails before writing the VSAM record, the counter is not decremented. Customer numbers are permanently consumed, creating gaps. The program header comment claims restoration but no SUBTRACT exists. |
| SYSIDERR retry fall-through (silent corruption) | CRECUST                                                        | High     | If all 100 SYSIDERR retries fail in GLCV010, the ELSE branch with the abort logic is skipped and the code falls through to ADD 1 on unread data. This can produce a corrupt customer number and corrupt control record writes.               |
| Control record update has no error check      | CRECUST                                                         | High     | The post-WRITE control record update (count increment) at WCV010 lines 1133-1146 has no RESP/RESP2 clause. A failed update silently proceeds to COMM-SUCCESS='Y', making the application believe the write succeeded.                         |
| ABEND without NODUMP inconsistency            | DELACC (HWPT), XFRFUN (WPCD), CREACC (HWPT)                    | Low      | PROCTRAN INSERT failure ABENDs in DELACC and CREACC use ABEND HWPT without NODUMP, generating unexpected CICS transaction dumps inconsistently with the rest of the application which uses NODUMP on explicit ABENDs.                        |
| Missing ABNDPROC call before some ABENDs      | DELACC (HRAC path), XFRFUN (TO forward-order unexpected fail-code, HROL forward-path) | Medium | Selected ABEND paths do not call ABNDPROC before issuing the ABEND, meaning no structured diagnostic record is written to ABNDFILE for those specific failure scenarios.                                                                    |
| UPDACC / UPDCUST dead abend infrastructure    | UPDACC, UPDCUST                                                 | Low      | Both programs declare ABNDINFO-REC and WS-ABEND-PGM in WORKING-STORAGE but never wire them to an ABEND path. Errors are handled solely by COMM-SUCCESS='N' with no abend logging.                                                           |
| Next statement date calculation inconsistency | CREACC (WAD010 vs. CD010)                                       | Low      | Two separate next-statement-date calculations exist in CREACC: CD010 uses partial month-awareness (February only); WAD010 uses unconditional +30. The value returned to the caller (COMM-NEXT-STMT-DT) comes from WAD010's simple +30, while CD010's value goes to DB2 local-storage only. |
| Statement date logic not fully month-aware    | CREACC (CD010), BANKDATA                                        | Low      | CD010 handles February with leap-year awareness but adds +30 for all other months regardless of month length. End-of-month account openings on 30-day months will land on invalid dates.                                                     |
| UPDACC header comment inaccurate              | UPDACC                                                          | Low      | Program header states statement dates can be amended but the active UPDATE SQL only modifies three fields (type, interest rate, overdraft limit). Commented-out alternative code block further contributes to confusion.                       |
| DELCUS header comment inaccurate              | DELCUS                                                          | Low      | Header states DELCUS writes a PROCTRAN delete record for each deleted account. In practice DELACC writes account-level records; DELCUS writes only one customer-level 'ODC' record.                                                          |
| Dead code / unused WORKING-STORAGE fields     | DBCRFUN, DELACC, INQACC, BANKDATA, ABNDPROC, CREACC, BNKMENU   | Low      | Multiple programs contain extensive dead WORKING-STORAGE fields: vestigial VSAM keys, multi-datastore type flags (DATASTORE-TYPE-DLI/DB2/VSAM), unused retry counters, dead IMS PCB pointer assignments, unreachable CALC-DAY-OF-WEEK section in BANKDATA. |
| IMS/DL-I artefacts in CICS-only programs      | CREACC, DELCUS, INQACCCU, INQACC (PCB pointer fields)           | Low      | COMM-PCB-POINTER and COMM-PCB1/PCB2 pointer fields appear in COMMAREA copybooks for several programs. SET ... TO NULL and PCB pointer threading logic exists in CICS-only programs, suggesting a prior IMS dispatch path that was removed.   |
| Dead code in CRECUST credit-agency EVALUATE   | CRECUST                                                         | Low      | Container EVALUATE in CC010 contains WHEN branches for containers CIPF, CIPG, CIPH, CIPI (agencies 6-9) that are unreachable since the loop only iterates to 5. These are dead WHEN clauses.                                                |
| DELACC-COMM-APPLID always spaces              | DELCUS                                                          | Low      | WS-APPLID is moved to DELACC-COMM-APPLID before each DELACC LINK, but WS-APPLID is never populated via EXEC CICS ASSIGN APPLID. DELACC receives spaces for APPLID.                                                                         |
| Deadlock/timeout diagnostic message mislabelled | XFRFUN (UADT010)                                             | Low      | At line 1485, when TO-account UPDATE fails with SQLCODE=-911 and retries exhausted, the program DISPLAYs 'TIMEOUT DETECTED!' while testing the deadlock SQLERRD value (13172872). The timeout code is 13172894 (checked correctly elsewhere). |
| BANKDATA reference data defects               | BANKDATA                                                        | Low      | SURNAME(24) assigned twice (Ramsbottom overwritten by Lloyd); SURNAME(27) misspelled as 'Higins'; INITIALS array has 'L' and 'K' transposed at positions 11-12. All generated test data affected.                                           |
| Statement dates hard-coded to 2021            | BANKDATA                                                        | Medium   | All batch-generated accounts have last statement = 01.07.2021 and next statement = 01.08.2021. Any modernized system consuming this data will find all accounts appear overdue.                                                              |

---

## Modernization Risks

| Risk                                                        | Impact | Likelihood | Mitigation                                                                                                                    |
| ----------------------------------------------------------- | ------ | ---------- | ----------------------------------------------------------------------------------------------------------------------------- |
| ABNDINFO copybook used by all 23 programs as cross-cutting concern | High   | High       | Any schema change to ABNDINFO requires coordinated recompilation of all 23 programs. In a modern system, extract this as a shared logging service contract with a versioned API. |
| PROCTRAN copybook with REDEFINES for each transaction type   | High   | Medium     | PROCTRAN uses REDEFINES to overlay a single description field with type-specific sub-layouts (transfer, debit, credit, create/delete customer/account). Modernizing requires either a union type or a normalised audit schema. |
| SORTCODE hardcoded as literal (987654) in copybook, shared by 18 programs | Medium | Medium | Sort code is a compile-time constant, not a runtime configuration. Changing it requires recompilation of 18 programs. Modernization should externalise this as a configuration property. |
| CICS ENQ/DEQ for sequence number serialisation              | High   | High       | Both CRECUST and CREACC use CICS ENQ on a sort-code-scoped resource name to serialise counter access. Modern equivalents require a distributed lock or database sequence; the SYSIDERR-retry-fall-through defect in CRECUST makes this especially fragile. |
| CICS pseudo-conversational 3270 BMS terminal interface      | High   | High       | All screen programs are written to the 3270 SEND/RECEIVE MAP model. Modernizing the UI layer requires extracting business logic from the BMS programs and providing REST/JSON or gRPC interfaces instead. |
| CICS Async API (RUN TRANSID / channels / containers)        | Medium | Medium     | CRECUST's credit-check fanout uses a CICS-specific async model. Modernizing requires replacing with a message queue (e.g., Kafka, MQ) or an async HTTP call pattern with a callback/aggregation step. |
| VSAM KSDS for CUSTOMER file                                 | High   | High       | CUSTOMER records are stored in VSAM KSDS with a 16-byte composite key. Migration to a relational DB (or another store) requires key mapping, handling of the control sentinel record (sortcode=000000, number=9999999999), and access pattern changes from CICS FILE commands to SQL. |
| PROCTRAN as write-only append log with no COBOL reader      | Medium | Medium     | PROCTRAN is written by 6 programs but has no reader in the COBOL source. It is likely consumed by an external reporting layer or z/OS Connect API. Migration must identify and preserve all consumers before removing the table. |
| GO TO statements in XFRFUN, INQACC, DELACC, CRECUST        | Medium | Medium     | Several programs use GO TO for error exits (GO TO UAD999, GO TO FD999, GO TO RAD999, GO TO DCV999). While these are structured exits (not spaghetti GOTO), they complicate direct translation to structured languages without GOTO semantics. |
| DATE format fragmentation                                   | Medium | High       | Dates are stored and formatted in at least four different ways across programs: DDMMYYYY (8-char), DD.MM.YYYY (10-char dot-separated), YYYY-MM-DD (DB2 internal), and YYYYMMDD (integer form for arithmetic). Any modernization must normalise date handling across all data stores. |
| CONTROL table as a mutable sequence generator               | Medium | Medium     | The CONTROL DB2 table is used as a counter (SELECT + UPDATE) for account number generation within a CICS ENQ scope. Replacing with a DB2 SEQUENCE or identity column removes the ENQ dependency and the associated retry/failure risks. |
| CICS HANDLE ABEND pattern                                   | Medium | Medium     | DBCRFUN, XFRFUN, and INQACC use EXEC CICS HANDLE ABEND LABEL(...) to register a local abend handler. This pattern has no direct equivalent in most modern languages; abend handlers must be replaced with structured exception handling. |
| BMS map copybooks (BNK1CAM, BNK1CCM, BNK1CDM, BNK1DAM, BNK1DCM, BNK1MAI, BNK1TFM, BNK1UAM) not in source | Medium | Low | These BMS symbolic map copybooks are referenced by COPY statements but absent from the analysed source. They are generated from BMS map macros at build time. A modernization must recover or reconstruct these layouts from the BMS source files. |
| Orphan copybooks suggest removed or unimplemented features  | Low    | Low        | NEWACCNO, NEWCUSNO, PROCISRT, CONTDB2, CONTROLI, INQACCCZ, INQACCZ, INQCUSTZ, DELACCZ suggest prior IMS dispatch paths and an account/customer number generation service that was reimplemented directly in CRECUST/CREACC. Risk of confusion during migration about which interface is canonical. |

---

## Decomposition Candidates

Programs or program groups that could be extracted as independent services or modules:

| Candidate                    | Programs                                       | Rationale                                                                                                                             | Dependencies                                                                               |
| ---------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Customer Service             | CRECUST, INQCUST, UPDCUST, DELCUS              | All operate on the CUSTOMER VSAM entity; shared CUSTOMER copybook; CRECUST orchestrates credit scoring; natural CRUD boundary         | CUSTOMER VSAM; PROCTRAN DB2; INQACCCU (via DELCUS); CRDTAGY1-5 (via CRECUST async)        |
| Account Service              | CREACC, INQACC, INQACCCU, UPDACC, DELACC      | All operate on the ACCOUNT DB2 entity; shared ACCDB2 and ACCOUNT copybooks; natural CRUD boundary                                     | ACCOUNT DB2; CONTROL DB2; PROCTRAN DB2; INQCUST (via CREACC, INQACCCU)                    |
| Transaction / Funds Service  | DBCRFUN, XFRFUN                               | Both operate on account balances and write PROCTRAN; share DB2 patterns including deadlock handling and storm drain logic              | ACCOUNT DB2; PROCTRAN DB2; ACCDB2, PROCTRAN copybooks                                     |
| Credit Scoring Service       | CRDTAGY1, CRDTAGY2, CRDTAGY3, CRDTAGY4, CRDTAGY5 | Five identical programs invoked asynchronously; all are stubs simulating an external credit-agency call; replace with a single parameterised external API call or message-driven worker | CIPCREDCHANN CICS channel (replace with MQ or HTTP); CRECUST as orchestrator           |
| Abend / Observability Service | ABNDPROC                                      | Pure write-through logger with no business logic; 23 programs depend on it; natural extraction as a structured logging microservice   | ABNDFILE VSAM (replace with structured log sink, e.g., ELK, Splunk, or cloud logging); ABNDINFO copybook as schema |
| Navigation / BFF Layer       | BNKMENU, all BNK1xxx screen programs           | All BMS screen programs contain only presentation logic and input validation; they are a Backend for Frontend (BFF) over the backend service layer | All backend programs; BMS mapsets; CICS 3270 terminal (can be replaced with web UI or REST BFF) |
| Utility / Configuration      | GETCOMPY, GETSCODE                            | Trivial static value services; candidates for replacement by a configuration service or environment variable injection                 | No data dependencies; only COMMAREA callers                                                |
| Data Initialisation          | BANKDATA                                      | Batch-only; no CICS coupling; self-contained destructive reload; can be replaced by a modern data fixture / migration script          | CUSTOMER VSAM; ACCOUNT DB2; CONTROL DB2; CEEGMT/CEEDATM LE calls (date utilities)         |

---

## Data Migration Considerations

| Data Store          | Type        | Volume Indicators                                                              | Migration Notes                                                                                                                                                                                                        |
| ------------------- | ----------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CUSTOMER (VSAM KSDS) | VSAM KSDS  | BANKDATA JCL generates 10,000 customers by default (PARM='1,10000,1,...')       | Key = SORTCODE(6) + CUSTOMER-NUMBER(10) = 16-byte composite; one special control sentinel record (sortcode=000000, number=9999999999, eyecatcher='CTRL') must be excluded from customer migration or treated separately; DOB stored as DDMMYYYY (8 bytes, no delimiters); credit review date stored similarly |
| ABNDFILE (VSAM KSDS) | VSAM KSDS  | Write-only; volume depends on operational error rate; 681-byte fixed records    | Records are keyed by UNIX microsecond timestamp + CICS task number; historical records may be useful for post-migration comparison; modernized equivalent is a structured log store (e.g., Elasticsearch, Splunk)      |
| ACCOUNT (DB2 table) | DB2         | Approximately 15,000-50,000 rows for 10,000 customers (1-5 accounts each); exact count held in CONTROL.ACCOUNT-COUNT | Dates stored as DD.MM.YYYY (10-char, dot-separated) in DB2 despite DB2's native DATE type; migration must parse and convert to ISO 8601 or native DB2 DATE; LOAN and MORTGAGE balances are negative; CONTROL.ACCOUNT-LAST holds the last assigned account number |
| PROCTRAN (DB2 table) | DB2         | Append-only; one row per significant financial event; volume proportional to transaction history | No COBOL reader identified; external consumers unknown; row description field uses REDEFINES-style overlay with different layouts per transaction type (transfer, debit/credit, create/delete); migration requires schema normalisation |
| CONTROL (DB2 table) | DB2         | Two rows per sort code: '<sortcode>-ACCOUNT-LAST' and '<sortcode>-ACCOUNT-COUNT' | Counter semantics; must be migrated to a DB2 SEQUENCE or identity column; concurrent access protected by CICS ENQ in current implementation; access pattern must change on migration |
| CICS CSD (DFHCSD)   | CICS CSD    | Defines 14 transactions, 29 programs, 9+ mapsets, 2 files, and associated definitions | BANK CSD group loaded via DFHCSDUP from CBSACSD.jcl; contents not directly available as text; all transaction/program mappings must be reverse-engineered from the JCL and source before migration |

---

## Patterns Observed

Notable coding patterns, idioms, or anti-patterns that affect modernization strategy:

- **Pseudo-conversational CICS pattern**: All screen programs use EXEC CICS RETURN TRANSID(self) with a 1-byte COMMAREA to loop back after each user action. This is the standard 3270 conversational design but has no equivalent in request/response web architectures. Each 'screen interaction' corresponds to a stateless HTTP request in a modern system.

- **Two-tier architecture (BMS screen + backend service)**: The application is cleanly layered: BNK1xxx programs handle presentation and basic field validation; backend programs (CREACC, CRECUST, DBCRFUN, XFRFUN, etc.) handle business logic and data access. The CICS LINK COMMAREA acts as a service contract. This layering supports incremental modernization by replacing the BMS tier with a REST/web API while keeping the backend programs initially.

- **COMMAREA-as-service-contract**: Each backend program has a dedicated copybook defining its COMMAREA layout (CREACC.cpy, CRECUST.cpy, PAYDBCR.cpy, XFRFUN.cpy, etc.). These are the closest equivalents to a service interface definition and should be treated as the schema for modernized API contracts.

- **SORTCODE copybook as a global constant**: The single-field SORTCODE copybook (VALUE 987654) is included by 18 programs. This is effectively a global configuration constant. In a modern system this belongs in a configuration service or environment property, not embedded in the compiled binary.

- **ABNDINFO as a centralised error schema**: The ABNDINFO copybook defines a structured error record used by all 23 programs. While the implementation has known defects (timestamp format bug), the intent - a single structured error schema with APPLID, TRANID, program, RESP, SQLCODE, and freeform text - maps directly to structured logging concepts (e.g., JSON log events).

- **CICS ENQ/DEQ as a distributed mutex**: CRECUST and CREACC use CICS ENQ on a resource name scoped to the sort code to provide mutual exclusion around counter access. This is a CICS-specific serialisation pattern with no direct equivalent in modern databases (use DB2 SEQUENCE or optimistic locking instead). The SYSIDERR-retry-fall-through defect in CRECUST exposes the fragility of this pattern.

- **Storm Drain / Circuit Breaker pattern**: DBCRFUN, XFRFUN, and INQACC implement a CHECK-FOR-STORM-DRAIN-DB2 paragraph that inspects SQLCODE for value 923 (DB2 connection lost). This is an early implementation of the circuit breaker pattern, providing diagnostic output when the DB2 subsystem becomes unavailable. The detection is informational only (no automatic backpressure); a modernised equivalent would integrate with a proper circuit breaker library.

- **Dead code from multi-datastore origin**: Multiple programs (DBCRFUN, DELACC, INQACC, ABNDPROC) carry WORKING-STORAGE fields with 88-level conditions for DATASTORE-TYPE-DLI, DATASTORE-TYPE-DB2, and DATASTORE-TYPE-VSAM. These are never used; they indicate the programs were originally designed or templated for both IMS/DL-I and DB2/VSAM dispatch, with only the DB2/VSAM paths activated.

- **IMS PCB pointer artefacts in CICS-only programs**: COMMAREA copybooks for INQACCCU, INQACC, INQCUST, and DELACC include POINTER fields named PCB1/PCB2 (IMS Program Communication Block pointers). In CICS-only programs these are set to NULL or passed through as uninitialized values. They are vestiges of an IMS/TM dispatch layer that was removed. Any modernized interface definition should omit these fields.

- **Date arithmetic using COBOL intrinsic functions**: CRECUST, CREACC, and BANKDATA use FUNCTION INTEGER-OF-DATE and FUNCTION DATE-OF-INTEGER for date offset calculations. These are portable COBOL functions; the arithmetic logic can be translated directly to most modern languages.

- **Asymmetric error handling coverage**: XFRFUN contains at least three cases where equivalent error paths receive different error handling (with vs. without ABNDPROC call, with vs. without NODUMP). This asymmetry is a maintenance risk and should be normalised in any equivalent modern implementation.
