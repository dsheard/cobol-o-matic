---
type: business-rules
program: CBACT04C
program_type: subprogram
status: draft
confidence: high
last_pass: 5
calls:
- CEE3ABD
called_by: []
uses_copybooks:
- CVACT01Y
- CVACT03Y
- CVTRA01Y
- CVTRA02Y
- CVTRA05Y
reads:
- ACCOUNT-FILE
- DISCGRP-FILE
- TCATBAL-FILE
- TRANSACT-FILE
- XREF-FILE
writes:
- ACCOUNT-FILE
- TRANSACT-FILE
db_tables: []
transactions: []
mq_queues: []
---

# CBACT04C -- Business Rules

## Program Purpose

CBACT04C is a batch interest calculation program. It reads transaction category balance records (TCATBAL-FILE) sequentially, groups them by account, looks up each account's disclosure group interest rate from DISCGRP-FILE, computes monthly interest for each transaction category that carries a non-zero rate, accumulates the interest per account, and writes a synthetic interest-charge transaction record to TRANSACT-FILE. When processing moves to a new account, the accumulated interest for the previous account is posted back to the account balance in ACCOUNT-FILE. The program receives a run date via the EXTERNAL-PARMS linkage parameter, which it uses as a prefix when constructing generated transaction IDs. A stub paragraph (1400-COMPUTE-FEES) exists but is not yet implemented.

## Input / Output

| Direction | Resource       | Type | Description                                                                 |
| --------- | -------------- | ---- | --------------------------------------------------------------------------- |
| IN        | TCATBAL-FILE   | File | Transaction category balance file (INDEXED, sequential read); key: account ID + type code + category code |
| IN        | XREF-FILE      | File | Card cross-reference file (INDEXED, random read by alternate key FD-XREF-ACCT-ID); maps account ID to card number |
| IN/OUT    | ACCOUNT-FILE   | File | Account master file (INDEXED, random read and rewrite); holds current balance and cycle credits/debits |
| IN        | DISCGRP-FILE   | File | Disclosure group interest rate file (INDEXED, random read by FD-DISCGRP-KEY); holds per-group/type/category annual interest rate |
| OUT       | TRANSACT-FILE  | File | Transaction output file (sequential write); receives generated interest-charge transaction records |
| IN        | EXTERNAL-PARMS | Linkage | Run date (PARM-DATE PIC X(10)) and length field passed by the JCL caller; used as prefix for TRAN-ID construction |

## Business Rules

### Main Processing Loop

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 1  | Sequential read drives main loop | PERFORM UNTIL END-OF-FILE = 'Y' | Reads one TCATBAL-FILE record per iteration; exits when EOF is detected | Lines 188-222 |
| 2  | Increment record counter on each valid read | END-OF-FILE = 'N' after 1000-TCATBALF-GET-NEXT | ADD 1 TO WS-RECORD-COUNT | Line 192 |
| 3  | Debug display of every processed record (unconditional) | Every TCATBAL record read successfully | DISPLAY TRAN-CAT-BAL-RECORD -- no guard condition; produces output for every record processed | Line 193 |
| 4  | Account boundary detection | TRANCAT-ACCT-ID NOT= WS-LAST-ACCT-NUM | A new account has been encountered; triggers account-change processing | Line 194 |
| 5  | Skip account update on first record ever | WS-FIRST-TIME = 'Y' at account boundary | MOVE 'N' TO WS-FIRST-TIME (do not call 1050-UPDATE-ACCOUNT for the very first account seen) | Lines 195-198 |
| 6  | Post accumulated interest to prior account at account boundary | WS-FIRST-TIME NOT = 'Y' AND TRANCAT-ACCT-ID NOT= WS-LAST-ACCT-NUM | PERFORM 1050-UPDATE-ACCOUNT to rewrite the previous account record | Lines 195-196 |
| 7  | Reset accumulated interest counter at account boundary | New account detected | MOVE 0 TO WS-TOTAL-INT | Line 200 |
| 8  | Track current account being processed | Account boundary crossed | MOVE TRANCAT-ACCT-ID TO WS-LAST-ACCT-NUM | Line 201 |
| 9  | Load account master record at account boundary | New account detected | Set FD-ACCT-ID from TRANCAT-ACCT-ID; PERFORM 1100-GET-ACCT-DATA | Lines 202-203 |
| 10 | Load card cross-reference at account boundary | New account detected | Set FD-XREF-ACCT-ID from TRANCAT-ACCT-ID; PERFORM 1110-GET-XREF-DATA | Lines 204-205 |
| 11 | Interest lookup and compute per category record | Executes for every TCATBAL record | Set DISCGRP key from ACCT-GROUP-ID + TRANCAT-CD + TRANCAT-TYPE-CD; PERFORM 1200-GET-INTEREST-RATE | Lines 210-213 |
| 12 | Skip interest calculation when rate is zero | DIS-INT-RATE = 0 after 1200-GET-INTEREST-RATE | Neither 1300-COMPUTE-INTEREST nor 1400-COMPUTE-FEES is called | Line 214 |
| 13 | Compute and record interest when rate is non-zero | DIS-INT-RATE NOT = 0 | PERFORM 1300-COMPUTE-INTEREST then PERFORM 1400-COMPUTE-FEES | Lines 215-216 |
| 14 | Final account update at end-of-file | END-OF-FILE = 'Y' (ELSE branch of inner IF END-OF-FILE = 'N') | PERFORM 1050-UPDATE-ACCOUNT to flush accumulated interest for the last account | Lines 219-220 |

