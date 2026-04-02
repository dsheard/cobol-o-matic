---
type: data
subtype: file-layouts
status: draft
confidence: high
last_pass: 5
---

# File Layouts

File descriptions (FD/SD) and their record layouts extracted from FILE SECTION, plus CICS VSAM datasets identified in online programs.

## Files

### ACCTDAT - Account Master File

| Property | Value |
| -------- | ----- |
| FD Name | ACCTFILE-FILE / ACCOUNT-FILE |
| DD Name / Path | ACCTDAT (CICS dataset name) |
| Organisation | Indexed (VSAM KSDS) |
| Access Mode | Random / Dynamic |
| Record Length | 300 bytes |
| Key Field | ACCT-ID PIC 9(11) |
| Read By | CBACT01C, CBTRN01C, CBTRN02C, CBACT04C, COACTVWC, COACTUPC, COBIL00C, CBSTM03B |
| Written By | COACTUPC (REWRITE via CICS) |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | ACCOUNT-RECORD | | 0 | 300 | Account master record |
| 05 | ACCT-ID | 9(11) | 0 | 11 | Account ID (primary key) |
| 05 | ACCT-ACTIVE-STATUS | X(01) | 11 | 1 | Active flag (Y/N) |
| 05 | ACCT-CURR-BAL | S9(10)V99 | 12 | 12 | Current balance |
| 05 | ACCT-CREDIT-LIMIT | S9(10)V99 | 24 | 12 | Credit limit |
| 05 | ACCT-CASH-CREDIT-LIMIT | S9(10)V99 | 36 | 12 | Cash credit limit |
| 05 | ACCT-OPEN-DATE | X(10) | 48 | 10 | Open date (YYYY-MM-DD) |
| 05 | ACCT-EXPIRAION-DATE | X(10) | 58 | 10 | Expiration date |
| 05 | ACCT-REISSUE-DATE | X(10) | 68 | 10 | Reissue date |
| 05 | ACCT-CURR-CYC-CREDIT | S9(10)V99 | 78 | 12 | Cycle credits |
| 05 | ACCT-CURR-CYC-DEBIT | S9(10)V99 | 90 | 12 | Cycle debits |
| 05 | ACCT-ADDR-ZIP | X(10) | 102 | 10 | Billing ZIP |
| 05 | ACCT-GROUP-ID | X(10) | 112 | 10 | Disclosure group ID |
| 05 | FILLER | X(178) | 122 | 178 | Reserved |

---

### CUSTDAT - Customer Master File

| Property | Value |
| -------- | ----- |
| FD Name | CUSTFILE-FILE / CUSTOMER-FILE |
| DD Name / Path | CUSTDAT (CICS dataset name) |
| Organisation | Indexed (VSAM KSDS) |
| Access Mode | Random |
| Record Length | 500 bytes |
| Key Field | CUST-ID PIC 9(09) |
| Read By | CBTRN01C, CBCUS01C, COACTVWC, COACTUPC, CBSTM03B |
| Written By | COACTUPC (REWRITE via CICS) |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | CUSTOMER-RECORD | | 0 | 500 | Customer master record |
| 05 | CUST-ID | 9(09) | 0 | 9 | Customer ID (primary key) |
| 05 | CUST-FIRST-NAME | X(25) | 9 | 25 | First name |
| 05 | CUST-MIDDLE-NAME | X(25) | 34 | 25 | Middle name |
| 05 | CUST-LAST-NAME | X(25) | 59 | 25 | Last name |
| 05 | CUST-ADDR-LINE-1 | X(50) | 84 | 50 | Address line 1 |
| 05 | CUST-ADDR-LINE-2 | X(50) | 134 | 50 | Address line 2 |
| 05 | CUST-ADDR-LINE-3 | X(50) | 184 | 50 | Address line 3 |
| 05 | CUST-ADDR-STATE-CD | X(02) | 234 | 2 | State code |
| 05 | CUST-ADDR-COUNTRY-CD | X(03) | 236 | 3 | Country code |
| 05 | CUST-ADDR-ZIP | X(10) | 239 | 10 | ZIP code |
| 05 | CUST-PHONE-NUM-1 | X(15) | 249 | 15 | Primary phone |
| 05 | CUST-PHONE-NUM-2 | X(15) | 264 | 15 | Secondary phone |
| 05 | CUST-SSN | 9(09) | 279 | 9 | Social security number |
| 05 | CUST-GOVT-ISSUED-ID | X(20) | 288 | 20 | Government ID |
| 05 | CUST-DOB-YYYY-MM-DD | X(10) | 308 | 10 | Date of birth |
| 05 | CUST-EFT-ACCOUNT-ID | X(10) | 318 | 10 | EFT account |
| 05 | CUST-PRI-CARD-HOLDER-IND | X(01) | 328 | 1 | Primary cardholder |
| 05 | CUST-FICO-CREDIT-SCORE | 9(03) | 329 | 3 | FICO score |
| 05 | FILLER | X(168) | 332 | 168 | Reserved |

