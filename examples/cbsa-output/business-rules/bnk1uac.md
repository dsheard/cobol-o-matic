---
type: business-rules
program: BNK1UAC
program_type: online
status: draft
confidence: high
last_pass: 5
calls:
- INQACC
- UPDACC
- ABNDPROC
called_by: []
uses_copybooks:
- ABNDINFO
- BNK1UAM
- DFHAID
reads: []
writes: []
db_tables: []
transactions:
- OUAC
mq_queues: []
---

# BNK1UAC -- Business Rules

## Program Purpose

BNK1UAC is the Update Account (OUAC) online screen program in the CBSA CICS Banking Application. It presents the BNK1UA BMS map to the user, accepts an account number, retrieves the account details by linking to INQACC, allows the user to amend editable fields (account type, interest rate, overdraft limit, statement dates, and balances), validates all amended data, and then submits the changes by linking to UPDACC. The program is pseudo-conversational: it returns to CICS with transaction ID OUAC after each interaction, preserving state in the COMMAREA.

## Input / Output

| Direction | Resource  | Type | Description                                             |
| --------- | --------- | ---- | ------------------------------------------------------- |
| IN        | BNK1UA    | CICS | BMS map receive -- account number and amended fields    |
| OUT       | BNK1UA    | CICS | BMS map send -- account details and status messages     |
| IN/OUT    | DFHCOMMAREA | CICS | Pseudo-conversational commarea carrying account state |
| OUT       | INQACC    | CICS LINK | Account inquiry -- retrieve current account record |
| OUT       | UPDACC    | CICS LINK | Account update -- persist amended account record    |
| OUT       | ABNDPROC  | CICS LINK | Abend handler -- called on any CICS error           |

## Business Rules

### Key Dispatch (A010)

| #  | Rule                              | Condition                            | Action                                                                        | Source Location |
| -- | --------------------------------- | ------------------------------------ | ----------------------------------------------------------------------------- | --------------- |
| 1  | First-time entry -- empty screen  | EIBCALEN = ZERO                      | Move LOW-VALUE to BNK1UAO, set cursor on ACCNO, SEND-ERASE, initialise commarea, PERFORM SEND-MAP | A010 line 205 |
| 2  | PA key -- no action               | EIBAID = DFHPA1 or DFHPA2 or DFHPA3 | CONTINUE (no processing)                                                      | A010 line 215 |
| 3  | PF3 -- return to main menu        | EIBAID = DFHPF3                      | EXEC CICS RETURN TRANSID('OMEN') IMMEDIATE                                    | A010 line 221 |
| 4  | AID or PF12 -- terminate session  | EIBAID = DFHAID or DFHPF12           | PERFORM SEND-TERMINATION-MSG then EXEC CICS RETURN                            | A010 line 233 |
| 5  | CLEAR -- erase screen             | EIBAID = DFHCLEAR                    | EXEC CICS SEND CONTROL ERASE FREEKB then EXEC CICS RETURN                     | A010 line 242 |
| 6  | ENTER -- retrieve account         | EIBAID = DFHENTER                    | PERFORM PROCESS-MAP (which runs RECEIVE-MAP, resets VALID-DATA-SW, then EDIT-DATA then INQ-ACC-DATA if valid) | A010 line 254 |
| 7  | PF5 -- submit update              | EIBAID = DFHPF5                      | PERFORM PROCESS-MAP (which runs RECEIVE-MAP, resets VALID-DATA-SW, then VALIDATE-DATA then UPD-ACC-DATA if valid) | A010 line 260 |
| 8  | Any other key -- invalid key      | WHEN OTHER                           | Move LOW-VALUES to BNK1UAO, move 'Invalid key pressed.' to MESSAGEO, SET SEND-DATAONLY-ALARM, PERFORM SEND-MAP | A010 line 266 |
| 9  | Commarea carry-forward            | EIBCALEN NOT = ZERO                  | Move all COMM-* fields to corresponding WS-COMM-* fields before RETURN (12 fields; WS-COMM-SUCCESS is NOT carried forward -- see note) | A010 line 280 |
| 10 | Pseudo-conversational return      | Always (end of A010)                 | EXEC CICS RETURN TRANSID('OUAC') COMMAREA(WS-COMM-AREA) LENGTH(99)            | A010 line 295 |

