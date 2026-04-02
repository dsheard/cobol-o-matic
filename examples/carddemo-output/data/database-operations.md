---
type: data
subtype: database-operations
status: draft
confidence: high
last_pass: 5
---

# Database Operations

All database access patterns extracted from EXEC SQL, EXEC DLI, and CICS file I/O statements.

## DB2 Operations

No EXEC SQL blocks were found in any program in the current source set. The CardDemo application does not use DB2 in the analysed source files.

Two DB2-related programs are referenced in the admin menu (COADM02Y.cpy) but are not present in the source directory:
- `COTRTLIC` (Transaction Type List/Update)
- `COTRTUPC` (Transaction Type Maintenance)

These were added as stubs in a "Db2 release" branch of COADM02Y but their source is not available. Admin option count was raised from 4 to 6 to accommodate them.

Additionally, menu option 11 of the main menu (COMEN02Y.cpy) references `COPAUS0C` (Pending Authorization View), which is also absent from the source set. This appears to be a planned but unimplemented feature.

| Program | Table | Operation | Key Columns | Host Variables | Cursor |
| ------- | ----- | --------- | ----------- | -------------- | ------ |
| (none in source set) | N/A | N/A | N/A | N/A | N/A |

---

## IMS/DB Operations

No EXEC DLI or CALL 'CBLTDLI' statements were found. The CardDemo application does not use IMS/DB.

| Program | Segment | Operation | PCB Reference | SSA Qualifications |
| ------- | ------- | --------- | ------------- | ------------------- |
| (none) | N/A | N/A | N/A | N/A |

---

## Indexed File Operations

All data access is performed via VSAM KSDS files accessed through CICS VSAM commands (online programs) or standard COBOL READ/WRITE/REWRITE/DELETE verbs (batch programs).

### Batch Program File Operations

