---
type: business-rules
program: CBEXPORT
program_type: batch
status: draft
confidence: high
last_pass: 4
calls:
- CEE3ABD
called_by: []
uses_copybooks:
- CVACT01Y
- CVACT02Y
- CVACT03Y
- CVCUS01Y
- CVEXPORT
- CVTRA05Y
reads:
- ACCOUNT-INPUT
- CARD-INPUT
- CUSTOMER-INPUT
- TRANSACTION-INPUT
- XREF-INPUT
writes:
- EXPORT-OUTPUT
db_tables: []
transactions: []
mq_queues: []
---

# CBEXPORT -- Business Rules

## Program Purpose

CBEXPORT is a batch program that exports all CardDemo operational data into a single
multi-record flat file for branch migration purposes. It reads five normalised indexed
VSAM files sequentially (customers, accounts, card-account cross-references,
transactions, and cards), maps each source record to a typed export record with common
header fields, writes every record to a single 500-byte fixed-length output file, and
prints processing statistics to SYSOUT on completion. The program is a one-shot bulk
extract: no filtering, selection, or transformation of business data values occurs --
every record present in each input file is exported.

## Input / Output

| Direction | Resource             | Type | Description                                                              |
| --------- | -------------------- | ---- | ------------------------------------------------------------------------ |
| IN        | CUSTOMER-INPUT       | File | Indexed VSAM file of customer profiles (CUSTFILE DD); key CUST-ID        |
| IN        | ACCOUNT-INPUT        | File | Indexed VSAM file of account records (ACCTFILE DD); key ACCT-ID          |
| IN        | XREF-INPUT           | File | Indexed VSAM cross-reference file (XREFFILE DD); key XREF-CARD-NUM       |
| IN        | TRANSACTION-INPUT    | File | Indexed VSAM transaction file (TRANSACT DD); key TRAN-ID                 |
| IN        | CARD-INPUT           | File | Indexed VSAM card file (CARDFILE DD); key CARD-NUM                       |
| OUT       | EXPORT-OUTPUT        | File | Indexed sequential export file (EXPFILE DD); 500-byte fixed records; key EXPORT-SEQUENCE-NUM |

## Business Rules

### File Open / Prerequisites

| #  | Rule                                 | Condition                                              | Action                                                                                       | Source Location |
| -- | ------------------------------------ | ------------------------------------------------------ | -------------------------------------------------------------------------------------------- | --------------- |
| 1  | CUSTOMER-INPUT must be openable      | File status after OPEN INPUT CUSTOMER-INPUT NOT = '00' | DISPLAY 'ERROR: Cannot open CUSTOMER-INPUT, Status: ' + WS-CUSTOMER-STATUS; PERFORM 9999-ABEND-PROGRAM | 1100-OPEN-FILES line 200-205 |
| 2  | ACCOUNT-INPUT must be openable       | File status after OPEN INPUT ACCOUNT-INPUT NOT = '00'  | DISPLAY 'ERROR: Cannot open ACCOUNT-INPUT, Status: ' + WS-ACCOUNT-STATUS; PERFORM 9999-ABEND-PROGRAM  | 1100-OPEN-FILES line 207-212 |
| 3  | XREF-INPUT must be openable          | File status after OPEN INPUT XREF-INPUT NOT = '00'     | DISPLAY 'ERROR: Cannot open XREF-INPUT, Status: ' + WS-XREF-STATUS; PERFORM 9999-ABEND-PROGRAM        | 1100-OPEN-FILES line 214-219 |
| 4  | TRANSACTION-INPUT must be openable   | File status after OPEN INPUT TRANSACTION-INPUT NOT = '00' | DISPLAY 'ERROR: Cannot open TRANSACTION-INPUT, Status: ' + WS-TRANSACTION-STATUS; PERFORM 9999-ABEND-PROGRAM | 1100-OPEN-FILES line 221-226 |
| 5  | CARD-INPUT must be openable          | File status after OPEN INPUT CARD-INPUT NOT = '00'     | DISPLAY 'ERROR: Cannot open CARD-INPUT, Status: ' + WS-CARD-STATUS; PERFORM 9999-ABEND-PROGRAM        | 1100-OPEN-FILES line 228-233 |
| 6  | EXPORT-OUTPUT must be openable       | File status after OPEN OUTPUT EXPORT-OUTPUT NOT = '00' | DISPLAY 'ERROR: Cannot open EXPORT-OUTPUT, Status: ' + WS-EXPORT-STATUS; PERFORM 9999-ABEND-PROGRAM   | 1100-OPEN-FILES line 235-240 |

**Note:** Open checks use 88-level conditions: WS-CUSTOMER-OK (VALUE '00'), WS-ACCOUNT-OK (VALUE '00'), WS-XREF-OK (VALUE '00'), WS-TRANSACTION-OK (VALUE '00'), WS-CARD-OK (VALUE '00'), WS-EXPORT-OK (VALUE '00'). The IF NOT ... pattern tests for any non-zero status.

### Read Error Handling

