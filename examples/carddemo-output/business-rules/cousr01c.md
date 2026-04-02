---
type: business-rules
program: COUSR01C
program_type: online
status: draft
confidence: high
last_pass: 2
calls: []
called_by: []
uses_copybooks:
- COCOM01Y
- COTTL01Y
- COUSR01
- CSDAT01Y
- CSMSG01Y
- CSUSR01Y
reads:
- USRSEC
writes:
- USRSEC
db_tables: []
transactions:
- CU01
mq_queues: []
---

# COUSR01C -- Business Rules

## Program Purpose

COUSR01C is a CICS online program that adds a new user (Regular or Admin type) to the USRSEC security file. It presents the user-add screen (map COUSR1A / mapset COUSR01), validates all mandatory input fields, and writes a new user record keyed by User ID. Duplicate user IDs are detected and reported. The program participates in the CardDemo pseudo-conversational pattern: it returns to transaction CU01 after every interaction, passing the communication area forward.

## Input / Output

| Direction | Resource | Type | Description |
| --------- | -------- | ---- | ----------- |
| IN        | COUSR1A (COUSR01) | CICS BMS Map | User-add screen input: First Name, Last Name, User ID, Password, User Type |
| OUT       | COUSR1A (COUSR01) | CICS BMS Map | User-add screen output with header info, error messages, and success confirmation |
| IN/OUT    | USRSEC   | CICS VSAM File | User security file -- new records written keyed by SEC-USR-ID |
| IN        | DFHCOMMAREA | CICS Commarea | Commarea passed from calling program (CARDDEMO-COMMAREA layout from COCOM01Y) |
| OUT       | CARDDEMO-COMMAREA | CICS Commarea | Updated commarea returned to transaction CU01 on RETURN, or passed to COADM01C on PF3 |

## Business Rules

### Session Initialisation

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 1 | No commarea on first entry | `EIBCALEN = 0` | Set `CDEMO-TO-PROGRAM` to `COSGN00C` and transfer control via XCTL (redirect to sign-on screen) | MAIN-PARA line 78-80 |
| 2 | First-time program entry | `EIBCALEN > 0` AND `NOT CDEMO-PGM-REENTER` (i.e., `CDEMO-PGM-CONTEXT = 0`) | Set `CDEMO-PGM-REENTER` to TRUE (context = 1), initialise map to LOW-VALUES, set cursor to First Name field, send user-add screen | MAIN-PARA lines 83-87 |
| 3 | Subsequent entries (re-enter) | `CDEMO-PGM-REENTER` (context = 1) | Receive screen input and dispatch on attention identifier (AID) | MAIN-PARA lines 88-103 |

### AID Key Routing

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 4 | Enter key pressed | `EIBAID = DFHENTER` | Perform input validation and write user record (PROCESS-ENTER-KEY) | MAIN-PARA lines 91-92 |
| 5 | PF3 key pressed | `EIBAID = DFHPF3` | Set `CDEMO-TO-PROGRAM` to `COADM01C` and transfer via XCTL (return to admin menu) | MAIN-PARA lines 93-95 |
| 6 | PF4 key pressed | `EIBAID = DFHPF4` | Clear all input fields and re-send blank user-add screen | MAIN-PARA lines 96-97 |
| 7 | Any other AID key | `EIBAID = OTHER` | Set error flag ON, set cursor to First Name field, display `CCDA-MSG-INVALID-KEY` message, re-send screen | MAIN-PARA lines 98-102 |

### Input Validation (PROCESS-ENTER-KEY)

Validation is sequential (EVALUATE TRUE with fall-through on first match). The first failing field stops validation; subsequent fields are not checked.

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 8 | First Name is mandatory | `FNAMEI OF COUSR1AI = SPACES OR LOW-VALUES` | Set error flag ON, display message `'First Name can NOT be empty...'`, set cursor to First Name field, re-send screen | PROCESS-ENTER-KEY lines 118-123 |
| 9 | Last Name is mandatory | `LNAMEI OF COUSR1AI = SPACES OR LOW-VALUES` | Set error flag ON, display message `'Last Name can NOT be empty...'`, set cursor to Last Name field, re-send screen | PROCESS-ENTER-KEY lines 124-129 |
| 10 | User ID is mandatory | `USERIDI OF COUSR1AI = SPACES OR LOW-VALUES` | Set error flag ON, display message `'User ID can NOT be empty...'`, set cursor to User ID field, re-send screen | PROCESS-ENTER-KEY lines 130-135 |
| 11 | Password is mandatory | `PASSWDI OF COUSR1AI = SPACES OR LOW-VALUES` | Set error flag ON, display message `'Password can NOT be empty...'`, set cursor to Password field, re-send screen | PROCESS-ENTER-KEY lines 136-141 |
| 12 | User Type is mandatory | `USRTYPEI OF COUSR1AI = SPACES OR LOW-VALUES` | Set error flag ON, display message `'User Type can NOT be empty...'`, set cursor to User Type field, re-send screen | PROCESS-ENTER-KEY lines 142-147 |
| 13 | All fields present -- proceed to write | `WHEN OTHER` (all five validations passed) | Set cursor to First Name (`MOVE -1 TO FNAMEL`), CONTINUE; then IF NOT ERR-FLG-ON: map input fields to SEC-USER-DATA record and perform WRITE-USER-SEC-FILE | PROCESS-ENTER-KEY lines 148-160 |

