---
type: business-rules
program: BNK1CAC
program_type: online
status: draft
confidence: high
last_pass: 5
calls:
- CREACC
- ABNDPROC
called_by: []
uses_copybooks:
- ABNDINFO
- BNK1CAM
reads: []
writes: []
db_tables: []
transactions:
- OCAC
mq_queues: []
---

# BNK1CAC -- Business Rules

## Program Purpose

BNK1CAC is the CICS online Create Account program for the CBSA banking application. It presents map BNK1CA (mapset BNK1CAM) to the terminal operator, collects account-creation inputs (customer number, account type, interest rate, overdraft limit), validates all inputs, then links to the back-end program CREACC to write the new account record. On success it displays the assigned sort code, account number, opening date, statement dates and balances back on the map. Transaction ID is OCAC.

Note: the program also COPYs `DFHAID` (standard CICS attention identifier definitions) at line 67. This copybook is a CICS system-supplied member and is therefore not listed in `uses_copybooks` above.

## Input / Output

| Direction | Resource    | Type | Description                                                          |
| --------- | ----------- | ---- | -------------------------------------------------------------------- |
| IN        | BNK1CA      | CICS | BMS map (mapset BNK1CAM) -- receives customer number, account type, interest rate, overdraft limit from terminal operator |
| OUT       | BNK1CA      | CICS | BMS map (mapset BNK1CAM) -- sends confirmation or error message to terminal |
| OUT       | CREACC      | CICS | EXEC CICS LINK with SUBPGM-PARMS commarea -- creates account record in datastore |
| OUT       | ABNDPROC    | CICS | EXEC CICS LINK with ABNDINFO-REC commarea -- abend handler called on any CICS failure |
| IN/OUT    | DFHCOMMAREA | CICS | 32-byte commarea carrying WS-COMM-AREA (customer number, account type, interest rate, overdraft limit) across pseudo-conversational returns |

## Business Rules

### Session Initialisation and Navigation (A010)

| #  | Rule                          | Condition                                          | Action                                                                                   | Source Location |
| -- | ----------------------------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------- | --------------- |
| 1  | First-time entry              | EIBCALEN = ZERO                                    | Initialise map to LOW-VALUE, set cursor to customer number field (CUSTNOL = -1), set SEND-ERASE flag, clear MESSAGEO, PERFORM SEND-MAP | A010 line 169   |
| 2  | PA key pressed -- ignore      | EIBAID = DFHPA1 OR DFHPA2 OR DFHPA3               | CONTINUE (no action); falls through to commarea propagation at line 239 and EXEC CICS RETURN TRANSID('OCAC') | A010 line 179   |
| 3  | PF3 pressed -- return to menu | EIBAID = DFHPF3                                    | EXEC CICS RETURN TRANSID('OMEN') IMMEDIATE -- terminates the task immediately; never reaches post-EVALUATE commarea code | A010 line 185   |
| 4  | AID or PF12 pressed -- end    | EIBAID = DFHAID OR DFHPF12                         | PERFORM SEND-TERMINATION-MSG then EXEC CICS RETURN -- terminates the task immediately; never reaches post-EVALUATE commarea code | A010 line 197   |
| 5  | CLEAR key pressed             | EIBAID = DFHCLEAR                                  | EXEC CICS SEND CONTROL ERASE FREEKB then EXEC CICS RETURN -- terminates the task immediately; never reaches post-EVALUATE commarea code | A010 line 206   |
| 6  | ENTER key pressed             | EIBAID = DFHENTER                                  | PERFORM PROCESS-MAP -- processes the submitted form; falls through to commarea propagation at line 239 | A010 line 218   |
| 7  | Any other AID key             | WHEN OTHER                                         | Set MESSAGEO = 'Invalid key pressed.', set SEND-DATAONLY-ALARM flag, PERFORM SEND-MAP; falls through to commarea propagation at line 239 | A010 line 224   |
| 8  | Commarea propagation -- defect | EIBCALEN NOT = 0 (after EVALUATE, unconditional for PA / ENTER / OTHER paths) | Copy SUBPGM-CUSTNO, SUBPGM-ACC-TYPE, SUBPGM-INT-RT, SUBPGM-OVERDR-LIM from SUBPGM-PARMS into WS-COMM-AREA. NOTE: PF3, PF12/AID, and CLEAR all issue EXEC CICS RETURN inside the EVALUATE and never reach this code. However, for PA keys (CONTINUE) and WHEN OTHER (invalid key), CREACC was never called so SUBPGM-PARMS contains stale or zero data from WORKING-STORAGE initialisation. | A010 line 239   |
| 9  | Commarea initialisation       | EIBCALEN = 0 (after EVALUATE)                      | INITIALIZE WS-COMM-AREA                                                                  | A010 line 244   |
| 10 | Pseudo-conversational return  | Always (after above)                               | EXEC CICS RETURN TRANSID('OCAC') COMMAREA(WS-COMM-AREA) LENGTH(32) -- re-queues transaction with 32-byte commarea | A010 line 248   |

