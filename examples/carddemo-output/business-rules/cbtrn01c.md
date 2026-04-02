---
type: business-rules
program: CBTRN01C
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
- CVTRA05Y
- CVTRA06Y
reads:
- ACCOUNT-FILE
- CARD-FILE
- CUSTOMER-FILE
- DALYTRAN-FILE
- TRANSACT-FILE
- XREF-FILE
writes: []
db_tables: []
transactions: []
mq_queues: []
---

# CBTRN01C -- Business Rules

## Program Purpose

CBTRN01C is a batch COBOL program that reads the daily transaction file (DALYTRAN-FILE) sequentially and, for each transaction record, attempts to validate the card number by performing a cross-reference lookup (XREF-FILE) and then reading the corresponding account record (ACCOUNT-FILE). This is a transaction posting validation step: it verifies that every card number on a daily transaction can be resolved to a known account. Transactions whose card numbers cannot be cross-referenced are reported and skipped. Account lookup failures are also reported. The program opens six files (DALYTRAN, CUSTOMER, XREF, CARD, ACCOUNT, TRANSACT), processes all transactions, closes all files, then terminates via GOBACK.

Note: The program opens CUSTOMER-FILE, CARD-FILE, and TRANSACT-FILE but does not read them in the current procedure code -- they are opened for potential future use or as part of a broader file-open pattern.

## Input / Output

| Direction | Resource        | Type | Description                                                          |
| --------- | --------------- | ---- | -------------------------------------------------------------------- |
| IN        | DALYTRAN-FILE   | File | Sequential daily transaction file; each record is 350 bytes (CVTRA06Y layout) |
| IN        | XREF-FILE       | File | Indexed card-to-account cross-reference file; keyed on card number (FD-XREF-CARD-NUM, 16 chars) |
| IN        | ACCOUNT-FILE    | File | Indexed account master file; keyed on account ID (FD-ACCT-ID, 11 digits) |
| IN        | CUSTOMER-FILE   | File | Indexed customer master file; keyed on customer ID (FD-CUST-ID, 9 digits) -- opened but not read in current code |
| IN        | CARD-FILE       | File | Indexed card master file; keyed on card number (FD-CARD-NUM, 16 chars) -- opened but not read in current code |
| IN        | TRANSACT-FILE   | File | Indexed transaction history file; keyed on transaction ID (FD-TRANS-ID, 16 chars) -- opened but not read in current code |

## Business Rules

### Transaction Processing Loop

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 1  | Process transactions until end-of-file | `END-OF-DAILY-TRANS-FILE = 'Y'` | Exit the PERFORM UNTIL loop | MAIN-PARA (line 164) |
| 2  | Only process when file not at EOF | `END-OF-DAILY-TRANS-FILE = 'N'` at loop top | Read next transaction record via 1000-DALYTRAN-GET-NEXT | MAIN-PARA (line 165) |
| 3  | Display each transaction read | Inner `IF END-OF-DAILY-TRANS-FILE = 'N'` after read | DISPLAY the full DALYTRAN-RECORD | MAIN-PARA (line 167-169) |
| 4  | Card number must be cross-referenceable | After each read, XREF lookup is always attempted within the outer EOF guard; `WS-XREF-READ-STATUS = 0` means success | If XREF lookup succeeds, proceed to account read; otherwise skip the transaction | MAIN-PARA (lines 170-184) |
| 5  | Skip transaction if card number cannot be verified | `WS-XREF-READ-STATUS NOT = 0` (XREF lookup returned INVALID KEY) | Display 'CARD NUMBER [x] COULD NOT BE VERIFIED. SKIPPING TRANSACTION ID-[y]' and do not process further | MAIN-PARA (lines 180-184) |
| 6  | Account must exist in ACCOUNT-FILE | `WS-ACCT-READ-STATUS NOT = 0` after 3000-READ-ACCOUNT | Display 'ACCOUNT [acct-id] NOT FOUND' -- processing continues to next transaction (non-fatal) | MAIN-PARA (lines 177-179) |
| 7  | XREF and account processing execute with stale data after final EOF read (latent defect) | The outer `IF END-OF-DAILY-TRANS-FILE = 'N'` (line 165) is evaluated as TRUE before calling 1000-DALYTRAN-GET-NEXT; when that read sets EOF='Y', execution continues inside the already-entered IF block; lines 170-184 then run XREF lookup and account read using DALYTRAN-CARD-NUM and derived values from the last successfully read record, not a new record | A spurious XREF lookup and potentially a spurious account read fire against the last record's data; if the XREF lookup fails for the stale key, a misleading 'CARD NUMBER ... COULD NOT BE VERIFIED' message is displayed for a record that has already been processed | MAIN-PARA (lines 166-184) |

