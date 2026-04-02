---
type: business-rules
program: BNKMENU
program_type: online
status: draft
confidence: high
last_pass: 5
calls:
- ABNDPROC
called_by: []
uses_copybooks:
- ABNDINFO
- BNK1MAI
- DFHAID
reads: []
writes: []
db_tables: []
transactions:
- OMEN
- ODCS
- ODAC
- OCCS
- OCAC
- OUAC
- OCRA
- OTFN
- OCCA
mq_queues: []
---

# BNKMENU -- Business Rules

## Program Purpose

BNKMENU is the main menu entry point for the CICS Banking Sample Application. It is initiated
under transaction OMEN and presents the BNK1ME BMS map (mapset BNK1MAI) to the terminal user.
The program accepts a single character menu selection (field ACTIONI), validates it, and then
immediately hands control to the appropriate downstream transaction via `EXEC CICS RETURN
TRANSID(...)  IMMEDIATE`. On the first invocation (EIBCALEN = ZERO), the map is displayed with
erased fields. On subsequent invocations the map is received, validated, and dispatched. There is
no database access -- the program is purely a menu router.

## Input / Output

| Direction | Resource           | Type | Description                                                        |
| --------- | ------------------ | ---- | ------------------------------------------------------------------ |
| IN        | BNK1ME (BNK1MAI)   | CICS | BMS map receive -- single ACTION field containing user selection   |
| OUT       | BNK1ME (BNK1MAI)   | CICS | BMS map send (ERASE, DATAONLY, or DATAONLY+ALARM modes)            |
| OUT       | END-OF-SESSION-MESSAGE | CICS | SEND TEXT 'Session Ended' on PF3/PF12 termination            |
| OUT       | ABNDPROC           | CICS | LINK to abend handler with ABNDINFO-REC on any CICS failure        |

## Business Rules

### Key Entry -- Attention Identifier (AID) Routing

| #  | Rule                         | Condition                                     | Action                                                                                                | Source Location |
| -- | ---------------------------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------- | --------------- |
| 1  | First-time display           | `EIBCALEN = ZERO`                             | Move LOW-VALUE to BNK1MEO, set cursor on ACTION field (ACTIONL = -1), send map with ERASE             | A010 line 116   |
| 2  | PA key -- no-op              | `EIBAID = DFHPA1 OR DFHPA2 OR DFHPA3`        | CONTINUE (no action taken; control falls through to EXEC CICS RETURN TRANSID('OMEN'))                 | A010 line 125   |
| 3  | Session termination (PF3/PF12) | `EIBAID = DFHPF3 OR DFHPF12`               | PERFORM SEND-TERMINATION-MSG (displays 'Session Ended'), then EXEC CICS RETURN (no transid -- ends session) | A010 line 131 |
| 4  | Clear key -- erase screen    | `EIBAID = DFHCLEAR`                           | EXEC CICS SEND CONTROL ERASE FREEKB, then EXEC CICS RETURN (no transid -- ends session)               | A010 line 141   |
| 5  | Enter key -- process input   | `EIBAID = DFHENTER`                           | PERFORM PROCESS-MENU-MAP (receive, validate, dispatch)                                                 | A010 line 152   |
| 6  | Invalid AID key              | `WHEN OTHER` (any key not listed above)       | Move 'Invalid key pressed.' to MESSAGEO, set cursor on ACTION (ACTIONL = -1), SEND-DATAONLY-ALARM     | A010 line 158   |

### Menu Option Validation (EDIT-MENU-DATA)

