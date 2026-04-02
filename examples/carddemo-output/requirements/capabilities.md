---
type: requirements
subtype: capabilities
status: draft
confidence: high
last_pass: 5
---

# Functional Capabilities

Derived functional capabilities describing what this COBOL application does, synthesized from business rules, data flows, and integration analysis.

## Capabilities

### User Authentication and Session Management

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | Authenticates users against a VSAM security file, routes them to role-appropriate menus (admin or regular user), and maintains pseudo-conversational session state via CICS COMMAREA throughout the application lifecycle. |
| Source Programs | COSGN00C |
| Input           | USRSEC (VSAM), terminal input (userid/password via BMS map COSGN0A) |
| Output          | CARDDEMO-COMMAREA (session context), CICS XCTL to COADM01C or COMEN01C |
| Business Rules  | User ID and password are mandatory; both normalized to uppercase before comparison. User type 'A' routes to admin menu; all other types route to regular menu. PF3 ends the session. Max 8-character user ID and password. Unexpected CICS errors display a generic message rather than aborting. No account lockout or failed-attempt counter exists. |
| Data Entities   | CSUSR01Y (SEC-USR-ID, SEC-USR-PWD, SEC-USR-TYPE), COCOM01Y (CARDDEMO-COMMAREA) |

---

### Navigation and Menu Routing

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | Provides role-separated navigation hubs that route authenticated users to the appropriate functional screens. COMEN01C is the main menu for regular users (10 options); COADM01C is the admin menu (6 options including DB2 extension items). Navigation is data-driven via CDEMO-MENU-OPT-PGMNAME lookups and CICS XCTL. |
| Source Programs | COMEN01C, COADM01C |
| Input           | CARDDEMO-COMMAREA (user role, navigation context), terminal input via BMS maps COMEN01 / COADM01 |
| Output          | CICS XCTL transfers to target programs; CARDDEMO-COMMAREA updated with from/to program context |
| Business Rules  | Regular users reach COMEN01C from COSGN00C; admin users reach COADM01C from COSGN00C. Menu option dispatch uses dynamic CDEMO-MENU-OPT-PGMNAME(WS-OPTION) lookup. COMEN01C optionally dispatches to COPAUS0C (pending authorization) if the extension module is installed (tested via CICS INQUIRE). PF3 from either menu returns to COSGN00C. |
| Data Entities   | COCOM01Y (CARDDEMO-COMMAREA), COMEN02Y (menu options), COADM02Y (admin menu options) |

---

### Account Inquiry and Update

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | Allows authenticated users to view or update account master data and linked customer records. The view function is read-only; the update function implements a 7-state machine with 29-field old-vs-new comparison, concurrent modification detection, and PF5-confirmed write-back to both ACCTDAT and CUSTDAT VSAM files. |
| Source Programs | COACTVWC, COACTUPC |
| Input           | ACCTDAT (VSAM), CUSTDAT (VSAM), CARDXREF/CXACAIX (VSAM alternate index), terminal input via BMS maps CACTVWA / CACTUPA |
| Output          | ACCTDAT (updated), CUSTDAT (updated), CICS BMS screen output |
| Business Rules  | Account lookup uses card cross-reference alternate index. Update requires PF5 confirmation before writing. All account and customer fields are subject to field-level validation before the write is permitted (29 fields including FICO score range 300-850, SSN format, US state code, state/zip cross-validation, North America area code lookup). COACTUPC uses a 7-state ACUP-CHANGE-ACTION state machine: not-fetched, show-details, changes-not-ok, changes-ok-not-confirmed, success, lock-error, write-failed. Concurrent modification is detected by comparing stored vs re-fetched values; a changed record forces re-display before retry. COACTUPC uses CICS READ UPDATE lock on ACCTDAT and CUSTDAT before REWRITE. A CICS SYNCPOINT is issued on PF3 exit (no SYNCPOINT spans the two VSAM writes — partial-update risk if CUSTDAT write fails after ACCTDAT succeeds). |
| Data Entities   | CVACT01Y (ACCOUNT-RECORD), CVCUS01Y (CUSTOMER-RECORD), CVACT03Y (XREF-RECORD), CVCRD01Y, CSLKPCDY (US state code and area code lookup tables) |

---

