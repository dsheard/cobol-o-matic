---
type: data
subtype: file-layouts
status: draft
confidence: high
last_pass: 2
---

# File Layouts

File descriptions (FD/SD) and their record layouts extracted from FILE SECTION and CICS file operations.

---

## Files

### CUSTOMER (VSAM KSDS)

| Property       | Value                                  |
| -------------- | -------------------------------------- |
| FD Name        | CUSTOMER-FILE                          |
| DD Name / Path | VSAM (SELECT ASSIGN TO VSAM)           |
| Organisation   | Indexed (KSDS)                         |
| Access Mode    | Random (BANKDATA batch); Dynamic (CICS)|
| Record Length  | ~265 bytes (derived from record layout)|
| Key Field      | CUSTOMER-KEY (SORTCODE 9(6) + NUMBER 9(10)) = 16 bytes |
| Read By        | INQCUST, DELCUS, UPDCUST, CRECUST (control record) |
| Written By     | BANKDATA (batch initialisation), CRECUST, UPDCUST |
| Deleted By     | DELCUS                                 |

**Record Layout:**

| Level | Name                        | PIC          | Offset | Length | Description                              |
| ----- | --------------------------- | ------------ | ------ | ------ | ---------------------------------------- |
| 03    | CUSTOMER-RECORD             |              | 0      | 265    | Customer master record                   |
| 05    | CUSTOMER-EYECATCHER         | X(4)         | 0      | 4      | Eye-catcher; value 'CUST'                |
| 05    | CUSTOMER-KEY                |              | 4      | 16     | Composite VSAM key (SORTCODE + NUMBER)   |
| 07    | CUSTOMER-SORTCODE           | 9(6) DISPLAY | 4      | 6      | Bank sort code                           |
| 07    | CUSTOMER-NUMBER             | 9(10) DISPLAY| 10     | 10     | Unique customer number                   |
| 05    | CUSTOMER-NAME               | X(60)        | 20     | 60     | Full customer name                       |
| 05    | CUSTOMER-ADDRESS            | X(160)       | 80     | 160    | Postal address                           |
| 05    | CUSTOMER-DATE-OF-BIRTH      | 9(8)         | 240    | 8      | Date of birth DDMMYYYY                   |
| 05    | CUSTOMER-CREDIT-SCORE       | 999          | 248    | 3      | Credit score 0-999                       |
| 05    | CUSTOMER-CS-REVIEW-DATE     | 9(8)         | 251    | 8      | Credit score review date DDMMYYYY        |

Notes:
- The CUSTOMER file also stores a control record (CUSTOMER-CONTROL-RECORD from CUSTCTRL.cpy) identified by eye-catcher 'CTRL'. The control record tracks NUMBER-OF-CUSTOMERS and LAST-CUSTOMER-NUMBER.
- CICS programs access this file via EXEC CICS READ/WRITE/REWRITE/DELETE FILE('CUSTOMER'), keyed by RIDFLD containing sort code + customer number.
- BANKDATA accesses this file via standard COBOL READ/WRITE using FD CUSTOMER-FILE.

---

### ABNDFILE (VSAM KSDS — Abend Log)

| Property       | Value                                         |
| -------------- | --------------------------------------------- |
| FD Name        | (CICS-managed; no FD in programs)             |
| DD Name / Path | ABNDFILE (CICS dataset name)                  |
| Organisation   | Indexed (KSDS)                                |
| Access Mode    | Random                                        |
| Record Length  | ~655 bytes (derived from ABNDINFO layout)     |
| Key Field      | ABND-VSAM-KEY (UTIME S9(15) COMP-3 + TASKNO 9(4)) |
| Read By        | (diagnostic use only)                         |
| Written By     | ABNDPROC                                      |

**Record Layout:**

| Level | Name               | PIC          | Offset | Length | Description                             |
| ----- | ------------------ | ------------ | ------ | ------ | --------------------------------------- |
| 03    | ABND-VSAM-KEY      |              | 0      | ~12    | Composite key                           |
| 05    | ABND-UTIME-KEY     | S9(15) COMP-3| 0      | 8      | Microsecond UTC timestamp               |
| 05    | ABND-TASKNO-KEY    | 9(4)         | 8      | 4      | CICS task number                        |
| 03    | ABND-APPLID        | X(8)         | 12     | 8      | CICS APPLID                             |
| 03    | ABND-TRANID        | X(4)         | 20     | 4      | CICS transaction ID at abend            |
| 03    | ABND-DATE          | X(10)        | 24     | 10     | Date of abend                           |
| 03    | ABND-TIME          | X(8)         | 34     | 8      | Time of abend                           |
| 03    | ABND-CODE          | X(4)         | 42     | 4      | Abend code (e.g. ASRA, AICA)            |
| 03    | ABND-PROGRAM       | X(8)         | 46     | 8      | Program that triggered the abend        |
| 03    | ABND-RESPCODE      | S9(8) DISPLAY| 54     | 9      | CICS RESP code (signed leading separate)|
| 03    | ABND-RESP2CODE     | S9(8) DISPLAY| 63     | 9      | CICS RESP2 code                         |
| 03    | ABND-SQLCODE       | S9(8) DISPLAY| 72     | 9      | DB2 SQLCODE at abend                    |
| 03    | ABND-FREEFORM      | X(600)       | 81     | 600    | Free-form diagnostic message text       |

