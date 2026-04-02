---
type: business-rules
program: INQACC
program_type: online
status: draft
confidence: high
last_pass: 4
calls: []
called_by:
- BNK1DAC
- BNK1UAC
uses_copybooks:
- ABNDINFO
- ACCDB2
- ACCOUNT
- INQACC
- SORTCODE
reads: []
writes: []
db_tables:
- ACCOUNT
transactions: []
mq_queues: []
---

# INQACC -- Business Rules

## Program Purpose

INQACC is an online CICS program that retrieves a single account record from
the DB2 ACCOUNT table. It accepts an account number and sort code via the
COMMAREA (INQACC-COMMAREA), looks up the matching row, and returns all account
fields to the caller. Two lookup modes are supported: standard lookup by
account number using a DB2 cursor (ACC-CURSOR), and a special "last account"
lookup that returns the highest-numbered account for the branch sort code. On
success INQACC-SUCCESS is set to 'Y'; on not-found it is set to 'N'. Any DB2
or VSAM error causes an immediate CICS ABEND with a diagnostic record written
via ABNDPROC.

The hard-coded sort code value is 987654, sourced from the SORTCODE copybook.

## Input / Output

| Direction | Resource      | Type | Description                                                                  |
| --------- | ------------- | ---- | ---------------------------------------------------------------------------- |
| IN        | DFHCOMMAREA   | CICS | INQACC-COMMAREA: INQACC-ACCNO (PIC 9(8)), sort code defaulted to 987654      |
| OUT       | DFHCOMMAREA   | CICS | All ACCOUNT fields plus INQACC-SUCCESS flag ('Y' found / 'N' not found)      |
| IN/OUT    | ACCOUNT (DB2) | DB2  | SELECT by ACCOUNT_SORTCODE + ACCOUNT_NUMBER via ACC-CURSOR (standard path)   |
| IN/OUT    | ACCOUNT (DB2) | DB2  | SELECT ORDER BY ACCOUNT_NUMBER DESC FETCH FIRST 1 ROW (last-account path)   |

## Business Rules

### Routing: Account Lookup Mode Selection

| #  | Rule                            | Condition                   | Action                                                                                      | Source Location |
| -- | ------------------------------- | --------------------------- | ------------------------------------------------------------------------------------------- | --------------- |
| 1  | Special "last account" sentinel | INQACC-ACCNO = 99999999     | PERFORM READ-ACCOUNT-LAST (returns highest-numbered account for the branch)                 | A010 line 218   |
| 2  | Normal account lookup           | INQACC-ACCNO NOT = 99999999 | PERFORM READ-ACCOUNT-DB2 (cursor lookup by sortcode + account number)                       | A010 line 221   |

### Validation: Account Found Check

| #  | Rule                          | Condition                                       | Action                                                                                 | Source Location |
| -- | ----------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------- | --------------- |
| 3  | Account not found / no data   | ACCOUNT-TYPE = SPACES OR LOW-VALUES after fetch | Move 'N' to INQACC-SUCCESS; do NOT populate output fields                              | A010 line 229   |
| 4  | Account found                 | ACCOUNT-TYPE NOT = SPACES AND NOT LOW-VALUES    | Move all 12 account fields to INQACC-COMMAREA; move 'Y' to INQACC-SUCCESS             | A010 line 231   |

### Data Retrieval: Standard DB2 Cursor Path (READ-ACCOUNT-DB2)

| #  | Rule                                            | Condition                                                                            | Action                                                                                    | Source Location      |
| -- | ----------------------------------------------- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- | -------------------- |
| 5  | Sort code applied to cursor                     | Always                                                                               | MOVE SORTCODE (987654) to HV-ACCOUNT-SORTCODE before opening cursor                       | RAD010 line 265      |
| 6  | Account number applied to cursor                | Always                                                                               | MOVE INQACC-ACCNO to HV-ACCOUNT-ACC-NO before opening cursor                              | RAD010 line 263      |
| 7  | DB2 cursor selects by sortcode + account number | ACCOUNT_SORTCODE = :HV-ACCOUNT-SORTCODE AND ACCOUNT_NUMBER = :HV-ACCOUNT-ACC-NO     | Retrieve all 12 account columns FOR FETCH ONLY                                            | ACC-CURSOR decl lines 66-85 |
| 8  | CURSOR OPEN failure is fatal                    | SQLCODE NOT = 0 after OPEN                                                           | PERFORM CHECK-FOR-STORM-DRAIN-DB2, then LINK ABNDPROC, then EXEC CICS ABEND ABCODE('HRAC') CANCEL NODUMP | RAD010 lines 273-339 |
| 9  | CURSOR CLOSE failure is fatal                   | SQLCODE NOT = 0 after CLOSE                                                          | PERFORM CHECK-FOR-STORM-DRAIN-DB2, then LINK ABNDPROC, then EXEC CICS ABEND ABCODE('HRAC') CANCEL NODUMP | RAD010 lines 353-420 |

