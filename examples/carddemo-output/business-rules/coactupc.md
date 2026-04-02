---
type: business-rules
program: COACTUPC
program_type: online
status: draft
confidence: high
last_pass: 4
calls: []
called_by: []
uses_copybooks:
- COACTUP
- COCOM01Y
- COTTL01Y
- CSDAT01Y
- CSLKPCDY
- CSMSG01Y
- CSMSG02Y
- CSSETATY
- CSSTRPFY
- CSUSR01Y
- CSUTLDPY
- CSUTLDWY
- CVACT01Y
- CVACT03Y
- CVCRD01Y
- CVCUS01Y
reads:
- ACCTDAT
- CUSTDAT
- CXACAIX
writes:
- ACCTDAT
- CUSTDAT
db_tables: []
transactions:
- CAUP
mq_queues: []
xctl_targets:
- COMEN01C
- COCRDLIC
- COCRDSLC
---

# COACTUPC -- Business Rules

## Program Purpose

COACTUPC is an online CICS program that handles account and customer record updates for the CardDemo application. It runs under transaction ID `CAUP` and uses BMS map `CACTUPA` (mapset `COACTUP`). The program operates as a multi-step interactive update workflow: the user first enters a search key (account number), the program fetches account and customer records, presents the details for editing, validates all user changes, requests a PF5 confirmation before writing, and then performs locked updates to the ACCTDAT and CUSTDAT VSAM files. It also cross-references the account through CXACAIX (card cross-reference alternate index). On PF3 exit the program issues an XCTL back to the calling program or the main menu (COMEN01C / transaction CM00).

## Input / Output

| Direction | Resource  | Type  | Description                                                  |
| --------- | --------- | ----- | ------------------------------------------------------------ |
| IN        | ACCTDAT   | VSAM  | Account master file -- read and rewrite for update           |
| IN        | CUSTDAT   | VSAM  | Customer master file -- read and rewrite for update          |
| IN        | CXACAIX   | VSAM  | Card cross-reference alternate index -- used to look up card by account |
| OUT       | ACCTDAT   | VSAM  | Account master file -- updated record written back           |
| OUT       | CUSTDAT   | VSAM  | Customer master file -- updated record written back          |
| IN/OUT    | CACTUPA   | CICS BMS | BMS map for account update screen (mapset COACTUP)        |
| OUT       | COMEN01C  | CICS XCTL | Transfer control to main menu program on PF3 exit        |
| IN        | DFHCOMMAREA | CICS | Communication area carrying CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA |

## Business Rules

### Initialisation and COMMAREA Handling

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 1  | Fresh entry: no prior context | `EIBCALEN = 0` OR (`CDEMO-FROM-PROGRAM = 'COMEN01C'` AND NOT `CDEMO-PGM-REENTER`) | Initialize CARDDEMO-COMMAREA and WS-THIS-PROGCOMMAREA; set `CDEMO-PGM-ENTER`; set `ACUP-DETAILS-NOT-FETCHED` | 0000-MAIN lines 30-36 |
| 2  | Continuation entry: prior context exists | `EIBCALEN > 0` AND NOT (entering from menu for first time) | Copy `DFHCOMMAREA(1:LENGTH OF CARDDEMO-COMMAREA)` into CARDDEMO-COMMAREA; copy remaining bytes into WS-THIS-PROGCOMMAREA | 0000-MAIN lines 38-43 |
| 3  | Transaction ID stored at entry | Always | MOVE `'CAUP'` (LIT-THISTRANID) to WS-TRANID | 0000-MAIN line 22 |
| 4  | Error/return message cleared at entry | Always | SET `WS-RETURN-MSG-OFF` TO TRUE (clears WS-RETURN-MSG to spaces) | 0000-MAIN line 26 |

### PF Key Validation and Routing Gate

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 5  | Valid AID keys: ENTER accepted | `CCARD-AID-ENTER` is true | Set `PFK-VALID` | 0000-MAIN lines 56-62 |
| 6  | Valid AID keys: PF3 accepted | `CCARD-AID-PFK03` is true | Set `PFK-VALID` | 0000-MAIN lines 56-62 |
| 7  | Valid AID keys: PF5 accepted only when changes validated but not yet confirmed | `CCARD-AID-PFK05` AND `ACUP-CHANGES-OK-NOT-CONFIRMED` (ACUP-CHANGE-ACTION = 'N') | Set `PFK-VALID` | 0000-MAIN lines 58-62 |
| 8  | Valid AID keys: PF12 accepted only when account data has been fetched | `CCARD-AID-PFK12` AND NOT `ACUP-DETAILS-NOT-FETCHED` | Set `PFK-VALID` | 0000-MAIN lines 60-62 |
| 9  | Invalid AID key: force to ENTER behavior | `PFK-INVALID` is true (no valid AID matched) | SET `CCARD-AID-ENTER` TO TRUE -- treat as ENTER keypress | 0000-MAIN lines 64-66 |

