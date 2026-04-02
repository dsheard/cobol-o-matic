---
type: test-specifications
subtype: data-contracts
status: draft
confidence: high
last_pass: 7
---

# Data Contract Tests

Data format, invariant, and boundary tests for each data store. These tests verify that the modernized system preserves data semantics regardless of storage technology changes (e.g. VSAM to database, flat file to API).

---

## File Contracts

| File / Dataset | Business Purpose | Record Layout | Producers | Consumers | Key Fields |
| -------------- | ---------------- | ------------- | --------- | --------- | ---------- |
| ACCTDAT | Account master: balances, limits, status, dates, group ID | CVACT01Y (300 bytes) | COACTUPC, COBIL00C, CBTRN02C, CBACT04C | COACTVWC, COACTUPC, COBIL00C, COTRN02C, CBTRN01C, CBTRN02C, CBACT04C, CBEXPORT, CBSTM03B, COACCT01 | ACCT-ID (PIC 9(11)) |
| CUSTDAT | Customer master: name, address, SSN, DOB, FICO score | CVCUS01Y (500 bytes) | COACTUPC | COACTVWC, COACTUPC, CBTRN01C, CBEXPORT, CBSTM03B | CUST-ID (PIC 9(09)) |
| CARDDAT | Card master: card number, CVV, embossed name, expiry, status | CVACT02Y (150 bytes) | COCRDUPC | COCRDSLC, COCRDUPC, CBTRN01C, CBEXPORT | CARD-NUM (PIC X(16)) |
| CARDXREF | Card-to-account cross-reference | CVACT03Y (50 bytes) | (pre-loaded via JCL) | COACTVWC, COACTUPC, COCRDLIC, COBIL00C, COTRN02C, CBTRN01C, CBTRN02C, CBACT04C, CBTRN03C, CBEXPORT, CBSTM03B | XREF-CARD-NUM (PIC X(16)) |
| TRANSACT | Transaction master: all posted transactions | CVTRA05Y (350 bytes) | COTRN02C, COBIL00C, CBTRN02C | COTRN00C, COTRN01C, CORPT00C, CBTRN01C, CBEXPORT, CREASTMT SORT | TRAN-ID (PIC X(16)) |
| TCATBALF | Transaction category balances: per-account/type/category running balances | CVTRA01Y (50 bytes) | CBTRN02C | CBACT04C | TRANCAT-ACCT-ID (9(11)) + TRANCAT-TYPE-CD (X(02)) + TRANCAT-CD (9(04)) |
| USRSEC | User security records: credentials and type | CSUSR01Y (80 bytes) | COUSR01C, COUSR02C | COSGN00C, COUSR00C, COUSR03C | SEC-USR-ID (PIC X(08)) |
| DISCGRP | Disclosure group interest rates: per-group/type/category annual rate | CVTRA02Y (50 bytes) | (pre-loaded via JCL) | CBACT04C | DIS-ACCT-GROUP-ID (X(10)) + DIS-TRAN-TYPE-CD (X(02)) + DIS-TRAN-CAT-CD (9(04)) |
| DALYTRAN | Daily transaction input feed | CVTRA06Y (350 bytes) | External feed | CBTRN01C, CBTRN02C | DALYTRAN-CARD-NUM (X(16)) |
| DALYREJS GDG | Daily transaction rejects with reason codes | 430-byte record (350-byte original + 80-byte trailer) | CBTRN02C | Downstream error processing | Sequential (no key) |
| TRANTYPE | Transaction type descriptions | CVTRA03Y (60 bytes) | TRANEXTR (DB2 extract) | CBTRN03C | TRAN-TYPE (PIC X(02)) |
| TRANCATG | Transaction category descriptions | CVTRA04Y (60 bytes) | TRANEXTR (DB2 extract) | CBTRN03C | TRAN-TYPE-CD (X(02)) + TRAN-CAT-CD (9(04)) |
| EXPORT.DATA | Multi-record bulk export for migration | CVEXPORT (500-byte fixed with REDEFINES type prefix) | CBEXPORT | CBIMPORT | Sequence number (auto-assigned) |

---

### ACCTDAT Contract Tests