| Program | File Name | Operation | Key Fields | Access Pattern |
| ------- | --------- | --------- | ---------- | -------------- |
| CBACT01C | ACCTFILE-FILE (ACCTDAT) | READ | ACCT-ID 9(11) | Sequential scan - reads all accounts |
| CBACT01C | OUT-FILE (OUTFILE) | WRITE | N/A | Sequential output |
| CBACT01C | ARRY-FILE (ARRYFILE) | WRITE | N/A | Sequential output - array format |
| CBACT01C | VBRC-FILE (VBRCFILE) | WRITE | N/A | Variable-length sequential output |
| CBACT02C | CARDFILE-FILE (CARDDAT) | READ | CARD-NUM X(16) | Sequential scan - reads all cards |
| CBACT03C | XREFFILE-FILE (CXREF) | READ | XREF-CARD-NUM X(16) | Sequential scan - reads all xref records |
| CBACT04C | TCATBAL-FILE | READ/WRITE/REWRITE | TRANCAT-ACCT-ID + TRANCAT-TYPE-CD + TRANCAT-CD | Random by composite key |
| CBACT04C | XREF-FILE (CXREF) | READ | XREF-CARD-NUM X(16) | Random by card number |
| CBACT04C | DISCGRP-FILE | READ | DIS-ACCT-GROUP-ID + DIS-TRAN-TYPE-CD + DIS-TRAN-CAT-CD | Random by composite key |
| CBACT04C | ACCOUNT-FILE (ACCTDAT) | READ/REWRITE | ACCT-ID 9(11) | Random by account ID; REWRITE to update |
| CBACT04C | TRANSACT-FILE (TRANSACT) | WRITE | TRAN-ID X(16) | Sequential output - writes new transactions |
| CBCUS01C | CUSTFILE-FILE (CUSTDAT) | READ | CUST-ID 9(09) | Sequential scan - reads all customers |
| CBSTM03A | STMT-FILE (STMTFILE) | WRITE | N/A | Sequential - plain-text statement output |
| CBSTM03A | HTML-FILE (HTMLFILE) | WRITE | N/A | Sequential - HTML statement output |
| CBSTM03B | TRNX-FILE (TRNXFILE) | READ (via LK-M03B-OPER) | FD-TRNXS-ID (CARD-NUM+TRAN-ID composite) | Sequential scan and keyed read; dispatched via operation code by CBSTM03A |
| CBSTM03B | XREF-FILE (CXREF / XREFFILE) | READ (via LK-M03B-OPER) | FD-XREF-CARD-NUM X(16) | Sequential or keyed read; dispatched by CBSTM03A |
| CBSTM03B | CUST-FILE (CUSTDAT / CUSTFILE) | READ (via LK-M03B-OPER) | FD-CUST-ID X(09) | Random by customer ID; dispatched by CBSTM03A |
| CBSTM03B | ACCT-FILE (ACCTDAT / ACCTFILE) | READ (via LK-M03B-OPER) | FD-ACCT-ID 9(11) | Random by account ID; dispatched by CBSTM03A |
| CBTRN01C | DALYTRAN-FILE | READ | N/A | Sequential - reads daily transaction feed |
| CBTRN01C | CUSTOMER-FILE (CUSTDAT) | READ | FD-CUST-ID 9(09) | Random by customer ID |
| CBTRN01C | XREF-FILE (CXREF) | READ | FD-XREF-CARD-NUM X(16) | Random by card number |
| CBTRN01C | CARD-FILE (CARDDAT) | READ | FD-CARD-NUM X(16) | Random by card number |
| CBTRN01C | ACCOUNT-FILE (ACCTDAT) | READ | FD-ACCT-ID 9(11) | Random by account ID |
| CBTRN01C | TRANSACT-FILE (TRANSACT) | READ | TRAN-ID X(16) | Keyed (OPEN INPUT — reads pre-existing transaction master) |
| CBTRN02C | DALYTRAN-FILE | READ | N/A | Sequential - reads daily transaction feed |
| CBTRN02C | TRANSACT-FILE (TRANSACT) | WRITE | TRAN-ID X(16) | Sequential output - validated transactions |
| CBTRN02C | XREF-FILE (CXREF) | READ | FD-XREF-CARD-NUM X(16) | Random by card number |
| CBTRN02C | DALYREJS-FILE (DALYREJS) | WRITE | N/A | Sequential - rejected transactions with 80-byte validation trailer |
| CBTRN02C | ACCOUNT-FILE (ACCTDAT) | READ | FD-ACCT-ID 9(11) | Random by account ID |
| CBTRN02C | TCATBAL-FILE | READ/WRITE/REWRITE | Composite key | Random - maintain category balances |
| CBTRN03C | TRANSACT-FILE (TRANSACT) | READ | TRAN-ID X(16) | Sequential scan for report |
| CBTRN03C | XREF-FILE (CXREF) | READ | FD-XREF-CARD-NUM X(16) | Random by card number |
| CBTRN03C | TRANTYPE-FILE | READ | FD-TRAN-TYPE X(02) | Random by type code |
| CBTRN03C | TRANCATG-FILE | READ | FD-TRAN-TYPE-CD + FD-TRAN-CAT-CD | Random by composite key |
| CBTRN03C | REPORT-FILE (REPORT) | WRITE | N/A | Sequential output |
| CBTRN03C | DATE-PARMS-FILE (DATEPARM) | READ | N/A | Sequential - reads date range parameters |
| CBEXPORT | (ACCTDAT, CUSTDAT, CARDDAT, CXREF, TRANSACT) | READ | Various primary keys | Sequential scan - exports all entities |
| CBEXPORT | EXPORTFILE | WRITE | N/A | Sequential - multi-record export output |
| CBIMPORT | EXPORTFILE | READ | N/A | Sequential - reads export file for import |
| CBIMPORT | (ACCTDAT, CUSTDAT, CARDDAT, CXREF, TRANSACT) | WRITE | Various primary keys | Random - inserts imported entities |

---

### Online (CICS) File Operations