### Main Dispatch (EVALUATE TRUE)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 10 | PF3 Exit: return to caller with SYNCPOINT | `CCARD-AID-PFK03` | Issue CICS SYNCPOINT; set navigation fields; XCTL to `CDEMO-TO-PROGRAM` passing CARDDEMO-COMMAREA | 0000-MAIN lines 77-109 |
| 11 | PF3 Exit: default navigation target is main menu | `CDEMO-FROM-TRANID = LOW-VALUES` OR `CDEMO-FROM-TRANID = SPACES` | MOVE `'CM00'` (LIT-MENUTRANID) to CDEMO-TO-TRANID | 0000-MAIN lines 80-82 |
| 12 | PF3 Exit: honour caller's return transaction | `CDEMO-FROM-TRANID` is not LOW-VALUES or SPACES | MOVE `CDEMO-FROM-TRANID` to `CDEMO-TO-TRANID` | 0000-MAIN lines 83-85 |
| 13 | PF3 Exit: default navigation program is main menu | `CDEMO-FROM-PROGRAM = LOW-VALUES` OR `CDEMO-FROM-PROGRAM = SPACES` | MOVE `'COMEN01C'` (LIT-MENUPGM) to `CDEMO-TO-PROGRAM` | 0000-MAIN lines 87-89 |
| 14 | PF3 Exit: honour caller's return program | `CDEMO-FROM-PROGRAM` is not LOW-VALUES or SPACES | MOVE `CDEMO-FROM-PROGRAM` to `CDEMO-TO-PROGRAM` | 0000-MAIN lines 90-92 |
| 15 | PF3 Exit: stamp FROM fields before transfer | Always on PF3 exit | MOVE `'CAUP'` to `CDEMO-FROM-TRANID`; MOVE `'COACTUPC'` to `CDEMO-FROM-PROGRAM`; SET `CDEMO-USRTYP-USER` and `CDEMO-PGM-ENTER` to TRUE; record last mapset/map | 0000-MAIN lines 94-100 |
| 16 | Fresh entry or initial screen: display blank search form | `ACUP-DETAILS-NOT-FETCHED` AND `CDEMO-PGM-ENTER` | PERFORM 3000-SEND-MAP, set `CDEMO-PGM-REENTER`, set `ACUP-DETAILS-NOT-FETCHED`; GO TO COMMON-RETURN | 0000-MAIN lines 114-123 |
| 17 | Entry from menu (first visit): display blank search form | `CDEMO-FROM-PROGRAM = 'COMEN01C'` AND NOT `CDEMO-PGM-REENTER` | INITIALIZE WS-THIS-PROGCOMMAREA; PERFORM 3000-SEND-MAP; set re-enter flags; GO TO COMMON-RETURN | 0000-MAIN lines 116-123 |
| 18 | After successful update: reset and prompt for new account | `ACUP-CHANGES-OKAYED-AND-DONE` (ACUP-CHANGE-ACTION = 'C') | INITIALIZE WS-THIS-PROGCOMMAREA, WS-MISC-STORAGE, CDEMO-ACCT-ID; set `CDEMO-PGM-ENTER`; PERFORM 3000-SEND-MAP; set `ACUP-DETAILS-NOT-FETCHED`; GO TO COMMON-RETURN | 0000-MAIN lines 129-139 |
| 19 | After failed update: reset and prompt for new account | `ACUP-CHANGES-FAILED` (ACUP-CHANGE-ACTION = 'L' or 'F') | Same reset and re-display as after successful update | 0000-MAIN lines 130-139 |
| 20 | Normal processing path (WHEN OTHER) | All other conditions not matched above | PERFORM 1000-PROCESS-INPUTS, 2000-DECIDE-ACTION, 3000-SEND-MAP in sequence; GO TO COMMON-RETURN | 0000-MAIN lines 146-153 |

### ACUP-CHANGE-ACTION State Machine (Domain Constraints)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 21 | State: details not yet fetched | `ACUP-CHANGE-ACTION = LOW-VALUES` or `SPACES` | 88-level `ACUP-DETAILS-NOT-FETCHED` is TRUE -- user must supply account number | data-division line 625 |
| 22 | State: details displayed to user | `ACUP-CHANGE-ACTION = 'S'` | 88-level `ACUP-SHOW-DETAILS` is TRUE | data-division line 628 |
| 23 | State: changes made with validation errors | `ACUP-CHANGE-ACTION = 'E'` | 88-level `ACUP-CHANGES-NOT-OK` is TRUE | data-division line 632 |
| 24 | State: changes validated, awaiting PF5 confirmation | `ACUP-CHANGE-ACTION = 'N'` | 88-level `ACUP-CHANGES-OK-NOT-CONFIRMED` is TRUE -- PF5 is only allowed in this state | data-division line 633 |
| 25 | State: update committed successfully | `ACUP-CHANGE-ACTION = 'C'` | 88-level `ACUP-CHANGES-OKAYED-AND-DONE` is TRUE -- program resets and prompts for new account | data-division line 634 |
| 26 | State: update failed -- lock error | `ACUP-CHANGE-ACTION = 'L'` | 88-level `ACUP-CHANGES-OKAYED-LOCK-ERROR` is TRUE | data-division line 636 |
| 27 | State: update failed -- write error | `ACUP-CHANGE-ACTION = 'F'` | 88-level `ACUP-CHANGES-OKAYED-BUT-FAILED` is TRUE | data-division line 637 |

### Screen Send Pipeline (3000-SEND-MAP)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 28 | Screen preparation sequence | Always on 3000-SEND-MAP | Execute six sub-steps in order: 3100-SCREEN-INIT, 3200-SETUP-SCREEN-VARS, 3250-SETUP-INFOMSG, 3300-SETUP-SCREEN-ATTRS, 3390-SETUP-INFOMSG-ATTRS, 3400-SEND-SCREEN | 3000-SEND-MAP lines 162-173 |

### Abend Handling

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 29 | Trap all CICS abends | Program entry | `EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE)` -- any CICS abend diverts to ABEND-ROUTINE | 0000-MAIN lines 12-14 |

### Input Processing Dispatcher (1000-PROCESS-INPUTS / 1200-EDIT-MAP-INPUTS)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 30 | Input processing sequence | Always | PERFORM 1100-RECEIVE-MAP then 1200-EDIT-MAP-INPUTS; copy WS-RETURN-MSG to CCARD-ERROR-MSG; set CCARD-NEXT-PROG to 'COACTUPC', CCARD-NEXT-MAPSET to 'COACTUP', CCARD-NEXT-MAP to 'CACTUPA' | 1000-PROCESS-INPUTS lines 9-18 |
| 31 | Dispatch to account search edits when data not yet fetched | `ACUP-DETAILS-NOT-FETCHED` (ACUP-CHANGE-ACTION = LOW-VALUES or SPACES) | PERFORM 1210-EDIT-ACCOUNT; clear ACUP-OLD-ACCT-DATA to LOW-VALUES; if account filter blank set NO-SEARCH-CRITERIA-RECEIVED; exit edit paragraph | 1200-EDIT-MAP-INPUTS lines 27-43 |
| 32 | Skip re-validation when no changes or already confirmed | `NO-CHANGES-FOUND` OR `ACUP-CHANGES-OK-NOT-CONFIRMED` OR `ACUP-CHANGES-OKAYED-AND-DONE` (after 1205-COMPARE-OLD-NEW) | Clear WS-NON-KEY-FLAGS to LOW-VALUES; exit edit paragraph without running field validators | 1200-EDIT-MAP-INPUTS lines 57-62 |
| 33 | Run full field validation when changes have been made | Data has been fetched AND changes detected AND not already confirmed | Set `ACUP-CHANGES-NOT-OK` to TRUE; perform all individual field validators in sequence; set `ACUP-CHANGES-OK-NOT-CONFIRMED` if no INPUT-ERROR at end | 1200-EDIT-MAP-INPUTS lines 64-269 |

