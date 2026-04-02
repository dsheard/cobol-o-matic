---
type: business-rules
program: CBTRN02C
program_type: batch
status: draft
confidence: high
last_pass: 4
calls:
- CEE3ABD
called_by: []
uses_copybooks:
- CVACT01Y
- CVACT03Y
- CVTRA01Y
- CVTRA05Y
- CVTRA06Y
reads:
- ACCOUNT-FILE
- DALYREJS-FILE
- DALYTRAN-FILE
- TCATBAL-FILE
- TRANSACT-FILE
- XREF-FILE
writes:
- DALYREJS-FILE
- TCATBAL-FILE
- TRANSACT-FILE
- ACCOUNT-FILE
db_tables: []
transactions: []
mq_queues: []
---

# CBTRN02C -- Business Rules

## Program Purpose

CBTRN02C is a batch COBOL program that posts daily credit card transactions from
a sequential input file (DALYTRAN-FILE) to the permanent transaction store.  For
each input record it: (1) validates the card number against a cross-reference
file, (2) validates the resolved account exists and the transaction does not
exceed the credit limit or account expiration date, (3) updates the
transaction-category balance file, (4) updates the account master balance
fields, and (5) writes the validated transaction to the permanent transaction
file.  Transactions that fail any validation step are written to a daily-rejects
file with a numeric reason code and human-readable description.  At end of job
the program sets RETURN-CODE = 4 if any transactions were rejected, allowing
the JCL to detect a partial-success condition.

## Input / Output

| Direction | Resource       | Type | Description                                                          |
| --------- | -------------- | ---- | -------------------------------------------------------------------- |
| IN        | DALYTRAN-FILE  | File | Sequential daily transaction input file (DALYTRAN, record 350 bytes) |
| IN        | XREF-FILE      | File | Card-number-to-account cross-reference (XREFFILE, indexed by card number, record 50 bytes) |
| IN/OUT    | ACCOUNT-FILE   | File | Account master file (ACCTFILE, opened I-O for read and rewrite, indexed by account ID, record 300 bytes) |
| IN/OUT    | TCATBAL-FILE   | File | Transaction category balance file (TCATBALF, opened I-O for read/write/rewrite, indexed by acct+type+category, record 50 bytes) |
| OUT       | TRANSACT-FILE  | File | Permanent transaction file (TRANFILE, opened OUTPUT -- destructive each run -- indexed by transaction ID, record 350 bytes) |
| OUT       | DALYREJS-FILE  | File | Daily transaction rejects file (DALYREJS, opened OUTPUT -- destructive each run -- sequential, record 430 bytes) |

## Business Rules

### Transaction Processing Loop

| #  | Rule                              | Condition                                           | Action                                                              | Source Location        |
| -- | --------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------- | ---------------------- |
| 1  | Read next daily transaction       | END-OF-FILE = 'N'                                   | PERFORM 1000-DALYTRAN-GET-NEXT to read next sequential record       | PROCEDURE DIVISION main loop, line 204 |
| 2  | Count every transaction attempted | After successful read (END-OF-FILE still 'N')       | ADD 1 TO WS-TRANSACTION-COUNT                                       | Main loop, line 206    |
| 3  | Clear validation state per record | Before each validation                              | MOVE 0 TO WS-VALIDATION-FAIL-REASON; MOVE SPACES TO WS-VALIDATION-FAIL-REASON-DESC | Main loop, lines 208-209 |
| 4  | Route valid transactions to post  | WS-VALIDATION-FAIL-REASON = 0 after 1500-VALIDATE-TRAN | PERFORM 2000-POST-TRANSACTION                                   | Main loop, line 212    |
| 5  | Route failed transactions to reject | WS-VALIDATION-FAIL-REASON not = 0                 | ADD 1 TO WS-REJECT-COUNT; PERFORM 2500-WRITE-REJECT-REC             | Main loop, lines 214-215 |
| 6  | Set non-zero return code on rejects | WS-REJECT-COUNT > 0 at end of job                 | MOVE 4 TO RETURN-CODE (allows JCL condition code checking)          | Main loop, lines 229-231 |
| 7  | TRANSACT-FILE is truncated on open | OPEN OUTPUT TRANSACT-FILE at job start             | Any existing records in TRANSACT-FILE are destroyed; only today's valid transactions are present after the run | 0100-TRANFILE-OPEN, line 256 |
| 8  | DALYREJS-FILE is truncated on open | OPEN OUTPUT DALYREJS-FILE at job start             | Any existing rejects from a prior run are destroyed; only today's rejects are present after the run | 0300-DALYREJS-OPEN, line 293 |

