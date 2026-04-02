---
type: business-rules
program: COMEN01C
program_type: online
status: draft
confidence: high
last_pass: 5
calls: []
called_by:
- COBIL00C
- COCRDLIC
- CORPT00C
- COSGN00C
- COTRN00C
- COTRN01C
- COTRN02C
uses_copybooks:
- COCOM01Y
- COMEN01
- COMEN02Y
- COTTL01Y
- CSDAT01Y
- CSMSG01Y
- CSUSR01Y
reads: []
writes: []
db_tables: []
transactions:
- CM00
mq_queues: []
---

# COMEN01C -- Business Rules

## Program Purpose

COMEN01C is the main menu controller for regular (non-admin) users in the CardDemo CICS application. It presents a numbered menu of up to 11 functional options, validates the user's selection, enforces access control based on user type, and transfers control to the selected sub-program via EXEC CICS XCTL. It runs under transaction CM00 and uses CARDDEMO-COMMAREA to pass context between programs.

## Input / Output

| Direction | Resource          | Type | Description                                                         |
| --------- | ----------------- | ---- | ------------------------------------------------------------------- |
| IN        | COMEN1A / COMEN01 | CICS | BMS map receive -- user's menu option selection (OPTIONI field)     |
| OUT       | COMEN1A / COMEN01 | CICS | BMS map send (ERASE) -- rendered menu with up to 12 option slots and error message |
| IN/OUT    | CARDDEMO-COMMAREA | CICS | COMMAREA passed on RETURN and XCTL to preserve session context      |
| OUT       | COSGN00C          | CICS | XCTL transfer to sign-on screen when no COMMAREA or PF3 pressed (no COMMAREA passed) |
| OUT       | Target sub-program | CICS | XCTL transfer to the program associated with the selected option (COMMAREA passed) |

## Business Rules

### Session Initialisation

| #  | Rule                              | Condition                             | Action                                                                                   | Source Location |
| -- | --------------------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------- | --------------- |
| 1  | No COMMAREA means unauthenticated | `EIBCALEN = 0`                        | Set CDEMO-FROM-PROGRAM = 'COSGN00C', PERFORM RETURN-TO-SIGNON-SCREEN (XCTL to COSGN00C) | MAIN-PARA       |
| 2  | First entry to menu               | COMMAREA present AND NOT CDEMO-PGM-REENTER (value = 0) | Set CDEMO-PGM-REENTER = TRUE (value 1), clear COMEN1AO to LOW-VALUES, PERFORM SEND-MENU-SCREEN | MAIN-PARA |
| 3  | Re-entry after first display      | COMMAREA present AND CDEMO-PGM-REENTER (value = 1) | PERFORM RECEIVE-MENU-SCREEN then evaluate AID key                                       | MAIN-PARA       |

### AID Key Routing

| #  | Rule                        | Condition                  | Action                                                                             | Source Location |
| -- | --------------------------- | -------------------------- | ---------------------------------------------------------------------------------- | --------------- |
| 4  | Enter key accepted          | `EIBAID = DFHENTER`        | PERFORM PROCESS-ENTER-KEY to validate and dispatch selection                       | MAIN-PARA       |
| 5  | PF3 returns to sign-on      | `EIBAID = DFHPF3`          | Set CDEMO-TO-PROGRAM = 'COSGN00C', PERFORM RETURN-TO-SIGNON-SCREEN (XCTL to COSGN00C, no COMMAREA passed) | MAIN-PARA   |
| 6  | Any other key is invalid    | `EIBAID = WHEN OTHER`      | Set WS-ERR-FLG = 'Y', move CCDA-MSG-INVALID-KEY ("Invalid key pressed. Please see below...") to WS-MESSAGE, re-send menu screen | MAIN-PARA |

### Option Input Validation