| #  | Invariant | Test | Derived From |
| -- | --------- | ---- | ------------ |
| 1  | ACCT-ID is unique across all account records | Query all account records; verify no two records share the same ACCT-ID | CVACT01Y copybook; VSAM KSDS primary key constraint |
| 2  | ACCT-ID is a positive integer in range 1 to 99999999999 | Sample accounts; verify ACCT-ID PIC 9(11) contains only digits; verify no all-zero ID | CVACT01Y; BR-COACTUPC-41 |
| 3  | ACCT-ACTIVE-STATUS is exactly 'Y' or 'N' | Read all account records; assert ACCT-ACTIVE-STATUS is one of {'Y', 'N'} | BR-COACTUPC-47 |
| 4  | ACCT-CURR-BAL is a valid signed decimal (S9(10)V99) | Verify all balance values are numeric and within S9(10)V99 range | CVACT01Y |
| 5  | ACCT-CREDIT-LIMIT is non-negative | Sample accounts; verify ACCT-CREDIT-LIMIT >= 0 | Domain expectation; CVACT01Y |
| 6  | ACCT-EXPIRAION-DATE is a valid CCYYMMDD date string or spaces | Read all accounts; if not spaces, verify ACCT-EXPIRAION-DATE (X(10)) parses as YYYY-MM-DD calendar date | CVACT01Y; BR-CBTRN02C-17 |
| 7  | ACCT-OPEN-DATE is a valid CCYYMMDD date string or spaces | Same as expiry date check applied to ACCT-OPEN-DATE | CVACT01Y; BR-COACTUPC-76 |
| 8  | ACCT-GROUP-ID maps to at least one DISCGRP record or to 'DEFAULT' | For each distinct ACCT-GROUP-ID in ACCTDAT, verify DISCGRP contains at least one record with that group ID or a record with group ID 'DEFAULT' | BR-CBACT04C-18 |
| 9  | Account record is exactly 300 bytes | Read binary; verify fixed-length 300 bytes per record | CVACT01Y (RECLN 300) |
| 10 | ACCT-CURR-CYC-CREDIT and ACCT-CURR-CYC-DEBIT are zeroed after interest run | After CBACT04C execution, read all accounts; verify ACCT-CURR-CYC-CREDIT = 0.00 and ACCT-CURR-CYC-DEBIT = 0.00 for all processed accounts | BR-CBACT04C-35, BR-CBACT04C-36 |

---

### CUSTDAT Contract Tests

| #  | Invariant | Test | Derived From |
| -- | --------- | ---- | ------------ |
| 1  | CUST-ID is unique | Query all customer records; verify no two share the same CUST-ID | CVCUS01Y |
| 2  | CUST-FICO-CREDIT-SCORE is in range 300-850 when non-zero | Read all customers; verify CUST-FICO-CREDIT-SCORE (PIC 9(03)) is either 0 or in [300..850] | BR-COACTUPC-99 |
| 3  | CUST-PRI-CARD-HOLDER-IND is 'Y' or 'N' | Verify value is one of {'Y', 'N', spaces} | BR-COACTUPC-48 |
| 4  | CUST-ADDR-STATE-CD is a valid US two-letter state code | Verify all non-blank state codes appear in the CSLKPCDY lookup table | BR-COACTUPC-97 |
| 5  | CUST-DOB-YYYY-MM-DD is a valid calendar date when non-blank | Parse as YYYY-MM-DD; verify it is a valid date | BR-COACTUPC-79 |
| 6  | CUST-SSN Parts 1 validation: first 3 digits not 000, 666, or 900-999 | Extract first 3 digits of CUST-SSN (PIC 9(09)); verify not in {0, 666, 900..999} | BR-COACTUPC-94 |
| 7  | Customer record is exactly 500 bytes | Verify fixed-length 500 bytes | CVCUS01Y (RECLN 500) |
| 8  | CUST-FIRST-NAME and CUST-LAST-NAME contain only letters and spaces | Verify no digit or special character in name fields (consistent with alpha-only validation rule) | BR-COACTUPC-50, BR-COACTUPC-51 |

---

### CARDDAT Contract Tests