---

## DB2 Table Declarations (DCLGEN Copybooks)

Although DB2 tables are not flat files, their schema is captured here from EXEC SQL DECLARE statements in the copybooks.

### ACCOUNT Table

Declared in: ACCDB2.cpy

| Column                     | DB2 Type       | Length  | Nullable | Description                        |
| -------------------------- | -------------- | ------- | -------- | ---------------------------------- |
| ACCOUNT_EYECATCHER         | CHAR(4)        | 4       | Yes      | Eye-catcher 'ACCT'                 |
| ACCOUNT_CUSTOMER_NUMBER    | CHAR(10)       | 10      | Yes      | Owning customer number             |
| ACCOUNT_SORTCODE           | CHAR(6)        | 6       | No       | Bank sort code (part of key)       |
| ACCOUNT_NUMBER             | CHAR(8)        | 8       | No       | Account number (part of key)       |
| ACCOUNT_TYPE               | CHAR(8)        | 8       | Yes      | Account type (e.g. CURRENT)        |
| ACCOUNT_INTEREST_RATE      | DECIMAL(4,2)   | 4.2     | Yes      | Annual interest rate               |
| ACCOUNT_OPENED             | DATE           | 10      | Yes      | Date account was opened            |
| ACCOUNT_OVERDRAFT_LIMIT    | INTEGER        | 4       | Yes      | Overdraft limit                    |
| ACCOUNT_LAST_STATEMENT     | DATE           | 10      | Yes      | Last statement date                |
| ACCOUNT_NEXT_STATEMENT     | DATE           | 10      | Yes      | Next scheduled statement date      |
| ACCOUNT_AVAILABLE_BALANCE  | DECIMAL(10,2)  | 10.2    | Yes      | Available balance                  |
| ACCOUNT_ACTUAL_BALANCE     | DECIMAL(10,2)  | 10.2    | Yes      | Actual balance                     |

---

### PROCTRAN Table

Declared in: PROCDB2.cpy

| Column                  | DB2 Type       | Length | Nullable | Description                        |
| ----------------------- | -------------- | ------ | -------- | ---------------------------------- |
| PROCTRAN_EYECATCHER     | CHAR(4)        | 4      | Yes      | Eye-catcher 'PRTR'                 |
| PROCTRAN_SORTCODE       | CHAR(6)        | 6      | No       | Sort code (part of key)            |
| PROCTRAN_NUMBER         | CHAR(8)        | 8      | No       | Account number (part of key)       |
| PROCTRAN_DATE           | CHAR(8)        | 8      | Yes      | Transaction date YYYYMMDD          |
| PROCTRAN_TIME           | CHAR(6)        | 6      | Yes      | Transaction time HHMMSS            |
| PROCTRAN_REF            | CHAR(12)       | 12     | Yes      | Transaction reference              |
| PROCTRAN_TYPE           | CHAR(3)        | 3      | Yes      | Transaction type code              |
| PROCTRAN_DESC           | CHAR(40)       | 40     | Yes      | Transaction description            |
| PROCTRAN_AMOUNT         | DECIMAL(12,2)  | 12.2   | Yes      | Transaction amount                 |

---

### CONTROL Table (STTESTER schema)

Declared in: CONTDB2.cpy

| Column             | DB2 Type   | Length | Nullable | Description                             |
| ------------------ | ---------- | ------ | -------- | --------------------------------------- |
| CONTROL_NAME       | CHAR(32)   | 32     | No       | Control record name (key)               |
| CONTROL_VALUE_NUM  | INTEGER    | 4      | Yes      | Numeric value (e.g. last account number)|
| CONTROL_VALUE_STR  | CHAR(40)   | 40     | Yes      | String value (e.g. sort code)           |

Note: The schema owner is STTESTER (EXEC SQL DECLARE STTESTER.CONTROL TABLE). The CONTROL table holds two rows per sort code at runtime: `<sortcode>-ACCOUNT-LAST` (last account number allocated) and `<sortcode>-ACCOUNT-COUNT` (total accounts). CREACC reads and updates `<sortcode>-ACCOUNT-LAST` as a fallback when the CICS Named Counter Service is unavailable. BANKDATA initialises both rows.

---

## File Summary

| File        | Organisation | Record Len | Read By                              | Written By                        | Deleted By |
| ----------- | ------------ | ---------- | ------------------------------------ | --------------------------------- | ---------- |
| CUSTOMER    | VSAM KSDS    | ~265 bytes | INQCUST, DELCUS, UPDCUST, CRECUST    | BANKDATA, CRECUST, UPDCUST        | DELCUS     |
| ABNDFILE    | VSAM KSDS    | ~655 bytes | (diagnostic)                         | ABNDPROC                          | --         |
| ACCOUNT     | DB2 table    | N/A        | INQACC, INQACCCU, DELACC, DBCRFUN, XFRFUN, UPDACC | BANKDATA, CREACC | DELACC, BANKDATA |
| PROCTRAN    | DB2 table    | N/A        | (query/reporting)                    | CREACC, CRECUST, DELACC, DELCUS, DBCRFUN, XFRFUN | -- |
| CONTROL     | DB2 table    | N/A        | CREACC                               | BANKDATA (x2 rows)                | BANKDATA   |