| #  | Rule                                     | Condition                                                                | Action                                                                                        | Source Location      |
| -- | ---------------------------------------- | ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- | -------------------- |
| 7  | Customer read must succeed or reach EOF  | WS-CUSTOMER-STATUS NOT = '00' AND NOT = '10'                             | DISPLAY 'ERROR: Reading CUSTOMER-INPUT, Status: ' + WS-CUSTOMER-STATUS; PERFORM 9999-ABEND-PROGRAM | 2100-READ-CUSTOMER-RECORD line 262-266 |
| 8  | Account read must succeed or reach EOF   | WS-ACCOUNT-STATUS NOT = '00' AND NOT = '10'                              | DISPLAY 'ERROR: Reading ACCOUNT-INPUT, Status: ' + WS-ACCOUNT-STATUS; PERFORM 9999-ABEND-PROGRAM   | 3100-READ-ACCOUNT-RECORD line 331-335 |
| 9  | Xref read must succeed or reach EOF      | WS-XREF-STATUS NOT = '00' AND NOT = '10'                                 | DISPLAY 'ERROR: Reading XREF-INPUT, Status: ' + WS-XREF-STATUS; PERFORM 9999-ABEND-PROGRAM         | 4100-READ-XREF-RECORD line 395-399 |
| 10 | Transaction read must succeed or reach EOF | WS-TRANSACTION-STATUS NOT = '00' AND NOT = '10'                        | DISPLAY 'ERROR: Reading TRANSACTION-INPUT, Status: ' + WS-TRANSACTION-STATUS; PERFORM 9999-ABEND-PROGRAM | 5100-READ-TRANSACTION-RECORD line 450-454 |
| 11 | Card read must succeed or reach EOF      | WS-CARD-STATUS NOT = '00' AND NOT = '10'                                 | DISPLAY 'ERROR: Reading CARD-INPUT, Status: ' + WS-CARD-STATUS; PERFORM 9999-ABEND-PROGRAM          | 5600-READ-CARD-RECORD line 515-519 |

**Note:** Read checks use paired 88-level conditions: WS-CUSTOMER-OK/WS-CUSTOMER-EOF, WS-ACCOUNT-OK/WS-ACCOUNT-EOF, etc. Status '10' (EOF) drives loop termination; any other non-zero status is fatal.

### Export Record Write Validation

| #  | Rule                                     | Condition                                  | Action                                                                                     | Source Location             |
| -- | ---------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------ | --------------------------- |
| 12 | Every WRITE to EXPORT-OUTPUT must succeed | WS-EXPORT-STATUS NOT = '00' after WRITE    | DISPLAY 'ERROR: Writing export record, Status: ' + WS-EXPORT-STATUS; PERFORM 9999-ABEND-PROGRAM | 2200, 3200, 4200, 5200, 5700 |

### File Close (No Error Checking)

| #  | Rule                                      | Condition | Action                                                                           | Source Location         |
| -- | ----------------------------------------- | --------- | -------------------------------------------------------------------------------- | ----------------------- |
| 77 | All six files closed without status check | Always    | CLOSE CUSTOMER-INPUT, ACCOUNT-INPUT, XREF-INPUT, TRANSACTION-INPUT, CARD-INPUT, EXPORT-OUTPUT with no subsequent file-status test | 6000-FINALIZE lines 556-561 |

**Note:** Unlike the OPEN path, CLOSE failures are silently ignored. If a CLOSE fails (e.g. EXPORT-OUTPUT flush error), the program proceeds to display statistics and ends normally. This is a known gap: a partially flushed output file would not be detected.

### Record Buffer Initialisation

| #  | Rule                                        | Condition           | Action                                                                      | Source Location                  |
| -- | ------------------------------------------- | ------------------- | --------------------------------------------------------------------------- | -------------------------------- |
| 76 | Export record buffer cleared before mapping | Every export record | INITIALIZE EXPORT-RECORD sets all 500 bytes to low-values/spaces before any field is moved | All CREATE paragraphs (lines 271, 340, 404, 459, 524) |

### Record Type Assignment (Routing)

| #  | Rule                                   | Condition                         | Action                                                         | Source Location               |
| -- | -------------------------------------- | --------------------------------- | -------------------------------------------------------------- | ----------------------------- |
| 13 | Customer records tagged with type 'C'  | Processing customer source record | MOVE 'C' TO EXPORT-REC-TYPE                                    | 2200-CREATE-CUSTOMER-EXP-REC line 274 |
| 14 | Account records tagged with type 'A'   | Processing account source record  | MOVE 'A' TO EXPORT-REC-TYPE                                    | 3200-CREATE-ACCOUNT-EXP-REC line 343  |
| 15 | Cross-reference records tagged 'X'     | Processing xref source record     | MOVE 'X' TO EXPORT-REC-TYPE                                    | 4200-CREATE-XREF-EXPORT-RECORD line 407 |
| 16 | Transaction records tagged with type 'T' | Processing transaction source record | MOVE 'T' TO EXPORT-REC-TYPE                                 | 5200-CREATE-TRAN-EXP-REC line 462     |
| 17 | Card records tagged with type 'D'      | Processing card source record     | MOVE 'D' TO EXPORT-REC-TYPE                                    | 5700-CREATE-CARD-EXPORT-RECORD line 527 |

