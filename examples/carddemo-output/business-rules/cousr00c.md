---
type: business-rules
program: COUSR00C
program_type: online
status: draft
confidence: high
last_pass: 5
calls: []
called_by: []
uses_copybooks:
- COCOM01Y
- COTTL01Y
- COUSR00
- CSDAT01Y
- CSMSG01Y
- CSUSR01Y
reads:
- USRSEC
writes: []
db_tables: []
transactions:
- CU00
mq_queues: []
---

# COUSR00C -- Business Rules

## Program Purpose

COUSR00C is a CICS online program that displays a paginated list of users from the USRSEC security file (up to 10 users per page). It allows an administrator to browse users forward (PF8) and backward (PF7), optionally filter the list by starting user ID, and select a user for update (U) or delete (D) by typing a selection code next to the user's row. The program transfers control to COUSR02C for updates or COUSR03C for deletes, and returns to COADM01C on PF3.

## Input / Output

| Direction | Resource | Type | Description |
| --------- | -------- | ---- | ----------- |
| IN        | USRSEC   | CICS VSAM KSDS (STARTBR/READNEXT/READPREV) | User security file; keyed on SEC-USR-ID (8 chars) |
| IN        | COUSR0A (map COUSR0A, mapset COUSR00) | CICS BMS Screen | User list screen -- receives user ID filter and row selection codes |
| OUT       | COUSR0A (map COUSR0A, mapset COUSR00) | CICS BMS Screen | User list screen -- sends paginated user list |
| IN/OUT    | CARDDEMO-COMMAREA | CICS COMMAREA | Cross-program communication area passed on XCTL and RETURN |

## Business Rules

### Entry and First-Time Initialisation

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 1 | No commarea = unauthenticated entry | `EIBCALEN = 0` | Set CDEMO-TO-PROGRAM to 'COSGN00C', perform RETURN-TO-PREV-SCREEN (XCTL to sign-on) | MAIN-PARA lines 110-112 |
| 2 | First entry (program not yet re-entered) | `NOT CDEMO-PGM-REENTER` (CDEMO-PGM-CONTEXT = 0) | Set CDEMO-PGM-REENTER (value 1), initialise output map to LOW-VALUES, perform PROCESS-ENTER-KEY (which internally calls PROCESS-PAGE-FORWARD and SEND-USRLST-SCREEN), then perform SEND-USRLST-SCREEN again explicitly -- note this results in two send calls on first entry | MAIN-PARA lines 115-119 |
| 3 | Subsequent entry (re-enter flag set) | `CDEMO-PGM-REENTER` (CDEMO-PGM-CONTEXT = 1) | Receive screen, then dispatch on EIBAID | MAIN-PARA lines 121-137 |

### Key Handling / Routing

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 4 | Enter key -- process selection and list | `EIBAID = DFHENTER` | Perform PROCESS-ENTER-KEY | MAIN-PARA lines 123-124 |
| 5 | PF3 -- return to admin menu | `EIBAID = DFHPF3` | Set CDEMO-TO-PROGRAM to 'COADM01C', perform RETURN-TO-PREV-SCREEN (XCTL) | MAIN-PARA lines 125-127 |
| 6 | PF7 -- page backward | `EIBAID = DFHPF7` | Perform PROCESS-PF7-KEY | MAIN-PARA lines 128-129 |
| 7 | PF8 -- page forward | `EIBAID = DFHPF8` | Perform PROCESS-PF8-KEY | MAIN-PARA lines 130-131 |
| 8 | Any other key is invalid | `WHEN OTHER` (EIBAID not in above set) | Set WS-ERR-FLG to 'Y', set cursor on USRIDINL, display message CCDA-MSG-INVALID-KEY ('Invalid key pressed. Please see below...'), perform SEND-USRLST-SCREEN | MAIN-PARA lines 132-136 |