---

### CARDDAT - Credit Card File

| Property | Value |
| -------- | ----- |
| FD Name | CARDFILE-FILE / CARD-FILE |
| DD Name / Path | CARDDAT (CICS dataset name) |
| Organisation | Indexed (VSAM KSDS) |
| Access Mode | Random / Dynamic |
| Record Length | 150 bytes |
| Key Field | CARD-NUM PIC X(16) |
| Alternate Index | CARDAIX - by CARD-ACCT-ID (account ID) |
| Read By | CBACT02C, CBTRN01C, COCRDLIC, COCRDSLC, COCRDUPC, COACTUPC, COACTVWC |
| Written By | COCRDUPC (REWRITE via CICS) |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | CARD-RECORD | | 0 | 150 | Credit card record |
| 05 | CARD-NUM | X(16) | 0 | 16 | Card number (primary key) |
| 05 | CARD-ACCT-ID | 9(11) | 16 | 11 | Associated account ID |
| 05 | CARD-CVV-CD | 9(03) | 27 | 3 | CVV code |
| 05 | CARD-EMBOSSED-NAME | X(50) | 30 | 50 | Embossed cardholder name |
| 05 | CARD-EXPIRAION-DATE | X(10) | 80 | 10 | Expiration date |
| 05 | CARD-ACTIVE-STATUS | X(01) | 90 | 1 | Active status (Y/N) |
| 05 | FILLER | X(59) | 91 | 59 | Reserved |

---

### CARDXREF - Card Cross-Reference File

| Property | Value |
| -------- | ----- |
| FD Name | XREF-FILE / XREFFILE-FILE |
| DD Name / Path | CXREF / CXACAIX (alternate index by account) |
| Organisation | Indexed (VSAM KSDS) |
| Access Mode | Random |
| Record Length | 50 bytes |
| Key Field | XREF-CARD-NUM PIC X(16) |
| Alternate Index | CXACAIX - by XREF-ACCT-ID |
| Read By | CBACT03C, CBTRN01C, CBTRN02C, CBACT04C, COTRN02C, COACTUPC, COACTVWC, CBSTM03B |
| Written By | None (reference file) |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | CARD-XREF-RECORD | | 0 | 50 | Card cross-reference record |
| 05 | XREF-CARD-NUM | X(16) | 0 | 16 | Card number (primary key) |
| 05 | XREF-CUST-ID | 9(09) | 16 | 9 | Customer ID |
| 05 | XREF-ACCT-ID | 9(11) | 25 | 11 | Account ID |
| 05 | FILLER | X(14) | 36 | 14 | Reserved |

---

### TRANSACT - Transaction File