### Common Export Record Header Fields (all record types)

| #  | Rule                                        | Condition             | Action                                                                          | Source Location                   |
| -- | ------------------------------------------- | --------------------- | ------------------------------------------------------------------------------- | --------------------------------- |
| 18 | Export timestamp set to job-start timestamp | Every export record   | MOVE WS-FORMATTED-TIMESTAMP TO EXPORT-TIMESTAMP (26-char 'YYYY-MM-DD HH:MM:SS.00') | All CREATE paragraphs            |
| 19 | Sequence number incremented per record      | Every export record   | ADD 1 TO WS-SEQUENCE-COUNTER; MOVE WS-SEQUENCE-COUNTER TO EXPORT-SEQUENCE-NUM  | All CREATE paragraphs             |
| 20 | Branch ID hardcoded to '0001'               | Every export record   | MOVE '0001' TO EXPORT-BRANCH-ID                                                 | All CREATE paragraphs             |
| 21 | Region code hardcoded to 'NORTH'            | Every export record   | MOVE 'NORTH' TO EXPORT-REGION-CODE                                              | All CREATE paragraphs             |

### Customer Record Field Mapping (record type 'C')

| #  | Rule                                       | Source Field               | Export Field                    | Source Location              |
| -- | ------------------------------------------ | -------------------------- | -------------------------------- | ---------------------------- |
| 22 | Customer ID mapped verbatim                | CUST-ID                    | EXP-CUST-ID (PIC 9(09) COMP)    | 2200-CREATE-CUSTOMER-EXP-REC |
| 23 | Customer first name mapped verbatim        | CUST-FIRST-NAME            | EXP-CUST-FIRST-NAME (PIC X(25)) | 2200-CREATE-CUSTOMER-EXP-REC |
| 24 | Customer middle name mapped verbatim       | CUST-MIDDLE-NAME           | EXP-CUST-MIDDLE-NAME (PIC X(25)) | 2200-CREATE-CUSTOMER-EXP-REC |
| 25 | Customer last name mapped verbatim         | CUST-LAST-NAME             | EXP-CUST-LAST-NAME (PIC X(25)) | 2200-CREATE-CUSTOMER-EXP-REC |
| 26 | Three address lines mapped verbatim        | CUST-ADDR-LINE-1/2/3       | EXP-CUST-ADDR-LINE(1..3) (PIC X(50) each) | 2200-CREATE-CUSTOMER-EXP-REC |
| 27 | State code mapped verbatim                 | CUST-ADDR-STATE-CD         | EXP-CUST-ADDR-STATE-CD (PIC X(02)) | 2200-CREATE-CUSTOMER-EXP-REC |
| 28 | Country code mapped verbatim               | CUST-ADDR-COUNTRY-CD       | EXP-CUST-ADDR-COUNTRY-CD (PIC X(03)) | 2200-CREATE-CUSTOMER-EXP-REC |
| 29 | ZIP code mapped verbatim                   | CUST-ADDR-ZIP              | EXP-CUST-ADDR-ZIP (PIC X(10))  | 2200-CREATE-CUSTOMER-EXP-REC |
| 30 | Two phone numbers mapped verbatim          | CUST-PHONE-NUM-1/2         | EXP-CUST-PHONE-NUM(1..2) (PIC X(15) each) | 2200-CREATE-CUSTOMER-EXP-REC |
| 31 | SSN mapped verbatim                        | CUST-SSN                   | EXP-CUST-SSN (PIC 9(09))       | 2200-CREATE-CUSTOMER-EXP-REC |
| 32 | Government-issued ID mapped verbatim       | CUST-GOVT-ISSUED-ID        | EXP-CUST-GOVT-ISSUED-ID (PIC X(20)) | 2200-CREATE-CUSTOMER-EXP-REC |
| 33 | Date of birth mapped verbatim              | CUST-DOB-YYYY-MM-DD        | EXP-CUST-DOB-YYYY-MM-DD (PIC X(10)) | 2200-CREATE-CUSTOMER-EXP-REC |
| 34 | EFT account ID mapped verbatim             | CUST-EFT-ACCOUNT-ID        | EXP-CUST-EFT-ACCOUNT-ID (PIC X(10)) | 2200-CREATE-CUSTOMER-EXP-REC |
| 35 | Primary card-holder indicator mapped verbatim | CUST-PRI-CARD-HOLDER-IND | EXP-CUST-PRI-CARD-HOLDER-IND (PIC X(01)) | 2200-CREATE-CUSTOMER-EXP-REC |
| 36 | FICO credit score mapped verbatim          | CUST-FICO-CREDIT-SCORE     | EXP-CUST-FICO-CREDIT-SCORE (PIC 9(03) COMP-3) | 2200-CREATE-CUSTOMER-EXP-REC |