| #  | Invariant | Test | Derived From |
| -- | --------- | ---- | ------------ |
| 1  | CARD-NUM is unique | Verify no duplicate CARD-NUM values across all card records | CVACT02Y; VSAM KSDS key |
| 2  | CARD-NUM is exactly 16 characters | Verify length of CARD-NUM (PIC X(16)) is always 16 | CVACT02Y |
| 3  | CARD-ACCT-ID references an existing account | For every CARD-ACCT-ID in CARDDAT, verify a corresponding account record exists in ACCTDAT | Referential integrity; BR-CBTRN01C-lookup |
| 4  | CARD-ACTIVE-STATUS is 'Y' or 'N' | Verify value is one of {'Y', 'N'} | CVACT02Y domain |
| 5  | CARD-CVV-CD is a 3-digit numeric value | Verify PIC 9(03) contains digits 0-9 | CVACT02Y |
| 6  | Card record is exactly 150 bytes | Verify fixed-length 150 bytes | CVACT02Y (RECLN 150) |

---

### CARDXREF Contract Tests

| #  | Invariant | Test | Derived From |
| -- | --------- | ---- | ------------ |
| 1  | XREF-CARD-NUM is unique | Verify no duplicate keys in cross-reference file | CVACT03Y; VSAM KSDS |
| 2  | XREF-CARD-NUM references an existing card | For every XREF-CARD-NUM, verify a CARD-NUM record exists in CARDDAT | Referential integrity |
| 3  | XREF-ACCT-ID references an existing account | For every XREF-ACCT-ID, verify ACCT-ID exists in ACCTDAT | Referential integrity |
| 4  | XREF-CUST-ID references an existing customer | For every XREF-CUST-ID, verify CUST-ID exists in CUSTDAT | Referential integrity |
| 5  | Cross-reference record is exactly 50 bytes | Verify fixed-length 50 bytes | CVACT03Y (RECLN 50) |
| 6  | Every card in CARDDAT has a corresponding cross-reference entry | For every CARD-NUM in CARDDAT, verify a XREF-CARD-NUM exists in CARDXREF | Referential integrity; BR-CBTRN02C-9 |

---

### TRANSACT Contract Tests

| #  | Invariant | Test | Derived From |
| -- | --------- | ---- | ------------ |
| 1  | TRAN-ID is unique | Verify no two transaction records share the same TRAN-ID | CVTRA05Y; VSAM KSDS key |
| 2  | TRAN-ID is a 16-character string | Verify PIC X(16) is populated; not spaces or low-values | CVTRA05Y |
| 3  | TRAN-CARD-NUM references a card in CARDXREF | For every TRAN-CARD-NUM, verify XREF-CARD-NUM exists in CARDXREF | BR-CBTRN02C anomaly 5 (no account ID on transaction) |
| 4  | TRAN-AMT is a valid signed decimal (PIC S9(09)V99) | Verify all transaction amounts are numeric and within S9(09)V99 range | CVTRA05Y |
| 5  | TRAN-TYPE-CD is a known transaction type | For every TRAN-TYPE-CD, verify a corresponding record exists in TRANTYPE reference data | BR-CBTRN03C-lookup |
| 6  | TRAN-CAT-CD is a known category for the given type | For every TRAN-TYPE-CD + TRAN-CAT-CD combination, verify a record exists in TRANCATG | BR-CBTRN03C-lookup |
| 7  | Bill payment transactions always have type '02' and category 2 | For all transactions written by the bill payment function, verify TRAN-TYPE-CD = '02' and TRAN-CAT-CD = 2 | BR-COBIL00C-16, BR-COBIL00C-17 |
| 8  | Interest transactions always have type '01' and category '05' | For all transactions written by the interest calculation batch, verify TRAN-TYPE-CD = '01' and TRAN-CAT-CD = '05' | BR-CBACT04C-26, BR-CBACT04C-27 |
| 9  | TRAN-PROC-TS always reflects the posting time, not input time | For batch-posted transactions, TRAN-PROC-TS value is a valid timestamp matching the batch run date/time; the original input DALYTRAN-PROC-TS is discarded | BR-CBTRN02C-38 |
| 10 | Transaction record is exactly 350 bytes | Verify fixed-length 350 bytes per record | CVTRA05Y (RECLN 350) |
| 11 | Transaction ID auto-generation produces sequentially increasing IDs | After a successful add, the new TRAN-ID equals the previously highest TRAN-ID + 1 | BR-COBIL00C-28, BR-COTRN02C-50 |

