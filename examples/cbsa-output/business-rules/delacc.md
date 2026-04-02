---
type: business-rules
program: DELACC
program_type: online
status: draft
confidence: high
last_pass: 4
calls:
- ABNDPROC
called_by:
- BNK1DAC
- DELCUS
uses_copybooks:
- ABNDINFO
- ACCDB2
- ACCOUNT
- ACCTCTRL
- DELACC
- PROCDB2
- PROCTRAN
- SORTCODE
reads: []
writes: []
db_tables:
- ACCOUNT
- PROCTRAN
transactions: []
mq_queues: []
---

# DELACC -- Business Rules

## Program Purpose

DELACC is an online CICS program that deletes a bank account record from the DB2 ACCOUNT table.
It receives an account number via the DFHCOMMAREA (DELACC-COMMAREA), reads the corresponding
account record using sort-code and account number as the key, deletes the row if found, and then
writes an audit entry to the PROCTRAN table. If the account is not found, it returns a failure
indicator in the COMMAREA. On any unexpected DB2 error the program ABENDs using the ABNDPROC
abend handler. The program is called by the branch delete-account screen handler (BNK1DAC) and
by the delete-customer program (DELCUS) when removing all accounts for a customer.

## Input / Output

| Direction | Resource | Type              | Description                                                                                    |
| --------- | -------- | ----------------- | ---------------------------------------------------------------------------------------------- |
| IN/OUT    | DFHCOMMAREA (DELACC-COMMAREA) | CICS | Incoming: DELACC-ACCNO (8-digit account number). Outgoing: all 12 account data fields, DELACC-DEL-SUCCESS flag, DELACC-DEL-FAIL-CD failure code |
| READ      | ACCOUNT  | DB2               | Retrieves account row by ACCOUNT_NUMBER + ACCOUNT_SORTCODE                                     |
| DELETE    | ACCOUNT  | DB2               | Deletes account row by ACCOUNT_SORTCODE + ACCOUNT_NUMBER                                       |
| INSERT    | PROCTRAN | DB2               | Writes audit transaction record for the deletion                                               |
| CALL      | ABNDPROC | CICS LINK         | Abend handler -- called on unexpected PROCTRAN INSERT failure (WS-ABEND-PGM VALUE 'ABNDPROC') |

## Business Rules

### Account Retrieval

| #   | Rule                                                              | Condition                                                                                                                                     | Action                                                                                                                                                             | Source Location              |
| --- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------- |
| 1   | Sort-code is always the installation sort-code                    | Unconditional                                                                                                                                 | SORTCODE copybook value is moved to REQUIRED-SORT-CODE and to HV-ACCOUNT-SORTCODE before any DB2 read                                                             | A010, RAD010 (lines 207, 246) |
| 2   | Account is looked up by account number and sort-code              | EXEC SQL SELECT FROM ACCOUNT WHERE ACCOUNT_NUMBER = :HV-ACCOUNT-ACC-NO AND ACCOUNT_SORTCODE = :HV-ACCOUNT-SORTCODE                           | All 12 account columns fetched into HOST-ACCOUNT-ROW host variables                                                                                               | RAD010 (lines 248-276)        |
| 3   | Account not found sets failure in COMMAREA and exits read section | SQLCODE = +100 (DB2 row-not-found)                                                                                                            | DELACC-DEL-SUCCESS = 'N', DELACC-DEL-FAIL-CD = '1'; OUTPUT-DATA initialised with sort-code and account number; GO TO RAD999 (skips all further processing)       | RAD010 (lines 350-357)        |
| 4   | Successful account read sets success flags                        | SQLCODE = 0                                                                                                                                   | DELACC-SUCCESS = ' ' (space), DELACC-DEL-SUCCESS = 'Y', DELACC-DEL-FAIL-CD = ' ' (space)                                                                         | RAD010 (lines 363-367)        |
| 5   | Account data is copied to intermediate OUTPUT-DATA then to COMMAREA | SQLCODE = 0                                                                                                                                 | All 12 account fields moved from HV-ACCOUNT-* to OUTPUT-DATA (ACCOUNT copybook overlay), then moved again to DELACC-* COMMAREA fields. DELACC-ACCNO (the input field) is overwritten with the DB2-retrieved account number at line 416 | RAD010 (lines 372-425)        |
| 6   | Date fields from DB2 are reformatted from YYYY-MM-DD to separate DD/MM/YYYY components | DB2 dates (ACCOUNT_OPENED, ACCOUNT_LAST_STATEMENT, ACCOUNT_NEXT_STATEMENT) stored as YYYY-MM-DD | Each date is moved through DB2-DATE-REFORMAT (overlay structure: PIC 9(4) / X / 99 / X / 99) to extract DB2-DATE-REF-DAY, DB2-DATE-REF-MNTH, DB2-DATE-REF-YR into separate OUTPUT-DATA sub-fields | RAD010 (lines 384-406) |
| 7   | Actual balance is preserved separately for PROCTRAN audit         | SQLCODE = 0                                                                                                                                   | HV-ACCOUNT-ACTUAL-BAL is moved to ACCOUNT-ACT-BAL-STORE (line 411 via OUTPUT-DATA). A second redundant MOVE at line 425 moves ACCOUNT-ACTUAL-BALANCE OF OUTPUT-DATA to ACCOUNT-ACT-BAL-STORE again; both produce the same value under normal conditions | RAD010 (lines 411, 425) |