### Account Record Field Mapping (record type 'A')

| #  | Rule                                     | Source Field               | Export Field                              | Source Location             |
| -- | ---------------------------------------- | -------------------------- | ----------------------------------------- | --------------------------- |
| 37 | Account ID mapped verbatim               | ACCT-ID                    | EXP-ACCT-ID (PIC 9(11))                   | 3200-CREATE-ACCOUNT-EXP-REC |
| 38 | Account active status mapped verbatim    | ACCT-ACTIVE-STATUS         | EXP-ACCT-ACTIVE-STATUS (PIC X(01))        | 3200-CREATE-ACCOUNT-EXP-REC |
| 39 | Current balance mapped verbatim          | ACCT-CURR-BAL              | EXP-ACCT-CURR-BAL (PIC S9(10)V99 COMP-3) | 3200-CREATE-ACCOUNT-EXP-REC |
| 40 | Credit limit mapped verbatim             | ACCT-CREDIT-LIMIT          | EXP-ACCT-CREDIT-LIMIT (PIC S9(10)V99)    | 3200-CREATE-ACCOUNT-EXP-REC |
| 41 | Cash credit limit mapped verbatim        | ACCT-CASH-CREDIT-LIMIT     | EXP-ACCT-CASH-CREDIT-LIMIT (PIC S9(10)V99 COMP-3) | 3200-CREATE-ACCOUNT-EXP-REC |
| 42 | Account open date mapped verbatim        | ACCT-OPEN-DATE             | EXP-ACCT-OPEN-DATE (PIC X(10))            | 3200-CREATE-ACCOUNT-EXP-REC |
| 43 | Account expiration date mapped verbatim  | ACCT-EXPIRAION-DATE        | EXP-ACCT-EXPIRAION-DATE (PIC X(10))       | 3200-CREATE-ACCOUNT-EXP-REC |
| 44 | Account reissue date mapped verbatim     | ACCT-REISSUE-DATE          | EXP-ACCT-REISSUE-DATE (PIC X(10))         | 3200-CREATE-ACCOUNT-EXP-REC |
| 45 | Current cycle credit mapped verbatim     | ACCT-CURR-CYC-CREDIT       | EXP-ACCT-CURR-CYC-CREDIT (PIC S9(10)V99) | 3200-CREATE-ACCOUNT-EXP-REC |
| 46 | Current cycle debit mapped verbatim      | ACCT-CURR-CYC-DEBIT        | EXP-ACCT-CURR-CYC-DEBIT (PIC S9(10)V99 COMP) | 3200-CREATE-ACCOUNT-EXP-REC |
| 47 | Account ZIP code mapped verbatim         | ACCT-ADDR-ZIP              | EXP-ACCT-ADDR-ZIP (PIC X(10))             | 3200-CREATE-ACCOUNT-EXP-REC |
| 48 | Account group ID mapped verbatim         | ACCT-GROUP-ID              | EXP-ACCT-GROUP-ID (PIC X(10))             | 3200-CREATE-ACCOUNT-EXP-REC |

### Cross-Reference Record Field Mapping (record type 'X')

| #  | Rule                                | Source Field    | Export Field                          | Source Location              |
| -- | ----------------------------------- | --------------- | ------------------------------------- | ---------------------------- |
| 49 | Card number mapped verbatim         | XREF-CARD-NUM   | EXP-XREF-CARD-NUM (PIC X(16))         | 4200-CREATE-XREF-EXPORT-RECORD |
| 50 | Customer ID mapped verbatim         | XREF-CUST-ID    | EXP-XREF-CUST-ID (PIC 9(09))          | 4200-CREATE-XREF-EXPORT-RECORD |
| 51 | Account ID mapped verbatim          | XREF-ACCT-ID    | EXP-XREF-ACCT-ID (PIC 9(11) COMP)     | 4200-CREATE-XREF-EXPORT-RECORD |

### Transaction Record Field Mapping (record type 'T')