### User Selection Validation (PROCESS-ENTER-KEY)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 9 | Detect selected row -- rows 1-10 checked in priority order | `SEL0001I ... SEL0010I NOT = SPACES AND LOW-VALUES` | First non-blank selection field wins (rows evaluated top-to-bottom); its value is captured into CDEMO-CU00-USR-SEL-FLG and the corresponding USRIDnn into CDEMO-CU00-USR-SELECTED | PROCESS-ENTER-KEY lines 151-185 |
| 10 | No row selected | `WHEN OTHER` (all SEL fields are spaces/low-values) | CDEMO-CU00-USR-SEL-FLG set to SPACES, CDEMO-CU00-USR-SELECTED set to SPACES -- no XCTL performed | PROCESS-ENTER-KEY lines 182-184 |
| 11 | Selection 'U' or 'u' -- update user | `CDEMO-CU00-USR-SEL-FLG = 'U' OR 'u'` (case-insensitive) AND both flag and selected ID are non-blank | Set CDEMO-TO-PROGRAM to 'COUSR02C', set CDEMO-FROM-TRANID to WS-TRANID ('CU00'), set CDEMO-FROM-PROGRAM to WS-PGMNAME ('COUSR00C'), set CDEMO-PGM-CONTEXT to 0, XCTL to COUSR02C passing commarea | PROCESS-ENTER-KEY lines 190-199 |
| 12 | Selection 'D' or 'd' -- delete user | `CDEMO-CU00-USR-SEL-FLG = 'D' OR 'd'` (case-insensitive) AND both flag and selected ID are non-blank | Set CDEMO-TO-PROGRAM to 'COUSR03C', set CDEMO-FROM-TRANID to WS-TRANID ('CU00'), set CDEMO-FROM-PROGRAM to WS-PGMNAME ('COUSR00C'), set CDEMO-PGM-CONTEXT to 0, XCTL to COUSR03C passing commarea | PROCESS-ENTER-KEY lines 200-209 |
| 13 | Invalid selection code | `WHEN OTHER` (selection is non-blank but not U/u/D/d) | Move literal 'Invalid selection. Valid values are U and D' to WS-MESSAGE, set cursor on USRIDINL | PROCESS-ENTER-KEY lines 210-214 |
| 14 | User ID filter: blank filter starts list from beginning | `USRIDINI OF COUSR0AI = SPACES OR LOW-VALUES` | Move LOW-VALUES to SEC-USR-ID (browse will start at the first record in key sequence) | PROCESS-ENTER-KEY lines 218-219 |
| 15 | User ID filter: non-blank filter starts from entered ID | `USRIDINI OF COUSR0AI NOT = SPACES/LOW-VALUES` | Move USRIDINI to SEC-USR-ID; STARTBR uses EQUAL positioning (GTEQ is commented out in STARTBR-USER-SEC-FILE) -- if the exact ID is not found, NOTFND is returned | PROCESS-ENTER-KEY lines 220-222 |
| 16 | After processing, reset page counter and load page | Always after selection/filter logic | CDEMO-CU00-PAGE-NUM set to 0, PROCESS-PAGE-FORWARD performed | PROCESS-ENTER-KEY lines 227-228 |
| 17 | Clear user ID input field on successful load | `NOT ERR-FLG-ON` after PROCESS-PAGE-FORWARD | Move SPACE to USRIDINO of COUSR0AO | PROCESS-ENTER-KEY lines 230-232 |

### Page Backward Navigation (PROCESS-PF7-KEY)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 18 | Set browse start key for backward page (blank anchor) | `CDEMO-CU00-USRID-FIRST = SPACES OR LOW-VALUES` | Move LOW-VALUES to SEC-USR-ID | PROCESS-PF7-KEY lines 239-240 |
| 19 | Set browse start key for backward page (non-blank anchor) | `CDEMO-CU00-USRID-FIRST NOT = SPACES/LOW-VALUES` | Move CDEMO-CU00-USRID-FIRST (first user ID on current page) to SEC-USR-ID | PROCESS-PF7-KEY lines 241-242 |
| 20 | Force NEXT-PAGE-YES before backward navigation | Unconditional | SET NEXT-PAGE-YES TO TRUE (ensures PROCESS-PAGE-BACKWARD can decrement page counter correctly) | PROCESS-PF7-KEY line 245 |
| 21 | Already at first page -- no backward navigation | `CDEMO-CU00-PAGE-NUM <= 1` (ELSE branch of `IF CDEMO-CU00-PAGE-NUM > 1`) | Display message 'You are already at the top of the page...', set SEND-ERASE-NO, perform SEND-USRLST-SCREEN without erasing | PROCESS-PF7-KEY lines 250-254 |
| 22 | Page number > 1 -- backward navigation allowed | `CDEMO-CU00-PAGE-NUM > 1` | Perform PROCESS-PAGE-BACKWARD | PROCESS-PF7-KEY lines 248-249 |

