---
type: business-rules
program: COADM01C
program_type: online
status: draft
confidence: high
last_pass: 5
calls: []
called_by:
- COSGN00C
- COUSR00C
- COUSR01C
- COUSR02C
- COUSR03C
uses_copybooks:
- COADM01
- COADM02Y
- COCOM01Y
- COTTL01Y
- CSDAT01Y
- CSMSG01Y
- CSUSR01Y
reads: []
writes: []
db_tables: []
transactions:
- CA00
mq_queues: []
---

# COADM01C -- Business Rules

## Program Purpose

COADM01C is the Admin Menu program for the CardDemo CICS application, accessible via transaction CA00. It presents a numbered menu of administrative options to admin users. On first entry it sends the menu screen; on re-entry it reads the user's menu selection, validates the option, and transfers control (XCTL) to the chosen sub-program. If a selected program is not installed (PGMIDERR), it catches the condition and displays an informational message rather than abending.

## Input / Output

| Direction | Resource | Type | Description |
| --------- | -------- | ---- | ----------- |
| IN        | COADM1A  | CICS | BMS map receive -- reads user's menu option selection (OPTIONI) |
| OUT       | COADM1A  | CICS | BMS map send -- displays admin menu with options and messages; always issued with ERASE (full-screen clear) |
| IN/OUT    | CARDDEMO-COMMAREA | CICS | COMMAREA passed between screens carrying session state |
| OUT       | (target program) | CICS XCTL | Transfers control to selected admin sub-program; CARDDEMO-COMMAREA passed on dispatch XCTL but NOT on signon redirect XCTL |

## Business Rules

### Entry and Session Initialisation

| #  | Rule                              | Condition                                                    | Action                                                                                                    | Source Location       |
| -- | --------------------------------- | ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- | --------------------- |
| 1  | No COMMAREA -- redirect to signon | `EIBCALEN = 0`                                               | Set `CDEMO-FROM-PROGRAM = 'COSGN00C'`, XCTL to signon screen via RETURN-TO-SIGNON-SCREEN                 | MAIN-PARA (line 86)   |
| 2  | First entry -- send menu          | `EIBCALEN > 0` AND `NOT CDEMO-PGM-REENTER` (context = 0)    | Set `CDEMO-PGM-REENTER` to TRUE (context = 1), clear screen map to LOW-VALUES, PERFORM SEND-MENU-SCREEN  | MAIN-PARA (lines 91-94) |
| 3  | Re-entry -- receive and dispatch  | `EIBCALEN > 0` AND `CDEMO-PGM-REENTER` (context = 1)        | PERFORM RECEIVE-MENU-SCREEN, then EVALUATE EIBAID for key routing                                        | MAIN-PARA (lines 96-107) |

### Key Routing (AID Key Dispatch)

| #  | Rule                       | Condition             | Action                                                                                             | Source Location         |
| -- | -------------------------- | --------------------- | -------------------------------------------------------------------------------------------------- | ----------------------- |
| 4  | Enter key -- process input | `EIBAID = DFHENTER`   | PERFORM PROCESS-ENTER-KEY                                                                          | MAIN-PARA (lines 98-99) |
| 5  | PF3 -- return to signon    | `EIBAID = DFHPF3`     | Move `'COSGN00C'` to `CDEMO-TO-PROGRAM`, PERFORM RETURN-TO-SIGNON-SCREEN                         | MAIN-PARA (lines 100-102) |
| 6  | Any other key -- error     | `EIBAID = WHEN OTHER` | Set `WS-ERR-FLG = 'Y'`, move `CCDA-MSG-INVALID-KEY` to `WS-MESSAGE`, PERFORM SEND-MENU-SCREEN    | MAIN-PARA (lines 103-106) |

### Menu Option Validation

| #  | Rule                                      | Condition                                                                                          | Action                                                                                                  | Source Location              |
| -- | ----------------------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------- |
| 7  | Option must be numeric                    | `WS-OPTION IS NOT NUMERIC`                                                                         | Set `WS-ERR-FLG = 'Y'`, display message `'Please enter a valid option number...'`, re-send menu screen | PROCESS-ENTER-KEY (line 131) |
| 8  | Option must not exceed menu count         | `WS-OPTION > CDEMO-ADMIN-OPT-COUNT` (currently 6)                                                 | Set `WS-ERR-FLG = 'Y'`, display message `'Please enter a valid option number...'`, re-send menu screen | PROCESS-ENTER-KEY (line 132) |
| 9  | Option must not be zero                   | `WS-OPTION = ZEROS`                                                                                | Set `WS-ERR-FLG = 'Y'`, display message `'Please enter a valid option number...'`, re-send menu screen | PROCESS-ENTER-KEY (line 133) |
| 10 | Option normalisation -- leading spaces    | Input field `OPTIONI` is right-justified; scan from right to find last non-space, extract, then INSPECT to replace remaining spaces with `'0'` before numeric coercion | WS-OPTION-X is set to right-trimmed, zero-padded option string; WS-OPTION receives numeric value        | PROCESS-ENTER-KEY (lines 121-128) |