| #  | Rule                                     | Source Field           | Export Field                              | Source Location       |
| -- | ---------------------------------------- | ---------------------- | ----------------------------------------- | --------------------- |
| 52 | Transaction ID mapped verbatim           | TRAN-ID                | EXP-TRAN-ID (PIC X(16))                   | 5200-CREATE-TRAN-EXP-REC |
| 53 | Transaction type code mapped verbatim    | TRAN-TYPE-CD           | EXP-TRAN-TYPE-CD (PIC X(02))              | 5200-CREATE-TRAN-EXP-REC |
| 54 | Transaction category code mapped verbatim | TRAN-CAT-CD           | EXP-TRAN-CAT-CD (PIC 9(04))               | 5200-CREATE-TRAN-EXP-REC |
| 55 | Transaction source mapped verbatim       | TRAN-SOURCE            | EXP-TRAN-SOURCE (PIC X(10))               | 5200-CREATE-TRAN-EXP-REC |
| 56 | Transaction description mapped verbatim  | TRAN-DESC              | EXP-TRAN-DESC (PIC X(100))                | 5200-CREATE-TRAN-EXP-REC |
| 57 | Transaction amount mapped verbatim       | TRAN-AMT               | EXP-TRAN-AMT (PIC S9(09)V99 COMP-3)       | 5200-CREATE-TRAN-EXP-REC |
| 58 | Merchant ID mapped verbatim              | TRAN-MERCHANT-ID       | EXP-TRAN-MERCHANT-ID (PIC 9(09) COMP)     | 5200-CREATE-TRAN-EXP-REC |
| 59 | Merchant name mapped verbatim            | TRAN-MERCHANT-NAME     | EXP-TRAN-MERCHANT-NAME (PIC X(50))        | 5200-CREATE-TRAN-EXP-REC |
| 60 | Merchant city mapped verbatim            | TRAN-MERCHANT-CITY     | EXP-TRAN-MERCHANT-CITY (PIC X(50))        | 5200-CREATE-TRAN-EXP-REC |
| 61 | Merchant ZIP mapped verbatim             | TRAN-MERCHANT-ZIP      | EXP-TRAN-MERCHANT-ZIP (PIC X(10))         | 5200-CREATE-TRAN-EXP-REC |
| 62 | Card number mapped verbatim              | TRAN-CARD-NUM          | EXP-TRAN-CARD-NUM (PIC X(16))             | 5200-CREATE-TRAN-EXP-REC |
| 63 | Original transaction timestamp mapped verbatim | TRAN-ORIG-TS     | EXP-TRAN-ORIG-TS (PIC X(26))              | 5200-CREATE-TRAN-EXP-REC |
| 64 | Processing timestamp mapped verbatim     | TRAN-PROC-TS           | EXP-TRAN-PROC-TS (PIC X(26))              | 5200-CREATE-TRAN-EXP-REC |

### Card Record Field Mapping (record type 'D')

| #  | Rule                                  | Source Field           | Export Field                              | Source Location              |
| -- | ------------------------------------- | ---------------------- | ----------------------------------------- | ---------------------------- |
| 65 | Card number mapped verbatim           | CARD-NUM               | EXP-CARD-NUM (PIC X(16))                  | 5700-CREATE-CARD-EXPORT-RECORD |
| 66 | Card account ID mapped verbatim       | CARD-ACCT-ID           | EXP-CARD-ACCT-ID (PIC 9(11) COMP)         | 5700-CREATE-CARD-EXPORT-RECORD |
| 67 | CVV code mapped verbatim              | CARD-CVV-CD            | EXP-CARD-CVV-CD (PIC 9(03) COMP)          | 5700-CREATE-CARD-EXPORT-RECORD |
| 68 | Embossed name mapped verbatim         | CARD-EMBOSSED-NAME     | EXP-CARD-EMBOSSED-NAME (PIC X(50))        | 5700-CREATE-CARD-EXPORT-RECORD |
| 69 | Card expiration date mapped verbatim  | CARD-EXPIRAION-DATE    | EXP-CARD-EXPIRAION-DATE (PIC X(10))       | 5700-CREATE-CARD-EXPORT-RECORD |
| 70 | Card active status mapped verbatim    | CARD-ACTIVE-STATUS     | EXP-CARD-ACTIVE-STATUS (PIC X(01))        | 5700-CREATE-CARD-EXPORT-RECORD |

### Processing Order

| #  | Rule                                              | Condition | Action                                                              | Source Location       |
| -- | ------------------------------------------------- | --------- | ------------------------------------------------------------------- | --------------------- |
| 71 | Customers exported before accounts                | Always    | 2000-EXPORT-CUSTOMERS completes entirely before 3000-EXPORT-ACCOUNTS begins | 0000-MAIN-PROCESSING |
| 72 | Accounts exported before cross-references         | Always    | 3000-EXPORT-ACCOUNTS completes before 4000-EXPORT-XREFS begins              | 0000-MAIN-PROCESSING |
| 73 | Cross-references exported before transactions     | Always    | 4000-EXPORT-XREFS completes before 5000-EXPORT-TRANSACTIONS begins          | 0000-MAIN-PROCESSING |
| 74 | Transactions exported before cards                | Always    | 5000-EXPORT-TRANSACTIONS completes before 5500-EXPORT-CARDS begins          | 0000-MAIN-PROCESSING |
| 75 | All input records exported with no filtering      | Always    | PERFORM UNTIL EOF pattern for each file; no selection criteria applied       | All 2000-5500 paragraphs |

### Intermediate Progress Messages

