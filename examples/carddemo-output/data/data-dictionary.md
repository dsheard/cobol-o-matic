---
type: data
subtype: data-dictionary
status: draft
confidence: high
last_pass: 5
---

# Data Dictionary

All data items extracted from WORKING-STORAGE, LOCAL-STORAGE, LINKAGE SECTION, and copybooks.

## Key Data Structures

### CUSTOMER-RECORD

Defined in: CVCUS01Y.cpy (primary) / CUSTREC.cpy (alternate)

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | CUSTOMER-RECORD | | | Customer master record (RECLN 500) |
| 05 | CUST-ID | 9(09) | DISPLAY | Unique customer identifier |
| 05 | CUST-FIRST-NAME | X(25) | DISPLAY | Customer first name |
| 05 | CUST-MIDDLE-NAME | X(25) | DISPLAY | Customer middle name |
| 05 | CUST-LAST-NAME | X(25) | DISPLAY | Customer last name |
| 05 | CUST-ADDR-LINE-1 | X(50) | DISPLAY | Address line 1 |
| 05 | CUST-ADDR-LINE-2 | X(50) | DISPLAY | Address line 2 |
| 05 | CUST-ADDR-LINE-3 | X(50) | DISPLAY | Address line 3 |
| 05 | CUST-ADDR-STATE-CD | X(02) | DISPLAY | US state code |
| 05 | CUST-ADDR-COUNTRY-CD | X(03) | DISPLAY | Country code (ISO) |
| 05 | CUST-ADDR-ZIP | X(10) | DISPLAY | ZIP/postal code |
| 05 | CUST-PHONE-NUM-1 | X(15) | DISPLAY | Primary phone number |
| 05 | CUST-PHONE-NUM-2 | X(15) | DISPLAY | Secondary phone number |
| 05 | CUST-SSN | 9(09) | DISPLAY | Social security number |
| 05 | CUST-GOVT-ISSUED-ID | X(20) | DISPLAY | Government-issued ID |
| 05 | CUST-DOB-YYYY-MM-DD | X(10) | DISPLAY | Date of birth (YYYY-MM-DD) -- CVCUS01Y |
| 05 | CUST-EFT-ACCOUNT-ID | X(10) | DISPLAY | Electronic funds transfer account |
| 05 | CUST-PRI-CARD-HOLDER-IND | X(01) | DISPLAY | Primary card holder indicator (Y/N) |
| 05 | CUST-FICO-CREDIT-SCORE | 9(03) | DISPLAY | FICO credit score (300-850) |
| 05 | FILLER | X(168) | | Reserved/padding to 500 bytes |

> Note: CUSTREC.cpy defines the same structure but names the DOB field `CUST-DOB-YYYYMMDD` (no dashes) rather than `CUST-DOB-YYYY-MM-DD`. CUSTREC.cpy is used by CBSTM03A for statement generation. CVCUS01Y.cpy is the authoritative definition used by all other programs.

---

### ACCOUNT-RECORD

Defined in: CVACT01Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | ACCOUNT-RECORD | | | Account master record (RECLN 300) |
| 05 | ACCT-ID | 9(11) | DISPLAY | Unique account identifier |
| 05 | ACCT-ACTIVE-STATUS | X(01) | DISPLAY | Account status (Y=active, N=inactive) |
| 05 | ACCT-CURR-BAL | S9(10)V99 | DISPLAY | Current balance |
| 05 | ACCT-CREDIT-LIMIT | S9(10)V99 | DISPLAY | Credit limit |
| 05 | ACCT-CASH-CREDIT-LIMIT | S9(10)V99 | DISPLAY | Cash advance credit limit |
| 05 | ACCT-OPEN-DATE | X(10) | DISPLAY | Account open date (YYYY-MM-DD) |
| 05 | ACCT-EXPIRAION-DATE | X(10) | DISPLAY | Account expiration date (note: typo in source) |
| 05 | ACCT-REISSUE-DATE | X(10) | DISPLAY | Card reissue date |
| 05 | ACCT-CURR-CYC-CREDIT | S9(10)V99 | DISPLAY | Current cycle credits |
| 05 | ACCT-CURR-CYC-DEBIT | S9(10)V99 | DISPLAY | Current cycle debits |
| 05 | ACCT-ADDR-ZIP | X(10) | DISPLAY | Account billing ZIP code |
| 05 | ACCT-GROUP-ID | X(10) | DISPLAY | Disclosure group ID for interest rates |
| 05 | FILLER | X(178) | | Reserved/padding to 300 bytes |

---

### CARD-RECORD

Defined in: CVACT02Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | CARD-RECORD | | | Credit card record (RECLN 150) |
| 05 | CARD-NUM | X(16) | DISPLAY | Credit card number (16-digit) |
| 05 | CARD-ACCT-ID | 9(11) | DISPLAY | Associated account ID |
| 05 | CARD-CVV-CD | 9(03) | DISPLAY | Card verification value |
| 05 | CARD-EMBOSSED-NAME | X(50) | DISPLAY | Name as embossed on card |
| 05 | CARD-EXPIRAION-DATE | X(10) | DISPLAY | Card expiration date (note: typo in source) |
| 05 | CARD-ACTIVE-STATUS | X(01) | DISPLAY | Card status (Y=active, N=inactive) |
| 05 | FILLER | X(59) | | Reserved/padding to 150 bytes |

---

### CARD-XREF-RECORD

Defined in: CVACT03Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | CARD-XREF-RECORD | | | Card cross-reference record (RECLN 50) |
| 05 | XREF-CARD-NUM | X(16) | DISPLAY | Credit card number |
| 05 | XREF-CUST-ID | 9(09) | DISPLAY | Associated customer ID |
| 05 | XREF-ACCT-ID | 9(11) | DISPLAY | Associated account ID |
| 05 | FILLER | X(14) | | Reserved/padding to 50 bytes |

---

### TRAN-RECORD

Defined in: CVTRA05Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | TRAN-RECORD | | | Transaction record (RECLN 350) |
| 05 | TRAN-ID | X(16) | DISPLAY | Unique transaction identifier |
| 05 | TRAN-TYPE-CD | X(02) | DISPLAY | Transaction type code |
| 05 | TRAN-CAT-CD | 9(04) | DISPLAY | Transaction category code |
| 05 | TRAN-SOURCE | X(10) | DISPLAY | Transaction source system |
| 05 | TRAN-DESC | X(100) | DISPLAY | Transaction description |
| 05 | TRAN-AMT | S9(09)V99 | DISPLAY | Transaction amount (signed) |
| 05 | TRAN-MERCHANT-ID | 9(09) | DISPLAY | Merchant identifier |
| 05 | TRAN-MERCHANT-NAME | X(50) | DISPLAY | Merchant name |
| 05 | TRAN-MERCHANT-CITY | X(50) | DISPLAY | Merchant city |
| 05 | TRAN-MERCHANT-ZIP | X(10) | DISPLAY | Merchant ZIP code |
| 05 | TRAN-CARD-NUM | X(16) | DISPLAY | Card number used for transaction |
| 05 | TRAN-ORIG-TS | X(26) | DISPLAY | Transaction origination timestamp |
| 05 | TRAN-PROC-TS | X(26) | DISPLAY | Transaction processing timestamp |
| 05 | FILLER | X(20) | | Reserved/padding to 350 bytes |

---

### TRNX-RECORD

Defined in: COSTM01.CPY

Used by: CBSTM03A (statement generation program)

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | TRNX-RECORD | | | Transaction record for statement reporting (RECLN 350) |
| 05 | TRNX-KEY | | | Composite key for TRNXFILE VSAM |
| 10 | TRNX-CARD-NUM | X(16) | DISPLAY | Credit card number (first key component) |
| 10 | TRNX-ID | X(16) | DISPLAY | Transaction ID (second key component) |
| 05 | TRNX-REST | | | Non-key data fields |
| 10 | TRNX-TYPE-CD | X(02) | DISPLAY | Transaction type code |
| 10 | TRNX-CAT-CD | 9(04) | DISPLAY | Transaction category code |
| 10 | TRNX-SOURCE | X(10) | DISPLAY | Source system |
| 10 | TRNX-DESC | X(100) | DISPLAY | Transaction description |
| 10 | TRNX-AMT | S9(09)V99 | DISPLAY | Transaction amount (signed) |
| 10 | TRNX-MERCHANT-ID | 9(09) | DISPLAY | Merchant identifier |
| 10 | TRNX-MERCHANT-NAME | X(50) | DISPLAY | Merchant name |
| 10 | TRNX-MERCHANT-CITY | X(50) | DISPLAY | Merchant city |
| 10 | TRNX-MERCHANT-ZIP | X(10) | DISPLAY | Merchant ZIP code |
| 10 | TRNX-ORIG-TS | X(26) | DISPLAY | Origination timestamp |
| 10 | TRNX-PROC-TS | X(26) | DISPLAY | Processing timestamp |
| 10 | FILLER | X(20) | | Reserved/padding to 350 bytes |