### Change Detection (1205-COMPARE-OLD-NEW)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 34 | Detect account field changes (pass 1) | Compare all account data fields old vs new | Fields compared: ACCT-ID, ACTIVE-STATUS (case-insensitive), CURR-BAL, CREDIT-LIMIT, CASH-CREDIT-LIMIT, OPEN-DATE, EXPIRATION-DATE, REISSUE-DATE, CURR-CYC-CREDIT, CURR-CYC-DEBIT, GROUP-ID (trimmed, case-insensitive) | 1205-COMPARE-OLD-NEW lines 278-298 |
| 35 | Detect customer field changes (pass 2) | Compare all customer data fields old vs new | Fields compared: CUST-ID, FIRST-NAME, MIDDLE-NAME, LAST-NAME, ADDR-LINE-1, ADDR-LINE-2, ADDR-LINE-3, ADDR-STATE-CD, ADDR-COUNTRY-CD, ADDR-ZIP, PHONE-NUM-1 (3 parts), PHONE-NUM-2 (3 parts), SSN-X, GOVT-ISSUED-ID, DOB-YYYY-MM-DD, EFT-ACCOUNT-ID, PRI-HOLDER-IND, FICO-SCORE-X | 1205-COMPARE-OLD-NEW lines 302-367 |
| 36 | No change detected | All 29 account + customer fields match between OLD and NEW | Set `NO-CHANGES-DETECTED` to TRUE (WS-RETURN-MSG = 'No change detected with respect to values fetched.') | 1205-COMPARE-OLD-NEW lines 363 |
| 37 | Change detected | Any one of the 29 fields differs | Set `CHANGE-HAS-OCCURRED` to TRUE; GO TO exit immediately | 1205-COMPARE-OLD-NEW lines 365-366 |
| 38 | String comparisons are case-insensitive and trim-based | Applied to: ACTIVE-STATUS, GROUP-ID, CUST-ID, all name fields, all address fields, GOVT-ISSUED-ID, PRI-HOLDER-IND | FUNCTION UPPER-CASE(FUNCTION TRIM(...)) used on both sides before comparison | 1205-COMPARE-OLD-NEW throughout |

### Account Number Validation (1210-EDIT-ACCOUNT)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 39 | Account number is mandatory | `CC-ACCT-ID = LOW-VALUES` OR `CC-ACCT-ID = SPACES` | Set INPUT-ERROR; set FLG-ACCTFILTER-BLANK; set WS-PROMPT-FOR-ACCT ('Account number not provided'); zero CDEMO-ACCT-ID and ACUP-NEW-ACCT-ID | 1210-EDIT-ACCOUNT lines 381-390 |
| 40 | Account number must be numeric | `CC-ACCT-ID IS NOT NUMERIC` | Set INPUT-ERROR; message 'Account Number if supplied must be a 11 digit Non-Zero Number' | 1210-EDIT-ACCOUNT lines 396-407 |
| 41 | Account number must be non-zero | `CC-ACCT-ID-N = ZEROS` (numeric value is zero) | Set INPUT-ERROR; message 'Account Number if supplied must be a 11 digit Non-Zero Number' | 1210-EDIT-ACCOUNT lines 397-407 |
| 42 | Account number valid: copy to COMMAREA | All edits pass | MOVE CC-ACCT-ID to CDEMO-ACCT-ID; set FLG-ACCTFILTER-ISVALID | 1210-EDIT-ACCOUNT lines 409-411 |

### Generic Mandatory Field Validation (1215-EDIT-MANDATORY)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 43 | Mandatory field must not be blank | Field value (up to WS-EDIT-ALPHANUM-LENGTH) is LOW-VALUES, SPACES, or zero-length after TRIM | Set INPUT-ERROR; set FLG-MANDATORY-BLANK; message '[field-name] must be supplied.' | 1215-EDIT-MANDATORY lines 418-444 |
| 44 | Address Line 1 uses 1215-EDIT-MANDATORY | Length = 50 | Required: must not be blank | 1200-EDIT-MAP-INPUTS lines 178-184 |

### Yes/No Field Validation (1220-EDIT-YESNO)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 45 | Yes/No field must be supplied | `WS-EDIT-YES-NO = LOW-VALUES` OR `SPACES` OR `ZEROS` | Set INPUT-ERROR; set FLG-YES-NO-BLANK; message '[field-name] must be supplied.' | 1220-EDIT-YESNO lines 455-468 |
| 46 | Yes/No field must be 'Y' or 'N' | Field is supplied but not 'Y' or 'N' (FLG-YES-NO-ISVALID is FALSE) | Set INPUT-ERROR; set FLG-YES-NO-NOT-OK; message '[field-name] must be Y or N.' | 1220-EDIT-YESNO lines 472-486 |
| 47 | Account Active Status validated as Y/N | ACUP-NEW-ACTIVE-STATUS via 1220-EDIT-YESNO | Valid values: 'Y' or 'N' only | 1200-EDIT-MAP-INPUTS lines 66-70 |
| 48 | Primary Card Holder indicator validated as Y/N | ACUP-NEW-CUST-PRI-HOLDER-IND via 1220-EDIT-YESNO | Valid values: 'Y' or 'N' only | 1200-EDIT-MAP-INPUTS lines 251-256 |

### Required Alpha-Only Field Validation (1225-EDIT-ALPHA-REQD)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 49 | Required alpha field must not be blank | Field value is LOW-VALUES, SPACES, or zero-length after TRIM | Set INPUT-ERROR; set FLG-ALPHA-BLANK; message '[field-name] must be supplied.' | 1225-EDIT-ALPHA-REQD lines 497-516 |
| 50 | Required alpha field must contain only letters and spaces | INSPECT converts all A-Z/a-z to spaces; remaining non-space characters indicate non-alpha content | Set INPUT-ERROR; set FLG-ALPHA-NOT-OK; message '[field-name] can have alphabets only.' | 1225-EDIT-ALPHA-REQD lines 519-541 |
| 51 | First Name uses 1225-EDIT-ALPHA-REQD | Length = 25 | Required; alphabets and spaces only | 1200-EDIT-MAP-INPUTS lines 154-160 |
| 52 | Last Name uses 1225-EDIT-ALPHA-REQD | Length = 25 | Required; alphabets and spaces only | 1200-EDIT-MAP-INPUTS lines 170-176 |
| 53 | State Code uses 1225-EDIT-ALPHA-REQD (then 1270) | Length = 2 | Required; alphabets only; then validated against US state code lookup table | 1200-EDIT-MAP-INPUTS lines 186-196 |
| 54 | City (stored in ADDR-LINE-3) uses 1225-EDIT-ALPHA-REQD | Length = 50 | Required; alphabets and spaces only | 1200-EDIT-MAP-INPUTS lines 209-215 |
| 55 | Country Code uses 1225-EDIT-ALPHA-REQD | Length = 3 | Required; alphabets only | 1200-EDIT-MAP-INPUTS lines 217-224 |

