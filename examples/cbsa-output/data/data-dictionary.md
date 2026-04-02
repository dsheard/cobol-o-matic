---
type: data
subtype: data-dictionary
status: draft
confidence: high
last_pass: 2
---

# Data Dictionary

All data items extracted from WORKING-STORAGE, LOCAL-STORAGE, LINKAGE SECTION, and copybooks.

---

## Key Data Structures

### ACCOUNT-DATA

Defined in: ACCOUNT.cpy

| Level | Name                        | PIC          | Usage   | Description                              |
| ----- | --------------------------- | ------------ | ------- | ---------------------------------------- |
| 03    | ACCOUNT-DATA                |              |         | Account record group (eye-catcher 'ACCT') |
| 05    | ACCOUNT-EYE-CATCHER         | X(4)         | DISPLAY | Eye-catcher; 88 value 'ACCT'             |
| 05    | ACCOUNT-CUST-NO             | 9(10)        | DISPLAY | Owning customer number                   |
| 05    | ACCOUNT-KEY                 |              |         | Composite VSAM/DB2 key                   |
| 07    | ACCOUNT-SORT-CODE           | 9(6)         | DISPLAY | Bank sort code                           |
| 07    | ACCOUNT-NUMBER              | 9(8)         | DISPLAY | Account number within sort code          |
| 05    | ACCOUNT-TYPE                | X(8)         | DISPLAY | Account type (e.g. CURRENT, SAVINGS)     |
| 05    | ACCOUNT-INTEREST-RATE       | 9(4)V99      | DISPLAY | Annual interest rate (4.2 decimal)       |
| 05    | ACCOUNT-OPENED              | 9(8)         | DISPLAY | Date opened DDMMYYYY                     |
| 05    | ACCOUNT-OPENED-GROUP        |              |         | REDEFINES ACCOUNT-OPENED                 |
| 07    | ACCOUNT-OPENED-DAY          | 99           | DISPLAY | Day portion of opened date               |
| 07    | ACCOUNT-OPENED-MONTH        | 99           | DISPLAY | Month portion of opened date             |
| 07    | ACCOUNT-OPENED-YEAR         | 9999         | DISPLAY | Year portion of opened date              |
| 05    | ACCOUNT-OVERDRAFT-LIMIT     | 9(8)         | DISPLAY | Overdraft limit in minor currency units  |
| 05    | ACCOUNT-LAST-STMT-DATE      | 9(8)         | DISPLAY | Last statement date DDMMYYYY             |
| 05    | ACCOUNT-LAST-STMT-GROUP     |              |         | REDEFINES ACCOUNT-LAST-STMT-DATE         |
| 07    | ACCOUNT-LAST-STMT-DAY       | 99           | DISPLAY | Day portion of last statement            |
| 07    | ACCOUNT-LAST-STMT-MONTH     | 99           | DISPLAY | Month portion of last statement          |
| 07    | ACCOUNT-LAST-STMT-YEAR      | 9999         | DISPLAY | Year portion of last statement           |
| 05    | ACCOUNT-NEXT-STMT-DATE      | 9(8)         | DISPLAY | Next statement date DDMMYYYY             |
| 05    | ACCOUNT-NEXT-STMT-GROUP     |              |         | REDEFINES ACCOUNT-NEXT-STMT-DATE         |
| 07    | ACCOUNT-NEXT-STMT-DAY       | 99           | DISPLAY | Day portion of next statement            |
| 07    | ACCOUNT-NEXT-STMT-MONTH     | 99           | DISPLAY | Month portion of next statement          |
| 07    | ACCOUNT-NEXT-STMT-YEAR      | 9999         | DISPLAY | Year portion of next statement           |
| 05    | ACCOUNT-AVAILABLE-BALANCE   | S9(10)V99    | DISPLAY | Available balance (signed, 10.2 decimal) |
| 05    | ACCOUNT-ACTUAL-BALANCE      | S9(10)V99    | DISPLAY | Actual balance (signed, 10.2 decimal)    |

---

### CUSTOMER-RECORD

Defined in: CUSTOMER.cpy

| Level | Name                        | PIC          | Usage   | Description                              |
| ----- | --------------------------- | ------------ | ------- | ---------------------------------------- |
| 03    | CUSTOMER-RECORD             |              |         | Customer master record (eye-catcher 'CUST') |
| 05    | CUSTOMER-EYECATCHER         | X(4)         | DISPLAY | Eye-catcher; 88 value 'CUST'             |
| 05    | CUSTOMER-KEY                |              |         | Composite VSAM key                       |
| 07    | CUSTOMER-SORTCODE           | 9(6)         | DISPLAY | Bank sort code                           |
| 07    | CUSTOMER-NUMBER             | 9(10)        | DISPLAY | Customer number (unique within sortcode) |
| 05    | CUSTOMER-NAME               | X(60)        | DISPLAY | Full customer name                       |
| 05    | CUSTOMER-ADDRESS            | X(160)       | DISPLAY | Full postal address                      |
| 05    | CUSTOMER-DATE-OF-BIRTH      | 9(8)         | DISPLAY | Date of birth DDMMYYYY                   |
| 05    | CUSTOMER-DOB-GROUP          |              |         | REDEFINES CUSTOMER-DATE-OF-BIRTH         |
| 07    | CUSTOMER-BIRTH-DAY          | 99           | DISPLAY | Day portion of date of birth             |
| 07    | CUSTOMER-BIRTH-MONTH        | 99           | DISPLAY | Month portion of date of birth           |
| 07    | CUSTOMER-BIRTH-YEAR         | 9999         | DISPLAY | Year portion of date of birth            |
| 05    | CUSTOMER-CREDIT-SCORE       | 999          | DISPLAY | Credit score (0-999)                     |
| 05    | CUSTOMER-CS-REVIEW-DATE     | 9(8)         | DISPLAY | Credit score review date DDMMYYYY        |
| 05    | CUSTOMER-CS-GROUP           |              |         | REDEFINES CUSTOMER-CS-REVIEW-DATE        |
| 07    | CUSTOMER-CS-REVIEW-DAY      | 99           | DISPLAY | Day portion of review date               |
| 07    | CUSTOMER-CS-REVIEW-MONTH    | 99           | DISPLAY | Month portion of review date             |
| 07    | CUSTOMER-CS-REVIEW-YEAR     | 9999         | DISPLAY | Year portion of review date              |

---

### PROC-TRAN-DATA

Defined in: PROCTRAN.cpy

| Level | Name                           | PIC        | Usage   | Description                                |
| ----- | ------------------------------ | ---------- | ------- | ------------------------------------------ |
| 03    | PROC-TRAN-DATA                 |            |         | Processed transaction record (eye-catcher 'PRTR') |
| 05    | PROC-TRAN-EYE-CATCHER          | X(4)       | DISPLAY | Eye-catcher; 88 'PRTR'; REDEFINES with logical delete flag |
| 05    | PROC-TRAN-LOGICAL-DELETE-AREA  |            |         | REDEFINES PROC-TRAN-EYE-CATCHER            |
| 07    | PROC-TRAN-LOGICAL-DELETE-FLAG  | X          | DISPLAY | X'FF' = logically deleted                 |
| 05    | PROC-TRAN-ID                   |            |         | Transaction key                            |
| 07    | PROC-TRAN-SORT-CODE            | 9(6)       | DISPLAY | Sort code                                  |
| 07    | PROC-TRAN-NUMBER               | 9(8)       | DISPLAY | Account number                             |
| 05    | PROC-TRAN-DATE                 | 9(8)       | DISPLAY | Transaction date YYYYMMDD                  |
| 05    | PROC-TRAN-DATE-GRP             |            |         | REDEFINES PROC-TRAN-DATE                   |
| 07    | PROC-TRAN-DATE-GRP-YYYY        | 9999       | DISPLAY | Year                                       |
| 07    | PROC-TRAN-DATE-GRP-MM          | 99         | DISPLAY | Month                                      |
| 07    | PROC-TRAN-DATE-GRP-DD          | 99         | DISPLAY | Day                                        |
| 05    | PROC-TRAN-TIME                 | 9(6)       | DISPLAY | Transaction time HHMMSS                    |
| 05    | PROC-TRAN-TIME-GRP             |            |         | REDEFINES PROC-TRAN-TIME                   |
| 07    | PROC-TRAN-TIME-GRP-HH          | 99         | DISPLAY | Hours                                      |
| 07    | PROC-TRAN-TIME-GRP-MM          | 99         | DISPLAY | Minutes                                    |
| 07    | PROC-TRAN-TIME-GRP-SS          | 99         | DISPLAY | Seconds                                    |
| 05    | PROC-TRAN-REF                  | 9(12)      | DISPLAY | Transaction reference number               |
| 05    | PROC-TRAN-TYPE                 | X(3)       | DISPLAY | Transaction type code (CHA/CHF/CHI/CHO/CRE/DEB/ICA/ICC/IDA/IDC/OCA/OCC/ODA/ODC/OCS/PCR/PDR/TFR) |
| 05    | PROC-TRAN-DESC                 | X(40)      | DISPLAY | Transaction description                    |
| 05    | PROC-TRAN-DESC-XFR             |            |         | REDEFINES PROC-TRAN-DESC for transfers      |
| 07    | PROC-TRAN-DESC-XFR-HEADER      | X(26)      | DISPLAY | Transfer description header                |
| 07    | PROC-TRAN-DESC-XFR-SORTCODE    | 9(6)       | DISPLAY | Target sort code for transfer              |
| 07    | PROC-TRAN-DESC-XFR-ACCOUNT     | 9(8)       | DISPLAY | Target account for transfer                |
| 05    | PROC-TRAN-DESC-DELACC          |            |         | REDEFINES PROC-TRAN-DESC for delete account |
| 05    | PROC-TRAN-DESC-CREACC          |            |         | REDEFINES PROC-TRAN-DESC for create account |
| 05    | PROC-TRAN-DESC-DELCUS          |            |         | REDEFINES PROC-TRAN-DESC for delete customer |
| 05    | PROC-TRAN-DESC-CRECUS          |            |         | REDEFINES PROC-TRAN-DESC for create customer |
| 05    | PROC-TRAN-AMOUNT               | S9(10)V99  | DISPLAY | Transaction amount (signed, 10.2 decimal)  |

