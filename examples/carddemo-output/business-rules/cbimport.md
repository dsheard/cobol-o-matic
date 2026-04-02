---
type: business-rules
program: CBIMPORT
program_type: batch
status: draft
confidence: high
last_pass: 5
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
- EXPORT-INPUT
writes:
- ACCOUNT-OUTPUT
- CARD-OUTPUT
- CUSTOMER-OUTPUT
- ERROR-OUTPUT
- TRANSACTION-OUTPUT
- XREF-OUTPUT
db_tables: []
transactions: []
mq_queues: []
---

# CBIMPORT -- Business Rules

## Program Purpose

CBIMPORT is a batch program that implements the import side of a branch migration pipeline. It reads a multi-record sequential export file (produced by CBEXPORT) and splits it into five separate normalised VSAM-target sequential files: CUSTOMER-OUTPUT, ACCOUNT-OUTPUT, XREF-OUTPUT, TRANSACTION-OUTPUT, and CARD-OUTPUT. Records that carry an unrecognised record-type indicator are written to a separate ERROR-OUTPUT file. The program is designed as the inverse of CBEXPORT -- together they form the branch data migration path.

Note: paragraph 3000-VALIDATE-IMPORT exists in the source but contains no substantive logic -- it only displays a "no validation errors detected" message. No checksum or count reconciliation is actually performed at runtime.

## Input / Output

| Direction | Resource            | Type | Description                                                                    |
| --------- | ------------------- | ---- | ------------------------------------------------------------------------------ |
| IN        | EXPORT-INPUT        | File | Multi-record indexed sequential export file (DD: EXPFILE); 500-byte fixed records; RECORD KEY is EXPORT-SEQUENCE-NUM (PIC 9(9) COMP); read sequentially |
| OUT       | CUSTOMER-OUTPUT     | File | Sequential file of customer records (DD: CUSTOUT); 500-byte fixed; layout from CVCUS01Y |
| OUT       | ACCOUNT-OUTPUT      | File | Sequential file of account records (DD: ACCTOUT); 300-byte fixed; layout from CVACT01Y |
| OUT       | XREF-OUTPUT         | File | Sequential file of card cross-reference records (DD: XREFOUT); 50-byte fixed; layout from CVACT03Y |
| OUT       | TRANSACTION-OUTPUT  | File | Sequential file of transaction records (DD: TRNXOUT); 350-byte fixed; layout from CVTRA05Y |
| OUT       | CARD-OUTPUT         | File | Sequential file of card records (DD: CARDOUT); 150-byte fixed; layout from CVACT02Y |
| OUT       | ERROR-OUTPUT        | File | Sequential file of error records (DD: ERROUT); 132-byte fixed; pipe-delimited layout defined in WS-ERROR-RECORD |

## Business Rules

### Record Type Routing

| #  | Rule                          | Condition                              | Action                                    | Source Location           |
| -- | ----------------------------- | -------------------------------------- | ----------------------------------------- | ------------------------- |
| 1  | Route customer record         | EXPORT-REC-TYPE = 'C'                  | PERFORM 2300-PROCESS-CUSTOMER-RECORD      | 2200-PROCESS-RECORD-BY-TYPE (line 273) |
| 2  | Route account record          | EXPORT-REC-TYPE = 'A'                  | PERFORM 2400-PROCESS-ACCOUNT-RECORD       | 2200-PROCESS-RECORD-BY-TYPE (line 275) |
| 3  | Route card cross-reference    | EXPORT-REC-TYPE = 'X'                  | PERFORM 2500-PROCESS-XREF-RECORD          | 2200-PROCESS-RECORD-BY-TYPE (line 277) |
| 4  | Route transaction record      | EXPORT-REC-TYPE = 'T'                  | PERFORM 2600-PROCESS-TRAN-RECORD          | 2200-PROCESS-RECORD-BY-TYPE (line 279) |
| 5  | Route card record             | EXPORT-REC-TYPE = 'D'                  | PERFORM 2650-PROCESS-CARD-RECORD          | 2200-PROCESS-RECORD-BY-TYPE (line 281) |
| 6  | Reject unknown record type    | EXPORT-REC-TYPE = any other value      | Increment WS-UNKNOWN-RECORD-TYPE-COUNT; build error record with message 'Unknown record type encountered'; write to ERROR-OUTPUT | 2700-PROCESS-UNKNOWN-RECORD (line 427) |