| Program | File Name | Operation | Key Fields | Access Pattern |
| ------- | --------- | --------- | ---------- | -------------- |
| COSGN00C | USRSEC (WS-USRSEC-FILE) | READ | SEC-USR-ID X(08) | Random - user authentication |
| COMEN01C | (none - navigation only) | N/A | N/A | N/A |
| COADM01C | (none - navigation only) | N/A | N/A | N/A |
| COACTVWC | ACCTDAT (LIT-ACCTFILENAME) | READ | ACCT-ID X(11) | Random by account ID |
| COACTVWC | CUSTDAT (LIT-CUSTFILENAME) | READ | CUST-ID X(09) | Random by customer ID |
| COACTVWC | CXACAIX (LIT-CARDXREFNAME-ACCT-PATH) | READ | XREF-ACCT-ID | Random via alternate index by account |
| COACTUPC | ACCTDAT (LIT-ACCTFILENAME) | READ, READ UPDATE, REWRITE | ACCT-ID X(11) | Random; UPDATE for exclusive lock before rewrite |
| COACTUPC | CUSTDAT (LIT-CUSTFILENAME) | READ, READ UPDATE, REWRITE | CUST-ID X(09) | Random; UPDATE for exclusive lock before rewrite |
| COACTUPC | CXACAIX (LIT-CARDXREFNAME-ACCT-PATH) | READ | XREF-ACCT-ID | Random via alternate index |
| COCRDLIC | CARDDAT (LIT-CARD-FILE) | STARTBR, READNEXT, READPREV | CARD-NUM X(16) | Sequential browse forward and backward |
| COCRDSLC | CARDDAT (LIT-CARDFILENAME) | READ | CARD-NUM X(16) | Random by card number |
| COCRDSLC | CARDAIX (LIT-CARDFILENAME-ACCT-PATH) | READ | CARD-ACCT-ID | Random via alternate index by account |
| COCRDUPC | CARDDAT (LIT-CARDFILENAME) | READ, READ UPDATE, REWRITE | CARD-NUM X(16) | Random; UPDATE lock; REWRITE to update card |
| COTRN00C | TRANSACT (WS-TRANSACT-FILE) | STARTBR, READNEXT, READPREV | TRAN-ID X(16) | Sequential browse forward and backward |
| COTRN01C | TRANSACT (WS-TRANSACT-FILE) | READ | TRAN-ID X(16) | Random by transaction ID |
| COTRN02C | CXACAIX (WS-CXACAIX-FILE) | READ | XREF-ACCT-ID | Random via alternate index by account |
| COTRN02C | CXREF (WS-CCXREF-FILE) | READ | XREF-CARD-NUM X(16) | Random by card number |
| COTRN02C | TRANSACT (WS-TRANSACT-FILE) | STARTBR, READPREV, WRITE | TRAN-ID X(16) | Browse to find position; WRITE new transaction |
| COBIL00C | TRANSACT (WS-TRANSACT-FILE) | STARTBR, READPREV, WRITE | TRAN-ID X(16) | Browse to find position; WRITE bill payment transaction |
| CORPT00C | TRANSACT (WS-TRANSACT-FILE) | (reference only) | TRAN-ID X(16) | Reads CVTRA05Y but accesses via batch job submission, not direct CICS file I/O |
| COUSR00C | USRSEC (WS-USRSEC-FILE) | STARTBR, READNEXT, READPREV | SEC-USR-ID X(08) | Sequential browse forward and backward |
| COUSR01C | USRSEC (WS-USRSEC-FILE) | WRITE | SEC-USR-ID X(08) | Random - create new user |
| COUSR02C | USRSEC (WS-USRSEC-FILE) | READ, REWRITE | SEC-USR-ID X(08) | Random - read then update user |
| COUSR03C | USRSEC (WS-USRSEC-FILE) | READ, DELETE | SEC-USR-ID X(08) | Random - read then delete user |

---

## CICS Transient Data Queue (TDQ) Operations

Extra-partition TDQ used to submit batch jobs from online programs.

| Program | Queue Name | Operation | Record Length | Purpose |
| ------- | ---------- | --------- | ------------- | ------- |
| CORPT00C | JOBS | WRITEQ TD | 80 bytes | Write JCL records to extra-partition TDQ for batch report job submission |

**Notes on CORPT00C TDQ Flow:**
CORPT00C builds a complete JCL job stream (stored as inline FILLER data in JOB-DATA) and writes it record-by-record to the 'JOBS' TDQ. The JCL invokes the TRANREPT batch procedure, passing the user-selected date range as SYSIN parameters. This triggers CBTRN03C to run as a batch job and produce the report.

---

## Cursors and Batch Access

Sequential browse patterns used in CICS programs (equivalent to cursor-based access in SQL systems).