### Optional Alpha Field Validation (1235-EDIT-ALPHA-OPT)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 56 | Optional alpha field: blank is acceptable | Field is LOW-VALUES, SPACES, or zero-length after TRIM | Set FLG-ALPHA-ISVALID; exit without error | 1235-EDIT-ALPHA-OPT lines 611-619 |
| 57 | Optional alpha field: if supplied must be letters/spaces only | Field supplied but contains non-alpha characters | Set INPUT-ERROR; set FLG-ALPHA-NOT-OK; message '[field-name] can have alphabets only.' | 1235-EDIT-ALPHA-OPT lines 625-647 |
| 58 | Middle Name uses 1235-EDIT-ALPHA-OPT | Length = 25 | Optional; if supplied must be alphabets and spaces only | 1200-EDIT-MAP-INPUTS lines 162-168 |

### Required Alphanumeric Field Validation (1230-EDIT-ALPHANUM-REQD)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 59 | Required alphanumeric field must not be blank | Field value is LOW-VALUES, SPACES, or zero-length after TRIM | Set INPUT-ERROR; set FLG-ALPHNANUM-BLANK; message '[field-name] must be supplied.' | 1230-EDIT-ALPHANUM-REQD lines 554-573 |
| 60 | Required alphanumeric field must contain only letters, digits, and spaces | INSPECT converts A-Z/a-z/0-9 to spaces; remaining content is invalid | Set INPUT-ERROR; set FLG-ALPHNANUM-NOT-OK; message '[field-name] can have numbers or alphabets only.' | 1230-EDIT-ALPHANUM-REQD lines 575-599 |

### Optional Alphanumeric Field Validation (1240-EDIT-ALPHANUM-OPT)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 61 | Optional alphanumeric field: blank is acceptable | Field is LOW-VALUES, SPACES, or zero-length after TRIM | Set FLG-ALPHNANUM-ISVALID; exit without error | 1240-EDIT-ALPHANUM-OPT lines 660-668 |
| 62 | Optional alphanumeric field: if supplied must be letters/digits/spaces | Field supplied but contains invalid characters | Set INPUT-ERROR; set FLG-ALPHNANUM-NOT-OK; message '[field-name] can have numbers or alphabets only.' | 1240-EDIT-ALPHANUM-OPT lines 673-694 |

### Required Numeric Field Validation (1245-EDIT-NUM-REQD)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 63 | Required numeric field must not be blank | Field value is LOW-VALUES, SPACES, or zero-length after TRIM | Set INPUT-ERROR; set FLG-ALPHNANUM-BLANK; message '[field-name] must be supplied.' | 1245-EDIT-NUM-REQD lines 708-727 |
| 64 | Required numeric field must be all digits | Field IS NUMERIC check fails | Set INPUT-ERROR; set FLG-ALPHNANUM-NOT-OK; message '[field-name] must be all numeric.' | 1245-EDIT-NUM-REQD lines 731-745 |
| 65 | Required numeric field must not be zero | FUNCTION NUMVAL(...) = 0 | Set INPUT-ERROR; set FLG-ALPHNANUM-NOT-OK; message '[field-name] must not be zero.' | 1245-EDIT-NUM-REQD lines 750-765 |
| 66 | FICO Score uses 1245-EDIT-NUM-REQD | Length = 3 | Required; numeric; non-zero; then validated by 1275-EDIT-FICO-SCORE for range | 1200-EDIT-MAP-INPUTS lines 139-150 |
| 67 | Zip Code uses 1245-EDIT-NUM-REQD | Length = 5 | Required; numeric; non-zero | 1200-EDIT-MAP-INPUTS lines 199-205 |
| 68 | EFT Account ID uses 1245-EDIT-NUM-REQD | Length = 10 | Required; numeric; non-zero | 1200-EDIT-MAP-INPUTS lines 242-249 |

### Signed Numeric (Currency) Field Validation (1250-EDIT-SIGNED-9V2)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 69 | Signed currency field must not be blank | `WS-EDIT-SIGNED-NUMBER-9V2-X = LOW-VALUES` OR `SPACES` | Set INPUT-ERROR; set FLG-SIGNED-NUMBER-BLANK; message '[field-name] must be supplied.' | 1250-EDIT-SIGNED-9V2 lines 778-793 |
| 70 | Signed currency field must pass NUMVAL-C | `FUNCTION TEST-NUMVAL-C(value) <> 0` | Set INPUT-ERROR; set FLG-SIGNED-NUMBER-NOT-OK; message '[field-name] is not valid' | 1250-EDIT-SIGNED-9V2 lines 795-809 |
| 71 | Credit Limit uses 1250-EDIT-SIGNED-9V2 | ACUP-NEW-CREDIT-LIMIT-X (PIC X(15)) | Required signed numeric with 2 decimal places | 1200-EDIT-MAP-INPUTS lines 78-82 |
| 72 | Cash Credit Limit uses 1250-EDIT-SIGNED-9V2 | ACUP-NEW-CASH-CREDIT-LIMIT-X (PIC X(15)) | Required signed numeric with 2 decimal places | 1200-EDIT-MAP-INPUTS lines 90-95 |
| 73 | Current Balance uses 1250-EDIT-SIGNED-9V2 | ACUP-NEW-CURR-BAL-X (PIC X(15)) | Required signed numeric with 2 decimal places | 1200-EDIT-MAP-INPUTS lines 103-107 |
| 74 | Current Cycle Credit uses 1250-EDIT-SIGNED-9V2 | ACUP-NEW-CURR-CYC-CREDIT-X (PIC X(15)) | Required signed numeric with 2 decimal places | 1200-EDIT-MAP-INPUTS lines 110-114 |
| 75 | Current Cycle Debit uses 1250-EDIT-SIGNED-9V2 | ACUP-NEW-CURR-CYC-DEBIT-X (PIC X(15)) | Required signed numeric with 2 decimal places | 1200-EDIT-MAP-INPUTS lines 117-121 |