**Note -- WS-COMM-SUCCESS not preserved across turns:** The copy-back block at lines 280-293 copies 12 WS-COMM-* fields but excludes WS-COMM-SUCCESS. This field therefore retains its WORKING-STORAGE initial value (not set by VALUE clause; uninitialised) at the start of each new task invocation. This is inconsequential in practice because COMM-SUCCESS in DFHCOMMAREA is explicitly pre-cleared to ' ' by UAD010 before every UPDACC call.

### Process-Map Routing (PM010)

| #  | Rule                                         | Condition               | Action                                                          | Source Location |
| -- | -------------------------------------------- | ----------------------- | --------------------------------------------------------------- | --------------- |
| 11 | RECEIVE-MAP executed before VALID-DATA-SW reset | Always, start of PM010 | PERFORM RECEIVE-MAP (line 371) then MOVE 'Y' TO VALID-DATA-SW (line 372); the receive must succeed before the switch is reset -- a CICS error in RECEIVE-MAP abends the task before the reset | PM010 lines 371-372 |
| 12 | ENTER triggers account inquiry               | EIBAID = DFHENTER       | PERFORM EDIT-DATA; if VALID-DATA then PERFORM INQ-ACC-DATA      | PM010 line 376  |
| 13 | PF5 triggers account update                  | EIBAID = DFHPF5         | PERFORM VALIDATE-DATA; if VALID-DATA then PERFORM UPD-ACC-DATA  | PM010 line 391  |
| 14 | Screen always refreshed after process        | Always                  | SET SEND-DATAONLY-ALARM TO TRUE, PERFORM SEND-MAP               | PM010 line 404  |

### Edit-Data Validation (ED010 -- ENTER key)

| #  | Rule                          | Condition                   | Action                                                                     | Source Location |
| -- | ----------------------------- | --------------------------- | -------------------------------------------------------------------------- | --------------- |
| 15 | Account number must be numeric | ACCNOI NOT NUMERIC          | Move 'Please enter an account number.' to MESSAGEO; set VALID-DATA-SW='N' | ED010 line 496  |

### Validate-Data Validation (VD010 -- PF5 key)