| Property | Value |
| -------- | ----- |
| FD Name | TRANSACT-FILE / TRANFILE |
| DD Name / Path | TRANSACT (CICS dataset name) |
| Organisation | Indexed (VSAM KSDS) |
| Access Mode | Sequential / Random / Dynamic |
| Record Length | 350 bytes |
| Key Field | TRAN-ID PIC X(16) |
| Read By | CBTRN02C, CBACT04C, CBTRN03C, COTRN00C, COTRN01C, COTRN02C, COBIL00C, CORPT00C |
| Written By | CBTRN02C (batch), COTRN02C (CICS WRITE), COBIL00C (CICS WRITE) |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | TRAN-RECORD | | 0 | 350 | Transaction record |
| 05 | TRAN-ID | X(16) | 0 | 16 | Transaction ID (primary key) |
| 05 | TRAN-TYPE-CD | X(02) | 16 | 2 | Transaction type code |
| 05 | TRAN-CAT-CD | 9(04) | 18 | 4 | Category code |
| 05 | TRAN-SOURCE | X(10) | 22 | 10 | Source system |
| 05 | TRAN-DESC | X(100) | 32 | 100 | Description |
| 05 | TRAN-AMT | S9(09)V99 | 132 | 11 | Amount (signed) |
| 05 | TRAN-MERCHANT-ID | 9(09) | 143 | 9 | Merchant ID |
| 05 | TRAN-MERCHANT-NAME | X(50) | 152 | 50 | Merchant name |
| 05 | TRAN-MERCHANT-CITY | X(50) | 202 | 50 | Merchant city |
| 05 | TRAN-MERCHANT-ZIP | X(10) | 252 | 10 | Merchant ZIP |
| 05 | TRAN-CARD-NUM | X(16) | 262 | 16 | Card number |
| 05 | TRAN-ORIG-TS | X(26) | 278 | 26 | Origination timestamp |
| 05 | TRAN-PROC-TS | X(26) | 304 | 26 | Processing timestamp |
| 05 | FILLER | X(20) | 330 | 20 | Reserved |

---

### TRNXFILE - Transaction File for Statement Generation

| Property | Value |
| -------- | ----- |
| FD Name | TRNX-FILE (in CBSTM03B) |
| DD Name / Path | TRNXFILE (batch DD); DSN=AWS.M2.CARDDEMO.TRXFL.VSAM.KSDS per CREASTMT.JCL |
| Organisation | Indexed (VSAM KSDS) |
| Access Mode | Sequential (CBSTM03B reads sequentially via LK-M03B-OPER='R') |
| Record Length | 350 bytes |
| Key Field | FD-TRNXS-ID (composite: TRNX-CARD-NUM X(16) + TRNX-ID X(16)) |
| Read By | CBSTM03A (via CBSTM03B subroutine) |
| Written By | External process (not in this source set) |

> Note: TRNXFILE uses the same 350-byte transaction layout as TRANSACT but is keyed differently. The composite key (card number + transaction ID) enables CBSTM03A to retrieve all transactions for a specific card by partial-key browse. COSTM01.CPY defines the TRNX-RECORD layout with the composite key structure.

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | TRNX-RECORD | | 0 | 350 | Transaction record for statement |
| 05 | TRNX-KEY | | 0 | 32 | Composite primary key |
| 10 | TRNX-CARD-NUM | X(16) | 0 | 16 | Card number (first key component) |
| 10 | TRNX-ID | X(16) | 16 | 16 | Transaction ID (second key component) |
| 05 | TRNX-REST | | 32 | 318 | Non-key transaction data |
| 10 | TRNX-TYPE-CD | X(02) | 32 | 2 | Transaction type code |
| 10 | TRNX-CAT-CD | 9(04) | 34 | 4 | Category code |
| 10 | TRNX-SOURCE | X(10) | 38 | 10 | Source system |
| 10 | TRNX-DESC | X(100) | 48 | 100 | Description |
| 10 | TRNX-AMT | S9(09)V99 | 148 | 11 | Amount (signed) |
| 10 | TRNX-MERCHANT-ID | 9(09) | 159 | 9 | Merchant ID |
| 10 | TRNX-MERCHANT-NAME | X(50) | 168 | 50 | Merchant name |
| 10 | TRNX-MERCHANT-CITY | X(50) | 218 | 50 | Merchant city |
| 10 | TRNX-MERCHANT-ZIP | X(10) | 268 | 10 | Merchant ZIP |
| 10 | TRNX-ORIG-TS | X(26) | 278 | 26 | Origination timestamp |
| 10 | TRNX-PROC-TS | X(26) | 304 | 26 | Processing timestamp |
| 10 | FILLER | X(20) | 330 | 20 | Reserved |

---

### DALYTRAN - Daily Transaction Input File