### Data Retrieval: FETCH-DATA (sub-paragraph of standard path)

| #  | Rule                                  | Condition                    | Action                                                                                                    | Source Location     |
| -- | ------------------------------------- | ---------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------- |
| 10 | No row returned (not found)           | SQLCODE = +100 after FETCH   | INITIALIZE OUTPUT-DATA, set ACCOUNT-SORT-CODE and ACCOUNT-NUMBER, GO TO FD999 (exit without populating)  | FD010 lines 450-458 |
| 11 | FETCH error: check storm drain first  | SQLCODE NOT = 0 after FETCH  | PERFORM CHECK-FOR-STORM-DRAIN-DB2 (sets STORM-DRAIN-CONDITION), then LINK ABNDPROC, EXEC CICS ABEND ABCODE('HRAC') CANCEL NODUMP | FD010 lines 460-528 |
| 12 | Row found: DB2 date reformatting      | SQLCODE = 0 after FETCH      | DB2 date strings (YYYY-MM-DD) are broken into day/month/year subfields via DB2-DATE-REFORMAT redefinition for OPENED, LAST-STMT, and NEXT-STMT dates | FD010 lines 534-572 |

### Data Retrieval: Last-Account Path (GET-LAST-ACCOUNT-DB2)

| #  | Rule                                                       | Condition                                   | Action                                                                                                                     | Source Location        |
| -- | ---------------------------------------------------------- | ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| 13 | Last account query filters only by sort code               | Always (called when INQACC-ACCNO=99999999)  | SELECT all 12 columns FROM ACCOUNT WHERE ACCOUNT_SORTCODE = :HV-ACCOUNT-SORTCODE ORDER BY ACCOUNT_NUMBER DESC FETCH FIRST 1 ROWS ONLY | GLAD010 lines 843-872  |
| 14 | Last account DB2 non-zero SQLCODE failure is fatal         | SQLCODE NOT = 0 after SELECT                | LINK ABNDPROC with message 'GLAD010 -ACCOUNT NCS [NCS-ACC-NO-NAME] CANNOT be accessed and DB2 SELECT failed. SQLCODE=...', then EXEC CICS ABEND ABCODE('HNCS') CANCEL NODUMP. Unlike FD010 and RAD010 error paths, GLAD010 does NOT call CHECK-FOR-STORM-DRAIN-DB2 before aborting. | GLAD010 lines 874-936  |
| 15 | Last account SQLCODE = +100 (no row) treated as success    | SQLCODE = +100 after singleton SELECT       | Falls into the ELSE branch of `IF SQLCODE IS NOT EQUAL TO ZERO`: OUTPUT-DATA was INITIALIZED at GLAD010 start and remains all zeros/spaces. ACCOUNT-TYPE = SPACES, so the caller (A010) will set INQACC-SUCCESS='N'. No explicit not-found handling exists in this path. | GLAD010 lines 937-981  |
| 16 | Last account found: same field mapping                     | SQLCODE = 0 after SELECT                    | Populate all 12 OUTPUT-DATA subfields including date reformatting (same logic as FETCH-DATA)                               | GLAD010 lines 937-980  |
| 17 | NCS-ACC-NO-VALUE populated after last-account              | Always (after GET-LAST-ACCOUNT-DB2 returns) | MOVE REQUIRED-ACC-NUMBER2 TO NCS-ACC-NO-VALUE. REQUIRED-ACC-NUMBER2 is initialized to VALUE 0 and is never set to the retrieved account number, so NCS-ACC-NO-VALUE always receives 0. The actual returned account number is in HV-ACCOUNT-ACC-NO. This appears to be a coding defect -- NCS-ACC-NO-VALUE is not used subsequently in this program. | RAN010 line 831        |

