---
type: business-rules
program: COUSR03C
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
- COUSR03
- CSDAT01Y
- CSMSG01Y
- CSUSR01Y
reads:
- USRSEC
writes: []
db_tables: []
transactions:
- CU03
mq_queues: []
---

# COUSR03C -- Business Rules

## Program Purpose

COUSR03C is an online CICS COBOL program that implements the user deletion function for the CardDemo application. It presents a confirmation screen (map COUSR3A in mapset COUSR03) pre-populated with user details read from the USRSEC VSAM file. The operator must first look up a user by entering a User ID (ENTER key), review the displayed first name, last name, and user type, then explicitly press PF5 to confirm and execute the deletion. The program is invoked by COUSR00C (the user administration menu) and returns control to the calling program or to COADM01C via CICS XCTL.

## Input / Output

| Direction | Resource  | Type | Description                                                                     |
| --------- | --------- | ---- | ------------------------------------------------------------------------------- |
| IN        | USRSEC    | CICS | VSAM keyed file; read with UPDATE lock to retrieve user record for confirmation |
| OUT       | USRSEC    | CICS | VSAM keyed file; DELETE issued after READ UPDATE to remove the user record      |
| IN        | COUSR3AI  | CICS | BMS map input: User ID field (USRIDINI) entered by operator                    |
| OUT       | COUSR3AO  | CICS | BMS map output: confirmation screen showing FNAME, LNAME, USRTYPE, error msgs   |
| IN/OUT    | CARDDEMO-COMMAREA | CICS | Communication area passed on RETURN and XCTL; carries program routing context |

## Business Rules

### Session Initialisation

| #  | Rule                              | Condition                                         | Action                                                                                     | Source Location         |
| -- | --------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------ | ----------------------- |
| 1  | No commarea -- redirect to signon | `EIBCALEN = 0`                                    | Set `CDEMO-TO-PROGRAM = 'COSGN00C'`, XCTL to signon program via RETURN-TO-PREV-SCREEN     | MAIN-PARA (line 90-92)  |
| 2  | Error flag initialised off        | Always on entry                                   | `SET ERR-FLG-OFF TO TRUE` (WS-ERR-FLG = 'N'); message area cleared to SPACES             | MAIN-PARA (line 84-87)  |
| 3  | Commarea present: first entry     | `EIBCALEN > 0` AND `NOT CDEMO-PGM-REENTER` (CDEMO-PGM-CONTEXT = 0) | Copy commarea, set CDEMO-PGM-REENTER=1, clear screen to LOW-VALUES, set cursor on USRIDIN | MAIN-PARA (line 95-105) |
| 4  | Pre-selected user from list       | First entry AND `CDEMO-CU03-USR-SELECTED NOT = SPACES AND LOW-VALUES` | Move selected user ID to USRIDINI, immediately PERFORM PROCESS-ENTER-KEY to pre-load data, then PERFORM SEND-USRDEL-SCREEN unconditionally | MAIN-PARA (line 99-105) |

### Key Routing (AID Dispatch)

| #  | Rule                    | Condition              | Action                                                                                                 | Source Location          |
| -- | ----------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------ |
| 5  | ENTER key -- look up user | `EIBAID = DFHENTER`  | PERFORM PROCESS-ENTER-KEY: validate User ID, read USRSEC, display user details for confirmation       | MAIN-PARA (line 109-110) |
| 6  | PF3 -- return to caller | `EIBAID = DFHPF3`     | If `CDEMO-FROM-PROGRAM` is spaces/low-values, go to 'COADM01C'; else go to `CDEMO-FROM-PROGRAM`; XCTL | MAIN-PARA (line 111-118) |
| 7  | PF4 -- clear screen     | `EIBAID = DFHPF4`     | PERFORM CLEAR-CURRENT-SCREEN: reinitialise all fields and redisplay empty form                        | MAIN-PARA (line 119-120) |
| 8  | PF5 -- confirm delete   | `EIBAID = DFHPF5`     | PERFORM DELETE-USER-INFO: validate User ID, read USRSEC UPDATE, issue CICS DELETE                     | MAIN-PARA (line 121-122) |
| 9  | PF12 -- go to admin menu | `EIBAID = DFHPF12`   | Set `CDEMO-TO-PROGRAM = 'COADM01C'`, XCTL to admin menu                                              | MAIN-PARA (line 123-125) |
| 10 | Any other key -- invalid | `WHEN OTHER`          | Set ERR-FLG-ON ('Y'), move `CCDA-MSG-INVALID-KEY` to WS-MESSAGE, redisplay screen                    | MAIN-PARA (line 126-129) |