| #  | Rule                                                                     | Condition                                                                                                                                | Action                                                                                                                   | Source Location   |
| -- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------------- |
| 16 | Account type must be one of the five valid values                        | ACTYPEI NOT = 'CURRENT ', 'SAVING  ', 'LOAN    ', 'MORTGAGE', or 'ISA     '                                                             | Msg: 'Account Type must be CURRENT, SAVING, LOAN, MORTGAGE or ISA. Then press PF5.'; cursor on ACTYPEL; VALID-DATA-SW='N' | VD010 line 511  |
| 17 | Interest rate field must not be empty                                    | INTRTL = ZERO                                                                                                                            | Msg: 'Please supply a numeric interest rate then press PF5.'; cursor on INTRTL; VALID-DATA-SW='N'; GO TO VD999           | VD010 line 526  |
| 18 | Interest rate must contain only valid characters                         | INTRTI(1:INTRTL) IS NOT NUMERIC -- INSPECT tallies digits 0-9, '.', '-', '+', ' '; if tally count < INTRTL then invalid characters present | Msg: 'Please supply a numeric interest rate'; cursor on INTRTL; VALID-DATA-SW='N'; GO TO VD999                         | VD010 line 536  |
| 19 | Interest rate must have at most one decimal point                        | WS-NUM-COUNT-POINT > 1 (count of '.' in INTRTI field)                                                                                   | Msg: 'Use one decimal point for interest rate only'; cursor on INTRTL; VALID-DATA-SW='N'; GO TO VD999                   | VD010 line 580  |
| 20 | Interest rate must have at most two decimal places                       | WS-NUM-COUNT-TOTAL > 2 (first pass: all chars after '.'; second pass: digits 0-9 and sign chars '-'/'+' after '.') -- see defect note below | Msg: 'Only up to two decimal places are supported'; cursor on INTRTL; VALID-DATA-SW='N'; GO TO VD999                 | VD010 line 625  |
| 21 | Interest rate must be zero or positive                                   | INTRTI-COMP-1 < 0 (after NUMVAL conversion)                                                                                              | Msg: 'Please supply a zero or positive interest rate'; cursor on INTRTL; VALID-DATA-SW='N'; GO TO VD999                 | VD010 line 646  |
| 22 | Interest rate must be less than 9999.99                                  | INTRTI-COMP-1 > 9999.99                                                                                                                  | Msg: 'Please supply an interest rate less than 9999.99%'; cursor on INTRTL; VALID-DATA-SW='N'; GO TO VD999              | VD010 line 656  |
| 23 | LOAN and MORTGAGE accounts cannot have zero interest rate                | (ACTYPEI = 'LOAN    ' AND INTRTI = '0000.00') OR (ACTYPEI = 'MORTGAGE' AND INTRTI = '0000.00')                                          | Msg: 'Interest rate cannot be 0 with this account type. Correct and press PF5.'; cursor on INTRTL; VALID-DATA-SW='N'; GO TO VD999 | VD010 line 667 |
| 24 | Overdraft limit must be present and numeric                              | OVERDRL = ZERO OR OVERDRI(1:OVERDRL) IS NOT NUMERIC                                                                                     | Msg: 'Overdraft must be numeric. Correct and press PF5.'; cursor on OVERDRL; VALID-DATA-SW='N'; GO TO VD999              | VD010 line 679  |
| 25 | Last statement date -- all parts must be numeric                         | LSTMTDDI NOT NUMERIC OR LSTMTMMI NOT NUMERIC OR LSTMTYYI NOT NUMERIC                                                                    | Msg: 'Last statement date must be numeric'; VALID-DATA-SW='N'; GO TO VD999                                               | VD010 line 687  |
| 26 | Next statement date -- all parts must be numeric                         | NSTMTDDI NOT NUMERIC OR NSTMTMMI NOT NUMERIC OR NSTMTYYI NOT NUMERIC                                                                    | Msg: 'Next statement date must be numeric'; VALID-DATA-SW='N'; GO TO VD999                                               | VD010 line 696  |
| 27 | Last statement date -- day must be 1-31, month must be 1-12             | WS-LSTMTDDI > 31 OR WS-LSTMTDDI = 0 OR WS-LSTMTMMI > 12 OR WS-LSTMTMMI = 0                                                            | Msg: 'Incorrect date for LAST STATEMENT.'; VALID-DATA-SW='N'                                                             | VD010 line 709  |
| 28 | Last statement date -- day 31 invalid for months 9, 4, 6, 11; day >29 invalid for month 2 | (WS-LSTMTDDI=31 AND WS-LSTMTMMI IN {9,4,6,11}) OR (WS-LSTMTDDI>29 AND WS-LSTMTMMI=2)             | Msg: 'Incorrect date for LAST STATEMENT.'; VALID-DATA-SW='N'                                                             | VD010 line 719  |
| 29 | Next statement date -- day 31 invalid for months 9, 4, 6, 11; day >29 invalid for month 2 | (WS-NSTMTDDI=31 AND WS-NSTMTMMI IN {9,4,6,11}) OR (WS-NSTMTDDI>29 AND WS-NSTMTMMI=2)            | Msg: 'Incorrect date for NEXT STATEMENT.'; VALID-DATA-SW='N'                                                             | VD010 line 733  |