---

### ACCOUNT-CONTROL-RECORD

Defined in: ACCTCTRL.cpy

| Level | Name                           | PIC   | Usage   | Description                            |
| ----- | ------------------------------ | ----- | ------- | -------------------------------------- |
| 03    | ACCOUNT-CONTROL-RECORD         |       |         | Account counter/control record (eye-catcher 'CTRL') |
| 05    | ACCOUNT-CONTROL-EYE-CATCHER    | X(4)  | DISPLAY | Eye-catcher                            |
| 05    | ACCOUNT-CONTROL-KEY            |       |         | Key for control record                 |
| 07    | ACCOUNT-CONTROL-SORT-CODE      | 9(6)  | DISPLAY | Sort code                              |
| 07    | ACCOUNT-CONTROL-NUMBER         | 9(8)  | DISPLAY | Control record number                  |
| 05    | NUMBER-OF-ACCOUNTS             | 9(8)  | DISPLAY | Total account count                    |
| 05    | LAST-ACCOUNT-NUMBER            | 9(8)  | DISPLAY | Last assigned account number           |
| 05    | ACCOUNT-CONTROL-SUCCESS-FLAG   | X     | DISPLAY | 'Y' = success                          |
| 05    | ACCOUNT-CONTROL-FAIL-CODE      | X     | DISPLAY | Failure code                           |

---

### CUSTOMER-CONTROL-RECORD

Defined in: CUSTCTRL.cpy

| Level | Name                            | PIC    | Usage   | Description                             |
| ----- | ------------------------------- | ------ | ------- | --------------------------------------- |
| 03    | CUSTOMER-CONTROL-RECORD         |        |         | Customer counter/control record (eye-catcher 'CTRL') |
| 05    | CUSTOMER-CONTROL-EYECATCHER     | X(4)   | DISPLAY | Eye-catcher                             |
| 05    | CUSTOMER-CONTROL-KEY            |        |         | Key for control record                  |
| 07    | CUSTOMER-CONTROL-SORTCODE       | 9(6)   | DISPLAY | Sort code                               |
| 07    | CUSTOMER-CONTROL-NUMBER         | 9(10)  | DISPLAY | Control record number                   |
| 05    | NUMBER-OF-CUSTOMERS             | 9(10)  | DISPLAY | Total customer count                    |
| 05    | LAST-CUSTOMER-NUMBER            | 9(10)  | DISPLAY | Last assigned customer number           |
| 05    | CUSTOMER-CONTROL-SUCCESS-FLAG   | X      | DISPLAY | 'Y' = success                           |
| 05    | CUSTOMER-CONTROL-FAIL-CODE      | X      | DISPLAY | Failure code                            |

---

### ABND-INFO

Defined in: ABNDINFO.cpy

| Level | Name               | PIC          | Usage        | Description                             |
| ----- | ------------------ | ------------ | ------------ | --------------------------------------- |
| 03    | ABND-VSAM-KEY      |              |              | Composite key for abend VSAM file       |
| 05    | ABND-UTIME-KEY     | S9(15)       | COMP-3       | Microsecond timestamp                   |
| 05    | ABND-TASKNO-KEY    | 9(4)         | DISPLAY      | CICS task number                        |
| 03    | ABND-APPLID        | X(8)         | DISPLAY      | CICS APPLID                             |
| 03    | ABND-TRANID        | X(4)         | DISPLAY      | CICS transaction ID                     |
| 03    | ABND-DATE          | X(10)        | DISPLAY      | Date of abend                           |
| 03    | ABND-TIME          | X(8)         | DISPLAY      | Time of abend                           |
| 03    | ABND-CODE          | X(4)         | DISPLAY      | Abend code                              |
| 03    | ABND-PROGRAM       | X(8)         | DISPLAY      | Program that abended                    |
| 03    | ABND-RESPCODE      | S9(8)        | DISPLAY SIGN | CICS RESP code                          |
| 03    | ABND-RESP2CODE     | S9(8)        | DISPLAY SIGN | CICS RESP2 code                         |
| 03    | ABND-SQLCODE       | S9(8)        | DISPLAY SIGN | DB2 SQLCODE at time of abend            |
| 03    | ABND-FREEFORM      | X(600)       | DISPLAY      | Free-form diagnostic text               |

---

### DELACC-COMMAREA

Defined in: DELACC.cpy

| Level | Name                  | PIC        | Usage   | Description                            |
| ----- | --------------------- | ---------- | ------- | -------------------------------------- |
| 01    | DELACC-COMMAREA       |            |         | COMMAREA for DELACC program            |
| 03    | DELACC-EYE            | X(4)       | DISPLAY | Eye-catcher                            |
| 03    | DELACC-CUSTNO         | X(10)      | DISPLAY | Customer number                        |
| 03    | DELACC-SCODE          | X(6)       | DISPLAY | Sort code                              |
| 03    | DELACC-ACCNO          | 9(8)       | DISPLAY | Account number                         |
| 03    | DELACC-ACC-TYPE       | X(8)       | DISPLAY | Account type                           |
| 03    | DELACC-INT-RATE       | 9(4)V99    | DISPLAY | Interest rate                          |
| 03    | DELACC-OPENED         | 9(8)       | DISPLAY | Date opened                            |
| 03    | DELACC-OVERDRAFT      | 9(8)       | DISPLAY | Overdraft limit                        |
| 03    | DELACC-LAST-STMT-DT   | 9(8)       | DISPLAY | Last statement date                    |
| 03    | DELACC-NEXT-STMT-DT   | 9(8)       | DISPLAY | Next statement date                    |
| 03    | DELACC-AVAIL-BAL      | S9(10)V99  | DISPLAY | Available balance                      |
| 03    | DELACC-ACTUAL-BAL     | S9(10)V99  | DISPLAY | Actual balance                         |
| 03    | DELACC-SUCCESS        | X          | DISPLAY | Account inquiry success flag           |
| 03    | DELACC-FAIL-CD        | X          | DISPLAY | Account inquiry failure code           |
| 03    | DELACC-DEL-SUCCESS    | X          | DISPLAY | Delete operation success flag          |
| 03    | DELACC-DEL-FAIL-CD    | X          | DISPLAY | Delete operation failure code          |
| 03    | DELACC-DEL-APPLID     | X(8)       | DISPLAY | APPLID for delete                      |
| 03    | DELACC-DEL-PCB1       | POINTER    |         | IMS PCB pointer 1                      |
| 03    | DELACC-DEL-PCB2       | POINTER    |         | IMS PCB pointer 2                      |
| 03    | DELACC-DEL-PCB3       | POINTER    |         | IMS PCB pointer 3                      |

---

### INQACC-COMMAREA

Defined in: INQACC.cpy / INQACCZ.cpy

