---
type: business-rules
program: CORPT00C
program_type: online
status: draft
confidence: high
last_pass: 5
calls:
- CSUTLDTC
called_by: []
uses_copybooks:
- COCOM01Y
- CORPT00
- COTTL01Y
- CSDAT01Y
- CSMSG01Y
- CVTRA05Y
reads: []
writes: []
db_tables: []
transactions:
- CR00
mq_queues: []
---

# CORPT00C -- Business Rules

## Program Purpose

CORPT00C is a CICS online program (transaction CR00) that allows users to request
transaction reports by submitting a batch job to an extra-partition transient data
queue (TDQ) named JOBS. The screen (map CORPT0A / mapset CORPT00) offers three
report types: Monthly, Yearly, or Custom date range. For Monthly and Yearly, the
program derives the date range automatically from the current date. For Custom
range, the program validates each date component entered by the user, then calls
the CSUTLDTC date-validation utility before writing JCL records to the JOBS TDQ.
The TDQ acts as an internal reader, causing the batch job TRNRPT00 (via procedure
TRANREPT in library AWS.M2.CARDDEMO.PROC) to be submitted automatically.

## Input / Output

| Direction | Resource    | Type | Description                                                      |
| --------- | ----------- | ---- | ---------------------------------------------------------------- |
| IN        | CORPT0A     | CICS | BMS map screen input -- report type selection and date fields    |
| OUT       | CORPT0A     | CICS | BMS map screen output -- confirmation messages and error text    |
| OUT       | JOBS        | CICS TDQ (extra-partition) | JCL records written to internal reader to submit TRNRPT00 batch job |
| IN/OUT    | CARDDEMO-COMMAREA | CICS COMMAREA | Program communication area passed across pseudo-conversational returns |
| CALL      | CSUTLDTC    | Subprogram | Date validation utility (wraps CEEDAYS LE API)               |

## Business Rules

### Session Initialisation

| #  | Rule                          | Condition                                              | Action                                                                    | Source Location |
| -- | ----------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------- | --------------- |
| 1  | No COMMAREA -- redirect to signon | `EIBCALEN = 0`                                     | Set `CDEMO-TO-PROGRAM = 'COSGN00C'`, PERFORM RETURN-TO-PREV-SCREEN (XCTL) | MAIN-PARA (line 172-174) |
| 2  | First entry -- display blank screen | `NOT CDEMO-PGM-REENTER` (i.e., `CDEMO-PGM-CONTEXT = 0`) | Set `CDEMO-PGM-REENTER` to TRUE, send initial screen with ERASE, cursor on MONTHLY field | MAIN-PARA (line 177-181) |
| 3  | Re-entry -- receive screen and dispatch | `CDEMO-PGM-REENTER` (i.e., `CDEMO-PGM-CONTEXT = 1`) | PERFORM RECEIVE-TRNRPT-SCREEN, then evaluate AID key                   | MAIN-PARA (line 182-195) |

### AID Key Routing

| #  | Rule                        | Condition                    | Action                                                                                  | Source Location |
| -- | --------------------------- | ---------------------------- | --------------------------------------------------------------------------------------- | --------------- |
| 4  | Enter key -- process input  | `EIBAID = DFHENTER`          | PERFORM PROCESS-ENTER-KEY                                                               | MAIN-PARA (line 185-186) |
| 5  | PF3 -- return to main menu  | `EIBAID = DFHPF3`            | Set `CDEMO-TO-PROGRAM = 'COMEN01C'`, PERFORM RETURN-TO-PREV-SCREEN (XCTL)              | MAIN-PARA (line 187-189) |
| 6  | Any other key -- invalid    | `EIBAID = WHEN OTHER`        | Set `WS-ERR-FLG = 'Y'`, move `CCDA-MSG-INVALID-KEY` to `WS-MESSAGE`, redisplay screen | MAIN-PARA (line 190-194) |

### Report Type Selection