### Date Field Validation (EDIT-DATE-CCYYMMDD / EDIT-DATE-OF-BIRTH)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 76 | Open Date validated as CCYYMMDD | ACUP-NEW-OPEN-DATE via EDIT-DATE-CCYYMMDD | Date must be valid calendar date in CCYYMMDD format | 1200-EDIT-MAP-INPUTS lines 72-76 |
| 77 | Expiry Date validated as CCYYMMDD | ACUP-NEW-EXPIRAION-DATE via EDIT-DATE-CCYYMMDD | Date must be valid calendar date in CCYYMMDD format | 1200-EDIT-MAP-INPUTS lines 84-88 |
| 78 | Reissue Date validated as CCYYMMDD | ACUP-NEW-REISSUE-DATE via EDIT-DATE-CCYYMMDD | Date must be valid calendar date in CCYYMMDD format | 1200-EDIT-MAP-INPUTS lines 97-101 |
| 79 | Date of Birth validated as CCYYMMDD, then as a valid birth date | ACUP-NEW-CUST-DOB-YYYY-MM-DD via EDIT-DATE-CCYYMMDD then EDIT-DATE-OF-BIRTH | First pass: valid calendar date; second pass (if first passes): valid birth date (age plausibility check) | 1200-EDIT-MAP-INPUTS lines 127-137 |

### US Phone Number Validation (1260-EDIT-US-PHONE-NUM)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 80 | Phone number is optional | All three parts (area, prefix, line) are SPACES or LOW-VALUES | Set WS-EDIT-US-PHONE-IS-VALID; exit without error | 1260-EDIT-US-PHONE-NUM lines 828-838 |
| 81 | Area code must be supplied if any phone part is provided | Area code is SPACES or LOW-VALUES but other parts are present | Set INPUT-ERROR; set FLG-EDIT-US-PHONEA-BLANK; message '[field]: Area code must be supplied.' | EDIT-AREA-CODE lines 841-852 |
| 82 | Area code must be 3 digits (numeric) | Area code IS NOT NUMERIC | Set INPUT-ERROR; set FLG-EDIT-US-PHONEA-NOT-OK; message '[field]: Area code must be A 3 digit number.' | EDIT-AREA-CODE lines 858-872 |
| 83 | Area code must be non-zero | `WS-EDIT-US-PHONE-NUMA-N = 0` | Set INPUT-ERROR; message '[field]: Area code cannot be zero' | EDIT-AREA-CODE lines 874-888 |
| 84 | Area code must be a valid North America general-purpose area code | Checked against CSLKPCDY lookup table (VALID-GENERAL-PURP-CODE) | Set INPUT-ERROR; message '[field]: Not valid North America general purpose area code' | EDIT-AREA-CODE lines 890-906 |
| 85 | Phone prefix must be supplied | Prefix is SPACES or LOW-VALUES | Set INPUT-ERROR; set FLG-EDIT-US-PHONEB-BLANK; message '[field]: Prefix code must be supplied.' | EDIT-US-PHONE-PREFIX lines 912-924 |
| 86 | Phone prefix must be 3 digits (numeric) | Prefix IS NOT NUMERIC | Set INPUT-ERROR; set FLG-EDIT-US-PHONEB-NOT-OK; message '[field]: Prefix code must be A 3 digit number.' | EDIT-US-PHONE-PREFIX lines 929-943 |
| 87 | Phone prefix must be non-zero | `WS-EDIT-US-PHONE-NUMB-N = 0` | Set INPUT-ERROR; message '[field]: Prefix code cannot be zero' | EDIT-US-PHONE-PREFIX lines 945-959 |
| 88 | Phone line number must be supplied | Line number is SPACES or LOW-VALUES | Set INPUT-ERROR; set FLG-EDIT-US-PHONEC-BLANK; message '[field]: Line number code must be supplied.' | EDIT-US-PHONE-LINENUM lines 965-977 |
| 89 | Phone line number must be 4 digits (numeric) | Line number IS NOT NUMERIC | Set INPUT-ERROR; set FLG-EDIT-US-PHONEC-NOT-OK; message '[field]: Line number code must be A 4 digit number.' | EDIT-US-PHONE-LINENUM lines 982-996 |
| 90 | Phone line number must be non-zero | `WS-EDIT-US-PHONE-NUMC-N = 0` | Set INPUT-ERROR; message '[field]: Line number code cannot be zero' | EDIT-US-PHONE-LINENUM lines 998-1012 |
| 91 | Phone Number 1 validated via 1260-EDIT-US-PHONE-NUM | ACUP-NEW-CUST-PHONE-NUM-1 | Format: (NXX)NXX-XXXX stored as X(15) = '(' + 3-digit area + ')' + 3-digit prefix + '-' + 4-digit line | 1200-EDIT-MAP-INPUTS lines 226-232 |
| 92 | Phone Number 2 validated via 1260-EDIT-US-PHONE-NUM | ACUP-NEW-CUST-PHONE-NUM-2 | Same format as Phone Number 1; both are optional as a unit | 1200-EDIT-MAP-INPUTS lines 234-240 |

### US Social Security Number Validation (1265-EDIT-US-SSN)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 93 | SSN Part 1 (first 3 digits) must be numeric and non-zero | Via 1245-EDIT-NUM-REQD with length=3 | Required; must be all numeric; must not be zero | 1265-EDIT-US-SSN lines 1033-1038 |
| 94 | SSN Part 1 must not be 000, 666, or 900-999 | `INVALID-SSN-PART1` (88-level: VALUES 0, 666, 900 THRU 999) | Set INPUT-ERROR; message 'SSN: First 3 chars: should not be 000, 666, or between 900 and 999' | 1265-EDIT-US-SSN lines 1042-1058 |
| 95 | SSN Part 2 (4th and 5th digits) must be numeric and non-zero | Via 1245-EDIT-NUM-REQD with length=2 | Required; must be all numeric; must not be zero | 1265-EDIT-US-SSN lines 1063-1069 |
| 96 | SSN Part 3 (last 4 digits) must be numeric and non-zero | Via 1245-EDIT-NUM-REQD with length=4 | Required; must be all numeric; must not be zero (range 0001-9999 implied by non-zero check) | 1265-EDIT-US-SSN lines 1075-1081 |