---

### TCATBALF Contract Tests

| #  | Invariant | Test | Derived From |
| -- | --------- | ---- | ------------ |
| 1  | Composite key (TRANCAT-ACCT-ID + TRANCAT-TYPE-CD + TRANCAT-CD) is unique | Verify no duplicate composite keys | CVTRA01Y; VSAM KSDS composite key |
| 2  | TRANCAT-ACCT-ID references an existing account | Verify all TRANCAT-ACCT-ID values exist in ACCTDAT | Referential integrity |
| 3  | TRAN-CAT-BAL is a valid signed decimal (S9(09)V99) | Verify all balance values are numeric | CVTRA01Y |
| 4  | After interest run: sum of TRAN-CAT-BAL grouped by account equals the interest base used | For each account, sum TRAN-CAT-BAL records; verify the accumulated interest in TRANSACT matches the formula output | BR-CBACT04C-22 |
| 5  | Category balance record is exactly 50 bytes | Verify fixed-length 50 bytes | CVTRA01Y (RECLN 50) |

---

### USRSEC Contract Tests

| #  | Invariant | Test | Derived From |
| -- | --------- | ---- | ------------ |
| 1  | SEC-USR-ID is unique | Verify no duplicate SEC-USR-ID values | CSUSR01Y; VSAM KSDS key; BR-COUSR01C-21 |
| 2  | SEC-USR-ID is up to 8 characters (never blank in a valid record) | Verify SEC-USR-ID (PIC X(08)) is not spaces or low-values | BR-COUSR01C-10 |
| 3  | SEC-USR-TYPE is 'A' or 'U' for records added via normal user administration | Verify all SEC-USR-TYPE values in USRSEC are in {'A', 'U'} (records added through known paths satisfy this; records added by COUSR01C may have any non-blank value due to the known input validation gap) | BR-COUSR01C-12 note; capabilities.md User Administration |
| 4  | SEC-USR-PWD is stored as plaintext (8 characters, unencrypted) | Read a known user record; verify the password field matches the literal value that was supplied at creation without transformation | Capability BR-11 plaintext note |
| 5  | User security record is exactly 80 bytes | Verify fixed-length 80 bytes | CSUSR01Y (RECLN 80) |
| 6  | SEC-USR-FNAME and SEC-USR-LNAME are not empty for records added through user add screen | Verify name fields (PIC X(20)) are not spaces | BR-COUSR01C-8, BR-COUSR01C-9 |

---

### DALYTRAN Contract Tests

| #  | Invariant | Test | Derived From |
| -- | --------- | ---- | ------------ |
| 1  | DALYTRAN-CARD-NUM is a 16-character value | Verify PIC X(16) is populated | CVTRA06Y |
| 2  | DALYTRAN-AMT is a valid signed decimal (S9(09)V99) | Verify numeric range | CVTRA06Y |
| 3  | DALYTRAN record is exactly 350 bytes | Verify fixed-length 350 bytes | CVTRA06Y (RECLN 350) |
| 4  | DALYTRAN-PROC-TS field value is discarded on posting | After batch posting, TRAN-PROC-TS in TRANSACT does not equal DALYTRAN-PROC-TS from the input record | BR-CBTRN02C-38 |

---

### DALYREJS GDG Contract Tests

| #  | Invariant | Test | Derived From |
| -- | --------- | ---- | ------------ |
| 1  | Every reject record is exactly 430 bytes (350-byte transaction + 80-byte trailer) | Verify fixed-length 430 bytes | BR-CBTRN02C-27 |
| 2  | Reject trailer contains a 4-digit numeric reason code | Verify first 4 bytes of trailer (WS-VALIDATION-FAIL-REASON) are numeric | BR-CBTRN02C-27 |
| 3  | Reason codes are from the defined set: 100, 101, 102, or 103 | Verify no reject record has a reason code outside {100, 101, 102, 103} (note: 109 may appear due to known defect but should not produce a reject record) | BR-CBTRN02C-9, BR-CBTRN02C-13, BR-CBTRN02C-15, BR-CBTRN02C-17 |
| 4  | DALYREJS is fully replaced on each batch run | Verify that after two consecutive batch runs, the reject file contains only rejects from the most recent run | BR-CBTRN02C-8 |
| 5  | Original 350-byte transaction data is preserved verbatim in the reject record | For a known rejected transaction, verify the first 350 bytes of the reject record exactly match the input DALYTRAN record | BR-CBTRN02C-26 |