### Interest Rate Lookup and Default Fallback

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 15 | Look up specific disclosure group interest rate | Key = ACCT-GROUP-ID + TRANCAT-TYPE-CD + TRANCAT-CAT-CD | READ DISCGRP-FILE INTO DIS-GROUP-RECORD | 1200-GET-INTEREST-RATE (line 416) |
| 16 | Display diagnostic messages when specific group record is absent | DISCGRP-STATUS = '23' (INVALID KEY clause fires) | DISPLAY 'DISCLOSURE GROUP RECORD MISSING'; DISPLAY 'TRY WITH DEFAULT GROUP CODE' | Lines 417-419 |
| 17 | Accept both found and not-found as non-error on first lookup | DISCGRP-STATUS = '00' OR '23' | MOVE 0 TO APPL-RESULT (file status '23' = record not found is tolerated at this stage) | Lines 422-426 |
| 18 | Fall back to DEFAULT group when specific group record is absent | DISCGRP-STATUS = '23' (record not found) | MOVE 'DEFAULT' TO FD-DIS-ACCT-GROUP-ID; PERFORM 1200-A-GET-DEFAULT-INT-RATE | Lines 436-438 |
| 19 | DEFAULT fallback key retains original type and category codes | DISCGRP-STATUS = '23' triggers fallback | Only FD-DIS-ACCT-GROUP-ID is changed to 'DEFAULT'; FD-DIS-TRAN-TYPE-CD and FD-DIS-TRAN-CAT-CD are NOT reset -- the DEFAULT lookup uses the same type-code and category-code as the failed primary lookup | Lines 437-438 (1200-GET-INTEREST-RATE) |
| 20 | Read default disclosure group record | Called from 1200-GET-INTEREST-RATE when DISCGRP-STATUS = '23' | READ DISCGRP-FILE INTO DIS-GROUP-RECORD using key containing 'DEFAULT' + original type/cat codes; no INVALID KEY clause on this read | 1200-A-GET-DEFAULT-INT-RATE (line 444) |
| 21 | Default rate read must succeed | DISCGRP-STATUS NOT = '00' after default read | DISPLAY 'ERROR READING DEFAULT DISCLOSURE GROUP'; abend | Lines 452-458 |

