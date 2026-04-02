---
type: business-rules
program: COUSR02C
program_type: online
status: draft
confidence: high
last_pass: 5
calls: []
called_by:
- COUSR00C
uses_copybooks:
- COCOM01Y
- COTTL01Y
- COUSR02
- CSDAT01Y
- CSMSG01Y
- CSUSR01Y
reads:
- USRSEC
writes: []
db_tables: []
transactions:
- CU02
mq_queues: []
---

# COUSR02C -- Business Rules

## Program Purpose

COUSR02C is an online CICS COBOL program that handles user record updates in the CardDemo application. It presents a user update screen (COUSR2A), reads the existing user record from the USRSEC VSAM file with a locked UPDATE intent, validates all mandatory fields, compares each field against the stored record to detect modifications, and rewrites the record only when at least one field has changed. It is invoked via transaction CU02 and is called by the user list/selection program COUSR00C.

## Input / Output

| Direction | Resource       | Type  | Description                                                      |
| --------- | -------------- | ----- | ---------------------------------------------------------------- |
| IN        | COUSR2A (screen) | CICS MAP | User update screen -- receives User ID, First Name, Last Name, Password, User Type entered by operator |
| IN/OUT    | USRSEC         | CICS VSAM FILE | User security file -- read with UPDATE lock, rewritten on change |
| IN        | DFHCOMMAREA    | CICS  | Communication area carrying CDEMO context (from/to program, user selection) |
| OUT       | COUSR2A (screen) | CICS MAP | User update screen -- displays current user data, validation errors, and success/failure messages |
| OUT       | CARDDEMO-COMMAREA | CICS XCTL/RETURN | Updated commarea passed on XCTL to previous program or on RETURN to transaction CU02 |

## Business Rules

### Entry and Dispatch Routing

| #  | Rule                              | Condition                                                                                           | Action                                                                                         | Source Location          |
| -- | --------------------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------ |
| 1  | Cold-start redirect               | EIBCALEN = 0 (no commarea -- session started without prior context)                                 | Set CDEMO-TO-PROGRAM = 'COSGN00C', perform RETURN-TO-PREV-SCREEN (XCTL to signon)              | MAIN-PARA (line 90-92)   |
| 2  | First-entry initialisation        | EIBCALEN > 0 AND NOT CDEMO-PGM-REENTER (CDEMO-PGM-CONTEXT not = 1)                                | Set CDEMO-PGM-REENTER to TRUE, clear screen map to LOW-VALUES, set cursor to User ID field     | MAIN-PARA (line 95-105)  |
| 3  | Pre-load user on first entry      | First entry AND CDEMO-CU02-USR-SELECTED not = SPACES or LOW-VALUES (user was selected by caller)   | Move selected user ID into USRIDINI field, PERFORM PROCESS-ENTER-KEY to look up and display record | MAIN-PARA (line 99-104) |
| 4  | ENTER key -- lookup/display user  | Re-enter AND EIBAID = DFHENTER                                                                      | PERFORM PROCESS-ENTER-KEY                                                                       | MAIN-PARA (line 109-110) |
| 5  | PF3 -- attempt save then return unconditionally | Re-enter AND EIBAID = DFHPF3                                                    | PERFORM UPDATE-USER-INFO (validation and save attempt), then unconditionally set CDEMO-TO-PROGRAM and PERFORM RETURN-TO-PREV-SCREEN regardless of whether UPDATE-USER-INFO succeeded, failed validation, or encountered an I/O error | MAIN-PARA (line 111-119) |
| 6  | PF3 return target fallback        | EIBAID = DFHPF3 AND CDEMO-FROM-PROGRAM = SPACES or LOW-VALUES                                      | Default return target set to 'COADM01C'                                                        | MAIN-PARA (line 113-114) |
| 7  | PF4 -- clear screen               | Re-enter AND EIBAID = DFHPF4                                                                        | PERFORM CLEAR-CURRENT-SCREEN (blank all input fields, redisplay)                                | MAIN-PARA (line 120-121) |
| 8  | PF5 -- save without navigate      | Re-enter AND EIBAID = DFHPF5                                                                        | PERFORM UPDATE-USER-INFO (save changes, stay on screen)                                         | MAIN-PARA (line 122-123) |
| 9  | PF12 -- cancel and return         | Re-enter AND EIBAID = DFHPF12                                                                       | Set CDEMO-TO-PROGRAM = 'COADM01C', XCTL (no save)                                              | MAIN-PARA (line 124-126) |
| 10 | Invalid key                       | Re-enter AND EIBAID = any key other than ENTER, PF3, PF4, PF5, PF12                                | Set ERR-FLG-ON, move CCDA-MSG-INVALID-KEY to WS-MESSAGE, redisplay screen                      | MAIN-PARA (line 127-130) |

