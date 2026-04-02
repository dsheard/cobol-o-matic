---
type: business-rules
program: BNK1CCA
program_type: online
status: draft
confidence: high
last_pass: 5
calls:
- INQACCCU
- ABNDPROC
called_by: []
uses_copybooks:
- ABNDINFO
- BNK1ACC
- INQACCCU
- DFHAID
reads: []
writes: []
db_tables: []
transactions:
- OCCA
mq_queues: []
---

# BNK1CCA -- Business Rules

## Program Purpose

BNK1CCA is a CICS online program that lists all accounts belonging to a specified customer number. The user enters a customer number on the BNK1ACC BMS map; the program validates the input, calls INQACCCU (via EXEC CICS LINK) to retrieve up to 20 accounts for that customer, and displays the account details (sort-code, account number, account type, available balance, and actual balance) on screen. The transaction ID is OCCA.

## Input / Output

| Direction | Resource    | Type  | Description                                                                                                   |
| --------- | ----------- | ----- | ------------------------------------------------------------------------------------------------------------- |
| IN        | BNK1ACC     | CICS  | BMS map / mapset -- user enters customer number (CUSTNOI field, 10 chars, BMS NUM attribute enforces digit-only input at terminal) |
| OUT       | BNK1ACC     | CICS  | BMS map / mapset -- displays account list (ACCOUNTO array, 10 rows x 79 chars) and message (MESSAGEO)        |
| IN/OUT    | DFHCOMMAREA | CICS  | 248-byte commarea carrying EYE, SCODE, CUSTNO, NAME, ADDR, DOB on pseudo-conversational RETURN; incoming values are never read back on re-entry (see Defects) |
| OUT       | INQACCCU    | CICS  | LINK commarea -- passes customer number and receives up to 20 account records (INQACCCU ODO table, OCCURS 1 TO 20 DEPENDING ON NUMBER-OF-ACCOUNTS) |

## Business Rules

### Entry-Point Routing (PREMIERE / A010)

| #  | Rule                              | Condition                                        | Action                                                                                                                                                      | Source Location |
| -- | --------------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 1  | First invocation -- empty screen  | `EIBCALEN = ZERO`                                | Initialise BNK1ACCO to LOW-VALUE, set cursor to CUSTNO field (CUSTNOL = -1), SET SEND-ERASE TO TRUE, PERFORM SEND-MAP; then falls through to unconditional RETURN TRANSID('OCCA') | A010 line 162   |
| 2  | PA key pressed -- no action       | `EIBAID = DFHPA1 OR DFHPA2 OR DFHPA3`           | CONTINUE (fall through to unconditional RETURN TRANSID('OCCA'))                                                                                             | A010 line 171   |
| 3  | PF3 -- return to main menu        | `EIBAID = DFHPF3`                                | `EXEC CICS RETURN TRANSID('OMEN') IMMEDIATE` -- transfers control to transaction OMEN. RESP/RESP2 are captured but no response check is performed           | A010 line 177   |
| 4  | AID key or PF12 -- end session    | `EIBAID = DFHAID OR DFHPF12`                     | PERFORM SEND-TERMINATION-MSG, then `EXEC CICS RETURN` (no transid -- ends conversation). Screen label reads 'F12=Cancel' but behaviour is session termination, not cancel/back | A010 line 189   |
| 5  | CLEAR key -- erase and exit       | `EIBAID = DFHCLEAR`                              | `EXEC CICS SEND CONTROL ERASE FREEKB`, then `EXEC CICS RETURN`. Neither CICS call has a RESP check -- defect/omission vs. all other branches                | A010 line 198   |
| 6  | ENTER key -- process input        | `EIBAID = DFHENTER`                              | PERFORM PROCESS-MAP; then falls through to unconditional RETURN TRANSID('OCCA')                                                                              | A010 line 210   |
| 7  | Any other key -- invalid key      | WHEN OTHER (all other AID values)                | Move LOW-VALUES to BNK1ACCO, display 'Invalid key pressed.' in MESSAGEO, set cursor to CUSTNO (CUSTNOL=-1), SET SEND-DATAONLY-ALARM TO TRUE, PERFORM SEND-MAP | A010 line 216   |
| 8  | Pseudo-conversational return      | Unconditional (after END-EVALUATE)               | `EXEC CICS RETURN TRANSID('OCCA') COMMAREA(WS-COMM-AREA) LENGTH(248)` -- keeps the session alive with OCCA; executes after every branch except DFHAID/PF12 and CLEAR (which issue their own RETURN earlier) | A010 line 225 |