| Level | Name                  | PIC        | Usage   | Description                            |
| ----- | --------------------- | ---------- | ------- | -------------------------------------- |
| 01    | INQACC-COMMAREA       |            |         | COMMAREA for INQACC program            |
| 03    | INQACC-EYE            | X(4)       | DISPLAY | Eye-catcher                            |
| 03    | INQACC-CUSTNO         | 9(10)      | DISPLAY | Customer number                        |
| 03    | INQACC-SCODE          | 9(6)       | DISPLAY | Sort code                              |
| 03    | INQACC-ACCNO          | 9(8)       | DISPLAY | Account number                         |
| 03    | INQACC-ACC-TYPE       | X(8)       | DISPLAY | Account type                           |
| 03    | INQACC-INT-RATE       | 9(4)V99    | DISPLAY | Interest rate                          |
| 03    | INQACC-OPENED         | 9(8)       | DISPLAY | Date opened                            |
| 03    | INQACC-OVERDRAFT      | 9(8)       | DISPLAY | Overdraft limit                        |
| 03    | INQACC-LAST-STMT-DT   | 9(8)       | DISPLAY | Last statement date                    |
| 03    | INQACC-NEXT-STMT-DT   | 9(8)       | DISPLAY | Next statement date                    |
| 03    | INQACC-AVAIL-BAL      | S9(10)V99  | DISPLAY | Available balance                      |
| 03    | INQACC-ACTUAL-BAL     | S9(10)V99  | DISPLAY | Actual balance                         |
| 03    | INQACC-SUCCESS        | X          | DISPLAY | Inquiry success flag                   |
| 03    | INQACC-PCB1-POINTER   | POINTER/X(4) |       | IMS PCB pointer (POINTER in .cpy, X(4) in .z variant) |

---

### INQACCCU COMMAREA (Accounts by Customer)

Defined in: INQACCCU.cpy / INQACCCZ.cpy

| Level | Name                  | PIC        | Usage    | Description                                         |
| ----- | --------------------- | ---------- | -------- | --------------------------------------------------- |
|       | NUMBER-OF-ACCOUNTS    | S9(8)      | BINARY   | Number of accounts in OCCURS table (1-20)           |
|       | CUSTOMER-NUMBER       | 9(10)      | DISPLAY  | Customer number to query                            |
|       | COMM-SUCCESS          | X          | DISPLAY  | Success flag                                        |
|       | COMM-FAIL-CODE        | X          | DISPLAY  | Failure code                                        |
|       | CUSTOMER-FOUND        | X          | DISPLAY  | Customer found indicator                            |
|       | COMM-PCB-POINTER      | POINTER/X(4) |        | IMS PCB pointer (POINTER in .cpy, X(4) in z-variant) |
|       | ACCOUNT-DETAILS       |            |          | OCCURS 1 TO 20 DEPENDING ON NUMBER-OF-ACCOUNTS      |
| 05    | COMM-EYE              | X(4)       | DISPLAY  | Eye-catcher per account                             |
| 05    | COMM-CUSTNO           | X(10)      | DISPLAY  | Customer number                                     |
| 05    | COMM-SCODE            | X(6)       | DISPLAY  | Sort code                                           |
| 05    | COMM-ACCNO            | 9(8)       | DISPLAY  | Account number                                      |
| 05    | COMM-ACC-TYPE         | X(8)       | DISPLAY  | Account type                                        |
| 05    | COMM-INT-RATE         | 9(4)V99    | DISPLAY  | Interest rate                                       |
| 05    | COMM-OPENED           | 9(8)       | DISPLAY  | Date opened DDMMYYYY                                |
| 05    | COMM-OPENED-GROUP     |            |          | REDEFINES COMM-OPENED                               |
| 07    | COMM-OPENED-DAY       | 99         | DISPLAY  | Day portion of opened date                          |
| 07    | COMM-OPENED-MONTH     | 99         | DISPLAY  | Month portion of opened date                        |
| 07    | COMM-OPENED-YEAR      | 9999       | DISPLAY  | Year portion of opened date                         |
| 05    | COMM-OVERDRAFT        | 9(8)       | DISPLAY  | Overdraft limit                                     |
| 05    | COMM-LAST-STMT-DT     | 9(8)       | DISPLAY  | Last statement date DDMMYYYY                        |
| 05    | COMM-LAST-STMT-GROUP  |            |          | REDEFINES COMM-LAST-STMT-DT                         |
| 07    | COMM-LAST-STMT-DAY    | 99         | DISPLAY  | Day portion of last statement                       |
| 07    | COMM-LAST-STMT-MONTH  | 99         | DISPLAY  | Month portion of last statement                     |
| 07    | COMM-LAST-STMT-YEAR   | 9999       | DISPLAY  | Year portion of last statement                      |
| 05    | COMM-NEXT-STMT-DT     | 9(8)       | DISPLAY  | Next statement date DDMMYYYY                        |
| 05    | COMM-NEXT-STMT-GROUP  |            |          | REDEFINES COMM-NEXT-STMT-DT                         |
| 07    | COMM-NEXT-STMT-DAY    | 99         | DISPLAY  | Day portion of next statement                       |
| 07    | COMM-NEXT-STMT-MONTH  | 99         | DISPLAY  | Month portion of next statement                     |
| 07    | COMM-NEXT-STMT-YEAR   | 9999       | DISPLAY  | Year portion of next statement                      |
| 05    | COMM-AVAIL-BAL        | S9(10)V99  | DISPLAY  | Available balance                                   |
| 05    | COMM-ACTUAL-BAL       | S9(10)V99  | DISPLAY  | Actual balance                                      |

---

### INQCUST-COMMAREA

Defined in: INQCUST.cpy / INQCUSTZ.cpy

| Level | Name                   | PIC    | Usage   | Description                     |
| ----- | ---------------------- | ------ | ------- | ------------------------------- |
| 03    | INQCUST-EYE            | X(4)   | DISPLAY | Eye-catcher                     |
| 03    | INQCUST-SCODE          | X(6)   | DISPLAY | Sort code                       |
| 03    | INQCUST-CUSTNO         | 9(10)  | DISPLAY | Customer number                 |
| 03    | INQCUST-NAME           | X(60)  | DISPLAY | Customer name                   |
| 03    | INQCUST-ADDR           | X(160) | DISPLAY | Customer address                |
| 03    | INQCUST-DOB            |        |         | Date of birth (DD/MM/YYYY)      |
| 05    | INQCUST-DOB-DD         | 99     | DISPLAY | Day                             |
| 05    | INQCUST-DOB-MM         | 99     | DISPLAY | Month                           |
| 05    | INQCUST-DOB-YYYY       | 9999   | DISPLAY | Year                            |
| 03    | INQCUST-CREDIT-SCORE   | 999    | DISPLAY | Credit score                    |
| 03    | INQCUST-CS-REVIEW-DT   |        |         | Credit score review date        |
| 05    | INQCUST-CS-REVIEW-DD   | 99     | DISPLAY | Day                             |
| 05    | INQCUST-CS-REVIEW-MM   | 99     | DISPLAY | Month                           |
| 05    | INQCUST-CS-REVIEW-YYYY | 9999   | DISPLAY | Year                            |
| 03    | INQCUST-INQ-SUCCESS    | X      | DISPLAY | Inquiry success flag            |
| 03    | INQCUST-INQ-FAIL-CD    | X      | DISPLAY | Inquiry failure code            |
| 03    | INQCUST-PCB-POINTER    | POINTER/X(4) |   | IMS PCB pointer                 |

---

### CREACC COMMAREA

Defined in: CREACC.cpy

| Level | Name                  | PIC        | Usage   | Description                            |
| ----- | --------------------- | ---------- | ------- | -------------------------------------- |
| 03    | COMM-EYECATCHER       | X(4)       | DISPLAY | Eye-catcher                            |
| 03    | COMM-CUSTNO           | 9(10)      | DISPLAY | Customer number                        |
| 03    | COMM-KEY              |            |         | Account key                            |
| 05    | COMM-SORTCODE         | 9(6)       | DISPLAY | Sort code                              |
| 05    | COMM-NUMBER           | 9(8)       | DISPLAY | Account number                         |
| 03    | COMM-ACC-TYPE         | X(8)       | DISPLAY | Account type                           |
| 03    | COMM-INT-RT           | 9(4)V99    | DISPLAY | Interest rate                          |
| 03    | COMM-OPENED           | 9(8)       | DISPLAY | Opened date                            |
| 03    | COMM-OVERDR-LIM       | 9(8)       | DISPLAY | Overdraft limit                        |
| 03    | COMM-LAST-STMT-DT     | 9(8)       | DISPLAY | Last statement date                    |
| 03    | COMM-NEXT-STMT-DT     | 9(8)       | DISPLAY | Next statement date                    |
| 03    | COMM-AVAIL-BAL        | S9(10)V99  | DISPLAY | Available balance                      |
| 03    | COMM-ACT-BAL          | S9(10)V99  | DISPLAY | Actual balance                         |
| 03    | COMM-SUCCESS          | X          | DISPLAY | Create success flag                    |
| 03    | COMM-FAIL-CODE        | X          | DISPLAY | Create failure code                    |