| Property | Value |
| -------- | ----- |
| FD Name | DALYTRAN-FILE |
| DD Name / Path | DALYTRAN (batch DD) |
| Organisation | Sequential |
| Access Mode | Sequential |
| Record Length | 350 bytes |
| Read By | CBTRN01C, CBTRN02C |
| Written By | External feed / prior batch |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | DALYTRAN-RECORD | | 0 | 350 | Daily transaction input |
| 05 | DALYTRAN-ID | X(16) | 0 | 16 | Transaction ID |
| 05 | DALYTRAN-TYPE-CD | X(02) | 16 | 2 | Type code |
| 05 | DALYTRAN-CAT-CD | 9(04) | 18 | 4 | Category code |
| 05 | DALYTRAN-SOURCE | X(10) | 22 | 10 | Source system |
| 05 | DALYTRAN-DESC | X(100) | 32 | 100 | Description |
| 05 | DALYTRAN-AMT | S9(09)V99 | 132 | 11 | Amount |
| 05 | DALYTRAN-MERCHANT-ID | 9(09) | 143 | 9 | Merchant ID |
| 05 | DALYTRAN-MERCHANT-NAME | X(50) | 152 | 50 | Merchant name |
| 05 | DALYTRAN-MERCHANT-CITY | X(50) | 202 | 50 | Merchant city |
| 05 | DALYTRAN-MERCHANT-ZIP | X(10) | 252 | 10 | Merchant ZIP |
| 05 | DALYTRAN-CARD-NUM | X(16) | 262 | 16 | Card number |
| 05 | DALYTRAN-ORIG-TS | X(26) | 278 | 26 | Origination timestamp |
| 05 | DALYTRAN-PROC-TS | X(26) | 304 | 26 | Processing timestamp |
| 05 | FILLER | X(20) | 330 | 20 | Reserved |

---

### DALYREJS - Daily Transaction Rejection File

| Property | Value |
| -------- | ----- |
| FD Name | DALYREJS-FILE |
| DD Name / Path | DALYREJS (batch DD) |
| Organisation | Sequential |
| Access Mode | Sequential |
| Record Length | 430 bytes (350 + 80 trailer) |
| Read By | None |
| Written By | CBTRN02C (rejected transaction records) |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | FD-REJS-RECORD | | 0 | 430 | Rejection record |
| 05 | FD-REJECT-RECORD | X(350) | 0 | 350 | Original DALYTRAN record (verbatim) |
| 05 | FD-VALIDATION-TRAILER | X(80) | 350 | 80 | Validation error reason appended by CBTRN02C |

---

### TCATBAL - Transaction Category Balance File

| Property | Value |
| -------- | ----- |
| FD Name | TCATBAL-FILE |
| DD Name / Path | TCATBAL (batch DD) |
| Organisation | Indexed (VSAM KSDS) |
| Access Mode | Random / Dynamic |
| Record Length | 50 bytes |
| Key Field | TRAN-CAT-KEY (composite: ACCT-ID 9(11) + TYPE-CD X(02) + CAT-CD 9(04)) |
| Read By | CBACT04C |
| Written By | CBTRN02C |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | TRAN-CAT-BAL-RECORD | | 0 | 50 | Transaction category balance |
| 05 | TRAN-CAT-KEY | | 0 | 17 | Composite primary key |
| 10 | TRANCAT-ACCT-ID | 9(11) | 0 | 11 | Account ID |
| 10 | TRANCAT-TYPE-CD | X(02) | 11 | 2 | Transaction type code |
| 10 | TRANCAT-CD | 9(04) | 13 | 4 | Transaction category code |
| 05 | TRAN-CAT-BAL | S9(09)V99 | 17 | 11 | Category balance |
| 05 | FILLER | X(22) | 28 | 22 | Reserved |

---

### DISCGRP - Disclosure Group (Interest Rate) File

| Property | Value |
| -------- | ----- |
| FD Name | DISCGRP-FILE |
| DD Name / Path | DISCGRP (batch DD) |
| Organisation | Indexed (VSAM KSDS) |
| Access Mode | Random |
| Record Length | 50 bytes |
| Key Field | DIS-GROUP-KEY (composite: GROUP-ID X(10) + TYPE-CD X(02) + CAT-CD 9(04)) |
| Read By | CBACT04C |
| Written By | None (reference/setup file) |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | DIS-GROUP-RECORD | | 0 | 50 | Disclosure group record |
| 05 | DIS-GROUP-KEY | | 0 | 16 | Composite primary key |
| 10 | DIS-ACCT-GROUP-ID | X(10) | 0 | 10 | Account group ID |
| 10 | DIS-TRAN-TYPE-CD | X(02) | 10 | 2 | Transaction type code |
| 10 | DIS-TRAN-CAT-CD | 9(04) | 12 | 4 | Transaction category code |
| 05 | DIS-INT-RATE | S9(04)V99 | 16 | 6 | Interest rate |
| 05 | FILLER | X(28) | 22 | 28 | Reserved |