### Input Validation (EDIT-DATA / ED010)

| #  | Rule                                          | Condition                | Action                                                                          | Source Location |
| -- | --------------------------------------------- | ------------------------ | ------------------------------------------------------------------------------- | --------------- |
| 9  | Customer number must be numeric               | `CUSTNOI NOT NUMERIC`    | Move 'Please enter a customer number.' to MESSAGEO; MOVE 'N' TO VALID-DATA-SW  | ED010 line 411  |
| 10 | Customer number field is 10 characters        | Structural / BMS         | CUSTNO BMS field is LENGTH=10 with ATTRB=NUM -- terminal enforces digit-only entry. INQACCCU CUSTOMER-NUMBER is PIC 9(10). No minimum-length, range, leading-zero, or zero-value checks are performed in program logic | BNK1ACC.bms line 38, ED010 |
| 11 | Alarm beep on every ENTER submission          | Unconditional in PM010   | `SET SEND-DATAONLY-ALARM TO TRUE` fires after GET-CUST-DATA (or after validation failure) -- every ENTER response, success or failure, triggers audible alarm at terminal | PM010 line 316  |

Note: VALID-DATA-SW has 88-level condition `VALID-DATA VALUE 'Y'`. It is initialised to 'Y' in WORKING-STORAGE, which is re-initialised on every new CICS task invocation (pseudo-conversational architecture). No stale 'N' state can carry over between ENTER keypresses.

### Customer Account Retrieval (GET-CUST-DATA / GCD010)