---

### CRECUST COMMAREA

Defined in: CRECUST.cpy

| Level | Name                        | PIC    | Usage   | Description                        |
| ----- | --------------------------- | ------ | ------- | ---------------------------------- |
| 03    | COMM-EYECATCHER             | X(4)   | DISPLAY | Eye-catcher                        |
| 03    | COMM-KEY                    |        |         | Customer key                       |
| 05    | COMM-SORTCODE               | 9(6)   | DISPLAY | Sort code                          |
| 05    | COMM-NUMBER                 | 9(10)  | DISPLAY | Customer number                    |
| 03    | COMM-NAME                   | X(60)  | DISPLAY | Customer name                      |
| 03    | COMM-ADDRESS                | X(160) | DISPLAY | Customer address                   |
| 03    | COMM-DATE-OF-BIRTH          | 9(8)   | DISPLAY | Date of birth                      |
| 03    | COMM-CREDIT-SCORE           | 999    | DISPLAY | Credit score                       |
| 03    | COMM-CS-REVIEW-DATE         | 9(8)   | DISPLAY | Credit score review date           |
| 03    | COMM-SUCCESS                | X      | DISPLAY | Create success flag                |
| 03    | COMM-FAIL-CODE              | X      | DISPLAY | Create failure code                |

---

### DELCUS COMMAREA

Defined in: DELCUS.cpy

| Level | Name                  | PIC    | Usage   | Description                         |
| ----- | --------------------- | ------ | ------- | ----------------------------------- |
| 03    | COMM-EYE              | X(4)   | DISPLAY | Eye-catcher                         |
| 03    | COMM-SCODE            | X(6)   | DISPLAY | Sort code                           |
| 03    | COMM-CUSTNO           | X(10)  | DISPLAY | Customer number                     |
| 03    | COMM-NAME             | X(60)  | DISPLAY | Customer name                       |
| 03    | COMM-ADDR             | X(160) | DISPLAY | Customer address                    |
| 03    | COMM-DOB              | 9(8)   | DISPLAY | Date of birth                       |
| 03    | COMM-CREDIT-SCORE     | 9(3)   | DISPLAY | Credit score                        |
| 03    | COMM-CS-REVIEW-DATE   | 9(8)   | DISPLAY | Credit score review date            |
| 03    | COMM-DEL-SUCCESS      | X      | DISPLAY | Delete success flag                 |
| 03    | COMM-DEL-FAIL-CD      | X      | DISPLAY | Delete failure code                 |

---

### UPDACC COMMAREA

Defined in: UPDACC.cpy

| Level | Name                  | PIC        | Usage   | Description                            |
| ----- | --------------------- | ---------- | ------- | -------------------------------------- |
| 03    | COMM-EYE              | X(4)       | DISPLAY | Eye-catcher                            |
| 03    | COMM-CUSTNO           | X(10)      | DISPLAY | Customer number                        |
| 03    | COMM-SCODE            | X(6)       | DISPLAY | Sort code                              |
| 03    | COMM-ACCNO            | 9(8)       | DISPLAY | Account number                         |
| 03    | COMM-ACC-TYPE         | X(8)       | DISPLAY | Account type                           |
| 03    | COMM-INT-RATE         | 9(4)V99    | DISPLAY | Interest rate                          |
| 03    | COMM-OPENED           | 9(8)       | DISPLAY | Opened date                            |
| 03    | COMM-OVERDRAFT        | 9(8)       | DISPLAY | Overdraft limit                        |
| 03    | COMM-LAST-STMT-DT     | 9(8)       | DISPLAY | Last statement date                    |
| 03    | COMM-NEXT-STMT-DT     | 9(8)       | DISPLAY | Next statement date                    |
| 03    | COMM-AVAIL-BAL        | S9(10)V99  | DISPLAY | Available balance                      |
| 03    | COMM-ACTUAL-BAL       | S9(10)V99  | DISPLAY | Actual balance                         |
| 03    | COMM-SUCCESS          | X          | DISPLAY | Update success flag                    |

---

### UPDCUST COMMAREA

Defined in: UPDCUST.cpy

| Level | Name                  | PIC    | Usage   | Description                         |
| ----- | --------------------- | ------ | ------- | ----------------------------------- |
| 03    | COMM-EYE              | X(4)   | DISPLAY | Eye-catcher                         |
| 03    | COMM-SCODE            | X(6)   | DISPLAY | Sort code                           |
| 03    | COMM-CUSTNO           | X(10)  | DISPLAY | Customer number                     |
| 03    | COMM-NAME             | X(60)  | DISPLAY | Customer name                       |
| 03    | COMM-ADDR             | X(160) | DISPLAY | Customer address                    |
| 03    | COMM-DOB              | 9(8)   | DISPLAY | Date of birth                       |
| 03    | COMM-CREDIT-SCORE     | 9(3)   | DISPLAY | Credit score                        |
| 03    | COMM-CS-REVIEW-DATE   | 9(8)   | DISPLAY | Credit score review date            |
| 03    | COMM-UPD-SUCCESS      | X      | DISPLAY | Update success flag                 |
| 03    | COMM-UPD-FAIL-CD      | X      | DISPLAY | Update failure code                 |

---

### XFRFUN COMMAREA

Defined in: XFRFUN.cpy

| Level | Name           | PIC        | Usage   | Description                              |
| ----- | -------------- | ---------- | ------- | ---------------------------------------- |
| 03    | COMM-FACCNO    | 9(8)       | DISPLAY | From-account number                      |
| 03    | COMM-FSCODE    | 9(6)       | DISPLAY | From-account sort code                   |
| 03    | COMM-TACCNO    | 9(8)       | DISPLAY | To-account number                        |
| 03    | COMM-TSCODE    | 9(6)       | DISPLAY | To-account sort code                     |
| 03    | COMM-AMT       | S9(10)V99  | DISPLAY | Transfer amount                          |
| 03    | COMM-FAVBAL    | S9(10)V99  | DISPLAY | From-account available balance after     |
| 03    | COMM-FACTBAL   | S9(10)V99  | DISPLAY | From-account actual balance after        |
| 03    | COMM-TAVBAL    | S9(10)V99  | DISPLAY | To-account available balance after       |
| 03    | COMM-TACTBAL   | S9(10)V99  | DISPLAY | To-account actual balance after          |
| 03    | COMM-FAIL-CODE | X          | DISPLAY | Failure code                             |
| 03    | COMM-SUCCESS   | X          | DISPLAY | Success flag                             |

---

### PAYDBCR COMMAREA (Debit/Credit)

Defined in: PAYDBCR.cpy

| Level | Name                | PIC        | Usage  | Description                                  |
| ----- | ------------------- | ---------- | ------ | -------------------------------------------- |
| 03    | COMM-ACCNO          | X(8)       | DISPLAY| Account number to debit/credit               |
| 03    | COMM-AMT            | S9(10)V99  | DISPLAY| Amount to debit or credit                    |
| 03    | COMM-SORTC          | 9(6)       | DISPLAY| Sort code                                    |
| 03    | COMM-AV-BAL         | S9(10)V99  | DISPLAY| Available balance after operation            |
| 03    | COMM-ACT-BAL        | S9(10)V99  | DISPLAY| Actual balance after operation               |
| 03    | COMM-ORIGIN         |            |        | Originating system identification            |
| 05    | COMM-APPLID         | X(8)       | DISPLAY| CICS APPLID                                  |
| 05    | COMM-USERID         | X(8)       | DISPLAY| User ID                                      |
| 05    | COMM-FACILITY-NAME  | X(8)       | DISPLAY| CICS facility name                           |
| 05    | COMM-NETWRK-ID      | X(8)       | DISPLAY| Network ID                                   |
| 05    | COMM-FACILTYPE      | S9(8)      | COMP   | Facility type                                |
| 03    | COMM-SUCCESS        | X          | DISPLAY| Success flag                                 |
| 03    | COMM-FAIL-CODE      | X          | DISPLAY| Failure code                                 |

---

### PROCISRT-COMMAREA

Defined in: PROCISRT.cpy

The PROCISRT structure uses a union-style REDEFINES pattern. The base structure `PROCISRT-DEBIT-STRUCT` contains a 120-byte area (account number 9(8), sortcode 9(6), amount S9(10)V99, FILLER X(100)) that is overlaid by six alternative REDEFINES interpretations based on `PROCISRT-FUNCTION`.