### Page Forward Navigation (PROCESS-PF8-KEY)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 23 | Set browse start key for forward page (blank anchor) | `CDEMO-CU00-USRID-LAST = SPACES OR LOW-VALUES` | Move HIGH-VALUES to SEC-USR-ID | PROCESS-PF8-KEY lines 262-263 |
| 24 | Set browse start key for forward page (non-blank anchor) | `CDEMO-CU00-USRID-LAST NOT = SPACES/LOW-VALUES` | Move CDEMO-CU00-USRID-LAST (last user ID on current page) to SEC-USR-ID | PROCESS-PF8-KEY lines 264-265 |
| 25 | Already at last page -- no forward navigation | `NEXT-PAGE-YES = FALSE` (CDEMO-CU00-NEXT-PAGE-FLG = 'N') | Display message 'You are already at the bottom of the page...', set SEND-ERASE-NO, perform SEND-USRLST-SCREEN without erasing | PROCESS-PF8-KEY lines 272-276 |
| 26 | More pages exist -- forward navigation allowed | `NEXT-PAGE-YES` (CDEMO-CU00-NEXT-PAGE-FLG = 'Y') | Perform PROCESS-PAGE-FORWARD | PROCESS-PF8-KEY lines 270-271 |

### Page-Forward Load Logic (PROCESS-PAGE-FORWARD)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 27 | Only proceed if file browse started successfully | `NOT ERR-FLG-ON` after STARTBR-USER-SEC-FILE | Continue to read records; else fall through with error already displayed by STARTBR-USER-SEC-FILE | PROCESS-PAGE-FORWARD line 286 |
| 28 | Skip one record on PF8 invocations | `EIBAID NOT = DFHENTER AND DFHPF7 AND DFHPF3` (i.e. EIBAID = DFHPF8 or other non-standard) | Perform READNEXT-USER-SEC-FILE once to advance past the current anchor record (the last ID on the previous page) | PROCESS-PAGE-FORWARD lines 288-290 |
| 29 | Initialise all 10 display rows before loading | `USER-SEC-NOT-EOF AND ERR-FLG-OFF` | PERFORM VARYING WS-IDX FROM 1 BY 1 UNTIL WS-IDX > 10: INITIALIZE-USER-DATA (clears all row fields to SPACES) | PROCESS-PAGE-FORWARD lines 292-296 |
| 30 | Read up to 10 records into display rows | `UNTIL WS-IDX >= 11 OR USER-SEC-EOF OR ERR-FLG-ON` | Starting WS-IDX at 1, repeatedly call READNEXT-USER-SEC-FILE; on each successful read call POPULATE-USER-DATA and increment WS-IDX | PROCESS-PAGE-FORWARD lines 298-306 |
| 31 | Detect next page exists after reading 10 records | `USER-SEC-NOT-EOF AND ERR-FLG-OFF` (after 10-record loop) | Increment CDEMO-CU00-PAGE-NUM by 1; attempt one more READNEXT; if record found SET NEXT-PAGE-YES else SET NEXT-PAGE-NO | PROCESS-PAGE-FORWARD lines 308-316 |
| 32 | Fewer than 10 records returned (partial page) | `NOT (USER-SEC-NOT-EOF AND ERR-FLG-OFF)` after loop | SET NEXT-PAGE-NO; increment CDEMO-CU00-PAGE-NUM by 1 only if at least one record was read (WS-IDX > 1) | PROCESS-PAGE-FORWARD lines 317-322 |
| 33 | Display page number and send screen after forward load | Unconditional (within the `NOT ERR-FLG-ON` guard) | Move CDEMO-CU00-PAGE-NUM to PAGENUMI, move SPACE to USRIDINO, perform SEND-USRLST-SCREEN | PROCESS-PAGE-FORWARD lines 327-329 |