**Defect -- missing range check for next statement date:** Rule 27 has no equivalent for the next statement date. After the numeric check (rule 26), the code moves NSTMTDDI/NSTMTMMI to WS-NSTMTDDI/WS-NSTMTMMI and proceeds directly to the calendar month check (rule 29) without first verifying WS-NSTMTDDI is 1-31 and WS-NSTMTMMI is 1-12. A next statement date with day=0 or month=0 would pass validation. Compare lines 709-717 (last statement range check) -- no equivalent block exists for next statement between lines 729-732.

**Defect -- duplicate next statement date calendar check:** Lines 743-751 are an exact duplicate of lines 733-741 (same condition, same message, same action). This appears to be a copy-paste artefact with no functional effect since VALID-DATA-SW is simply set to 'N' again.

**Defect -- interest rate decimal-places check off-by-one (rule 20):** The two-stage decimal check at lines 593-641 works as follows: (1) count all characters after '.'; (2) only if that count > 2, re-tally digits 0-9 and sign chars '-'/'+'  AFTER '.'. However, the inner INSPECT at line 610 positions the substring starting at (chars-before-dot + 2), which lands on the '.' character itself, and the AFTER '.' qualifier on that same INSPECT then advances past the dot -- skipping the first decimal digit. As a result, the inner count tallies digits starting from the second decimal position onward. For example, `1.234` yields an inner count of 2 (digits '3' and '4' after position 4), which fails the `> 2` test -- so three decimal places are incorrectly allowed. The check effectively tolerates up to three significant decimal digits rather than the intended two.

### Account Inquiry Result Handling (IAD010)

| #  | Rule                                         | Condition                                                      | Action                                                                                                                   | Source Location |
| -- | -------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | --------------- |
| 30 | DFHCOMMAREA initialised before INQACC call   | Always, start of IAD010                                        | INITIALIZE DFHCOMMAREA; SET COMM-PCB1-POINTER TO NULL; MOVE ACCNOI TO COMM-ACCNO -- clears all fields before inquiry    | IAD010 line 762 |
| 31 | Account not found after INQACC link          | COMM-ACC-TYPE = SPACES AND COMM-LAST-STMT-DT = ZERO            | Msg: 'This account number could not be found'; cursor on ACCNOL; VALID-DATA-SW='N'                                      | IAD010 line 837 |
| 32 | Account found -- display and prompt for edit | COMM-ACC-TYPE NOT SPACES OR COMM-LAST-STMT-DT NOT ZERO         | Msg: 'Please amend fields and hit <pf5> to apply changes'; populate all output map fields from COMM-* data              | IAD010 line 844 |

Note: ACCNO is displayed via ACCNO2O (the second account number field on the map), not ACCNOO. The opened date is displayed (OPENDDO/OPENMMO/OPENYYO from COMM-OPENED) but is treated as read-only on the inquiry screen; however it is still read back from the screen and passed to UPDACC on PF5 (see rule 33).

Note: COMM-PCB1-POINTER is set to NULL before the EXEC CICS LINK to INQACC (line 765). The DFHCOMMAREA layout includes a POINTER field intended for IMS PCB use; setting it to NULL is a defensive measure when calling INQACC as a pure CICS service without an IMS thread. This pointer field is not included in WS-COMM-AREA (which is only 99 bytes and has no POINTER field); therefore COMM-PCB1-POINTER is never persisted across pseudo-conversational iterations and must be reset to NULL at the start of each IAD010 call (see commarea structure note below).

### Account Update Data Preparation and Result Handling (UAD010)