### Validation -- Card Number Lookup (1500-A-LOOKUP-XREF)

| #  | Rule                              | Condition                                           | Action                                                              | Source Location        |
| -- | --------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------- | ---------------------- |
| 9  | Card number must exist in XREF    | READ XREF-FILE INVALID KEY (card number not found) | MOVE 100 TO WS-VALIDATION-FAIL-REASON; MOVE 'INVALID CARD NUMBER FOUND' TO WS-VALIDATION-FAIL-REASON-DESC | 1500-A-LOOKUP-XREF, lines 384-387 |
| 10 | Card number lookup key            | DALYTRAN-CARD-NUM (PIC X(16)) used as key          | MOVE DALYTRAN-CARD-NUM TO FD-XREF-CARD-NUM before READ             | 1500-A-LOOKUP-XREF, line 382 |
| 11 | Cross-reference lookup resolves account ID | NOT INVALID KEY on XREF READ                | XREF-ACCT-ID (PIC 9(11)) is available for subsequent account lookup | 1500-A-LOOKUP-XREF, line 390 |

### Validation -- Account Record Lookup and Business Checks (1500-B-LOOKUP-ACCT)

| #  | Rule                                    | Condition                                                            | Action                                                                          | Source Location               |
| -- | --------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ----------------------------- |
| 12 | Account lookup only runs if card is valid | IF WS-VALIDATION-FAIL-REASON = 0 (from XREF step)                 | PERFORM 1500-B-LOOKUP-ACCT; otherwise CONTINUE                                 | 1500-VALIDATE-TRAN, lines 372-375 |
| 13 | Account must exist in account master    | READ ACCOUNT-FILE INVALID KEY (XREF-ACCT-ID not found)             | MOVE 101 TO WS-VALIDATION-FAIL-REASON; MOVE 'ACCOUNT RECORD NOT FOUND' TO WS-VALIDATION-FAIL-REASON-DESC | 1500-B-LOOKUP-ACCT, lines 396-399 |
| 14 | Account lookup key                      | XREF-ACCT-ID (resolved from XREF record) used as key               | MOVE XREF-ACCT-ID TO FD-ACCT-ID before READ                                   | 1500-B-LOOKUP-ACCT, line 394 |
| 15 | Overlimit check uses cycle net balance  | COMPUTE WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT; IF ACCT-CREDIT-LIMIT < WS-TEMP-BAL | MOVE 102 TO WS-VALIDATION-FAIL-REASON; MOVE 'OVERLIMIT TRANSACTION' TO WS-VALIDATION-FAIL-REASON-DESC | 1500-B-LOOKUP-ACCT, lines 403-412 |
| 16 | Overlimit check uses current cycle balances, not total current balance | WS-TEMP-BAL based on ACCT-CURR-CYC-CREDIT and ACCT-CURR-CYC-DEBIT (cycle-to-date), not ACCT-CURR-BAL (all-time) | This means prior-cycle carry-forward balance is excluded from the overlimit calculation -- potential business logic gap | 1500-B-LOOKUP-ACCT, lines 403-405 |
| 17 | Transaction must not be received after account expiration | Code: IF ACCT-EXPIRAION-DATE >= DALYTRAN-ORIG-TS(1:10) CONTINUE ELSE fail -- i.e. reject when expiration date is earlier than the first 10 characters (date portion) of the transaction origination timestamp | MOVE 103 TO WS-VALIDATION-FAIL-REASON; MOVE 'TRANSACTION RECEIVED AFTER ACCT EXPIRATION' TO WS-VALIDATION-FAIL-REASON-DESC | 1500-B-LOOKUP-ACCT, lines 414-419 |
| 18 | Expiration date field has a typo in its name | Field is ACCT-EXPIRAION-DATE (missing 'T' in EXPIRATION) | No functional impact -- the copybook defines it this way -- but affects maintenance and search | 1500-B-LOOKUP-ACCT, line 414 |
| 19 | Validation extension point          | Comment '* ADD MORE VALIDATIONS HERE' follows END-IF             | No logic -- marks intended extension point for additional validators         | 1500-VALIDATE-TRAN, line 377 |
| 20 | Both overlimit and expiration checks run independently | No short-circuit between rules 15 and 17 | If overlimit fails (reason 102), the expiration check still runs and may overwrite reason with 103 -- last failing check wins | 1500-B-LOOKUP-ACCT, lines 403-420 |