Note: No format, length, or value-range validation is applied beyond the mandatory-presence check. User Type is accepted as any non-blank/non-low single character (PIC X(01)); no 88-level constraint enforces 'A' or 'U' at entry time in this program.

Note: `RECEIVE-USRADD-SCREEN` captures RESP/RESP2 into WS-RESP-CD/WS-REAS-CD but does NOT evaluate or branch on those codes -- map receive errors are silently ignored and processing continues with whatever is in COUSR1AI.

### Field Mapping to Security Record

The USRSEC record (SEC-USER-DATA from CSUSR01Y) is 80 bytes total: 8+20+20+8+1+23 bytes (including a 23-byte filler `SEC-USR-FILLER PIC X(23)` that is never populated here and is implicitly initialised to whatever was in working storage). The WRITE uses `LENGTH OF SEC-USER-DATA` dynamically.

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 14 | Map User ID to record key | Validation passed | `USERIDI OF COUSR1AI` (PIC X(08)) → `SEC-USR-ID` (PIC X(08)) -- also the VSAM RIDFLD | PROCESS-ENTER-KEY line 154 |
| 15 | Map First Name to record | Validation passed | `FNAMEI OF COUSR1AI` → `SEC-USR-FNAME` (PIC X(20)) | PROCESS-ENTER-KEY line 155 |
| 16 | Map Last Name to record | Validation passed | `LNAMEI OF COUSR1AI` → `SEC-USR-LNAME` (PIC X(20)) | PROCESS-ENTER-KEY line 156 |
| 17 | Map Password to record | Validation passed | `PASSWDI OF COUSR1AI` → `SEC-USR-PWD` (PIC X(08)) | PROCESS-ENTER-KEY line 157 |
| 18 | Map User Type to record | Validation passed | `USRTYPEI OF COUSR1AI` → `SEC-USR-TYPE` (PIC X(01)) | PROCESS-ENTER-KEY line 158 |
| 19 | Record filler not populated | Always | `SEC-USR-FILLER` (PIC X(23)) is not set before write -- written with residual working-storage content | WRITE-USER-SEC-FILE (implicit) |

### Duplicate User Detection (WRITE-USER-SEC-FILE)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 20 | Successful write | `WS-RESP-CD = DFHRESP(NORMAL)` | Initialise all input fields, set error message colour to green (DFHGREEN), build success message `'User <id> has been added ...'` using STRING, re-send screen | WRITE-USER-SEC-FILE lines 251-259 |
| 21 | Duplicate User ID -- DUPKEY | `WS-RESP-CD = DFHRESP(DUPKEY)` | Set error flag ON, display message `'User ID already exist...'`, set cursor to User ID field, re-send screen | WRITE-USER-SEC-FILE lines 260-266 |
| 22 | Duplicate User ID -- DUPREC | `WS-RESP-CD = DFHRESP(DUPREC)` | Same action as DUPKEY (shares WHEN clause): set error flag ON, display message `'User ID already exist...'`, set cursor to User ID field, re-send screen | WRITE-USER-SEC-FILE lines 260-266 |
| 23 | Any other CICS write error | `WS-RESP-CD = OTHER` | Set error flag ON, display message `'Unable to Add User...'`, set cursor to First Name field, re-send screen. RESP/RESP2 codes are captured in WS-RESP-CD / WS-REAS-CD but not displayed (DISPLAY statement is commented out at line 268) | WRITE-USER-SEC-FILE lines 267-273 |