### User ID Validation (PROCESS-ENTER-KEY)

| #  | Rule                     | Condition                                              | Action                                                                                          | Source Location                   |
| -- | ------------------------ | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------- | --------------------------------- |
| 11 | User ID mandatory        | USRIDINI of COUSR2AI = SPACES or LOW-VALUES            | Set ERR-FLG-ON, message: "User ID can NOT be empty...", set cursor to User ID field, redisplay  | PROCESS-ENTER-KEY (line 146-151)  |
| 12 | Clear dependent fields before lookup | NOT ERR-FLG-ON (User ID is non-blank)         | MOVE SPACES to FNAMEI, LNAMEI, PASSWDI, USRTYPEI before issuing READ -- prevents stale data showing if read fails | PROCESS-ENTER-KEY (line 157-161) |
| 13 | Lookup user after valid ID | NOT ERR-FLG-ON                                       | Move USRIDINI to SEC-USR-ID, PERFORM READ-USER-SEC-FILE                                         | PROCESS-ENTER-KEY (line 162-163)  |
| 14 | Populate screen from file | NOT ERR-FLG-ON (after successful read)                | Move SEC-USR-FNAME, SEC-USR-LNAME, SEC-USR-PWD, SEC-USR-TYPE to corresponding screen input fields, then PERFORM SEND-USRUPD-SCREEN | PROCESS-ENTER-KEY (line 166-172) |

### Mandatory Field Validation (UPDATE-USER-INFO)

All five validations are checked in sequence via EVALUATE TRUE; the first failing condition sets the error flag and calls SEND-USRUPD-SCREEN, stopping further evaluation for that invocation.

| #  | Rule                     | Condition                                                  | Action                                                                                             | Source Location                    |
| -- | ------------------------ | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------- |
| 15 | User ID mandatory        | USRIDINI of COUSR2AI = SPACES or LOW-VALUES                | Set ERR-FLG-ON, message: "User ID can NOT be empty...", cursor to User ID field, redisplay         | UPDATE-USER-INFO (line 180-185)    |
| 16 | First Name mandatory     | FNAMEI of COUSR2AI = SPACES or LOW-VALUES                  | Set ERR-FLG-ON, message: "First Name can NOT be empty...", cursor to First Name field, redisplay   | UPDATE-USER-INFO (line 186-191)    |
| 17 | Last Name mandatory      | LNAMEI of COUSR2AI = SPACES or LOW-VALUES                  | Set ERR-FLG-ON, message: "Last Name can NOT be empty...", cursor to Last Name field, redisplay     | UPDATE-USER-INFO (line 192-197)    |
| 18 | Password mandatory       | PASSWDI of COUSR2AI = SPACES or LOW-VALUES                 | Set ERR-FLG-ON, message: "Password can NOT be empty...", cursor to Password field, redisplay       | UPDATE-USER-INFO (line 198-203)    |
| 19 | User Type mandatory      | USRTYPEI of COUSR2AI = SPACES or LOW-VALUES                | Set ERR-FLG-ON, message: "User Type can NOT be empty...", cursor to User Type field, redisplay     | UPDATE-USER-INFO (line 204-209)    |

### Optimistic / Compare-Before-Write (UPDATE-USER-INFO)

| #  | Rule                              | Condition                                                                       | Action                                                                                           | Source Location                    |
| -- | --------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------- |
| 20 | Read with lock before update      | All mandatory fields pass validation                                            | EXEC CICS READ DATASET(WS-USRSEC-FILE) UPDATE issued against USRSEC to lock the record before any field comparison | UPDATE-USER-INFO (line 215-217) via READ-USER-SEC-FILE |
| 21 | First Name change detection       | FNAMEI of COUSR2AI NOT = SEC-USR-FNAME (screen value differs from file value)  | Move new value to SEC-USR-FNAME; set USR-MODIFIED-YES to TRUE                                    | UPDATE-USER-INFO (line 219-222)    |
| 22 | Last Name change detection        | LNAMEI of COUSR2AI NOT = SEC-USR-LNAME                                         | Move new value to SEC-USR-LNAME; set USR-MODIFIED-YES to TRUE                                    | UPDATE-USER-INFO (line 223-226)    |
| 23 | Password change detection         | PASSWDI of COUSR2AI NOT = SEC-USR-PWD                                          | Move new value to SEC-USR-PWD; set USR-MODIFIED-YES to TRUE                                      | UPDATE-USER-INFO (line 227-230)    |
| 24 | User Type change detection        | USRTYPEI of COUSR2AI NOT = SEC-USR-TYPE                                        | Move new value to SEC-USR-TYPE; set USR-MODIFIED-YES to TRUE                                     | UPDATE-USER-INFO (line 231-234)    |
| 25 | No-change guard                   | USR-MODIFIED-YES = FALSE (none of the four fields changed)                     | No rewrite issued; message: "Please modify to update ...", display in RED, redisplay screen      | UPDATE-USER-INFO (line 236-243)    |
| 26 | Write only when changed           | USR-MODIFIED-YES = TRUE (at least one field changed)                           | PERFORM UPDATE-USER-SEC-FILE (EXEC CICS REWRITE)                                                 | UPDATE-USER-INFO (line 236-237)    |