| #  | Rule                                                                    | Condition                                                              | Action                                                                                           | Source Location  |
| -- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ---------------- |
| 33 | Opened date is passed through to UPDACC from screen fields              | Always, before EXEC CICS LINK UPDACC                                   | OPENDDI/OPENMMI/OPENYYI moved to WS-DATE-SPLIT then to COMM-OPENED; the date is not editable by intent but the value comes from the screen, not from a preserved commarea field | UAD010 lines 902-905 |
| 34 | Account number override for display -- use ACCNO2I when ACCNOI = sentinel | ACCNOI = 99999999                                                    | COMM-ACCNO is set from ACCNO2I rather than ACCNOI; handles cases where ACCNOI field shows 99999999 (map overflow sentinel) | UAD010 line 893 |
| 35 | COMM-SUCCESS pre-cleared before update call                             | Always, before EXEC CICS LINK UPDACC                                   | MOVE ' ' TO COMM-SUCCESS (space, not 'N'); allows UPDACC to set the actual result               | UAD010 line 952  |
| 36 | Update failed -- UPDACC returned failure flag                           | COMM-SUCCESS = 'N'                                                     | Msg: 'Update unsuccessful, try again later.'; VALID-DATA-SW='N'                                  | UAD010 line 1024 |
| 37 | Update succeeded -- refresh screen with result                          | COMM-SUCCESS NOT = 'N' (i.e., space or any value other than 'N')       | Msg: 'Account update successfully applied.'; populate all output map fields from returned COMM-* data | UAD010 line 1030 |

Note: The success check tests COMM-SUCCESS = 'N' for failure. Because COMM-SUCCESS is pre-cleared to ' ' (space) rather than 'N', a non-response from UPDACC (COMM-SUCCESS left as ' ') would be treated as a successful update.

**Commarea structure note:** WS-COMM-AREA in WORKING-STORAGE (passed to CICS RETURN at LENGTH(99)) contains 13 fields totalling 99 bytes and has no POINTER field. DFHCOMMAREA in LINKAGE SECTION contains the same 13 fields plus COMM-PCB1-POINTER (POINTER type, 4 bytes on 31-bit / 8 bytes on 64-bit). The RETURN TRANSID call always uses LENGTH(99), so COMM-PCB1-POINTER is excluded from the commarea stored between pseudo-conversational turns. This means COMM-PCB1-POINTER is uninitialised at the start of each new task invocation and must be explicitly set before use (which IAD010 does by setting it to NULL at line 765).

**SYNCONRETURN note:** Both EXEC CICS LINK calls (INQACC at line 772 and UPDACC at line 959) specify the SYNCONRETURN option. This causes CICS to take a syncpoint when the linked program returns control to BNK1UAC, committing any recoverable resources owned by INQACC or UPDACC before BNK1UAC continues. This means database changes made by UPDACC are committed at the point of return, not when BNK1UAC issues its own pseudo-conversational RETURN.

## Calculations

| Calculation | Formula / Logic | Input Fields | Output Field | Source Location |
| ----------- | --------------- | ------------ | ------------ | --------------- |
| Interest rate COMP-1 conversion (validate) | `COMPUTE INTRTI-COMP-1 = FUNCTION NUMVAL(INTRTI)` -- converts the screen interest rate string to a floating-point numeric value for range checking | INTRTI (screen field, character) | INTRTI-COMP-1 (COMP-1 float) | VD010 line 644 |
| Interest rate conversion for commarea | `COMPUTE INTRTI-COMP-1 = FUNCTION NUMVAL(INTRTI)`, then MOVE to INT-RT-9 (PIC 9(4)V99 within INT-RT-CONVERT redefine), then MOVE INT-RT-9 to COMM-INT-RATE | INTRTI (screen field) | COMM-INT-RATE (PIC 9(4)V99) | UAD010 lines 899-901 |
| Overdraft conversion for commarea | `COMPUTE COMM-OVERDRAFT = FUNCTION NUMVAL(OVERDRI(1:OVERDRL))` -- converts overdraft screen string to numeric | OVERDRI / OVERDRL (screen field) | COMM-OVERDRAFT (PIC 9(8)) | UAD010 line 906 |
| Available balance decimal conversion | Screen field AVBALI (PIC X(14)) is redefined as WS-CONVERT-PICX, overlaid by WS-CONVERT-SPLIT: sign(X) + decimal(9(10)) + point(X) + remainder(99). `COMPUTE WS-CONVERTED-VAL1 = WS-CONVERT-REMAIN / 100` (cents to fractional); `COMPUTE WS-CONVERTED-VAL2 = WS-CONVERT-DEC` (whole-number portion); `COMPUTE WS-CONVERTED-VAL3 = WS-CONVERTED-VAL1 + WS-CONVERTED-VAL2`; negate if WS-CONVERT-SIGN = '-' | AVBALI (screen field, PIC X(14) via WS-CONVERT-PICX split into sign, decimal, point, remainder) | COMM-AVAIL-BAL (S9(10)V99) | UAD010 lines 925-937 |
| Actual balance decimal conversion | Same algorithm as available balance conversion | ACTBALI (screen field, PIC X(14)) | COMM-ACTUAL-BAL (S9(10)V99) | UAD010 lines 939-951 |