| #  | Rule                            | Condition                                                                                                  | Action                                                                                                              | Source Location |
| -- | ------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | --------------- |
| 7  | ACTION field -- valid values    | `ACTIONI NOT = '1' AND NOT = '2' AND NOT = '3' AND NOT = '4' AND NOT = '5' AND NOT = '6' AND NOT = '7' AND NOT = 'A'` | Move SPACES then 'You must enter a valid value (1-7 or A).' to MESSAGEO; set VALID-DATA-SW = 'N' (88 VALID-DATA is false) | EMD010 line 360 |
| 8  | ACTION field -- accepted        | ACTIONI is one of '1', '2', '3', '4', '5', '6', '7', 'A'                                                 | Move ACTIONI to ACTION-ALPHA; VALID-DATA-SW remains 'Y' (WORKING-STORAGE VALUE 'Y' is re-established each CICS task invocation; EMD010 never explicitly sets it back to 'Y') | EMD010 line 370 |

### Menu Option Dispatch (INVOKE-OTHER-TXNS)

Dispatch only executes when VALID-DATA is true (VALID-DATA-SW = 'Y').

| #  | Rule                                    | Condition          | Action                                                       | Source Location |
| -- | --------------------------------------- | ------------------ | ------------------------------------------------------------ | --------------- |
| 9  | Option 1 -- Display Customer details    | `ACTIONI = '1'`    | EXEC CICS RETURN TRANSID('ODCS') IMMEDIATE                   | IOT010 line 386 |
| 10 | Option 2 -- Display Account details     | `ACTIONI = '2'`    | EXEC CICS RETURN TRANSID('ODAC') IMMEDIATE                   | IOT010 line 458 |
| 11 | Option 3 -- Create a Customer           | `ACTIONI = '3'`    | EXEC CICS RETURN TRANSID('OCCS') IMMEDIATE                   | IOT010 line 531 |
| 12 | Option 4 -- Create an Account           | `ACTIONI = '4'`    | EXEC CICS RETURN TRANSID('OCAC') IMMEDIATE                   | IOT010 line 604 |
| 13 | Option 5 -- Update an Account           | `ACTIONI = '5'`    | EXEC CICS RETURN TRANSID('OUAC') IMMEDIATE                   | IOT010 line 677 |
| 14 | Option 6 -- Credit/Debit funds          | `ACTIONI = '6'`    | EXEC CICS RETURN TRANSID('OCRA') IMMEDIATE                   | IOT010 line 750 |
| 15 | Option 7 -- Transfer funds              | `ACTIONI = '7'`    | EXEC CICS RETURN TRANSID('OTFN') IMMEDIATE                   | IOT010 line 823 |
| 16 | Option A -- Look up Accounts by Customer| `ACTIONI = 'A'`    | EXEC CICS RETURN TRANSID('OCCA') IMMEDIATE                   | IOT010 line 897 |

### Map Receive Error Handling (RECEIVE-MENU-MAP)

| #  | Rule                                    | Condition                                          | Action                                                                                       | Source Location |
| -- | --------------------------------------- | -------------------------------------------------- | -------------------------------------------------------------------------------------------- | --------------- |
| 17 | MAPFAIL on receive -- benign empty map  | `WS-CICS-RESP = DFHRESP(MAPFAIL)`                 | Move LOW-VALUES to BNK1MEO, set cursor on ACTION, SEND-ERASE (redisplay empty map); no abend | RMM010 line 284 |
| 18 | Other CICS error on receive             | `WS-CICS-RESP NOT = DFHRESP(NORMAL)` and not MAPFAIL | Build ABNDINFO-REC, LINK to ABNDPROC, then PERFORM ABEND-THIS-TASK (ABEND code 'HBNK')    | RMM010 line 297 |

### Send-Map Modes (SEND-MAP)

| #  | Rule                            | Condition                 | Action                                                                                          | Source Location  |
| -- | ------------------------------- | ------------------------- | ----------------------------------------------------------------------------------------------- | ---------------- |
| 19 | Send with full erase            | `88 SEND-ERASE` (value '1') | EXEC CICS SEND MAP BNK1ME FROM BNK1MEO ERASE FREEKB; GO TO SMM999 on success                 | SMM010 line 978  |
| 20 | Send data only (no erase)       | `88 SEND-DATAONLY` (value '2') | EXEC CICS SEND MAP BNK1ME FROM BNK1MEO DATAONLY FREEKB; GO TO SMM999 on success          | SMM010 line 1053 |
| 21 | Send data with alarm (error)    | `88 SEND-DATAONLY-ALARM` (value '3') | EXEC CICS SEND MAP BNK1ME FROM BNK1MEO DATAONLY ALARM FREEKB                      | SMM010 line 1130 |