| #  | Rule                           | Condition                                                         | Action                                                                                 | Source Location |
| -- | ------------------------------ | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------- | --------------- |
| 7  | Monthly report selected        | `MONTHLYI OF CORPT0AI NOT = SPACES AND LOW-VALUES`               | Derive date range for current month (first day through last day), set `WS-REPORT-NAME = 'Monthly'`, PERFORM SUBMIT-JOB-TO-INTRDR | PROCESS-ENTER-KEY (line 213-238) |
| 8  | Yearly report selected         | `YEARLYI OF CORPT0AI NOT = SPACES AND LOW-VALUES`                | Set date range to full current year (01/01 through 12/31), set `WS-REPORT-NAME = 'Yearly'`, PERFORM SUBMIT-JOB-TO-INTRDR | PROCESS-ENTER-KEY (line 239-255) |
| 9  | Custom date range selected     | `CUSTOMI OF CORPT0AI NOT = SPACES AND LOW-VALUES`                | Validate each date component, call CSUTLDTC for each date, submit if no errors; set `WS-REPORT-NAME = 'Custom'` | PROCESS-ENTER-KEY (line 256-436) |
| 10 | No report type selected        | WHEN OTHER (none of the above fields populated)                   | Set `WS-ERR-FLG = 'Y'`, message: `'Select a report type to print report...'`, cursor on MONTHLY | PROCESS-ENTER-KEY (line 437-442) |

### Custom Date Validation -- Mandatory Field Checks (performed first, in order)

| #  | Rule                                  | Condition                                             | Error Message                                   | Action                                    | Source Location |
| -- | ------------------------------------- | ----------------------------------------------------- | ----------------------------------------------- | ----------------------------------------- | --------------- |
| 11 | Start Date Month is mandatory         | `SDTMMI OF CORPT0AI = SPACES OR LOW-VALUES`          | `'Start Date - Month can NOT be empty...'`      | Set ERR-FLG-ON, cursor on SDTMM, redisplay | PROCESS-ENTER-KEY (line 259-265) |
| 12 | Start Date Day is mandatory           | `SDTDDI OF CORPT0AI = SPACES OR LOW-VALUES`          | `'Start Date - Day can NOT be empty...'`        | Set ERR-FLG-ON, cursor on SDTDD, redisplay | PROCESS-ENTER-KEY (line 266-272) |
| 13 | Start Date Year is mandatory          | `SDTYYYYI OF CORPT0AI = SPACES OR LOW-VALUES`        | `'Start Date - Year can NOT be empty...'`       | Set ERR-FLG-ON, cursor on SDTYYYY, redisplay | PROCESS-ENTER-KEY (line 273-279) |
| 14 | End Date Month is mandatory           | `EDTMMI OF CORPT0AI = SPACES OR LOW-VALUES`          | `'End Date - Month can NOT be empty...'`        | Set ERR-FLG-ON, cursor on EDTMM, redisplay | PROCESS-ENTER-KEY (line 280-286) |
| 15 | End Date Day is mandatory             | `EDTDDI OF CORPT0AI = SPACES OR LOW-VALUES`          | `'End Date - Day can NOT be empty...'`          | Set ERR-FLG-ON, cursor on EDTDD, redisplay | PROCESS-ENTER-KEY (line 287-293) |
| 16 | End Date Year is mandatory            | `EDTYYYYI OF CORPT0AI = SPACES OR LOW-VALUES`        | `'End Date - Year can NOT be empty...'`         | Set ERR-FLG-ON, cursor on EDTYYYY, redisplay | PROCESS-ENTER-KEY (line 294-300) |

Note: Each mandatory-field check is a WHEN clause inside an EVALUATE TRUE block (lines 258-303). Each branch PERFORMs SEND-TRNRPT-SCREEN which unconditionally executes `GO TO RETURN-TO-CICS`. This means only the first failing field is reported per transaction; subsequent WHEN clauses are never reached once one fires. The WHEN OTHER branch is CONTINUE, meaning execution falls through to line 305 only when all six fields are populated.

### Custom Date Validation -- Range/Format Checks (applied after NUMVAL-C conversion)

