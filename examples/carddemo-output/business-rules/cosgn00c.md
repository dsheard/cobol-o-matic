---
type: business-rules
program: COSGN00C
program_type: online
status: draft
confidence: high
last_pass: 5
calls: []
called_by:
- COADM01C
- COBIL00C
- COMEN01C
- CORPT00C
- COTRN00C
- COTRN01C
- COTRN02C
- COUSR00C
- COUSR01C
- COUSR02C
- COUSR03C
uses_copybooks:
- COCOM01Y
- COSGN00
- COTTL01Y
- CSDAT01Y
- CSMSG01Y
- CSUSR01Y
reads:
- USRSEC
writes: []
db_tables: []
transactions:
- CC00
mq_queues: []
---

# COSGN00C -- Business Rules

## Program Purpose

COSGN00C is the signon screen handler for the CardDemo CICS online application. It presents users with a userid/password entry screen (map COSGN0A / mapset COSGN00), validates that both fields are entered, reads the user security file (USRSEC) to authenticate credentials, and routes authenticated users to either the admin menu (COADM01C for user type 'A') or the standard menu (COMEN01C for all other user types). It runs under transaction CC00 and persists session context through CARDDEMO-COMMAREA on every CICS RETURN.

## Input / Output

| Direction | Resource  | Type | Description                                                                 |
| --------- | --------- | ---- | --------------------------------------------------------------------------- |
| IN        | COSGN0A   | CICS | BMS map receiving userid (USERIDI) and password (PASSWDI) from the terminal |
| IN        | USRSEC    | CICS | VSAM keyed security file; record layout defined in copybook CSUSR01Y        |
| IN/OUT    | CARDDEMO-COMMAREA | CICS | Commarea passed on RETURN; carries user type, user ID, program context |
| OUT       | COSGN0A   | CICS | BMS map sent back to terminal with error message (ERRMSGO) when sign-on fails |
| OUT       | COADM01C  | CICS | XCTL transfer target for authenticated admin users (SEC-USR-TYPE = 'A')    |
| OUT       | COMEN01C  | CICS | XCTL transfer target for authenticated regular users (all other types)     |

## Business Rules

### Entry Point and Initial Display

| #  | Rule                         | Condition                        | Action                                                                                          | Source Location |
| -- | ---------------------------- | -------------------------------- | ----------------------------------------------------------------------------------------------- | --------------- |
| 1  | First invocation display     | EIBCALEN = 0 (no commarea)       | Clear screen map (LOW-VALUES to COSGN0AO), set cursor on userid field (USERIDL = -1), send signon screen | MAIN-PARA line 80-83 |
| 2  | Return invocation dispatching | EIBCALEN > 0 (commarea present)  | Evaluate EIBAID to determine which key was pressed and route to the appropriate processing paragraph | MAIN-PARA line 85-95 |

### Key Handling and Routing

| #  | Rule                         | Condition                        | Action                                                                                          | Source Location |
| -- | ---------------------------- | -------------------------------- | ----------------------------------------------------------------------------------------------- | --------------- |
| 3  | Enter key processing         | EIBAID = DFHENTER                | Perform PROCESS-ENTER-KEY to receive map data and authenticate user                              | MAIN-PARA line 86-87 |
| 4  | PF3 exit / thank-you         | EIBAID = DFHPF3                  | Move CCDA-MSG-THANK-YOU to WS-MESSAGE, perform SEND-PLAIN-TEXT, then EXEC CICS RETURN (no transid, ends session) | MAIN-PARA line 88-90 |
| 5  | Invalid key rejection        | EIBAID = any other key           | Set ERR-FLG-ON ('Y'), move CCDA-MSG-INVALID-KEY to WS-MESSAGE, re-display signon screen with error | MAIN-PARA line 91-94 |

### Input Validation (PROCESS-ENTER-KEY)