### Transaction Posting (2000-POST-TRANSACTION)

| #  | Rule                                          | Condition                 | Action                                                                                                   | Source Location             |
| -- | --------------------------------------------- | ------------------------- | -------------------------------------------------------------------------------------------------------- | --------------------------- |
| 21 | Map all daily transaction fields to TRAN-RECORD | Always (when valid)     | MOVE DALYTRAN-ID, TYPE-CD, CAT-CD, SOURCE, DESC, AMT, MERCHANT-ID, MERCHANT-NAME, MERCHANT-CITY, MERCHANT-ZIP, CARD-NUM, ORIG-TS to corresponding TRAN-* fields | 2000-POST-TRANSACTION, lines 425-436 |
| 22 | Assign processing timestamp at post time      | Always (when valid)       | PERFORM Z-GET-DB2-FORMAT-TIMESTAMP; MOVE DB2-FORMAT-TS TO TRAN-PROC-TS                                  | 2000-POST-TRANSACTION, lines 437-438 |
| 23 | Update transaction category balance           | Always (when valid)       | PERFORM 2700-UPDATE-TCATBAL                                                                              | 2000-POST-TRANSACTION, line 440 |
| 24 | Update account master balances                | Always (when valid)       | PERFORM 2800-UPDATE-ACCOUNT-REC                                                                          | 2000-POST-TRANSACTION, line 441 |
| 25 | Write to permanent transaction file           | Always (when valid)       | PERFORM 2900-WRITE-TRANSACTION-FILE                                                                      | 2000-POST-TRANSACTION, line 442 |
| 37 | TRAN-RECORD does not contain account ID       | Structural (CVTRA05Y copybook) | TRAN-RECORD fields: TRAN-ID, TRAN-TYPE-CD, TRAN-CAT-CD, TRAN-SOURCE, TRAN-DESC, TRAN-AMT, TRAN-MERCHANT-ID, TRAN-MERCHANT-NAME, TRAN-MERCHANT-CITY, TRAN-MERCHANT-ZIP, TRAN-CARD-NUM, TRAN-ORIG-TS, TRAN-PROC-TS, FILLER(20). No TRAN-ACCT-ID field exists. Account linkage in the permanent transaction store can only be recovered by re-joining through XREF-FILE using TRAN-CARD-NUM. | CVTRA05Y copybook, lines 4-18 |
| 38 | Input DALYTRAN-PROC-TS is discarded           | Always (when valid)       | DALYTRAN-RECORD contains DALYTRAN-PROC-TS (PIC X(26)) but it is never copied to TRAN-PROC-TS. TRAN-PROC-TS is always set from FUNCTION CURRENT-DATE at the time of batch posting, discarding any timestamp carried in the input record. | 2000-POST-TRANSACTION, lines 436-438; CVTRA06Y copybook |

### Reject Record Composition (2500-WRITE-REJECT-REC)