### Post-Dispatch Loop Back

| #  | Rule                                        | Condition                                           | Action                                                                                                           | Source Location |
| -- | ------------------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | --------------- |
| 22 | Re-display menu after failed validation     | VALID-DATA is false after EDIT-MENU-DATA            | INVOKE-OTHER-TXNS is skipped; SET SEND-DATAONLY-ALARM TO TRUE; PERFORM SEND-MAP (redisplays with error message) | PMM010 line 258 |
| 23 | Pseudo-conversational return under OMEN     | After every path through A010 (except termination) | EXEC CICS RETURN TRANSID('OMEN') COMMAREA(COMMUNICATION-AREA) LENGTH(1) -- keeps session alive under OMEN      | A010 line 170   |

### Note -- Unreachable Code in PMM010

Lines 258-263 in PMM010 (`SET SEND-DATAONLY-ALARM TO TRUE` followed by `PERFORM SEND-MAP`) are
placed unconditionally after `PERFORM INVOKE-OTHER-TXNS`. However, when INVOKE-OTHER-TXNS
successfully issues `EXEC CICS RETURN IMMEDIATE`, the task terminates and these statements are
never reached. They are only reachable when VALID-DATA is false (INVOKE-OTHER-TXNS is not
PERFORMed). In practice this works correctly, but the unconditional placement could mislead
readers into thinking the map is always resent after dispatch.

### Note -- MAPFAIL Fall-Through into Validation (UX Defect)

When MAPFAIL occurs in RMM010, the code performs SEND-MAP (SEND-ERASE) and then returns normally
to PMM010. PMM010 does NOT exit after RECEIVE-MENU-MAP returns -- it proceeds unconditionally to
PERFORM EDIT-MENU-DATA (line 248) and then to PERFORM INVOKE-OTHER-TXNS if VALID-DATA is true.
Because the CICS RECEIVE MAP failed, BNK1MEI was not populated, so ACTIONI contains LOW-VALUES.
EDIT-MENU-DATA evaluates ACTIONI against '1'-'7' and 'A'; LOW-VALUES matches none of these, so
VALID-DATA-SW is set to 'N' and the message 'You must enter a valid value (1-7 or A).' is moved
to MESSAGEO. PMM010 then calls SET SEND-DATAONLY-ALARM TO TRUE and PERFORM SEND-MAP a second
time, overwriting the blank map just sent with an alarm map showing a spurious validation error.
The user sees 'You must enter a valid value (1-7 or A).' instead of a clean blank menu on
MAPFAIL. This is a UX defect caused by the absence of an early exit from PMM010 after RMM010
handles MAPFAIL. Source: RMM010 lines 284-288, PMM010 lines 246-263.

## Calculations

| Calculation    | Formula / Logic                                                                                        | Input Fields                                             | Output Field | Source Location |
| -------------- | ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------- | ------------ | --------------- |
| Time formatting | `EXEC CICS ASKTIME ABSTIME(WS-U-TIME)` then `EXEC CICS FORMATTIME ABSTIME(...) DDMMYYYY(...) TIME(...) DATESEP` | CICS system clock                               | WS-U-TIME, WS-ORIG-DATE (DD/MM/YYYY with separator), WS-TIME-NOW (HHMMSS) | PTD010 line 1302 |
| ABND-TIME build | STRING of HH ':' MM ':' MM (note: seconds field uses MM twice -- appears to be a copy-paste defect)  | WS-TIME-NOW-GRP-HH, WS-TIME-NOW-GRP-MM (used twice)     | ABND-TIME    | A010 line 200, repeated in all error paths |