| #  | Rule                           | Condition                                            | Action                                                                                        | Source Location          |
| -- | ------------------------------ | ---------------------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------ |
| 6  | User ID mandatory              | USERIDI OF COSGN0AI = SPACES OR LOW-VALUES           | Set ERR-FLG-ON, display 'Please enter User ID ...', set cursor on userid field (USERIDL = -1), re-display screen | PROCESS-ENTER-KEY line 118-122 |
| 7  | Password mandatory             | PASSWDI OF COSGN0AI = SPACES OR LOW-VALUES           | Set ERR-FLG-ON, display 'Please enter Password ...', set cursor on password field (PASSWDL = -1), re-display screen | PROCESS-ENTER-KEY line 123-127 |
| 8  | Password validation deferred   | Both fields present (WHEN OTHER / CONTINUE)          | Fall through to read user security file; no format validation is applied to either field       | PROCESS-ENTER-KEY line 128-129 |
| 9  | User ID case normalisation     | Unconditional -- executes even when ERR-FLG-ON is set | FUNCTION UPPER-CASE applied to USERIDI before storing in WS-USER-ID and CDEMO-USER-ID; lookup is case-insensitive | PROCESS-ENTER-KEY line 132-134 |
| 10 | Password case normalisation    | Unconditional -- executes even when ERR-FLG-ON is set | FUNCTION UPPER-CASE applied to PASSWDI before storing in WS-USER-PWD; comparison is case-insensitive | PROCESS-ENTER-KEY line 135-136 |
| 11 | File read gated on error flag  | NOT ERR-FLG-ON                                       | Only proceed to READ-USER-SEC-FILE if neither validation rule 6 nor 7 triggered; upper-case conversion (rules 9-10) has already run regardless | PROCESS-ENTER-KEY line 138-140 |

### Authentication (READ-USER-SEC-FILE)

| #  | Rule                              | Condition                                                   | Action                                                                                                  | Source Location              |
| -- | --------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------- |
| 12 | Successful read + password match  | WS-RESP-CD = 0 AND SEC-USR-PWD = WS-USER-PWD               | Populate commarea (CDEMO-FROM-TRANID='CC00', CDEMO-FROM-PROGRAM='COSGN00C', CDEMO-USER-ID, CDEMO-USER-TYPE from SEC-USR-TYPE, CDEMO-PGM-CONTEXT=0), then route user | READ-USER-SEC-FILE line 223-240 |
| 13 | Admin user routing                | WS-RESP-CD = 0, password matches, CDEMO-USRTYP-ADMIN (SEC-USR-TYPE = 'A') | EXEC CICS XCTL PROGRAM('COADM01C') COMMAREA(CARDDEMO-COMMAREA) -- transfers control to admin menu | READ-USER-SEC-FILE line 230-234 |
| 14 | Regular user routing              | WS-RESP-CD = 0, password matches, NOT CDEMO-USRTYP-ADMIN   | EXEC CICS XCTL PROGRAM('COMEN01C') COMMAREA(CARDDEMO-COMMAREA) -- transfers control to main menu | READ-USER-SEC-FILE line 235-239 |
| 15 | Wrong password                    | WS-RESP-CD = 0 AND SEC-USR-PWD NOT = WS-USER-PWD           | Display 'Wrong Password. Try again ...', set cursor on password field (PASSWDL = -1), re-display signon screen | READ-USER-SEC-FILE line 242-245 |
| 16 | User not found                    | WS-RESP-CD = 13 (CICS NOTFND condition)                    | Set ERR-FLG-ON, display 'User not found. Try again ...', set cursor on userid field (USERIDL = -1), re-display signon screen | READ-USER-SEC-FILE line 247-251 |
| 17 | Unexpected CICS error             | WS-RESP-CD = any value other than 0 or 13                  | Set ERR-FLG-ON, display 'Unable to verify the User ...', set cursor on userid field (USERIDL = -1), re-display signon screen | READ-USER-SEC-FILE line 252-256 |
| 18 | User ID key length constraint     | Always (KEYLENGTH clause on CICS READ)                     | Lookup in USRSEC uses exactly 8 bytes (LENGTH OF WS-USER-ID); user IDs longer than 8 characters are not supported | READ-USER-SEC-FILE line 211-219 |