### Storm Drain: DB2 Workload Circuit-Breaker Check

| #  | Rule                                       | Condition              | Action                                                                                      | Source Location         |
| -- | ------------------------------------------ | ---------------------- | ------------------------------------------------------------------------------------------- | ----------------------- |
| 18 | DB2 SQLCODE 923 triggers Storm Drain flag  | SQLCODE = 923          | MOVE 'DB2 Connection lost ' TO STORM-DRAIN-CONDITION; DISPLAY diagnostic message             | CFSDCD010 lines 606-619 |
| 19 | Any other SQLCODE is not Storm Drain       | WHEN OTHER             | MOVE 'Not Storm Drain     ' TO STORM-DRAIN-CONDITION; processing continues                  | CFSDCD010 lines 609-610 |
| 20 | Storm drain check called from three error paths | SQLCODE NOT = 0 on OPEN, FETCH, or CLOSE | CHECK-FOR-STORM-DRAIN-DB2 is PERFORMed from: (a) RAD010 OPEN error (line 333), (b) FD010 FETCH error (line 466), (c) RAD010 CLOSE error (line 413). It is NOT called from the GLAD010 last-account SELECT error path. | RAD010 lines 333, 413; FD010 line 466 |

### ABEND Handling (ABEND-HANDLING -- CICS HANDLE ABEND target)

| #  | Rule                                              | Condition                                                         | Action                                                                                                                          | Source Location     |
| -- | ------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| 21 | DB2 deadlock abend logged with full diagnostics   | MY-ABEND-CODE = 'AD2Z'                                            | DISPLAY SQLCODE, SQLSTATE, SQLERRMC (substring to SQLERRML length), SQLERRD(1-6); falls through to storm-drain=N re-abend path  | AH010 lines 651-665 |
| 22 | VSAM RLS abend AFCR handled as Storm Drain        | MY-ABEND-CODE = 'AFCR'                                            | Falls through to AFCT logic (shared WHEN -- no code between AFCR and AFCS)                                                      | AH010 line 672      |
| 23 | VSAM RLS abend AFCS handled as Storm Drain        | MY-ABEND-CODE = 'AFCS'                                            | Falls through to AFCT logic (shared WHEN -- no code between AFCS and AFCT)                                                      | AH010 line 674      |
| 24 | VSAM RLS abend AFCT: Storm Drain rollback         | MY-ABEND-CODE = 'AFCT' (also covers AFCR, AFCS)                  | SET WS-STORM-DRAIN='Y', DISPLAY diagnostic, EXEC CICS SYNCPOINT ROLLBACK, MOVE 'N' to INQACC-SUCCESS, EXEC CICS RETURN (graceful exit -- does NOT re-abend) | AH010 lines 676-759 |
| 25 | SYNCPOINT ROLLBACK failure within VSAM RLS path   | WS-CICS-RESP NOT = DFHRESP(NORMAL) after SYNCPOINT ROLLBACK       | LINK ABNDPROC with message 'AH010 -Unable to perform SYNCPOINT ROLLBACK. Possible integrity issue following VSAM RLS abend.', then EXEC CICS ABEND ABCODE('HROL') NODUMP CANCEL | AH010 lines 687-753 |
| 26 | All other abends (including AD2Z) re-abend        | WS-STORM-DRAIN = 'N' after EVALUATE (covers AD2Z and any unknown codes) | LINK ABNDPROC with freeform 'AH010 -WVS-STORM-DRAIN=N ...', then EXEC CICS ABEND ABCODE(MY-ABEND-CODE) NODUMP CANCEL       | AH010 lines 763-818 |

## Calculations