### Credit Card Management

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | Provides browse, detail view, and update of credit card records. The list screen supports admin users viewing all cards, or regular users viewing only cards linked to their account. Navigation is hub-and-spoke through COCRDLIC. |
| Source Programs | COCRDLIC, COCRDSLC, COCRDUPC |
| Input           | CARDDAT (VSAM), CXACAIX / CARDAIX (VSAM alternate index paths), terminal input via BMS maps CCRDLIA / CCRDSLA / CCRDUPA |
| Output          | CARDDAT (updated by COCRDUPC), CICS BMS screen output |
| Business Rules  | Admin users see all cards; regular users see only cards linked to the account in COMMAREA. Card list drives to detail view (COCRDSLC) or update (COCRDUPC) via dynamic CCARD-NEXT-PROG field in COMMAREA. Card updates are written back to CARDDAT. No before/after audit record is written on card update. |
| Data Entities   | CVACT02Y (CARD-RECORD), CVCRD01Y, CVACT03Y (XREF), COCOM01Y |

---

### Transaction Inquiry and Manual Entry

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | Allows operators to browse the transaction master, view individual transaction details, and manually add new transactions with full field validation and date checking. Transaction IDs are auto-generated by reading backwards through the TRANSACT file. |
| Source Programs | COTRN00C, COTRN01C, COTRN02C |
| Input           | TRANSACT (VSAM), CCXREF / CXACAIX (VSAM), CSUTLDTC (date validation subprogram), terminal input via BMS maps COTRN0A / COTRN1A / COTRN2A |
| Output          | TRANSACT (written by COTRN02C), CICS BMS screen output |
| Business Rules  | Transaction list browses TRANSACT with paging. Detail view reads a single record by key. Add transaction validates account/card cross-reference, date fields (via CSUTLDTC/CEEDAYS), transaction type and category codes, and amount. Transaction ID is generated as the highest existing ID plus one, derived from a backwards browse. Confirmation with 'Y' is required before the write. Concurrent online adds could generate duplicate IDs (no locking during ID generation). |
| Data Entities   | CVTRA05Y (TRAN-RECORD), CVACT01Y, CVACT03Y, COCOM01Y |

---

### Bill Payment Processing

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | Enables cardholders to pay their outstanding account balance in full through an online CICS screen. The payment writes a transaction record and zeros the account balance. |
| Source Programs | COBIL00C |
| Input           | ACCTDAT (VSAM, READ UPDATE), CXACAIX (VSAM, card lookup), TRANSACT (VSAM, backwards browse for ID generation), terminal input via BMS map COBIL0A |
| Output          | TRANSACT (new bill payment transaction, type '02', category 2), ACCTDAT (balance set to zero) |
| Business Rules  | Account ID is mandatory. No payment is allowed when balance is zero or negative. Operator must confirm with 'Y' before posting. Next transaction ID is generated by backwards browse. The full balance is always paid; partial payments are not supported. The CICS READ UPDATE lock is held between the read and the rewrite. Known defects: (1) program cannot process the first-ever payment when TRANSACT is empty (STARTBR NOTFND blocks); (2) account balance is unconditionally reduced after a TRANSACT write attempt, even if the write fails with DUPKEY, creating a zero-balance account with no payment record. |
| Data Entities   | CVACT01Y (ACCOUNT-RECORD), CVTRA05Y (TRAN-RECORD), CVACT03Y (XREF), COCOM01Y |

---