### Page-Backward Load Logic (PROCESS-PAGE-BACKWARD)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 34 | Skip one record on PF7 invocations | `EIBAID NOT = DFHENTER AND DFHPF8` (i.e. EIBAID = DFHPF7 or other non-standard) | Perform READPREV-USER-SEC-FILE once to back up past the current anchor record (the first ID on the current page) | PROCESS-PAGE-BACKWARD lines 342-344 |
| 35 | Initialise all 10 display rows before loading | `USER-SEC-NOT-EOF AND ERR-FLG-OFF` | PERFORM VARYING WS-IDX FROM 1 BY 1 UNTIL WS-IDX > 10: INITIALIZE-USER-DATA (clears all row fields to SPACES) | PROCESS-PAGE-BACKWARD lines 346-350 |
| 36 | Read up to 10 records backward into display rows | Starting WS-IDX at 10; `UNTIL WS-IDX <= 0 OR USER-SEC-EOF OR ERR-FLG-ON` | Call READPREV-USER-SEC-FILE; on each successful read call POPULATE-USER-DATA and decrement WS-IDX by 1; records are filled bottom-up so the page is displayed in ascending key order on screen | PROCESS-PAGE-BACKWARD lines 352-360 |
| 37 | Decrement page counter after backward read | `USER-SEC-NOT-EOF AND ERR-FLG-OFF` AND `NEXT-PAGE-YES` AND `CDEMO-CU00-PAGE-NUM > 1` | SUBTRACT 1 FROM CDEMO-CU00-PAGE-NUM | PROCESS-PAGE-BACKWARD lines 362-367 |
| 38 | Reset to page 1 if page counter cannot go lower | Inner conditions not met (NEXT-PAGE-YES false, or backward extra read returns EOF, or page-num already <= 1) | MOVE 1 TO CDEMO-CU00-PAGE-NUM | PROCESS-PAGE-BACKWARD lines 368-369 |
| 39 | Display page number and send screen after backward load | Unconditional (within the `NOT ERR-FLG-ON` guard) | Move CDEMO-CU00-PAGE-NUM to PAGENUMI, perform SEND-USRLST-SCREEN | PROCESS-PAGE-BACKWARD lines 376-377 |

### Display Population (POPULATE-USER-DATA)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 40 | Row 1 also tracks first visible user ID | `WS-IDX = 1` | SEC-USR-ID copied to both USRID01I OF COUSR0AI and CDEMO-CU00-USRID-FIRST (commarea anchor for PF7 backward navigation) | POPULATE-USER-DATA lines 388-389 |
| 41 | Row 10 also tracks last visible user ID | `WS-IDX = 10` | SEC-USR-ID copied to both USRID10I OF COUSR0AI and CDEMO-CU00-USRID-LAST (commarea anchor for PF8 forward navigation) | POPULATE-USER-DATA lines 434-435 |
| 42 | Each row displays user ID, first name, last name, user type | `WS-IDX = 1..10` | SEC-USR-ID, SEC-USR-FNAME, SEC-USR-LNAME, SEC-USR-TYPE moved to corresponding screen fields USRIDnnI, FNAMEnnI, LNAMEnnI, UTYPEnnI | POPULATE-USER-DATA lines 386-441 |

### Navigation Guard (RETURN-TO-PREV-SCREEN)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 43 | Default destination is sign-on screen | `CDEMO-TO-PROGRAM = LOW-VALUES OR SPACES` | Move 'COSGN00C' to CDEMO-TO-PROGRAM | RETURN-TO-PREV-SCREEN lines 508-510 |
| 44 | Commarea departure metadata always stamped before XCTL | Unconditional | Move WS-TRANID ('CU00') to CDEMO-FROM-TRANID, move WS-PGMNAME ('COUSR00C') to CDEMO-FROM-PROGRAM, move ZEROS to CDEMO-PGM-CONTEXT, then XCTL to CDEMO-TO-PROGRAM passing CARDDEMO-COMMAREA | RETURN-TO-PREV-SCREEN lines 511-517 |

### Screen Send Mode

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 45 | First send uses ERASE to clear terminal | `SEND-ERASE-YES` (WS-SEND-ERASE-FLG = 'Y', the initial value set at program entry) | EXEC CICS SEND MAP('COUSR0A') MAPSET('COUSR00') with ERASE and CURSOR | SEND-USRLST-SCREEN lines 528-535 |
| 46 | Subsequent sends (error/boundary messages) do not erase | `SEND-ERASE-NO` (WS-SEND-ERASE-FLG = 'N', set explicitly before page-boundary or error message sends) | EXEC CICS SEND MAP('COUSR0A') MAPSET('COUSR00') without ERASE, with CURSOR | SEND-USRLST-SCREEN lines 536-543 |