**Note on interest rate precision:** The conversion path is NUMVAL(INTRTI) -> INTRTI-COMP-1 (COMP-1 floating point) -> INT-RT-9 (PIC 9(4)V99 without sign). Since INT-RT-9 is unsigned PIC 9(4)V99, the maximum representable value is 9999.99, which aligns with the validation rule (rule 22). However, the COMP-1 intermediate value may introduce floating-point rounding before truncation to fixed decimal.

## Error Handling

| Condition | Action | Return Code | Source Location |
| --------- | ------ | ----------- | --------------- |
| EXEC CICS RETURN TRANSID(OUAC) fails (WS-CICS-RESP NOT NORMAL) | LINK to ABNDPROC with ABNDINFO-REC; ABEND code 'HBNK'; msg: 'BNK1UAC - A010 - RETURN TRANSID(OUAC) FAIL' | ABEND HBNK | A010 lines 303-360 |
| EXEC CICS RECEIVE MAP fails (WS-CICS-RESP NOT NORMAL) | LINK to ABNDPROC; ABEND 'HBNK'; msg: 'BNKUAC - RM010 - RECEIVE MAP FAIL' | ABEND HBNK | RM010 lines 427-485 |
| EXEC CICS LINK INQACC fails (WS-CICS-RESP NOT NORMAL) | LINK to ABNDPROC; ABEND 'HBNK'; msg: 'BNK1UAC - IAD010 - LINK INQACC FAIL' | ABEND HBNK | IAD010 lines 775-832 |
| EXEC CICS LINK UPDACC fails (WS-CICS-RESP NOT NORMAL) | LINK to ABNDPROC; ABEND 'HBNK'; msg: 'BNK1UAC - UAD010 - LINK UPDACC FAIL' | ABEND HBNK | UAD010 lines 962-1019 |
| EXEC CICS SEND MAP (ERASE) fails (WS-CICS-RESP NOT NORMAL) | LINK to ABNDPROC; ABEND 'HBNK'; msg: 'BNK1UAC - SM010 - SEND MAP ERASE FAIL' | ABEND HBNK | SM010 lines 1084-1142 |
| EXEC CICS SEND MAP (DATAONLY) fails (WS-CICS-RESP NOT NORMAL) | LINK to ABNDPROC; ABEND 'HBNK'; msg: 'BNK1UAC - SM010 - SEND MAP DATAONLY FAIL' | ABEND HBNK | SM010 lines 1161-1219 |
| EXEC CICS SEND MAP (DATAONLY ALARM) fails (WS-CICS-RESP NOT NORMAL) | LINK to ABNDPROC; ABEND 'HBNK'; msg: 'BNK1UAC - SM010 - SEND MAP DATAONLY ALARM FAIL' | ABEND HBNK | SM010 lines 1238-1296 |
| EXEC CICS SEND TEXT (termination) fails (WS-CICS-RESP NOT NORMAL) | LINK to ABNDPROC; ABEND 'HBNK'; msg: 'BNK1UAC - STM010 - SEND TEXT FAIL' | ABEND HBNK | STM010 lines 1317-1375 |
| UPDACC reports update failure (COMM-SUCCESS = 'N') | Display 'Update unsuccessful, try again later.' on screen; VALID-DATA-SW='N' (no abend) | None -- user retry | UAD010 line 1024 |
| INQACC reports account not found (COMM-ACC-TYPE=SPACES AND COMM-LAST-STMT-DT=ZERO) | Display 'This account number could not be found' on screen; VALID-DATA-SW='N' | None -- user retry | IAD010 line 837 |