| #  | Rule                                          | Condition                 | Action                                                                                                   | Source Location             |
| -- | --------------------------------------------- | ------------------------- | -------------------------------------------------------------------------------------------------------- | --------------------------- |
| 26 | Reject record contains full original transaction | Always on reject path  | MOVE DALYTRAN-RECORD TO REJECT-TRAN-DATA (X(350)); MOVE WS-VALIDATION-TRAILER TO VALIDATION-TRAILER (X(80)) | 2500-WRITE-REJECT-REC, lines 447-448 |
| 27 | Reject trailer layout                         | WS-VALIDATION-TRAILER = WS-VALIDATION-FAIL-REASON (PIC 9(04)) + WS-VALIDATION-FAIL-REASON-DESC (PIC X(76)) | Trailer is exactly 80 bytes appended to the 350-byte transaction copy; total reject record = 430 bytes | FILE SECTION, lines 82-84; WORKING-STORAGE, lines 180-182 |

### Transaction Category Balance Maintenance (2700-UPDATE-TCATBAL)

| #  | Rule                                               | Condition                                            | Action                                                                                    | Source Location            |
| -- | -------------------------------------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------- | -------------------------- |
| 28 | Look up transaction category balance record        | Key = XREF-ACCT-ID + DALYTRAN-TYPE-CD + DALYTRAN-CAT-CD | READ TCATBAL-FILE; set WS-CREATE-TRANCAT-REC = 'N' initially                          | 2700-UPDATE-TCATBAL, lines 469-479 |
| 29 | TCATBAL key is composite: account + type + category | FD-TRAN-CAT-KEY = FD-TRANCAT-ACCT-ID (9(11)) + FD-TRANCAT-TYPE-CD (X(02)) + FD-TRANCAT-CD (9(04)) | One balance record per account per transaction type per category | 2700-UPDATE-TCATBAL, lines 469-471; FILE SECTION lines 93-96 |
| 30 | Create new category balance record if not found    | READ TCATBAL-FILE INVALID KEY (status '23')          | DISPLAY 'TCATBAL record not found for key: ... Creating.'; MOVE 'Y' TO WS-CREATE-TRANCAT-REC; branch to 2700-A-CREATE-TCATBAL-REC | 2700-UPDATE-TCATBAL, lines 475-478 |
| 31 | Update existing category balance record if found   | READ TCATBAL-FILE NOT INVALID KEY (WS-CREATE-TRANCAT-REC = 'N') | PERFORM 2700-B-UPDATE-TCATBAL-REC                                             | 2700-UPDATE-TCATBAL, lines 495-499 |
| 32 | Accept status '00' or '23' as non-error on TCATBAL read | TCATBALF-STATUS = '00' OR '23'                 | MOVE 0 TO APPL-RESULT (status '23' = record not found is expected / handled)             | 2700-UPDATE-TCATBAL, lines 481-482 |

### Account Balance Update (2800-UPDATE-ACCOUNT-REC)

| #  | Rule                                            | Condition                     | Action                                                                    | Source Location               |
| -- | ----------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------- | ----------------------------- |
| 33 | Always add transaction amount to current balance | Unconditional                 | ADD DALYTRAN-AMT TO ACCT-CURR-BAL                                        | 2800-UPDATE-ACCOUNT-REC, line 547 |
| 34 | Positive amount (credit) updates cycle credit   | DALYTRAN-AMT >= 0             | ADD DALYTRAN-AMT TO ACCT-CURR-CYC-CREDIT                                 | 2800-UPDATE-ACCOUNT-REC, lines 548-549 |
| 35 | Negative amount (debit/payment) updates cycle debit | DALYTRAN-AMT < 0          | ADD DALYTRAN-AMT TO ACCT-CURR-CYC-DEBIT                                  | 2800-UPDATE-ACCOUNT-REC, lines 550-551 |
| 36 | Account record must be rewritable               | REWRITE FD-ACCTFILE-REC INVALID KEY | MOVE 109 TO WS-VALIDATION-FAIL-REASON; MOVE 'ACCOUNT RECORD NOT FOUND' TO WS-VALIDATION-FAIL-REASON-DESC -- no reject write or abend follows (see defect note below) | 2800-UPDATE-ACCOUNT-REC, lines 554-558 |