| #  | Rule                                    | Condition                                                                              | Error Message                               | Action                                    | Source Location |
| -- | --------------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------- | ----------------------------------------- | --------------- |
| 17 | Start Date Month must be numeric 01-12  | `SDTMMI NOT NUMERIC OR SDTMMI > '12'`                                                 | `'Start Date - Not a valid Month...'`       | Set ERR-FLG-ON, cursor on SDTMM, redisplay | PROCESS-ENTER-KEY (line 329-336) |
| 18 | Start Date Day must be numeric 01-31   | `SDTDDI NOT NUMERIC OR SDTDDI > '31'`                                                 | `'Start Date - Not a valid Day...'`         | Set ERR-FLG-ON, cursor on SDTDD, redisplay | PROCESS-ENTER-KEY (line 338-345) |
| 19 | Start Date Year must be numeric        | `SDTYYYYI NOT NUMERIC`                                                                 | `'Start Date - Not a valid Year...'`        | Set ERR-FLG-ON, cursor on SDTYYYY, redisplay | PROCESS-ENTER-KEY (line 347-353) |
| 20 | End Date Month must be numeric 01-12   | `EDTMMI NOT NUMERIC OR EDTMMI > '12'`                                                 | `'End Date - Not a valid Month...'`         | Set ERR-FLG-ON, cursor on EDTMM, redisplay | PROCESS-ENTER-KEY (line 355-362) |
| 21 | End Date Day must be numeric 01-31     | `EDTDDI NOT NUMERIC OR EDTDDI > '31'`                                                 | `'End Date - Not a valid Day...'`           | Set ERR-FLG-ON, cursor on EDTDD, redisplay | PROCESS-ENTER-KEY (line 364-371) |
| 22 | End Date Year must be numeric          | `EDTYYYYI NOT NUMERIC`                                                                 | `'End Date - Not a valid Year...'`          | Set ERR-FLG-ON, cursor on EDTYYYY, redisplay | PROCESS-ENTER-KEY (line 373-379) |

Note: These six range/format checks are sequential IF statements (not an EVALUATE), so in principle they could all be evaluated. However, each IF branch PERFORMs SEND-TRNRPT-SCREEN which immediately executes `GO TO RETURN-TO-CICS`, returning control to CICS before the next IF is reached. The effective behaviour is therefore identical to the mandatory checks: only the first failing range check is reported per transaction. The NUMVAL-C normalisation at lines 305-327 runs unconditionally before these IFs, but only when all mandatory fields were populated (otherwise RETURN-TO-CICS was already taken by one of the mandatory-field WHEN branches).

### Custom Date Validation -- Calendar Validity via CSUTLDTC

| #  | Rule                                        | Condition                                                                                   | Error Message                               | Action                                    | Source Location |
| -- | ------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------- | ----------------------------------------- | --------------- |
| 23 | Start Date must be a valid calendar date    | `CSUTLDTC-RESULT-SEV-CD NOT = '0000'` AND `CSUTLDTC-RESULT-MSG-NUM NOT = '2513'` for start date | `'Start Date - Not a valid date...'`    | Set ERR-FLG-ON, cursor on SDTMM, redisplay | PROCESS-ENTER-KEY (line 396-405) |
| 24 | End Date must be a valid calendar date      | `CSUTLDTC-RESULT-SEV-CD NOT = '0000'` AND `CSUTLDTC-RESULT-MSG-NUM NOT = '2513'` for end date   | `'End Date - Not a valid date...'`      | Set ERR-FLG-ON, cursor on EDTMM, redisplay | PROCESS-ENTER-KEY (line 416-425) |
| 25 | CSUTLDTC message 2513 is tolerated         | `CSUTLDTC-RESULT-MSG-NUM = '2513'` (even if severity non-zero)                              | (no error)                                  | CONTINUE -- message 2513 is treated as acceptable (likely a non-fatal informational code from CEEDAYS) | PROCESS-ENTER-KEY (line 399, 419) |
| 26 | Custom validation gate -- only submit when all validations pass | `NOT ERR-FLG-ON` after all six range checks and both CSUTLDTC calls | PERFORM SUBMIT-JOB-TO-INTRDR | PROCESS-ENTER-KEY (line 434-436) |