| #  | Rule                                              | Condition                                                              | Action                                                                                                                                                          | Source Location     |
| -- | ------------------------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| 12 | Request up to 20 accounts per customer            | Unconditional setup before LINK                                        | MOVE 20 TO NUMBER-OF-ACCOUNTS; MOVE 'N' TO COMM-SUCCESS; MOVE CUSTNOI TO CUSTOMER-NUMBER; SET COMM-PCB-POINTER TO NULL (IMS pointer nulled for CICS-only usage). NUMBER-OF-ACCOUNTS=20 pre-sizes the ODO commarea to maximum before the LINK | GCD010 line 426     |
| 13 | Call INQACCCU to retrieve accounts                | Unconditional                                                          | `EXEC CICS LINK PROGRAM('INQACCCU') COMMAREA(INQACCCU-COMMAREA) SYNCONRETURN`. Program name is referenced via data item INQACCCU-PROGRAM (VALUE 'INQACCCU')    | GCD010 line 435     |
| 14 | Customer not found after inquiry                  | `CUSTOMER-FOUND = 'N'` (returned by INQACCCU)                         | Move SPACES to MESSAGEO; STRING 'Unable to find customer ' + CUSTOMER-NUMBER INTO MESSAGEO; clear all 10 screen account rows to SPACES; GO TO GCD999            | GCD010 line 505     |
| 15 | Pre-clear display rows before repopulation        | Unconditional when CUSTOMER-FOUND is not 'N'                          | PERFORM VARYING WS-INDEX FROM 1 BY 1 UNTIL WS-INDEX > 10: MOVE SPACES TO ACCOUNTO(WS-INDEX) -- erases stale data from a prior search before writing new results | GCD010 line 526     |
| 16 | No accounts exist for found customer              | `NUMBER-OF-ACCOUNTS = ZERO`                                            | Display 'No accounts found for customer' in MESSAGEO; account-populate loop does not execute                                                                   | GCD010 line 531     |
| 17 | INQACCCU returned error flag with non-zero count  | `COMM-SUCCESS = 'N'` AND `NUMBER-OF-ACCOUNTS > 0` (inner IF inside outer ELSE) | Move SPACES to MESSAGEO; STRING 'Error accessing accounts for customer ' + CUSTOMER-NUMBER + '.' INTO MESSAGEO. COMM-FAIL-CODE is present in the commarea but is never inspected. DEFECT: account-populate loop still executes (see Defects) | GCD010 line 534     |
| 18 | Accounts retrieved successfully -- set message    | `NUMBER-OF-ACCOUNTS > 0` AND `COMM-SUCCESS` not 'N' (inner ELSE)     | Move NUMBER-OF-ACCOUNTS to NUMBER-OF-ACCOUNTS-DISPLAY (PIC Z9, leading-zero suppressed); STRING number + ' accounts found' INTO MESSAGEO                      | GCD010 line 539     |
| 19 | Screen display limit: at most 10 accounts         | PERFORM VARYING WS-INDEX FROM 1 BY 1 UNTIL `WS-INDEX > NUMBER-OF-ACCOUNTS OR WS-INDEX > 10`; executes for ALL cases where NUMBER-OF-ACCOUNTS > 0 (both success and COMM-SUCCESS='N' paths) | Loop iterates for WS-INDEX 1..MIN(NUMBER-OF-ACCOUNTS, 10); up to 10 account rows populated in ACCOUNTO array | GCD010 line 552     |
| 20 | Available balance sign indicator                  | `COMM-AVAIL-BAL(WS-INDEX) < 0`                                         | Set WS-AVAIL-BAL-SIGN = '-'; otherwise set to '+'                                                                                                               | GCD010 line 562     |
| 21 | Actual balance sign indicator                     | `COMM-ACTUAL-BAL(WS-INDEX) < 0`                                        | Set WS-ACT-BAL-SIGN = '-'; otherwise set to '+'                                                                                                                 | GCD010 line 568     |
| 22 | Account display row format                        | Unconditional STRING build per account                                 | STRING SCODE-CHAR + 6 spaces + ACCNO-CHAR + 9 spaces + COMM-ACC-TYPE + 7 spaces + WS-AVAIL-BAL-SIGN + pounds + '.' + pence + 2 spaces + WS-ACT-BAL-SIGN + pounds + '.' + pence INTO ACCOUNTO(WS-INDEX) | GCD010 line 579 |
| 23 | INQACCCU returned fields not displayed            | Informational                                                          | COMM-INT-RATE, COMM-OPENED, COMM-OVERDRAFT, COMM-LAST-STMT-DT, COMM-NEXT-STMT-DT, COMM-EYE, COMM-CUSTNO are returned in the ACCOUNT-DETAILS ODO array but are never moved to the screen output. Only COMM-SCODE, COMM-ACCNO, COMM-ACC-TYPE, COMM-AVAIL-BAL, COMM-ACTUAL-BAL are used | INQACCCU.cpy lines 15-36 |

### Screen Send Mode Selection (SEND-MAP / SM010)

| #  | Rule                                | Condition                          | Action                                                                                 | Source Location |
| -- | ----------------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------- | --------------- |
| 24 | Send map with full erase            | `SEND-ERASE` (flag = '1')          | `EXEC CICS SEND MAP ERASE FREEKB`; on success GO TO SM999                              | SM010 line 621  |
| 25 | Send data only (no erase)           | `SEND-DATAONLY` (flag = '2')       | `EXEC CICS SEND MAP DATAONLY FREEKB`; on success GO TO SM999                           | SM010 line 696  |
| 26 | Send data with audible alarm        | `SEND-DATAONLY-ALARM` (flag = '3') | `EXEC CICS SEND MAP DATAONLY ALARM FREEKB`; falls through to SM999 (no GO TO, unlike the two modes above) | SM010 line 773  |

## Calculations