## Calculations

| Calculation                     | Formula / Logic                                                                                       | Input Fields                                                                  | Output Field       | Source Location           |
| ------------------------------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------------------ | ------------------------- |
| Projected balance for overlimit check | WS-TEMP-BAL = ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT                        | ACCT-CURR-CYC-CREDIT (S9(10)V99), ACCT-CURR-CYC-DEBIT (S9(10)V99), DALYTRAN-AMT (S9(09)V99) | WS-TEMP-BAL (S9(09)V99) | 1500-B-LOOKUP-ACCT, lines 403-405 |
| Credit limit check              | IF ACCT-CREDIT-LIMIT >= WS-TEMP-BAL then OK, else OVERLIMIT                                          | ACCT-CREDIT-LIMIT (S9(10)V99), WS-TEMP-BAL                                   | WS-VALIDATION-FAIL-REASON = 102 on failure | 1500-B-LOOKUP-ACCT, line 407 |
| Current balance update          | ADD DALYTRAN-AMT TO ACCT-CURR-BAL (signed addition; positive = charge, negative = payment/credit)    | DALYTRAN-AMT (S9(09)V99)                                                    | ACCT-CURR-BAL (S9(10)V99) | 2800-UPDATE-ACCOUNT-REC, line 547 |
| Cycle credit accumulation       | ADD DALYTRAN-AMT TO ACCT-CURR-CYC-CREDIT when DALYTRAN-AMT >= 0                                      | DALYTRAN-AMT                                                                  | ACCT-CURR-CYC-CREDIT (S9(10)V99) | 2800-UPDATE-ACCOUNT-REC, line 549 |
| Cycle debit accumulation        | ADD DALYTRAN-AMT TO ACCT-CURR-CYC-DEBIT when DALYTRAN-AMT < 0                                        | DALYTRAN-AMT                                                                  | ACCT-CURR-CYC-DEBIT (S9(10)V99) | 2800-UPDATE-ACCOUNT-REC, line 551 |
| Category balance -- new record  | INITIALIZE TRAN-CAT-BAL-RECORD (zeros all fields); ADD DALYTRAN-AMT TO TRAN-CAT-BAL (starts from zero) | DALYTRAN-AMT                                                                | TRAN-CAT-BAL (S9(09)V99) | 2700-A-CREATE-TCATBAL-REC, lines 504-508 |
| Category balance -- existing record | ADD DALYTRAN-AMT TO TRAN-CAT-BAL (accumulates onto existing balance)                             | DALYTRAN-AMT, TRAN-CAT-BAL (existing)                                         | TRAN-CAT-BAL (S9(09)V99) | 2700-B-UPDATE-TCATBAL-REC, line 527 |
| DB2-format processing timestamp | YYYY-MM-DD-HH.MIN.SS.MIL0000 constructed from FUNCTION CURRENT-DATE; separator chars are '-' for date parts and '.' for time parts; milliseconds field is 2-digit (COB-MIL cast to DB2-MIL PIC 9(002)); trailing 4 characters are literal '0000' | FUNCTION CURRENT-DATE components (COB-YYYY, COB-MM, COB-DD, COB-HH, COB-MIN, COB-SS, COB-MIL) | DB2-FORMAT-TS (X(26)); TRAN-PROC-TS | Z-GET-DB2-FORMAT-TIMESTAMP, lines 693-703 |

## Error Handling