### Validation -- User ID (PROCESS-ENTER-KEY)

| #  | Rule                         | Condition                                                    | Action                                                                                                   | Source Location                  |
| -- | ---------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- | -------------------------------- |
| 11 | User ID is mandatory         | `USRIDINI OF COUSR3AI = SPACES OR LOW-VALUES`                | Set ERR-FLG-ON, move 'User ID can NOT be empty...' to WS-MESSAGE, set cursor on USRIDIN, redisplay screen | PROCESS-ENTER-KEY (lines 145-150) |
| 12 | Valid User ID -- read record | `WHEN OTHER` (User ID not empty) AND `NOT ERR-FLG-ON`        | Clear FNAME/LNAME/USRTYPE fields, move USRIDINI to SEC-USR-ID, PERFORM READ-USER-SEC-FILE               | PROCESS-ENTER-KEY (lines 151-162) |
| 13 | Display user after read      | `NOT ERR-FLG-ON` after READ-USER-SEC-FILE returns normally   | Move SEC-USR-FNAME, SEC-USR-LNAME, SEC-USR-TYPE to screen fields, send confirmation screen              | PROCESS-ENTER-KEY (lines 164-169) |

### Validation -- User ID (DELETE-USER-INFO)

| #  | Rule                            | Condition                                             | Action                                                                                                        | Source Location                   |
| -- | ------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| 14 | User ID is mandatory before delete | `USRIDINI OF COUSR3AI = SPACES OR LOW-VALUES`      | Set ERR-FLG-ON, move 'User ID can NOT be empty...' to WS-MESSAGE, set cursor on USRIDIN, redisplay screen    | DELETE-USER-INFO (lines 177-182)  |
| 15 | Proceed only if no error at entry | `NOT ERR-FLG-ON` evaluated once before both PERFORMs | Move USRIDINI to SEC-USR-ID, PERFORM READ-USER-SEC-FILE then PERFORM DELETE-USER-SEC-FILE. **Critical:** the guard is evaluated only once at line 188; if READ-USER-SEC-FILE subsequently sets ERR-FLG-ON (NOTFND or OTHER), DELETE-USER-SEC-FILE still executes -- see bug note below | DELETE-USER-INFO (lines 188-192)  |

### Program Navigation

| #  | Rule                                   | Condition                                               | Action                                                                                         | Source Location                    |
| -- | -------------------------------------- | ------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ---------------------------------- |
| 16 | Default return target if none set      | `CDEMO-TO-PROGRAM = LOW-VALUES OR SPACES`               | Set `CDEMO-TO-PROGRAM = 'COSGN00C'` as fallback                                               | RETURN-TO-PREV-SCREEN (line 199-200) |
| 17 | Stamp from-program on XCTL             | Always before XCTL                                      | Move WS-TRANID ('CU03') to CDEMO-FROM-TRANID, WS-PGMNAME ('COUSR03C') to CDEMO-FROM-PROGRAM   | RETURN-TO-PREV-SCREEN (lines 202-203) |
| 18 | Clear program context on navigate      | Always before XCTL                                      | Move ZEROS to CDEMO-PGM-CONTEXT (resets to CDEMO-PGM-ENTER state for target program)          | RETURN-TO-PREV-SCREEN (line 204)   |

### USRSEC File Read