### Customer Record Mapping (type 'C')

| #  | Rule                                   | Condition                     | Action                                                                            | Source Location              |
| -- | -------------------------------------- | ----------------------------- | --------------------------------------------------------------------------------- | ---------------------------- |
| 7  | Initialise customer record before load | Record type = 'C'             | INITIALIZE CUSTOMER-RECORD (clears all fields before mapping)                     | 2300-PROCESS-CUSTOMER-RECORD (line 290) |
| 8  | Map customer ID                        | Always                        | MOVE EXP-CUST-ID TO CUST-ID (PIC 9(09) COMP -- binary integer)                   | 2300-PROCESS-CUSTOMER-RECORD (line 293) |
| 9  | Map customer name fields               | Always                        | MOVE EXP-CUST-FIRST-NAME (X25), EXP-CUST-MIDDLE-NAME (X25), EXP-CUST-LAST-NAME (X25) to corresponding CUST- fields | 2300-PROCESS-CUSTOMER-RECORD (lines 294-296) |
| 10 | Map address lines (3-element table)    | Always                        | MOVE EXP-CUST-ADDR-LINE(1) TO CUST-ADDR-LINE-1; (2) TO CUST-ADDR-LINE-2; (3) TO CUST-ADDR-LINE-3 (each X50) | 2300-PROCESS-CUSTOMER-RECORD (lines 297-299) |
| 11 | Map address state, country, zip        | Always                        | MOVE EXP-CUST-ADDR-STATE-CD (X02), EXP-CUST-ADDR-COUNTRY-CD (X03), EXP-CUST-ADDR-ZIP (X10) | 2300-PROCESS-CUSTOMER-RECORD (lines 300-302) |
| 12 | Map phone numbers (2-element table)    | Always                        | MOVE EXP-CUST-PHONE-NUM(1) TO CUST-PHONE-NUM-1; (2) TO CUST-PHONE-NUM-2 (each X15) | 2300-PROCESS-CUSTOMER-RECORD (lines 303-304) |
| 13 | Map SSN                                | Always                        | MOVE EXP-CUST-SSN (PIC 9(09) display) TO CUST-SSN                                | 2300-PROCESS-CUSTOMER-RECORD (line 305) |
| 14 | Map government-issued ID               | Always                        | MOVE EXP-CUST-GOVT-ISSUED-ID (X20) TO CUST-GOVT-ISSUED-ID                        | 2300-PROCESS-CUSTOMER-RECORD (line 306) |
| 15 | Map date of birth                      | Always                        | MOVE EXP-CUST-DOB-YYYY-MM-DD (X10) TO CUST-DOB-YYYY-MM-DD                        | 2300-PROCESS-CUSTOMER-RECORD (line 307) |
| 16 | Map EFT account ID                     | Always                        | MOVE EXP-CUST-EFT-ACCOUNT-ID (X10) TO CUST-EFT-ACCOUNT-ID                        | 2300-PROCESS-CUSTOMER-RECORD (line 308) |
| 17 | Map primary card holder indicator      | Always                        | MOVE EXP-CUST-PRI-CARD-HOLDER-IND (X01) TO CUST-PRI-CARD-HOLDER-IND              | 2300-PROCESS-CUSTOMER-RECORD (line 309) |
| 18 | Map FICO credit score                  | Always                        | MOVE EXP-CUST-FICO-CREDIT-SCORE (PIC 9(03) COMP-3) TO CUST-FICO-CREDIT-SCORE     | 2300-PROCESS-CUSTOMER-RECORD (line 310) |
| 19 | Write customer record; abort on error  | WS-CUSTOMER-STATUS NOT = '00' | DISPLAY error message with file status; PERFORM 9999-ABEND-PROGRAM                | 2300-PROCESS-CUSTOMER-RECORD (lines 312-318) |
| 20 | Increment customer counter             | After successful write        | ADD 1 TO WS-CUSTOMER-RECORDS-IMPORTED                                             | 2300-PROCESS-CUSTOMER-RECORD (line 320) |