### Daily Transaction Posting (Batch)

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | Reads a sequential daily transaction feed, validates each transaction (card validity, account existence, credit limit, account expiration), posts valid transactions to the VSAM transaction master and category balance file, updates account balances, and writes rejected transactions to a reject GDG with reason codes. |
| Source Programs | CBTRN02C |
| Input           | DALYTRAN (sequential PS), XREFFILE (VSAM), ACCOUNT-FILE (VSAM I-O), TCATBAL-FILE (VSAM I-O) |
| Output          | TRANSACT-FILE (VSAM, truncated each run), TCATBALF (updated), ACCOUNT-FILE (updated), DALYREJS GDG (reject records with reason codes) |
| Business Rules  | Reject reason 100: card not in XREF. Reason 101: account not found. Reason 102: transaction would exceed credit limit (cycle balance check). Reason 103: transaction after account expiration date. RETURN-CODE=4 if any rejects. Overlimit check uses cycle-to-date balances only, excluding prior-cycle carry-forward. Both overlimit and expiration checks run without short-circuit; if both fail, only reason 103 is recorded. TRAN-RECORD does not contain account ID; account linkage requires re-join via CARDXREF using TRAN-CARD-NUM. Input DALYTRAN-PROC-TS is discarded; TRAN-PROC-TS is set from batch runtime clock. Known defect: account REWRITE failure (INVALID KEY) sets reason 109 but no reject is written and no abend occurs; the transaction is written to TRANSACT as if the account update succeeded. |
| Data Entities   | CVTRA06Y (DALYTRAN-RECORD), CVTRA05Y (TRAN-RECORD), CVACT01Y (ACCOUNT-RECORD), CVACT03Y (XREF-RECORD), CVTRA01Y (TRAN-CAT-BAL-RECORD) |

---

### Interest and Fees Calculation (Batch)

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | Calculates monthly interest charges per account by reading transaction category balances, looking up per-group annual interest rates from a disclosure group file, computing monthly interest (annual rate / 1200 formula), writing system-generated interest transactions, and updating account master balances. |
| Source Programs | CBACT04C |
| Input           | TCATBAL-FILE (VSAM sequential), XREF-FILE (VSAM random), ACCOUNT-FILE (VSAM I-O), DISCGRP-FILE (VSAM random), EXTERNAL-PARMS (JCL PARM: run date) |
| Output          | TRANSACT-FILE (GDG output: SYSTRAN), ACCOUNT-FILE (updated balances, cycle fields cleared) |
| Business Rules  | Monthly interest = (category balance * annual rate) / 1200. Groups without a specific disclosure group rate fall back to the 'DEFAULT' group using the same type and category codes. Missing accounts or XREF records cause an abend (not a soft skip). Cycle credit and debit balances are zeroed after interest posting. Fee computation is present as a stub (1400-COMPUTE-FEES paragraph) but contains no logic. Unconditional DISPLAY of every TCATBAL record is a debug artifact left in production code. |
| Data Entities   | CVTRA01Y / CVTRA02Y (TRAN-CAT-BAL-RECORD / DISCGRP), CVACT01Y (ACCOUNT-RECORD), CVACT03Y (XREF-RECORD), CVTRA05Y (TRAN-RECORD) |

---

### Account Statement Generation (Batch)

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | Generates account statements in both plain text (80-byte) and HTML (100-byte) formats for every card/account in the cross-reference file. Statements include account summary, customer name and address, and an itemized transaction list. |
| Source Programs | CBSTM03A, CBSTM03B |
| Input           | TRNXFILE (VSAM, card-keyed transaction file rebuilt by CREASTMT JCL SORT step), XREFFILE (VSAM), CUSTFILE (VSAM), ACCTFILE (VSAM) |
| Output          | STATEMNT.PS (plain text), STATEMNT.HTML (HTML), optionally converted to PDF by TXT2PDF1 JCL |
| Business Rules  | All VSAM I/O is delegated to CBSTM03B via a parameter block. The CREASTMT JCL must pre-sort TRANSACT by card number then transaction ID before CBSTM03A runs. CBSTM03A uses ALTER/GO TO dispatch and a two-dimensional in-memory transaction array. Transactions are grouped by card number. Both text and HTML formats are written in parallel. CBSTM03A accesses the MVS Task I/O Table (TIOT) via POINTER arithmetic to enumerate DD names at runtime — a z/OS-specific technique with no non-mainframe equivalent. |
| Data Entities   | COSTM01 (TRNX-RECORD), CUSTREC (CUSTOMER-RECORD), CVACT01Y (ACCOUNT-RECORD), CVACT03Y (XREF-RECORD) |

---