## Error Handling

| Condition                               | Action                                                                                      | Return Code / ABEND | Source Location              |
| --------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------- | ---------------------------- |
| CICS RETURN TRANSID('OMEN') fails       | Build ABNDINFO-REC (code 'HBNK'); ABND-FREEFORM = 'A010 - RETURN TRANSID(MENU) FAIL.'; LINK to ABNDPROC; PERFORM ABEND-THIS-TASK | HBNK | A010 line 178 |
| CICS RECEIVE MAP fails (not MAPFAIL)    | Build ABNDINFO-REC; ABND-FREEFORM = 'RMM010  - RECEIVE MAP FAIL.'; LINK to ABNDPROC; ABEND-THIS-TASK | HBNK         | RMM010 line 297              |
| CICS RECEIVE MAP MAPFAIL                | Redisplay empty map (SEND-ERASE); not treated as fatal error; see UX defect note above      | none                | RMM010 line 284              |
| CICS SEND MAP ERASE fails               | Build ABNDINFO-REC; ABND-FREEFORM = 'SMM010 - SEND MAP ERASE FAIL.'; LINK to ABNDPROC; ABEND-THIS-TASK | HBNK      | SMM010 line 988              |
| CICS SEND MAP DATAONLY fails            | Build ABNDINFO-REC; ABND-FREEFORM = 'SMM010 - SEND MAP DATAONLY FAIL.'; LINK to ABNDPROC; ABEND-THIS-TASK | HBNK   | SMM010 line 1063             |
| CICS SEND MAP DATAONLY ALARM fails      | Build ABNDINFO-REC; ABND-FREEFORM = 'SMM010 - SEND MAP DATAONLY ALARM FAIL.'; LINK to ABNDPROC; ABEND-THIS-TASK | HBNK | SMM010 line 1141           |
| CICS RETURN TRANSID('ODCS') fails       | Build ABNDINFO-REC; ABND-FREEFORM = 'IOT010 - RETURN TRANSID(ODCS) FAIL.'; LINK to ABNDPROC; ABEND-THIS-TASK | HBNK   | IOT010 line 394              |
| CICS RETURN TRANSID('ODAC') fails       | Build ABNDINFO-REC; ABND-FREEFORM = 'IOT010 - RETURN TRANSID(ODAC) FAIL.'; LINK to ABNDPROC; ABEND-THIS-TASK | HBNK   | IOT010 line 466              |
| CICS RETURN TRANSID('OCCS') fails       | Build ABNDINFO-REC; ABND-FREEFORM = 'IOT010 - RETURN TRANSID(OCCS) FAIL.'; LINK to ABNDPROC; ABEND-THIS-TASK | HBNK   | IOT010 line 539              |
| CICS RETURN TRANSID('OCAC') fails       | Build ABNDINFO-REC; ABND-FREEFORM = 'IOT010 - RETURN TRANSID(OCAC) FAIL.'; LINK to ABNDPROC; ABEND-THIS-TASK | HBNK   | IOT010 line 612              |
| CICS RETURN TRANSID('OUAC') fails       | Build ABNDINFO-REC; ABND-FREEFORM = 'IOT010 - RETURN TRANSID(OUAC) FAIL.'; LINK to ABNDPROC; ABEND-THIS-TASK | HBNK   | IOT010 line 685              |
| CICS RETURN TRANSID('OCRA') fails       | Build ABNDINFO-REC; ABND-FREEFORM = 'IOT010 - RETURN TRANSID(OCRA) FAIL.'; LINK to ABNDPROC; ABEND-THIS-TASK | HBNK   | IOT010 line 758              |
| CICS RETURN TRANSID('OTFN') fails       | Build ABNDINFO-REC; ABND-FREEFORM = 'IOT010 - RETURN TRANSID(OTFN) FAIL.'; LINK to ABNDPROC; ABEND-THIS-TASK | HBNK   | IOT010 line 831              |
| CICS RETURN TRANSID('OCCA') fails       | Build ABNDINFO-REC; ABND-FREEFORM = 'IOT010 - RETURN TRANSID(OCCA) FAIL.'; LINK to ABNDPROC; ABEND-THIS-TASK | HBNK   | IOT010 line 905              |
| CICS SEND TEXT termination fails        | Build ABNDINFO-REC; ABND-FREEFORM = 'STM010 - SEND TEXT FAIL.'; LINK to ABNDPROC; ABEND-THIS-TASK | HBNK          | STM010 line 1221             |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. **A010** (PREMIERE SECTION) -- main entry point; evaluates EIBAID/EIBCALEN to route control
2. **SEND-MAP / SMM010** -- called on first entry (SEND-ERASE) and after invalid AID or failed validation
3. **PROCESS-MENU-MAP / PMM010** -- called when ENTER key pressed; orchestrates receive, validate, dispatch sequence
4. **RECEIVE-MENU-MAP / RMM010** -- EXEC CICS RECEIVE MAP BNK1ME; handles MAPFAIL as benign
5. **EDIT-MENU-DATA / EMD010** -- validates ACTIONI must be '1'-'7' or 'A'; sets VALID-DATA-SW
6. **INVOKE-OTHER-TXNS / IOT010** -- dispatches EXEC CICS RETURN TRANSID(...) IMMEDIATE for each valid option; only reached when VALID-DATA is true
7. **SEND-TERMINATION-MSG / STM010** -- sends 'Session Ended' text on PF3/PF12, then EXEC CICS RETURN (session ends)
8. **ABEND-THIS-TASK / ATT010** -- called from all error paths; DISPLAY WS-FAIL-INFO, then EXEC CICS ABEND ABCODE('HBNK') NODUMP
9. **POPULATE-TIME-DATE / PTD010** -- ASKTIME + FORMATTIME DATESEP to populate date/time fields for ABNDINFO-REC; called from every error path before LINK to ABNDPROC
10. EXEC CICS LINK **ABNDPROC** -- called with COMMAREA(ABNDINFO-REC) from every error path before ABEND-THIS-TASK
11. EXEC CICS RETURN TRANSID('OMEN') -- pseudo-conversational loop-back at the end of A010 (every non-terminating path); LENGTH(1) COMMAREA