---

### TRANTYPE - Transaction Type Reference File

| Property | Value |
| -------- | ----- |
| FD Name | TRANTYPE-FILE |
| DD Name / Path | TRANTYPE (batch DD) |
| Organisation | Indexed (VSAM KSDS) |
| Access Mode | Sequential |
| Record Length | 60 bytes |
| Key Field | TRAN-TYPE PIC X(02) |
| Read By | CBTRN03C |
| Written By | None (reference file) |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | TRAN-TYPE-RECORD | | 0 | 60 | Transaction type record |
| 05 | TRAN-TYPE | X(02) | 0 | 2 | Transaction type code (key) |
| 05 | TRAN-TYPE-DESC | X(50) | 2 | 50 | Description |
| 05 | FILLER | X(08) | 52 | 8 | Reserved |

---

### TRANCATG - Transaction Category Reference File

| Property | Value |
| -------- | ----- |
| FD Name | TRANCATG-FILE |
| DD Name / Path | TRANCATG (batch DD) |
| Organisation | Indexed (VSAM KSDS) |
| Access Mode | Sequential |
| Record Length | 60 bytes |
| Key Field | TRAN-CAT-KEY (composite: TYPE-CD X(02) + CAT-CD 9(04)) |
| Read By | CBTRN03C |
| Written By | None (reference file) |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | TRAN-CAT-RECORD | | 0 | 60 | Transaction category record |
| 05 | TRAN-CAT-KEY | | 0 | 6 | Composite primary key |
| 10 | TRAN-TYPE-CD | X(02) | 0 | 2 | Transaction type code |
| 10 | TRAN-CAT-CD | 9(04) | 2 | 4 | Category code |
| 05 | TRAN-CAT-TYPE-DESC | X(50) | 6 | 50 | Category description |
| 05 | FILLER | X(04) | 56 | 4 | Reserved |

---

### USRSEC - User Security File

| Property | Value |
| -------- | ----- |
| FD Name | (CICS VSAM, no FD in batch) |
| DD Name / Path | WS-USRSEC-FILE (resolved at runtime via CICS) |
| Organisation | Indexed (VSAM KSDS) |
| Access Mode | Random / Sequential |
| Record Length | 80 bytes |
| Key Field | SEC-USR-ID PIC X(08) |
| Read By | COSGN00C, COUSR00C, COUSR02C, COUSR03C |
| Written By | COUSR01C (WRITE), COUSR02C (REWRITE), COUSR03C (DELETE) |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | SEC-USER-DATA | | 0 | 80 | User security record |
| 05 | SEC-USR-ID | X(08) | 0 | 8 | User ID (primary key) |
| 05 | SEC-USR-FNAME | X(20) | 8 | 20 | First name |
| 05 | SEC-USR-LNAME | X(20) | 28 | 20 | Last name |
| 05 | SEC-USR-PWD | X(08) | 48 | 8 | Password (plaintext) |
| 05 | SEC-USR-TYPE | X(01) | 56 | 1 | User type (A/U) |
| 05 | SEC-USR-FILLER | X(23) | 57 | 23 | Reserved |

---

### REPORT-FILE - Daily Transaction Report Output

| Property | Value |
| -------- | ----- |
| FD Name | REPORT-FILE |
| DD Name / Path | REPORT (batch DD) |
| Organisation | Sequential |
| Access Mode | Sequential |
| Record Length | 133 bytes |
| Read By | None |
| Written By | CBTRN03C |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | FD-REPTFILE-REC | X(133) | 0 | 133 | Report line (variable content) |

---

### DATE-PARMS-FILE - Report Date Parameter File

| Property | Value |
| -------- | ----- |
| FD Name | DATE-PARMS-FILE |
| DD Name / Path | DATEPARM (batch DD) |
| Organisation | Sequential |
| Access Mode | Sequential |
| Record Length | 80 bytes |
| Read By | CBTRN03C |
| Written By | CORPT00C (writes to TDQ 'JOBS', which drives the batch JCL that provides this file) |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | FD-DATEPARM-REC | X(80) | 0 | 80 | Date parameter record |
| - | WS-START-DATE (working storage) | X(10) | 0 | 10 | Report start date YYYY-MM-DD |
| - | FILLER | X(01) | 10 | 1 | Space separator |
| - | WS-END-DATE (working storage) | X(10) | 11 | 10 | Report end date YYYY-MM-DD |