### Input Validation (ED010 / EDIT-DATA)

| #  | Rule                                       | Condition                                                                                           | Action                                                                            | Source Location  |
| -- | ------------------------------------------ | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ---------------- |
| 11 | Customer number -- mandatory, non-blank    | CUSTNOL < 1 OR CUSTNOI = '__________' (ten underscores, BMS default fill)                           | MESSAGEO = 'Please enter a 10 digit Customer Number', VALID-DATA-SW = 'N', cursor to CUSTNOL, GO TO ED999 | ED010 line 437   |
| 12 | Customer number -- must be numeric         | CUSTNOI NOT NUMERIC (after DEEDIT)                                                                  | MESSAGEO = 'Please enter a numeric Customer number', VALID-DATA-SW = 'N', cursor to CUSTNOL, GO TO ED999 | ED010 line 448   |
| 13 | Account type -- mandatory, non-blank       | ACCTYPI = '________' OR ACCTYPL < 1                                                                 | MESSAGEO = 'Account Type should be ISA,CURRENT,LOAN,SAVING or MORTGAGE', VALID-DATA-SW = 'N', cursor to ACCTYPL, GO TO ED999 | ED010 line 459   |
| 14 | Account type -- valid values (case insensitive) | ACCTYPL > 0 -- EVALUATE ACCTYPI WHEN OTHER                                               | Valid values: ISA, CURRENT, LOAN, SAVING, MORTGAGE (any case; padded or underscore-filled variants normalised to canonical padded form). Any other value sets MESSAGEO = 'Account Type should be ISA,CURRENT,LOAN,SAVING or MORTGAGE', VALID-DATA-SW = 'N', GO TO ED999 | ED010 line 472   |
| 15 | Account type -- ISA normalisation          | ACCTYPI IN ('ISA_____', 'isa_____', 'isa     ')                                                     | Normalise to 'ISA     ' (8 chars padded)                                          | ED010 line 475   |
| 16 | Account type -- CURRENT normalisation      | ACCTYPI IN ('CURRENT_', 'current_', 'current ')                                                     | Normalise to 'CURRENT ' (8 chars padded)                                          | ED010 line 486   |
| 17 | Account type -- LOAN normalisation         | ACCTYPI IN ('LOAN____', 'loan____', 'loan    ')                                                     | Normalise to 'LOAN    ' (8 chars padded)                                          | ED010 line 497   |
| 18 | Account type -- SAVING normalisation       | ACCTYPI IN ('SAVING__', 'saving__', 'saving  ')                                                     | Normalise to 'SAVING  ' (8 chars padded)                                          | ED010 line 508   |
| 19 | Account type -- MORTGAGE normalisation     | ACCTYPI = 'mortgage'                                                                                | Normalise to 'MORTGAGE' (8 chars)                                                 | ED010 line 521   |
| 20 | Interest rate -- mandatory                 | INTRTL = ZERO                                                                                       | MESSAGEO = 'Please supply a numeric interest rate', VALID-DATA-SW = 'N', cursor to INTRTL, GO TO ED999 | ED010 line 538   |
| 21 | Interest rate -- valid characters          | INTRTI(1:INTRTL) IS NOT NUMERIC: tally digits 0-9, '.', '-', '+', ' '; if WS-NUM-COUNT-TOTAL < INTRTL (unrecognised chars present) | MESSAGEO = 'Please supply a numeric interest rate', VALID-DATA-SW = 'N', GO TO ED999 | ED010 line 548   |
| 22 | Interest rate -- at most one decimal point | WS-NUM-COUNT-POINT > 1 (more than one '.' found in INTRTI)                                          | MESSAGEO = 'Use one decimal point for interest rate only', VALID-DATA-SW = 'N', GO TO ED999 | ED010 line 594   |
| 23 | Interest rate -- at most two decimal places | WS-NUM-COUNT-POINT = 1 AND WS-NUM-COUNT-TOTAL > 2 (more than two significant digits after '.', excluding trailing +/- signs) | MESSAGEO = 'Only up to two decimal places are supported', VALID-DATA-SW = 'N', GO TO ED999 | ED010 line 606   |
| 24 | Interest rate -- must not be negative      | INTRTI-COMP-1 (COMP-1 numeric value of INTRTI via FUNCTION NUMVAL) < 0                             | MESSAGEO = 'Please supply a zero or positive interest rate', VALID-DATA-SW = 'N', GO TO ED999 | ED010 line 663   |
| 25 | Interest rate -- maximum value             | INTRTI-COMP-1 > 9999.99                                                                             | MESSAGEO = 'Please supply an interest rate less than 9999.99%', VALID-DATA-SW = 'N', GO TO ED999 | ED010 line 673   |
| 26 | Overdraft limit -- must be numeric digits only | Trailing spaces stripped from OVERDRI; count digits 0-9 in OVERDRI(1:OVERDRL); if WS-NUM-COUNT-TOTAL < OVERDRL (non-digit characters present) | MESSAGEO = 'Overdraft Limit must be numeric positive int', VALID-DATA-SW = 'N', cursor to OVERDRL, GO TO ED999 | ED010 line 701   |
| 27 | Overdraft limit -- default to zero if omitted | OVERDRL < 1 OR OVERDRI = '________' OR OVERDRI = SPACES (after DEEDIT)                            | MOVE ZERO TO OVERDRI (overdraft defaults to 0 if not supplied)                    | ED010 line 717   |
| 28 | Overdraft limit -- post-DEEDIT numeric check | OVERDRI NOT NUMERIC (after EXEC CICS BIF DEEDIT)                                                   | MESSAGEO = 'The Overdraft Limit must be numeric', VALID-DATA-SW = 'N', cursor to OVERDRL, GO TO ED999 | ED010 line 724   |
| 29 | Cross-field check -- customer and account type both present | CUSTNOL < 1 OR ACCTYPL < 1                                                      | MESSAGEO = 'Missing expected data.', VALID-DATA-SW = 'N', GO TO ED999            | ED010 line 736   |