| #  | Rule                                               | Condition | Action                                                               | Source Location            |
| -- | -------------------------------------------------- | --------- | -------------------------------------------------------------------- | -------------------------- |
| 78 | Customer phase progress displayed before loop      | Always    | DISPLAY 'CBEXPORT: Processing customer records'                      | 2000-EXPORT-CUSTOMERS line 245 |
| 79 | Customer count displayed after phase completes     | Always    | DISPLAY 'CBEXPORT: Customers exported: ' WS-CUSTOMER-RECORDS-EXPORTED | 2000-EXPORT-CUSTOMERS line 254-255 |
| 80 | Account phase progress displayed before loop       | Always    | DISPLAY 'CBEXPORT: Processing account records'                       | 3000-EXPORT-ACCOUNTS line 314 |
| 81 | Account count displayed after phase completes      | Always    | DISPLAY 'CBEXPORT: Accounts exported: ' WS-ACCOUNT-RECORDS-EXPORTED  | 3000-EXPORT-ACCOUNTS line 323-324 |
| 82 | Xref phase progress displayed before loop          | Always    | DISPLAY 'CBEXPORT: Processing cross-reference records'               | 4000-EXPORT-XREFS line 378 |
| 83 | Xref count displayed after phase completes         | Always    | DISPLAY 'CBEXPORT: Cross-references exported: ' WS-XREF-RECORDS-EXPORTED | 4000-EXPORT-XREFS line 387-388 |
| 84 | Transaction phase progress displayed before loop   | Always    | DISPLAY 'CBEXPORT: Processing transaction records'                   | 5000-EXPORT-TRANSACTIONS line 433 |
| 85 | Transaction count displayed after phase completes  | Always    | DISPLAY 'CBEXPORT: Transactions exported: ' WS-TRAN-RECORDS-EXPORTED | 5000-EXPORT-TRANSACTIONS line 442-443 |
| 86 | Card phase progress displayed before loop          | Always    | DISPLAY 'CBEXPORT: Processing card records'                          | 5500-EXPORT-CARDS line 498 |
| 87 | Card count displayed after phase completes         | Always    | DISPLAY 'CBEXPORT: Cards exported: ' WS-CARD-RECORDS-EXPORTED        | 5500-EXPORT-CARDS line 507-508 |

## Calculations

| Calculation                  | Formula / Logic                                                                   | Input Fields               | Output Field                | Source Location          |
| ---------------------------- | --------------------------------------------------------------------------------- | -------------------------- | --------------------------- | ------------------------ |
| Sequence number increment    | ADD 1 TO WS-SEQUENCE-COUNTER; MOVE WS-SEQUENCE-COUNTER TO EXPORT-SEQUENCE-NUM for each record written  | WS-SEQUENCE-COUNTER (PIC 9(09) VALUE 0)        | EXPORT-SEQUENCE-NUM (PIC 9(9) COMP) | All CREATE paragraphs |
| Customer record count        | ADD 1 TO WS-CUSTOMER-RECORDS-EXPORTED; ADD 1 TO WS-TOTAL-RECORDS-EXPORTED per customer written | WS-CUSTOMER-RECORDS-EXPORTED (PIC 9(09) VALUE 0) | WS-CUSTOMER-RECORDS-EXPORTED, WS-TOTAL-RECORDS-EXPORTED | 2200-CREATE-CUSTOMER-EXP-REC lines 309-310 |
| Account record count         | ADD 1 TO WS-ACCOUNT-RECORDS-EXPORTED; ADD 1 TO WS-TOTAL-RECORDS-EXPORTED per account written   | WS-ACCOUNT-RECORDS-EXPORTED (PIC 9(09) VALUE 0)  | WS-ACCOUNT-RECORDS-EXPORTED, WS-TOTAL-RECORDS-EXPORTED  | 3200-CREATE-ACCOUNT-EXP-REC lines 372-373  |
| Xref record count            | ADD 1 TO WS-XREF-RECORDS-EXPORTED; ADD 1 TO WS-TOTAL-RECORDS-EXPORTED per xref written         | WS-XREF-RECORDS-EXPORTED (PIC 9(09) VALUE 0)     | WS-XREF-RECORDS-EXPORTED, WS-TOTAL-RECORDS-EXPORTED     | 4200-CREATE-XREF-EXPORT-RECORD lines 427-428 |
| Transaction record count     | ADD 1 TO WS-TRAN-RECORDS-EXPORTED; ADD 1 TO WS-TOTAL-RECORDS-EXPORTED per transaction written  | WS-TRAN-RECORDS-EXPORTED (PIC 9(09) VALUE 0)     | WS-TRAN-RECORDS-EXPORTED, WS-TOTAL-RECORDS-EXPORTED     | 5200-CREATE-TRAN-EXP-REC lines 492-493     |
| Card record count            | ADD 1 TO WS-CARD-RECORDS-EXPORTED; ADD 1 TO WS-TOTAL-RECORDS-EXPORTED per card written         | WS-CARD-RECORDS-EXPORTED (PIC 9(09) VALUE 0)     | WS-CARD-RECORDS-EXPORTED, WS-TOTAL-RECORDS-EXPORTED     | 5700-CREATE-CARD-EXPORT-RECORD lines 550-551 |
| Export timestamp formatting  | Three STRING operations: (1) STRING WS-CURR-YEAR '-' WS-CURR-MONTH '-' WS-CURR-DAY DELIMITED BY SIZE INTO WS-EXPORT-DATE; (2) STRING WS-CURR-HOUR ':' WS-CURR-MINUTE ':' WS-CURR-SECOND DELIMITED BY SIZE INTO WS-EXPORT-TIME; (3) STRING WS-EXPORT-DATE ' ' WS-EXPORT-TIME '.00' DELIMITED BY SIZE INTO WS-FORMATTED-TIMESTAMP. Hundredths are always written as literal '.00' -- WS-CURR-HUNDREDTH is accepted from TIME (line 176) but is never used in the STRING. | WS-CURR-YEAR (9(04)), WS-CURR-MONTH (9(02)), WS-CURR-DAY (9(02)), WS-CURR-HOUR (9(02)), WS-CURR-MINUTE (9(02)), WS-CURR-SECOND (9(02)) | WS-EXPORT-DATE (X(10)), WS-EXPORT-TIME (X(08)), WS-FORMATTED-TIMESTAMP (X(26)) | 1050-GENERATE-TIMESTAMP lines 179-194 |