### File Open Rules

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 8  | All six files must open successfully at startup | APPL-RESULT initialised to 8 before each OPEN; if file status = '00', APPL-RESULT set to 0; otherwise set to 12 | If APPL-AOK (value 0) is false, display error, display I/O status, call Z-ABEND-PROGRAM | 0000-DALYTRAN-OPEN through 0500-TRANFILE-OPEN (lines 252-359) |
| 9  | DALYTRAN-FILE open failure is fatal | DALYTRAN-STATUS NOT = '00' | Display 'ERROR OPENING DAILY TRANSACTION FILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM | 0000-DALYTRAN-OPEN (line 263) |
| 10 | CUSTOMER-FILE open failure is fatal | CUSTFILE-STATUS NOT = '00' | Display 'ERROR OPENING CUSTOMER FILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM | 0100-CUSTFILE-OPEN (line 282) |
| 11 | XREF-FILE open failure is fatal | XREFFILE-STATUS NOT = '00' | Display 'ERROR OPENING CROSS REF FILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM | 0200-XREFFILE-OPEN (line 300) |
| 12 | CARD-FILE open failure is fatal | CARDFILE-STATUS NOT = '00' | Display 'ERROR OPENING CARD FILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM | 0300-CARDFILE-OPEN (line 318) |
| 13 | ACCOUNT-FILE open failure is fatal | ACCTFILE-STATUS NOT = '00' | Display 'ERROR OPENING ACCOUNT FILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM | 0400-ACCTFILE-OPEN (line 336) |
| 14 | TRANSACT-FILE open failure is fatal | TRANFILE-STATUS NOT = '00' | Display 'ERROR OPENING TRANSACTION FILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM | 0500-TRANFILE-OPEN (line 354) |

### File Close Rules

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 15 | All six files must close successfully at shutdown | `ADD 8 TO ZERO GIVING APPL-RESULT`; if file status = '00', APPL-RESULT set to 0; otherwise set to 12 | If APPL-AOK false, display error, Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM | 9000-DALYTRAN-CLOSE through 9500-TRANFILE-CLOSE (lines 361-467) |
| 16 | DALYTRAN-FILE close failure is fatal -- message and status source are both wrong (dual defect) | DALYTRAN-STATUS NOT = '00' | Display 'ERROR CLOSING CUSTOMER FILE' (wrong message: should say DAILY TRANSACTION FILE); additionally `MOVE CUSTFILE-STATUS TO IO-STATUS` (line 373) -- wrong status source, should be `MOVE DALYTRAN-STATUS TO IO-STATUS`; diagnostic display will show the customer file status, not the daily transaction file status | 9000-DALYTRAN-CLOSE (lines 372-373) |
| 17 | CUSTOMER-FILE close failure is fatal | CUSTFILE-STATUS NOT = '00' | Display 'ERROR CLOSING CUSTOMER FILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM | 9100-CUSTFILE-CLOSE (line 390) |
| 18 | XREF-FILE close failure is fatal | XREFFILE-STATUS NOT = '00' | Display 'ERROR CLOSING CROSS REF FILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM | 9200-XREFFILE-CLOSE (line 408) |
| 19 | CARD-FILE close failure is fatal | CARDFILE-STATUS NOT = '00' | Display 'ERROR CLOSING CARD FILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM | 9300-CARDFILE-CLOSE (line 426) |
| 20 | ACCOUNT-FILE close failure is fatal | ACCTFILE-STATUS NOT = '00' | Display 'ERROR CLOSING ACCOUNT FILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM | 9400-ACCTFILE-CLOSE (line 444) |
| 21 | TRANSACT-FILE close failure is fatal | TRANFILE-STATUS NOT = '00' | Display 'ERROR CLOSING TRANSACTION FILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM | 9500-TRANFILE-CLOSE (line 462) |