### Account Record Mapping (type 'A')

| #  | Rule                                  | Condition                     | Action                                                                            | Source Location              |
| -- | ------------------------------------- | ----------------------------- | --------------------------------------------------------------------------------- | ---------------------------- |
| 21 | Initialise account record before load | Record type = 'A'             | INITIALIZE ACCOUNT-RECORD                                                         | 2400-PROCESS-ACCOUNT-RECORD (line 325) |
| 22 | Map account ID                        | Always                        | MOVE EXP-ACCT-ID (PIC 9(11) display) TO ACCT-ID                                  | 2400-PROCESS-ACCOUNT-RECORD (line 328) |
| 23 | Map account active status             | Always                        | MOVE EXP-ACCT-ACTIVE-STATUS (X01) TO ACCT-ACTIVE-STATUS                          | 2400-PROCESS-ACCOUNT-RECORD (line 329) |
| 24 | Map current balance                   | Always                        | MOVE EXP-ACCT-CURR-BAL (S9(10)V99 COMP-3) TO ACCT-CURR-BAL                       | 2400-PROCESS-ACCOUNT-RECORD (line 330) |
| 25 | Map credit limit                      | Always                        | MOVE EXP-ACCT-CREDIT-LIMIT (S9(10)V99 display) TO ACCT-CREDIT-LIMIT              | 2400-PROCESS-ACCOUNT-RECORD (line 331) |
| 26 | Map cash credit limit                 | Always                        | MOVE EXP-ACCT-CASH-CREDIT-LIMIT (S9(10)V99 COMP-3) TO ACCT-CASH-CREDIT-LIMIT     | 2400-PROCESS-ACCOUNT-RECORD (line 332) |
| 27 | Map account dates                     | Always                        | MOVE EXP-ACCT-OPEN-DATE (X10), EXP-ACCT-EXPIRAION-DATE (X10), EXP-ACCT-REISSUE-DATE (X10) to corresponding ACCT- fields | 2400-PROCESS-ACCOUNT-RECORD (lines 333-335) |
| 28 | Map cycle credit / debit              | Always                        | MOVE EXP-ACCT-CURR-CYC-CREDIT (S9(10)V99 display) and EXP-ACCT-CURR-CYC-DEBIT (S9(10)V99 COMP binary) to corresponding ACCT- fields | 2400-PROCESS-ACCOUNT-RECORD (lines 336-337) |
| 29 | Map account zip and group ID          | Always                        | MOVE EXP-ACCT-ADDR-ZIP (X10), EXP-ACCT-GROUP-ID (X10) to corresponding ACCT- fields | 2400-PROCESS-ACCOUNT-RECORD (lines 338-339) |
| 30 | Write account record; abort on error  | WS-ACCOUNT-STATUS NOT = '00'  | DISPLAY error message with file status; PERFORM 9999-ABEND-PROGRAM                | 2400-PROCESS-ACCOUNT-RECORD (lines 341-347) |
| 31 | Increment account counter             | After successful write        | ADD 1 TO WS-ACCOUNT-RECORDS-IMPORTED                                              | 2400-PROCESS-ACCOUNT-RECORD (line 349) |

### Card Cross-Reference Record Mapping (type 'X')