### Menu Option Dispatch

| #  | Rule                                    | Condition                                                                                               | Action                                                                                              | Source Location              |
| -- | --------------------------------------- | ------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------- |
| 11 | Transfer to installed program           | `NOT ERR-FLG-ON` AND `CDEMO-ADMIN-OPT-PGMNAME(WS-OPTION)(1:5) NOT = 'DUMMY'`                          | Set `CDEMO-FROM-TRANID = WS-TRANID ('CA00')`, `CDEMO-FROM-PROGRAM = 'COADM01C'`, reset `CDEMO-PGM-CONTEXT = 0`, EXEC CICS XCTL to selected program passing CARDDEMO-COMMAREA | PROCESS-ENTER-KEY (lines 140-148) |
| 12 | Option not installed (program = DUMMY)  | `NOT ERR-FLG-ON` AND `CDEMO-ADMIN-OPT-PGMNAME(WS-OPTION)(1:5) = 'DUMMY'`                              | Build message `'This option is not installed ...'` in green (DFHGREEN) and re-send menu screen; note: option name is commented out of the STRING statement so the message is generic | PROCESS-ENTER-KEY (lines 150-157) |
| 13 | Signon redirect -- no COMMAREA          | `CDEMO-TO-PROGRAM = LOW-VALUES OR SPACES` at time of RETURN-TO-SIGNON-SCREEN                           | Defaulted to `'COSGN00C'` before XCTL; XCTL is issued WITHOUT a COMMAREA clause -- the session state is not forwarded to signon | RETURN-TO-SIGNON-SCREEN (lines 163-170) |

### Admin Menu Option Table (from COADM02Y)

| #  | Rule                              | Condition                  | Action                                        | Source Location        |
| -- | --------------------------------- | -------------------------- | --------------------------------------------- | ---------------------- |
| 14 | Option 1 -- User List             | `WS-OPTION = 1`            | XCTL to `COUSR00C` (User List (Security))     | COADM02Y (option data) |
| 15 | Option 2 -- User Add              | `WS-OPTION = 2`            | XCTL to `COUSR01C` (User Add (Security))      | COADM02Y (option data) |
| 16 | Option 3 -- User Update           | `WS-OPTION = 3`            | XCTL to `COUSR02C` (User Update (Security))   | COADM02Y (option data) |
| 17 | Option 4 -- User Delete           | `WS-OPTION = 4`            | XCTL to `COUSR03C` (User Delete (Security))   | COADM02Y (option data) |
| 18 | Option 5 -- Transaction Type List | `WS-OPTION = 5`            | XCTL to `COTRTLIC` (Transaction Type List/Update (Db2)) | COADM02Y (option data) |
| 19 | Option 6 -- Transaction Type Maint| `WS-OPTION = 6`            | XCTL to `COTRTUPC` (Transaction Type Maintenance (Db2)) | COADM02Y (option data) |
| 20 | Max options count                 | `CDEMO-ADMIN-OPT-COUNT = 6`| Upper bound for option validation (rule 8); array defined with OCCURS 9 but only 6 entries populated; a commented-out prior VALUE of 4 in COADM02Y confirms options 5 and 6 were added in the Db2 release | COADM02Y (lines 21-22) |

### PGMIDERR Error Handling

| #  | Rule                               | Condition                                    | Action                                                                                                   | Source Location          |
| -- | ---------------------------------- | -------------------------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------ |
| 21 | Catch PGMIDERR on XCTL             | CICS raises PGMIDERR when target program not found in CSD | Handle declared at program entry via `EXEC CICS HANDLE CONDITION PGMIDERR(PGMIDERR-ERR-PARA)` | MAIN-PARA (lines 77-79)  |
| 22 | PGMIDERR recovery -- info message  | Branched to by CICS condition handler        | Build message `'This option is not installed ...'` in green (DFHGREEN), re-send menu, then EXEC CICS RETURN with TRANSID(CA00); note: option name is commented out of STRING statement, so message is always generic | PGMIDERR-ERR-PARA (lines 270-283) |