### Note -- Defect in ABND-TIME Construction

In every error handling block (A010, RMM010, IOT010, SMM010, STM010), the STRING that builds
ABND-TIME uses `WS-TIME-NOW-GRP-MM` for both the minutes and seconds positions. The seconds
component (`WS-TIME-NOW-GRP-SS`) is never referenced. The ABND-TIME field stored in the abend
record will therefore always show minutes in the seconds position (e.g., HH:MM:MM instead of
HH:MM:SS). Source: line 200-206 (A010), confirmed repeated in RMM010 line 312-318 and all
other error paths.

### Note -- A010 ABND-FREEFORM Message Wording

The ABND-FREEFORM message for the EXEC CICS RETURN TRANSID('OMEN') failure in A010 reads
`'A010 - RETURN TRANSID(MENU) FAIL.'` -- note it says MENU (not OMEN). This is the literal
text embedded at source line 216. The WS-CICS-FAIL-MSG text at line 230 similarly reads
`'BNKMENU - A010 - RETURN TRANSID(MENU) FAIL'`. This wording is potentially confusing since the
actual transid being returned is OMEN, but the label 'MENU' appears to be an informal name for
the transaction.

### Note -- Debug Display Statement in PTD010

Line 1300 contains `D    DISPLAY 'POPULATE-TIME-DATE SECTION'` -- this is a COBOL debug line
(column 7 contains 'D'). It is only active when the WITH DEBUGGING MODE clause is present in
the ENVIRONMENT DIVISION. The program does not declare WITH DEBUGGING MODE (source line 25:
OBJECT-COMPUTER IBM-370 with no debugging clause), so this DISPLAY is inactive in production.