| Condition                                           | Action                                                                                                        | Return Code / Reason | Source Location                     |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | -------------------- | ----------------------------------- |
| DALYTRAN-FILE OPEN fails (status != '00')           | DISPLAY 'ERROR OPENING DALYTRAN'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM                  | Abend (CEE3ABD, code 999) | 0000-DALYTRAN-OPEN, lines 247-250 |
| TRANSACT-FILE OPEN fails (status != '00')           | DISPLAY 'ERROR OPENING TRANSACTION FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM          | Abend (CEE3ABD, code 999) | 0100-TRANFILE-OPEN, lines 265-268 |
| XREF-FILE OPEN fails (status != '00')               | DISPLAY 'ERROR OPENING CROSS REF FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM            | Abend (CEE3ABD, code 999) | 0200-XREFFILE-OPEN, lines 284-287 |
| DALYREJS-FILE OPEN fails (status != '00')           | DISPLAY 'ERROR OPENING DALY REJECTS FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM         | Abend (CEE3ABD, code 999) | 0300-DALYREJS-OPEN, lines 302-305 |
| ACCOUNT-FILE OPEN fails (status != '00')            | DISPLAY 'ERROR OPENING ACCOUNT MASTER FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM       | Abend (CEE3ABD, code 999) | 0400-ACCTFILE-OPEN, lines 320-323 |
| TCATBAL-FILE OPEN fails (status != '00')            | DISPLAY 'ERROR OPENING TRANSACTION BALANCE FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM  | Abend (CEE3ABD, code 999) | 0500-TCATBALF-OPEN, lines 338-341 |
| DALYTRAN-FILE READ -- end of file (status '10')     | MOVE 16 TO APPL-RESULT; 88 APPL-EOF is TRUE; MOVE 'Y' TO END-OF-FILE; loop exits normally                    | None (normal termination) | 1000-DALYTRAN-GET-NEXT, lines 351-361 |
| DALYTRAN-FILE READ -- unexpected error (status not '00' and not '10') | DISPLAY 'ERROR READING DALYTRAN FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | Abend (CEE3ABD, code 999) | 1000-DALYTRAN-GET-NEXT, lines 363-366 |
| Card number not found in XREF (INVALID KEY)         | MOVE 100 TO WS-VALIDATION-FAIL-REASON; MOVE 'INVALID CARD NUMBER FOUND' TO WS-VALIDATION-FAIL-REASON-DESC; transaction rejected | Reject reason 100 | 1500-A-LOOKUP-XREF, lines 385-387 |
| Account ID not found in ACCOUNT-FILE (INVALID KEY)  | MOVE 101 TO WS-VALIDATION-FAIL-REASON; MOVE 'ACCOUNT RECORD NOT FOUND' TO WS-VALIDATION-FAIL-REASON-DESC; transaction rejected | Reject reason 101 | 1500-B-LOOKUP-ACCT, lines 397-399 |
| Transaction amount would exceed credit limit        | MOVE 102 TO WS-VALIDATION-FAIL-REASON; MOVE 'OVERLIMIT TRANSACTION' TO WS-VALIDATION-FAIL-REASON-DESC; transaction rejected | Reject reason 102 | 1500-B-LOOKUP-ACCT, lines 410-412 |
| Transaction originated after account expiration date | MOVE 103 TO WS-VALIDATION-FAIL-REASON; MOVE 'TRANSACTION RECEIVED AFTER ACCT EXPIRATION' TO WS-VALIDATION-FAIL-REASON-DESC; transaction rejected | Reject reason 103 | 1500-B-LOOKUP-ACCT, lines 417-419 |
| DALYREJS-FILE WRITE fails (status != '00')          | DISPLAY 'ERROR WRITING TO REJECTS FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM           | Abend (CEE3ABD, code 999) | 2500-WRITE-REJECT-REC, lines 460-463 |
| TCATBAL-FILE READ error (status not '00' or '23')   | DISPLAY 'ERROR READING TRANSACTION BALANCE FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM  | Abend (CEE3ABD, code 999) | 2700-UPDATE-TCATBAL, lines 489-492 |
| TCATBAL-FILE WRITE fails (status != '00')           | DISPLAY 'ERROR WRITING TRANSACTION BALANCE FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM  | Abend (CEE3ABD, code 999) | 2700-A-CREATE-TCATBAL-REC, lines 520-523 |
| TCATBAL-FILE REWRITE fails (status != '00')         | DISPLAY 'ERROR REWRITING TRANSACTION BALANCE FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | Abend (CEE3ABD, code 999) | 2700-B-UPDATE-TCATBAL-REC, lines 538-541 |
| ACCOUNT-FILE REWRITE INVALID KEY                    | MOVE 109 TO WS-VALIDATION-FAIL-REASON; MOVE 'ACCOUNT RECORD NOT FOUND' TO WS-VALIDATION-FAIL-REASON-DESC -- no reject write or abend follows; account balance update is silently lost | Reason code 109 set but not actioned (defect) | 2800-UPDATE-ACCOUNT-REC, lines 554-558 |
| TRANSACT-FILE WRITE fails (status != '00')          | DISPLAY 'ERROR WRITING TO TRANSACTION FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM        | Abend (CEE3ABD, code 999) | 2900-WRITE-TRANSACTION-FILE, lines 574-577 |
| Any file CLOSE fails (all six close paragraphs)     | DISPLAY 'ERROR CLOSING [file name]'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM               | Abend (CEE3ABD, code 999) | 9000-9500, various lines |
| Any error requiring abend                           | DISPLAY 'ABENDING PROGRAM'; MOVE 999 TO ABCODE; CALL 'CEE3ABD' USING ABCODE, TIMING (TIMING = 0)             | Abend code 999       | 9999-ABEND-PROGRAM, lines 707-711 |
| I/O status display -- non-numeric or 9xx status     | Parse status bytes via TWO-BYTES-BINARY overlay; DISPLAY 'FILE STATUS IS: NNNN' IO-STATUS-04                 | Display only         | 9910-DISPLAY-IO-STATUS, lines 715-725 |
| Any rejects exist at end of job                     | MOVE 4 TO RETURN-CODE                                                                                         | RETURN-CODE = 4      | Main loop, lines 229-231 |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. PROCEDURE DIVISION (main) -- open all six files, then enter main loop
2. 0000-DALYTRAN-OPEN -- open DALYTRAN-FILE INPUT; abend on failure
3. 0100-TRANFILE-OPEN -- open TRANSACT-FILE OUTPUT (destructive open); abend on failure
4. 0200-XREFFILE-OPEN -- open XREF-FILE INPUT; abend on failure
5. 0300-DALYREJS-OPEN -- open DALYREJS-FILE OUTPUT (destructive open); abend on failure
6. 0400-ACCTFILE-OPEN -- open ACCOUNT-FILE I-O (read/update); abend on failure
7. 0500-TCATBALF-OPEN -- open TCATBAL-FILE I-O (read/update); abend on failure
8. PERFORM UNTIL END-OF-FILE = 'Y' -- main processing loop
9. 1000-DALYTRAN-GET-NEXT -- sequential read of one daily transaction; set END-OF-FILE = 'Y' on EOF; abend on other errors
10. 1500-VALIDATE-TRAN -- dispatcher: PERFORM 1500-A then conditionally 1500-B
11. 1500-A-LOOKUP-XREF -- random read of XREF-FILE by card number; set reason 100 on INVALID KEY
12. 1500-B-LOOKUP-ACCT -- random read of ACCOUNT-FILE by account ID; check overlimit (reason 102) and expiration (reason 103); set reason 101 on INVALID KEY
13. 2000-POST-TRANSACTION -- map fields, get timestamp, then PERFORM 2700, 2800, 2900 in sequence
14. Z-GET-DB2-FORMAT-TIMESTAMP -- build DB2-FORMAT-TS from FUNCTION CURRENT-DATE (utility paragraph named with 'Z-' prefix; located at line 692)
15. 2700-UPDATE-TCATBAL -- read category balance; branch to 2700-A (create) or 2700-B (update)
16. 2700-A-CREATE-TCATBAL-REC -- INITIALIZE and WRITE new TRAN-CAT-BAL-RECORD
17. 2700-B-UPDATE-TCATBAL-REC -- ADD amount and REWRITE existing TRAN-CAT-BAL-RECORD
18. 2800-UPDATE-ACCOUNT-REC -- update ACCT-CURR-BAL, ACCT-CURR-CYC-CREDIT or ACCT-CURR-CYC-DEBIT; REWRITE account record
19. 2900-WRITE-TRANSACTION-FILE -- WRITE TRAN-RECORD to TRANSACT-FILE; abend on failure
20. 2500-WRITE-REJECT-REC -- (alternative path) WRITE REJECT-RECORD (transaction data + validation trailer) to DALYREJS-FILE; abend on failure
21. 9000-9500 -- close all six files in reverse open order; abend on any failure
22. Display final counts (WS-TRANSACTION-COUNT, WS-REJECT-COUNT)
23. IF WS-REJECT-COUNT > 0 THEN MOVE 4 TO RETURN-CODE
24. GOBACK
25. CALL 'CEE3ABD' (via 9999-ABEND-PROGRAM) -- LE abend with code 999 when any unrecoverable I/O error occurs