### Account Deletion

| #   | Rule                                                      | Condition                                                                                                                                    | Action                                                                                                                                      | Source Location          |
| --- | --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| 8   | Delete is conditional on successful read                  | DELACC-DEL-SUCCESS = 'Y' (set by read step)                                                                                                  | PERFORM DEL-ACCOUNT-DB2 is only executed when read succeeded                                                                               | A010 (lines 218-224)     |
| 9   | Account is deleted by sort-code and account number        | EXEC SQL DELETE FROM ACCOUNT WHERE ACCOUNT_SORTCODE = :HV-ACCOUNT-SORTCODE AND ACCOUNT_NUMBER = :HV-ACCOUNT-ACC-NO                          | Row is removed from the ACCOUNT table using the same host variable values populated during the SELECT                                       | DADB010 (lines 438-442)  |
| 10  | DELETE failure sets failure indicator in COMMAREA -- no abend | SQLCODE NOT = 0 after DELETE                                                                                                             | DELACC-SUCCESS = ' ', DELACC-DEL-SUCCESS = 'N', DELACC-DEL-FAIL-CD = '3'. No ABEND is issued; control returns to caller with fail code '3' | DADB010 (lines 444-448)  |

### PROCTRAN Audit Write

| #   | Rule                                                                        | Condition                                                         | Action                                                                                                                                                               | Source Location            |
| --- | --------------------------------------------------------------------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| 11  | Audit record is only written after a successful delete                      | DELACC-DEL-SUCCESS = 'Y' after DEL-ACCOUNT-DB2                   | PERFORM WRITE-PROCTRAN (which immediately performs WRITE-PROCTRAN-DB2)                                                                                               | A010 (lines 221-223)       |
| 12  | PROCTRAN eyecatcher is always 'PRTR'                                        | Unconditional                                                     | HV-PROCTRAN-EYECATCHER = 'PRTR'                                                                                                                                      | WPD010 (line 472)          |
| 13  | PROCTRAN sort-code and account number come from OUTPUT-DATA fields          | Unconditional                                                     | ACCOUNT-SORT-CODE OF OUTPUT-DATA moved to HV-PROCTRAN-SORT-CODE; ACCOUNT-NUMBER OF OUTPUT-DATA moved to HV-PROCTRAN-ACC-NUMBER (not directly from HV-ACCOUNT-* host variables) | WPD010 (lines 473-474)     |
| 14  | PROCTRAN transaction type is set to branch delete account                   | Unconditional (SET PROC-TY-BRANCH-DELETE-ACCOUNT TO TRUE)         | HV-PROCTRAN-TYPE = 'ODA' (88-level value from PROCTRAN copybook)                                                                                                     | WPD010 (lines 513, 518)    |
| 15  | PROCTRAN description footer flag is set to 'DELETE'                         | Unconditional (SET PROC-DESC-DELACC-FLAG TO TRUE)                 | PROC-DESC-DELACC-FOOTER = 'DELETE' in the 40-byte description field; description also carries customer number, account type, and last/next statement dates (DD/MM/YYYY components) | WPD010 (lines 495-518) |
| 16  | PROCTRAN amount is the account's actual balance at time of deletion         | Unconditional                                                     | ACCOUNT-ACT-BAL-STORE (saved from account read at RAD010) is moved to HV-PROCTRAN-AMOUNT                                                                             | WPD010 (line 519)          |
| 17  | PROCTRAN reference is the CICS task number                                  | Unconditional                                                     | EIBTASKN is moved to WS-EIBTASKN12 (12-digit PIC 9(12)) then to HV-PROCTRAN-REF (12-char)                                                                           | WPD010 (lines 475-476)     |
| 18  | PROCTRAN date and time are captured at write time using CICS FORMATTIME     | Unconditional                                                     | EXEC CICS ASKTIME stores epoch into WS-U-TIME; FORMATTIME produces DDMMYYYY in WS-ORIG-DATE and HHMMSS time in HV-PROCTRAN-TIME (using DATESEP('.')); WS-ORIG-DATE overlaid by WS-ORIG-DATE-GRP-X to produce DD.MM.YYYY string in HV-PROCTRAN-DATE | WPD010 (lines 481-493) |
| 19  | HOST-PROCTRAN-ROW and WS-EIBTASKN12 are initialised before population      | Unconditional                                                     | INITIALIZE HOST-PROCTRAN-ROW and INITIALIZE WS-EIBTASKN12 are called at the start of WPD010 to clear any residual values before building the audit record            | WPD010 (lines 469-470)     |