| #  | Rule                                | Condition                   | Action                                                                                                          | Source Location                    |
| -- | ----------------------------------- | --------------------------- | --------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| 19 | Read with UPDATE lock               | EXEC CICS READ ... UPDATE   | Record locked for update; intent is to hold lock before issuing DELETE; key is SEC-USR-ID (8-byte user ID)     | READ-USER-SEC-FILE (lines 269-278) |
| 20 | Read success -- prompt for PF5      | `DFHRESP(NORMAL)`           | Move 'Press PF5 key to delete this user ...' to WS-MESSAGE in neutral colour (DFHNEUTR); PERFORM SEND-USRDEL-SCREEN unconditionally from within READ-USER-SEC-FILE. Note: line 282 contains a dead `CONTINUE` statement before the MOVE that has no effect on behaviour | READ-USER-SEC-FILE (lines 281-286) |
| 21 | User not found on read              | `DFHRESP(NOTFND)`           | Set ERR-FLG-ON, move 'User ID NOT found...' to WS-MESSAGE, set cursor on USRIDIN, redisplay screen            | READ-USER-SEC-FILE (lines 287-292) |
| 22 | Unexpected CICS error on read       | `WHEN OTHER`                | DISPLAY response codes (RESP/REAS) to SYSOUT, set ERR-FLG-ON, move 'Unable to lookup User...' to WS-MESSAGE, set cursor on FNAME, redisplay screen | READ-USER-SEC-FILE (lines 293-299) |

### USRSEC File Delete

| #  | Rule                                | Condition                   | Action                                                                                                                         | Source Location                      |
| -- | ----------------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------ |
| 23 | Delete relies on prior READ UPDATE  | EXEC CICS DELETE (no RIDFLD) | DELETE issued without RIDFLD -- relies on the file position established by the prior CICS READ ... UPDATE on the same task    | DELETE-USER-SEC-FILE (lines 307-311) |
| 24 | Delete success -- confirmation msg  | `DFHRESP(NORMAL)`           | PERFORM INITIALIZE-ALL-FIELDS; move SPACES to WS-MESSAGE; STRING 'User ' + SEC-USR-ID (trimmed by SPACE) + ' has been deleted ...' into WS-MESSAGE; set colour DFHGREEN; redisplay screen | DELETE-USER-SEC-FILE (lines 314-322) |
| 25 | User not found on delete            | `DFHRESP(NOTFND)`           | Set ERR-FLG-ON, move 'User ID NOT found...' to WS-MESSAGE, set cursor on USRIDIN, redisplay screen                           | DELETE-USER-SEC-FILE (lines 323-328) |
| 26 | Unexpected CICS error on delete     | `WHEN OTHER`                | DISPLAY response codes (RESP/REAS) to SYSOUT, set ERR-FLG-ON, move 'Unable to Update User...' to WS-MESSAGE, set cursor on FNAME, redisplay screen | DELETE-USER-SEC-FILE (lines 329-335) |

### Screen Initialisation

| #  | Rule                               | Condition     | Action                                                                                                       | Source Location                    |
| -- | ---------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------- |
| 27 | PF4 clears all input fields        | `EIBAID = DFHPF4` | INITIALIZE-ALL-FIELDS: set USRIDINL=-1 (cursor), blank USRIDINI, FNAMEI, LNAMEI, USRTYPEI, WS-MESSAGE     | CLEAR-CURRENT-SCREEN (lines 341-344) / INITIALIZE-ALL-FIELDS (lines 349-356) |
| 28 | Screen reset after successful delete | After DFHRESP(NORMAL) on DELETE | Same INITIALIZE-ALL-FIELDS called to blank all fields ready for next deletion                          | DELETE-USER-SEC-FILE (line 315)    |

## Calculations

| Calculation         | Formula / Logic                                                                                              | Input Fields             | Output Field | Source Location                      |
| ------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------ | ------------ | ------------------------------------ |
| Confirmation message | STRING 'User ' DELIMITED BY SIZE + SEC-USR-ID DELIMITED BY SPACE (trailing-space trim) + ' has been deleted ...' DELIMITED BY SIZE INTO WS-MESSAGE | SEC-USR-ID (PIC X(08)) | WS-MESSAGE (PIC X(80)) | DELETE-USER-SEC-FILE (lines 318-321) |
| Date formatting     | FUNCTION CURRENT-DATE broken into MM, DD, YY(3:2) components and assembled into WS-CURDATE-MM-DD-YY         | FUNCTION CURRENT-DATE    | CURDATEO OF COUSR3AO | POPULATE-HEADER-INFO (lines 245-256) |
| Time formatting     | WS-CURTIME-HOURS, WS-CURTIME-MINUTE, WS-CURTIME-SECOND assembled into WS-CURTIME-HH-MM-SS                   | FUNCTION CURRENT-DATE    | CURTIMEO OF COUSR3AO | POPULATE-HEADER-INFO (lines 258-262) |