### Interest Calculation and Transaction Write

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 22 | Monthly interest formula | Non-zero DIS-INT-RATE | WS-MONTHLY-INT = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200 | 1300-COMPUTE-INTEREST (line 464-465) |
| 23 | Accumulate monthly interest into account total | After computing WS-MONTHLY-INT | ADD WS-MONTHLY-INT TO WS-TOTAL-INT | Line 467 |
| 24 | Write interest transaction record | After computing WS-MONTHLY-INT | PERFORM 1300-B-WRITE-TX | Line 468 |
| 25 | Construct unique transaction ID | Per interest transaction | ADD 1 TO WS-TRANID-SUFFIX; STRING PARM-DATE, WS-TRANID-SUFFIX DELIMITED BY SIZE INTO TRAN-ID | Lines 474-480 |
| 26 | Interest transaction type code is fixed | Always | MOVE '01' TO TRAN-TYPE-CD | Line 482 |
| 27 | Interest transaction category code is fixed | Always | MOVE '05' TO TRAN-CAT-CD | Line 483 |
| 28 | Interest transaction source is fixed | Always | MOVE 'System' TO TRAN-SOURCE | Line 484 |
| 29 | Interest transaction description constructed | Always | STRING 'Int. for a/c ', ACCT-ID DELIMITED BY SIZE INTO TRAN-DESC | Lines 485-489 |
| 30 | Interest amount set to computed monthly interest | Always | MOVE WS-MONTHLY-INT TO TRAN-AMT | Line 490 |
| 31 | Merchant fields are blanked for interest transactions | Always | TRAN-MERCHANT-ID = 0; TRAN-MERCHANT-NAME, TRAN-MERCHANT-CITY, TRAN-MERCHANT-ZIP = SPACES | Lines 491-494 |
| 32 | Card number sourced from cross-reference | Always | MOVE XREF-CARD-NUM TO TRAN-CARD-NUM | Line 495 |
| 33 | Both original and processing timestamps set to current system time | Always | PERFORM Z-GET-DB2-FORMAT-TIMESTAMP; MOVE DB2-FORMAT-TS TO TRAN-ORIG-TS and TRAN-PROC-TS | Lines 496-498 |

### Account Balance Update

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 34 | Add accumulated interest to account current balance | At account boundary or EOF | ADD WS-TOTAL-INT TO ACCT-CURR-BAL | 1050-UPDATE-ACCOUNT (line 352) |
| 35 | Clear cycle credit balance on update | Always on account update | MOVE 0 TO ACCT-CURR-CYC-CREDIT | Line 353 |
| 36 | Clear cycle debit balance on update | Always on account update | MOVE 0 TO ACCT-CURR-CYC-DEBIT | Line 354 |
| 37 | Rewrite account record to file | After balance adjustments | REWRITE FD-ACCTFILE-REC FROM ACCOUNT-RECORD | Line 356 |

### Fees (Stub)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 38 | Fee computation is not implemented | 1400-COMPUTE-FEES called after interest calculation | Paragraph body contains only EXIT -- no logic | 1400-COMPUTE-FEES (line 518-520) |

## Calculations

| Calculation | Formula / Logic | Input Fields | Output Field | Source Location |
| ----------- | --------------- | ------------ | ------------ | --------------- |
| Monthly interest per category | WS-MONTHLY-INT = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200. No ROUNDED or ON SIZE ERROR clause is present. If the intermediate product (TRAN-CAT-BAL * DIS-INT-RATE) overflows S9(09)V99 capacity before division by 1200, the result is silently truncated or an abend may occur depending on the runtime. | TRAN-CAT-BAL (S9(09)V99 from CVTRA01Y/TCATBAL-FILE), DIS-INT-RATE (S9(04)V99 annual rate from CVTRA02Y/DISCGRP-FILE) | WS-MONTHLY-INT (S9(09)V99) | 1300-COMPUTE-INTEREST line 464 |
| Accumulated account interest | Running sum per account of all category monthly interests | WS-MONTHLY-INT (per category) | WS-TOTAL-INT (S9(09)V99) | Lines 467, 352 |
| Transaction ID construction | PARM-DATE (10 chars) concatenated with WS-TRANID-SUFFIX (6-digit incrementing counter, incremented before each STRING call) | PARM-DATE, WS-TRANID-SUFFIX (PIC 9(06)) | TRAN-ID (PIC X(16)) | 1300-B-WRITE-TX lines 474-480 |
| DB2-format timestamp | Convert COBOL CURRENT-DATE (YYYYMMDDHHMMSSCC) to DB2 format YYYY-MM-DD-HH.MM.SS.CC0000 | FUNCTION CURRENT-DATE | DB2-FORMAT-TS (PIC X(26)) | Z-GET-DB2-FORMAT-TIMESTAMP lines 614-625 |