---

### DISCGRP Contract Tests

| #  | Invariant | Test | Derived From |
| -- | --------- | ---- | ------------ |
| 1  | A 'DEFAULT' group record exists for every distinct TRANCAT-TYPE-CD + TRANCAT-CD combination in TCATBALF | Before running CBACT04C, verify that for each unique type/category pair in TCATBALF, DISCGRP contains a record with group ID 'DEFAULT' and matching type/category | BR-CBACT04C-19, BR-CBACT04C-21 |
| 2  | DIS-INT-RATE is a valid signed decimal (S9(04)V99) | Verify rate values are numeric | CVTRA02Y |
| 3  | Disclosure group record is exactly 50 bytes | Verify fixed-length 50 bytes | CVTRA02Y (RECLN 50) |

---

### TRANTYPE Contract Tests

| #  | Invariant | Test | Derived From |
| -- | --------- | ---- | ------------ |
| 1  | TRAN-TYPE code is unique within the TRANTYPE reference file | Verify no duplicate TRAN-TYPE (PIC X(02)) values | CVTRA03Y |
| 2  | Every TRAN-TYPE-CD used in TRANSACT has a description record in TRANTYPE | Cross-reference all distinct TRAN-TYPE-CD values in TRANSACT against TRANTYPE | BR-CBTRN03C-lookup |
| 3  | Type record is exactly 60 bytes | Verify fixed-length 60 bytes | CVTRA03Y (RECLN 60) |

---

### TRANCATG Contract Tests

| #  | Invariant | Test | Derived From |
| -- | --------- | ---- | ------------ |
| 1  | Composite key (TRAN-TYPE-CD + TRAN-CAT-CD) is unique in TRANCATG | Verify no duplicate composite keys | CVTRA04Y |
| 2  | Every TRAN-TYPE-CD + TRAN-CAT-CD combination in TRANSACT has a description record in TRANCATG | Cross-reference all distinct type/category pairs in TRANSACT against TRANCATG | BR-CBTRN03C-lookup |
| 3  | Category record is exactly 60 bytes | Verify fixed-length 60 bytes | CVTRA04Y (RECLN 60) |

---

### EXPORT.DATA Contract Tests

| #  | Invariant | Test | Derived From |
| -- | --------- | ---- | ------------ |
| 1  | Export records are exactly 500 bytes each | Verify fixed-length 500 bytes per record | CVEXPORT (500-byte fixed) |
| 2  | Record type prefix is one of 'C', 'A', 'X', 'T', or 'D' | Verify first byte of each record is in {'C', 'A', 'X', 'T', 'D'} | BR-CBEXPORT-main (REDEFINES type prefix) |
| 3  | Record counts per type match source file counts | Count 'C' records = CUSTDAT records; 'A' records = ACCTDAT records; 'X' records = CARDXREF records; 'T' records = TRANSACT records; 'D' records = CARDDAT records | BR-CBEXPORT-nofilter |
| 4  | Import output customer count equals export 'C' record count | Run CBIMPORT on export file; verify row count in CUSTOUT matches count of 'C'-type records in export file | BR-CBIMPORT-split |

---

## Database Contracts

| Table / Segment | Business Purpose | Writers | Readers | Key Columns |
| --------------- | ---------------- | ------- | ------- | ----------- |
| CARDDEMO.TRANSACTION_TYPE | Transaction type reference data (DB2 extension module) | COBTUPDT (batch DML) | COTRTLIC (CICS list), COTRTUPC (CICS update), TRANEXTR (extract) | TR_TYPE (primary key) |
| IMS DBPAUTP0 PAUTSUM0 | Pending authorization summary (IMS extension module) | COPAUA0C (authorization event processor) | COPAUS0C, COPAUS1C | Account ID (root segment key) |
| IMS DBPAUTP0 PAUTDTL1 | Pending authorization detail (IMS extension module) | COPAUA0C | COPAUS1C | Account ID + detail sequence (child key) |