### STARTBR Positioning Behaviour

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 47 | STARTBR uses EQUAL (not GTEQ) key positioning | The GTEQ option is commented out in the STARTBR call | The browse cursor is positioned at the exact SEC-USR-ID value; if that exact key does not exist in USRSEC, CICS returns DFHRESP(NOTFND); there is no automatic positioning to the next greater key | STARTBR-USER-SEC-FILE lines 588-595 |

## Calculations

| Calculation | Formula / Logic | Input Fields | Output Field | Source Location |
| --- | --- | --- | --- | --- |
| Increment page number (full forward page) | `CDEMO-CU00-PAGE-NUM = CDEMO-CU00-PAGE-NUM + 1` (when 10 records read and file not at EOF) | CDEMO-CU00-PAGE-NUM | CDEMO-CU00-PAGE-NUM | PROCESS-PAGE-FORWARD lines 309-310 |
| Increment page number (partial forward page) | `CDEMO-CU00-PAGE-NUM = CDEMO-CU00-PAGE-NUM + 1` (only when WS-IDX > 1, meaning at least one record was read) | CDEMO-CU00-PAGE-NUM, WS-IDX | CDEMO-CU00-PAGE-NUM | PROCESS-PAGE-FORWARD lines 319-321 |
| Increment record index (forward) | `COMPUTE WS-IDX = WS-IDX + 1` | WS-IDX | WS-IDX | PROCESS-PAGE-FORWARD line 304 |
| Decrement record index (backward) | `COMPUTE WS-IDX = WS-IDX - 1` | WS-IDX | WS-IDX | PROCESS-PAGE-BACKWARD line 358 |
| Decrement page number (backward) | `SUBTRACT 1 FROM CDEMO-CU00-PAGE-NUM` | CDEMO-CU00-PAGE-NUM | CDEMO-CU00-PAGE-NUM | PROCESS-PAGE-BACKWARD line 367 |

## Error Handling

| Condition | Action | Return Code | Source Location |
| --- | --- | --- | --- |
| STARTBR returns NOTFND (exact key not found; GTEQ is commented out) | SET USER-SEC-EOF to TRUE; display message 'You are at the top of the page...'; set cursor on USRIDINL; perform SEND-USRLST-SCREEN | DFHRESP(NOTFND) | STARTBR-USER-SEC-FILE lines 600-606 |
| STARTBR returns any other unexpected response | DISPLAY 'RESP:' WS-RESP-CD 'REAS:' WS-REAS-CD to SYSOUT; set WS-ERR-FLG = 'Y' (ERR-FLG-ON); display message 'Unable to lookup User...'; set cursor on USRIDINL; perform SEND-USRLST-SCREEN | DFHRESP(OTHER) | STARTBR-USER-SEC-FILE lines 607-613 |
| READNEXT returns ENDFILE (end of file reached) | SET USER-SEC-EOF to TRUE; display message 'You have reached the bottom of the page...'; set cursor on USRIDINL; perform SEND-USRLST-SCREEN | DFHRESP(ENDFILE) | READNEXT-USER-SEC-FILE lines 634-640 |
| READNEXT returns any other unexpected response | DISPLAY 'RESP:' WS-RESP-CD 'REAS:' WS-REAS-CD to SYSOUT; set WS-ERR-FLG = 'Y'; display message 'Unable to lookup User...'; set cursor on USRIDINL; perform SEND-USRLST-SCREEN | DFHRESP(OTHER) | READNEXT-USER-SEC-FILE lines 641-647 |
| READPREV returns ENDFILE (beginning of file reached) | SET USER-SEC-EOF to TRUE; display message 'You have reached the top of the page...'; set cursor on USRIDINL; perform SEND-USRLST-SCREEN | DFHRESP(ENDFILE) | READPREV-USER-SEC-FILE lines 668-674 |
| READPREV returns any other unexpected response | DISPLAY 'RESP:' WS-RESP-CD 'REAS:' WS-REAS-CD to SYSOUT; set WS-ERR-FLG = 'Y'; display message 'Unable to lookup User...'; set cursor on USRIDINL; perform SEND-USRLST-SCREEN | DFHRESP(OTHER) | READPREV-USER-SEC-FILE lines 675-681 |
| EXEC CICS RECEIVE MAP error (MAPFAIL or other) | No RESP check on RECEIVE -- MAPFAIL and all CICS errors from screen receive are silently ignored; WS-RESP-CD and WS-REAS-CD are populated but never evaluated after RECEIVE | unhandled | RECEIVE-USRLST-SCREEN lines 551-557 |
| EXEC CICS ENDBR error | No RESP clause on ENDBR call -- any CICS error closing the browse cursor is silently discarded | unhandled | ENDBR-USER-SEC-FILE lines 689-691 |
| Invalid attention key pressed | Set WS-ERR-FLG = 'Y'; set cursor on USRIDINL; display CCDA-MSG-INVALID-KEY ('Invalid key pressed. Please see below...'); perform SEND-USRLST-SCREEN | n/a (AID check) | MAIN-PARA lines 132-136 |
| Invalid selection code entered (not U/u/D/d) | Move 'Invalid selection. Valid values are U and D' to WS-MESSAGE; set cursor on USRIDINL | n/a | PROCESS-ENTER-KEY lines 210-214 |
| PF7 pressed but already on page 1 | Move 'You are already at the top of the page...' to WS-MESSAGE; SET SEND-ERASE-NO; perform SEND-USRLST-SCREEN without erase | n/a | PROCESS-PF7-KEY lines 251-254 |
| PF8 pressed but no next page exists (NEXT-PAGE-NO) | Move 'You are already at the bottom of the page...' to WS-MESSAGE; SET SEND-ERASE-NO; perform SEND-USRLST-SCREEN without erase | n/a | PROCESS-PF8-KEY lines 273-276 |