### Notable Defects / Anomalies

**Defect 1 -- Copy-paste error in 9300-DALYREJS-CLOSE (line 649):** When DALYREJS-FILE close fails, the error-display branch executes `MOVE XREFFILE-STATUS TO IO-STATUS` instead of `MOVE DALYREJS-STATUS TO IO-STATUS`. The wrong file's status code is displayed -- a copy-paste defect that makes DALYREJS close error diagnosis misleading.

**Defect 2 -- Silent account rewrite failure in 2800-UPDATE-ACCOUNT-REC (lines 554-558):** When `REWRITE FD-ACCTFILE-REC INVALID KEY` fires, WS-VALIDATION-FAIL-REASON is set to 109 and a description is loaded, but the program does not subsequently write a reject record, abend, or take any recovery action. The account balance update is silently lost. The transaction is still written to TRANSACT-FILE as if it succeeded (PERFORM 2900 proceeds regardless), creating a data inconsistency between the account master and the transaction file.

**Defect 3 -- Overlimit check uses cycle balances only (lines 403-405):** WS-TEMP-BAL is computed as `ACCT-CURR-CYC-CREDIT - ACCT-CURR-CYC-DEBIT + DALYTRAN-AMT`. Prior-cycle carry-forward balance in ACCT-CURR-BAL is not included. A customer whose current balance is entirely from prior cycles would pass the overlimit check on all transactions until cycle reset. Whether this is intentional policy or a defect depends on product rules.