### Screen Build Logic

| #  | Rule                              | Condition                                       | Action                                                                                           | Source Location             |
| -- | --------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------ | --------------------------- |
| 23 | Menu supports up to 10 options     | `WS-IDX` 1..10 in BUILD-MENU-OPTIONS loop       | Each option formatted as `{num}. {name}` and placed into OPTN001O..OPTN010O screen fields; options beyond 10 are silently skipped (WHEN OTHER: CONTINUE) | BUILD-MENU-OPTIONS (lines 231-265) |
| 24 | Header date formatted as MM/DD/YY  | Always on each SEND-MENU-SCREEN call            | `FUNCTION CURRENT-DATE` result is decomposed; year reduced to 2-digit YY via `WS-CURDATE-YEAR(3:2)` before moving to screen field CURDATEO | POPULATE-HEADER-INFO (lines 207-218) |
| 25 | Header time formatted as HH:MM:SS  | Always on each SEND-MENU-SCREEN call            | Hours, minutes, and seconds extracted from `FUNCTION CURRENT-DATE` result and moved to CURTIMEO screen field | POPULATE-HEADER-INFO (lines 220-224) |
| 26 | Every screen send erases the display | Always -- no conditional path skips ERASE     | `EXEC CICS SEND MAP ERASE` is unconditional; every send -- initial, error, re-display -- does a full terminal erase rather than a merge/dataonly update | SEND-MENU-SCREEN (line 186) |

### Dead Code and Missing Error Handling (Observations)

| #  | Rule                                    | Condition                                                    | Action                                                                                    | Source Location                   |
| -- | --------------------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------------- | --------------------------------- |
| 27 | WS-USRSEC-FILE is dead code             | `WS-USRSEC-FILE PIC X(08) VALUE 'USRSEC  '` defined in WORKING-STORAGE | Field is never referenced anywhere in the PROCEDURE DIVISION; likely a vestige of a VSAM user-security file access that was removed from this program | WORKING-STORAGE (line 39)         |
| 28 | RECEIVE-MENU-SCREEN RESP not tested     | `WS-RESP-CD` and `WS-REAS-CD` are populated from CICS RESP/RESP2 on the MAP RECEIVE | Neither field is tested after RECEIVE-MENU-SCREEN returns; a CICS error on receive (e.g. MAPFAIL) is silently ignored and processing continues to EVALUATE EIBAID | RECEIVE-MENU-SCREEN (lines 194-200) |
| 29 | 'Not installed' message omits option name | `CDEMO-ADMIN-OPT-NAME(WS-OPTION)` is commented out of the STRING statements in both PROCESS-ENTER-KEY and PGMIDERR-ERR-PARA | Message always reads `'This option is not installed ...'` with no context about which option; the commented-out code was never re-enabled | PROCESS-ENTER-KEY (lines 153-154), PGMIDERR-ERR-PARA (lines 274-275) |
| 30 | Stray period after PGMIDERR-ERR-PARA END-EXEC | Line 284 contains a bare `.` immediately after the `END-EXEC.` at line 283 | Redundant period following the paragraph-terminating period; does not create a new paragraph but is unusual coding style that could confuse maintenance programmers | PGMIDERR-ERR-PARA (line 284) |

## Calculations

| Calculation          | Formula / Logic                                                                                                       | Input Fields                         | Output Field    | Source Location              |
| -------------------- | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------ | --------------- | ---------------------------- |
| Option normalisation | Scan OPTIONI from right to find last non-space character position; extract substring OPTIONI(1:WS-IDX); INSPECT to replace all spaces with '0'; MOVE to numeric WS-OPTION | OPTIONI (BMS input field), WS-IDX (loop counter) | WS-OPTION (PIC 9(02)) | PROCESS-ENTER-KEY (lines 121-128) |
| Menu text build      | STRING {opt-num} DELIMITED BY SIZE + '. ' + {opt-name} DELIMITED BY SIZE INTO WS-ADMIN-OPT-TXT                       | CDEMO-ADMIN-OPT-NUM, CDEMO-ADMIN-OPT-NAME | WS-ADMIN-OPT-TXT (PIC X(40)) | BUILD-MENU-OPTIONS (lines 236-239) |
| Current date/time    | `MOVE FUNCTION CURRENT-DATE TO WS-CURDATE-DATA` -- intrinsic function returns 21-byte date/time/offset string; decomposed into month, day, year (4-digit), hours, minutes, seconds sub-fields | FUNCTION CURRENT-DATE (system) | WS-CURDATE-MM, WS-CURDATE-DD, WS-CURDATE-YY (2-digit), WS-CURTIME-HH, WS-CURTIME-MM, WS-CURTIME-SS | POPULATE-HEADER-INFO (line 207) |