### Confirmation Gate

| #  | Rule                                      | Condition                                                 | Action                                                                                        | Source Location |
| -- | ----------------------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------------------------- | --------------- |
| 27 | Confirm field is mandatory before submit  | `CONFIRMI OF CORPT0AI = SPACES OR LOW-VALUES`            | Message: `'Please confirm to print the <report-name> report...'`, set ERR-FLG-ON, cursor on CONFIRM, redisplay | SUBMIT-JOB-TO-INTRDR (line 464-473) |
| 28 | Confirm = Y or y -- proceed with submit   | `CONFIRMI = 'Y' OR 'y'`                                  | CONTINUE -- write JCL records to TDQ                                                          | SUBMIT-JOB-TO-INTRDR (line 478-479) |
| 29 | Confirm = N or n -- cancel submission     | `CONFIRMI = 'N' OR 'n'`                                  | PERFORM INITIALIZE-ALL-FIELDS, set ERR-FLG-ON, redisplay screen (no batch job submitted)     | SUBMIT-JOB-TO-INTRDR (line 480-483) |
| 30 | Confirm = any other value -- invalid      | WHEN OTHER                                               | Message: `'"<value>" is not a valid value to confirm...'`, set ERR-FLG-ON, cursor on CONFIRM, redisplay | SUBMIT-JOB-TO-INTRDR (line 484-493) |

### Post-Submission Feedback

| #  | Rule                                 | Condition                    | Action                                                                            | Source Location |
| -- | ------------------------------------ | ---------------------------- | --------------------------------------------------------------------------------- | --------------- |
| 31 | Success confirmation message         | `NOT ERR-FLG-ON` after submit | PERFORM INITIALIZE-ALL-FIELDS, colour ERRMSG green (`DFHGREEN`), display message `'<report-name> report submitted for printing ...'` | PROCESS-ENTER-KEY (line 445-454) |

### Navigation / Fallback

| #  | Rule                                         | Condition                                           | Action                                                                 | Source Location |
| -- | -------------------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------- | --------------- |
| 32 | RETURN-TO-PREV-SCREEN defaults to signon     | `CDEMO-TO-PROGRAM = LOW-VALUES OR SPACES`          | Set `CDEMO-TO-PROGRAM = 'COSGN00C'` before XCTL                       | RETURN-TO-PREV-SCREEN (line 542-544) |
| 33 | RETURN-TO-PREV-SCREEN records return context | Always (before XCTL)                               | Set `CDEMO-FROM-TRANID = WS-TRANID ('CR00')`, `CDEMO-FROM-PROGRAM = WS-PGMNAME ('CORPT00C')`, `CDEMO-PGM-CONTEXT = ZEROS` in COMMAREA before XCTL | RETURN-TO-PREV-SCREEN (line 545-550) |

### Screen Send Behaviour

| #  | Rule                                      | Condition                        | Action                                                                   | Source Location |
| -- | ----------------------------------------- | -------------------------------- | ------------------------------------------------------------------------ | --------------- |
| 34 | Screen always sent with ERASE flag        | `SEND-ERASE-YES` (88-level, always TRUE) | `EXEC CICS SEND MAP ERASE CURSOR`. The ELSE branch (send without ERASE) is initialised in WORKING-STORAGE but `WS-SEND-ERASE-FLG` is never set to 'N' in the PROCEDURE DIVISION -- the non-ERASE path is dead code | SEND-TRNRPT-SCREEN (line 562-578) |
| 35 | RECEIVE-TRNRPT-SCREEN does not check RESP | Always (no IF after RECEIVE)     | RESP/RESP2 are captured in `WS-RESP-CD`/`WS-REAS-CD` but never tested after a RECEIVE -- any CICS error on receive is silently ignored | RECEIVE-TRNRPT-SCREEN (line 596-604) |

### Code Quality Observations