> Note: This layout mirrors TRAN-RECORD (CVTRA05Y.cpy) but uses a composite key (CARD-NUM + TRAN-ID) instead of TRAN-ID alone. This allows TRNXFILE to be keyed by card number for efficient per-card transaction retrieval during statement generation.

---

### DALYTRAN-RECORD

Defined in: CVTRA06Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | DALYTRAN-RECORD | | | Daily transaction input record (RECLN 350) |
| 05 | DALYTRAN-ID | X(16) | DISPLAY | Transaction identifier |
| 05 | DALYTRAN-TYPE-CD | X(02) | DISPLAY | Transaction type code |
| 05 | DALYTRAN-CAT-CD | 9(04) | DISPLAY | Transaction category code |
| 05 | DALYTRAN-SOURCE | X(10) | DISPLAY | Source system |
| 05 | DALYTRAN-DESC | X(100) | DISPLAY | Transaction description |
| 05 | DALYTRAN-AMT | S9(09)V99 | DISPLAY | Transaction amount (signed) |
| 05 | DALYTRAN-MERCHANT-ID | 9(09) | DISPLAY | Merchant identifier |
| 05 | DALYTRAN-MERCHANT-NAME | X(50) | DISPLAY | Merchant name |
| 05 | DALYTRAN-MERCHANT-CITY | X(50) | DISPLAY | Merchant city |
| 05 | DALYTRAN-MERCHANT-ZIP | X(10) | DISPLAY | Merchant ZIP |
| 05 | DALYTRAN-CARD-NUM | X(16) | DISPLAY | Card number |
| 05 | DALYTRAN-ORIG-TS | X(26) | DISPLAY | Origination timestamp |
| 05 | DALYTRAN-PROC-TS | X(26) | DISPLAY | Processing timestamp |
| 05 | FILLER | X(20) | | Reserved/padding to 350 bytes |

---

### TRAN-CAT-BAL-RECORD

Defined in: CVTRA01Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | TRAN-CAT-BAL-RECORD | | | Transaction category balance record (RECLN 50) |
| 05 | TRAN-CAT-KEY | | | Composite key |
| 10 | TRANCAT-ACCT-ID | 9(11) | DISPLAY | Account ID (key component) |
| 10 | TRANCAT-TYPE-CD | X(02) | DISPLAY | Transaction type code (key component) |
| 10 | TRANCAT-CD | 9(04) | DISPLAY | Transaction category code (key component) |
| 05 | TRAN-CAT-BAL | S9(09)V99 | DISPLAY | Balance for category |
| 05 | FILLER | X(22) | | Reserved/padding to 50 bytes |

---

### DIS-GROUP-RECORD

Defined in: CVTRA02Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | DIS-GROUP-RECORD | | | Disclosure group (interest rate) record (RECLN 50) |
| 05 | DIS-GROUP-KEY | | | Composite key |
| 10 | DIS-ACCT-GROUP-ID | X(10) | DISPLAY | Account group identifier (key component) |
| 10 | DIS-TRAN-TYPE-CD | X(02) | DISPLAY | Transaction type code (key component) |
| 10 | DIS-TRAN-CAT-CD | 9(04) | DISPLAY | Transaction category code (key component) |
| 05 | DIS-INT-RATE | S9(04)V99 | DISPLAY | Interest rate for this group/type/category |
| 05 | FILLER | X(28) | | Reserved/padding to 50 bytes |

---

### TRAN-TYPE-RECORD

Defined in: CVTRA03Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | TRAN-TYPE-RECORD | | | Transaction type lookup record (RECLN 60) |
| 05 | TRAN-TYPE | X(02) | DISPLAY | Transaction type code (key) |
| 05 | TRAN-TYPE-DESC | X(50) | DISPLAY | Description of transaction type |
| 05 | FILLER | X(08) | | Reserved/padding to 60 bytes |

---

### TRAN-CAT-RECORD

Defined in: CVTRA04Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | TRAN-CAT-RECORD | | | Transaction category lookup record (RECLN 60) |
| 05 | TRAN-CAT-KEY | | | Composite key |
| 10 | TRAN-TYPE-CD | X(02) | DISPLAY | Transaction type code (key component) |
| 10 | TRAN-CAT-CD | 9(04) | DISPLAY | Transaction category code (key component) |
| 05 | TRAN-CAT-TYPE-DESC | X(50) | DISPLAY | Description of category |
| 05 | FILLER | X(04) | | Reserved/padding to 60 bytes |

---

### SEC-USER-DATA

Defined in: CSUSR01Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | SEC-USER-DATA | | | User security record (RECLN 80) |
| 05 | SEC-USR-ID | X(08) | DISPLAY | User identifier |
| 05 | SEC-USR-FNAME | X(20) | DISPLAY | User first name |
| 05 | SEC-USR-LNAME | X(20) | DISPLAY | User last name |
| 05 | SEC-USR-PWD | X(08) | DISPLAY | User password (plaintext) |
| 05 | SEC-USR-TYPE | X(01) | DISPLAY | User type (A=Admin, U=User) |
| 05 | SEC-USR-FILLER | X(23) | | Reserved/padding to 80 bytes |

---

### CARDDEMO-COMMAREA

Defined in: COCOM01Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | CARDDEMO-COMMAREA | | | CICS communication area for CardDemo |
| 05 | CDEMO-GENERAL-INFO | | | Navigation and session info |
| 10 | CDEMO-FROM-TRANID | X(04) | DISPLAY | Source transaction ID |
| 10 | CDEMO-FROM-PROGRAM | X(08) | DISPLAY | Source program name |
| 10 | CDEMO-TO-TRANID | X(04) | DISPLAY | Target transaction ID |
| 10 | CDEMO-TO-PROGRAM | X(08) | DISPLAY | Target program name |
| 10 | CDEMO-USER-ID | X(08) | DISPLAY | Signed-on user ID |
| 10 | CDEMO-USER-TYPE | X(01) | DISPLAY | User type (A=Admin, U=User) |
| 10 | CDEMO-PGM-CONTEXT | 9(01) | DISPLAY | Program context (0=enter, 1=re-enter) |
| 05 | CDEMO-CUSTOMER-INFO | | | Current customer context |
| 10 | CDEMO-CUST-ID | 9(09) | DISPLAY | Customer ID |
| 10 | CDEMO-CUST-FNAME | X(25) | DISPLAY | Customer first name |
| 10 | CDEMO-CUST-MNAME | X(25) | DISPLAY | Customer middle name |
| 10 | CDEMO-CUST-LNAME | X(25) | DISPLAY | Customer last name |
| 05 | CDEMO-ACCOUNT-INFO | | | Current account context |
| 10 | CDEMO-ACCT-ID | 9(11) | DISPLAY | Account ID |
| 10 | CDEMO-ACCT-STATUS | X(01) | DISPLAY | Account status |
| 05 | CDEMO-CARD-INFO | | | Current card context |
| 10 | CDEMO-CARD-NUM | 9(16) | DISPLAY | Card number |
| 05 | CDEMO-MORE-INFO | | | Screen navigation |
| 10 | CDEMO-LAST-MAP | X(07) | DISPLAY | Last BMS map name |
| 10 | CDEMO-LAST-MAPSET | X(07) | DISPLAY | Last BMS map set name |

---

### CC-WORK-AREAS

Defined in: CVCRD01Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | CC-WORK-AREAS | | | Common CICS work areas |
| 05 | CC-WORK-AREA | | | |
| 10 | CCARD-AID | X(5) | DISPLAY | AID key value from last CICS input |
| 10 | CCARD-NEXT-PROG | X(8) | DISPLAY | Next program to XCTL to |
| 10 | CCARD-NEXT-MAPSET | X(7) | DISPLAY | Next BMS map set |
| 10 | CCARD-NEXT-MAP | X(7) | DISPLAY | Next BMS map |
| 10 | CCARD-ERROR-MSG | X(75) | DISPLAY | Error message text |
| 10 | CCARD-RETURN-MSG | X(75) | DISPLAY | Return/status message |
| 10 | CC-ACCT-ID | X(11) | DISPLAY | Account ID (alphanumeric) |
| 10 | CC-ACCT-ID-N (REDEFINES CC-ACCT-ID) | 9(11) | DISPLAY | Account ID (numeric) |
| 10 | CC-CARD-NUM | X(16) | DISPLAY | Card number (alphanumeric) |
| 10 | CC-CARD-NUM-N (REDEFINES CC-CARD-NUM) | 9(16) | DISPLAY | Card number (numeric) |
| 10 | CC-CUST-ID | X(09) | DISPLAY | Customer ID (alphanumeric) |
| 10 | CC-CUST-ID-N (REDEFINES CC-CUST-ID) | 9(09) | DISPLAY | Customer ID (numeric) |