| Calculation                        | Formula / Logic                                                                                                                                                                                                                    | Input Fields                                                | Output Field                                                                                        | Source Location    |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------ |
| Balance display decomposition      | COMM-AVAIL-BAL and COMM-ACTUAL-BAL (COMP signed S9(10)V99) are moved into PIC 9(10)V99 working fields which are redefined as two character strings: pounds (10 chars, WS-AVAIL-BAL-X-PND / WS-ACT-BAL-X-PND) and pence (2 chars, WS-AVAIL-BAL-X-PNCE / WS-ACT-BAL-X-PNCE). Absolute value only -- sign is derived separately by comparing original signed value to zero. The four components (sign, pounds, '.', pence) are concatenated via STRING into the display row. Note: negative balance moves S9(10)V99 into 9(10)V99, so the absolute value is displayed correctly; sign character handles the negative indication. | COMM-AVAIL-BAL(WS-INDEX), COMM-ACTUAL-BAL(WS-INDEX)        | WS-AVAIL-BAL-X-PND, WS-AVAIL-BAL-X-PNCE, WS-ACT-BAL-X-PND, WS-ACT-BAL-X-PNCE, WS-AVAIL-BAL-SIGN, WS-ACT-BAL-SIGN -- combined into ACCOUNTO(WS-INDEX) | GCD010 line 559    |
| Account count display conversion   | NUMBER-OF-ACCOUNTS (S9(8) BINARY) moved to NUMBER-OF-ACCOUNTS-DISPLAY (PIC Z9 DISPLAY) for leading-zero suppression before STRING into MESSAGEO                                                                                   | NUMBER-OF-ACCOUNTS                                          | NUMBER-OF-ACCOUNTS-DISPLAY                                                                          | GCD010 line 540    |

## Error Handling

| Condition                                         | Action                                                                                                                              | Return Code / ABEND Code | Source Location    |
| ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------ | ------------------ |
| EXEC CICS RETURN TRANSID('OCCA') fails            | Populate ABNDINFO-REC (RESPCODE, RESP2CODE, APPLID, TASKNO, TRANID, date/time, program name, freeform 'A010 - RETURN TRANSID(OCCA) FAIL'); LINK ABNDPROC; DISPLAY 'BNK1CCA - A010 - RETURN TRANSID(OCCA) FAIL'; PERFORM ABEND-THIS-TASK | HBNK                 | A010 line 233      |
| EXEC CICS RECEIVE MAP fails                       | Populate ABNDINFO-REC; LINK ABNDPROC; DISPLAY 'BNKMENU - RM010 - RECEIVE MAP FAIL'; PERFORM ABEND-THIS-TASK. Note: DISPLAY text reads 'BNKMENU' but executing program is BNK1CCA -- copy-paste defect | HBNK               | RM010 line 341     |
| EXEC CICS LINK INQACCCU fails                     | Populate ABNDINFO-REC; LINK ABNDPROC; DISPLAY 'BNK1CCA - GCD010 - LINK INQACCCU FAIL'; PERFORM ABEND-THIS-TASK                    | HBNK                     | GCD010 line 443    |
| EXEC CICS SEND MAP ERASE fails                    | Populate ABNDINFO-REC; LINK ABNDPROC; DISPLAY 'BNK1CCA - SM010 - SEND MAP ERASE FAIL'; PERFORM ABEND-THIS-TASK                    | HBNK                     | SM010 line 631     |
| EXEC CICS SEND MAP DATAONLY fails                 | Populate ABNDINFO-REC; LINK ABNDPROC; DISPLAY 'BNK1CCA - SM010 - SEND MAP DATAONLY FAIL'; PERFORM ABEND-THIS-TASK                 | HBNK                     | SM010 line 706     |
| EXEC CICS SEND MAP DATAONLY ALARM fails           | Populate ABNDINFO-REC; LINK ABNDPROC; DISPLAY 'BNK1CCA - SM010 - SEND MAP DATAONLY ALARM FAIL'; PERFORM ABEND-THIS-TASK           | HBNK                     | SM010 line 784     |
| EXEC CICS SEND TEXT (termination message) fails   | Populate ABNDINFO-REC; LINK ABNDPROC; DISPLAY 'BNK1CCA - STM010 - SEND TEXT FAIL'; PERFORM ABEND-THIS-TASK                       | HBNK                     | STM010 line 865    |
| Customer number field is non-numeric (soft error) | Set VALID-DATA-SW = 'N'; display 'Please enter a customer number.' in MESSAGEO; do not call INQACCCU                               | n/a (message only)       | ED010 line 411     |
| Customer not found (soft error)                   | Display 'Unable to find customer [CUSTOMER-NUMBER]' in MESSAGEO; clear all 10 account display rows to SPACES; GO TO GCD999        | n/a                      | GCD010 line 505    |
| INQACCCU returned COMM-SUCCESS = 'N' (soft error) | Display 'Error accessing accounts for customer [CUSTOMER-NUMBER].' in MESSAGEO; COMM-FAIL-CODE is available but never inspected; DEFECT: account rows are still populated if NUMBER-OF-ACCOUNTS > 0 | n/a                      | GCD010 line 534    |
| ABEND-THIS-TASK (terminal handler)                | DISPLAY WS-FAIL-INFO; `EXEC CICS ABEND ABCODE('HBNK') NODUMP`                                                                    | HBNK                     | ATT010 line 930    |
| CLEAR key -- CICS calls not checked               | `EXEC CICS SEND CONTROL ERASE FREEKB` and `EXEC CICS RETURN` issued with no RESP check -- unlike all other CICS calls in the program | n/a (no handler)      | A010 line 198      |
| PF3 RETURN -- response not checked                | `EXEC CICS RETURN TRANSID('OMEN') IMMEDIATE` captures RESP/RESP2 but has no IF check on the response                             | n/a (no handler)         | A010 line 177      |
| POPULATE-TIME-DATE CICS calls not checked         | `EXEC CICS ASKTIME` and `EXEC CICS FORMATTIME` in PTD010 have no RESP check -- if either fails, ABND-DATE and ABND-TIME in the abend record will contain uninitialised or wrong values | n/a (no handler)  | PTD010 line 943    |