### US State Code Validation (1270-EDIT-US-STATE-CD)

| #   | Rule | Condition | Action | Source Location |
| --- | ---- | --------- | ------ | --------------- |
| 97 | State code must be a valid US state code | `VALID-US-STATE-CODE` condition from CSLKPCDY copybook lookup table | Set INPUT-ERROR; set FLG-STATE-NOT-OK; message '[field]: is not a valid state code' | 1270-EDIT-US-STATE-CD lines 1087-1104 |
| 98 | State code validation is only called if alpha-edit passes | `FLG-ALPHA-ISVALID` must be TRUE before calling 1270 | Guards against running lookup on non-alpha data | 1200-EDIT-MAP-INPUTS lines 193-196 |

### FICO Credit Score Validation (1275-EDIT-FICO-SCORE)

| #   | Rule | Condition | Action | Source Location |
| --- | ---- | --------- | ------ | --------------- |
| 99  | FICO score must be in range 300-850 | `FICO-RANGE-IS-VALID` (88-level: VALUES 300 THROUGH 850 on ACUP-NEW-CUST-FICO-SCORE PIC 9(03)) | Set INPUT-ERROR; set FLG-FICO-SCORE-NOT-OK; message '[field]: should be between 300 and 850' | 1275-EDIT-FICO-SCORE lines 1108-1123 |
| 100 | FICO range check only called if numeric check passes | `FLG-FICO-SCORE-ISVALID` must be TRUE before calling 1275 | Guards against running range check on non-numeric data | 1200-EDIT-MAP-INPUTS lines 147-150 |

### Cross-Field Validation: State/Zip Combination (1280-EDIT-US-STATE-ZIP-CD)

| #   | Rule | Condition | Action | Source Location |
| --- | ---- | --------- | ------ | --------------- |
| 101 | Zip code must be valid for the given state | Build composite key STATE-CD + ZIP(1:2); check `VALID-US-STATE-ZIP-CD2-COMBO` from CSLKPCDY lookup | Set INPUT-ERROR; set FLG-STATE-NOT-OK AND FLG-ZIPCODE-NOT-OK; message 'Invalid zip code for state' | 1280-EDIT-US-STATE-ZIP-CD lines 1130-1150 |
| 102 | Cross-field state/zip check only runs if both individual edits pass | `FLG-STATE-ISVALID` AND `FLG-ZIPCODE-ISVALID` must both be TRUE | Prevents spurious cross-field error when underlying fields are already invalid | 1200-EDIT-MAP-INPUTS lines 259-263 |

### Validation Final Status (1200-EDIT-MAP-INPUTS end)

| #   | Rule | Condition | Action | Source Location |
| --- | ---- | --------- | ------ | --------------- |
| 103 | All validators passed: advance state to awaiting confirmation | `INPUT-ERROR` is FALSE (INPUT-OK is TRUE) after all validators complete | Set `ACUP-CHANGES-OK-NOT-CONFIRMED` to TRUE -- enables PF5 key on next display | 1200-EDIT-MAP-INPUTS lines 265-269 |
| 104 | Any validator failed: retain error state | `INPUT-ERROR` is TRUE | ACUP-CHANGE-ACTION remains 'E' (ACUP-CHANGES-NOT-OK); screen re-displayed with error message | 1200-EDIT-MAP-INPUTS lines 265-269 |

### Error Message Priority (WS-RETURN-MSG)

| #   | Rule | Condition | Action | Source Location |
| --- | ---- | --------- | ------ | --------------- |
| 105 | Only the first error message is retained | Every error STRING block is guarded by `IF WS-RETURN-MSG-OFF` | WS-RETURN-MSG is only written once per screen submission; subsequent errors do not overwrite it | All 1210/1215/1220/1225/1230/1235/1240/1245/1250/1260/1265/1270/1275/1280 paragraphs |

### Action Decision Routing (2000-DECIDE-ACTION)