### Account Creation (CAD010 / CRE-ACC-DATA)

| #  | Rule                                         | Condition                              | Action                                                                                                                  | Source Location |
| -- | -------------------------------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | --------------- |
| 30 | Invoke account creation back-end             | VALID-DATA is true (88-level)          | Initialise SUBPGM-PARMS; set eyecatcher 'ACCT'; set SUBPGM-SUCCESS = 'N'; copy CUSTNOI, ACCTYPI, INTRTI-COMP-1, OVERDRI to SUBPGM-PARMS; zero sort code, account number, opened date, last/next statement dates, balances; EXEC CICS LINK PROGRAM('CREACC') COMMAREA(SUBPGM-PARMS) SYNCONRETURN | CAD010 line 753 |
| 31 | Creation failure -- customer not found       | SUBPGM-SUCCESS = 'N' AND SUBPGM-FAIL-CODE = '1' | MESSAGEO = 'The supplied customer number does not exist.'                                                     | CAD010 line 851 |
| 32 | Creation failure -- customer data inaccessible | SUBPGM-SUCCESS = 'N' AND SUBPGM-FAIL-CODE = '2' | MESSAGEO = 'The customer data cannot be accessed, unable to create account.'                                | CAD010 line 855 |
| 33 | Creation failure -- ENQ on ACCOUNT NC failed | SUBPGM-SUCCESS = 'N' AND SUBPGM-FAIL-CODE = '3' | MESSAGEO = 'Account record creation failed. (unable to ENQ ACCOUNT NC).'                                    | CAD010 line 862 |
| 34 | Creation failure -- increment ACCOUNT NC failed | SUBPGM-SUCCESS = 'N' AND SUBPGM-FAIL-CODE = '4' | MESSAGEO = 'Account record creation failed, (unable to increment ACCOUNT NC).'                            | CAD010 line 869 |
| 35 | Creation failure -- restore ACCOUNT NC failed | SUBPGM-SUCCESS = 'N' AND SUBPGM-FAIL-CODE = '5' | MESSAGEO = 'Account record creation failed, (unable to restore ACCOUNT NC).'                              | CAD010 line 876 |
| 36 | Creation failure -- WRITE to ACCOUNT file failed | SUBPGM-SUCCESS = 'N' AND SUBPGM-FAIL-CODE = '6' | MESSAGEO = 'Account record creation failed, (unable to WRITE to ACCOUNT file).'                         | CAD010 line 883 |
| 37 | Creation failure -- INSERT into ACCOUNT DB2 failed | SUBPGM-SUCCESS = 'N' AND SUBPGM-FAIL-CODE = '7' | MESSAGEO = 'Account record creation failed, (unable to INSERT into ACCOUNT).'                         | CAD010 line 890 |
| 38 | Creation failure -- too many accounts        | SUBPGM-SUCCESS = 'N' AND SUBPGM-FAIL-CODE = '8' | MESSAGEO = 'Account record creation failed, (too many accounts).'                                           | CAD010 line 897 |
| 39 | Creation failure -- unable to count accounts | SUBPGM-SUCCESS = 'N' AND SUBPGM-FAIL-CODE = '9' | MESSAGEO = 'Account record creation failed, unable to count accounts.'                                      | CAD010 line 904 |
| 40 | Creation failure -- account type unsupported | SUBPGM-SUCCESS = 'N' AND SUBPGM-FAIL-CODE = 'A' | MESSAGEO = 'Account record creation failed, account type unsupported.'                                      | CAD010 line 911 |
| 41 | Creation failure -- unrecognised fail code   | SUBPGM-SUCCESS = 'N' AND SUBPGM-FAIL-CODE = OTHER | MESSAGEO = 'The account was not created.'                                                                  | CAD010 line 918 |
| 42 | Creation success -- populate map fields      | SUBPGM-SUCCESS NOT = 'N' (i.e. success) | MESSAGEO = 'The Account has been successfully created'; populate SRTCDO, ACCNOO, OPENDDO/MM/YY, NSTMTDDO/MM/YY, LSTMDDO/MM/YY, AVAILO, ACTBALO from SUBPGM-PARMS | CAD010 line 923 |
| 43 | Always populate editable output fields       | Always (after success/failure branch)  | Copy SUBPGM-CUSTNO to CUSTNOO, SUBPGM-ACC-TYPE to ACCTYPO, SUBPGM-INT-RT (via INTRT-PIC9) to INTRTO, SUBPGM-OVERDR-LIM to OVERDRO | CAD010 line 950 |