### Transaction Report Generation (Batch)

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | Produces a formatted transaction detail report covering a configurable date range. The TRANREPT JCL unloads and sorts the transaction VSAM, and CBTRN03C reads the sorted file with transaction type and category reference data to produce the formatted report GDG. |
| Source Programs | CBTRN03C |
| Input           | TRANSACT.DALY GDG (sorted/filtered by TRANREPT JCL), CARDXREF (VSAM), TRANTYPE (VSAM), TRANCATG (VSAM), DATEPARM (date parameter file) |
| Output          | TRANREPT GDG (formatted transaction report) |
| Business Rules  | Date range filtering is done by the SORT step, not CBTRN03C. CBTRN03C looks up type and category descriptions from VSAM reference tables. Report formatted with type/category descriptions from TRANTYPE and TRANCATG. TRANTYPE and TRANCATG are mastered in DB2 in the extension module and extracted to VSAM for batch use. |
| Data Entities   | CVTRA05Y (TRAN-RECORD), CVTRA03Y / CVTRA04Y / CVTRA07Y (report/type/category layouts), CVACT03Y (XREF) |

---

### User Administration

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | Allows admin users to list, add, update, and delete user records in the USRSEC security file. Full CRUD operations are available exclusively through the admin menu. |
| Source Programs | COUSR00C, COUSR01C, COUSR02C, COUSR03C, COADM01C |
| Input           | USRSEC (VSAM), terminal input via BMS maps COUSR0A / COUSR1A / COUSR2A / COUSR3A / COADM1A |
| Output          | USRSEC (written, updated, deleted), CICS BMS screen output |
| Business Rules  | User list is admin-only (accessible only from COADM01C, not COMEN01C). Add user validates all mandatory fields (first name, last name, user ID, password, user type) and rejects duplicates. User type domain: 'A' (admin) or 'U' (regular); however COUSR01C does not enforce the 'A'/'U' domain at data entry — any non-blank character is accepted as user type. User ID is up to 8 characters. Delete requires navigating to the delete screen and pressing PF5 to confirm. Passwords are stored in plaintext (PIC X(08)); no hashing or encryption is applied. COUSR01C: CICS RECEIVE RESP not evaluated; user ID and user type are NOT forwarded in COMMAREA on PF3 navigation (commented-out code). COUSR02C: PF3 exits unconditionally without checking whether the pending save succeeded or failed; an error condition on the screen is visible momentarily before XCTL occurs. COUSR03C: the DELETE call executes even when the preceding READ UPDATE fails; CICS issues NOTFND on the DELETE (no data corruption, but an unnecessary I/O call is made). |
| Data Entities   | CSUSR01Y (SEC-USR-ID, SEC-USR-PWD, SEC-USR-TYPE, SEC-USR-FNAME, SEC-USR-LNAME) |

---

### Report Request (Online to Batch Trigger)

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | Allows users to initiate a batch transaction report from the online CICS session by entering date range parameters. The program writes JCL records to the JOBS extra-partition TDQ backed by the JES internal reader, which causes JES to submit the batch report job. |
| Source Programs | CORPT00C |
| Input           | Terminal input via BMS map CORPT0A (start date, end date), CSUTLDTC (date validation), TRANSACT (VSAM, used only to check record existence) |
| Output          | JOBS TDQ (JCL records submitted to JES internal reader), CICS BMS screen confirmation |
| Business Rules  | Date range parameters are validated using CSUTLDTC (which calls the CEEDAYS LE API). JCL is written record-by-record to the JOBS TDQ in 80-byte fixed format. The batch job runs asynchronously; no feedback is returned to the online user. |
| Data Entities   | CVTRA05Y (TRANSACT browse), COCOM01Y |

---

### Data Migration Export and Import

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | Provides a full bulk export of all operational data (customers, accounts, cards, card-account cross-references, transactions) to a single multi-record VSAM export file, and a corresponding import that splits the export file back into normalized sequential target files. Used for branch migration and system-to-system data transfer. |
| Source Programs | CBEXPORT, CBIMPORT |
| Input (export)  | CUSTFILE, ACCTFILE, XREFFILE, TRANSACT, CARDFILE (all VSAM) |
| Output (export) | EXPORT.DATA (VSAM, multi-record 500-byte fixed with REDEFINES type prefix C/A/X/T/D) |
| Input (import)  | EXPORT.DATA (VSAM) |
| Output (import) | CUSTOUT, ACCTOUT, XREFOUT, TRNXOUT (sequential PS), ERROUT (errors), CARDOUT (defined in code, missing JCL DD) |
| Business Rules  | Export writes every record without filtering or transformation; sequence numbers are auto-assigned. Import validates checksums and splits by record type prefix. A missing CARDOUT DD in CBIMPORT.jcl is a known JCL omission — card import output may fail silently or abend at runtime. |
| Data Entities   | CVEXPORT (multi-record export layout with REDEFINES), CVCUS01Y, CVACT01Y, CVACT02Y, CVACT03Y, CVTRA05Y |