## Error Handling

| Condition                              | Action                                                                                      | Return Code | Source Location                    |
| -------------------------------------- | ------------------------------------------------------------------------------------------- | ----------- | ---------------------------------- |
| EIBCALEN = 0 (no prior COMMAREA)       | XCTL to COSGN00C signon screen without COMMAREA; program does not abend                    | n/a         | MAIN-PARA (line 86)                |
| Invalid AID key (not Enter or PF3)     | Set ERR-FLG-ON; display CCDA-MSG-INVALID-KEY via WS-MESSAGE on screen; redisplay menu      | n/a         | MAIN-PARA (lines 103-106)          |
| Option not numeric, zero, or > max     | Set ERR-FLG-ON; display `'Please enter a valid option number...'`; redisplay menu          | n/a         | PROCESS-ENTER-KEY (lines 131-137)  |
| Option program name prefix = 'DUMMY'   | Display `'This option is not installed ...'` in green; redisplay menu; do not XCTL         | n/a         | PROCESS-ENTER-KEY (lines 150-157)  |
| CICS PGMIDERR on XCTL                  | Caught by HANDLE CONDITION; display `'This option is not installed ...'`; RETURN to CA00   | n/a         | PGMIDERR-ERR-PARA (lines 270-283)  |
| CICS error on MAP RECEIVE (MAPFAIL etc.) | WS-RESP-CD / WS-REAS-CD are set but never tested; no error branch exists -- gap in error handling | n/a    | RECEIVE-MENU-SCREEN (lines 194-200) |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. MAIN-PARA -- entry point; registers PGMIDERR handler; clears error flag and message
2. IF EIBCALEN = 0 -- PERFORM RETURN-TO-SIGNON-SCREEN (XCTL to COSGN00C without COMMAREA; program ends)
3. ELSE -- copy DFHCOMMAREA into CARDDEMO-COMMAREA
4. IF NOT CDEMO-PGM-REENTER -- first entry path: set re-enter flag, clear map, PERFORM SEND-MENU-SCREEN
5. ELSE -- re-entry path: PERFORM RECEIVE-MENU-SCREEN
6. EVALUATE EIBAID -- DFHENTER: PERFORM PROCESS-ENTER-KEY / DFHPF3: PERFORM RETURN-TO-SIGNON-SCREEN / OTHER: set error, PERFORM SEND-MENU-SCREEN
7. EXEC CICS RETURN TRANSID(WS-TRANID='CA00') COMMAREA(CARDDEMO-COMMAREA) -- suspends and awaits next user input
8. PROCESS-ENTER-KEY -- trims and normalises option input; validates numeric / range / non-zero; if invalid: PERFORM SEND-MENU-SCREEN (implicit fall-through back to RETURN)
9. PROCESS-ENTER-KEY (continued) -- if no error and not DUMMY program: EXEC CICS XCTL to target program passing CARDDEMO-COMMAREA (program exits here)
10. PROCESS-ENTER-KEY (continued) -- if DUMMY program: display 'not installed' message, PERFORM SEND-MENU-SCREEN
11. SEND-MENU-SCREEN -- PERFORM POPULATE-HEADER-INFO then PERFORM BUILD-MENU-OPTIONS; EXEC CICS SEND MAP ERASE
12. POPULATE-HEADER-INFO -- calls FUNCTION CURRENT-DATE; populates title, transaction name, program name, date (MM/DD/YY), and time (HH:MM:SS) in output map
13. BUILD-MENU-OPTIONS -- PERFORM VARYING loop 1 to CDEMO-ADMIN-OPT-COUNT; formats each option text; places into up to 10 output screen fields (OPTN001O..OPTN010O)
14. PGMIDERR-ERR-PARA -- CICS condition handler branch: builds 'not installed' message, PERFORM SEND-MENU-SCREEN, EXEC CICS RETURN TRANSID(CA00)