### Map Send Mode (PM010)

| #  | Rule                                      | Condition                     | Action                                                                                 | Source Location |
| -- | ----------------------------------------- | ----------------------------- | -------------------------------------------------------------------------------------- | --------------- |
| 44 | Alarm always fires after PROCESS-MAP      | Unconditional (after VALID-DATA check and optional CRE-ACC-DATA call) | SET SEND-DATAONLY-ALARM TO TRUE before PERFORM SEND-MAP -- the terminal beeps on every ENTER submission including successful account creation | PM010 line 340  |

## Calculations

| Calculation              | Formula / Logic                                                                                                                  | Input Fields          | Output Field      | Source Location |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------- | --------------------- | ----------------- | --------------- |
| Interest rate conversion | COMPUTE INTRTI-COMP-1 = FUNCTION NUMVAL(INTRTI) -- converts display string entered by operator into COMP-1 floating-point value for range validation and downstream use | INTRTI (screen field, PIC X) | INTRTI-COMP-1 (COMP-1) | ED010 line 658; CAD010 line 763 |
| Overdraft trailing-space strip | MOVE FUNCTION REVERSE(OVERDRI) TO WS-REVERSE; INSPECT WS-REVERSE TALLYING WS-NUM-COUNT-TOTAL FOR LEADING SPACES; SUBTRACT WS-NUM-COUNT-TOTAL FROM OVERDRL GIVING OVERDRL -- adjusts the length cursor to exclude trailing spaces before digit-only check | OVERDRI, WS-REVERSE   | OVERDRL           | ED010 line 683  |
| Decimal-places count     | INSPECT INTRTI(1:INTRTL) TALLYING WS-NUM-COUNT-TOTAL FOR CHARACTERS AFTER '.'; if WS-NUM-COUNT-TOTAL > 2, check further for trailing +/- -- ensures no more than 2 significant decimal digits | INTRTI, INTRTL        | WS-NUM-COUNT-TOTAL, WS-NUM-COUNT-POINT | ED010 line 606 |
| Interest rate display    | MOVE SUBPGM-INT-RT TO INTRT-PIC9 (PIC 9999.99) then MOVE INTRT-PIC9 TO INTRTO -- reformats COMP-1 rate to display picture | SUBPGM-INT-RT         | INTRTO (map output field) | CAD010 line 952 |