## Error Handling

| Condition                                    | Action                                                                        | Return Code              | Source Location                      |
| -------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------ | ------------------------------------ |
| EIBCALEN = 0 (no commarea on entry)          | XCTL to 'COSGN00C' (signon); program cannot run without session context       | --                       | MAIN-PARA (lines 90-92)              |
| Unrecognised AID key pressed                 | ERR-FLG-ON, display CCDA-MSG-INVALID-KEY, redisplay screen                   | WS-ERR-FLG = 'Y'         | MAIN-PARA (lines 126-129)            |
| User ID empty (ENTER or PF5)                 | ERR-FLG-ON, display 'User ID can NOT be empty...', cursor on USRIDIN         | WS-ERR-FLG = 'Y'         | PROCESS-ENTER-KEY / DELETE-USER-INFO |
| CICS RECEIVE MAP error                       | Response codes stored in WS-RESP-CD / WS-REAS-CD but never evaluated; errors silently ignored | WS-ERR-FLG remains 'N' | RECEIVE-USRDEL-SCREEN (lines 232-238) |
| CICS READ NOTFND on USRSEC                   | ERR-FLG-ON, display 'User ID NOT found...', cursor on USRIDIN                | WS-ERR-FLG = 'Y'         | READ-USER-SEC-FILE (lines 287-292)   |
| CICS READ OTHER error on USRSEC              | DISPLAY RESP/REAS codes, ERR-FLG-ON, display 'Unable to lookup User...'      | WS-ERR-FLG = 'Y'         | READ-USER-SEC-FILE (lines 293-299)   |
| CICS DELETE NOTFND on USRSEC                 | ERR-FLG-ON, display 'User ID NOT found...', cursor on USRIDIN                | WS-ERR-FLG = 'Y'         | DELETE-USER-SEC-FILE (lines 323-328) |
| CICS DELETE OTHER error on USRSEC            | DISPLAY RESP/REAS codes, ERR-FLG-ON, display 'Unable to Update User...'      | WS-ERR-FLG = 'Y'         | DELETE-USER-SEC-FILE (lines 329-335) |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. MAIN-PARA -- entry point; initialises flags; routes on EIBCALEN and CDEMO-PGM-CONTEXT
2. RETURN-TO-PREV-SCREEN -- called when EIBCALEN=0; XCTL to signon before any processing
3. RECEIVE-USRDEL-SCREEN -- reads BMS map COUSR3A/COUSR03 into COUSR3AI on re-entry
4. PROCESS-ENTER-KEY -- validates User ID not empty; calls READ-USER-SEC-FILE; displays record for confirmation
5. DELETE-USER-INFO -- validates User ID not empty; calls READ-USER-SEC-FILE then DELETE-USER-SEC-FILE
6. CLEAR-CURRENT-SCREEN -- calls INITIALIZE-ALL-FIELDS then SEND-USRDEL-SCREEN
7. RETURN-TO-PREV-SCREEN -- XCTL to CDEMO-FROM-PROGRAM or 'COADM01C' on PF3/PF12
8. READ-USER-SEC-FILE -- EXEC CICS READ DATASET('USRSEC') INTO(SEC-USER-DATA) ... UPDATE; evaluates DFHRESP
9. DELETE-USER-SEC-FILE -- EXEC CICS DELETE DATASET('USRSEC') (position-based, no RIDFLD); evaluates DFHRESP
10. POPULATE-HEADER-INFO -- formats current date/time, moves title constants and transaction/program names to output map
11. SEND-USRDEL-SCREEN -- calls POPULATE-HEADER-INFO; EXEC CICS SEND MAP ERASE CURSOR
12. INITIALIZE-ALL-FIELDS -- blanks all screen input fields and message area; sets cursor length to -1
13. EXEC CICS RETURN TRANSID('CU03') COMMAREA(CARDDEMO-COMMAREA) -- terminal of MAIN-PARA; suspends and passes control back to CICS, re-driving CU03 on next operator input