> Note: The FD defines the full 80-byte record. The CBTRN03C working storage WS-DATEPARM-RECORD shows the actual content: start date (10), space (1), end date (10), with remaining bytes unused.

---

### EXPORTFILE - Multi-Record Sequential Export File

| Property | Value |
| -------- | ----- |
| FD Name | (defined in CBEXPORT.cbl) |
| DD Name / Path | EXPORTFILE (batch DD) |
| Organisation | Sequential |
| Access Mode | Sequential |
| Record Length | 500 bytes |
| Read By | CBIMPORT |
| Written By | CBEXPORT |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | EXPORT-RECORD | | 0 | 500 | Export record (multi-type via REDEFINES) |
| 05 | EXPORT-REC-TYPE | X(1) | 0 | 1 | Record type ('C'=customer, 'A'=account, 'T'=transaction, 'X'=xref, 'K'=card) |
| 05 | EXPORT-TIMESTAMP | X(26) | 1 | 26 | Export timestamp |
| 05 | EXPORT-SEQUENCE-NUM | 9(9) COMP | 27 | 4 | Sequence number (binary, 4 bytes) |
| 05 | EXPORT-BRANCH-ID | X(4) | 31 | 4 | Branch identifier |
| 05 | EXPORT-REGION-CODE | X(5) | 35 | 5 | Region code |
| 05 | EXPORT-RECORD-DATA | X(460) | 40 | 460 | Type-specific payload (see CVEXPORT.cpy for sub-structures) |

**Type-Specific Payload Sub-Structures (REDEFINES EXPORT-RECORD-DATA):**

| Record Type | Redefines Name | Key Fields | Notes |
| ----------- | -------------- | ---------- | ----- |
| 'C' | EXPORT-CUSTOMER-DATA | EXP-CUST-ID 9(9) COMP; address array OCCURS 3 TIMES; phone array OCCURS 2 TIMES | FICO as COMP-3; full customer fields including state, country, ZIP, SSN, DOB, EFT |
| 'A' | EXPORT-ACCOUNT-DATA | EXP-ACCT-ID 9(11); balance as COMP-3; cycle-debit as COMP | Mixed DISPLAY/COMP fields; includes active-status, dates, credit-limit, group-id |
| 'T' | EXPORT-TRANSACTION-DATA | EXP-TRAN-ID X(16); amount COMP-3; merchant-id COMP | Full transaction fields including card-num, timestamps, merchant detail |
| 'X' | EXPORT-CARD-XREF-DATA | EXP-XREF-CARD-NUM X(16); EXP-XREF-CUST-ID 9(09); EXP-XREF-ACCT-ID 9(11) COMP | Three-field xref record |
| 'K' | EXPORT-CARD-DATA | EXP-CARD-NUM X(16); EXP-CARD-ACCT-ID 9(11) COMP; CVV COMP | Full card including embossed name, expiry date, active status |

> Note (iteration 5 correction): Record type for card data is 'K' (not 'D' as previously noted in copybook inventory). Type codes confirmed directly from CVEXPORT.cpy source.

---

### STMTFILE - Account Statement Plain-Text Output

| Property | Value |
| -------- | ----- |
| FD Name | STMT-FILE |
| DD Name / Path | STMTFILE (batch DD); per CREASTMT.JCL, step 1 uses DELETE disposition, step 2 creates new dataset |
| Organisation | Sequential |
| Access Mode | Sequential |
| Record Length | 80 bytes |
| Read By | None |
| Written By | CBSTM03A |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | FD-STMTFILE-REC | X(80) | 0 | 80 | Statement text line (80 characters) |

> Note: CBSTM03A writes formatted plain-text account statement lines to STMTFILE. The content includes customer name, address, account ID, balance, FICO score, and per-transaction detail lines (TRAN-ID, description, amount) using STATEMENT-LINES working storage templates.

---

### HTMLFILE - Account Statement HTML Output