| #  | Rule                              | Condition                                                                            | Action                                                                                         | Source Location  |
| -- | --------------------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- | ---------------- |
| 7  | Trailing-space trimming           | Always on Enter key path                                                             | Scan OPTIONI from right (position LENGTH) decrementing WS-IDX by -1; loop exits when character is NOT space OR WS-IDX reaches 1 (floor guard); extract substring 1:WS-IDX; replace remaining spaces with '0'; MOVE to WS-OPTION-X (PIC X(02) JUST RIGHT); MOVE to WS-OPTION (PIC 9(02)). Edge case: fully-blank input leaves WS-IDX=1 with position-1 character = space, which after INSPECT becomes WS-OPTION=00, triggering Rule 10. | PROCESS-ENTER-KEY |
| 8  | Option must be numeric            | `WS-OPTION IS NOT NUMERIC`                                                           | Set WS-ERR-FLG = 'Y', move "Please enter a valid option number..." to WS-MESSAGE, re-send screen | PROCESS-ENTER-KEY |
| 9  | Option must not exceed menu count | `WS-OPTION > CDEMO-MENU-OPT-COUNT` (max value = 11 per COMEN02Y copybook)           | Set WS-ERR-FLG = 'Y', move "Please enter a valid option number..." to WS-MESSAGE, re-send screen | PROCESS-ENTER-KEY |
| 10 | Option must not be zero           | `WS-OPTION = ZEROS`                                                                  | Set WS-ERR-FLG = 'Y', move "Please enter a valid option number..." to WS-MESSAGE, re-send screen | PROCESS-ENTER-KEY |

Note: Rules 8, 9, and 10 are evaluated as a single combined IF (OR logic). An invalid option triggers one shared error message; ERR-FLG-ON remains false (WS-ERR-FLG = 'Y' but the 88-level ERR-FLG-ON maps to the same field). However the `PERFORM SEND-MENU-SCREEN` inside the IF block causes the screen to be re-sent immediately, and no further code in PROCESS-ENTER-KEY executes because the access-control and dispatch blocks each depend on `ERR-FLG-ON` being false or the flag check at line 145.

### Access Control

| #  | Rule                                        | Condition                                                                                  | Action                                                                                              | Source Location  |
| -- | ------------------------------------------- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- | ---------------- |
| 11 | Regular users cannot access Admin-only options | `CDEMO-USRTYP-USER` (CDEMO-USER-TYPE = 'U') AND `CDEMO-MENU-OPT-USRTYPE(WS-OPTION) = 'A'` | Set ERR-FLG-ON = TRUE, move "No access - Admin Only option... " to WS-MESSAGE, re-send screen      | PROCESS-ENTER-KEY |
| 12 | All 11 current menu options are 'U' type    | CDEMO-MENU-OPT-USRTYPE values in COMEN02Y are all 'U'                                     | Rule 11 cannot trigger for any currently defined option; reserved for future Admin-flagged options | COMEN02Y copybook |

### Program Dispatch

| #  | Rule                                            | Condition                                                                             | Action                                                                                                                         | Source Location  |
| -- | ----------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ---------------- |
| 13 | Special handling for COPAUS0C option            | `CDEMO-MENU-OPT-PGMNAME(WS-OPTION) = 'COPAUS0C'`                                     | EXEC CICS INQUIRE PROGRAM (NOHANDLE) to check installation before XCTL; if not installed show error (red): "This option [name] is not installed..." | PROCESS-ENTER-KEY |
| 14 | Installed COPAUS0C dispatched via XCTL          | `EIBRESP = DFHRESP(NORMAL)` after INQUIRE                                             | Set CDEMO-FROM-TRANID = WS-TRANID ('CM00'), CDEMO-FROM-PROGRAM = 'COMEN01C', CDEMO-PGM-CONTEXT = 0; EXEC CICS XCTL to selected program with COMMAREA | PROCESS-ENTER-KEY |
| 15 | DUMMY placeholder options not yet available     | `CDEMO-MENU-OPT-PGMNAME(WS-OPTION)(1:5) = 'DUMMY'`                                   | Set error message colour to DFHGREEN, show: "This option [name] is coming soon ..." -- no XCTL, menu is re-sent                  | PROCESS-ENTER-KEY |
| 16 | All other valid programs dispatched via XCTL    | WHEN OTHER in EVALUATE (all options other than COPAUS0C and DUMMY)                    | Set CDEMO-FROM-TRANID = 'CM00', CDEMO-FROM-PROGRAM = 'COMEN01C', CDEMO-PGM-CONTEXT = 0; EXEC CICS XCTL to selected program with COMMAREA | PROCESS-ENTER-KEY |
| 17 | Re-send menu when no XCTL occurred              | Reached only when no XCTL was executed -- i.e. COPAUS0C not installed, DUMMY option, or XCTL failure | PERFORM SEND-MENU-SCREEN at line 190 (inside `IF NOT ERR-FLG-ON` block); runs for all non-dispatching EVALUATE branches        | PROCESS-ENTER-KEY |