| Calculation         | Formula / Logic                                                                                                                                                          | Input Fields                                                                               | Output Field                                                                                  | Source Location                            |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- | ------------------------------------------ |
| DB2 date decompose  | DB2 stores dates as YYYY-MM-DD (PIC X(10)); DB2-DATE-REFORMAT redefines overlaid field: YR=positions 1-4, separator=5, MNTH=6-7, separator=8, DAY=9-10. Used for all three date fields. | HV-ACCOUNT-OPENED / HV-ACCOUNT-LAST-STMT / HV-ACCOUNT-NEXT-STMT (PIC X(10))               | ACCOUNT-OPENED-DAY/MONTH/YEAR, ACCOUNT-LAST-STMT-DAY/MONTH/YEAR, ACCOUNT-NEXT-STMT-DAY/MONTH/YEAR | FD010 lines 546-572; GLAD010 lines 953-975 |
| Abend time format   | CICS FORMATTIME with DDMMYYYY and TIME separators (DATESEP). ABND-TIME STRING built as HH:MM:MM -- WS-TIME-NOW-GRP-MM is used for both the minutes and seconds positions (WS-TIME-NOW-GRP-SS is never referenced). This is a copy-paste defect repeated in 5 distinct STRING blocks. | WS-U-TIME (ABSTIME from CICS ASKTIME)                                                      | ABND-DATE (WS-ORIG-DATE), ABND-TIME (in ABNDINFO-REC)                                        | PTD010 lines 988-999; ABND strings at lines 296-302, 376-382, 491-497, 710-716, 785-791, 898-904 |

## Error Handling