---

### WS-DATE-TIME

Defined in: CSDAT01Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | WS-DATE-TIME | | | Current date/time working storage |
| 05 | WS-CURDATE-DATA | | | Current date container |
| 10 | WS-CURDATE | | | Date in YYYYMMDD parts |
| 15 | WS-CURDATE-YEAR | 9(04) | DISPLAY | Current year |
| 15 | WS-CURDATE-MONTH | 9(02) | DISPLAY | Current month |
| 15 | WS-CURDATE-DAY | 9(02) | DISPLAY | Current day |
| 10 | WS-CURTIME | | | Time in HHMMSSMS parts |
| 15 | WS-CURTIME-HOURS | 9(02) | DISPLAY | Current hours |
| 15 | WS-CURTIME-MINUTE | 9(02) | DISPLAY | Current minutes |
| 15 | WS-CURTIME-SECOND | 9(02) | DISPLAY | Current seconds |
| 15 | WS-CURTIME-MILSEC | 9(02) | DISPLAY | Milliseconds |
| 05 | WS-TIMESTAMP | | | Formatted timestamp string |
| 10 | WS-TIMESTAMP-DT-YYYY | 9(04) | DISPLAY | Timestamp year |
| 10 | WS-TIMESTAMP-DT-MM | 9(02) | DISPLAY | Timestamp month |
| 10 | WS-TIMESTAMP-DT-DD | 9(02) | DISPLAY | Timestamp day |
| 10 | WS-TIMESTAMP-TM-HH | 9(02) | DISPLAY | Timestamp hours |
| 10 | WS-TIMESTAMP-TM-MM | 9(02) | DISPLAY | Timestamp minutes |
| 10 | WS-TIMESTAMP-TM-SS | 9(02) | DISPLAY | Timestamp seconds |
| 10 | WS-TIMESTAMP-TM-MS6 | 9(06) | DISPLAY | Timestamp microseconds |

---

### WS-EDIT-DATE-CCYYMMDD (Date Validation Working Storage)

Defined in: CSUTLDWY.cpy

Note: CSUTLDWY.cpy defines items at level 10 (embedded inside a parent 01-level group in the including program). COACTUPC.cbl is the primary user; the copybook is included within a larger WS group.

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 10 | WS-EDIT-DATE-CCYYMMDD | | | Date being validated (CCYYMMDD) |
| 20 | WS-EDIT-DATE-CCYY | | | Century-year portion |
| 25 | WS-EDIT-DATE-CC | X(2) | DISPLAY | Century characters |
| 25 | WS-EDIT-DATE-CC-N (REDEFINES WS-EDIT-DATE-CC) | 9(2) | DISPLAY | Century numeric; 88 THIS-CENTURY=20, LAST-CENTURY=19 |
| 25 | WS-EDIT-DATE-YY | X(2) | DISPLAY | Year characters |
| 25 | WS-EDIT-DATE-YY-N (REDEFINES WS-EDIT-DATE-YY) | 9(2) | DISPLAY | Year numeric |
| 20 | WS-EDIT-DATE-CCYY-N (REDEFINES WS-EDIT-DATE-CCYY) | 9(4) | DISPLAY | Full 4-digit year numeric |
| 20 | WS-EDIT-DATE-MM | X(2) | DISPLAY | Month characters |
| 20 | WS-EDIT-DATE-MM-N (REDEFINES WS-EDIT-DATE-MM) | 9(2) | DISPLAY | Month numeric; 88 WS-VALID-MONTH=1-12, WS-31-DAY-MONTH, WS-FEBRUARY=2 |
| 20 | WS-EDIT-DATE-DD | X(2) | DISPLAY | Day characters |
| 20 | WS-EDIT-DATE-DD-N (REDEFINES WS-EDIT-DATE-DD) | 9(2) | DISPLAY | Day numeric; 88 WS-VALID-DAY=1-31, WS-DAY-31=31, WS-DAY-30=30, WS-DAY-29=29, WS-VALID-FEB-DAY=1-28 |
| 10 | WS-EDIT-DATE-CCYYMMDD-N (REDEFINES WS-EDIT-DATE-CCYYMMDD) | 9(8) | DISPLAY | Full date as 8-digit numeric |
| 10 | WS-EDIT-DATE-BINARY | S9(9) | BINARY | Binary date for integer arithmetic |
| 10 | WS-CURRENT-DATE | | | Current system date container |
| 20 | WS-CURRENT-DATE-YYYYMMDD | X(8) | DISPLAY | Current date YYYYMMDD |
| 20 | WS-CURRENT-DATE-YYYYMMDD-N (REDEFINES WS-CURRENT-DATE-YYYYMMDD) | 9(8) | DISPLAY | Current date as 8-digit numeric |
| 20 | WS-CURRENT-DATE-BINARY | S9(9) | BINARY | Current date as binary integer |
| 10 | WS-EDIT-DATE-FLGS | | | Validation result flags; 88 WS-EDIT-DATE-IS-VALID=LOW-VALUES, WS-EDIT-DATE-IS-INVALID='000' |
| 20 | WS-EDIT-YEAR-FLG | X(1) | DISPLAY | Year validation flag; 88 FLG-YEAR-ISVALID=LOW-VALUES, FLG-YEAR-NOT-OK='0', FLG-YEAR-BLANK='B' |
| 20 | WS-EDIT-MONTH | X(1) | DISPLAY | Month validation flag; 88 FLG-MONTH-ISVALID=LOW-VALUES, FLG-MONTH-NOT-OK='0', FLG-MONTH-BLANK='B' |
| 20 | WS-EDIT-DAY | X(1) | DISPLAY | Day validation flag; 88 FLG-DAY-ISVALID=LOW-VALUES, FLG-DAY-NOT-OK='0', FLG-DAY-BLANK='B' |
| 10 | WS-DATE-FORMAT | X(08) | DISPLAY | Format string (VALUE 'YYYYMMDD') |
| 10 | WS-DATE-VALIDATION-RESULT | | | Result of CEEDAYS validation call |
| 20 | WS-SEVERITY | X(04) | DISPLAY | Severity code |
| 20 | WS-SEVERITY-N (REDEFINES WS-SEVERITY) | 9(4) | DISPLAY | Severity numeric |
| 20 | FILLER | X(11) | | Literal 'Mesg Code:' |
| 20 | WS-MSG-NO | X(04) | DISPLAY | Message number |
| 20 | WS-MSG-NO-N (REDEFINES WS-MSG-NO) | 9(4) | DISPLAY | Message number numeric |
| 20 | FILLER | X(01) | | Space |
| 20 | WS-RESULT | X(15) | DISPLAY | Result text |
| 20 | FILLER | X(01) | | Space |
| 20 | FILLER | X(09) | | Literal 'TstDate:' |
| 20 | WS-DATE | X(10) | DISPLAY | Date being tested |
| 20 | FILLER | X(01) | | Space |
| 20 | FILLER | X(10) | | Literal 'Mask used:' |
| 20 | WS-DATE-FMT | X(10) | DISPLAY | Format mask used |
| 20 | FILLER | X(01) | | Space |
| 20 | FILLER | X(03) | | Spaces |

---

### CCDA-SCREEN-TITLE

Defined in: COTTL01Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | CCDA-SCREEN-TITLE | | | Application title strings displayed on all screens |
| 05 | CCDA-TITLE01 | X(40) | DISPLAY | Line 1 title: 'AWS Mainframe Modernization' |
| 05 | CCDA-TITLE02 | X(40) | DISPLAY | Line 2 title: 'CardDemo' |
| 05 | CCDA-THANK-YOU | X(40) | DISPLAY | Sign-off message |

---

### CCDA-COMMON-MESSAGES