### Cross-Reference (XREF) Lookup

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 22 | Card number key match required in XREF-FILE | DALYTRAN-CARD-NUM moved to XREF-CARD-NUM then to FD-XREF-CARD-NUM; keyed READ on FD-XREF-CARD-NUM | INVALID KEY: display 'INVALID CARD NUMBER FOR XREF', set WS-XREF-READ-STATUS = 4 | 2000-LOOKUP-XREF (lines 227-239) |
| 23 | Successful XREF lookup reveals account and customer IDs | NOT INVALID KEY | Display 'SUCCESSFUL READ OF XREF', card number, XREF-ACCT-ID, and XREF-CUST-ID; WS-XREF-READ-STATUS remains 0 | 2000-LOOKUP-XREF (lines 234-238) |

### Account Read

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 24 | Account must exist for the cross-referenced account ID | XREF-ACCT-ID moved to ACCT-ID then to FD-ACCT-ID; keyed READ on FD-ACCT-ID | INVALID KEY: display 'INVALID ACCOUNT NUMBER FOUND', set WS-ACCT-READ-STATUS = 4 | 3000-READ-ACCOUNT (lines 241-250) |
| 25 | Successful account read is confirmed | NOT INVALID KEY | Display 'SUCCESSFUL READ OF ACCOUNT FILE'; WS-ACCT-READ-STATUS remains 0 | 3000-READ-ACCOUNT (line 249) |

### Daily Transaction File Read

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 26 | Normal read sets APPL-RESULT to 0 | DALYTRAN-STATUS = '00' | APPL-RESULT = 0 (APPL-AOK true) | 1000-DALYTRAN-GET-NEXT (line 205) |
| 27 | End-of-file detection | DALYTRAN-STATUS = '10' | APPL-RESULT = 16 (APPL-EOF true); sets END-OF-DAILY-TRANS-FILE = 'Y' | 1000-DALYTRAN-GET-NEXT (lines 207-217) |
| 28 | Any other read status is a fatal I/O error | DALYTRAN-STATUS NOT '00' and NOT '10' | APPL-RESULT = 12; display 'ERROR READING DAILY TRANSACTION FILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM | 1000-DALYTRAN-GET-NEXT (lines 219-222) |

## Calculations

| Calculation | Formula / Logic | Input Fields | Output Field | Source Location |
| ----------- | --------------- | ------------ | ------------ | --------------- |
| APPL-RESULT open sentinel | Before each OPEN, set APPL-RESULT = 8; if file status = '00' then set to 0, else set to 12 | File status (per file) | APPL-RESULT (S9(9) COMP) | All 0xxx-open paragraphs |
| APPL-RESULT close sentinel | `ADD 8 TO ZERO GIVING APPL-RESULT`; if file status = '00' then set to 0, else set to 12 | File status (per file) | APPL-RESULT (S9(9) COMP) | All 9xxx-close paragraphs |
| IO-STATUS-04 numeric decode | If IO-STAT1 = '9' (extended status): copy STAT1 to position 1; BINARY-decode STAT2 into TWO-BYTES-BINARY then move to IO-STATUS-0403; else overlay IO-STATUS-04(3:2) with the two-character decimal status; display 'FILE STATUS IS: NNNN' followed by IO-STATUS-04 | IO-STATUS (IO-STAT1, IO-STAT2) | IO-STATUS-04 (display format) | Z-DISPLAY-IO-STATUS (lines 476-489) |

## Error Handling