| #  | Rule                                 | Condition                  | Action                                                            | Source Location              |
| -- | ------------------------------------ | -------------------------- | ----------------------------------------------------------------- | ---------------------------- |
| 32 | Initialise XREF record before load   | Record type = 'X'          | INITIALIZE CARD-XREF-RECORD                                       | 2500-PROCESS-XREF-RECORD (line 354) |
| 33 | Map card number                      | Always                     | MOVE EXP-XREF-CARD-NUM (X16) TO XREF-CARD-NUM                    | 2500-PROCESS-XREF-RECORD (line 357) |
| 34 | Map customer ID                      | Always                     | MOVE EXP-XREF-CUST-ID (PIC 9(09) display) TO XREF-CUST-ID        | 2500-PROCESS-XREF-RECORD (line 358) |
| 35 | Map account ID                       | Always                     | MOVE EXP-XREF-ACCT-ID (PIC 9(11) COMP binary) TO XREF-ACCT-ID    | 2500-PROCESS-XREF-RECORD (line 359) |
| 36 | Write XREF record; abort on error    | WS-XREF-STATUS NOT = '00'  | DISPLAY error message with file status; PERFORM 9999-ABEND-PROGRAM | 2500-PROCESS-XREF-RECORD (lines 361-367) |
| 37 | Increment XREF counter               | After successful write     | ADD 1 TO WS-XREF-RECORDS-IMPORTED                                 | 2500-PROCESS-XREF-RECORD (line 369) |

### Transaction Record Mapping (type 'T')

| #  | Rule                                          | Condition                        | Action                                                              | Source Location              |
| -- | --------------------------------------------- | -------------------------------- | ------------------------------------------------------------------- | ---------------------------- |
| 38 | Initialise transaction record before load     | Record type = 'T'                | INITIALIZE TRAN-RECORD                                              | 2600-PROCESS-TRAN-RECORD (line 374) |
| 39 | Map transaction ID                            | Always                           | MOVE EXP-TRAN-ID (X16) TO TRAN-ID                                  | 2600-PROCESS-TRAN-RECORD (line 377) |
| 40 | Map transaction type code                     | Always                           | MOVE EXP-TRAN-TYPE-CD (X02) TO TRAN-TYPE-CD                        | 2600-PROCESS-TRAN-RECORD (line 378) |
| 41 | Map transaction category code                 | Always                           | MOVE EXP-TRAN-CAT-CD (PIC 9(04) display) TO TRAN-CAT-CD            | 2600-PROCESS-TRAN-RECORD (line 379) |
| 42 | Map transaction source                        | Always                           | MOVE EXP-TRAN-SOURCE (X10) TO TRAN-SOURCE                          | 2600-PROCESS-TRAN-RECORD (line 380) |
| 43 | Map transaction description                   | Always                           | MOVE EXP-TRAN-DESC (X100) TO TRAN-DESC                             | 2600-PROCESS-TRAN-RECORD (line 381) |
| 44 | Map transaction amount                        | Always                           | MOVE EXP-TRAN-AMT (S9(09)V99 COMP-3) TO TRAN-AMT                  | 2600-PROCESS-TRAN-RECORD (line 382) |
| 45 | Map merchant ID, name, city, zip              | Always                           | MOVE EXP-TRAN-MERCHANT-ID (PIC 9(09) COMP binary), EXP-TRAN-MERCHANT-NAME (X50), EXP-TRAN-MERCHANT-CITY (X50), EXP-TRAN-MERCHANT-ZIP (X10) to corresponding TRAN- fields | 2600-PROCESS-TRAN-RECORD (lines 383-386) |
| 46 | Map card number on transaction                | Always                           | MOVE EXP-TRAN-CARD-NUM (X16) TO TRAN-CARD-NUM                      | 2600-PROCESS-TRAN-RECORD (line 387) |
| 47 | Map origination and processing timestamps     | Always                           | MOVE EXP-TRAN-ORIG-TS (X26) TO TRAN-ORIG-TS; MOVE EXP-TRAN-PROC-TS (X26) TO TRAN-PROC-TS | 2600-PROCESS-TRAN-RECORD (lines 388-389) |
| 48 | Write transaction record; abort on error      | WS-TRANSACTION-STATUS NOT = '00' | DISPLAY error message with file status; PERFORM 9999-ABEND-PROGRAM  | 2600-PROCESS-TRAN-RECORD (lines 391-397) |
| 49 | Increment transaction counter                 | After successful write           | ADD 1 TO WS-TRAN-RECORDS-IMPORTED                                   | 2600-PROCESS-TRAN-RECORD (line 399) |

### Card Record Mapping (type 'D')