| Level | Name                              | PIC        | Usage   | Description                                          |
| ----- | --------------------------------- | ---------- | ------- | ---------------------------------------------------- |
| 01    | PROCISRT-COMMAREA                 |            |         | Process transaction insert COMMAREA                  |
| 03    | PROCISRT-FUNCTION                 | X          | DISPLAY | Function code (88-values below)                      |
| 03    | PROCISRT-PCB-POINTER              | POINTER    |         | IMS PCB pointer                                      |
| 03    | PROCISRT-DEBIT-STRUCT             |            |         | Debit operation / base for all REDEFINES             |
| 05    | PROCISRT-DEBIT-ACCNO              | 9(8)       | DISPLAY | Account number                                       |
| 05    | PROCISRT-DEBIT-SORTCODE           | 9(6)       | DISPLAY | Sort code                                            |
| 05    | PROCISRT-DEBIT-AMOUNT             | S9(10)V99  | DISPLAY | Debit amount                                         |
| 05    | FILLER                            | X(100)     |         | Padding to accommodate larger union variants         |
| 03    | PROCISRT-CREDIT-STRUCT            |            |         | REDEFINES PROCISRT-DEBIT-STRUCT for credit           |
| 05    | PROCISRT-CREDIT-ACCNO             | 9(8)       | DISPLAY | Account number                                       |
| 05    | PROCISRT-CREDIT-SORTCODE          | 9(6)       | DISPLAY | Sort code                                            |
| 05    | PROCISRT-CREDIT-AMOUNT            | S9(10)V99  | DISPLAY | Credit amount                                        |
| 03    | PROCISRT-XFR-LOCAL-STRUCT         |            |         | REDEFINES for local transfer                         |
| 05    | PROCISRT-XFR-L-ACCNO              | 9(8)       | DISPLAY | Source account number                                |
| 05    | PROCISRT-XFR-L-SORTCODE           | 9(6)       | DISPLAY | Source sort code                                     |
| 05    | PROCISRT-XFR-L-AMOUNT             | S9(10)V99  | DISPLAY | Transfer amount                                      |
| 05    | PROCISRT-XFR-L-TARGET-ACCNO       | 9(8)       | DISPLAY | Target account number                                |
| 03    | PROCISRT-DELETE-CUST-STRUCT       |            |         | REDEFINES for delete customer                        |
| 05    | PROCISRT-DELETE-CUST-ACCNO        | 9(8)       | DISPLAY | Account number                                       |
| 05    | PROCISRT-DELETE-CUST-SORTCODE     | 9(6)       | DISPLAY | Sort code                                            |
| 05    | PROCISRT-DELETE-CUST-BALANCE      | S9(10)V99  | DISPLAY | Customer balance                                     |
| 05    | PROCISRT-DELETE-CUST-DOB          |            |         | Date of birth group                                  |
| 07    | PROCISRT-DELETE-CUST-DOB-YYYY     | 9999       | DISPLAY | Year of birth                                        |
| 07    | PROCISRT-DELETE-CUST-DOB-MM       | 99         | DISPLAY | Month of birth                                       |
| 07    | PROCISRT-DELETE-CUST-DOB-DD       | 99         | DISPLAY | Day of birth                                         |
| 05    | PROCISRT-DELETE-CUST-NAME         | X(60)      | DISPLAY | Customer name                                        |
| 05    | PROCISRT-DELETE-CUST-NUMBER       | 9(10)      | DISPLAY | Customer number                                      |
| 03    | PROCISRT-CREATE-CUST-STRUCT       |            |         | REDEFINES for create customer                        |
| 05    | PROCISRT-CREATE-CUST-ACCNO        | 9(8)       | DISPLAY | Account number                                       |
| 05    | PROCISRT-CREATE-CUST-SORTCODE     | 9(6)       | DISPLAY | Sort code                                            |
| 05    | PROCISRT-CREATE-CUST-BALANCE      | S9(10)V99  | DISPLAY | Balance                                              |
| 05    | PROCISRT-CREATE-CUST-DOB          |            |         | Date of birth group                                  |
| 07    | PROCISRT-CREATE-CUST-DOB-YYYY     | 9999       | DISPLAY | Year of birth                                        |
| 07    | PROCISRT-CREATE-CUST-DOB-MM       | 99         | DISPLAY | Month of birth                                       |
| 07    | PROCISRT-CREATE-CUST-DOB-DD       | 99         | DISPLAY | Day of birth                                         |
| 05    | PROCISRT-CREATE-CUST-NAME         | X(60)      | DISPLAY | Customer name                                        |
| 05    | PROCISRT-CREATE-CUST-NUMBER       | 9(10)      | DISPLAY | Customer number                                      |
| 03    | PROCISRT-DELACC-STRUCT            |            |         | REDEFINES for delete account                         |
| 05    | PROCISRT-DELACC-ACCNO             | 9(8)       | DISPLAY | Account number                                       |
| 05    | PROCISRT-DELACC-SORTCODE          | 9(6)       | DISPLAY | Sort code                                            |
| 05    | PROCISRT-DELACC-BALANCE           | S9(10)V99  | DISPLAY | Account balance                                      |
| 05    | PROCISRT-DELACC-L-STMNT           |            |         | Last statement date group                            |
| 07    | PROCISRT-DELACC-L-STMNT-YYYY      | 9999       | DISPLAY | Year                                                 |
| 07    | PROCISRT-DELACC-L-STMNT-MM        | 99         | DISPLAY | Month                                                |
| 07    | PROCISRT-DELACC-L-STMNT-DD        | 99         | DISPLAY | Day                                                  |
| 05    | PROCISRT-DELACC-N-STMNT           |            |         | Next statement date group                            |
| 07    | PROCISRT-DELACC-N-STMNT-YYYY      | 9999       | DISPLAY | Year                                                 |
| 07    | PROCISRT-DELACC-N-STMNT-MM        | 99         | DISPLAY | Month                                                |
| 07    | PROCISRT-DELACC-N-STMNT-DD        | 99         | DISPLAY | Day                                                  |
| 05    | PROCISRT-DELACC-TYPE              | X(8)       | DISPLAY | Account type                                         |
| 05    | PROCISRT-DELACC-CUSTNO            | 9(10)      | DISPLAY | Customer number                                      |
| 03    | PROCISRT-CREACC-STRUCT            |            |         | REDEFINES for create account                         |
| 05    | PROCISRT-CREACC-ACCNO             | 9(8)       | DISPLAY | Account number                                       |
| 05    | PROCISRT-CREACC-SORTCODE          | 9(6)       | DISPLAY | Sort code                                            |
| 05    | PROCISRT-CREACC-BALANCE           | S9(10)V99  | DISPLAY | Balance                                              |
| 05    | PROCISRT-CREACC-L-STMNT           |            |         | Last statement date group                            |
| 07    | PROCISRT-CREACC-L-STMNT-YYYY      | 9999       | DISPLAY | Year                                                 |
| 07    | PROCISRT-CREACC-L-STMNT-MM        | 99         | DISPLAY | Month                                                |
| 07    | PROCISRT-CREACC-L-STMNT-DD        | 99         | DISPLAY | Day                                                  |
| 05    | PROCISRT-CREAET-ACCT-N-STMNT      |            |         | Next statement date group                            |
| 07    | PROCISRT-CREACC-N-STMNT-YYYY      | 9999       | DISPLAY | Year                                                 |
| 07    | PROCISRT-CREACC-N-STMNT-MM        | 99         | DISPLAY | Month                                                |
| 07    | PROCISRT-CREACC-N-STMNT-DD        | 99         | DISPLAY | Day                                                  |
| 05    | PROCISRT-CREACC-TYPE              | X(8)       | DISPLAY | Account type                                         |
| 05    | PROCISRT-CREACC-CUSTNO            | 9(10)      | DISPLAY | Customer number                                      |

---

### NEWACCNO COMMAREA

Defined in: NEWACCNO.cpy

| Level | Name                  | PIC   | Usage   | Description                              |
| ----- | --------------------- | ----- | ------- | ---------------------------------------- |
| 03    | NEWACCNO-FUNCTION     | X     | DISPLAY | 'G'=GetNew, 'R'=Rollback, 'C'=Current   |
| 03    | ACCOUNT-NUMBER        | 9(8)  | DISPLAY | Returned or current account number       |
| 03    | NEWACCNO-SUCCESS      | X     | DISPLAY | Success flag                             |
| 03    | NEWACCNO-FAIL-CODE    | X     | DISPLAY | Failure code                             |

---

### NEWCUSNO COMMAREA

Defined in: NEWCUSNO.cpy

| Level | Name                  | PIC    | Usage   | Description                              |
| ----- | --------------------- | ------ | ------- | ---------------------------------------- |
| 03    | NEWCUSNO-FUNCTION     | X      | DISPLAY | 'G'=GetNew, 'R'=Rollback, 'C'=Current   |
| 03    | CUSTOMER-NUMBER       | 9(10)  | DISPLAY | Returned or current customer number      |
| 03    | NEWCUSNO-SUCCESS      | X      | DISPLAY | Success flag                             |
| 03    | NEWCUSNO-FAIL-CODE    | X      | DISPLAY | Failure code                             |