| Property | Value |
| -------- | ----- |
| FD Name | HTML-FILE |
| DD Name / Path | HTMLFILE (batch DD); per CREASTMT.JCL, step 2 creates new dataset |
| Organisation | Sequential |
| Access Mode | Sequential |
| Record Length | 100 bytes |
| Read By | None |
| Written By | CBSTM03A |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | FD-HTMLFILE-REC | X(100) | 0 | 100 | HTML output line (100 characters) |

> Note: CBSTM03A writes HTML-formatted account statement lines to HTMLFILE. The content mirrors STMTFILE but in HTML table format. HTML_LINES working storage contains the complete set of HTML tags and styled table cell literals used to construct the output.

---

### OUT-FILE - Account Detail Output File (CBACT01C)

| Property | Value |
| -------- | ----- |
| FD Name | OUT-FILE |
| DD Name / Path | OUTFILE (batch DD) |
| Organisation | Sequential |
| Access Mode | Sequential |
| Record Length | ~107 bytes |
| Read By | None |
| Written By | CBACT01C |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | OUT-ACCT-REC | | 0 | ~107 | Account output record |
| 05 | OUT-ACCT-ID | 9(11) | 0 | 11 | Account ID |
| 05 | OUT-ACCT-ACTIVE-STATUS | X(01) | 11 | 1 | Active status |
| 05 | OUT-ACCT-CURR-BAL | S9(10)V99 | 12 | 12 | Current balance |
| 05 | OUT-ACCT-CREDIT-LIMIT | S9(10)V99 | 24 | 12 | Credit limit |
| 05 | OUT-ACCT-CASH-CREDIT-LIMIT | S9(10)V99 | 36 | 12 | Cash credit limit |
| 05 | OUT-ACCT-OPEN-DATE | X(10) | 48 | 10 | Open date |
| 05 | OUT-ACCT-EXPIRAION-DATE | X(10) | 58 | 10 | Expiration date |
| 05 | OUT-ACCT-REISSUE-DATE | X(10) | 68 | 10 | Reissue date |
| 05 | OUT-ACCT-CURR-CYC-CREDIT | S9(10)V99 | 78 | 12 | Cycle credits |
| 05 | OUT-ACCT-CURR-CYC-DEBIT | S9(10)V99 COMP-3 | 90 | 7 | Cycle debits (packed decimal) |
| 05 | OUT-ACCT-GROUP-ID | X(10) | 97 | 10 | Group ID |

---

### ARRY-FILE - Account Array Output File (CBACT01C)

| Property | Value |
| -------- | ----- |
| FD Name | ARRY-FILE |
| DD Name / Path | ARRYFILE (batch DD) |
| Organisation | Sequential |
| Access Mode | Sequential |
| Record Length | ~125 bytes |
| Read By | None |
| Written By | CBACT01C |

**Record Layout:**

| Level | Name | PIC | Offset | Length | Description |
| ----- | ---- | --- | ------ | ------ | ----------- |
| 01 | ARR-ARRAY-REC | | 0 | ~125 | Account array record |
| 05 | ARR-ACCT-ID | 9(11) | 0 | 11 | Account ID |
| 05 | ARR-ACCT-BAL OCCURS 5 TIMES | | 11 | 110 | Array of 5 balance entries |
| 10 | ARR-ACCT-CURR-BAL | S9(10)V99 | varies | 12 | Current balance (DISPLAY) |
| 10 | ARR-ACCT-CURR-CYC-DEBIT | S9(10)V99 COMP-3 | varies | 7 | Cycle debit (packed) |
| 05 | ARR-FILLER | X(04) | ~121 | 4 | Reserved |

---

### VBRC-FILE - Variable-Length Account Record File (CBACT01C)

| Property | Value |
| -------- | ----- |
| FD Name | VBRC-FILE |
| DD Name / Path | VBRCFILE (batch DD) |
| Organisation | Sequential |
| Access Mode | Sequential |
| Record Length | Variable: 10 to 80 bytes |
| Recording Mode | V (variable) |
| Read By | None |
| Written By | CBACT01C |

**Record Layout:**

Two working-storage record templates are populated and written:

**VBRC-REC1 (short record, ~12 bytes):**

| Level | Name | PIC | Length | Description |
| ----- | ---- | --- | ------ | ----------- |
| 01 | VBRC-REC1 | | ~12 | Short variable-length record |
| 05 | VB1-ACCT-ID | 9(11) | 11 | Account ID |
| 05 | VB1-ACCT-ACTIVE-STATUS | X(01) | 1 | Active status |