## Calculations

| Calculation           | Formula / Logic                                                                                                                                       | Input Fields                                         | Output Field              | Source Location                  |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | ------------------------- | -------------------------------- |
| Balance preserved for audit | Actual balance stored at account-read time so it remains available even after the account row is deleted from DB2                               | HV-ACCOUNT-ACTUAL-BAL (from DB2 SELECT)              | ACCOUNT-ACT-BAL-STORE     | RAD010 (lines 411, 425)          |
| PROCTRAN date format  | CICS FORMATTIME DDMMYYYY output (dot-separated DATESEP('.')) overlaid by WS-ORIG-DATE-GRP-X redefine to produce DD.MM.YYYY format string              | WS-ORIG-DATE (DDMMYYYY from FORMATTIME with DATESEP('.')) | HV-PROCTRAN-DATE (10 chars) | WPD010 (lines 492-493)         |
| ABEND time string (defective) | STRING HH:MM:MM built using WS-TIME-NOW-GRP-HH, ':', WS-TIME-NOW-GRP-MM, ':', WS-TIME-NOW-GRP-MM -- the seconds slot reuses MM instead of SS | WS-TIME-NOW-GRP-HH, WS-TIME-NOW-GRP-MM               | ABND-TIME                 | RAD010 (lines 305-311); WPD010 (lines 575-581) |
| DB2 date reformat     | DB2 YYYY-MM-DD date overlaid by DB2-DATE-REFORMAT group (PIC 9(4) / X / 99 / X / 99) to extract day, month, year into separate numeric fields        | HV-ACCOUNT-OPENED / HV-ACCOUNT-LAST-STMT / HV-ACCOUNT-NEXT-STMT (YYYY-MM-DD) | ACCOUNT-OPENED-DAY/MONTH/YEAR etc. in OUTPUT-DATA | RAD010 (lines 384-406) |

## Error Handling