| Condition                                       | Action                                                                                                        | Return Code / Abend | Source Location         |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------- | ----------------------- |
| SQLCODE NOT = 0 on OPEN ACC-CURSOR              | INITIALIZE ABNDINFO-REC, populate diagnostics, PERFORM CHECK-FOR-STORM-DRAIN-DB2, LINK ABNDPROC (WS-ABEND-PGM='ABNDPROC'), EXEC CICS ABEND ABCODE('HRAC') CANCEL NODUMP | HRAC                | RAD010 lines 273-339    |
| SQLCODE NOT = 0 on CLOSE ACC-CURSOR             | Same ABNDINFO pattern, PERFORM CHECK-FOR-STORM-DRAIN-DB2, LINK ABNDPROC, EXEC CICS ABEND ABCODE('HRAC') CANCEL NODUMP | HRAC                | RAD010 lines 353-420    |
| SQLCODE = +100 on FETCH (not found)             | INITIALIZE OUTPUT-DATA, preserve sortcode + accno, GO TO FD999 (no abend)                                     | none (not found)    | FD010 lines 450-458     |
| SQLCODE NOT = 0 on FETCH (DB2 error)            | PERFORM CHECK-FOR-STORM-DRAIN-DB2, LINK ABNDPROC, EXEC CICS ABEND ABCODE('HRAC') CANCEL NODUMP                | HRAC                | FD010 lines 460-528     |
| SQLCODE NOT = 0 on last-account SELECT          | LINK ABNDPROC with message 'GLAD010 -ACCOUNT NCS [NCS-ACC-NO-NAME] CANNOT be accessed and DB2 SELECT failed', EXEC CICS ABEND ABCODE('HNCS') CANCEL NODUMP. No storm-drain check performed. | HNCS                | GLAD010 lines 874-936   |
| SQLCODE = +100 on last-account SELECT           | No explicit handling: ELSE branch maps initialized OUTPUT-DATA to commarea; ACCOUNT-TYPE=SPACES causes A010 to set INQACC-SUCCESS='N' | none (silent not-found) | GLAD010 lines 937-981 |
| CICS ABEND code = 'AD2Z' (DB2 deadlock)         | DISPLAY SQLSTATE and full SQLERRD detail; falls through to WS-STORM-DRAIN='N' path which re-issues abend       | AD2Z (re-issued)    | AH010 lines 651-665     |
| CICS ABEND code = 'AFCR'/'AFCS'/'AFCT' (VSAM RLS) | SYNCPOINT ROLLBACK, MOVE 'N' to INQACC-SUCCESS, EXEC CICS RETURN (graceful)                                | none (returned)     | AH010 lines 672-759     |
| SYNCPOINT ROLLBACK fails in VSAM RLS path       | LINK ABNDPROC with message 'AH010 -Unable to perform SYNCPOINT ROLLBACK...', EXEC CICS ABEND ABCODE('HROL') NODUMP CANCEL | HROL                | AH010 lines 687-753     |
| Any other CICS ABEND (WS-STORM-DRAIN='N')       | LINK ABNDPROC with freeform 'AH010 -WVS-STORM-DRAIN=N...', EXEC CICS ABEND ABCODE(MY-ABEND-CODE) NODUMP CANCEL | Original code       | AH010 lines 763-818     |
| SQLCODE = 923 detected in CHECK-FOR-STORM-DRAIN-DB2 | DISPLAY 'INQACC: Check-For-Storm-Drain-DB2: Storm Drain condition ... has been met'; diagnostic only, caller still abends | diagnostic only     | CFSDCD010 lines 617-619 |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. A010 (PREMIERE SECTION) -- Entry point. INITIALIZE OUTPUT-DATA. Register HANDLE ABEND to ABEND-HANDLING. MOVE SORTCODE (987654) to REQUIRED-SORT-CODE OF ACCOUNT-KY.
2. A010 routing -- IF INQACC-ACCNO = 99999999 THEN PERFORM READ-ACCOUNT-LAST ELSE PERFORM READ-ACCOUNT-DB2.
3. READ-ACCOUNT-DB2 (RAD010) -- Move host variables (sortcode, accno). OPEN ACC-CURSOR (SQLCODE check: if not zero, PERFORM CHECK-FOR-STORM-DRAIN-DB2 then LINK ABNDPROC then fatal ABEND 'HRAC'). PERFORM FETCH-DATA. CLOSE ACC-CURSOR (same error pattern on non-zero SQLCODE).
4. FETCH-DATA (FD010) -- EXEC SQL FETCH into HOST-ACCOUNT-ROW. Handle SQLCODE +100 (not found -- GO TO FD999) or non-zero error (PERFORM CHECK-FOR-STORM-DRAIN-DB2 then LINK ABNDPROC then fatal abend). On success, map all 12 fields including date decomposition into OUTPUT-DATA.
5. READ-ACCOUNT-LAST (RAN010) -- PERFORM GET-LAST-ACCOUNT-DB2. Then MOVE REQUIRED-ACC-NUMBER2 (always 0) TO NCS-ACC-NO-VALUE.
6. GET-LAST-ACCOUNT-DB2 (GLAD010) -- INITIALIZE OUTPUT-DATA. EXEC SQL SELECT all 12 columns ... ORDER BY ACCOUNT_NUMBER DESC FETCH FIRST 1 ROWS ONLY. On non-zero SQLCODE, LINK ABNDPROC then ABEND 'HNCS' (no storm-drain check). On zero or +100 SQLCODE, map all 12 fields with date decomposition into OUTPUT-DATA (SQLCODE +100 is silently treated as success with zeroed-out data).
7. A010 success check -- IF ACCOUNT-TYPE = SPACES OR LOW-VALUES THEN INQACC-SUCCESS='N' ELSE map OUTPUT-DATA to INQACC-COMMAREA fields and INQACC-SUCCESS='Y'.
8. GET-ME-OUT-OF-HERE (GMOFH010) -- EXEC CICS RETURN then GOBACK.
9. ABEND-HANDLING (AH010) -- CICS HANDLE ABEND target. EXEC CICS ASSIGN ABCODE(MY-ABEND-CODE). EVALUATE MY-ABEND-CODE: 'AD2Z' logs deadlock detail; 'AFCR'/'AFCS'/'AFCT' rollback and return; all others (WS-STORM-DRAIN='N') re-abend with original code.
10. CHECK-FOR-STORM-DRAIN-DB2 (CFSDCD010) -- PERFORMed from RAD010 OPEN error, RAD010 CLOSE error, and FD010 FETCH error paths (not from GLAD010). EVALUATE SQLCODE: 923 sets 'DB2 Connection lost '; other codes set 'Not Storm Drain     '. Displays diagnostic only if storm drain condition met. Does not itself abend; caller handles the abend.
11. POPULATE-TIME-DATE (PTD010) -- Called within abend info capture blocks. EXEC CICS ASKTIME ABSTIME(WS-U-TIME). EXEC CICS FORMATTIME DDMMYYYY(WS-ORIG-DATE) TIME(WS-TIME-NOW) DATESEP. Populates WS-ORIG-DATE (DD/MM/YYYY) and WS-TIME-NOW (HHMMSS) for ABNDINFO-REC.
12. CALL ABNDPROC (via EXEC CICS LINK PROGRAM(WS-ABEND-PGM)) -- Invoked before every CICS ABEND. WS-ABEND-PGM VALUE 'ABNDPROC'. Receives ABNDINFO-REC as COMMAREA.