### Navigation / Return Rules

| #  | Rule                          | Condition                                              | Action                                                                                         | Source Location                     |
| -- | ----------------------------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------- | ----------------------------------- |
| 27 | Return target default         | CDEMO-TO-PROGRAM = LOW-VALUES or SPACES at return time | Override with 'COSGN00C'                                                                       | RETURN-TO-PREV-SCREEN (line 252-253) |
| 28 | Stamp outbound context        | Always on return                                       | Set CDEMO-FROM-TRANID = WS-TRANID ('CU02'), CDEMO-FROM-PROGRAM = WS-PGMNAME ('COUSR02C'), CDEMO-PGM-CONTEXT = 0 | RETURN-TO-PREV-SCREEN (line 255-257) |
| 29 | XCTL to target program        | Always on return                                       | EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA(CARDDEMO-COMMAREA)                           | RETURN-TO-PREV-SCREEN (line 258-261) |

## Calculations

| Calculation       | Formula / Logic                                                                                                                        | Input Fields                               | Output Field | Source Location                      |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ | ------------ | ------------------------------------ |
| Success message   | STRING 'User ' DELIMITED BY SIZE, SEC-USR-ID DELIMITED BY SPACE, ' has been updated ...' DELIMITED BY SIZE INTO WS-MESSAGE            | SEC-USR-ID (8-char user ID, trailing spaces trimmed by DELIMITED BY SPACE) | WS-MESSAGE   | UPDATE-USER-SEC-FILE (line 372-375) |
| Current date/time | FUNCTION CURRENT-DATE stored in WS-CURDATE-DATA; WS-CURDATE-MONTH/DAY moved to WS-CURDATE-MM/DD; WS-CURDATE-YEAR(3:2) moved to WS-CURDATE-YY (last two digits only); combined as MM/DD/YY into CURDATEO; similarly HH:MM:SS into CURTIMEO | System date/time | CURDATEO, CURTIMEO of COUSR2AO | POPULATE-HEADER-INFO (line 298-315) |

## Error Handling