Defined in: CSMSG01Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | CCDA-COMMON-MESSAGES | | | Standard message literals for all online programs |
| 05 | CCDA-MSG-THANK-YOU | X(50) | DISPLAY | 'Thank you for using CardDemo application...' |
| 05 | CCDA-MSG-INVALID-KEY | X(50) | DISPLAY | 'Invalid key pressed. Please see below...' |

---

### ABEND-DATA

Defined in: CSMSG02Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | ABEND-DATA | | | Abend/error information structure |
| 05 | ABEND-CODE | X(4) | DISPLAY | Abend code |
| 05 | ABEND-CULPRIT | X(8) | DISPLAY | Program causing abend |
| 05 | ABEND-REASON | X(50) | DISPLAY | Reason description |
| 05 | ABEND-MSG | X(72) | DISPLAY | Full error message |

---

### EXPORT-RECORD

Defined in: CVEXPORT.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | EXPORT-RECORD | | | Multi-type export file record (RECLN 500) |
| 05 | EXPORT-REC-TYPE | X(1) | DISPLAY | Record type discriminator ('C'=customer, 'A'=account, 'T'=transaction, 'X'=xref, 'K'=card) |
| 05 | EXPORT-TIMESTAMP | X(26) | DISPLAY | Export timestamp |
| 05 | EXPORT-TIMESTAMP-R (REDEFINES EXPORT-TIMESTAMP) | | | Timestamp sub-fields |
| 10 | EXPORT-DATE | X(10) | DISPLAY | Date portion |
| 10 | EXPORT-DATE-TIME-SEP | X(1) | DISPLAY | Separator character |
| 10 | EXPORT-TIME | X(15) | DISPLAY | Time portion |
| 05 | EXPORT-SEQUENCE-NUM | 9(9) | COMP | Sequence number (binary 4 bytes) |
| 05 | EXPORT-BRANCH-ID | X(4) | DISPLAY | Branch identifier |
| 05 | EXPORT-REGION-CODE | X(5) | DISPLAY | Region code |
| 05 | EXPORT-RECORD-DATA | X(460) | DISPLAY | Record payload (varies by type) |
| 05 | EXPORT-CUSTOMER-DATA (REDEFINES EXPORT-RECORD-DATA) | | | Customer record payload (type 'C') |
| 10 | EXP-CUST-ID | 9(09) | COMP | Customer ID (binary) |
| 10 | EXP-CUST-FIRST-NAME | X(25) | DISPLAY | First name |
| 10 | EXP-CUST-MIDDLE-NAME | X(25) | DISPLAY | Middle name |
| 10 | EXP-CUST-LAST-NAME | X(25) | DISPLAY | Last name |
| 10 | EXP-CUST-ADDR-LINES OCCURS 3 TIMES | | | Address lines array |
| 15 | EXP-CUST-ADDR-LINE | X(50) | DISPLAY | One address line (3 x 50 = 150 bytes) |
| 10 | EXP-CUST-ADDR-STATE-CD | X(02) | DISPLAY | State code |
| 10 | EXP-CUST-ADDR-COUNTRY-CD | X(03) | DISPLAY | Country code |
| 10 | EXP-CUST-ADDR-ZIP | X(10) | DISPLAY | ZIP code |
| 10 | EXP-CUST-PHONE-NUMS OCCURS 2 TIMES | | | Phone numbers array |
| 15 | EXP-CUST-PHONE-NUM | X(15) | DISPLAY | One phone number (2 x 15 = 30 bytes) |
| 10 | EXP-CUST-SSN | 9(09) | DISPLAY | Social security number |
| 10 | EXP-CUST-GOVT-ISSUED-ID | X(20) | DISPLAY | Government-issued ID |
| 10 | EXP-CUST-DOB-YYYY-MM-DD | X(10) | DISPLAY | Date of birth |
| 10 | EXP-CUST-EFT-ACCOUNT-ID | X(10) | DISPLAY | EFT account ID |
| 10 | EXP-CUST-PRI-CARD-HOLDER-IND | X(01) | DISPLAY | Primary card holder indicator |
| 10 | EXP-CUST-FICO-CREDIT-SCORE | 9(03) | COMP-3 | FICO score (packed decimal) |
| 10 | FILLER | X(134) | | Reserved/padding |
| 05 | EXPORT-ACCOUNT-DATA (REDEFINES EXPORT-RECORD-DATA) | | | Account record payload (type 'A') |
| 10 | EXP-ACCT-ID | 9(11) | DISPLAY | Account ID |
| 10 | EXP-ACCT-ACTIVE-STATUS | X(01) | DISPLAY | Active status (Y/N) |
| 10 | EXP-ACCT-CURR-BAL | S9(10)V99 | COMP-3 | Current balance (packed decimal) |
| 10 | EXP-ACCT-CREDIT-LIMIT | S9(10)V99 | DISPLAY | Credit limit |
| 10 | EXP-ACCT-CASH-CREDIT-LIMIT | S9(10)V99 | COMP-3 | Cash credit limit (packed) |
| 10 | EXP-ACCT-OPEN-DATE | X(10) | DISPLAY | Open date |
| 10 | EXP-ACCT-EXPIRAION-DATE | X(10) | DISPLAY | Expiration date (typo in source) |
| 10 | EXP-ACCT-REISSUE-DATE | X(10) | DISPLAY | Reissue date |
| 10 | EXP-ACCT-CURR-CYC-CREDIT | S9(10)V99 | DISPLAY | Cycle credits |
| 10 | EXP-ACCT-CURR-CYC-DEBIT | S9(10)V99 | COMP | Cycle debits (binary) |
| 10 | EXP-ACCT-ADDR-ZIP | X(10) | DISPLAY | Billing ZIP |
| 10 | EXP-ACCT-GROUP-ID | X(10) | DISPLAY | Group ID |
| 10 | FILLER | X(352) | | Reserved/padding |
| 05 | EXPORT-TRANSACTION-DATA (REDEFINES EXPORT-RECORD-DATA) | | | Transaction record payload (type 'T') |
| 10 | EXP-TRAN-ID | X(16) | DISPLAY | Transaction ID |
| 10 | EXP-TRAN-TYPE-CD | X(02) | DISPLAY | Transaction type code |
| 10 | EXP-TRAN-CAT-CD | 9(04) | DISPLAY | Category code |
| 10 | EXP-TRAN-SOURCE | X(10) | DISPLAY | Source system |
| 10 | EXP-TRAN-DESC | X(100) | DISPLAY | Description |
| 10 | EXP-TRAN-AMT | S9(09)V99 | COMP-3 | Amount (packed decimal) |
| 10 | EXP-TRAN-MERCHANT-ID | 9(09) | COMP | Merchant ID (binary) |
| 10 | EXP-TRAN-MERCHANT-NAME | X(50) | DISPLAY | Merchant name |
| 10 | EXP-TRAN-MERCHANT-CITY | X(50) | DISPLAY | Merchant city |
| 10 | EXP-TRAN-MERCHANT-ZIP | X(10) | DISPLAY | Merchant ZIP |
| 10 | EXP-TRAN-CARD-NUM | X(16) | DISPLAY | Card number |
| 10 | EXP-TRAN-ORIG-TS | X(26) | DISPLAY | Origination timestamp |
| 10 | EXP-TRAN-PROC-TS | X(26) | DISPLAY | Processing timestamp |
| 10 | FILLER | X(140) | | Reserved/padding |
| 05 | EXPORT-CARD-XREF-DATA (REDEFINES EXPORT-RECORD-DATA) | | | Card cross-reference payload (type 'X') |
| 10 | EXP-XREF-CARD-NUM | X(16) | DISPLAY | Card number |
| 10 | EXP-XREF-CUST-ID | 9(09) | DISPLAY | Customer ID |
| 10 | EXP-XREF-ACCT-ID | 9(11) | COMP | Account ID (binary) |
| 10 | FILLER | X(427) | | Reserved/padding |
| 05 | EXPORT-CARD-DATA (REDEFINES EXPORT-RECORD-DATA) | | | Card record payload (type 'K') |
| 10 | EXP-CARD-NUM | X(16) | DISPLAY | Card number |
| 10 | EXP-CARD-ACCT-ID | 9(11) | COMP | Account ID (binary) |
| 10 | EXP-CARD-CVV-CD | 9(03) | COMP | CVV code (binary) |
| 10 | EXP-CARD-EMBOSSED-NAME | X(50) | DISPLAY | Embossed name |
| 10 | EXP-CARD-EXPIRAION-DATE | X(10) | DISPLAY | Expiration date (typo in source) |
| 10 | EXP-CARD-ACTIVE-STATUS | X(01) | DISPLAY | Active status |
| 10 | FILLER | X(373) | | Reserved/padding |