| Condition                                            | Action                                                                                                                                                                                      | Return Code / ABEND                              | Source Location            |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | -------------------------- |
| SQLCODE NOT = 0 AND NOT = +100 on ACCOUNT SELECT     | INITIALIZE ABNDINFO-REC; MOVE ZERO to ABND-RESPCODE/ABND-RESP2CODE; collect APPLID, EIBTASKN, EIBTRNID, date/time; set ABND-CODE = 'HRAC'; DISPLAY error; EXEC CICS ABEND ABCODE('HRAC') NODUMP | ABEND HRAC (with NODUMP)                     | RAD010 (lines 282-343)     |
| SQLCODE = +100 on ACCOUNT SELECT (account not found) | Set DELACC-DEL-SUCCESS = 'N', DELACC-DEL-FAIL-CD = '1'; INITIALIZE OUTPUT-DATA with sort-code and account number; GO TO RAD999 (exits read section, bypasses delete)                       | Fail code '1' returned in COMMAREA               | RAD010 (lines 350-357)     |
| SQLCODE NOT = 0 on ACCOUNT DELETE                    | Set DELACC-SUCCESS = ' ', DELACC-DEL-SUCCESS = 'N', DELACC-DEL-FAIL-CD = '3'. No abend. Control returns to A010 then to GET-ME-OUT-OF-HERE (GOBACK)                                        | Fail code '3' returned in COMMAREA               | DADB010 (lines 444-448)    |
| SQLCODE NOT = 0 on PROCTRAN INSERT                   | INITIALIZE ABNDINFO-REC; MOVE EIBRESP/EIBRESP2 to ABND-RESPCODE/ABND-RESP2CODE; collect APPLID, EIBTASKN, EIBTRNID, date/time; set ABND-CODE = 'HWPT'; EXEC CICS LINK PROGRAM(WS-ABEND-PGM) COMMAREA(ABNDINFO-REC); DISPLAY error; EXEC CICS ABEND ABCODE('HWPT') -- no NODUMP | ABEND HWPT (no NODUMP; dump is generated) | WPD010 (lines 552-615)     |

### ABEND Code Summary

| ABEND Code | Trigger                                                             | NODUMP? |
| ---------- | ------------------------------------------------------------------- | ------- |
| HRAC       | Unexpected DB2 error on ACCOUNT SELECT (SQLCODE not 0 or +100)     | Yes     |
| HWPT       | Unexpected DB2 error on PROCTRAN INSERT                             | No      |

### Defect Notes

1. **ABND-TIME built as HH:MM:MM (not HH:MM:SS)**: In both ABEND handling blocks (RAD010 lines 305-311 and WPD010 lines 575-581) the time string is built with STRING using `WS-TIME-NOW-GRP-MM` in the seconds position instead of `WS-TIME-NOW-GRP-SS`. The ABND-TIME field in the abend record always shows minutes twice and never shows seconds. This is a code defect that does not affect functional behaviour.

2. **POPULATE-TIME-DATE uses bare DATESEP vs. DATESEP('.')**: The POPULATE-TIME-DATE section (PTD010, line 645) calls FORMATTIME with `DATESEP` (no separator argument, uses system default), while the WRITE-PROCTRAN-DB2 section (WPD010, line 489) calls FORMATTIME with `DATESEP('.')`. If the system default separator is not a period, the ABND-DATE value populated by POPULATE-TIME-DATE may use a different format than HV-PROCTRAN-DATE. Functionally inconsequential for the delete operation itself but relevant to abend diagnostics.

3. **DELACC-ACCNO overwritten on successful read**: After a successful DB2 SELECT, line 416 moves `ACCOUNT-NUMBER OF OUTPUT-DATA` (the DB2-retrieved value) back to `DELACC-ACCNO` in the COMMAREA, overwriting the input value. Under normal circumstances these values are identical, but if there is any data mismatch the original input is lost.

4. **HRAC ABEND does not call ABNDPROC**: Unlike the HWPT path (which performs EXEC CICS LINK to ABNDPROC before ABENDing), the HRAC path (RAD010 lines 282-343) issues EXEC CICS ABEND directly without first linking to the ABNDPROC handler. This means the ABNDINFO-REC data populated for HRAC is never delivered to ABNDPROC -- it is only written to the CICS log via the preceding DISPLAY statement.

## Dead Code / Unused Definitions