---

### Reference Data Utility Operations (Batch Diagnostics)

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | A set of diagnostic batch programs that read each major VSAM master file and print all records to SYSOUT. Used for data verification, reconciliation, and support. CBTRN01C is a more comprehensive validation program that reads DALYTRAN and verifies card, XREF, account, and customer lookups without posting. |
| Source Programs | CBACT01C, CBACT02C, CBACT03C, CBCUS01C, CBTRN01C |
| Input           | ACCTFILE (CBACT01C), CARDFILE (CBACT02C), XREFFILE (CBACT03C), CUSTFILE (CBCUS01C), DALYTRAN + XREFFILE + ACCTFILE + CARDFILE + CUSTFILE + TRANSACT (CBTRN01C) |
| Output          | SYSOUT (printed records); CBACT01C also produces PSCOMP, ARRYPS, and VBPS output files in three different formats |
| Business Rules  | CBACT01C additionally calls COBDATFT assembler routine for date conversion and writes output in three physical formats (compressed PS, array PS, variable-block PS). All programs use CEE3ABD for abnormal termination. CBTRN01C serves as a dry-run validation tool for the POSTTRAN pipeline but has no associated JCL in the current source set. |
| Data Entities   | CVACT01Y, CVACT02Y, CVACT03Y, CVCUS01Y, CVTRA05Y, CVTRA06Y |

---

### Batch Job Sequencing Utility

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | Provides a configurable batch wait/sleep step that introduces a controlled delay into a JCL job stream. Used to sequence batch job steps where timing dependencies exist between jobs. |
| Source Programs | COBSWAIT |
| Input           | SYSIN (8-byte centisecond wait duration parameter) |
| Output          | (none — side effect is time elapsed before the step completes) |
| Business Rules  | SYSIN value is read as PIC X(8) and converted to PIC 9(8) COMP before being passed to MVSWAIT. No explicit error handling for non-numeric or missing SYSIN values; the program has no file I/O or database access. Normal termination (STOP RUN) occurs after the wait completes. |
| Data Entities   | (none) |

---

### Transaction Type Administration (DB2 Extension)

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | Provides online list and update screens for the DB2 TRANSACTION_TYPE reference table, plus a batch maintenance program for bulk insert/update/delete. Part of the optional app-transaction-type-db2 extension module. Reference data is periodically extracted from DB2 and loaded into VSAM TRANTYPE/TRANCATG files for use by the batch transaction report. |
| Source Programs | COTRTLIC, COTRTUPC, COBTUPDT |
| Input           | CARDDEMO.TRANSACTION_TYPE (DB2), terminal input via BMS maps CTRTLIA / CTRTUPA; INPFILE (sequential, for COBTUPDT) |
| Output          | CARDDEMO.TRANSACTION_TYPE (DB2, via COTRTUPC and COBTUPDT), TRANTYPE.PS / TRANCATG.PS (via TRANEXTR DSNTIAUL extract) |
| Business Rules  | COTRTLIC supports forward and backward cursor paging on the DB2 table. COTRTUPC performs SELECT then UPDATE on the selected transaction type. COBTUPDT reads an input file with action codes A (add), D (delete), U (update) and issues corresponding SQL DML. Reference data sync to VSAM uses DSNTIAUL unload followed by IDCAMS REPRO. |
| Data Entities   | CARDDEMO.TRANSACTION_TYPE (TR_TYPE primary key), CVTRA03Y / CVTRA04Y (VSAM reference table layouts) |

---