> Note: Corrected in iteration 5. The prior draft listed only a subset of fields for each REDEFINES variant. All sub-fields now sourced directly from CVEXPORT.cpy. Record type codes used in EXPORT-REC-TYPE: 'C'=customer, 'A'=account, 'T'=transaction, 'X'=card cross-reference, 'K'=card. The inventory copybook list used type code 'D' for card data, but the source shows 'K'.

---

### CODATECN-REC

Defined in: CODATECN.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | CODATECN-REC | | | Date conversion utility interface record |
| 05 | CODATECN-IN-REC | | | Input record |
| 10 | CODATECN-TYPE | X | DISPLAY | Input format type (1=YYYYMMDD, 2=YYYY-MM-DD) |
| 10 | CODATECN-INP-DATE | X(20) | DISPLAY | Input date string |
| 05 | CODATECN-OUT-REC | | | Output record |
| 10 | CODATECN-OUTTYPE | X | DISPLAY | Output format type |
| 10 | CODATECN-0UT-DATE | X(20) | DISPLAY | Output date string |
| 05 | CODATECN-ERROR-MSG | X(38) | DISPLAY | Conversion error message |

---

### CARDDEMO-MAIN-MENU-OPTIONS

Defined in: COMEN02Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | CARDDEMO-MAIN-MENU-OPTIONS | | | Main menu configuration table |
| 05 | CDEMO-MENU-OPT-COUNT | 9(02) | DISPLAY | Number of menu options (VALUE 11) |
| 05 | CDEMO-MENU-OPTIONS-DATA | | | Raw data for menu options (FILLER entries) |
| 05 | CDEMO-MENU-OPTIONS (REDEFINES CDEMO-MENU-OPTIONS-DATA) | | | Structured access overlay |
| 10 | CDEMO-MENU-OPT OCCURS 12 TIMES | | | Each menu option entry |
| 15 | CDEMO-MENU-OPT-NUM | 9(02) | DISPLAY | Menu option number |
| 15 | CDEMO-MENU-OPT-NAME | X(35) | DISPLAY | Menu option display name |
| 15 | CDEMO-MENU-OPT-PGMNAME | X(08) | DISPLAY | Program to invoke |
| 15 | CDEMO-MENU-OPT-USRTYPE | X(01) | DISPLAY | Required user type (U=User, A=Admin) |

**Menu options defined (all type 'U'):**

| Option | Name | Program |
| ------ | ---- | ------- |
| 1 | Account View | COACTVWC |
| 2 | Account Update | COACTUPC |
| 3 | Credit Card List | COCRDLIC |
| 4 | Credit Card View | COCRDSLC |
| 5 | Credit Card Update | COCRDUPC |
| 6 | Transaction List | COTRN00C |
| 7 | Transaction View | COTRN01C |
| 8 | Transaction Add | COTRN02C |
| 9 | Transaction Reports | CORPT00C |
| 10 | Bill Payment | COBIL00C |
| 11 | Pending Authorization View | COPAUS0C |

> Note (iteration 5 finding): Menu option 11 references program `COPAUS0C` (Pending Authorization View). This program is NOT present in the source directory and was not listed in the program inventory. It appears to be a planned but unimplemented feature.

---

### CARDDEMO-ADMIN-MENU-OPTIONS

Defined in: COADM02Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | CARDDEMO-ADMIN-MENU-OPTIONS | | | Admin menu configuration table |
| 05 | CDEMO-ADMIN-OPT-COUNT | 9(02) | DISPLAY | Number of admin options (VALUE 6; commented-out version VALUE 4) |
| 05 | CDEMO-ADMIN-OPTIONS-DATA | | | Raw data for admin options (FILLER entries) |
| 05 | CDEMO-ADMIN-OPTIONS (REDEFINES CDEMO-ADMIN-OPTIONS-DATA) | | | Structured access overlay |
| 10 | CDEMO-ADMIN-OPT OCCURS 9 TIMES | | | Each admin option entry |
| 15 | CDEMO-ADMIN-OPT-NUM | 9(02) | DISPLAY | Option number |
| 15 | CDEMO-ADMIN-OPT-NAME | X(35) | DISPLAY | Option display name |
| 15 | CDEMO-ADMIN-OPT-PGMNAME | X(08) | DISPLAY | Program to invoke |

> Note: Options 5 and 6 reference DB2 programs COTRTLIC (Transaction Type List/Update) and COTRTUPC (Transaction Type Maintenance), which are not present in the source directory. These were added for a planned DB2 release.

---

### ACUP-UPDATE-SCREENS (COACTUPC Working Storage)

Defined in: COACTUPC.cbl WORKING-STORAGE

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | WS-THIS-PROGCOMMAREA | | | COACTUPC program commarea |
| 05 | ACCT-UPDATE-SCREEN-DATA | | | Screen state tracking |
| 10 | ACUP-CHANGE-ACTION | X(1) | DISPLAY | Pending action code (S/E/N/C/L/F) |
| 05 | ACUP-OLD-DETAILS | | | Pre-update values for comparison |
| 10 | ACUP-OLD-ACCT-DATA | | | Old account fields (mirrors ACCOUNT-RECORD) |
| 10 | ACUP-OLD-CUST-DATA | | | Old customer fields (mirrors CUSTOMER-RECORD) |
| 05 | ACUP-NEW-DETAILS | | | Post-update values entered by user |
| 10 | ACUP-NEW-ACCT-DATA | | | New account fields |
| 10 | ACUP-NEW-CUST-DATA | | | New customer fields |

---

### CSUTLDTC LINKAGE SECTION

Defined in: CSUTLDTC.cbl LINKAGE SECTION

Called by: COACTUPC (via CSUTLDPY / EDIT-DATE-LE), CORPT00C (direct CALL)

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | LS-DATE | X(10) | DISPLAY | Input date string to validate |
| 01 | LS-DATE-FORMAT | X(10) | DISPLAY | Format descriptor (e.g., 'YYYYMMDD') |
| 01 | LS-RESULT | X(80) | DISPLAY | Validation result message returned to caller |

CSUTLDTC internally calls LE service CEEDAYS to validate dates. The working storage includes:

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | WS-DATE-TO-TEST | | | Variable-length string passed to CEEDAYS |
| 02 | Vstring-length | S9(4) | BINARY | Length of date string |
| 02 | Vstring-text | OCCURS 0-256 TIMES | | Date characters |
| 01 | OUTPUT-LILLIAN | S9(9) | BINARY | Lillian date returned by CEEDAYS |
| 01 | FEEDBACK-CODE | | | CEEDAYS API feedback token |
| 02 | SEVERITY | S9(4) | BINARY | Error severity (0=valid) |
| 02 | MSG-NO | S9(4) | BINARY | Error message number |

---

### CORPT00C Report Submission Structures

Defined in: CORPT00C.cbl WORKING-STORAGE

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | JOB-DATA | | | Inline JCL for batch report submission |
| 02 | JOB-DATA-1 | | | JCL lines as literal FILLER fields |
| 05 | JOB-LINES (via JOB-DATA-2 REDEFINES) OCCURS 1000 TIMES | X(80) | DISPLAY | Each JCL record line (80 bytes) |
| 01 | CSUTLDTC-PARM | | | Parameter block for CSUTLDTC date validation call |
| 05 | CSUTLDTC-DATE | X(10) | DISPLAY | Date to validate |
| 05 | CSUTLDTC-DATE-FORMAT | X(10) | DISPLAY | Format string |
| 05 | CSUTLDTC-RESULT | | | Result from CSUTLDTC |
| 10 | CSUTLDTC-RESULT-SEV-CD | X(04) | DISPLAY | Severity code |
| 10 | CSUTLDTC-RESULT-MSG-NUM | X(04) | DISPLAY | Message number |
| 10 | CSUTLDTC-RESULT-MSG | X(61) | DISPLAY | Result message text |

---

### TRANSACTION-DETAIL-REPORT