---

### CONTROLI (Control Counter Area)

Defined in: CONTROLI.cpy

| Level | Name                       | PIC    | Usage          | Description                        |
| ----- | -------------------------- | ------ | -------------- | ---------------------------------- |
| 03    | CONTROL-CUSTOMER-COUNT     | 9(10)  | PACKED-DECIMAL | Total customer count               |
| 03    | CONTROL-CUSTOMER-LAST      | 9(10)  | PACKED-DECIMAL | Last customer number allocated     |
| 03    | CONTROL-ACCOUNT-COUNT      | 9(8)   | PACKED-DECIMAL | Total account count                |
| 03    | CONTROL-ACCOUNT-LAST       | 9(8)   | PACKED-DECIMAL | Last account number allocated      |

---

### STCUSTNO (Customer Number Key)

Defined in: STCUSTNO.cpy

| Level | Name             | PIC    | Usage   | Description                   |
| ----- | ---------------- | ------ | ------- | ----------------------------- |
| 05    | Customer-Number-Key |     |         | Customer number key group     |
| 10    | CNO-KEY          | 9(10)  | DISPLAY | Customer number key value     |

---

### GETCOMPY COMMAREA

Defined in: GETCOMPY.cpy

| Level | Name                  | PIC    | Usage   | Description                         |
| ----- | --------------------- | ------ | ------- | ----------------------------------- |
| 03    | GETCompanyOperation   |        |         | Get company name operation struct   |
| 06    | company-name          | X(40)  | DISPLAY | Company/bank name returned          |

---

### GETSCODE COMMAREA

Defined in: GETSCODE.cpy

| Level | Name                    | PIC     | Usage   | Description              |
| ----- | ----------------------- | ------- | ------- | ------------------------ |
| 03    | GETSORTCODEOperation    |         |         | Get sort code struct     |
| 06    | SORTCODE                | X(6)    | DISPLAY | Sort code returned       |

---

### BANKDATA Working Storage Key Structures

Defined in: BANKDATA.cbl (WORKING-STORAGE)

| Level | Name                      | PIC        | Usage    | Description                                        |
| ----- | ------------------------- | ---------- | -------- | -------------------------------------------------- |
| 01    | HOST-ACCOUNT-ROW          |            |          | DB2 host variable row for ACCOUNT table            |
| 03    | HV-ACCOUNT-DATA           |            |          | Account data group                                 |
| 05    | HV-ACCOUNT-EYECATCHER     | X(4)       | DISPLAY  | Account eye-catcher host variable                  |
| 05    | HV-ACCOUNT-CUST-NO        | X(10)      | DISPLAY  | Customer number host variable                      |
| 05    | HV-ACCOUNT-KEY            |            |          | Account key group                                  |
| 07    | HV-ACCOUNT-SORT-CODE      | X(6)       | DISPLAY  | Sort code host variable                            |
| 07    | HV-ACCOUNT-NUMBER         | X(8)       | DISPLAY  | Account number host variable                       |
| 05    | HV-ACCOUNT-TYPE           | X(8)       | DISPLAY  | Account type host variable                         |
| 05    | HV-ACCOUNT-INTEREST-RATE  | S9(4)V99   | COMP-3   | Interest rate host variable                        |
| 05    | HV-ACCOUNT-OPENED         | X(10)      | DISPLAY  | Opened date (ISO format: DD-MM-YYYY)               |
| 05    | HV-ACCOUNT-OVERDRAFT-LIMIT| S9(9)      | COMP     | Overdraft limit host variable                      |
| 05    | HV-ACCOUNT-LAST-STMT-DATE | X(10)      | DISPLAY  | Last statement date host variable                  |
| 05    | HV-ACCOUNT-NEXT-STMT-DATE | X(10)      | DISPLAY  | Next statement date host variable                  |
| 05    | HV-ACCOUNT-AVAILABLE-BALANCE | S9(10)V99 | COMP-3 | Available balance host variable                    |
| 05    | HV-ACCOUNT-ACTUAL-BALANCE | S9(10)V99  | COMP-3   | Actual balance host variable                       |
| 01    | HOST-CONTROL-ROW          |            |          | DB2 host variable row for CONTROL table            |
| 03    | HV-CONTROL-NAME           | X(32)      | DISPLAY  | Control record name                                |
| 03    | HV-CONTROL-VALUE-NUM      | S9(9)      | COMP     | Control numeric value                              |
| 03    | HV-CONTROL-VALUE-STR      | X(40)      | DISPLAY  | Control string value                               |
| 01    | FORENAMES                 |            |          | Array of first names (OCCURS 100)                  |
| 05    | FORENAME                  | X(20)      | DISPLAY  | First name entry                                   |
| 01    | SURNAMES                  |            |          | Array of surnames (OCCURS 100)                     |
| 05    | SURNAME                   | X(20)      | DISPLAY  | Surname entry                                      |
| 01    | TOWNS                     |            |          | Array of town names (OCCURS 50)                    |
| 05    | TOWN                      | X(20)      | DISPLAY  | Town name entry                                    |

---

### NCS-ACC-NO-STUFF (Named Counter Service - Account)

Defined in: CREACC.cbl (LOCAL-STORAGE), INQACC.cbl (WORKING-STORAGE)

The CICS Named Counter Service (NCS) is used by CREACC to allocate new account numbers and by INQACC to determine the range of existing accounts. Two distinct NCS counter names are used across programs:

- `CBSAACCT` + sort-code suffix: the production counter name used in CREACC
- `HBNKACCT` + sort-code suffix: the counter name used in INQACC for browse range determination

| Level | Name                   | PIC     | Usage   | Description                                            |
| ----- | ---------------------- | ------- | ------- | ------------------------------------------------------ |
| 01    | NCS-ACC-NO-STUFF       |         |         | Named counter control block for account number sequence |
| 03    | NCS-ACC-NO-NAME        |         |         | 16-byte counter name passed to CICS ENQ/DEQ            |
| 05    | NCS-ACC-NO-ACT-NAME    | X(8)    | DISPLAY | Counter prefix: 'CBSAACCT' (CREACC) or 'HBNKACCT' (INQACC) |
| 05    | NCS-ACC-NO-TEST-SORT   | X(6)    | DISPLAY | Sort code appended to form unique counter name         |
| 05    | NCS-ACC-NO-FILL        | XX      | DISPLAY | Padding to complete 16-byte name                       |
| 03    | NCS-ACC-NO-INC         | 9(16)   | COMP    | Increment value (set to 1 before GET COUNTER)          |
| 03    | NCS-ACC-NO-VALUE       | 9(16)   | COMP    | Current counter value returned from NCS                |
| 03    | NCS-ACC-NO-RESP        | XX      | DISPLAY | NCS response code ('00' = success)                     |
| 01    | NCS-ACC-NO-DISP        | 9(16)   | DISPLAY | Display form of counter value; rightmost 8 digits used as account number |
| 01    | NCS-UPDATED            | X       | DISPLAY | 'Y' if NCS counter was incremented this invocation     |

Note: CREACC uses EXEC CICS ENQ RESOURCE(NCS-ACC-NO-NAME) to serialise counter access, then reads/increments the counter via the CONTROL DB2 table as a fallback when NCS is unavailable.

---

### NCS-CUST-NO-STUFF (Named Counter Service - Customer)

Defined in: CRECUST.cbl (LOCAL-STORAGE), INQCUST.cbl (WORKING-STORAGE)

Parallel NCS structure for customer number allocation. Two counter names are used:

- `CBSACUST` + sort-code suffix: production counter used in CRECUST
- `HBNKCUST` + sort-code suffix: counter used in INQCUST for browse range determination

| Level | Name                   | PIC     | Usage   | Description                                              |
| ----- | ---------------------- | ------- | ------- | -------------------------------------------------------- |
| 01    | NCS-CUST-NO-STUFF      |         |         | Named counter control block for customer number sequence |
| 03    | NCS-CUST-NO-NAME       |         |         | 16-byte counter name passed to CICS ENQ/DEQ              |
| 05    | NCS-CUST-NO-ACT-NAME   | X(8)    | DISPLAY | Counter prefix: 'CBSACUST' (CRECUST) or 'HBNKCUST' (INQCUST) |
| 05    | NCS-CUST-NO-TEST-SORT  | X(6)    | DISPLAY | Sort code appended to form unique counter name           |
| 05    | NCS-CUST-NO-FILL       | XX      | DISPLAY | Padding to complete 16-byte name                         |
| 03    | NCS-CUST-NO-INC        | 9(16)   | COMP    | Increment value                                          |
| 03    | NCS-CUST-NO-VALUE      | 9(16)   | COMP    | Current counter value returned from NCS                  |
| 03    | NCS-CUST-NO-RESP       | XX      | DISPLAY | NCS response code ('00' = success)                       |
| 01    | NCS-UPDATED            | X       | DISPLAY | 'Y' if NCS counter was incremented this invocation       |