### CARDDEMO.TRANSACTION_TYPE Contract Tests

| #  | Invariant | Test | Derived From |
| -- | --------- | ---- | ------------ |
| 1  | TR_TYPE primary key is unique | Verify no duplicate TR_TYPE values in the DB2 table | COBTUPDT SQL; capabilities.md Transaction Type Administration |
| 2  | Every TRAN-TYPE in TRANTYPE VSAM extract matches a row in DB2 | After TRANEXTR extract, verify row counts match; verify each TR_TYPE value in VSAM appears in DB2 | Data flows: TranType Sync chain |
| 3  | Add action 'A' inserts row; Delete action 'D' removes row; Update action 'U' modifies row | Run COBTUPDT with each action code; verify the DB2 table reflects the expected state | BR-COTRTLIC-COBTUPDT |

---

## Message Contracts

| Queue / Channel | Business Purpose | Producers | Consumers | Message Format |
| --------------- | ---------------- | --------- | --------- | -------------- |
| Extra-partition TDQ (JES internal reader) | Online-to-batch report job submission | CORPT00C | JES (job submission) | JCL records: 80-byte fixed (PIC X(80)) |
| CARDDEMO.REQUEST.QUEUE | MQ account and date inquiry requests (extension) | External client | COACCT01, CODATE01 | 1000-byte fixed: WS-FUNC (4 bytes) + WS-KEY (11-byte account ID) + filler (985 bytes) |
| CARD.DEMO.REPLY.ACCT | Account inquiry reply (extension) | COACCT01 | External client | 1000-byte buffer with account status, balance, credit limit, dates, and group ID |
| CARD.DEMO.REPLY.DATE | Date/time inquiry reply (extension) | CODATE01 | External client | 1000-byte buffer: 'SYSTEM DATE : MM-DD-YYYY SYSTEM TIME : HH:MM:SS' |
| CARD.DEMO.ERROR | MQ error messages (extension) | COACCT01, CODATE01 | External monitoring | MQ-ERR-DISPLAY: paragraph (25 bytes) + return message (25 bytes) + condition (2 bytes) + reason (5 bytes) + queue name (48 bytes) |

### Extra-partition TDQ (JES Internal Reader) Contract Tests

| #  | Invariant | Test | Derived From |
| -- | --------- | ---- | ------------ |
| 1  | Each JCL record written to TDQ is exactly 80 bytes | Intercept TDQ writes; verify each record is exactly 80 bytes PIC X(80) | BR-CORPT00C-submit; data flows messaging |
| 2  | Submitted JCL produces a runnable batch report job | Trigger report submission; verify JES accepts the JCL without syntax errors and the job appears in the JES job queue | BR-CORPT00C-submit |
| 3  | Date parameters in submitted JCL reflect the operator-entered range | Extract start and end date values from the submitted JCL; verify they match the values entered on the online screen | BR-CORPT00C-datevalidation |

### CARDDEMO.REQUEST.QUEUE Contract Tests

| #  | Invariant | Test | Derived From |
| -- | --------- | ---- | ------------ |
| 1  | Request message is exactly 1000 bytes | Verify message length on GET | data-flows.md messaging |
| 2  | Function code 'INQA' triggers account inquiry response on CARD.DEMO.REPLY.ACCT | Send message with WS-FUNC = 'INQA' and valid account ID; verify reply arrives on CARD.DEMO.REPLY.ACCT with account data | data-flows.md MQ Acct Inquiry chain |
| 3  | Invalid account ID routes error to CARD.DEMO.ERROR | Send 'INQA' message with non-existent account ID; verify error message arrives on CARD.DEMO.ERROR | data-flows.md |
| 4  | Reply date/time format is 'MM-DD-YYYY HH:MM:SS' | Trigger date inquiry; verify CARD.DEMO.REPLY.DATE contains the pattern 'SYSTEM DATE : MM-DD-YYYY SYSTEM TIME : HH:MM:SS' | data-flows.md MQ Date Inquiry chain |