### Pending Authorization Management (IMS/MQ Extension)

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | Manages real-time card authorization decisions using an IMS hierarchical database. Incoming authorization requests arrive via MQ, are processed and stored in IMS, and can be reviewed online. Expired pending authorizations are purged by a batch program. Part of the optional app-authorization-ims-db2-mq extension module. |
| Source Programs | COPAUS0C, COPAUS1C, COPAUS2C, COPAUA0C, CBPAUP0C |
| Input           | Dynamic MQ request queue (COPAUA0C), IMS DBPAUTP0 segments PAUTSUM0/PAUTDTL1 (COPAUS0C, COPAUS1C), ACCTDAT/CUSTDAT/CARDDAT (COPAUS0C, COPAUS1C for display) |
| Output          | IMS DBPAUTP0 (COPAUA0C writes; CBPAUP0C deletes expired), dynamic MQ reply queue (COPAUA0C), CICS BMS screens |
| Business Rules  | COPAUA0C receives authorization events on a dynamic MQ queue, processes against IMS and VSAM data, and replies on MQMD-REPLYTOQ. COPAUS1C can mark a pending auth as fraud via CICS LINK to COPAUS2C. CBPAUP0C purges records older than WS-EXPIRY-DAYS. Authorization decision rules, expiry thresholds, and fraud criteria are not fully recoverable from the analysed source. |
| Data Entities   | IMS PAUTSUM0 (root segment, keyed by account ID), PAUTDTL1 (child segment, authorization details) |

---

### MQ Account and Date Inquiry Services (VSAM-MQ Extension)

| Property        | Value                               |
| --------------- | ----------------------------------- |
| Description     | Provides two MQ-triggered CICS services: an account data inquiry that reads ACCTDAT and returns account details, and a system date/time service. Both are part of the optional app-vsam-mq extension module and respond to requests on a shared MQ input queue. |
| Source Programs | COACCT01, CODATE01 |
| Input           | CARDDEMO.REQUEST.QUEUE (MQ GET), ACCTDAT (CICS READ for COACCT01) |
| Output          | CARD.DEMO.REPLY.ACCT (MQ PUT, account data), CARD.DEMO.REPLY.DATE (MQ PUT, date/time), CARD.DEMO.ERROR (MQ PUT, errors) |
| Business Rules  | COACCT01 receives a 1000-byte request message containing function code 'INQA' and an 11-digit account ID; returns account status, balance, credit limit, and dates. CODATE01 returns the current system date and time formatted as 'MM-DD-YYYY HH:MM:SS'. Errors for both programs are routed to CARD.DEMO.ERROR queue. |
| Data Entities   | CVACT01Y (ACCOUNT-RECORD via CICS READ on ACCTDAT) |

---

## Capability Map

| #   | Capability | Programs   | Complexity        | Description        |
| --- | ---------- | ---------- | ----------------- | ------------------ |
| 1   | User Authentication and Session Management | COSGN00C | Low | CICS signon, credential check, role-based routing |
| 2   | Navigation and Menu Routing | COMEN01C, COADM01C | Low | Role-separated menu hubs with dynamic XCTL dispatch |
| 3   | Account Inquiry and Update | COACTVWC, COACTUPC | High | Online account and customer view and edit; 7-state machine with 29-field compare-before-write, concurrent modification detection, PF5 confirmation |
| 4   | Credit Card Management | COCRDLIC, COCRDSLC, COCRDUPC | Medium | Browse, view, and update credit card records |
| 5   | Transaction Inquiry and Manual Entry | COTRN00C, COTRN01C, COTRN02C | Medium | Browse, view, and add transactions online with date validation |
| 6   | Bill Payment Processing | COBIL00C | Medium | Online full-balance payment with CICS locking and transaction write; two known data integrity defects |
| 7   | Daily Transaction Posting | CBTRN02C | High | Batch validation and posting of daily transaction feed to VSAM master |
| 8   | Interest and Fees Calculation | CBACT04C | High | Batch monthly interest computation with disclosure group rate lookup |
| 9   | Account Statement Generation | CBSTM03A, CBSTM03B | High | Batch statement production in plain text and HTML using ALTER/GO TO dispatch |
| 10  | Transaction Report Generation | CBTRN03C | Medium | Batch formatted transaction detail report with reference data lookup |
| 11  | User Administration | COUSR00C, COUSR01C, COUSR02C, COUSR03C, COADM01C | Medium | Admin CRUD for user security records; shared template defects across COUSR01C-03C including unchecked RECEIVE RESP, PF-key handling anomalies |
| 12  | Report Request (Online to Batch) | CORPT00C | Low | CICS-to-batch JCL submission via JES internal reader TDQ |
| 13  | Data Migration Export and Import | CBEXPORT, CBIMPORT | Medium | Bulk multi-record export and split-import for branch migration |
| 14  | Reference Data Utility Operations | CBACT01C, CBACT02C, CBACT03C, CBCUS01C, CBTRN01C | Low | Diagnostic batch reads and prints of VSAM master files; dry-run transaction validation |
| 15  | Batch Job Sequencing Utility | COBSWAIT | Low | Configurable batch wait step (centisecond delay via SYSIN) used for JCL job step timing |
| 16  | Transaction Type Administration (ext) | COTRTLIC, COTRTUPC, COBTUPDT | Medium | DB2-backed online and batch maintenance of transaction type reference data |
| 17  | Pending Authorization Management (ext) | COPAUS0C, COPAUS1C, COPAUS2C, COPAUA0C, CBPAUP0C | High | IMS/MQ-based card authorization processing, review, and purge |
| 18  | MQ Account and Date Inquiry (ext) | COACCT01, CODATE01 | Low | MQ-triggered CICS services for account lookup and system date inquiry |