---

### BNK1DDM BMS Map

Defined in: BNK1DDM.cpy

| Level | Name      | PIC    | Usage | Description                          |
| ----- | --------- | ------ | ----- | ------------------------------------ |
| 01    | BNK1DDI   |        |       | Bank menu/data display input map     |
| 02    | COMPANYI  | X(56)  |       | Company name input field             |
| 02    | MESSAGEI  | X(79)  |       | Message field input                  |
| 02    | DUMMYI    | X(1)   |       | Dummy AID field                      |
| 01    | BNK1DDO   |        |       | REDEFINES BNK1DDI (output map)       |
| 02    | COMPANYO  | X(56)  |       | Company name output field            |
| 02    | MESSAGEO  | X(79)  |       | Message field output                 |
| 02    | DUMMYO    | X(1)   |       | Dummy AID field output               |

---

### BANKMAPI / BANKMAPO (Administration Screen BMS Map)

Defined in: BANKMAP.cpy

The BANKMAP BMS symbolic map is used by the BANKDATA administration screen. It reveals that the application architecture was designed to support a much broader set of datastores beyond those implemented in the current COBOL source (CUSTOMER, ACCOUNT, PROCTRAN). The presence of B2BX, CLEARING, SODD, and NCOU control/count fields indicates the original design included B2B transfer, clearing, standing-order/direct-debit, and named-counter datastore categories.

| Field Group | Input Field  | Output Field | PIC    | Description                               |
| ----------- | ------------ | ------------ | ------ | ----------------------------------------- |
| Company     | COMPANYI     | COMPANYO     | X(40)  | Company name display                      |
| Sort Code   | SORTCODEI    | SORTCODEO    | X(6)   | Sort code                                 |
| Cust Ctrl   | CUSTCTRLI    | CUSTCTRLO    | X(1)   | Customer control record indicator         |
| Customer    | CUSTOMERI    | CUSTOMERO    | X(10)  | Customer count or number                  |
| Acct Ctrl   | ACCTCTRLI    | ACCTCTRLO    | X(1)   | Account control record indicator          |
| Account     | ACCOUNTI     | ACCOUNTO     | X(10)  | Account count or number                   |
| Proc Ctrl   | PROCCTRLI    | PROCCTRLO    | X(1)   | Processed transaction control indicator   |
| ProcTran    | PROCTRANI    | PROCTRANO    | X(10)  | Processed transaction count               |
| Rejt Ctrl   | REJTCTRLI    | REJTCTRLO    | X(1)   | Rejected transaction control indicator    |
| RejTran     | REJTRANI     | REJTRANO     | X(10)  | Rejected transaction count                |
| B2BX Ctrl   | B2BXCTRLI    | B2BXCTRLO    | X(1)   | B2B transfer control indicator (unused)   |
| B2BX        | B2BXFRI      | B2BXFRO      | X(10)  | B2B transfer count (unused)               |
| Clea Ctrl   | CLEACTRLI    | CLEACTRLO    | X(1)   | Clearing control indicator (unused)       |
| Clearing    | CLEARINGI    | CLEARINGO    | X(10)  | Clearing count (unused)                   |
| SODD Ctrl   | SODDCTRLI    | SODDCTRLO    | X(1)   | Standing order/direct debit ctrl (unused) |
| SODD        | SODDI        | SODDO        | X(10)  | SODD count (unused)                       |
| NCOU Ctrl   | NCOUCTRLI    | NCOUCTRLO    | X(1)   | Named counter control indicator (unused)  |
| NCounter    | NCOUNTERI    | NCOUNTERO    | X(10)  | Named counter count (unused)              |
| Cust Msg    | CUSTMSGI     | CUSTMSGO     | X(70)  | Customer status message                   |
| Acct Msg    | ACCTMSGI     | ACCTMSGO     | X(70)  | Account status message                    |
| Proc Msg    | PROCMSGI     | PROCMSGO     | X(70)  | Processed transaction status message      |
| Rejt Msg    | REJTMSGI     | REJTMSGO     | X(70)  | Rejected transaction status message       |
| B2BX Msg    | B2BXMSGI     | B2BXMSGO     | X(70)  | B2B transfer status message               |
| Clea Msg    | CLEAMSGI     | CLEAMSGO     | X(70)  | Clearing status message                   |
| SODD Msg    | SODDMSGI     | SODDMSGO     | X(70)  | SODD status message                       |
| NCOU Msg    | NCOUMSGI     | NCOUMSGO     | X(70)  | Named counter status message              |

Each BMS field pair has an associated length (COMP S9(4)), flag/attribute (PICTURE X), and a REDEFINES attribute byte (PICTURE X) as per standard BMS symbolic map layout.

---

### CUSTMAP BMS Map (CSTMAP1I / CSTMAP1O)

Defined in: CUSTMAP.cpy

| Level | Name       | Input Field | Output Field | PIC    | Description                   |
| ----- | ---------- | ----------- | ------------ | ------ | ----------------------------- |
| 01    | CSTMAP1I   |             |              |        | Customer screen input map     |
| 02    |            | CUSTEYEI    | CUSTEYEO     | X(4)   | Customer eye-catcher          |
| 02    |            | CUSTKEYI    | CUSTKEYO     | X(10)  | Customer key / number         |
| 02    |            | CUSTNAMEI   | CUSTNAMEO    | X(60)  | Customer name                 |
| 02    |            | ADDR1I      | ADDR1O       | X(60)  | Address line 1                |
| 02    |            | ADDR2I      | ADDR2O       | X(60)  | Address line 2                |
| 02    |            | ADDR3I      | ADDR3O       | X(40)  | Address line 3 / town         |
| 02    |            | CUSTDOBI    | CUSTDOBO     | X(10)  | Date of birth                 |
| 01    | CSTMAP1O   |             |              |        | REDEFINES CSTMAP1I (output)   |

---

## Shared Data Items

Data items defined in copybooks and used across multiple programs:

| Data Item              | Defined In    | Used By Programs                                         | PIC        | Description                          |
| ---------------------- | ------------- | -------------------------------------------------------- | ---------- | ------------------------------------ |
| ACCOUNT-DATA           | ACCOUNT.cpy   | BANKDATA, CREACC (LOCAL-STORAGE)                         | (group)    | Full account record structure        |
| CUSTOMER-RECORD        | CUSTOMER.cpy  | BANKDATA (FD), CREACC (LOCAL-STORAGE)                    | (group)    | Full customer record structure       |
| PROC-TRAN-DATA         | PROCTRAN.cpy  | CREACC, DELACC, DBCRFUN, XFRFUN, CRECUST, DELCUS         | (group)    | Processed transaction record         |
| ACCOUNT-CONTROL-RECORD | ACCTCTRL.cpy  | BANKDATA, CREACC (LOCAL-STORAGE)                         | (group)    | Account control counter              |
| CUSTOMER-CONTROL-RECORD| CUSTCTRL.cpy  | BANKDATA, CRECUST                                        | (group)    | Customer control counter             |
| ABND-INFO              | ABNDINFO.cpy  | ABNDPROC, CREACC (LOCAL-STORAGE), most programs          | (group)    | Abend diagnostic information         |
| SORTCODE               | SORTCODE.cpy  | BANKDATA, CREACC, DBCRFUN, XFRFUN, and others            | 9(6)       | Bank sort code literal value 987654  |
| INQACC-COMMAREA        | INQACC.cpy    | INQACC, BNK1CAC, callers of INQACC                       | (group)    | Account inquiry interface            |
| INQACCCU (COMMAREA)    | INQACCCU.cpy  | INQACCCU, BNK1CAC, CREACC (LOCAL-STORAGE)                | (group)    | Accounts-by-customer interface       |
| INQCUST COMMAREA       | INQCUST.cpy   | INQCUST, BNK1CCA, CREACC (LOCAL-STORAGE)                 | (group)    | Customer inquiry interface           |
| DELACC-COMMAREA        | DELACC.cpy    | DELACC, BNK1DAC                                          | (group)    | Delete account interface             |
| DELCUS COMMAREA        | DELCUS.cpy    | DELCUS, BNK1DCS                                          | (group)    | Delete customer interface            |
| CREACC COMMAREA        | CREACC.cpy    | CREACC (DFHCOMMAREA), BNK1CCA                            | (group)    | Create account interface             |
| CRECUST COMMAREA       | CRECUST.cpy   | CRECUST (DFHCOMMAREA), BNK1CCS                           | (group)    | Create customer interface            |
| UPDACC COMMAREA        | UPDACC.cpy    | UPDACC, BNK1UAC                                          | (group)    | Update account interface             |
| UPDCUST COMMAREA       | UPDCUST.cpy   | UPDCUST, BNK1UAC                                         | (group)    | Update customer interface            |
| XFRFUN COMMAREA        | XFRFUN.cpy    | XFRFUN, BNK1TFN                                          | (group)    | Fund transfer interface              |
| PAYDBCR COMMAREA       | PAYDBCR.cpy   | DBCRFUN, BNK1CAC                                         | (group)    | Debit/credit payment interface       |
| NEWACCNO COMMAREA      | NEWACCNO.cpy  | CREACC, callers needing new account numbers              | (group)    | New account number allocation        |
| NEWCUSNO COMMAREA      | NEWCUSNO.cpy  | CRECUST, callers needing new customer numbers            | (group)    | New customer number allocation       |
| PROCISRT-COMMAREA      | PROCISRT.cpy  | CRDTAGY1-5 (IMS write agents)                            | (group)    | Process transaction insert           |
| CONTROLI               | CONTROLI.cpy  | Used by IMS-based programs                               | (group)    | Control table counters               |
| STCUSTNO               | STCUSTNO.cpy  | IMS-based programs                                       | 9(10)      | Customer number key for IMS          |
| BANKMAP (BMS)          | BANKMAP.cpy   | BNKMENU                                                  | (group)    | Bank menu BMS map I/O                |
| BNK1DDM (BMS)          | BNK1DDM.cpy   | BNKMENU                                                  | (group)    | Bank data display BMS map            |
| CUSTMAP (BMS)          | CUSTMAP.cpy   | BNK1CCS, BNK1UAC, BNK1CCA, BNK1DCS                      | (group)    | Customer BMS map I/O                 |