Defined in: CVTRA07Y.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | REPORT-NAME-HEADER | | | Report header line |
| 05 | REPT-SHORT-NAME | X(38) | DISPLAY | Short report name (VALUE 'DALYREPT') |
| 05 | REPT-LONG-NAME | X(41) | DISPLAY | Long report name (VALUE 'Daily Transaction Report') |
| 05 | REPT-DATE-HEADER | X(12) | DISPLAY | Date range label (VALUE 'Date Range: ') |
| 05 | REPT-START-DATE | X(10) | DISPLAY | Report date range start (YYYY-MM-DD) |
| 05 | FILLER | X(04) | DISPLAY | Separator literal ' to ' |
| 05 | REPT-END-DATE | X(10) | DISPLAY | Report date range end (YYYY-MM-DD) |
| 01 | TRANSACTION-DETAIL-REPORT | | | Detail report line layout |
| 05 | TRAN-REPORT-TRANS-ID | X(16) | DISPLAY | Transaction ID column |
| 05 | FILLER | X(01) | | Space separator |
| 05 | TRAN-REPORT-ACCOUNT-ID | X(11) | DISPLAY | Account ID column |
| 05 | FILLER | X(01) | | Space separator |
| 05 | TRAN-REPORT-TYPE-CD | X(02) | DISPLAY | Type code column |
| 05 | FILLER | X(01) | | Dash separator |
| 05 | TRAN-REPORT-TYPE-DESC | X(15) | DISPLAY | Type description column |
| 05 | FILLER | X(01) | | Space separator |
| 05 | TRAN-REPORT-CAT-CD | 9(04) | DISPLAY | Category code column |
| 05 | FILLER | X(01) | | Dash separator |
| 05 | TRAN-REPORT-CAT-DESC | X(29) | DISPLAY | Category description column |
| 05 | FILLER | X(01) | | Space separator |
| 05 | TRAN-REPORT-SOURCE | X(10) | DISPLAY | Source column |
| 05 | FILLER | X(04) | | Spaces |
| 05 | TRAN-REPORT-AMT | -ZZZ,ZZZ,ZZZ.ZZ | DISPLAY | Amount column (edited numeric) |
| 05 | FILLER | X(02) | | Trailing spaces |
| 01 | TRANSACTION-HEADER-1 | | | Column header line (printable labels) |
| 05 | FILLER | X(17) | DISPLAY | 'Transaction ID' label |
| 05 | FILLER | X(12) | DISPLAY | 'Account ID' label |
| 05 | FILLER | X(19) | DISPLAY | 'Transaction Type' label |
| 05 | FILLER | X(35) | DISPLAY | 'Tran Category' label |
| 05 | FILLER | X(14) | DISPLAY | 'Tran Source' label |
| 05 | FILLER | X(01) | | Space |
| 05 | FILLER | X(16) | DISPLAY | '        Amount' label |
| 01 | TRANSACTION-HEADER-2 | X(133) | DISPLAY | Separator line (VALUE ALL '-') |
| 01 | REPORT-PAGE-TOTALS | | | Page total line |
| 05 | FILLER | X(11) | DISPLAY | 'Page Total' label |
| 05 | FILLER | X(86) | DISPLAY | Dot-fill (VALUE ALL '.') |
| 05 | REPT-PAGE-TOTAL | +ZZZ,ZZZ,ZZZ.ZZ | DISPLAY | Page total amount (signed edited) |
| 01 | REPORT-ACCOUNT-TOTALS | | | Account total line |
| 05 | FILLER | X(13) | DISPLAY | 'Account Total' label |
| 05 | FILLER | X(84) | DISPLAY | Dot-fill (VALUE ALL '.') |
| 05 | REPT-ACCOUNT-TOTAL | +ZZZ,ZZZ,ZZZ.ZZ | DISPLAY | Account total amount (signed edited) |
| 01 | REPORT-GRAND-TOTALS | | | Grand total line |
| 05 | FILLER | X(11) | DISPLAY | 'Grand Total' label |
| 05 | FILLER | X(86) | DISPLAY | Dot-fill (VALUE ALL '.') |
| 05 | REPT-GRAND-TOTAL | +ZZZ,ZZZ,ZZZ.ZZ | DISPLAY | Grand total amount (signed edited) |

> Note (iteration 5 correction): Prior draft omitted REPT-DATE-HEADER, FILLER separator, and the three report header/separator structures (TRANSACTION-HEADER-1, TRANSACTION-HEADER-2). All now added from direct source read of CVTRA07Y.cpy.

---

### WS-LOOKUP-CODES (Phone and State Validation)

Defined in: CSLKPCDY.cpy

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | WS-US-PHONE-AREA-CODE-TO-EDIT | X(3) | DISPLAY | Area code being validated |

CSLKPCDY.cpy is a large (>400 line) lookup table containing:
- North American phone area codes (from NANPA registry)
- US state codes (2-letter abbreviations)
- US state + first-2-of-ZIP validation pairs

Used only by COACTUPC for field validation of phone numbers, state codes, and ZIP codes on the account update screen.

---

### UNUSED-DATA

Defined in: UNUSED1Y.cpy

> Note: This copybook is not referenced by any active program in the source set. It mirrors the SEC-USER-DATA layout (same field widths, 80 bytes total) but with generic UNUSED- prefix names.

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | UNUSED-DATA | | | Orphan data structure -- not used by any active program |
| 05 | UNUSED-ID | X(08) | DISPLAY | Placeholder ID field (mirrors SEC-USR-ID) |
| 05 | UNUSED-FNAME | X(20) | DISPLAY | Placeholder first name (mirrors SEC-USR-FNAME) |
| 05 | UNUSED-LNAME | X(20) | DISPLAY | Placeholder last name (mirrors SEC-USR-LNAME) |
| 05 | UNUSED-PWD | X(08) | DISPLAY | Placeholder password (mirrors SEC-USR-PWD) |
| 05 | UNUSED-TYPE | X(01) | DISPLAY | Placeholder type (mirrors SEC-USR-TYPE) |
| 05 | UNUSED-FILLER | X(23) | | Reserved/padding to 80 bytes |

---

### COBSWAIT Working Storage

Defined in: COBSWAIT.cbl WORKING-STORAGE

A simple utility program that calls the MVS WAIT service. Has no file I/O and no copybooks.

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | MVSWAIT-TIME | 9(8) | COMP | Wait duration in centiseconds (passed to MVSWAIT) |
| 01 | PARM-VALUE | X(8) | DISPLAY | Raw value read from SYSIN; moved to MVSWAIT-TIME |

---

### CBSTM03A Working Storage

Defined in: CBSTM03A.CBL WORKING-STORAGE

Statement generation program that produces both plain-text and HTML account statements. Uses CBSTM03B as a file I/O subroutine.

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | COMP-VARIABLES | | COMP | Binary counter group |
| 05 | CR-CNT | S9(4) | COMP | Card record count |
| 05 | TR-CNT | S9(4) | COMP | Transaction record count |
| 05 | CR-JMP | S9(4) | COMP | Card table jump index |
| 05 | TR-JMP | S9(4) | COMP | Transaction table jump index |
| 01 | COMP3-VARIABLES | | COMP-3 | Packed decimal group |
| 05 | WS-TOTAL-AMT | S9(9)V99 | COMP-3 | Running total transaction amount |
| 01 | MISC-VARIABLES | | | Miscellaneous working storage |
| 05 | WS-FL-DD | X(8) | DISPLAY | File DD name passed to CBSTM03B (default 'TRNXFILE') |
| 05 | WS-TRN-AMT | S9(9)V99 | DISPLAY | Current transaction amount |
| 05 | WS-SAVE-CARD | X(16) | DISPLAY | Saved card number for group break detection |
| 05 | END-OF-FILE | X(01) | DISPLAY | EOF flag (Y/N) |
| 01 | WS-M03B-AREA | | | Parameter area passed to CBSTM03B subroutine |
| 05 | WS-M03B-DD | X(08) | DISPLAY | DD name for file operation |
| 05 | WS-M03B-OPER | X(01) | DISPLAY | Operation code; 88 M03B-OPEN='O', M03B-CLOSE='C', M03B-READ='R', M03B-READ-K='K', M03B-WRITE='W', M03B-REWRITE='Z' |
| 05 | WS-M03B-RC | X(02) | DISPLAY | Return code from file operation |
| 05 | WS-M03B-KEY | X(25) | DISPLAY | Key for keyed READ (CARD-NUM 16 + TRAN-ID 16 = 32, truncated to 25 for partial key browse) |
| 05 | WS-M03B-KEY-LN | S9(4) | DISPLAY | Effective length of key |
| 05 | WS-M03B-FLDT | X(1000) | DISPLAY | File data area returned from read operations |
| 01 | WS-TRNX-TABLE | | | In-memory transaction table (51 cards x 10 transactions) |
| 05 | WS-CARD-TBL OCCURS 51 TIMES | | | One card entry |
| 10 | WS-CARD-NUM | X(16) | DISPLAY | Card number |
| 10 | WS-TRAN-TBL OCCURS 10 TIMES | | | Up to 10 transactions per card |
| 15 | WS-TRAN-NUM | X(16) | DISPLAY | Transaction ID |
| 15 | WS-TRAN-REST | X(318) | DISPLAY | Remaining transaction data |
| 01 | WS-TRN-TBL-CNTR | | | Transaction count table (parallel to WS-TRNX-TABLE) |
| 05 | WS-TRN-TBL-CTR OCCURS 51 TIMES | | | Count per card |
| 10 | WS-TRCT | S9(4) | COMP | Transaction count for this card slot |
| 01 | PSAPTR | POINTER | | Pointer to PSA (Prefixed Save Area) for TIOT access |
| 01 | BUMP-TIOT | S9(08) | BINARY | Integer used to walk TIOT entries |
| 01 | TIOT-INDEX (REDEFINES BUMP-TIOT) | POINTER | | Pointer redefine for TIOT navigation |