### Navigation -- Return to Previous Screen

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 24 | Default target program guard | `CDEMO-TO-PROGRAM = LOW-VALUES OR SPACES` at time of XCTL | Default `CDEMO-TO-PROGRAM` to `COSGN00C` before transferring control | RETURN-TO-PREV-SCREEN lines 167-169 |
| 25 | Commarea population before XCTL | Always | Set `CDEMO-FROM-TRANID` = `WS-TRANID` ('CU01'), `CDEMO-FROM-PROGRAM` = `WS-PGMNAME` ('COUSR01C'), `CDEMO-PGM-CONTEXT` = 0 (CDEMO-PGM-ENTER) before XCTL | RETURN-TO-PREV-SCREEN lines 170-174 |
| 26 | User identity NOT propagated | Always | Commented-out code at lines 172-173 (`MOVE WS-USER-ID TO CDEMO-USER-ID` and `MOVE SEC-USR-TYPE TO CDEMO-USER-TYPE`) means user ID and user type are NOT placed in the commarea on navigation away from this screen | RETURN-TO-PREV-SCREEN lines 172-173 (commented out) |

### Screen Clear (PF4)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 27 | PF4 clears all fields | `EIBAID = DFHPF4` | Initialise all five input fields and WS-MESSAGE to SPACES; set cursor to First Name (cursor length = -1); re-send screen (with ERASE, clearing entire terminal) | CLEAR-CURRENT-SCREEN / INITIALIZE-ALL-FIELDS lines 279-295 |

### Screen Send Behaviour

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 28 | Every send erases the terminal | Always (all paths) | EXEC CICS SEND MAP uses ERASE option -- the entire terminal screen is cleared before each map send, not a partial update | SEND-USRADD-SCREEN line 194 |

## Calculations

| Calculation | Formula / Logic | Input Fields | Output Field | Source Location |
| --- | --- | --- | --- | --- |
| Success message construction | STRING literal `'User '` DELIMITED BY SIZE + `SEC-USR-ID` DELIMITED BY SPACE (trims trailing spaces from the 8-char User ID) + literal `' has been added ...'` DELIMITED BY SIZE INTO `WS-MESSAGE` | `SEC-USR-ID` | `WS-MESSAGE` (PIC X(80)) | WRITE-USER-SEC-FILE lines 255-258 |
| Header date formatting | FUNCTION CURRENT-DATE stored in WS-CURDATE-DATA; month (positions 5-6) → WS-CURDATE-MM; day (positions 7-8) → WS-CURDATE-DD; year last 2 digits (WS-CURDATE-YEAR positions 3:2) → WS-CURDATE-YY; assembled into WS-CURDATE-MM-DD-YY (MM/DD/YY format) | `WS-CURDATE-DATA` from FUNCTION CURRENT-DATE | `CURDATEO OF COUSR1AO` | POPULATE-HEADER-INFO lines 216-227 |
| Header time formatting | Current time: hours (WS-CURTIME-HOURS) → WS-CURTIME-HH; minutes (WS-CURTIME-MINUTE) → WS-CURTIME-MM; seconds (WS-CURTIME-SECOND) → WS-CURTIME-SS; assembled into WS-CURTIME-HH-MM-SS (HH:MM:SS format) | `WS-CURDATE-DATA` (time portion, from same FUNCTION CURRENT-DATE call) | `CURTIMEO OF COUSR1AO` | POPULATE-HEADER-INFO lines 229-233 |
| USRSEC record length | LENGTH OF SEC-USER-DATA = 80 bytes (8 + 20 + 20 + 8 + 1 + 23 filler); length and key length passed dynamically to CICS WRITE | `SEC-USER-DATA` structure from CSUSR01Y | CICS WRITE LENGTH / KEYLENGTH parameters | WRITE-USER-SEC-FILE lines 243-245 |

## Error Handling