| #  | Rule                                           | Condition              | Action                                                                          | Source Location |
| -- | ---------------------------------------------- | ---------------------- | ------------------------------------------------------------------------------- | --------------- |
| 36 | Dead-code literal WS-TRANSACT-FILE             | Always (never used)    | `WS-TRANSACT-FILE PIC X(08) VALUE 'TRANSACT'` is defined in WORKING-STORAGE but no READ, WRITE, or OPEN statement references it -- this is a vestigial field from an earlier design | WS-VARIABLES (line 40) |
| 37 | Debug DISPLAY statement left in production code | Always (unconditional) | `DISPLAY 'PROCESS ENTER KEY'` executes every time the Enter key is pressed; this will appear in CICS job log / JESMSGLG output and is not protected by any debug flag | PROCESS-ENTER-KEY (line 210) |
| 38 | Dead-code flag WS-TRANSACT-EOF / TRANSACT-NOT-EOF | Always (never tested) | `SET TRANSACT-NOT-EOF TO TRUE` is executed unconditionally in MAIN-PARA (line 166) but the 88-level conditions `TRANSACT-EOF` and `TRANSACT-NOT-EOF` are never evaluated anywhere in the PROCEDURE DIVISION -- vestigial from an earlier design that may have read a file | MAIN-PARA (line 166); WS-VARIABLES (lines 44-46) |
| 39 | CICS RETURN omits LENGTH clause                | Always (RETURN-TO-CICS and MAIN-PARA fall-through) | The `LENGTH(LENGTH OF CARDDEMO-COMMAREA)` parameter is commented out at line 590 -- CICS infers the COMMAREA length from the incoming EIBCALEN rather than the declared structure length. This is generally safe but could cause truncation if the COMMAREA grows across a version boundary | RETURN-TO-CICS (line 590) |
| 40 | JCL loop exits on SPACES/LOW-VALUES as well as /*EOF | `JCL-RECORD = SPACES OR LOW-VALUES` inside the PERFORM VARYING loop | Sets END-LOOP-YES and still calls WIRTE-JOBSUB-TDQ, writing the empty/null record to the TDQ before loop terminates -- this is in addition to the documented `/*EOF` sentinel exit | SUBMIT-JOB-TO-INTRDR (line 502-507) |

## Calculations

| Calculation                             | Formula / Logic                                                                                                                                                                                                        | Input Fields                                               | Output Field            | Source Location |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ----------------------- | --------------- |
| Monthly report -- start date derivation | Start date = first day of current month: `WS-CURDATE-YEAR / WS-CURDATE-MONTH / '01'`                                                                                                                                  | `WS-CURDATE-YEAR`, `WS-CURDATE-MONTH`                     | `WS-START-DATE` (YYYY-MM-DD) | PROCESS-ENTER-KEY (line 217-220) |
| Monthly report -- end date derivation   | End date = last day of current month. Logic: set day=1, increment month by 1 (roll year if month > 12), then `COMPUTE WS-CURDATE-N = FUNCTION DATE-OF-INTEGER(FUNCTION INTEGER-OF-DATE(WS-CURDATE-N) - 1)` to get the day before the first of the next month | `WS-CURDATE-YEAR`, `WS-CURDATE-MONTH` (incremented)       | `WS-END-DATE` (YYYY-MM-DD)   | PROCESS-ENTER-KEY (line 223-236) |
| Yearly report -- start date derivation  | Start date = `<current-year>-01-01` (fixed first day of year)                                                                                                                                                         | `WS-CURDATE-YEAR`                                          | `WS-START-DATE`         | PROCESS-ENTER-KEY (line 243-247) |
| Yearly report -- end date derivation    | End date = `<current-year>-12-31` (fixed last day of year)                                                                                                                                                            | `WS-CURDATE-YEAR`                                          | `WS-END-DATE`           | PROCESS-ENTER-KEY (line 250-252) |
| Custom date -- NUMVAL-C normalisation   | Each of the six date components (SDTMM, SDTDD, SDTYYYY, EDTMM, EDTDD, EDTYYYY) is converted from character to numeric via `FUNCTION NUMVAL-C(field)` and moved back to the input field before range validation. Month/day use WS-NUM-99 (PIC 99), year uses WS-NUM-9999 (PIC 9999) | Screen input fields (character)                            | Same fields (normalised to numeric) | PROCESS-ENTER-KEY (line 305-327) |

## Error Handling

| Condition                                                    | Action                                                                                               | Return Code / Flag | Source Location |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- | ------------------ | --------------- |
| CICS WRITEQ TD to JOBS TDQ fails (non-NORMAL response)      | DISPLAY `'RESP:'` + WS-RESP-CD + `'REAS:'` + WS-REAS-CD, set ERR-FLG-ON, message `'Unable to Write TDQ (JOBS)...'`, cursor on MONTHLY, redisplay | `WS-RESP-CD` / `WS-REAS-CD` | WIRTE-JOBSUB-TDQ (line 525-534) |
| CSUTLDTC start-date validation failure (non-zero severity, not msg 2513) | Set ERR-FLG-ON, message `'Start Date - Not a valid date...'`, cursor on SDTMM, redisplay          | `CSUTLDTC-RESULT-SEV-CD` | PROCESS-ENTER-KEY (line 396-405) |
| CSUTLDTC end-date validation failure (non-zero severity, not msg 2513)   | Set ERR-FLG-ON, message `'End Date - Not a valid date...'`, cursor on EDTMM, redisplay            | `CSUTLDTC-RESULT-SEV-CD` | PROCESS-ENTER-KEY (line 416-425) |
| Any custom date component empty (6 individual checks)       | Set ERR-FLG-ON, field-specific message (see rules 11-16), cursor on offending field, redisplay      | `WS-ERR-FLG = 'Y'` | PROCESS-ENTER-KEY (line 259-300) |
| Any custom date component out of range (6 individual checks) | Set ERR-FLG-ON, field-specific message (see rules 17-22), cursor on offending field, redisplay     | `WS-ERR-FLG = 'Y'` | PROCESS-ENTER-KEY (line 329-379) |
| Confirmation field empty                                     | Set ERR-FLG-ON, message `'Please confirm to print the <report-name> report...'`, cursor on CONFIRM, redisplay | `WS-ERR-FLG = 'Y'` | SUBMIT-JOB-TO-INTRDR (line 464-473) |
| Confirmation field invalid value                             | Set ERR-FLG-ON, message `'"<value>" is not a valid value to confirm...'`, cursor on CONFIRM, redisplay | `WS-ERR-FLG = 'Y'` | SUBMIT-JOB-TO-INTRDR (line 484-493) |
| Invalid AID key pressed                                      | Set ERR-FLG-ON, move `CCDA-MSG-INVALID-KEY` to WS-MESSAGE, cursor on MONTHLY, redisplay            | `WS-ERR-FLG = 'Y'` | MAIN-PARA (line 190-194) |
| CICS RECEIVE failure (no RESP check)                         | RESP/RESP2 captured but never evaluated -- any CICS error during screen receive is silently ignored | (none checked)     | RECEIVE-TRNRPT-SCREEN (line 596-604) |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. MAIN-PARA -- entry point; initialise ERR-FLG-OFF, TRANSACT-NOT-EOF, SEND-ERASE-YES flags; check EIBCALEN and COMMAREA re-entry state
2. RETURN-TO-PREV-SCREEN -- called when EIBCALEN=0; sets CDEMO-FROM-TRANID/CDEMO-FROM-PROGRAM/CDEMO-PGM-CONTEXT in COMMAREA then XCTL to COSGN00C (or target program set in COMMAREA)
3. SEND-TRNRPT-SCREEN -- called on first entry; displays blank CORPT0A map with ERASE; ends with GO TO RETURN-TO-CICS
4. RECEIVE-TRNRPT-SCREEN -- called on re-entry; receives CORPT0AI from CICS (RESP not checked)
5. PROCESS-ENTER-KEY -- called when DFHENTER pressed; evaluates which report type radio button is set
6. SUBMIT-JOB-TO-INTRDR -- called from PROCESS-ENTER-KEY after date range is established; checks CONFIRM field before writing JCL
7. WIRTE-JOBSUB-TDQ -- called in a PERFORM VARYING loop (WS-IDX 1 to 1000) from SUBMIT-JOB-TO-INTRDR; loop exits when `WS-IDX > 1000`, `END-LOOP-YES`, or `ERR-FLG-ON`; END-LOOP-YES is set when the current JCL record is `/*EOF`, SPACES, or LOW-VALUES -- in all three cases WIRTE-JOBSUB-TDQ is still called for that final iteration, meaning the sentinel or empty record is written to the TDQ before the loop terminates
8. CALL 'CSUTLDTC' -- called twice (once for start date, once for end date) in the Custom report path; passes CSUTLDTC-DATE (10 chars), CSUTLDTC-DATE-FORMAT (`'YYYY-MM-DD'`), and CSUTLDTC-RESULT (80-char result area with SEV-CD and MSG-NUM)
9. SEND-TRNRPT-SCREEN -- called after any error or after successful submission; always uses GO TO RETURN-TO-CICS to exit (never falls through)
10. RETURN-TO-PREV-SCREEN -- called when PF3 pressed; XCTL to COMEN01C
11. POPULATE-HEADER-INFO -- called by SEND-TRNRPT-SCREEN; populates title, transaction ID, program name, date, and time in the screen output map
12. INITIALIZE-ALL-FIELDS -- called on successful submission or confirmation=N; INITIALIZE on all 10 input fields (MONTHLY, YEARLY, CUSTOM, SDTMM, SDTDD, SDTYYYY, EDTMM, EDTDD, EDTYYYY, CONFIRM) plus WS-MESSAGE; cursor reset to MONTHLY
13. RETURN-TO-CICS -- reached via GO TO from SEND-TRNRPT-SCREEN; issues `EXEC CICS RETURN TRANSID(CR00) COMMAREA(CARDDEMO-COMMAREA)` (without LENGTH clause -- see rule 39) to maintain pseudo-conversational state
14. MAIN-PARA (fall-through) -- if no GO TO was taken, `EXEC CICS RETURN TRANSID(CR00) COMMAREA(CARDDEMO-COMMAREA)` at lines 199-202 also returns control to CICS

### JCL Structure Written to JOBS TDQ

The program embeds a complete JCL stream in WORKING-STORAGE (JOB-DATA, lines 81-127) that is written record-by-record to the JOBS TDQ. The structure is a table of 80-byte records accessed as `JOB-LINES OCCURS 1000 TIMES` via REDEFINES. Key JCL content:

- Job card: `//TRNRPT00 JOB 'TRAN REPORT',CLASS=A,MSGCLASS=0`
- Notification: `// NOTIFY=&SYSUID`
- Procedure library: `//JOBLIB JCLLIB ORDER=('AWS.M2.CARDDEMO.PROC')`
- Step: `//STEP10 EXEC PROC=TRANREPT`
- SYMNAMES DD (`//STEP05R.SYMNAMES DD *`) that defines SORT fields: `TRAN-CARD-NUM,263,16,ZD` and `TRAN-PROC-DT,305,10,CH`
- PARM-START-DATE and PARM-END-DATE injected into SYMNAMES as `PARM-START-DATE,C'<date>'` and `PARM-END-DATE,C'<date>'` via FILLER-1 / FILLER-2 overlays
- `/*` inline-data-end delimiter closes the SYMNAMES DD inline stream (line 113-114)
- DATEPARM DD (`//STEP10R.DATEPARM DD *`) with start and end date on a single record via FILLER-3 overlay: `<start-date> <end-date>`
- `/*` inline-data-end delimiter closes the DATEPARM DD inline stream (line 122-123)
- Loop terminates at `/*EOF` sentinel record (line 125), or earlier if a SPACES/LOW-VALUES record is encountered; in both cases the final record is written to the TDQ before the loop exits