## Error Handling

| Condition | Action | Return Code | Source Location |
| --------- | ------ | ----------- | --------------- |
| TCATBAL-FILE open fails (TCATBALF-STATUS NOT = '00') | DISPLAY 'ERROR OPENING TRANSACTION CATEGORY BALANCE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | APPL-RESULT = 12 | 0000-TCATBALF-OPEN lines 245-248 |
| XREF-FILE open fails (XREFFILE-STATUS NOT = '00') | DISPLAY 'ERROR OPENING CROSS REF FILE' + status; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | APPL-RESULT = 12 | 0100-XREFFILE-OPEN lines 263-266 |
| DISCGRP-FILE open fails (DISCGRP-STATUS NOT = '00') | DISPLAY 'ERROR OPENING DALY REJECTS FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | APPL-RESULT = 12 | 0200-DISCGRP-OPEN lines 281-284 |
| ACCOUNT-FILE open fails (ACCTFILE-STATUS NOT = '00') | DISPLAY 'ERROR OPENING ACCOUNT MASTER FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | APPL-RESULT = 12 | 0300-ACCTFILE-OPEN lines 300-303 |
| TRANSACT-FILE open fails (TRANFILE-STATUS NOT = '00') | DISPLAY 'ERROR OPENING TRANSACTION FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | APPL-RESULT = 12 | 0400-TRANFILE-OPEN lines 318-321 |
| TCATBAL-FILE read error (not '00' or '10') | DISPLAY 'ERROR READING TRANSACTION CATEGORY FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | APPL-RESULT = 12 | 1000-TCATBALF-GET-NEXT lines 342-345 |
| TCATBAL-FILE EOF (status '10') | MOVE 'Y' TO END-OF-FILE -- normal termination | APPL-RESULT = 16 (APPL-EOF) | 1000-TCATBALF-GET-NEXT lines 330-340 |
| ACCOUNT-FILE read key not found (ACCTFILE-STATUS = '23') | INVALID KEY clause fires DISPLAY 'ACCOUNT NOT FOUND: ' FD-ACCT-ID (line 375); status '23' then fails the '= 00' check so APPL-RESULT = 12; second DISPLAY 'ERROR READING ACCOUNT FILE' (line 386); PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM -- FATAL abend, not a soft skip | APPL-RESULT = 12 | 1100-GET-ACCT-DATA lines 374-389 |
| XREF-FILE read key not found (XREFFILE-STATUS = '23') | INVALID KEY clause fires DISPLAY 'ACCOUNT NOT FOUND: ' FD-XREF-ACCT-ID (line 397); status '23' then fails the '= 00' check so APPL-RESULT = 12; second DISPLAY 'ERROR READING XREF FILE' (line 408); PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM -- FATAL abend, not a soft skip | APPL-RESULT = 12 | 1110-GET-XREF-DATA lines 396-411 |
| DISCGRP-FILE read error (status not '00' or '23') | DISPLAY 'ERROR READING DISCLOSURE GROUP FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | APPL-RESULT = 12 | 1200-GET-INTEREST-RATE lines 431-434 |
| DISCGRP-FILE default record read error | DISPLAY 'ERROR READING DEFAULT DISCLOSURE GROUP'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | APPL-RESULT = 12 | 1200-A-GET-DEFAULT-INT-RATE lines 455-458 |
| ACCOUNT-FILE rewrite fails (ACCTFILE-STATUS NOT = '00') | DISPLAY 'ERROR RE-WRITING ACCOUNT FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | APPL-RESULT = 12 | 1050-UPDATE-ACCOUNT lines 365-368 |
| TRANSACT-FILE write fails (TRANFILE-STATUS NOT = '00') | DISPLAY 'ERROR WRITING TRANSACTION RECORD'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | APPL-RESULT = 12 | 1300-B-WRITE-TX lines 510-513 |
| TCATBAL-FILE close fails | DISPLAY 'ERROR CLOSING TRANSACTION BALANCE FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | APPL-RESULT = 12 | 9000-TCATBALF-CLOSE lines 533-536 |
| XREF-FILE close fails | DISPLAY 'ERROR CLOSING CROSS REF FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | APPL-RESULT = 12 | 9100-XREFFILE-CLOSE lines 552-555 |
| DISCGRP-FILE close fails | DISPLAY 'ERROR CLOSING DISCLOSURE GROUP FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | APPL-RESULT = 12 | 9200-DISCGRP-CLOSE lines 570-573 |
| ACCOUNT-FILE close fails | DISPLAY 'ERROR CLOSING ACCOUNT FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | APPL-RESULT = 12 | 9300-ACCTFILE-CLOSE lines 588-591 |
| TRANSACT-FILE close fails | DISPLAY 'ERROR CLOSING TRANSACTION FILE'; PERFORM 9910-DISPLAY-IO-STATUS; PERFORM 9999-ABEND-PROGRAM | APPL-RESULT = 12 | 9400-TRANFILE-CLOSE lines 606-609 |
| Any I/O status with non-numeric value or first byte = '9' (platform-specific status) | Convert to 4-digit display format via binary overlay; DISPLAY 'FILE STATUS IS: NNNN' IO-STATUS-04 | n/a | 9910-DISPLAY-IO-STATUS lines 636-647 |
| Abend requested | DISPLAY 'ABENDING PROGRAM'; MOVE 999 TO ABCODE; CALL 'CEE3ABD' USING ABCODE, TIMING | ABCODE = 999, TIMING = 0 | 9999-ABEND-PROGRAM lines 629-632 |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. PROCEDURE DIVISION inline -- DISPLAY 'START OF EXECUTION OF PROGRAM CBACT04C'
2. 0000-TCATBALF-OPEN -- open TCATBAL-FILE for sequential INPUT; abend on failure
3. 0100-XREFFILE-OPEN -- open XREF-FILE for random INPUT; abend on failure
4. 0200-DISCGRP-OPEN -- open DISCGRP-FILE for random INPUT; abend on failure
5. 0300-ACCTFILE-OPEN -- open ACCOUNT-FILE for I-O (read and rewrite); abend on failure
6. 0400-TRANFILE-OPEN -- open TRANSACT-FILE for sequential OUTPUT; abend on failure
7. PERFORM UNTIL END-OF-FILE = 'Y' -- main processing loop:
   a. 1000-TCATBALF-GET-NEXT -- read next TCATBAL record; sets END-OF-FILE='Y' on EOF
   b. Account boundary check: if TRANCAT-ACCT-ID changed, call 1050-UPDATE-ACCOUNT (except first time) then reset WS-TOTAL-INT, load account data (1100-GET-ACCT-DATA), load XREF data (1110-GET-XREF-DATA)
   c. 1200-GET-INTEREST-RATE -- lookup rate by group/type/category; fall back to DEFAULT group via 1200-A-GET-DEFAULT-INT-RATE if not found
   d. If DIS-INT-RATE NOT = 0: 1300-COMPUTE-INTEREST (compute monthly interest, accumulate, write transaction via 1300-B-WRITE-TX), then 1400-COMPUTE-FEES (stub, no-op)
   e. On EOF branch (ELSE of inner IF END-OF-FILE = 'N'): 1050-UPDATE-ACCOUNT to flush last account's accumulated interest