| #  | Rule                               | Condition                    | Action                                                              | Source Location               |
| -- | ---------------------------------- | ---------------------------- | ------------------------------------------------------------------- | ----------------------------- |
| 50 | Initialise card record before load | Record type = 'D'            | INITIALIZE CARD-RECORD                                              | 2650-PROCESS-CARD-RECORD (line 404) |
| 51 | Map card number                    | Always                       | MOVE EXP-CARD-NUM (X16) TO CARD-NUM                                 | 2650-PROCESS-CARD-RECORD (line 407) |
| 52 | Map card account ID                | Always                       | MOVE EXP-CARD-ACCT-ID (PIC 9(11) COMP binary) TO CARD-ACCT-ID      | 2650-PROCESS-CARD-RECORD (line 408) |
| 53 | Map card CVV code                  | Always                       | MOVE EXP-CARD-CVV-CD (PIC 9(03) COMP binary) TO CARD-CVV-CD        | 2650-PROCESS-CARD-RECORD (line 409) |
| 54 | Map embossed name                  | Always                       | MOVE EXP-CARD-EMBOSSED-NAME (X50) TO CARD-EMBOSSED-NAME            | 2650-PROCESS-CARD-RECORD (line 410) |
| 55 | Map card expiration date           | Always                       | MOVE EXP-CARD-EXPIRAION-DATE (X10) TO CARD-EXPIRAION-DATE           | 2650-PROCESS-CARD-RECORD (line 411) |
| 56 | Map card active status             | Always                       | MOVE EXP-CARD-ACTIVE-STATUS (X01) TO CARD-ACTIVE-STATUS             | 2650-PROCESS-CARD-RECORD (line 412) |
| 57 | Write card record; abort on error  | WS-CARD-STATUS NOT = '00'    | DISPLAY error message with file status; PERFORM 9999-ABEND-PROGRAM  | 2650-PROCESS-CARD-RECORD (lines 414-420) |
| 58 | Increment card counter             | After successful write       | ADD 1 TO WS-CARD-RECORDS-IMPORTED                                   | 2650-PROCESS-CARD-RECORD (line 422) |

### Error Record Handling

| #  | Rule                                        | Condition                                   | Action                                                                           | Source Location              |
| -- | ------------------------------------------- | ------------------------------------------- | -------------------------------------------------------------------------------- | ---------------------------- |
| 59 | Build error record for unknown type         | EXPORT-REC-TYPE not in {C, A, X, T, D}      | Populate ERR-TIMESTAMP from FUNCTION CURRENT-DATE (21 chars moved into 26-char field; trailing 5 bytes are spaces), ERR-RECORD-TYPE from EXPORT-REC-TYPE (1 char), ERR-SEQUENCE from EXPORT-SEQUENCE-NUM -- NOTE: source field is PIC 9(9) COMP (9-digit binary) but target ERR-SEQUENCE is PIC 9(07); the MOVE silently truncates to 7 digits, losing any sequence number >= 10,000,000; ERR-MESSAGE = 'Unknown record type encountered' (50 chars); PERFORM 2750-WRITE-ERROR | 2700-PROCESS-UNKNOWN-RECORD (lines 429-434); CVEXPORT.cpy line 16 |
| 60 | Write error record; continue on write error | WS-ERROR-STATUS NOT = '00'                  | DISPLAY 'ERROR: Writing error record, Status: ' WS-ERROR-STATUS -- program does NOT abend; continues processing | 2750-WRITE-ERROR (lines 439-444) |
| 61 | Increment error counter                     | After every call to 2750-WRITE-ERROR        | ADD 1 TO WS-ERROR-RECORDS-WRITTEN                                                | 2750-WRITE-ERROR (line 446) |

### Validation Stub (No-op)

| #  | Rule                              | Condition | Action                                                                                                  | Source Location             |
| -- | --------------------------------- | --------- | ------------------------------------------------------------------------------------------------------- | --------------------------- |
| 62 | Import validation is a no-op stub | Always    | DISPLAY 'CBIMPORT: Import validation completed'; DISPLAY 'CBIMPORT: No validation errors detected' -- no actual data validation is performed; counts are not reconciled against any header or trailer record | 3000-VALIDATE-IMPORT (lines 451-452) |