| Condition                                 | Action                                                                                                       | Return Code              | Source Location                        |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------ | -------------------------------------- |
| CICS READ USRSEC -- NORMAL                | CONTINUE (dead statement), then set WS-MESSAGE = "Press PF5 key to save your updates ...", set ERRMSGC = DFHNEUTR (neutral colour), PERFORM SEND-USRUPD-SCREEN. NOTE: this paragraph always sends the screen on NORMAL, even when called from UPDATE-USER-INFO (see Behavioral Anomaly note below) | DFHRESP(NORMAL) | READ-USER-SEC-FILE (line 334-339) |
| CICS READ USRSEC -- NOTFND                | Set ERR-FLG-ON, message: "User ID NOT found...", cursor to User ID field, PERFORM SEND-USRUPD-SCREEN         | DFHRESP(NOTFND)          | READ-USER-SEC-FILE (line 340-345)      |
| CICS READ USRSEC -- OTHER (unexpected)    | DISPLAY 'RESP:' WS-RESP-CD 'REAS:' WS-REAS-CD to CICS log, set ERR-FLG-ON, message: "Unable to lookup User...", cursor to First Name field, PERFORM SEND-USRUPD-SCREEN | Any other RESP code | READ-USER-SEC-FILE (line 346-352) |
| CICS REWRITE USRSEC -- NORMAL             | MOVE SPACES to WS-MESSAGE, set ERRMSGC = DFHGREEN (green colour), STRING success message "User &lt;ID&gt; has been updated ..." into WS-MESSAGE, PERFORM SEND-USRUPD-SCREEN | DFHRESP(NORMAL) | UPDATE-USER-SEC-FILE (line 369-376) |
| CICS REWRITE USRSEC -- NOTFND             | Set ERR-FLG-ON, message: "User ID NOT found...", cursor to User ID field, PERFORM SEND-USRUPD-SCREEN         | DFHRESP(NOTFND)          | UPDATE-USER-SEC-FILE (line 377-382)    |
| CICS REWRITE USRSEC -- OTHER (unexpected) | DISPLAY 'RESP:' WS-RESP-CD 'REAS:' WS-REAS-CD to CICS log, set ERR-FLG-ON, message: "Unable to Update User...", cursor to First Name field, PERFORM SEND-USRUPD-SCREEN | Any other RESP code | UPDATE-USER-SEC-FILE (line 383-389) |
| Invalid AID key (any unrecognised key)    | MOVE 'Y' to WS-ERR-FLG, move CCDA-MSG-INVALID-KEY to WS-MESSAGE, PERFORM SEND-USRUPD-SCREEN without saving  | WS-ERR-FLG = 'Y'         | MAIN-PARA (line 128-130)               |
| No changes detected on save               | Message: "Please modify to update ...", ERRMSGC = DFHRED (red colour), no file write, screen stays open     | WS-ERR-FLG stays 'N'     | UPDATE-USER-INFO (line 239-242)        |
| CICS RECEIVE map -- no RESP check         | EXEC CICS RECEIVE stores codes in WS-RESP-CD / WS-REAS-CD but neither is tested after the call -- any RECEIVE failure (e.g., map send error) silently proceeds into AID evaluation with whatever data was in COUSR2AI | Not checked | RECEIVE-USRUPD-SCREEN (line 285-291) |

### Behavioral Anomaly: Dead CONTINUE Statements

Three `CONTINUE` statements appear immediately before or after substantive code, where they serve no purpose (they are no-ops). All three are in the WHEN OTHER or WHEN branches of EVALUATE TRUE structures:

- **Line 335** (READ-USER-SEC-FILE, WHEN DFHRESP(NORMAL)): `CONTINUE` appears before the MOVE that sets WS-MESSAGE. Has no effect.
- **Line 154** (PROCESS-ENTER-KEY, WHEN OTHER): `CONTINUE` appears after `MOVE -1 TO USRIDINL`. Has no effect; the paragraph continues to the next IF statement regardless.
- **Line 212** (UPDATE-USER-INFO, WHEN OTHER): `CONTINUE` appears after `MOVE -1 TO FNAMEL`. Has no effect; the paragraph continues to the field-comparison block regardless.

These dead statements suggest either copy-paste template artefacts or remnants of removed code. They have no functional impact but add noise for maintainers.

### Behavioral Anomaly: Double Screen Send on READ NORMAL

READ-USER-SEC-FILE is a shared paragraph called from two places. Its NORMAL response branch unconditionally calls PERFORM SEND-USRUPD-SCREEN (line 336-339) -- it does not return silently. This double-send anomaly occurs on two distinct paths:

**Path A -- UPDATE-USER-INFO (PF3 or PF5):**
1. UPDATE-USER-INFO (line 217) calls READ-USER-SEC-FILE. NORMAL branch sends the screen with "Press PF5 key to save your updates ...".
2. Control returns to UPDATE-USER-INFO, which compares fields and, if any changed, calls UPDATE-USER-SEC-FILE which sends the screen again with the green success message.

Net result: two SEND MAP operations. The second SEND MAP (with ERASE) overwrites the first, so the final visible screen is the green success message. The intermediate send is harmless but wasteful.

**Path B -- First-entry pre-load (MAIN-PARA lines 99-105):**
1. When first entry AND CDEMO-CU02-USR-SELECTED is non-blank, MAIN-PARA calls PROCESS-ENTER-KEY (line 103). PROCESS-ENTER-KEY calls READ-USER-SEC-FILE (NORMAL sends screen), then on successful return populates screen fields and calls SEND-USRUPD-SCREEN again (line 171).
2. After PROCESS-ENTER-KEY returns, MAIN-PARA unconditionally calls PERFORM SEND-USRUPD-SCREEN again (line 105).

Net result on Path B: up to three SEND MAP operations on a successful first-entry pre-load with a pre-selected user. The final visible screen is the last send from MAIN-PARA line 105.

Modernisation work should refactor READ-USER-SEC-FILE to separate the I/O and display concerns.

### Behavioral Anomaly: PF3 Ignores Update Outcome