**Bug: DELETE executes even when READ fails (DELETE-USER-INFO).** At lines 188-192, both PERFORM READ-USER-SEC-FILE and PERFORM DELETE-USER-SEC-FILE are inside a single `IF NOT ERR-FLG-ON` block. The condition is evaluated once on entry. If READ-USER-SEC-FILE subsequently sets ERR-FLG-ON (due to NOTFND or an unexpected error), the `IF` block has already been entered and DELETE-USER-SEC-FILE still executes. Because the DELETE is position-based (no RIDFLD), CICS will attempt a DELETE on whatever file position is current for the task -- with no prior successful READ UPDATE, this results in a NOTFND or INVREQ condition, which DELETE-USER-SEC-FILE handles by setting ERR-FLG-ON and displaying 'User ID NOT found...'. The user sees an error message and no data is corrupted, but the DELETE CICS call is still issued unnecessarily on every failed READ.

**Double SEND on ENTER key (confirmed from source).** When the operator presses ENTER and the user lookup succeeds, SEND-USRDEL-SCREEN is called twice within the same CICS task. First call: inside READ-USER-SEC-FILE (lines 283-286) with WS-MESSAGE = 'Press PF5 key to delete this user ...' and blank FNAME/LNAME/USRTYPE (cleared by PROCESS-ENTER-KEY at lines 157-159 before the READ). Second call: back in PROCESS-ENTER-KEY (lines 164-169) after READ returns, with FNAME/LNAME/USRTYPE now populated from SEC-USER-DATA. Only the second SEND is visible to the operator (the first is overwritten by the second ERASE before the terminal refreshes). This is a redundant SEND that causes an unnecessary CICS BMS write on every successful user lookup.

**Double SEND on first entry with pre-selected user.** When COUSR00C sets CDEMO-CU03-USR-SELECTED to a non-blank/non-low-value user ID, MAIN-PARA on first entry performs PROCESS-ENTER-KEY (line 103) -- which itself calls SEND-USRDEL-SCREEN internally -- and then unconditionally performs SEND-USRDEL-SCREEN again at line 105. This produces a second redundant BMS SEND (in addition to those already described for the ENTER key path) before the terminal is released to the operator.

**RECEIVE-USRDEL-SCREEN error response not checked.** EXEC CICS RECEIVE MAP at lines 232-238 specifies RESP(WS-RESP-CD) RESP2(WS-REAS-CD), but there is no subsequent IF or EVALUATE on these response codes. If the BMS receive fails (e.g., MAPFAIL, LENGERR), the program continues silently with whatever data was already in COUSR3AI, potentially processing stale or uninitialised input.

**Unused WS-USR-MODIFIED flag.** WS-USR-MODIFIED (88-levels: USR-MODIFIED-YES = 'Y', USR-MODIFIED-NO = 'N') is initialised to USR-MODIFIED-NO at line 85 but is never set to USR-MODIFIED-YES anywhere in the PROCEDURE DIVISION. This flag has no effect on program behaviour and appears to be dead code left from a shared template or a prior version.

**Dead CONTINUE in READ-USER-SEC-FILE NORMAL branch.** At line 282, the DFHRESP(NORMAL) branch begins with `CONTINUE` before the MOVE statement. This statement is syntactically valid but logically inert. It has no effect on program behaviour but indicates either a template residue or that prior code in this branch was removed without cleanup.

**Lock held between ENTER and next CICS task.** When PROCESS-ENTER-KEY is triggered by the ENTER key, READ-USER-SEC-FILE acquires an UPDATE lock on the USRSEC record. Control then returns to MAIN-PARA, which issues EXEC CICS RETURN (line 134). CICS releases file locks at task end, so the lock is released when the RETURN completes -- it is not held across the inter-task interval. This means when the operator presses PF5, a fresh READ UPDATE is issued to re-lock the record before DELETE. There is no concurrency window issue from the ENTER key's READ UPDATE, but the lock acquisition on ENTER is entirely unnecessary for display purposes.