### Data Loss / Silently Discarded Fields

| #  | Rule                                                   | Condition | Action                                                                                                                                                          | Source Location              |
| -- | ------------------------------------------------------ | --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| 63 | EXPORT-BRANCH-ID not mapped to any output record       | Always    | EXPORT-BRANCH-ID (PIC X(04), bytes 28-31 of every export record, defined in CVEXPORT common header) is read but never moved to any output file; branch provenance is lost on import | CVEXPORT.cpy line 17; no MOVE in any paragraph |
| 64 | EXPORT-REGION-CODE not mapped to any output record     | Always    | EXPORT-REGION-CODE (PIC X(05), bytes 32-36 of every export record, defined in CVEXPORT common header) is read but never moved to any output file; region provenance is lost on import | CVEXPORT.cpy line 18; no MOVE in any paragraph |
| 65 | EXPORT-TIMESTAMP not mapped to any output record       | Always    | EXPORT-TIMESTAMP (PIC X(26), bytes 2-27 of every export record -- the original export creation timestamp, with REDEFINES subfields EXPORT-DATE X(10), EXPORT-DATE-TIME-SEP X(1), EXPORT-TIME X(15)) is read but never moved to any output file; the original export date and time are lost on import | CVEXPORT.cpy lines 11-15; no MOVE in any paragraph |

## Calculations

| Calculation                 | Formula / Logic                                          | Input Fields                          | Output Field                      | Source Location              |
| --------------------------- | -------------------------------------------------------- | ------------------------------------- | --------------------------------- | ---------------------------- |
| Total records read          | ADD 1 TO counter for each record read from EXPORT-INPUT  | WS-TOTAL-RECORDS-READ                 | WS-TOTAL-RECORDS-READ             | 2000-PROCESS-EXPORT-FILE (line 253) |
| Customer records imported   | ADD 1 after each successful CUSTOMER-OUTPUT write        | WS-CUSTOMER-RECORDS-IMPORTED          | WS-CUSTOMER-RECORDS-IMPORTED      | 2300-PROCESS-CUSTOMER-RECORD (line 320) |
| Account records imported    | ADD 1 after each successful ACCOUNT-OUTPUT write         | WS-ACCOUNT-RECORDS-IMPORTED           | WS-ACCOUNT-RECORDS-IMPORTED       | 2400-PROCESS-ACCOUNT-RECORD (line 349) |
| XREF records imported       | ADD 1 after each successful XREF-OUTPUT write            | WS-XREF-RECORDS-IMPORTED              | WS-XREF-RECORDS-IMPORTED          | 2500-PROCESS-XREF-RECORD (line 369) |
| Transaction records imported| ADD 1 after each successful TRANSACTION-OUTPUT write     | WS-TRAN-RECORDS-IMPORTED              | WS-TRAN-RECORDS-IMPORTED          | 2600-PROCESS-TRAN-RECORD (line 399) |
| Card records imported       | ADD 1 after each successful CARD-OUTPUT write            | WS-CARD-RECORDS-IMPORTED              | WS-CARD-RECORDS-IMPORTED          | 2650-PROCESS-CARD-RECORD (line 422) |
| Error records written       | ADD 1 after each call to 2750-WRITE-ERROR                | WS-ERROR-RECORDS-WRITTEN              | WS-ERROR-RECORDS-WRITTEN          | 2750-WRITE-ERROR (line 446) |
| Unknown record type count   | ADD 1 for each record where type not in {C,A,X,T,D}     | WS-UNKNOWN-RECORD-TYPE-COUNT          | WS-UNKNOWN-RECORD-TYPE-COUNT      | 2700-PROCESS-UNKNOWN-RECORD (line 427) |
| Import date construction    | Concatenate CURRENT-DATE subfields: YYYY(1:4) + '-' + MM(5:2) + '-' + DD(7:2) | FUNCTION CURRENT-DATE | WS-IMPORT-DATE (X10)             | 1000-INITIALIZE (lines 178-182) |
| Import time construction    | Concatenate CURRENT-DATE subfields: HH(9:2) + ':' + MI(11:2) + ':' + SS(13:2) | FUNCTION CURRENT-DATE | WS-IMPORT-TIME (X08)             | 1000-INITIALIZE (lines 184-188) |