| Program | Browse Pattern | File | Purpose | Fetch Pattern |
| ------- | -------------- | ---- | ------- | ------------- |
| COTRN00C | STARTBR + READNEXT / READPREV | TRANSACT | Display transaction list with pagination | READNEXT for forward paging; READPREV for backward paging |
| COTRN02C | STARTBR + READPREV | TRANSACT | Position to last record before writing new transaction | Find last TRAN-ID before INSERT |
| COBIL00C | STARTBR + READPREV | TRANSACT | Position to last record before writing bill payment | Find last TRAN-ID before INSERT |
| COCRDLIC | STARTBR + READNEXT / READPREV | CARDDAT | Display card list with pagination | READNEXT forward; READPREV backward |
| COUSR00C | STARTBR + READNEXT / READPREV | USRSEC | Display user list with pagination | READNEXT forward; READPREV backward |
| CBSTM03A | Sequential READ (via CBSTM03B M03B-READ) | TRNXFILE | Read all transactions for each card | Sequential scan; card group break on TRNX-CARD-NUM |

---

## Data Access Patterns Summary

### Access Pattern Notes

1. **No DB2 or IMS** - CardDemo uses VSAM files exclusively for persistent storage. No relational database is present in the analysed source. Two DB2 admin menu stubs (COTRTLIC, COTRTUPC) exist in COADM02Y.cpy but their programs are absent from the source set.

2. **Alternate Indexes** - Two alternate indexes are used for cross-entity lookups:
   - `CARDAIX` (also referenced as `CARDAIX `) - allows lookup of CARD-RECORD by CARD-ACCT-ID
   - `CXACAIX` - allows lookup of CARD-XREF-RECORD by XREF-ACCT-ID

3. **Optimistic locking pattern** - COACTUPC and COCRDUPC implement an optimistic locking pattern: READ (no UPDATE) to display data, save snapshot; user makes changes; READ UPDATE to get exclusive lock; compare saved snapshot to freshly-read record; if changed, reject; otherwise REWRITE.

4. **Sequential batch to VSAM** - Batch programs (CBTRN01C, CBTRN02C) read DALYTRAN sequential file and write validated records to the TRANSACT VSAM KSDS. CBACT04C reads TRANSACT and TCATBAL to compute interest.

5. **DALYREJS** - CBTRN02C produces a rejection file (DALYREJS) containing records that failed validation, with an 80-byte validation trailer appended to each rejected transaction (total 430 bytes per reject record).

6. **TDQ-driven batch** - CORPT00C does not directly access files at runtime. Instead it builds a JCL job stream in memory and writes it to extra-partition TDQ 'JOBS', which submits a batch job running CBTRN03C to produce the report. Date parameters flow from the CICS screen through the JCL SYSIN into the DATE-PARMS-FILE read by CBTRN03C.

7. **Export/Import pipeline** - CBEXPORT reads all five entity files (accounts, customers, cards, xref, transactions) sequentially and writes a single multi-type sequential file (EXPORTFILE) using REDEFINES-based record typing. CBIMPORT performs the reverse, splitting EXPORTFILE back into the individual VSAM files.

8. **COBSWAIT** - Utility program with no file I/O. Reads a centisecond wait duration from SYSIN and calls the MVS WAIT service (`MVSWAIT`). Used in JCL step WAITSTEP to introduce a configurable delay between batch job steps.

9. **CBSTM03A/CBSTM03B statement pipeline** - CBSTM03A generates per-account statements (plain text to STMTFILE, HTML to HTMLFILE) by reading TRNXFILE (transaction VSAM with composite card+tran key), XREFFILE (card xref), CUSTFILE (customer), and ACCTFILE (account) via the CBSTM03B file I/O subroutine. CBSTM03A passes a WS-M03B-AREA parameter block to CBSTM03B specifying the DD name, operation code, key, and data area. CBSTM03A also uses a non-standard MVS TIOT scan technique (via LINKAGE SECTION pointer arithmetic through PSA and TCB control blocks) to discover which DD names are allocated at runtime. The in-memory transaction table holds up to 51 cards with 10 transactions each.

10. **Missing program COPAUS0C** - Main menu option 11 (Pending Authorization View) in COMEN02Y.cpy references program COPAUS0C, which is absent from the source set. No file I/O patterns can be documented for this program. It represents a planned but unimplemented feature.