## Error Handling

| Condition                                  | Action                                                                          | Return Code          | Source Location                           |
| ------------------------------------------ | ------------------------------------------------------------------------------- | -------------------- | ----------------------------------------- |
| CUSTOMER-INPUT OPEN fails (status != '00') | DISPLAY 'ERROR: Cannot open CUSTOMER-INPUT, Status: ' WS-CUSTOMER-STATUS; PERFORM 9999-ABEND-PROGRAM; CALL 'CEE3ABD' | Abnormal end         | 1100-OPEN-FILES lines 200-205             |
| ACCOUNT-INPUT OPEN fails (status != '00')  | DISPLAY 'ERROR: Cannot open ACCOUNT-INPUT, Status: ' WS-ACCOUNT-STATUS; PERFORM 9999-ABEND-PROGRAM; CALL 'CEE3ABD' | Abnormal end         | 1100-OPEN-FILES lines 207-212             |
| XREF-INPUT OPEN fails (status != '00')     | DISPLAY 'ERROR: Cannot open XREF-INPUT, Status: ' WS-XREF-STATUS; PERFORM 9999-ABEND-PROGRAM; CALL 'CEE3ABD' | Abnormal end         | 1100-OPEN-FILES lines 214-219             |
| TRANSACTION-INPUT OPEN fails (status != '00') | DISPLAY 'ERROR: Cannot open TRANSACTION-INPUT, Status: ' WS-TRANSACTION-STATUS; PERFORM 9999-ABEND-PROGRAM; CALL 'CEE3ABD' | Abnormal end      | 1100-OPEN-FILES lines 221-226             |
| CARD-INPUT OPEN fails (status != '00')     | DISPLAY 'ERROR: Cannot open CARD-INPUT, Status: ' WS-CARD-STATUS; PERFORM 9999-ABEND-PROGRAM; CALL 'CEE3ABD' | Abnormal end         | 1100-OPEN-FILES lines 228-233             |
| EXPORT-OUTPUT OPEN fails (status != '00')  | DISPLAY 'ERROR: Cannot open EXPORT-OUTPUT, Status: ' WS-EXPORT-STATUS; PERFORM 9999-ABEND-PROGRAM; CALL 'CEE3ABD' | Abnormal end         | 1100-OPEN-FILES lines 235-240             |
| CUSTOMER-INPUT READ error (status != '00' and != '10') | DISPLAY 'ERROR: Reading CUSTOMER-INPUT, Status: ' WS-CUSTOMER-STATUS; PERFORM 9999-ABEND-PROGRAM | Abnormal end | 2100-READ-CUSTOMER-RECORD lines 262-266 |
| ACCOUNT-INPUT READ error (status != '00' and != '10')  | DISPLAY 'ERROR: Reading ACCOUNT-INPUT, Status: ' WS-ACCOUNT-STATUS; PERFORM 9999-ABEND-PROGRAM  | Abnormal end | 3100-READ-ACCOUNT-RECORD lines 331-335  |
| XREF-INPUT READ error (status != '00' and != '10')     | DISPLAY 'ERROR: Reading XREF-INPUT, Status: ' WS-XREF-STATUS; PERFORM 9999-ABEND-PROGRAM        | Abnormal end | 4100-READ-XREF-RECORD lines 395-399     |
| TRANSACTION-INPUT READ error (status != '00' and != '10') | DISPLAY 'ERROR: Reading TRANSACTION-INPUT, Status: ' WS-TRANSACTION-STATUS; PERFORM 9999-ABEND-PROGRAM | Abnormal end | 5100-READ-TRANSACTION-RECORD lines 450-454 |
| CARD-INPUT READ error (status != '00' and != '10')     | DISPLAY 'ERROR: Reading CARD-INPUT, Status: ' WS-CARD-STATUS; PERFORM 9999-ABEND-PROGRAM        | Abnormal end | 5600-READ-CARD-RECORD lines 515-519     |
| EXPORT-OUTPUT WRITE error (status != '00') | DISPLAY 'ERROR: Writing export record, Status: ' WS-EXPORT-STATUS; PERFORM 9999-ABEND-PROGRAM | Abnormal end         | 2200 line 303, 3200 line 366, 4200 line 421, 5200 line 486, 5700 line 544 |
| Any abend trigger (9999-ABEND-PROGRAM)     | DISPLAY 'CBEXPORT: ABENDING PROGRAM'; CALL 'CEE3ABD' (Language Environment abend) | Abnormal end (dump) | 9999-ABEND-PROGRAM lines 578-579          |
| CLOSE failures (all six files)             | No status check performed after CLOSE -- errors silently ignored               | None (normal end)    | 6000-FINALIZE lines 556-561               |