**Abend handler pattern (ATT010):** Every CICS error path calls PERFORM ABEND-THIS-TASK, which DISPLAYs WS-FAIL-INFO (containing program name, message, RESP and RESP2 values) then issues EXEC CICS ABEND ABCODE('HBNK') NODUMP.

**Bug -- ABND-TIME seconds field:** In all POPULATE-TIME-DATE calls the STRING that builds ABND-TIME uses WS-TIME-NOW-GRP-MM twice (e.g., lines 327-330, 453, 801, 988) instead of WS-TIME-NOW-GRP-MM for minutes and WS-TIME-NOW-GRP-SS for seconds. The seconds component of the abend timestamp is therefore always equal to the minutes value. This affects all eight abend paths in the program (A010, RM010, IAD010, UAD010, SM010 x3, STM010).

**Bug -- silent success on UPDACC non-response:** COMM-SUCCESS is pre-set to ' ' (space) before the LINK to UPDACC (line 952). The result check at line 1024 only tests COMM-SUCCESS = 'N' for failure. If UPDACC fails to populate COMM-SUCCESS (e.g., an unexpected error path), the space value passes the test and the program displays 'Account update successfully applied.' This is a potential false-positive success indication.

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. **A010** -- Main dispatch: EVALUATE EIBAID to determine which action to take
2. **PROCESS-MAP (PM010)** -- Called when ENTER or PF5 pressed; orchestrates receive, validate, and data operations; RECEIVE-MAP is called first, then VALID-DATA-SW is reset to 'Y'
3. **RECEIVE-MAP (RM010)** -- EXEC CICS RECEIVE MAP BNK1UA into BNK1UAI
4. **EDIT-DATA (ED010)** -- Called only on ENTER: validates ACCNOI is numeric
5. **INQ-ACC-DATA (IAD010)** -- Called on ENTER if ED010 passes: INITIALIZE DFHCOMMAREA; SET COMM-PCB1-POINTER TO NULL; EXEC CICS LINK INQACC SYNCONRETURN; populates screen output fields from returned commarea
6. **VALIDATE-DATA (VD010)** -- Called only on PF5: validates account type, interest rate (format/range/sign), overdraft, and both statement dates; uses GO TO VD999 for early exits
7. **UPD-ACC-DATA (UAD010)** -- Called on PF5 if VD010 passes: converts screen values to commarea numeric formats; EXEC CICS LINK UPDACC SYNCONRETURN; interprets COMM-SUCCESS result
8. **SEND-MAP (SM010)** -- Routes ERASE / DATAONLY / DATAONLY-ALARM sends of BNK1UA map based on SEND-FLAG value (88-levels: SEND-ERASE='1', SEND-DATAONLY='2', SEND-DATAONLY-ALARM='3')
9. **SEND-TERMINATION-MSG (STM010)** -- EXEC CICS SEND TEXT 'Session Ended' on PF12/AID; then caller issues EXEC CICS RETURN
10. **ABEND-THIS-TASK (ATT010)** -- DISPLAY WS-FAIL-INFO; EXEC CICS ABEND ABCODE('HBNK') NODUMP
11. **POPULATE-TIME-DATE (PTD010)** -- EXEC CICS ASKTIME / FORMATTIME to populate WS-U-TIME and WS-ORIG-DATE for abend records; FORMATTIME uses DDMMYYYY format with DATESEP
12. EXEC CICS RETURN TRANSID('OUAC') COMMAREA(WS-COMM-AREA) LENGTH(99) -- pseudo-conversational return at end of A010