Note: Source code at lines 179-180 contains a duplicate `MOVE WS-PGMNAME TO CDEMO-FROM-PROGRAM` statement in the WHEN OTHER dispatch branch. This appears to be a copy-paste redundancy with no functional effect. Additionally, two lines are commented out in this branch: `MOVE WS-USER-ID TO CDEMO-USER-ID` and `MOVE SEC-USR-TYPE TO CDEMO-USER-TYPE`, suggesting user identity propagation was previously intended but removed.

Note: The STRING used to build the "not installed" error message (COPAUS0C path, line 165) uses `DELIMITED BY '  '` (two spaces) to terminate the option name, whereas the DUMMY path (line 174) uses `DELIMITED BY SPACE` (single space). These differ in how they truncate option names that contain embedded spaces -- the COPAUS0C path preserves option names until two consecutive spaces are found, while the DUMMY path stops at the first space.

### Menu Option Definitions (from COMEN02Y)

| #  | Rule                                         | Option | Program Name | User Type |
| -- | -------------------------------------------- | ------ | ------------ | --------- |
| 18 | Option 1: Account View                       | 1      | COACTVWC     | U         |
| 19 | Option 2: Account Update                     | 2      | COACTUPC     | U         |
| 20 | Option 3: Credit Card List                   | 3      | COCRDLIC     | U         |
| 21 | Option 4: Credit Card View                   | 4      | COCRDSLC     | U         |
| 22 | Option 5: Credit Card Update                 | 5      | COCRDUPC     | U         |
| 23 | Option 6: Transaction List                   | 6      | COTRN00C     | U         |
| 24 | Option 7: Transaction View                   | 7      | COTRN01C     | U         |
| 25 | Option 8: Transaction Add                    | 8      | COTRN02C     | U         |
| 26 | Option 9: Transaction Reports                | 9      | CORPT00C     | U         |
| 27 | Option 10: Bill Payment                      | 10     | COBIL00C     | U         |
| 28 | Option 11: Pending Authorization View        | 11     | COPAUS0C     | U         |

### Return-to-Sign-on Guard

| #  | Rule                                      | Condition                                            | Action                                     | Source Location          |
| -- | ----------------------------------------- | ---------------------------------------------------- | ------------------------------------------ | ------------------------ |
| 29 | Default sign-on target if none specified  | `CDEMO-TO-PROGRAM = LOW-VALUES OR SPACES`            | Set CDEMO-TO-PROGRAM = 'COSGN00C' before XCTL | RETURN-TO-SIGNON-SCREEN |
| 30 | XCTL to sign-on passes no COMMAREA        | Always in RETURN-TO-SIGNON-SCREEN                    | EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) -- no COMMAREA clause; session context is not forwarded to sign-on | RETURN-TO-SIGNON-SCREEN |

### Menu Screen Construction