When EIBAID = DFHPF3, MAIN-PARA calls UPDATE-USER-INFO (line 112) then unconditionally proceeds to set CDEMO-TO-PROGRAM and PERFORM RETURN-TO-PREV-SCREEN (lines 113-119). There is no check of WS-ERR-FLG after UPDATE-USER-INFO returns. This means:

- If a mandatory field is blank, UPDATE-USER-INFO sets ERR-FLG-ON and sends an error screen, but the program immediately XCTLs away anyway.
- If the CICS READ or REWRITE fails, same outcome -- XCTL proceeds.
- The error screen is sent (so the user may briefly see it) but the transaction is already transferring control.

PF5 does NOT have this problem -- it only calls UPDATE-USER-INFO and then falls through to EXEC CICS RETURN, staying on the screen. PF3 is the only key with this unconditional navigation defect.

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. MAIN-PARA -- Entry point. Initialises WS-ERR-FLG to 'N' (ERR-FLG-OFF) and WS-USR-MODIFIED to 'N' (USR-MODIFIED-NO). Clears WS-MESSAGE and ERRMSGO. Branches on EIBCALEN = 0 (cold start), first entry (NOT CDEMO-PGM-REENTER), or re-entry (EVALUATE EIBAID dispatch).
2. RECEIVE-USRUPD-SCREEN -- Receives map COUSR2A from mapset COUSR02 into COUSR2AI on every re-entry before AID evaluation. RESP/RESP2 are captured in WS-RESP-CD/WS-REAS-CD but not tested.
3. PROCESS-ENTER-KEY -- Validates User ID is non-blank; clears dependent fields; reads USRSEC with UPDATE lock via READ-USER-SEC-FILE; if read succeeds, populates screen fields from SEC-USER-DATA and calls SEND-USRUPD-SCREEN again.
4. UPDATE-USER-INFO -- Validates all five mandatory fields (EVALUATE TRUE, first failure wins). If all pass, reads USRSEC with UPDATE lock via READ-USER-SEC-FILE (which also sends screen on NORMAL), then compares each of the four editable fields to the file record, rewrites only if at least one change detected.
5. READ-USER-SEC-FILE -- Issues EXEC CICS READ DATASET(WS-USRSEC-FILE='USRSEC  ') INTO(SEC-USER-DATA) with UPDATE keyword (record-level lock). On NORMAL: dead CONTINUE (line 335), then sets WS-MESSAGE and calls SEND-USRUPD-SCREEN (side effect -- see Behavioral Anomaly above). On NOTFND/OTHER: sets ERR-FLG-ON and sends screen with error message. Called by both PROCESS-ENTER-KEY and UPDATE-USER-INFO.
6. UPDATE-USER-SEC-FILE -- Issues EXEC CICS REWRITE DATASET(WS-USRSEC-FILE='USRSEC  ') FROM(SEC-USER-DATA). Handles NORMAL (green success), NOTFND, and OTHER (display RESP/REAS codes).
7. SEND-USRUPD-SCREEN -- Calls POPULATE-HEADER-INFO, moves WS-MESSAGE to ERRMSGO of COUSR2AO, issues EXEC CICS SEND MAP('COUSR2A') MAPSET('COUSR02') ERASE CURSOR.
8. POPULATE-HEADER-INFO -- Formats current date as MM/DD/YY (year as last 2 digits via WS-CURDATE-YEAR(3:2)) and time as HH:MM:SS from FUNCTION CURRENT-DATE; populates CCDA-TITLE01, CCDA-TITLE02, WS-TRANID, WS-PGMNAME into screen header fields.
9. RETURN-TO-PREV-SCREEN -- Sets CDEMO-FROM-TRANID = WS-TRANID, CDEMO-FROM-PROGRAM = WS-PGMNAME, CDEMO-PGM-CONTEXT = 0, then EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA(CARDDEMO-COMMAREA).
10. CLEAR-CURRENT-SCREEN -- Calls INITIALIZE-ALL-FIELDS then SEND-USRUPD-SCREEN. PF4 handler.
11. INITIALIZE-ALL-FIELDS -- Sets cursor length to -1 on USRIDINL; moves SPACES to USRIDINI, FNAMEI, LNAMEI, PASSWDI, USRTYPEI, WS-MESSAGE.
12. EXEC CICS RETURN (MAIN-PARA, line 135-138) -- Returns control to CICS with TRANSID(WS-TRANID='CU02') COMMAREA(CARDDEMO-COMMAREA); executed at the end of every path that does not XCTL away.