---

### CBSTM03A LINKAGE SECTION (MVS Control Block Access)

Defined in: CBSTM03A.CBL LINKAGE SECTION

CBSTM03A directly accesses MVS control blocks via LINKAGE SECTION pointers to enumerate open DD names from the TIOT (Task I/O Table). This non-standard technique is used to discover at runtime which DD names are available for statement output.

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | ALIGN-PSA | 9(16) | BINARY | PSA base address alignment field |
| 01 | PSA-BLOCK | | | Prefixed Save Area block |
| 05 | FILLER | X(536) | | Padding to TCB pointer offset |
| 05 | TCB-POINT | POINTER | | Pointer to current Task Control Block |
| 01 | TCB-BLOCK | | | Task Control Block |
| 05 | FILLER | X(12) | | Padding to TIOT pointer offset |
| 05 | TIOT-POINT | POINTER | | Pointer to TIOT |
| 01 | TIOT-BLOCK | | | Task I/O Table header |
| 05 | TIOTNJOB | X(08) | DISPLAY | Job name |
| 05 | TIOTJSTP | X(08) | DISPLAY | Job step name |
| 05 | TIOTPSTP | X(08) | DISPLAY | Procedure step name |
| 01 | TIOT-ENTRY | | | Individual TIOT entry (DD name slot) |
| 05 | TIOT-SEG | | | TIOT entry segment |
| 10 | TIO-LEN | X(01) | DISPLAY | Entry length |
| 10 | FILLER | X(03) | | Reserved |
| 10 | TIOCDDNM | X(08) | DISPLAY | DD name for this allocation |
| 10 | FILLER | X(05) | | Reserved |
| 10 | UCB-ADDR | X(03) | DISPLAY | UCB address; 88 NULL-UCB=LOW-VALUES (end marker) |
| 05 | FILLER | X(04) | | Reserved; 88 END-OF-TIOT=LOW-VALUES |

---

### CBSTM03B LINKAGE SECTION

Defined in: CBSTM03B.CBL LINKAGE SECTION

Called by: CBSTM03A (via CALL 'CBSTM03B' USING WS-M03B-AREA)

| Level | Name | PIC | Usage | Description |
| ----- | ---- | --- | ----- | ----------- |
| 01 | LK-M03B-AREA | | | File operation parameter block |
| 05 | LK-M03B-DD | X(08) | DISPLAY | DD name of file to operate on |
| 05 | LK-M03B-OPER | X(01) | DISPLAY | Operation code; 88 M03B-OPEN='O', M03B-CLOSE='C', M03B-READ='R', M03B-READ-K='K', M03B-WRITE='W', M03B-REWRITE='Z' |
| 05 | LK-M03B-RC | X(02) | DISPLAY | File status code returned to caller |
| 05 | LK-M03B-KEY | X(25) | DISPLAY | Search key for keyed READ |
| 05 | LK-M03B-KEY-LN | S9(4) | DISPLAY | Key length |
| 05 | LK-M03B-FLDT | X(1000) | DISPLAY | File data area (record read into / written from here) |

---

### BMS Screen Map Structures (Selected)

BMS-generated copybooks follow a standard pattern. Each copybook defines an input map (suffix `I`) and an output map (suffix `O` via REDEFINES). Each field has length (`L` suffix), flag (`F` suffix), and attribute (`A` suffix) companions.

#### COSGN0AI / COSGN0AO (COSGN00.CPY - Signon Screen)

| Field | PIC | Description |
| ----- | --- | ----------- |
| TRNNAMEI | X(4) | Transaction name (display) |
| TITLE01I | X(40) | Screen title line 1 |
| CURDATEI | X(8) | Current date display |
| PGMNAMEI | X(8) | Program name display |
| TITLE02I | X(40) | Screen title line 2 |
| CURTIMEI | X(9) | Current time display |
| APPLIDI | X(8) | Application ID display |
| SYSIDI | X(8) | System ID display |
| USERIDI | X(8) | User ID input field |
| PASSWDI | X(8) | Password input field |
| ERRMSGI | X(78) | Error message display |

#### COMEN1AI / COMEN1AO (COMEN01.CPY - Main Menu Screen)

| Field | PIC | Description |
| ----- | --- | ----------- |
| OPTN001I .. OPTN012I | X(40) | Menu option text lines 1-12 |
| OPTIONI | X(2) | User's selected option number |
| ERRMSGI | X(78) | Error message display |

#### CORPT0AI / CORPT0AO (CORPT00.CPY - Report Request Screen)

| Field | PIC | Description |
| ----- | --- | ----------- |
| MONTHLYI | X(1) | Monthly report flag |
| YEARLYI | X(1) | Yearly report flag |
| CUSTOMI | X(1) | Custom date range flag |
| SDTMMI/SDTDDI/SDTYYYYI | X(2)/X(2)/X(4) | Start date components (MM/DD/YYYY) |
| EDTMMI/EDTDDI/EDTYYYYI | X(2)/X(2)/X(4) | End date components (MM/DD/YYYY) |
| CONFIRMI | X(1) | Confirm submission flag |
| ERRMSGI | X(78) | Error message display |

---

## Shared Data Items

Data items defined in copybooks and used across multiple programs:

| Data Item | Defined In | Used By Programs | PIC | Description |
| --------- | ---------- | ---------------- | --- | ----------- |
| CUSTOMER-RECORD | CVCUS01Y.cpy | CBTRN01C, CBCUS01C, COACTUPC, COACTVWC, COUSR02C, CBEXPORT, CBIMPORT | 9(09)+X fields | Customer master entity |
| CUSTOMER-RECORD | CUSTREC.cpy | CBSTM03A | 9(09)+X fields | Alternate customer layout (DOB field name differs); used for statement generation |
| ACCOUNT-RECORD | CVACT01Y.cpy | CBACT01C, CBACT04C, CBTRN01C, CBTRN02C, COACTUPC, COACTVWC, COBIL00C, COTRN02C, CBEXPORT, CBIMPORT, CBSTM03A | 9(11)+S9 fields | Account master entity |
| CARD-RECORD | CVACT02Y.cpy | CBACT02C, CBTRN01C, COACTVWC, COCRDLIC, COCRDSLC, COCRDUPC, CBEXPORT, CBIMPORT | X(16)+9 fields | Credit card entity |
| CARD-XREF-RECORD | CVACT03Y.cpy | CBACT03C, CBTRN01C, CBTRN02C, CBTRN03C, CBACT04C, COACTUPC, COACTVWC, COBIL00C, COTRN02C, CBEXPORT, CBIMPORT, COCRDLIC, CBSTM03A | X(16)+9 fields | Card-to-account cross-reference |
| TRAN-RECORD | CVTRA05Y.cpy | CBTRN02C, CBACT04C, CBTRN03C, COTRN00C, COTRN01C, COTRN02C, COBIL00C, CORPT00C, CBEXPORT, CBIMPORT | X(16)+S9 fields | Transaction master entity |
| TRNX-RECORD | COSTM01.CPY | CBSTM03A | X(16)+X(16) key + S9 fields | Transaction record variant with composite card+tran key for TRNXFILE VSAM |
| DALYTRAN-RECORD | CVTRA06Y.cpy | CBTRN01C, CBTRN02C | X(16)+S9 fields | Daily transaction batch input |
| TRAN-CAT-BAL-RECORD | CVTRA01Y.cpy | CBTRN02C, CBACT04C | 9(11)+X+9 fields | Transaction category balance |
| DIS-GROUP-RECORD | CVTRA02Y.cpy | CBACT04C | X(10)+X+9 fields | Disclosure group / interest rates |
| TRAN-TYPE-RECORD | CVTRA03Y.cpy | CBTRN03C | X(02)+X(50) | Transaction type reference |
| TRAN-CAT-RECORD | CVTRA04Y.cpy | CBTRN03C | X(02)+9(04)+X | Transaction category reference |
| SEC-USER-DATA | CSUSR01Y.cpy | COSGN00C, COUSR00C, COUSR01C, COUSR02C, COUSR03C, COADM01C, COACTUPC, COACTVWC, COCRDLIC, COCRDSLC, COCRDUPC, COMEN01C | X(08)+X(20)+X | User security record |
| CARDDEMO-COMMAREA | COCOM01Y.cpy | All online CICS programs | Various | Session state / navigation |
| CC-WORK-AREAS | CVCRD01Y.cpy | COACTUPC, COACTVWC, COCRDLIC, COCRDSLC, COCRDUPC | Various | Common CICS screen work areas |
| WS-DATE-TIME | CSDAT01Y.cpy | COADM01C, COACTUPC, COACTVWC, COBIL00C, COCRDSLC, COCRDUPC, COMEN01C, CORPT00C, COSGN00C, COTRN00C, COTRN01C, COTRN02C, COUSR00C, COUSR01C, COUSR02C, COUSR03C | 9(04)/9(02) | Current date/time |
| ABEND-DATA | CSMSG02Y.cpy | COACTUPC, COACTVWC, COCRDSLC, COCRDUPC | X(4)+X(8)+X fields | CICS abend/error handling |
| CCDA-SCREEN-TITLE | COTTL01Y.cpy | All online CICS programs | X(40) | Application title displayed on every screen |
| CCDA-COMMON-MESSAGES | CSMSG01Y.cpy | All online CICS programs | X(50) | Standard message literals |
| WS-EDIT-DATE-CCYYMMDD | CSUTLDWY.cpy | COACTUPC | Various | Date validation working storage fields |
| EXPORT-RECORD | CVEXPORT.cpy | CBEXPORT, CBIMPORT | X(460) payload | Multi-type export/import file record |
| UNUSED-DATA | UNUSED1Y.cpy | (none - orphan copybook) | X fields | Mirrors SEC-USER-DATA; unused |