**Note:** Status '00' is normal completion; status '10' is end-of-file. Any other file status value triggers an immediate abnormal end via CEE3ABD. CLOSE operations are unguarded -- a flush failure on EXPORT-OUTPUT would not be detected.

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. 0000-MAIN-PROCESSING -- entry point; PERFORMs six phases in sequence, then GOBACK
2. 1000-INITIALIZE -- DISPLAY start banner; PERFORM 1050-GENERATE-TIMESTAMP; PERFORM 1100-OPEN-FILES; DISPLAY export date and time
3. 1050-GENERATE-TIMESTAMP -- ACCEPT system date (YYYYMMDD) and time; three STRING operations build WS-EXPORT-DATE (X(10)), WS-EXPORT-TIME (X(08)), WS-FORMATTED-TIMESTAMP (X(26)); hundredths always written as '.00'
4. 1100-OPEN-FILES -- OPEN INPUT all five source files; OPEN OUTPUT EXPORT-OUTPUT; abend on any non-zero file status
5. 2000-EXPORT-CUSTOMERS -- DISPLAY progress; prime-read then PERFORM UNTIL WS-CUSTOMER-EOF; DISPLAY running count
6. 2100-READ-CUSTOMER-RECORD -- READ CUSTOMER-INPUT next sequential record; abend on non-EOF error
7. 2200-CREATE-CUSTOMER-EXP-REC -- INITIALIZE EXPORT-RECORD; set type 'C' and header fields; MOVE 18 customer source fields; WRITE record; ADD 1 to customer and total counters
8. 3000-EXPORT-ACCOUNTS -- DISPLAY progress; prime-read then PERFORM UNTIL WS-ACCOUNT-EOF; DISPLAY running count
9. 3100-READ-ACCOUNT-RECORD -- READ ACCOUNT-INPUT; abend on non-EOF error
10. 3200-CREATE-ACCOUNT-EXP-REC -- INITIALIZE EXPORT-RECORD; set type 'A' and header fields; MOVE 12 account fields; WRITE record; ADD 1 to account and total counters
11. 4000-EXPORT-XREFS -- DISPLAY progress; prime-read then PERFORM UNTIL WS-XREF-EOF; DISPLAY running count
12. 4100-READ-XREF-RECORD -- READ XREF-INPUT; abend on non-EOF error
13. 4200-CREATE-XREF-EXPORT-RECORD -- INITIALIZE EXPORT-RECORD; set type 'X' and header fields; MOVE 3 xref fields; WRITE record; ADD 1 to xref and total counters
14. 5000-EXPORT-TRANSACTIONS -- DISPLAY progress; prime-read then PERFORM UNTIL WS-TRANSACTION-EOF; DISPLAY running count
15. 5100-READ-TRANSACTION-RECORD -- READ TRANSACTION-INPUT; abend on non-EOF error
16. 5200-CREATE-TRAN-EXP-REC -- INITIALIZE EXPORT-RECORD; set type 'T' and header fields; MOVE 13 transaction fields; WRITE record; ADD 1 to transaction and total counters
17. 5500-EXPORT-CARDS -- DISPLAY progress; prime-read then PERFORM UNTIL WS-CARD-EOF; DISPLAY running count
18. 5600-READ-CARD-RECORD -- READ CARD-INPUT; abend on non-EOF error
19. 5700-CREATE-CARD-EXPORT-RECORD -- INITIALIZE EXPORT-RECORD; set type 'D' and header fields; MOVE 6 card fields; WRITE record; ADD 1 to card and total counters
20. 6000-FINALIZE -- CLOSE all six files (no status check); DISPLAY completion banner and five per-type counts, then total; returns to 0000-MAIN-PROCESSING
21. CALL 'CEE3ABD' -- Language Environment service; forces abnormal termination with system dump; invoked only from 9999-ABEND-PROGRAM (line 579)

**Sequence counter:** Starts at 0 (VALUE 0 in WORKING-STORAGE) and increments by 1 for every record written across all five entity types. It forms the EXPORT-SEQUENCE-NUM key for the output file.

**No commit points:** The program is a batch sequential processor with no SYNCPOINT or COMMIT statements. Recovery requires re-running from the start.

**Finalize display order:** SYSOUT statistics in 6000-FINALIZE display in this exact order: 'Export completed', Customers Exported, Accounts Exported, XRefs Exported, Transactions Exported, Cards Exported, Total Records Exported (lines 563-573).