### Domain Constraints (from CSUSR01Y and COCOM01Y copybooks)

| #  | Rule                              | Condition                                                   | Action                                                                                                  | Source Location              |
| -- | --------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------- |
| 19 | User ID field length              | Always                                                      | SEC-USR-ID is PIC X(08); user IDs are exactly 8 bytes in the security record                           | CSUSR01Y |
| 20 | Password field length             | Always                                                      | SEC-USR-PWD is PIC X(08); passwords are exactly 8 bytes in the security record; no minimum length enforced by program logic | CSUSR01Y |
| 21 | User type domain -- admin         | SEC-USR-TYPE = 'A' (88 CDEMO-USRTYP-ADMIN VALUE 'A')       | User is classified as administrator; routed to COADM01C                                                 | COCOM01Y |
| 22 | User type domain -- regular user  | SEC-USR-TYPE = 'U' (88 CDEMO-USRTYP-USER VALUE 'U')        | User is classified as regular user; routed to COMEN01C. Any SEC-USR-TYPE value other than 'A' also routes to COMEN01C (NOT CDEMO-USRTYP-ADMIN guard) | COCOM01Y |
| 23 | Program context initialised to 0  | Always on successful authentication                         | CDEMO-PGM-CONTEXT is set to ZEROS (88 CDEMO-PGM-ENTER VALUE 0), signalling to the receiving program that this is a fresh entry, not a re-entry | COCOM01Y / READ-USER-SEC-FILE line 228 |

### Session and Commarea Management

| #  | Rule                              | Condition                    | Action                                                                                                  | Source Location   |
| -- | --------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------- | ----------------- |
| 24 | Persistent session via RETURN     | Always (at end of MAIN-PARA) | EXEC CICS RETURN TRANSID(WS-TRANID) COMMAREA(CARDDEMO-COMMAREA) -- WS-TRANID VALUE 'CC00' -- keeps transaction active between interactions | MAIN-PARA line 98-102 |
| 25 | PF3 terminates session            | EIBAID = DFHPF3              | EXEC CICS RETURN (no TRANSID) in SEND-PLAIN-TEXT ends pseudo-conversational loop; session is terminated | SEND-PLAIN-TEXT line 171-172 |
| 26 | XCTL terminates signon loop       | Successful authentication    | EXEC CICS XCTL does not return; the CC00 transaction does not continue executing after transfer         | READ-USER-SEC-FILE line 231-239 |

## Calculations

| Calculation      | Formula / Logic                                                                                         | Input Fields                              | Output Field                  | Source Location          |
| ---------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ----------------------------- | ------------------------ |
| Date formatting  | WS-CURDATE-MONTH -> WS-CURDATE-MM, WS-CURDATE-DAY -> WS-CURDATE-DD, WS-CURDATE-YEAR(3:2) -> WS-CURDATE-YY; assembled into WS-CURDATE-MM-DD-YY | FUNCTION CURRENT-DATE result (WS-CURDATE-DATA) | CURDATEO OF COSGN0AO | POPULATE-HEADER-INFO line 186-190 |
| Time formatting  | WS-CURTIME-HOURS -> WS-CURTIME-HH, WS-CURTIME-MINUTE -> WS-CURTIME-MM, WS-CURTIME-SECOND -> WS-CURTIME-SS; assembled into WS-CURTIME-HH-MM-SS | FUNCTION CURRENT-DATE result (WS-CURDATE-DATA) | CURTIMEO OF COSGN0AO | POPULATE-HEADER-INFO line 192-196 |

## Error Handling