---

## Data Invariants

Cross-store consistency rules that must hold across the modernized system:

| #  | Invariant | Stores Involved | Test | Derived From |
| -- | --------- | --------------- | ---- | ------------ |
| 1  | Every card in CARDDAT has exactly one cross-reference entry in CARDXREF | CARDDAT, CARDXREF | For every CARD-NUM in CARDDAT, assert exactly one XREF-CARD-NUM = CARD-NUM in CARDXREF; and vice versa | CVACT02Y, CVACT03Y; BR-CBTRN02C-9 |
| 2  | Every cross-reference XREF-ACCT-ID has a corresponding account record | CARDXREF, ACCTDAT | For every XREF-ACCT-ID in CARDXREF, assert ACCT-ID exists in ACCTDAT | CVACT03Y, CVACT01Y |
| 3  | Every cross-reference XREF-CUST-ID has a corresponding customer record | CARDXREF, CUSTDAT | For every XREF-CUST-ID in CARDXREF, assert CUST-ID exists in CUSTDAT | CVACT03Y, CVCUS01Y |
| 4  | Every transaction TRAN-CARD-NUM maps back to a card via CARDXREF | TRANSACT, CARDXREF | For every TRAN-CARD-NUM in TRANSACT, assert XREF-CARD-NUM exists in CARDXREF | CVTRA05Y, CVACT03Y; BR-CBTRN02C anomaly 5 |
| 5  | Account balance in ACCTDAT reflects sum of posted transaction amounts | ACCTDAT, TRANSACT, TCATBALF | After a batch posting run, for a sample account: verify ACCT-CURR-BAL equals the prior balance plus the sum of DALYTRAN-AMT values posted in this run | BR-CBTRN02C-33 |
| 6  | Cycle-to-date category balances in TCATBALF sum to match the cycle portion of ACCT-CURR-BAL | ACCTDAT, TCATBALF | For a given account within a billing cycle, sum all TRAN-CAT-BAL records; verify the net matches the net of ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT | BR-CBTRN02C-28 through BR-CBTRN02C-35 |
| 7  | User in USRSEC must have a valid SEC-USR-TYPE to authenticate via the signon screen | USRSEC | For each user added via admin user-add function, verify the user can authenticate at the signon screen and is routed to the correct menu for their type | BR-COSGN00C-21, BR-COSGN00C-22; BR-COUSR01C-18 |
| 8  | After a successful bill payment: account balance is zero AND a payment transaction exists in TRANSACT | ACCTDAT, TRANSACT | After confirming a bill payment for an account with a known positive balance, verify ACCT-CURR-BAL = 0.00 in ACCTDAT AND a TRAN-RECORD with TRAN-TYPE-CD = '02' and TRAN-AMT = the prior balance exists in TRANSACT | BR-COBIL00C-14, BR-COBIL00C-24 |
| 9  | After interest batch: accumulated interest appears in both ACCT-CURR-BAL and as a TRANSACT record with type '01' | ACCTDAT, TRANSACT | After CBACT04C run, for a sample account: verify ACCT-CURR-BAL increased by the computed interest AND a TRANSACT record exists with TRAN-TYPE-CD = '01', TRAN-AMT = the computed interest | BR-CBACT04C-22, BR-CBACT04C-34 |
| 10 | After export + import: account IDs, customer IDs, and card numbers are identical in import output vs. original VSAM source | ACCTDAT, CUSTDAT, CARDDAT, EXPORT.DATA, import output files | Run CBEXPORT then CBIMPORT; compare ACCT-ID values in ACCTDAT with ACCT-ID values in ACCTOUT; repeat for customer IDs and card numbers | BR-CBEXPORT-main, BR-CBIMPORT-split |
| 11 | TCATBALF records are only created for transaction type/category combinations that appear in TRANTYPE and TRANCATG | TCATBALF, TRANTYPE, TRANCATG | Query all TRANCAT-TYPE-CD + TRANCAT-CD combinations in TCATBALF; verify each pair exists in TRANCATG reference data | BR-CBTRN02C-28, BR-CBTRN03C-lookup |