## Error Handling

| Condition                                    | Action                                                                                                                  | Return Code | Source Location      |
| -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------- | -------------------- |
| EXEC CICS RETURN TRANSID(OCAC) non-NORMAL    | INITIALIZE ABNDINFO-REC; capture EIBRESP/RESP2, APPLID, TASKNO, TRANID, time/date; ABND-CODE = 'HBNK'; string diagnostic into ABND-FREEFORM ('A010- RETURN TRANSID(OCAC)...'); EXEC CICS LINK PROGRAM('ABNDPROC'); PERFORM ABEND-THIS-TASK | HBNK (CICS abend code) | A010 line 256 |
| EXEC CICS RECEIVE MAP non-NORMAL             | Same abend pattern; ABND-FREEFORM = 'RM010 - RECEIVE MAP FAIL...'                                                      | HBNK        | RM010 line 364       |
| EXEC CICS LINK PROGRAM('CREACC') non-NORMAL  | Same abend pattern; ABND-FREEFORM = 'CAD010 - LINK CREACC FAILED...'                                                   | HBNK        | CAD010 line 783      |
| EXEC CICS SEND MAP (ERASE mode) non-NORMAL   | Same abend pattern; ABND-FREEFORM = 'SM010 -SEND MAP ERASE FAIL...'                                                    | HBNK        | SM010 line 976       |
| EXEC CICS SEND MAP (DATAONLY mode) non-NORMAL | Same abend pattern; ABND-FREEFORM = 'SM010 - SEND MAP DATAONLY Fail...'                                               | HBNK        | SM010 line 1051      |
| EXEC CICS SEND MAP (DATAONLY ALARM mode) non-NORMAL | Same abend pattern; ABND-FREEFORM = 'SM010 - SEND MAP DATAONLY ALARM fail...'                                  | HBNK        | SM010 line 1130      |
| EXEC CICS SEND TEXT (termination msg) non-NORMAL | Same abend pattern; ABND-FREEFORM = 'STM010 - SEND TEXT FAIL...'                                                  | HBNK        | STM010 line 1208     |
| ABEND-THIS-TASK (ATT010)                     | DISPLAY WS-FAIL-INFO (program name + message + RESP + RESP2 + 'ABENDING TASK.'); EXEC CICS ABEND ABCODE('HBNK') NODUMP | HBNK        | ATT010 line 1273     |
| CREACC returns SUBPGM-SUCCESS = 'N'          | Set VALID-DATA-SW = 'N'; map SUBPGM-FAIL-CODE to a user-facing MESSAGEO string (fail codes '1' through '9', 'A', OTHER -- see rules 31-41) | VALID-DATA-SW = 'N' | CAD010 line 845 |
| ABND-TIME always contains HH:MM:MM (defect)  | In every abend STRING block the third token is WS-TIME-NOW-GRP-MM instead of WS-TIME-NOW-GRP-SS -- the seconds component of the abend timestamp is always incorrect (shows minutes twice). Affects A010, RM010, CAD010, SM010 (x3), STM010. | N/A (diagnostic defect) | A010 line 289; RM010 line 396; CAD010 line 810; SM010 lines 1007, 1083, 1161; STM010 line 1235 |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. A010 (PREMIERE SECTION) -- main dispatch; evaluates EIBAID to route terminal input
2. PROCESS-MAP (PM010) -- called when ENTER is pressed; orchestrates receive-validate-create cycle
3. RECEIVE-MAP (RM010) -- EXEC CICS RECEIVE MAP BNK1CA into BNK1CAI
4. EDIT-DATA (ED010) -- sequential field-by-field validation of CUSTNOI, ACCTYPI, INTRTI, OVERDRI; uses GO TO ED999 for early exit on first failure
5. CRE-ACC-DATA (CAD010) -- called only when VALID-DATA (88-level condition is true); builds SUBPGM-PARMS and EXEC CICS LINK PROGRAM('CREACC') SYNCONRETURN; interprets SUBPGM-SUCCESS and SUBPGM-FAIL-CODE
6. SEND-MAP (SM010) -- sends BNK1CA map in one of three modes: ERASE (first display), DATAONLY, or DATAONLY with ALARM; mode controlled by SEND-FLAG 88-levels; PM010 always sets SEND-DATAONLY-ALARM before calling SEND-MAP
7. SEND-TERMINATION-MSG (STM010) -- EXEC CICS SEND TEXT with 'Session Ended' message
8. ABEND-THIS-TASK (ATT010) -- called on any CICS failure; displays error and issues EXEC CICS ABEND ABCODE('HBNK') NODUMP
9. POPULATE-TIME-DATE (PTD010) -- EXEC CICS ASKTIME + FORMATTIME DDMMYYYY; populates WS-U-TIME, WS-ORIG-DATE, WS-TIME-NOW for abend info records
10. EXEC CICS RETURN TRANSID('OCAC') -- always executed at end of A010 (for PA, ENTER, OTHER, and first-time paths) to maintain pseudo-conversational loop with 32-byte commarea

## Implementation Notes

The following WORKING-STORAGE fields are defined but never referenced anywhere in the PROCEDURE DIVISION. They appear to be template code copied from a sibling BNK1 program and not cleaned up:

- `COMM-DOB-SPLIT` (lines 69-72) -- PIC 99 DD/MM/YYYY split structure; no date-of-birth field exists on the BNK1CA map
- `DATE-REFORMED` (lines 80-89) -- NSTMTDD/MM/YY split structures; the procedure uses direct substring moves (e.g. SUBPGM-NEXT-STMT-DT(1:2)) rather than this structure
- `MORE-STRING-CONVS` / `NST-CHAR` / `NST-DATE-GRP` (lines 91-94) -- 8-byte string conversion area; unused
- `COMPANY-NAME-FULL` (line 119) -- PIC X(32); not populated or referenced
- `ACTION-ALPHA` / `ACTION-NUM` (lines 53-54) -- single-digit action code; not referenced
- `RESPONSE-CODE` (line 61) -- PIC S9(8) COMP; CICS response stored in WS-CICS-RESP instead
- `COMMUNICATION-AREA` (line 63) -- PIC X single-byte placeholder; the actual commarea is DFHCOMMAREA in the LINKAGE SECTION