| #   | Rule | Condition | Action | Source Location |
| --- | ---- | --------- | ------ | --------------- |
| 106 | No data fetched yet: fetch account record | `ACUP-DETAILS-NOT-FETCHED` (ACUP-CHANGE-ACTION = LOW-VALUES or SPACES) AND `FLG-ACCTFILTER-ISVALID` | Clear WS-RETURN-MSG; PERFORM 9000-READ-ACCT THRU 9000-READ-ACCT-EXIT; if `FOUND-CUST-IN-MASTER` then SET `ACUP-SHOW-DETAILS` TO TRUE | 2000-DECIDE-ACTION lines 15-27 |
| 107 | PF12 cancel while account filter valid: re-fetch account | `CCARD-AID-PFK12` AND `FLG-ACCTFILTER-ISVALID` | Same as rule 106: clear WS-RETURN-MSG; PERFORM 9000-READ-ACCT; if customer found then SET `ACUP-SHOW-DETAILS` TO TRUE | 2000-DECIDE-ACTION lines 19-27 |
| 108 | Details shown with no errors and no changes: do nothing (CONTINUE) | `ACUP-SHOW-DETAILS` AND (`INPUT-ERROR` OR `NO-CHANGES-DETECTED`) | CONTINUE -- screen is re-displayed as-is without state change | 2000-DECIDE-ACTION lines 32-38 |
| 109 | Details shown, changes detected, no input errors: advance to confirmation state | `ACUP-SHOW-DETAILS` AND NOT `INPUT-ERROR` AND NOT `NO-CHANGES-DETECTED` | SET `ACUP-CHANGES-OK-NOT-CONFIRMED` TO TRUE (ACUP-CHANGE-ACTION = 'N') -- PF5 key becomes available | 2000-DECIDE-ACTION lines 36-38 |
| 110 | Validation errors present: do nothing (CONTINUE) | `ACUP-CHANGES-NOT-OK` (ACUP-CHANGE-ACTION = 'E') | CONTINUE -- error state retained; screen re-displayed with existing error message | 2000-DECIDE-ACTION lines 43-44 |
| 111 | Changes confirmed with PF5: attempt to write updates | `ACUP-CHANGES-OK-NOT-CONFIRMED` (ACUP-CHANGE-ACTION = 'N') AND `CCARD-AID-PFK05` | PERFORM 9600-WRITE-PROCESSING THRU 9600-WRITE-PROCESSING-EXIT; then evaluate write outcome | 2000-DECIDE-ACTION lines 49-62 |
| 112 | Write outcome: account record could not be locked | `COULD-NOT-LOCK-ACCT-FOR-UPDATE` (WS-RETURN-MSG = 'Could not lock account record for update') | SET `ACUP-CHANGES-OKAYED-LOCK-ERROR` TO TRUE (ACUP-CHANGE-ACTION = 'L') | 2000-DECIDE-ACTION lines 54-55 |
| 113 | Write outcome: record was locked but write failed | `LOCKED-BUT-UPDATE-FAILED` (WS-RETURN-MSG = 'Update of record failed') | SET `ACUP-CHANGES-OKAYED-BUT-FAILED` TO TRUE (ACUP-CHANGE-ACTION = 'F') | 2000-DECIDE-ACTION lines 56-57 |
| 114 | Write outcome: concurrent modification detected -- record changed by another user between fetch and save | `DATA-WAS-CHANGED-BEFORE-UPDATE` (WS-RETURN-MSG = 'Record changed by some one else. Please review') | SET `ACUP-SHOW-DETAILS` TO TRUE (ACUP-CHANGE-ACTION = 'S') -- forces re-display of re-fetched data so user can review before retrying | 2000-DECIDE-ACTION lines 58-59 |
| 115 | Write outcome: update succeeded | WHEN OTHER after write processing | SET `ACUP-CHANGES-OKAYED-AND-DONE` TO TRUE (ACUP-CHANGE-ACTION = 'C') | 2000-DECIDE-ACTION lines 60-61 |
| 116 | Confirmation not given (WHEN OTHER on outer EVALUATE): re-display for confirmation | `ACUP-CHANGES-OK-NOT-CONFIRMED` AND NOT `CCARD-AID-PFK05` | CONTINUE -- details screen re-sent prompting user to press PF5 | 2000-DECIDE-ACTION lines 67-68 |
| 117 | Post-update success: reset COMMAREA navigation fields if no prior caller | `ACUP-CHANGES-OKAYED-AND-DONE` AND (`CDEMO-FROM-TRANID = LOW-VALUES` OR `CDEMO-FROM-TRANID = SPACES`) | MOVE ZEROES to CDEMO-ACCT-ID and CDEMO-CARD-NUM; MOVE LOW-VALUES to CDEMO-ACCT-STATUS | 2000-DECIDE-ACTION lines 72-79 |
| 118 | Transition to details view after post-update | `ACUP-CHANGES-OKAYED-AND-DONE` | SET `ACUP-SHOW-DETAILS` TO TRUE before COMMAREA reset check | 2000-DECIDE-ACTION lines 73-79 |
| 119 | Unexpected program state: abend with code 0001 | WHEN OTHER (no EVALUATE arm matched) | MOVE 'COACTUPC' to ABEND-CULPRIT; MOVE '0001' to ABEND-CODE; MOVE SPACES to ABEND-REASON; MOVE 'UNEXPECTED DATA SCENARIO' to ABEND-MSG; PERFORM ABEND-ROUTINE THRU ABEND-ROUTINE-EXIT | 2000-DECIDE-ACTION lines 80-87 |

## Calculations

| Calculation | Formula / Logic | Input Fields | Output Field | Source Location |
| ----------- | --------------- | ------------ | ------------ | --------------- |
| COMMAREA split | WS-THIS-PROGCOMMAREA extracted as `DFHCOMMAREA(LENGTH OF CARDDEMO-COMMAREA + 1 : LENGTH OF WS-THIS-PROGCOMMAREA)` | DFHCOMMAREA, EIBCALEN | WS-THIS-PROGCOMMAREA | 0000-MAIN lines 40-42 |
| State/Zip combo key | STRING STATE-CD + ZIP(1:2) DELIMITED BY SIZE INTO US-STATE-AND-FIRST-ZIP2 | ACUP-NEW-CUST-ADDR-STATE-CD, ACUP-NEW-CUST-ADDR-ZIP | US-STATE-AND-FIRST-ZIP2 | 1280-EDIT-US-STATE-ZIP-CD line 1131-1134 |

## Error Handling

| Condition | Action | Return Code | Source Location |
| --------- | ------ | ----------- | --------------- |
| Any CICS abend | Divert execution to ABEND-ROUTINE label | N/A (CICS mechanism) | 0000-MAIN lines 12-14 |
| Invalid AID key pressed | Override AID to ENTER (CCARD-AID-ENTER set TRUE); program re-displays screen without processing | PFK-INVALID flag | 0000-MAIN lines 64-66 |
| Update failed (lock error, state 'L') | Reset program state; prompt user for new account number; message implied by ACUP-CHANGES-FAILED state | 'L' in ACUP-CHANGE-ACTION | 0000-MAIN lines 130-139 |
| Update failed (write error, state 'F') | Reset program state; prompt user for new account number | 'F' in ACUP-CHANGE-ACTION | 0000-MAIN lines 130-139 |
| Account number blank | Set INPUT-ERROR; WS-RETURN-MSG = 'Account number not provided'; zero CDEMO-ACCT-ID | FLG-ACCTFILTER-BLANK | 1210-EDIT-ACCOUNT lines 383-390 |
| Account number not numeric or zero | Set INPUT-ERROR; WS-RETURN-MSG = 'Account Number if supplied must be a 11 digit Non-Zero Number' | FLG-ACCTFILTER-NOT-OK | 1210-EDIT-ACCOUNT lines 396-407 |
| No search criteria received | Set NO-SEARCH-CRITERIA-RECEIVED (WS-RETURN-MSG = 'No input received') | FLG-ACCTFILTER-BLANK leads to NO-SEARCH-CRITERIA-RECEIVED | 1200-EDIT-MAP-INPUTS lines 35-37 |
| No changes detected | Set NO-CHANGES-DETECTED (WS-RETURN-MSG = 'No change detected with respect to values fetched.') | WS-DATACHANGED-FLAG = '0' | 1205-COMPARE-OLD-NEW line 363 |
| SSN Part 1 invalid (000, 666, or 900-999) | Set INPUT-ERROR; WS-RETURN-MSG = 'SSN: First 3 chars: should not be 000, 666, or between 900 and 999' | FLG-EDIT-US-SSN-PART1-NOT-OK | 1265-EDIT-US-SSN lines 1044-1054 |
| FICO score out of range (not 300-850) | Set INPUT-ERROR; WS-RETURN-MSG = '[field]: should be between 300 and 850' | FLG-FICO-SCORE-NOT-OK | 1275-EDIT-FICO-SCORE lines 1112-1121 |
| Invalid US state code | Set INPUT-ERROR; WS-RETURN-MSG = '[field]: is not a valid state code' | FLG-STATE-NOT-OK | 1270-EDIT-US-STATE-CD lines 1092-1103 |
| Invalid state/zip combination | Set INPUT-ERROR; WS-RETURN-MSG = 'Invalid zip code for state'; set both FLG-STATE-NOT-OK and FLG-ZIPCODE-NOT-OK | Two flags set | 1280-EDIT-US-STATE-ZIP-CD lines 1139-1147 |
| Phone area code not a valid North America general-purpose code | Set INPUT-ERROR; WS-RETURN-MSG = '[field]: Not valid North America general purpose area code' | FLG-EDIT-US-PHONEA-NOT-OK | EDIT-AREA-CODE lines 895-904 |
| Account record could not be locked for update | SET ACUP-CHANGES-OKAYED-LOCK-ERROR; WS-RETURN-MSG = 'Could not lock account record for update' | ACUP-CHANGE-ACTION = 'L' | 2000-DECIDE-ACTION lines 54-55 |
| Record locked but REWRITE failed | SET ACUP-CHANGES-OKAYED-BUT-FAILED; WS-RETURN-MSG = 'Update of record failed' | ACUP-CHANGE-ACTION = 'F' | 2000-DECIDE-ACTION lines 56-57 |
| Concurrent modification: record changed by another user before save | SET ACUP-SHOW-DETAILS; WS-RETURN-MSG = 'Record changed by some one else. Please review'; re-display re-fetched data | ACUP-CHANGE-ACTION = 'S' | 2000-DECIDE-ACTION lines 58-59 |
| Unexpected program state in 2000-DECIDE-ACTION | PERFORM ABEND-ROUTINE with ABEND-CODE '0001', ABEND-MSG 'UNEXPECTED DATA SCENARIO', ABEND-CULPRIT 'COACTUPC' | '0001' | 2000-DECIDE-ACTION lines 80-87 |