---

## Procedure Division Copybooks (No Data Definitions)

The following copybooks contain PROCEDURE DIVISION code only and define no data items:

| Copybook | Purpose |
| -------- | ------- |
| CSSTRPFY.cpy | YYYY-STORE-PFKEY paragraph -- maps EIBAID to CCARD-AID-xxx 88-level condition names in CVCRD01Y |
| CSSETATY.cpy | Inline condition snippet -- sets BMS field colour to red and inserts '*' marker when a field fails validation (uses parameterised names via copybook substitution) |
| CSUTLDPY.cpy | Date validation paragraphs (EDIT-DATE-CCYYMMDD, EDIT-YEAR-CCYY, EDIT-MONTH, EDIT-DAY, EDIT-DAY-MONTH-YEAR, EDIT-DATE-LE, EDIT-DATE-OF-BIRTH) -- depends on CSUTLDWY.cpy working storage; calls CSUTLDTC |

---

## Constants and Literals

Named constants (88-level items) and significant literals found in the codebase:

| Constant | Value | Defined In | Usage Context |
| -------- | ----- | ---------- | ------------- |
| CDEMO-USRTYP-ADMIN | 'A' | COCOM01Y.cpy | User type check in all CICS programs |
| CDEMO-USRTYP-USER | 'U' | COCOM01Y.cpy | User type check in all CICS programs |
| CDEMO-PGM-ENTER | 0 | COCOM01Y.cpy | First entry to program |
| CDEMO-PGM-REENTER | 1 | COCOM01Y.cpy | Re-entry after send map |
| CCARD-AID-ENTER | 'ENTER' | CVCRD01Y.cpy | Enter key pressed |
| CCARD-AID-CLEAR | 'CLEAR' | CVCRD01Y.cpy | Clear key pressed |
| CCARD-AID-PFK01..12 | 'PFK01'..'PFK12' | CVCRD01Y.cpy | Function key identifiers |
| APPL-AOK | 0 | Multiple programs | Successful file I/O status |
| APPL-EOF | 16 | Multiple programs | End of file reached |
| THIS-CENTURY | 20 | CSUTLDWY.cpy | Valid century check (year 2000s) |
| LAST-CENTURY | 19 | CSUTLDWY.cpy | Valid century check (year 1900s) |
| WS-EDIT-DATE-IS-VALID | LOW-VALUES | CSUTLDWY.cpy | All date validation flags clear |
| WS-EDIT-DATE-IS-INVALID | '000' | CSUTLDWY.cpy | One or more date validation flags set |
| WS-VALID-MONTH | 1 THROUGH 12 | CSUTLDWY.cpy | Valid month range |
| WS-31-DAY-MONTH | 1,3,5,7,8,10,12 | CSUTLDWY.cpy | Months with 31 days |
| WS-FEBRUARY | 2 | CSUTLDWY.cpy | February month number |
| WS-VALID-DAY | 1 THROUGH 31 | CSUTLDWY.cpy | Valid day range |
| FC-INVALID-DATE | X'0000000000000000' | CSUTLDTC.cbl | CEEDAYS: date is valid (feedback token) |
| FC-INSUFFICIENT-DATA | X'000309CB...' | CSUTLDTC.cbl | CEEDAYS: insufficient data |
| FC-BAD-DATE-VALUE | X'000309CC...' | CSUTLDTC.cbl | CEEDAYS: bad date value |
| FC-INVALID-MONTH | X'000309D5...' | CSUTLDTC.cbl | CEEDAYS: invalid month |
| FC-NON-NUMERIC-DATA | X'000309D8...' | CSUTLDTC.cbl | CEEDAYS: non-numeric data |
| FICO-RANGE-IS-VALID | 300 THROUGH 850 | COACTUPC.cbl | Valid FICO score range |
| LIT-ACCTFILENAME | 'ACCTDAT ' | COACTUPC.cbl, COACTVWC.cbl | CICS VSAM file name for accounts |
| LIT-CUSTFILENAME | 'CUSTDAT ' | COACTUPC.cbl, COACTVWC.cbl | CICS VSAM file name for customers |
| LIT-CARDFILENAME | 'CARDDAT ' | COACTUPC.cbl, COCRDSLC.cbl, COCRDUPC.cbl | CICS VSAM file name for cards |
| LIT-CARDFILENAME-ACCT-PATH | 'CARDAIX ' | COACTUPC.cbl, COCRDSLC.cbl | Card file alternate index by account |
| LIT-CARDXREFNAME-ACCT-PATH | 'CXACAIX ' | COACTUPC.cbl, COACTVWC.cbl | Card xref alternate index by account |
| CDEMO-MENU-OPT-COUNT | 11 | COMEN02Y.cpy | Number of main menu items |
| CDEMO-ADMIN-OPT-COUNT | 6 | COADM02Y.cpy | Number of admin menu items (includes 2 DB2 placeholders) |
| CCDA-TITLE01 | 'AWS Mainframe Modernization' | COTTL01Y.cpy | Screen title line 1 |
| CCDA-TITLE02 | 'CardDemo' | COTTL01Y.cpy | Screen title line 2 |
| WS-TRANID (CORPT00C) | 'CR00' | CORPT00C.cbl | CICS transaction ID for report program |
| JCL TDQ QUEUE | 'JOBS' | CORPT00C.cbl | Extra-partition TDQ for batch job submission |
| MVSWAIT-TIME default | 00003600 (centiseconds) | COBSWAIT WAITSTEP.jcl | Default wait = 36 seconds; passed via SYSIN PARM |
| M03B-OPEN | 'O' | CBSTM03A.CBL / CBSTM03B.CBL | File open operation code passed to CBSTM03B |
| M03B-CLOSE | 'C' | CBSTM03A.CBL / CBSTM03B.CBL | File close operation code |
| M03B-READ | 'R' | CBSTM03A.CBL / CBSTM03B.CBL | Sequential read operation code |
| M03B-READ-K | 'K' | CBSTM03A.CBL / CBSTM03B.CBL | Keyed (random) read operation code |
| WS-TRNX-TABLE capacity | 51 cards x 10 transactions | CBSTM03A.CBL | Hard limit on cards and transactions per statement run |
| EXPORT-REC-TYPE values | 'C','A','T','X','K' | CVEXPORT.cpy | Record type discriminator for multi-type export file |