## Error Handling

| Condition                                         | Action                                                                                       | Return Code / Status | Source Location              |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------- | -------------------- | ---------------------------- |
| EXPORT-INPUT cannot be opened (status not '00')   | DISPLAY 'ERROR: Cannot open EXPORT-INPUT, Status: ' WS-EXPORT-STATUS; PERFORM 9999-ABEND-PROGRAM | N/A -- abend    | 1100-OPEN-FILES (lines 199-203) |
| CUSTOMER-OUTPUT cannot be opened (status not '00')| DISPLAY 'ERROR: Cannot open CUSTOMER-OUTPUT, Status: ' WS-CUSTOMER-STATUS; PERFORM 9999-ABEND-PROGRAM | N/A -- abend  | 1100-OPEN-FILES (lines 206-210) |
| ACCOUNT-OUTPUT cannot be opened (status not '00') | DISPLAY 'ERROR: Cannot open ACCOUNT-OUTPUT, Status: ' WS-ACCOUNT-STATUS; PERFORM 9999-ABEND-PROGRAM | N/A -- abend   | 1100-OPEN-FILES (lines 213-217) |
| XREF-OUTPUT cannot be opened (status not '00')    | DISPLAY 'ERROR: Cannot open XREF-OUTPUT, Status: ' WS-XREF-STATUS; PERFORM 9999-ABEND-PROGRAM | N/A -- abend      | 1100-OPEN-FILES (lines 220-224) |
| TRANSACTION-OUTPUT cannot be opened (not '00')    | DISPLAY 'ERROR: Cannot open TRANSACTION-OUTPUT, Status: ' WS-TRANSACTION-STATUS; PERFORM 9999-ABEND-PROGRAM | N/A -- abend | 1100-OPEN-FILES (lines 227-231) |
| CARD-OUTPUT cannot be opened (status not '00')    | DISPLAY 'ERROR: Cannot open CARD-OUTPUT, Status: ' WS-CARD-STATUS; PERFORM 9999-ABEND-PROGRAM | N/A -- abend     | 1100-OPEN-FILES (lines 233-238) |
| ERROR-OUTPUT cannot be opened (status not '00')   | DISPLAY 'ERROR: Cannot open ERROR-OUTPUT, Status: ' WS-ERROR-STATUS; PERFORM 9999-ABEND-PROGRAM | N/A -- abend   | 1100-OPEN-FILES (lines 241-245) |
| EXPORT-INPUT read returns status not '00' and not '10' (EOF) | DISPLAY 'ERROR: Reading EXPORT-INPUT, Status: ' WS-EXPORT-STATUS; PERFORM 9999-ABEND-PROGRAM | N/A -- abend | 2100-READ-EXPORT-RECORD (lines 263-267) |
| CUSTOMER-OUTPUT write fails (status not '00')     | DISPLAY 'ERROR: Writing customer record, Status: ' WS-CUSTOMER-STATUS; PERFORM 9999-ABEND-PROGRAM | N/A -- abend  | 2300-PROCESS-CUSTOMER-RECORD (lines 314-318) |
| ACCOUNT-OUTPUT write fails (status not '00')      | DISPLAY 'ERROR: Writing account record, Status: ' WS-ACCOUNT-STATUS; PERFORM 9999-ABEND-PROGRAM | N/A -- abend   | 2400-PROCESS-ACCOUNT-RECORD (lines 343-347) |
| XREF-OUTPUT write fails (status not '00')         | DISPLAY 'ERROR: Writing xref record, Status: ' WS-XREF-STATUS; PERFORM 9999-ABEND-PROGRAM | N/A -- abend         | 2500-PROCESS-XREF-RECORD (lines 363-367) |
| TRANSACTION-OUTPUT write fails (status not '00')  | DISPLAY 'ERROR: Writing transaction record, Status: ' WS-TRANSACTION-STATUS; PERFORM 9999-ABEND-PROGRAM | N/A -- abend | 2600-PROCESS-TRAN-RECORD (lines 393-397) |
| CARD-OUTPUT write fails (status not '00')         | DISPLAY 'ERROR: Writing card record, Status: ' WS-CARD-STATUS; PERFORM 9999-ABEND-PROGRAM | N/A -- abend        | 2650-PROCESS-CARD-RECORD (lines 416-420) |
| ERROR-OUTPUT write fails (status not '00')        | DISPLAY 'ERROR: Writing error record, Status: ' WS-ERROR-STATUS -- program continues (no abend) | Degraded -- errors lost | 2750-WRITE-ERROR (lines 441-444) |
| All seven CLOSE statements in 4000-FINALIZE       | No file-status check is performed after any CLOSE -- close errors are silently ignored; statistics are still displayed and program GOBACKs normally | Silent data loss possible | 4000-FINALIZE (lines 457-463) |
| Abend invoked (9999-ABEND-PROGRAM)                | DISPLAY 'CBIMPORT: ABENDING PROGRAM'; CALL 'CEE3ABD' -- LE runtime abend with dump            | Platform dump        | 9999-ABEND-PROGRAM (lines 483-484) |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. 0000-MAIN-PROCESSING -- entry point; dispatches the four top-level phases in sequence then GOBACKs
2. 1000-INITIALIZE -- captures system date and time into WS-IMPORT-DATE / WS-IMPORT-TIME; calls 1100-OPEN-FILES
3. 1100-OPEN-FILES -- opens all seven files (one INPUT, six OUTPUT); abends immediately on any file-open failure
4. 2000-PROCESS-EXPORT-FILE -- priming read followed by PERFORM UNTIL WS-EXPORT-EOF loop; increments WS-TOTAL-RECORDS-READ per record; calls 2200-PROCESS-RECORD-BY-TYPE per record
5. 2100-READ-EXPORT-RECORD -- issues READ EXPORT-INPUT INTO EXPORT-RECORD; abends on I/O error (status not '00' and not '10')
6. 2200-PROCESS-RECORD-BY-TYPE -- EVALUATE on EXPORT-REC-TYPE; routes to one of five typed-record paragraphs or to 2700-PROCESS-UNKNOWN-RECORD
7. 2300-PROCESS-CUSTOMER-RECORD -- INITIALIZE + 18-field MOVE mapping + WRITE CUSTOMER-RECORD + counter increment; abends on write failure
8. 2400-PROCESS-ACCOUNT-RECORD -- INITIALIZE + 12-field MOVE mapping + WRITE ACCOUNT-RECORD + counter increment; abends on write failure
9. 2500-PROCESS-XREF-RECORD -- INITIALIZE + 3-field MOVE mapping + WRITE CARD-XREF-RECORD + counter increment; abends on write failure
10. 2600-PROCESS-TRAN-RECORD -- INITIALIZE + 13-field MOVE mapping + WRITE TRAN-RECORD + counter increment; abends on write failure
11. 2650-PROCESS-CARD-RECORD -- INITIALIZE + 6-field MOVE mapping + WRITE CARD-RECORD + counter increment; abends on write failure
12. 2700-PROCESS-UNKNOWN-RECORD -- increments unknown-type counter; populates WS-ERROR-RECORD (ERR-SEQUENCE sourced from EXPORT-SEQUENCE-NUM, a 9-digit COMP field truncated to the 7-digit ERR-SEQUENCE); calls 2750-WRITE-ERROR
13. 2750-WRITE-ERROR -- writes WS-ERROR-RECORD to ERROR-OUTPUT; logs file-status warning but does NOT abend on write failure; increments WS-ERROR-RECORDS-WRITTEN
14. 3000-VALIDATE-IMPORT -- stub only; displays fixed messages; performs no actual validation or count reconciliation
15. 4000-FINALIZE -- closes all seven files (no close-status checking); displays final statistics (total read, each record type count, errors written, unknown count)
16. CALL 'CEE3ABD' -- LE runtime abend with memory dump; invoked from 9999-ABEND-PROGRAM on any fatal I/O error