**Defect 4 -- Last-failing-check-wins in 1500-B-LOOKUP-ACCT (lines 403-420):** Both the overlimit check (reason 102) and the expiration date check (reason 103) run without a short-circuit. If both conditions fail, the reason code is overwritten by the second failing check (reason 103). The reject record will only show one reason even when both validations fail.

**Anomaly 5 -- No account ID in the permanent transaction record (CVTRA05Y):** TRAN-RECORD (copied via CVTRA05Y) contains no TRAN-ACCT-ID field. The account ID resolved from XREF is used only transiently during posting (to look up and update the account master and category balance files) but is not stored in TRANSACT-FILE. Any query of TRANSACT-FILE that needs account context must re-join through XREF-FILE using TRAN-CARD-NUM. This is an architectural data model constraint, not a runtime bug.

**Anomaly 6 -- Input processing timestamp is discarded on posting (lines 436-438):** DALYTRAN-RECORD includes DALYTRAN-PROC-TS (PIC X(26)). The field is physically present in the input record but 2000-POST-TRANSACTION never MOVEs it to TRAN-PROC-TS. Instead, TRAN-PROC-TS is always set from FUNCTION CURRENT-DATE at batch runtime. If upstream processes populated DALYTRAN-PROC-TS with a meaningful value, it is silently overwritten.