## Control Flow

Key PERFORM and CALL sequences in execution order for the main dispatch path:

1. **0000-MAIN** -- Entry point. Initialises storage, loads COMMAREA, determines entry type, validates AID key, then dispatches via EVALUATE TRUE.
2. **YYYY-STORE-PFKEY** -- Remaps PF key input to internal AID flags before the main dispatch logic.
3. **EVALUATE TRUE dispatch** -- Five branches:
   - PF3 pressed: issue SYNCPOINT then XCTL to calling program or COMEN01C.
   - Fresh / menu entry: PERFORM 3000-SEND-MAP then COMMON-RETURN.
   - Post-update (success or fail): reset state, PERFORM 3000-SEND-MAP, then COMMON-RETURN.
   - Normal processing (WHEN OTHER): sequentially PERFORM 1000-PROCESS-INPUTS, 2000-DECIDE-ACTION, 3000-SEND-MAP, then COMMON-RETURN.
4. **1000-PROCESS-INPUTS** -- Receives map input (1100-RECEIVE-MAP) then validates all input fields (1200-EDIT-MAP-INPUTS).
5. **1200-EDIT-MAP-INPUTS** -- Master validation dispatcher. When data is not yet fetched: calls 1210-EDIT-ACCOUNT only. When data is fetched and changes detected: calls 1205-COMPARE-OLD-NEW, then sequentially invokes 18 individual field validators: 1220 (Account Status), EDIT-DATE-CCYYMMDD (Open Date), 1250 (Credit Limit), EDIT-DATE-CCYYMMDD (Expiry Date), 1250 (Cash Credit Limit), EDIT-DATE-CCYYMMDD (Reissue Date), 1250 (Current Balance), 1250 (Current Cycle Credit), 1250 (Current Cycle Debit), 1265 (SSN), EDIT-DATE-CCYYMMDD + EDIT-DATE-OF-BIRTH (Date of Birth), 1245 + 1275 (FICO Score), 1225 (First Name), 1235 (Middle Name), 1225 (Last Name), 1215 (Address Line 1), 1225 + 1270 (State), 1245 (Zip), 1225 (City), 1225 (Country), 1260 (Phone 1), 1260 (Phone 2), 1245 (EFT Account ID), 1220 (Primary Card Holder), then cross-field 1280 (State/Zip). Sets ACUP-CHANGES-OK-NOT-CONFIRMED if all pass.
6. **1205-COMPARE-OLD-NEW** -- Field-by-field comparison of 29 account and customer fields between OLD and NEW snapshots to detect actual changes; returns CHANGE-HAS-OCCURRED or NO-CHANGES-DETECTED.
7. **2000-DECIDE-ACTION** -- State machine dispatcher. Uses EVALUATE TRUE across ACUP-CHANGE-ACTION and CCARD-AID-PFK* to route to the appropriate action:
   - ACUP-DETAILS-NOT-FETCHED or CCARD-AID-PFK12 (cancel): PERFORM 9000-READ-ACCT to load data.
   - ACUP-SHOW-DETAILS: advance to ACUP-CHANGES-OK-NOT-CONFIRMED if changes valid, else CONTINUE.
   - ACUP-CHANGES-NOT-OK: CONTINUE (error state persists).
   - ACUP-CHANGES-OK-NOT-CONFIRMED + PF5: PERFORM 9600-WRITE-PROCESSING; evaluate write result into one of four outcome states (lock error, write failure, concurrent-modification, or success).
   - ACUP-CHANGES-OK-NOT-CONFIRMED without PF5: CONTINUE (wait for PF5).
   - ACUP-CHANGES-OKAYED-AND-DONE: SET ACUP-SHOW-DETAILS; reset COMMAREA navigation fields if no prior caller.
   - WHEN OTHER: ABEND with code '0001' and message 'UNEXPECTED DATA SCENARIO'.
8. **3000-SEND-MAP** -- Prepares and sends BMS map CACTUPA (mapset COACTUP): screen init, variable setup, info message, attribute setup, and SEND.
9. **COMMON-RETURN** -- Returns control to CICS (EXEC CICS RETURN with TRANSID 'CAUP' and updated COMMAREA).
10. **ABEND-ROUTINE** -- Invoked on any CICS abend (via HANDLE ABEND); performs error logging and clean termination.