**Code quality note -- vestigial CONTINUE in error handlers:** In all three file I/O paragraphs (STARTBR-USER-SEC-FILE, READNEXT-USER-SEC-FILE, READPREV-USER-SEC-FILE), every non-NORMAL WHEN clause begins with a `CONTINUE` statement immediately before the actual error-handling code. In COBOL, `CONTINUE` within a WHEN block is a no-op -- execution proceeds to the following statements in the same WHEN block -- so the error handling is functional. The `CONTINUE` statements are likely vestiges of stub code that was incrementally filled in. Example at lines 600-602: `WHEN DFHRESP(NOTFND)` / `CONTINUE` / `SET USER-SEC-EOF TO TRUE`. A modernisation effort should remove these dead statements to avoid confusion.

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. MAIN-PARA -- entry point; initialises flags (ERR-FLG-OFF, USER-SEC-NOT-EOF, NEXT-PAGE-NO, SEND-ERASE-YES), clears WS-MESSAGE and ERRMSGO, tests EIBCALEN, dispatches on first-entry vs re-entry
2. RETURN-TO-PREV-SCREEN -- XCTL to COSGN00C when no commarea (unauthenticated)
3. PROCESS-ENTER-KEY -- on first entry or ENTER key: detects row selection (rows 1-10 in order), validates selection code (U/u/D/d), sets browse key from USRIDINI filter, resets page counter to 0, calls PROCESS-PAGE-FORWARD
4. PROCESS-PF7-KEY -- on PF7: sets browse key from CDEMO-CU00-USRID-FIRST, forces NEXT-PAGE-YES, validates page number > 1, calls PROCESS-PAGE-BACKWARD
5. PROCESS-PF8-KEY -- on PF8: sets browse key from CDEMO-CU00-USRID-LAST, checks NEXT-PAGE-YES flag, calls PROCESS-PAGE-FORWARD
6. PROCESS-PAGE-FORWARD -- calls STARTBR-USER-SEC-FILE; conditionally skips one record (PF8 path); initialises 10 rows; reads up to 10 records forward via READNEXT loop; probes for an 11th record to set NEXT-PAGE flag; calls ENDBR-USER-SEC-FILE; moves page number to screen; sends screen
7. PROCESS-PAGE-BACKWARD -- calls STARTBR-USER-SEC-FILE; conditionally skips one record (PF7 path); initialises 10 rows; reads up to 10 records backward via READPREV loop (WS-IDX from 10 down to 1, filling rows bottom-up to maintain ascending display order); probes for one more READPREV to adjust page counter; calls ENDBR-USER-SEC-FILE; moves page number to screen; sends screen
8. STARTBR-USER-SEC-FILE -- EXEC CICS STARTBR DATASET(WS-USRSEC-FILE='USRSEC  ') RIDFLD(SEC-USR-ID) KEYLENGTH(LENGTH OF SEC-USR-ID) with EQUAL positioning (GTEQ commented out); handles NORMAL, NOTFND, OTHER responses
9. READNEXT-USER-SEC-FILE -- EXEC CICS READNEXT DATASET(WS-USRSEC-FILE) INTO(SEC-USER-DATA) RIDFLD(SEC-USR-ID); handles NORMAL, ENDFILE, OTHER responses
10. READPREV-USER-SEC-FILE -- EXEC CICS READPREV DATASET(WS-USRSEC-FILE) INTO(SEC-USER-DATA) RIDFLD(SEC-USR-ID); handles NORMAL, ENDFILE, OTHER responses
11. POPULATE-USER-DATA -- EVALUATE WS-IDX (1-10): maps SEC-USR-ID/FNAME/LNAME/TYPE into screen row fields; for WS-IDX=1 also saves SEC-USR-ID to CDEMO-CU00-USRID-FIRST; for WS-IDX=10 also saves to CDEMO-CU00-USRID-LAST
12. INITIALIZE-USER-DATA -- EVALUATE WS-IDX (1-10): moves SPACES to the four screen row fields (USRID/FNAME/LNAME/UTYPE) for the given index
13. ENDBR-USER-SEC-FILE -- EXEC CICS ENDBR DATASET(WS-USRSEC-FILE) to close the browse cursor; no RESP clause -- errors silently discarded
14. SEND-USRLST-SCREEN -- calls POPULATE-HEADER-INFO, moves WS-MESSAGE to ERRMSGO, then sends BMS map COUSR0A/COUSR00 with ERASE+CURSOR (SEND-ERASE-YES) or CURSOR only (SEND-ERASE-NO)
15. RECEIVE-USRLST-SCREEN -- EXEC CICS RECEIVE MAP('COUSR0A') MAPSET('COUSR00') INTO(COUSR0AI) capturing RESP/RESP2 into WS-RESP-CD/WS-REAS-CD; no subsequent EVALUATE on response -- MAPFAIL and other errors are silently ignored
16. POPULATE-HEADER-INFO -- FUNCTION CURRENT-DATE to WS-CURDATE-DATA; moves CCDA-TITLE01/02, WS-TRANID ('CU00'), WS-PGMNAME ('COUSR00C'), formatted date (MM/DD/YY from WS-CURDATE-YEAR(3:2)), formatted time (HH:MM:SS) to screen header fields
17. RETURN-TO-PREV-SCREEN -- stamps CDEMO-FROM-TRANID, CDEMO-FROM-PROGRAM, CDEMO-PGM-CONTEXT=0, defaults CDEMO-TO-PROGRAM to 'COSGN00C' if blank, then EXEC CICS XCTL PROGRAM(CDEMO-TO-PROGRAM) COMMAREA(CARDDEMO-COMMAREA)
18. EXEC CICS XCTL to COUSR02C -- transfer control to user update program when selection = 'U'/'u' (inside PROCESS-ENTER-KEY)
19. EXEC CICS XCTL to COUSR03C -- transfer control to user delete program when selection = 'D'/'d' (inside PROCESS-ENTER-KEY)
20. EXEC CICS RETURN TRANSID(WS-TRANID='CU00') COMMAREA(CARDDEMO-COMMAREA) -- pseudo-conversational return at end of every normal path (MAIN-PARA line 141-144)

## Dead Code / Unused Working-Storage

The following WORKING-STORAGE fields are declared but never referenced in the PROCEDURE DIVISION:

- `WS-REC-COUNT` (PIC S9(04) COMP, line 52) -- a record counter that is never incremented or tested; the program uses WS-IDX for all loop control instead
- `WS-PAGE-NUM` (PIC S9(04) COMP, line 54) -- a local page number field that is never used; all page-number logic uses CDEMO-CU00-PAGE-NUM in the commarea
- `WS-USER-DATA` (lines 56-64) -- a local `USER-REC OCCURS 10 TIMES` table with fields USER-SEL, USER-ID, USER-NAME, USER-TYPE; this appears to be a remnant of an earlier design where user records were buffered locally before display; in the current implementation all display data is moved directly into BMS map fields (COUSR0AI/COUSR0AO) without passing through this array

These fields should be removed in any modernisation effort to avoid confusion about their intended purpose.