| #  | Rule                                         | Condition                                                              | Action                                                                                                       | Source Location    |
| -- | -------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------ |
| 31 | Menu supports up to 11 populated slots       | `WS-IDX` iterates 1 to CDEMO-MENU-OPT-COUNT (=11)                     | Each iteration formats "[num]. [name]" into WS-MENU-OPT-TXT and moves to OPTN001O through OPTN011O on map   | BUILD-MENU-OPTIONS |
| 32 | Slot 12 is defined but unreachable           | EVALUATE WS-IDX WHEN 12 branch exists in source (line 298)            | OPTN012O would be populated if CDEMO-MENU-OPT-COUNT were raised to 12; currently unreachable with COMEN02Y data (count = 11) | BUILD-MENU-OPTIONS |
| 33 | Indices above 12 are silently ignored        | `WHEN OTHER` in EVALUATE WS-IDX                                        | CONTINUE -- no output field populated; loop bounded by CDEMO-MENU-OPT-COUNT so this branch is also unreachable in practice | BUILD-MENU-OPTIONS |
| 34 | Screen send uses ERASE                       | Always on SEND-MENU-SCREEN path                                        | EXEC CICS SEND MAP ERASE -- entire terminal screen is cleared before menu is written                         | SEND-MENU-SCREEN   |
| 35 | Header shows current date and time           | Always on SEND-MENU-SCREEN path                                        | FUNCTION CURRENT-DATE split into MM, DD, YY and HH, MM, SS; moved to CURDATEO and CURTIMEO map fields        | POPULATE-HEADER-INFO |
| 36 | Header shows transaction ID and program name | Always                                                                 | WS-TRANID ('CM00') to TRNNAMEO; WS-PGMNAME ('COMEN01C') to PGMNAMEO                                          | POPULATE-HEADER-INFO |

### Dead Code and Observations

| #  | Observation                                      | Details                                                                                                                   | Source Location      |
| -- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| 37 | WS-USRSEC-FILE defined but never used            | WORKING-STORAGE field `WS-USRSEC-FILE PIC X(08) VALUE 'USRSEC  '` is declared at line 39 but has no reference in PROCEDURE DIVISION; no EXEC CICS READ or file I/O against USRSEC exists in this program | Lines 39 / WORKING-STORAGE |
| 38 | RECEIVE-MENU-SCREEN RESP codes captured but not checked | EXEC CICS RECEIVE stores response in WS-RESP-CD and WS-REAS-CD (RESP/RESP2) but no subsequent IF EIBRESP or WS-RESP-CD check exists; map receive errors are silently ignored | RECEIVE-MENU-SCREEN  |

## Calculations

| Calculation       | Formula / Logic                                                                                                                          | Input Fields                                    | Output Field  | Source Location   |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | ------------- | ----------------- |
| Option normalisation | PERFORM VARYING WS-IDX FROM LENGTH OF OPTIONI BY -1; loop exits when `OPTIONI(WS-IDX:1) NOT = SPACES` OR `WS-IDX = 1` (floor guard prevents underflow). After loop: MOVE OPTIONI(1:WS-IDX) TO WS-OPTION-X; INSPECT WS-OPTION-X REPLACING ALL ' ' BY '0'; MOVE WS-OPTION-X TO WS-OPTION (PIC 9(02)). Edge case: fully-blank input causes WS-IDX=1 where character at position 1 is still a space; after INSPECT WS-OPTION becomes 00, which triggers the WS-OPTION = ZEROS validation error (Rule 10). | OPTIONI of COMEN1AI (user-typed option field)   | WS-OPTION     | PROCESS-ENTER-KEY |
| Date formatting   | FUNCTION CURRENT-DATE gives 21-char result; positions 5-6 = month, 7-8 = day, 9-12 = year (last 2 chars used); assembled as MM-DD-YY   | WS-CURDATE-DATA (current date)                  | CURDATEO      | POPULATE-HEADER-INFO |
| Time formatting   | FUNCTION CURRENT-DATE positions 9-10 = hours, 11-12 = minutes, 13-14 = seconds; assembled as HH-MM-SS                                  | WS-CURDATE-DATA (current date)                  | CURTIMEO      | POPULATE-HEADER-INFO |
| Menu text build   | STRING CDEMO-MENU-OPT-NUM DELIMITED BY SIZE + '. ' + CDEMO-MENU-OPT-NAME DELIMITED BY SIZE INTO WS-MENU-OPT-TXT (40 chars)              | CDEMO-MENU-OPT-NUM(n), CDEMO-MENU-OPT-NAME(n)  | WS-MENU-OPT-TXT | BUILD-MENU-OPTIONS |