| Condition                                        | Action                                                                       | Return Code          | Source Location                   |
| ------------------------------------------------ | ---------------------------------------------------------------------------- | -------------------- | --------------------------------- |
| User ID field is blank or low-values on ENTER    | Set WS-ERR-FLG='Y', move 'Please enter User ID ...' to WS-MESSAGE, set cursor USERIDL=-1, re-send screen | ERR-FLG-ON           | PROCESS-ENTER-KEY line 118-122   |
| Password field is blank or low-values on ENTER   | Set WS-ERR-FLG='Y', move 'Please enter Password ...' to WS-MESSAGE, set cursor PASSWDL=-1, re-send screen | ERR-FLG-ON           | PROCESS-ENTER-KEY line 123-127   |
| Invalid AID key pressed                          | Set WS-ERR-FLG='Y', move CCDA-MSG-INVALID-KEY to WS-MESSAGE, re-send screen | ERR-FLG-ON           | MAIN-PARA line 91-94             |
| USRSEC READ returns RESP=13 (NOTFND)             | Set WS-ERR-FLG='Y', move 'User not found. Try again ...' to WS-MESSAGE, set cursor USERIDL=-1, re-send screen | RESP=13 / ERR-FLG-ON | READ-USER-SEC-FILE line 247-251  |
| USRSEC READ returns RESP != 0 and != 13          | Set WS-ERR-FLG='Y', move 'Unable to verify the User ...' to WS-MESSAGE, set cursor USERIDL=-1, re-send screen | RESP=OTHER / ERR-FLG-ON | READ-USER-SEC-FILE line 252-256 |
| Password mismatch (record found, passwords differ) | Move 'Wrong Password. Try again ...' to WS-MESSAGE, set cursor PASSWDL=-1, re-send screen (ERR-FLG not set) | none                 | READ-USER-SEC-FILE line 242-245  |
| EXEC CICS RECEIVE error (map receive fails)      | WS-RESP-CD from RECEIVE is captured but never evaluated; it is silently overwritten by WS-RESP-CD from the subsequent CICS READ; any terminal receive error is undetected | none (silently ignored) | PROCESS-ENTER-KEY line 110-115 |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. MAIN-PARA -- entry point; initialises error flag (ERR-FLG-OFF) and clears message area
2. IF EIBCALEN = 0 -- first invocation path: clear map, set cursor, PERFORM SEND-SIGNON-SCREEN, fall through to EXEC CICS RETURN
3. ELSE EVALUATE EIBAID -- return invocation path:
   - WHEN DFHENTER: PERFORM PROCESS-ENTER-KEY
   - WHEN DFHPF3: PERFORM SEND-PLAIN-TEXT (which issues its own EXEC CICS RETURN and never falls through)
   - WHEN OTHER: set error, PERFORM SEND-SIGNON-SCREEN, fall through to EXEC CICS RETURN
4. EXEC CICS RETURN TRANSID(WS-TRANID) COMMAREA(CARDDEMO-COMMAREA) -- at end of MAIN-PARA; keeps session alive (WS-TRANID VALUE 'CC00')
5. PROCESS-ENTER-KEY -- receives map, validates User ID and Password presence, unconditionally normalises both to upper case, conditionally PERFORMs READ-USER-SEC-FILE (only when ERR-FLG-OFF)
6. READ-USER-SEC-FILE -- issues EXEC CICS READ on USRSEC keyed by WS-USER-ID (8-byte key); on success compares SEC-USR-PWD to WS-USER-PWD; on match populates commarea and issues EXEC CICS XCTL to COADM01C or COMEN01C based on CDEMO-USRTYP-ADMIN (SEC-USR-TYPE = 'A')
7. SEND-SIGNON-SCREEN -- PERFORMs POPULATE-HEADER-INFO, moves WS-MESSAGE to ERRMSGO, issues EXEC CICS SEND MAP
8. POPULATE-HEADER-INFO -- obtains current date/time via FUNCTION CURRENT-DATE, formats date and time fields, moves title constants (CCDA-TITLE01, CCDA-TITLE02), transaction ID, program name, APPLID (from EXEC CICS ASSIGN), and SYSID (from EXEC CICS ASSIGN) into the output map
9. SEND-PLAIN-TEXT -- sends plain text message via EXEC CICS SEND TEXT then issues bare EXEC CICS RETURN to end the pseudo-conversational session (PF3 path only)