## Coding Anomalies

| #  | Anomaly                               | Location             | Description                                                                                                                                                                          |
| -- | ------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A1 | ABND-TIME seconds field is wrong      | Lines 296-302, 376-382, 491-497, 710-716, 785-791, 898-904 | WS-TIME-NOW-GRP-MM (minutes) is repeated for the seconds position in the HH:MM:SS STRING; WS-TIME-NOW-GRP-SS is never used. Abend time records always show minutes twice and omit seconds. This defect appears in 5 distinct ABND capture blocks (RAD010 OPEN, RAD010 CLOSE, FD010 FETCH, AH010 VSAM path, AH010 re-abend path, GLAD010). |
| A2 | NCS-ACC-NO-VALUE always set to 0      | RAN010 line 831      | After GET-LAST-ACCOUNT-DB2 returns, `MOVE REQUIRED-ACC-NUMBER2 TO NCS-ACC-NO-VALUE` is executed. REQUIRED-ACC-NUMBER2 is never assigned from the DB2 result; it retains its VALUE 0 initialisation. The retrieved account number resides in HV-ACCOUNT-ACC-NO but is not captured here. NCS-ACC-NO-VALUE is not used subsequently in INQACC. |
| A3 | GLAD010 does not check storm drain    | GLAD010 lines 874-936 | The FETCH error path (FD010) and both RAD010 cursor error paths call PERFORM CHECK-FOR-STORM-DRAIN-DB2 before aborting. The last-account SELECT error path (GLAD010) abends with HNCS immediately without calling CHECK-FOR-STORM-DRAIN-DB2. This asymmetry means SQLCODE 923 is only detected as a storm drain condition on the standard cursor path. |
| A4 | GLAD010 silently ignores SQLCODE +100 | GLAD010 lines 937-981 | The singleton SELECT INTO in GLAD010 returns SQLCODE=+100 if no account row exists. Unlike FD010 which explicitly handles +100 with a GO TO FD999 and preserves account number, GLAD010 has no IF SQLCODE = +100 check. The condition falls into the ELSE branch (SQLCODE=0 path): OUTPUT-DATA remains INITIALIZED (all spaces/zeros). A010 then sees ACCOUNT-TYPE=SPACES and sets INQACC-SUCCESS='N'. The behaviour is ultimately correct but relies on the INITIALIZE at GLAD010 start and the downstream ACCOUNT-TYPE check in A010 rather than explicit handling. |
| A5 | Redundant host variable initialisation in GLAD010 | GLAD010 lines 840-842 | Three setup moves occur before the SELECT: (1) `MOVE REQUIRED-ACC-NUMBER2 TO HV-ACCOUNT-ACC-NO` (line 840) -- HV-ACCOUNT-ACC-NO is not referenced in the SELECT WHERE clause so this move has no effect on query results; (2) `MOVE REQUIRED-SORT-CODE TO HV-ACCOUNT-SORTCODE` (line 841) -- immediately overwritten by (3) `MOVE SORTCODE TO HV-ACCOUNT-SORTCODE` (line 842). The move at line 841 is dead code. Both REQUIRED-ACC-NUMBER2 and REQUIRED-SORT-CODE are VALUE 0 at this point (REQUIRED-SORT-CODE is set from SORTCODE only in the ACCOUNT-KY group, not in ACCOUNT-KY2). The net effect is correct: the SELECT uses SORTCODE (987654) as the filter. |
| A6 | Dead WORKING-STORAGE items            | Lines 91-111, 124-126 | Several WORKING-STORAGE fields declared in the DATA DIVISION are never referenced in the PROCEDURE DIVISION: EXIT-BROWSE-LOOP (PIC X VALUE 'N'), FETCH-DATA-CNT (PIC 9(4) COMP), DB2-EXIT-LOOP (PIC X), WS-CUST-ALT-KEY-LEN (PIC S9(4) COMP VALUE +10), DESIRED-KEY (PIC 9(10) BINARY), and the entire RETURNED-DATA group (01-level at lines 96-109 with 11 subordinate fields). These are likely remnants of a prior VSAM-based implementation that was replaced by the current DB2-only path. |