### Defects Noted

| Defect | Location | Description |
| ------ | -------- | ----------- |
| ABND-TIME string uses MM twice instead of MM:SS | A010 line 255, RM010 line 364, GCD010 line 465, SM010 lines 653/729/808, STM010 line 887 | All ABEND time-string builders concatenate `WS-TIME-NOW-GRP-HH ':' WS-TIME-NOW-GRP-MM ':' WS-TIME-NOW-GRP-MM`. The third token should be `WS-TIME-NOW-GRP-SS` -- the seconds are always recorded as a repeat of the minutes value. |
| RECEIVE MAP FAIL display text names wrong program | RM010 line 395 | `WS-CICS-FAIL-MSG` is set to `'BNKMENU - RM010 - RECEIVE MAP FAIL '` but the executing program is BNK1CCA, not BNKMENU -- copy-paste from BNK1MEN or similar program. |
| COMM-FAIL-CODE not inspected | GCD010 line 534 | INQACCCU returns COMM-FAIL-CODE alongside COMM-SUCCESS, but BNK1CCA only checks COMM-SUCCESS = 'N'. The specific failure reason is silently discarded. |
| POPULATE-TIME-DATE CICS calls unchecked | PTD010 lines 943/947 | `EXEC CICS ASKTIME` and `EXEC CICS FORMATTIME` are issued without RESP/RESP2 checks. Every other CICS call in the program checks RESP. A failure here would silently corrupt the date/time fields in the abend record. |
| Account-populate loop executes on COMM-SUCCESS='N' path | GCD010 lines 534-607 | The PERFORM loop that populates ACCOUNTO rows (line 552) is nested inside the outer ELSE block (NUMBER-OF-ACCOUNTS > 0) but is a sibling -- not a child -- of the inner IF COMM-SUCCESS='N'/ELSE structure. This means when INQACCCU signals failure (COMM-SUCCESS='N') but returns a non-zero account count, the error message is set in MESSAGEO AND the account rows are still overwritten with whatever data INQACCCU returned. The user sees both the error message and account data, which is contradictory. |
| Incoming DFHCOMMAREA never read | A010, full procedure division | DFHCOMMAREA (LINKAGE SECTION, 248 bytes) carries COMM-EYE, COMM-SCODE, COMM-CUSTNO, COMM-NAME, COMM-ADDR, COMM-DOB back from the prior pseudo-conversational RETURN. None of these fields are ever read in the PROCEDURE DIVISION. WS-COMM-AREA is written on RETURN but the round-trip data serves no function. The commarea is passed but never consumed -- suggesting either dead carry-over from a prior design or an incomplete feature. |
| Screen label 'F12=Cancel' behaves as session end | A010 line 189 | The BMS map footer (BNK1ACC.bms line 54) displays 'F3=Exit  F12=Cancel'. PF12 is handled identically to DFHAID (AID key) -- it sends a 'Session Ended' termination message and issues EXEC CICS RETURN with no TRANSID. This is a session termination, not a cancel/back that returns to the previous state. User expectation from the label is not met. |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. **A010 (PREMIERE SECTION)** -- Main dispatch; evaluates EIBCALEN and EIBAID to route first-time entry, PA keys, PF3, AID/PF12, CLEAR, ENTER, and invalid keys.
2. **SEND-MAP (SM010)** -- Called for first-time entry (SEND-ERASE) and for invalid-key response (SEND-DATAONLY-ALARM).
3. **PROCESS-MAP (PM010)** -- Called when ENTER is pressed; orchestrates receive, validate, retrieve, and send.
   - 3a. **RECEIVE-MAP (RM010)** -- `EXEC CICS RECEIVE MAP('BNK1ACC') MAPSET('BNK1ACC') INTO(BNK1ACCI)` to capture user input.
   - 3b. **EDIT-DATA (ED010)** -- Validates CUSTNOI is numeric; sets VALID-DATA-SW = 'N' if not.
   - 3c. **GET-CUST-DATA (GCD010)** -- Only if VALID-DATA: sets NUMBER-OF-ACCOUNTS=20 (pre-sizes ODO commarea), nulls COMM-PCB-POINTER, sets CUSTOMER-NUMBER=CUSTNOI; `EXEC CICS LINK PROGRAM('INQACCCU') SYNCONRETURN`; interprets CUSTOMER-FOUND, NUMBER-OF-ACCOUNTS, COMM-SUCCESS; pre-clears all 10 ACCOUNTO rows unconditionally; formats up to 10 account rows into ACCOUNTO array.
   - 3d. SET SEND-DATAONLY-ALARM TO TRUE (unconditional in PM010, after GET-CUST-DATA -- alarm beep fires on every ENTER response).
   - 3e. **SEND-MAP (SM010)** -- Called with SEND-DATAONLY-ALARM to return results (or validation error) to the user.