| Item | Location | Notes |
| ---- | -------- | ----- |
| `RETURNED-DATA` (01-level group) | WORKING-STORAGE (lines 115-128) | Full account data structure (eye-catcher, customer number, sort-code, account number, type, interest rate, dates, balances). Defined but never referenced anywhere in the PROCEDURE DIVISION. |
| `DATA-STORE-TYPE` with 88-levels `DATASTORE-TYPE-DB2 VALUE '2'` and `DATASTORE-TYPE-VSAM VALUE 'V'` | WORKING-STORAGE (lines 140-143) | Never SET or tested in the PROCEDURE DIVISION. Suggests an earlier design where VSAM was a supported backend; only DB2 is actually used. |
| `DESIRED-KEY` PIC 9(10) BINARY | WORKING-STORAGE (line 130) | Defined but never assigned or referenced in the PROCEDURE DIVISION. |
| `EXIT-BROWSE-LOOP` PIC X VALUE 'N' | WORKING-STORAGE (line 102) | Defined but never referenced in the PROCEDURE DIVISION. Likely a vestige from a browse/cursor pattern that was removed. |
| `SYSIDERR-RETRY`, `FILE-RETRY`, `WS-EXIT-RETRY-LOOP` | WORKING-STORAGE (lines 45-47) | Retry control fields defined but never referenced. No retry loops exist in the PROCEDURE DIVISION. |
| `DB2-EXIT-LOOP`, `FETCH-DATA-CNT` | WORKING-STORAGE (lines 144-145) | DB2 cursor loop control variables defined but never used -- no FETCH or OPEN CURSOR statements exist in this program. |
| `WS-CUST-ALT-KEY-LEN`, `MY-TCB`, `MY-TCB-STRING`, `WS-ACC-KEY-LEN`, `WS-ACC-NUM` | WORKING-STORAGE (lines 146, 154-159) | Various length/key fields defined but never referenced in the PROCEDURE DIVISION. |
| `PROCTRAN-RIDFLD`, `PROCTRAN-RETRY` | WORKING-STORAGE (lines 110-111) | PROCTRAN record ID and retry counter defined but never used. No VSAM PROCTRAN access is performed. |
| `WS-TOKEN` | WORKING-STORAGE (line 178) | Token field defined but never referenced. |
| `STORM-DRAIN-CONDITION` | WORKING-STORAGE (line 181) | Pattern-named field for absorbing unexpected CICS conditions; defined but never referenced. |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. A010 (PREMIERE SECTION) -- main entry point; moves SORTCODE to REQUIRED-SORT-CODE; orchestrates read, delete, and audit
2. PERFORM READ-ACCOUNT-DB2 (RAD010) -- SELECT account row from DB2 by account number + sort-code; sets DELACC-DEL-SUCCESS; ABENDs on unexpected SQL error; exits via GO TO RAD999 on row-not-found
3. IF DELACC-DEL-SUCCESS = 'Y' -- outer guard: delete and audit only run if read succeeded
4. PERFORM DEL-ACCOUNT-DB2 (DADB010) -- DELETE account row; sets DELACC-DEL-SUCCESS = 'N' and fail code '3' on SQL error (no abend)
5. IF DELACC-DEL-SUCCESS = 'Y' (inner) -- inner guard: PROCTRAN audit only written if delete also succeeded
6. PERFORM WRITE-PROCTRAN (WP010) -- thin dispatcher that calls WRITE-PROCTRAN-DB2
7. WRITE-PROCTRAN-DB2 (WPD010) -- initialises HOST-PROCTRAN-ROW; builds all PROCTRAN fields; calls ASKTIME/FORMATTIME for timestamp; INSERTs PROCTRAN row; on SQL error: CICS LINK ABNDPROC then CICS ABEND HWPT (no NODUMP)
8. PERFORM GET-ME-OUT-OF-HERE (GMOFH010) -- unconditional GOBACK; reached regardless of success or failure path
9. POPULATE-TIME-DATE (PTD010) -- utility section called from within ABEND handling blocks only; ASKTIME + FORMATTIME with bare DATESEP (system default)
10. CICS LINK to ABNDPROC -- only on PROCTRAN INSERT failure; passes full ABNDINFO-REC as COMMAREA