8. 9000-TCATBALF-CLOSE -- close TCATBAL-FILE; abend on failure
9. 9100-XREFFILE-CLOSE -- close XREF-FILE; abend on failure
10. 9200-DISCGRP-CLOSE -- close DISCGRP-FILE; abend on failure
11. 9300-ACCTFILE-CLOSE -- close ACCOUNT-FILE; abend on failure
12. 9400-TRANFILE-CLOSE -- close TRANSACT-FILE; abend on failure
13. DISPLAY 'END OF EXECUTION OF PROGRAM CBACT04C'
14. GOBACK

**Supporting paragraphs:**
- Z-GET-DB2-FORMAT-TIMESTAMP -- converts FUNCTION CURRENT-DATE to DB2-format timestamp string YYYY-MM-DD-HH.MM.SS.CC0000; called from 1300-B-WRITE-TX
- 9910-DISPLAY-IO-STATUS -- decodes and displays numeric or platform-specific file status codes; called before every abend
- 9999-ABEND-PROGRAM -- issues structured abend via CALL 'CEE3ABD' with ABCODE=999

**Note on DISCGRP-FILE error message:** The error message for DISCGRP-FILE open failure reads 'ERROR OPENING DALY REJECTS FILE' -- this appears to be a copy-paste error in the source; the file is the Disclosure Group (interest rate) file, not a daily rejects file.