**VBRC-REC2 (longer record):**

| Level | Name | PIC | Length | Description |
| ----- | ---- | --- | ------ | ----------- |
| 01 | VBRC-REC2 | | varies | Long variable-length record |
| 05 | VB2-ACCT-ID | 9(11) | 11 | Account ID |
| 05 | VB2-ACCT-CURR-BAL | S9(10)V99 | 12 | Current balance |
| 05 | VB2-ACCT-CREDIT-LIMIT | S9(10)V99 | 12 | Credit limit |
| 05 | VB2-ACCT-REISSUE-YYYY | X(04) | 4 | Reissue year |

---

## File Summary

| File | Organisation | Record Len | Key Fields | Read By | Written By |
| ---- | ------------ | ---------- | ---------- | ------- | ---------- |
| ACCTDAT | Indexed (VSAM KSDS) | 300 | ACCT-ID 9(11) | CBACT01C, CBTRN01C, CBTRN02C, CBACT04C, COACTVWC, COACTUPC, COBIL00C, CBSTM03B | COACTUPC |
| CUSTDAT | Indexed (VSAM KSDS) | 500 | CUST-ID 9(09) | CBTRN01C, CBCUS01C, COACTVWC, COACTUPC, CBSTM03B | COACTUPC |
| CARDDAT | Indexed (VSAM KSDS) | 150 | CARD-NUM X(16) | CBACT02C, CBTRN01C, COCRDLIC, COCRDSLC, COCRDUPC, COACTUPC, COACTVWC | COCRDUPC |
| CARDAIX | Indexed (VSAM AIX) | 150 | CARD-ACCT-ID | COACTUPC, COACTVWC, COCRDSLC | None (AIX) |
| CXREF | Indexed (VSAM KSDS) | 50 | XREF-CARD-NUM X(16) | CBACT03C, CBTRN01C, CBTRN02C, CBACT04C, COTRN02C, COACTUPC, COACTVWC, CBSTM03B | None |
| CXACAIX | Indexed (VSAM AIX) | 50 | XREF-ACCT-ID | COTRN02C, COACTVWC | None (AIX) |
| TRANSACT | Indexed (VSAM KSDS) | 350 | TRAN-ID X(16) | CBTRN02C, CBACT04C, CBTRN03C, COTRN00C, COTRN01C, COTRN02C, COBIL00C, CORPT00C | CBTRN02C, COTRN02C, COBIL00C |
| TRNXFILE | Indexed (VSAM KSDS) | 350 | TRNX-CARD-NUM+TRNX-ID X(32) | CBSTM03A (via CBSTM03B) | External |
| DALYTRAN | Sequential | 350 | N/A | CBTRN01C, CBTRN02C | External |
| DALYREJS | Sequential | 430 (350+80) | N/A | None | CBTRN02C |
| TCATBAL | Indexed (VSAM KSDS) | 50 | Composite key (3 parts) | CBACT04C | CBTRN02C |
| DISCGRP | Indexed (VSAM KSDS) | 50 | Composite key (3 parts) | CBACT04C | None |
| TRANTYPE | Indexed (VSAM KSDS) | 60 | TRAN-TYPE X(02) | CBTRN03C | None |
| TRANCATG | Indexed (VSAM KSDS) | 60 | Composite key (2 parts) | CBTRN03C | None |
| USRSEC | Indexed (VSAM KSDS) | 80 | SEC-USR-ID X(08) | COSGN00C, COUSR00C, COUSR02C, COUSR03C | COUSR01C, COUSR02C, COUSR03C |
| EXPORTFILE | Sequential | 500 | N/A | CBIMPORT | CBEXPORT |
| STMTFILE | Sequential | 80 | N/A | None | CBSTM03A |
| HTMLFILE | Sequential | 100 | N/A | None | CBSTM03A |
| REPORT | Sequential | 133 | N/A | None | CBTRN03C |
| DATEPARM | Sequential | 80 | N/A | CBTRN03C | Via JCL from CORPT00C TDQ |
| OUTFILE | Sequential | ~107 | N/A | None | CBACT01C |
| ARRYFILE | Sequential | ~125 | N/A | None | CBACT01C |
| VBRCFILE | Sequential (V) | 10-80 | N/A | None | CBACT01C |