---

## Constants and Literals

Named constants (88-level items) and significant literals found in the codebase:

| Constant                         | Value     | Defined In     | Usage Context                                       |
| -------------------------------- | --------- | -------------- | --------------------------------------------------- |
| SORTCODE                         | 987654    | SORTCODE.cpy   | Bank sort code used throughout all programs         |
| ACCOUNT-EYECATCHER-VALUE         | 'ACCT'    | ACCOUNT.cpy    | Validates account record eye-catcher                |
| CUSTOMER-EYECATCHER-VALUE        | 'CUST'    | CUSTOMER.cpy   | Validates customer record eye-catcher               |
| PROC-TRAN-VALID                  | 'PRTR'    | PROCTRAN.cpy   | Validates processed transaction eye-catcher         |
| PROC-TRAN-LOGICALLY-DELETED      | X'FF'     | PROCTRAN.cpy   | Logical delete flag in eye-catcher field            |
| ACCOUNT-CONTROL-EYECATCHER-V     | 'CTRL'    | ACCTCTRL.cpy   | Account control record eye-catcher                  |
| CUSTOMER-CONTROL-EYECATCHER-V    | 'CTRL'    | CUSTCTRL.cpy   | Customer control record eye-catcher                 |
| ACCOUNT-CONTROL-SUCCESS          | 'Y'       | ACCTCTRL.cpy   | Account control operation success                   |
| CUSTOMER-CONTROL-SUCCESS         | 'Y'       | CUSTCTRL.cpy   | Customer control operation success                  |
| NEWACCNO-FUNCTION-GETNEW         | 'G'       | NEWACCNO.cpy   | Get a new account number                            |
| NEWACCNO-FUNCTION-ROLLBACK       | 'R'       | NEWACCNO.cpy   | Roll back account number allocation                 |
| NEWACCNO-FUNCTION-CURRENT        | 'C'       | NEWACCNO.cpy   | Return current account number                       |
| NEWCUSNO-FUNCTION-GETNEW         | 'G'       | NEWCUSNO.cpy   | Get a new customer number                           |
| NEWCUSNO-FUNCTION-ROLLBACK       | 'R'       | NEWCUSNO.cpy   | Roll back customer number allocation                |
| NEWCUSNO-FUNCTION-CURRENT        | 'C'       | NEWCUSNO.cpy   | Return current customer number                      |
| PROCISRT-DEBIT                   | '1'       | PROCISRT.cpy   | Insert debit transaction                            |
| PROCISRT-CREDIT                  | '2'       | PROCISRT.cpy   | Insert credit transaction                           |
| PROCISRT-XFR-LOCAL               | '3'       | PROCISRT.cpy   | Insert local transfer transaction                   |
| PROCISRT-DELETE-CUSTOMER         | '4'       | PROCISRT.cpy   | Insert delete customer transaction                  |
| PROCISRT-CREATE-CUSTOMER         | '5'       | PROCISRT.cpy   | Insert create customer transaction                  |
| PROCISRT-DELETE-ACCOUNT          | '6'       | PROCISRT.cpy   | Insert delete account transaction                   |
| PROCISRT-CREATE-ACCOUNT          | '7'       | PROCISRT.cpy   | Insert create account transaction                   |
| PROC-TY-CHEQUE-ACKNOWLEDGED      | 'CHA'     | PROCTRAN.cpy   | Transaction type: cheque acknowledged               |
| PROC-TY-CHEQUE-FAILURE           | 'CHF'     | PROCTRAN.cpy   | Transaction type: cheque failure                    |
| PROC-TY-CHEQUE-PAID-IN           | 'CHI'     | PROCTRAN.cpy   | Transaction type: cheque paid in                    |
| PROC-TY-CHEQUE-PAID-OUT          | 'CHO'     | PROCTRAN.cpy   | Transaction type: cheque paid out                   |
| PROC-TY-CREDIT                   | 'CRE'     | PROCTRAN.cpy   | Transaction type: credit                            |
| PROC-TY-DEBIT                    | 'DEB'     | PROCTRAN.cpy   | Transaction type: debit                             |
| PROC-TY-WEB-CREATE-ACCOUNT       | 'ICA'     | PROCTRAN.cpy   | Transaction type: web create account                |
| PROC-TY-WEB-CREATE-CUSTOMER      | 'ICC'     | PROCTRAN.cpy   | Transaction type: web create customer               |
| PROC-TY-WEB-DELETE-ACCOUNT       | 'IDA'     | PROCTRAN.cpy   | Transaction type: web delete account                |
| PROC-TY-WEB-DELETE-CUSTOMER      | 'IDC'     | PROCTRAN.cpy   | Transaction type: web delete customer               |
| PROC-TY-BRANCH-CREATE-ACCOUNT    | 'OCA'     | PROCTRAN.cpy   | Transaction type: branch create account             |
| PROC-TY-BRANCH-CREATE-CUSTOMER   | 'OCC'     | PROCTRAN.cpy   | Transaction type: branch create customer            |
| PROC-TY-BRANCH-DELETE-ACCOUNT    | 'ODA'     | PROCTRAN.cpy   | Transaction type: branch delete account             |
| PROC-TY-BRANCH-DELETE-CUSTOMER   | 'ODC'     | PROCTRAN.cpy   | Transaction type: branch delete customer            |
| PROC-TY-CREATE-SODD              | 'OCS'     | PROCTRAN.cpy   | Transaction type: create standing order direct debit|
| PROC-TY-PAYMENT-CREDIT           | 'PCR'     | PROCTRAN.cpy   | Transaction type: payment credit                    |
| PROC-TY-PAYMENT-DEBIT            | 'PDR'     | PROCTRAN.cpy   | Transaction type: payment debit                     |
| PROC-TY-TRANSFER                 | 'TFR'     | PROCTRAN.cpy   | Transaction type: transfer                          |
| NCS-ACC-NO-ACT-NAME (CREACC)     | 'CBSAACCT'| CREACC.cbl     | CICS Named Counter name prefix for account numbers  |
| NCS-ACC-NO-ACT-NAME (INQACC)     | 'HBNKACCT'| INQACC.cbl     | CICS Named Counter name prefix for account browse   |
| NCS-CUST-NO-ACT-NAME (CRECUST)   | 'CBSACUST'| CRECUST.cbl    | CICS Named Counter name prefix for customer numbers |
| NCS-CUST-NO-ACT-NAME (INQCUST)   | 'HBNKCUST'| INQCUST.cbl    | CICS Named Counter name prefix for customer browse  |
| WS-TESTING-TYPE (XFRFUN)         | 'STTESTER.'| XFRFUN.cbl    | DB2 schema owner prefix for dynamic SQL in XFRFUN  |