**Note on debug output:** Line 193 contains an unconditional `DISPLAY TRAN-CAT-BAL-RECORD` statement that will emit every processed TCATBAL record to SYSOUT with no guard condition. This is a debug artifact left in production code and will produce high-volume output.

**Note on account/xref not-found severity:** The INVALID KEY clause on both 1100-GET-ACCT-DATA (line 374) and 1110-GET-XREF-DATA (line 396) displays a "NOT FOUND" message but does NOT set APPL-EOF or soft-skip. The subsequent file-status check requires status '00'; status '23' (not found) sets APPL-RESULT=12 and the program abends. In each case a second DISPLAY message also fires ('ERROR READING ACCOUNT FILE' at line 386 and 'ERROR READING XREF FILE' at line 408) before the abend. Missing accounts and missing xref records are therefore fatal -- this differs from the superficial appearance of a non-fatal INVALID KEY handler.

**Note on COMPUTE overflow risk:** The COMPUTE at line 464 (`WS-MONTHLY-INT = (TRAN-CAT-BAL * DIS-INT-RATE) / 1200`) has no ROUNDED or ON SIZE ERROR clause. TRAN-CAT-BAL is S9(09)V99 and DIS-INT-RATE is S9(04)V99; the intermediate product can require up to 15 integer digits plus 4 decimal places before the division by 1200 reduces its magnitude. WS-MONTHLY-INT is S9(09)V99. If the unrounded product exceeds receiver capacity the result is silently truncated per COBOL default arithmetic rules, potentially yielding a wrong interest charge with no error indication.

**Note on account boundary comparison type mismatch:** At line 194 the condition `TRANCAT-ACCT-ID NOT= WS-LAST-ACCT-NUM` compares TRANCAT-ACCT-ID (PIC 9(11), numeric from CVTRA01Y) against WS-LAST-ACCT-NUM (PIC X(11), alphanumeric). IBM COBOL performs an alphanumeric comparison in this case (numeric is treated as display characters), which produces correct results for zero-padded account numbers but represents an implicit type coercion that modernisation tooling must handle explicitly.

**Note on DEFAULT fallback key composition:** When the primary DISCGRP-FILE lookup returns status '23' (record not found), only `FD-DIS-ACCT-GROUP-ID` is overwritten with the literal `'DEFAULT'` (line 437). `FD-DIS-TRAN-TYPE-CD` and `FD-DIS-TRAN-CAT-CD` are not reset; they retain the values set from the current TCATBAL record (lines 211-212). Consequently the DEFAULT rate lookup uses the composite key `DEFAULT` + original-type-code + original-category-code, not a blanket `DEFAULT` key. DISCGRP-FILE must therefore contain a DEFAULT record for each distinct type/category combination used in TCATBAL-FILE, or the default read will also fail and the program will abend.

**Note on lost-update window on ACCOUNT-FILE:** The account record is READ (without a `READ ... UPDATE` lock) in 1100-GET-ACCT-DATA when an account boundary is first crossed, but is not REWRITTEN until the next account boundary or end-of-file -- potentially many TCATBAL records later. There is no record locking between the READ and the REWRITE. If another batch job or process modifies the same account record during this window, the REWRITE at line 356 will silently overwrite those changes, causing a lost update. This is a concurrency risk if ACCOUNT-FILE can be accessed by more than one job simultaneously.