4. **SEND-TERMINATION-MSG (STM010)** -- Called on AID/PF12; sends 'Session Ended' text (literal END-OF-SESSION-MESSAGE VALUE 'Session Ended') with ERASE.
5. **POPULATE-TIME-DATE (PTD010)** -- Called from every ABEND path; `EXEC CICS ASKTIME ABSTIME(WS-U-TIME)` then `EXEC CICS FORMATTIME DDMMYYYY(WS-ORIG-DATE) TIME(WS-TIME-NOW) DATESEP` to obtain date and time for the ABND record. Neither CICS call has a RESP check.
6. **ABEND-THIS-TASK (ATT010)** -- Terminal error handler; DISPLAYs WS-FAIL-INFO and issues `EXEC CICS ABEND ABCODE('HBNK') NODUMP`.
7. CALL **ABNDPROC** (via `EXEC CICS LINK PROGRAM('ABNDPROC')` using data item WS-ABEND-PGM VALUE 'ABNDPROC') -- Called from every CICS error path to record abend information before the hard ABEND.
8. `EXEC CICS RETURN TRANSID('OCCA') COMMAREA(WS-COMM-AREA) LENGTH(248)` -- Unconditional pseudo-conversational return at end of A010; fires after first-entry, PA-key, ENTER, and invalid-key branches. The PF3, AID/PF12, and CLEAR branches issue their own RETURN before reaching this point.