| Condition | Action | Return Code | Source Location |
| ----------------- | -------------------------- | ----------- | --------------- |
| `EIBCALEN = 0` (no commarea -- session not started) | XCTL to `COSGN00C` (sign-on screen) | n/a | MAIN-PARA lines 78-80 |
| Invalid AID key pressed | Set `WS-ERR-FLG = 'Y'`, display `CCDA-MSG-INVALID-KEY`, re-send screen | n/a | MAIN-PARA lines 99-102 |
| First Name empty | Set `WS-ERR-FLG = 'Y'`, display `'First Name can NOT be empty...'`, cursor to First Name | n/a | PROCESS-ENTER-KEY lines 118-123 |
| Last Name empty | Set `WS-ERR-FLG = 'Y'`, display `'Last Name can NOT be empty...'`, cursor to Last Name | n/a | PROCESS-ENTER-KEY lines 124-129 |
| User ID empty | Set `WS-ERR-FLG = 'Y'`, display `'User ID can NOT be empty...'`, cursor to User ID | n/a | PROCESS-ENTER-KEY lines 130-135 |
| Password empty | Set `WS-ERR-FLG = 'Y'`, display `'Password can NOT be empty...'`, cursor to Password | n/a | PROCESS-ENTER-KEY lines 136-141 |
| User Type empty | Set `WS-ERR-FLG = 'Y'`, display `'User Type can NOT be empty...'`, cursor to User Type | n/a | PROCESS-ENTER-KEY lines 142-147 |
| CICS RECEIVE MAP error | RESP/RESP2 captured in WS-RESP-CD/WS-REAS-CD but NOT evaluated -- receive errors are silently ignored and processing continues with stale/partial COUSR1AI data | n/a (unchecked) | RECEIVE-USRADD-SCREEN lines 203-209 |
| CICS WRITE DUPREC / DUPKEY on USRSEC | Set `WS-ERR-FLG = 'Y'`, display `'User ID already exist...'`, cursor to User ID | DFHRESP(DUPKEY) / DFHRESP(DUPREC) | WRITE-USER-SEC-FILE lines 260-266 |
| Any other CICS WRITE error on USRSEC | Set `WS-ERR-FLG = 'Y'`, display `'Unable to Add User...'`, cursor to First Name. RESP/RESP2 codes are retained in WS-RESP-CD and WS-REAS-CD. Diagnostic DISPLAY is commented out (line 268) | DFHRESP(OTHER) | WRITE-USER-SEC-FILE lines 267-273 |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. MAIN-PARA -- Entry point; initialises error flag (`WS-ERR-FLG = 'N'`) and clears WS-MESSAGE and ERRMSGO
2. MAIN-PARA -- If `EIBCALEN = 0`: RETURN-TO-PREV-SCREEN (XCTL to COSGN00C, no further processing)
3. MAIN-PARA -- If `EIBCALEN > 0`: moves DFHCOMMAREA(1:EIBCALEN) into CARDDEMO-COMMAREA
4. MAIN-PARA -- If first entry (`NOT CDEMO-PGM-REENTER`): sets context to REENTER, initialises map to LOW-VALUES, sends initial blank screen via SEND-USRADD-SCREEN
5. MAIN-PARA -- If re-entry: calls RECEIVE-USRADD-SCREEN then dispatches on EIBAID
6. RECEIVE-USRADD-SCREEN -- EXEC CICS RECEIVE MAP('COUSR1A') MAPSET('COUSR01') INTO(COUSR1AI); response captured in WS-RESP-CD / WS-REAS-CD but NOT evaluated
7. PROCESS-ENTER-KEY (on DFHENTER) -- Sequential EVALUATE TRUE validates five mandatory fields; first failure sends screen and sets error flag; stops further validation
8. PROCESS-ENTER-KEY -- If no error (`NOT ERR-FLG-ON`): maps input fields to SEC-USER-DATA record, then performs WRITE-USER-SEC-FILE
9. WRITE-USER-SEC-FILE -- EXEC CICS WRITE DATASET('USRSEC') FROM(SEC-USER-DATA) keyed by SEC-USR-ID with dynamic LENGTH and KEYLENGTH; evaluates WS-RESP-CD for NORMAL / DUPKEY / DUPREC / OTHER
10. WRITE-USER-SEC-FILE (NORMAL) -- Performs INITIALIZE-ALL-FIELDS then builds green success message via STRING, then performs SEND-USRADD-SCREEN
11. RETURN-TO-PREV-SCREEN (on DFHPF3) -- Sets commarea routing fields (FROM-TRANID, FROM-PROGRAM, PGM-CONTEXT=0), EXEC CICS XCTL to COADM01C
12. CLEAR-CURRENT-SCREEN (on DFHPF4) -- Performs INITIALIZE-ALL-FIELDS then SEND-USRADD-SCREEN with blank fields
13. SEND-USRADD-SCREEN -- Performs POPULATE-HEADER-INFO to fill title/date/time, moves WS-MESSAGE to ERRMSGO, then EXEC CICS SEND MAP with ERASE and CURSOR
14. POPULATE-HEADER-INFO -- Moves FUNCTION CURRENT-DATE to working storage; assembles MM-DD-YY and HH-MM-SS strings for display; moves transaction ID and program name to header fields
15. INITIALIZE-ALL-FIELDS -- Clears USERIDI, FNAMEI, LNAMEI, PASSWDI, USRTYPEI, WS-MESSAGE to SPACES; sets cursor length to -1 (positions cursor on First Name)
16. MAIN-PARA -- Unconditional EXEC CICS RETURN TRANSID('CU01') COMMAREA(CARDDEMO-COMMAREA) -- pseudo-conversational return at end of every path