## Error Handling

| Condition                                       | Action                                                                                          | Return Code | Source Location  |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------- | ----------- | ---------------- |
| EIBCALEN = 0 (no COMMAREA on entry)             | XCTL to COSGN00C sign-on screen; flow does not continue                                        | --          | MAIN-PARA        |
| Invalid AID key (not ENTER or PF3)              | WS-ERR-FLG = 'Y'; display "Invalid key pressed. Please see below..." in ERRMSGO; re-send menu  | --          | MAIN-PARA        |
| Option not numeric                              | WS-ERR-FLG = 'Y'; display "Please enter a valid option number..." in ERRMSGO; re-send menu     | --          | PROCESS-ENTER-KEY |
| Option > CDEMO-MENU-OPT-COUNT (11) or = 0      | WS-ERR-FLG = 'Y'; display "Please enter a valid option number..." in ERRMSGO; re-send menu     | --          | PROCESS-ENTER-KEY |
| User type 'U' selects Admin-only option ('A')   | ERR-FLG-ON = TRUE; display "No access - Admin Only option... " in WS-MESSAGE; re-send menu     | --          | PROCESS-ENTER-KEY |
| COPAUS0C not installed (CICS INQUIRE fails)     | Set ERRMSGC to DFHRED; STRING "This option [name] is not installed..." into WS-MESSAGE; re-send menu | EIBRESP != DFHRESP(NORMAL) | PROCESS-ENTER-KEY |
| Option maps to DUMMY program (1:5 = 'DUMMY')    | Set ERRMSGC to DFHGREEN; STRING "This option [name] is coming soon ..." into WS-MESSAGE; re-send menu | --      | PROCESS-ENTER-KEY |
| RECEIVE-MENU-SCREEN CICS error                  | WS-RESP-CD and WS-REAS-CD are populated but never tested; error is silently ignored and processing continues as if receive succeeded | RESP/RESP2 stored but unchecked | RECEIVE-MENU-SCREEN |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. MAIN-PARA -- entry point; initialises flags; checks EIBCALEN; branches on first vs. re-entry
2. RETURN-TO-SIGNON-SCREEN -- called when EIBCALEN=0 or PF3; XCTLs to COSGN00C (or CDEMO-TO-PROGRAM); no COMMAREA passed on this XCTL
3. SEND-MENU-SCREEN -- called on first entry; builds and sends BMS map COMEN1A with ERASE
4. POPULATE-HEADER-INFO -- called by SEND-MENU-SCREEN; populates date, time, tranid, pgmname fields
5. BUILD-MENU-OPTIONS -- called by SEND-MENU-SCREEN; iterates CDEMO-MENU-OPT-COUNT (=11) entries into OPTN001O-OPTN011O
6. RECEIVE-MENU-SCREEN -- called on re-entry; reads BMS map COMEN1A into COMEN1AI; RESP codes stored but not checked
7. PROCESS-ENTER-KEY -- called when ENTER pressed; normalises option input; validates; enforces access control; dispatches
8. EXEC CICS INQUIRE PROGRAM (NOHANDLE) -- conditional check only for COPAUS0C before XCTL
9. EXEC CICS XCTL PROGRAM(...) COMMAREA(CARDDEMO-COMMAREA) -- unconditional program transfer to selected menu option's program (sets CDEMO-FROM-TRANID='CM00', CDEMO-FROM-PROGRAM='COMEN01C', CDEMO-PGM-CONTEXT=0 in COMMAREA before transfer)
10. EXEC CICS RETURN TRANSID(WS-TRANID='CM00') COMMAREA(CARDDEMO-COMMAREA) -- issued at end of MAIN-PARA to retain transaction context across screen interactions