## Gaps and Assumptions

Capabilities where the reverse-engineered understanding is incomplete or assumptions were made:

| Capability | Gap / Assumption  | Confidence   | Rationale |
| ---------- | ----------------- | ------------ | --------- |
| Interest and Fees Calculation | Fee computation (1400-COMPUTE-FEES) is a stub; actual fee rules are unknown | low | Paragraph body is EXIT only; no evidence of intended fee logic in the source |
| Daily Transaction Posting | Overlimit check uses cycle-to-date balances, not total balance; whether this is intentional business policy is unclear | medium | The code is unambiguous but the business intent (cycle-reset billing vs. revolving credit) is not documented |
| Account Statement Generation | HTML formatting logic is reverse-engineered from code; no business specification for statement layout was found | medium | CBSTM03A generates valid HTML but the required visual format is inferred from the program |
| Data Migration Export/Import | CARDOUT DD is missing from CBIMPORT.jcl; card export correctness is uncertain | medium | CBIMPORT.cbl declares SELECT CARD-OUTPUT ASSIGN TO CARDOUT; the matching JCL DD is absent |
| Pending Authorization Management | Authorization decision rules, expiry thresholds, and fraud criteria are not in the analysed source set | low | Source is in a separate module directory; decision logic in COPAUA0C and COPAUS2C is only partially recoverable |
| Transaction Type DB2 Module | COTRTLIC/COTRTUPC/COBTUPDT operate against a DB2 table; schema and referential integrity rules are partially inferred from SQL in the programs | medium | DDL and full table constraints are in the extension module, not the core source |
| Bill Payment Processing | First-ever payment on an empty TRANSACT file will always fail (STARTBR NOTFND); this is a code defect whose operational impact depends on whether TRANSACT is ever truly empty | medium | Confirmed from COBIL00C business rules analysis; operational risk depends on deployment procedure |
| Reference Data Utility Operations | CBTRN01C has no JCL in the current source set; it is unclear whether it is used in production or is a development/test artifact | low | No JCL job found referencing CBTRN01C as an entry point program |
| User Administration | COUSR02C PF3 key exits unconditionally even when save validation fails; the extent to which operators rely on PF3-to-save behavior in practice is unknown | medium | Confirmed from COUSR02C source; behavioral impact depends on operator workflow |
| User Administration | COUSR01C does not enforce the 'A'/'U' domain for user type at data entry; any non-blank character is accepted. Whether this has allowed non-standard user type values to enter USRSEC is unknown | medium | Confirmed from COUSR01C PROCESS-ENTER-KEY lines 142-147; no domain check beyond non-blank |
| User Administration | COUSR01C has commented-out code that would forward user ID and user type in the COMMAREA on PF3 navigation; whether the omission was intentional design or a template oversight is unknown | low | Confirmed from COUSR01C RETURN-TO-PREV-SCREEN lines 172-173; no functional impact on the called program (COADM01C reads these fields from its own COMMAREA state) |
| Account Inquiry and Update | COACTUPC partial-update risk (ACCTDAT succeeds, CUSTDAT fails) has no evident production mitigant; whether this has occurred in practice is unknown | medium | Confirmed from 9600-WRITE-PROCESSING source; no SYNCPOINT between the two REWRITE calls |