| Condition | Action | Return Code | Source Location |
| --------- | ------ | ----------- | --------------- |
| Any file open failure | DISPLAY error message, PERFORM Z-DISPLAY-IO-STATUS, PERFORM Z-ABEND-PROGRAM | ABCODE = 999, TIMING = 0; CALL 'CEE3ABD' | 0000 through 0500 open paragraphs |
| Any file close failure | DISPLAY error message, PERFORM Z-DISPLAY-IO-STATUS, PERFORM Z-ABEND-PROGRAM | ABCODE = 999, TIMING = 0; CALL 'CEE3ABD' | 9000 through 9500 close paragraphs |
| Daily transaction file read error (non-EOF) | DISPLAY 'ERROR READING DAILY TRANSACTION FILE', Z-DISPLAY-IO-STATUS, Z-ABEND-PROGRAM | ABCODE = 999 | 1000-DALYTRAN-GET-NEXT (line 219) |
| XREF card number not found (INVALID KEY) | DISPLAY 'INVALID CARD NUMBER FOR XREF'; set WS-XREF-READ-STATUS = 4 | None (non-fatal, transaction skipped) | 2000-LOOKUP-XREF (line 232) |
| Account not found (INVALID KEY) | DISPLAY 'INVALID ACCOUNT NUMBER FOUND'; set WS-ACCT-READ-STATUS = 4 | None (non-fatal, reported and processing continues) | 3000-READ-ACCOUNT (line 246) |
| IO-STATUS not numeric or STAT1 = '9' | Extended format: decode STAT2 as binary, display 'FILE STATUS IS: NNNN' with extended status code | Diagnostic display only | Z-DISPLAY-IO-STATUS (lines 477-483) |
| IO-STATUS is numeric | Standard format: overlay IO-STATUS-04(3:2) with status, display 'FILE STATUS IS: NNNN' | Diagnostic display only | Z-DISPLAY-IO-STATUS (lines 485-487) |
| Z-ABEND-PROGRAM called | DISPLAY 'ABENDING PROGRAM'; MOVE 0 TO TIMING; MOVE 999 TO ABCODE; CALL 'CEE3ABD' USING ABCODE, TIMING | Abend code 999 via LE runtime | Z-ABEND-PROGRAM (lines 469-473) |
| DALYTRAN-FILE close error -- dual defect | Error message incorrectly reads 'ERROR CLOSING CUSTOMER FILE' instead of 'ERROR CLOSING DAILY TRANSACTION FILE'; additionally IO-STATUS is sourced from CUSTFILE-STATUS (line 373) instead of DALYTRAN-STATUS -- the diagnostic output will show the customer file status code, masking the real cause of the DALYTRAN close failure | N/A -- dual code defect in 9000-DALYTRAN-CLOSE | 9000-DALYTRAN-CLOSE (lines 372-373) |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. MAIN-PARA -- entry point; displays 'START OF EXECUTION OF PROGRAM CBTRN01C'; orchestrates all opens, processing loop, closes, and GOBACK
2. 0000-DALYTRAN-OPEN -- open DALYTRAN-FILE for INPUT; fatal if fails
3. 0100-CUSTFILE-OPEN -- open CUSTOMER-FILE for INPUT; fatal if fails
4. 0200-XREFFILE-OPEN -- open XREF-FILE for INPUT; fatal if fails
5. 0300-CARDFILE-OPEN -- open CARD-FILE for INPUT; fatal if fails
6. 0400-ACCTFILE-OPEN -- open ACCOUNT-FILE for INPUT; fatal if fails
7. 0500-TRANFILE-OPEN -- open TRANSACT-FILE for INPUT; fatal if fails
8. PERFORM UNTIL END-OF-DAILY-TRANS-FILE = 'Y' -- main processing loop; guarded by outer IF END-OF-DAILY-TRANS-FILE = 'N'
9. 1000-DALYTRAN-GET-NEXT -- read next sequential transaction record (READ DALYTRAN-FILE INTO DALYTRAN-RECORD); sets EOF flag on status '10'; ABENDs on any other non-zero status
10. 2000-LOOKUP-XREF -- keyed read of XREF-FILE by card number (XREF-CARD-NUM / FD-XREF-CARD-NUM); sets WS-XREF-READ-STATUS = 4 if not found; NOTE: also fires with stale key data after final EOF read due to latent defect (Rule 7)
11. 3000-READ-ACCOUNT -- keyed read of ACCOUNT-FILE by account ID (ACCT-ID / FD-ACCT-ID); sets WS-ACCT-READ-STATUS = 4 if not found; only called when WS-XREF-READ-STATUS = 0
12. 9000-DALYTRAN-CLOSE -- close DALYTRAN-FILE; fatal if fails (error diagnostics use wrong message text and wrong status field -- see dual defect in Error Handling)
13. 9100-CUSTFILE-CLOSE -- close CUSTOMER-FILE; fatal if fails
14. 9200-XREFFILE-CLOSE -- close XREF-FILE; fatal if fails
15. 9300-CARDFILE-CLOSE -- close CARD-FILE; fatal if fails
16. 9400-ACCTFILE-CLOSE -- close ACCOUNT-FILE; fatal if fails
17. 9500-TRANFILE-CLOSE -- close TRANSACT-FILE; fatal if fails
18. MAIN-PARA displays 'END OF EXECUTION OF PROGRAM CBTRN01C' then executes GOBACK
19. Z-DISPLAY-IO-STATUS -- formats and displays file status code (numeric or extended binary); called before all ABENDs
20. Z-ABEND-PROGRAM -- issues CEE3ABD call with ABCODE=999, TIMING=0 to force abnormal termination
21. CALL 'CEE3ABD' USING ABCODE, TIMING -- LE runtime abend; terminates the job with abend code 999
