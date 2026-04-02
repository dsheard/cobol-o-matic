---
type: business-rules
program: COCRDSLC
program_type: online
status: draft
confidence: high
last_pass: 5
calls: []
called_by:
- COCRDLIC
uses_copybooks:
- COCOM01Y
- COCRDSL
- COTTL01Y
- CSDAT01Y
- CSMSG01Y
- CSMSG02Y
- CSSTRPFY
- CSUSR01Y
- CVACT02Y
- CVCRD01Y
- CVCUS01Y
reads:
- CARDAIX
- CARDDAT
writes: []
db_tables: []
transactions:
- CCDL
mq_queues: []
---

# COCRDSLC -- Business Rules

## Program Purpose

COCRDSLC (transaction CCDL) is the credit card detail selection screen. It accepts an account number and a card number from the user, validates both inputs, reads the card record from the CARDDAT VSAM file by card number (primary key via WS-CARD-RID-CARDNUM, 16 bytes), and then displays the card detail results on map CCRDSLA (mapset COCRDSL). An alternate-index read path via CARDAIX (9150-GETCARD-BYACCT) is fully coded but is not invoked by 9000-READ-DATA -- it can only be reached if called directly. The program is the entry point for the card detail flow; PF3 returns control to the calling program or main menu (COMEN01C / CM00). COCRDLIC (the card list program) XCTLs to this program when the user selects a card from the list.

## Input / Output

| Direction | Resource | Type | Description |
| --------- | -------- | ---- | ----------- |
| IN | CCRDSLAI (mapset COCRDSL, map CCRDSLA) | CICS BMS | User-entered account ID (11 digits) and card number (16 digits) |
| IN | CARDDAT | CICS VSAM File | Card record read by card number (primary key WS-CARD-RID-CARDNUM, 16 bytes) |
| IN | CARDAIX | CICS VSAM File | Card record read by account ID (alternate index WS-CARD-RID-ACCT-ID, 11 bytes) -- coded in 9150-GETCARD-BYACCT but not invoked in current 9000-READ-DATA path |
| IN | DFHCOMMAREA | CICS Commarea | CARDDEMO-COMMAREA (offset 1) + WS-THIS-PROGCOMMAREA (offset LENGTH OF CARDDEMO-COMMAREA + 1) passed on re-entry |
| OUT | CCRDSLAO (mapset COCRDSL, map CCRDSLA) | CICS BMS | Card detail screen: embossed name, expiry month/year, card status, error/info messages |
| OUT | CARDDEMO-COMMAREA | CICS Commarea | Updated commarea returned via EXEC CICS RETURN TRANSID(LIT-THISTRANID = 'CCDL') with WS-COMMAREA (2000 bytes) |

## Business Rules

### Entry Condition and Commarea Initialisation

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 1 | Fresh entry -- no commarea | EIBCALEN = 0 OR (CDEMO-FROM-PROGRAM = LIT-MENUPGM ('COMEN01C') AND NOT CDEMO-PGM-REENTER) | INITIALIZE CARDDEMO-COMMAREA and WS-THIS-PROGCOMMAREA; treat as first entry | 0000-MAIN lines 268-272 |
| 2 | Re-entry -- commarea present | EIBCALEN > 0 AND NOT first-entry condition | MOVE DFHCOMMAREA(1:LENGTH OF CARDDEMO-COMMAREA) to CARDDEMO-COMMAREA; MOVE DFHCOMMAREA(LENGTH OF CARDDEMO-COMMAREA + 1: LENGTH OF WS-THIS-PROGCOMMAREA) to WS-THIS-PROGCOMMAREA | 0000-MAIN lines 273-278 |

### PF Key Validation and Mapping

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 3 | PF key normalisation (PF13-PF24 remapping) | EIBAID = DFHPF13 through DFHPF24 | Map to equivalent PF01-PF12 in CCARD-AID-PFKxx; PF13=PF01, PF14=PF02, PF15=PF03, etc. | YYYY-STORE-PFKEY (CSSTRPFY copybook, line 855) |
| 4 | ENTER key is valid | CCARD-AID-ENTER | Set PFK-VALID | 0000-MAIN lines 292-295 |
| 5 | PF3 is valid | CCARD-AID-PFK03 | Set PFK-VALID | 0000-MAIN lines 292-295 |
| 6 | Any other key is treated as ENTER | PFK-INVALID (any AID other than ENTER or PF3) | Set CCARD-AID-ENTER to TRUE; continue processing as if Enter was pressed | 0000-MAIN lines 297-299 |

### Main Dispatch Routing

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 7 | PF3 -- exit / return to caller | CCARD-AID-PFK03 | Determine return target: if CDEMO-FROM-TRANID is LOW-VALUES or SPACES use LIT-MENUTRANID ('CM00') and LIT-MENUPGM ('COMEN01C'); otherwise use CDEMO-FROM-TRANID and CDEMO-FROM-PROGRAM. Set CDEMO-FROM-TRANID=LIT-THISTRANID ('CCDL'), CDEMO-FROM-PROGRAM=LIT-THISPGM ('COCRDSLC'), CDEMO-USRTYP-USER, CDEMO-PGM-ENTER, CDEMO-LAST-MAPSET=LIT-THISMAPSET ('COCRDSL '), CDEMO-LAST-MAP=LIT-THISMAP ('CCRDSLA'), then EXEC CICS XCTL to CDEMO-TO-PROGRAM with CARDDEMO-COMMAREA | 0000-MAIN lines 305-334 |
| 8 | Entry from card list program with pre-validated criteria | CDEMO-PGM-ENTER AND CDEMO-FROM-PROGRAM = LIT-CCLISTPGM ('COCRDLIC') | Set INPUT-OK, move CDEMO-ACCT-ID to CC-ACCT-ID-N and CDEMO-CARD-NUM to CC-CARD-NUM-N; PERFORM 9000-READ-DATA then 1000-SEND-MAP; GO TO COMMON-RETURN | 0000-MAIN lines 339-348 |
| 9 | Entry from any other context (first display) | CDEMO-PGM-ENTER (not from COCRDLIC) | PERFORM 1000-SEND-MAP (blank screen for data entry); GO TO COMMON-RETURN | 0000-MAIN lines 349-356 |
| 10 | Re-entry (user has typed data and pressed Enter) | CDEMO-PGM-REENTER | PERFORM 2000-PROCESS-INPUTS; if INPUT-ERROR re-display map; else PERFORM 9000-READ-DATA then 1000-SEND-MAP | 0000-MAIN lines 357-371 |
| 11 | Unexpected scenario | WHEN OTHER (none of the EVALUATE branches match) | Set ABEND-CULPRIT=LIT-THISPGM ('COCRDSLC'), ABEND-CODE='0001', ABEND-REASON=SPACES; move 'UNEXPECTED DATA SCENARIO' to WS-RETURN-MSG; PERFORM SEND-PLAIN-TEXT (debug utility -- sends plain text and issues EXEC CICS RETURN) | 0000-MAIN lines 373-380 |
| 12 | Error slip-through guard | INPUT-ERROR after EVALUATE (handles error conditions that fall through the EVALUATE without a GO TO) | Move WS-RETURN-MSG to CCARD-ERROR-MSG; re-display map via 1000-SEND-MAP; GO TO COMMON-RETURN | 0000-MAIN lines 386-391 |

### Input Validation -- Account Number (2210-EDIT-ACCOUNT)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 13 | Account number is mandatory -- blank/zero check | CC-ACCT-ID = LOW-VALUES OR SPACES OR CC-ACCT-ID-N = ZEROS | Set INPUT-ERROR, Set FLG-ACCTFILTER-BLANK; if WS-RETURN-MSG-OFF then SET WS-PROMPT-FOR-ACCT TO TRUE (message: 'Account number not provided'); MOVE ZEROES to CDEMO-ACCT-ID; GO TO 2210-EDIT-ACCOUNT-EXIT | 2210-EDIT-ACCOUNT lines 651-661 |
| 14 | Account number must be numeric (11 digits) | CC-ACCT-ID IS NOT NUMERIC | Set INPUT-ERROR, Set FLG-ACCTFILTER-NOT-OK; if WS-RETURN-MSG-OFF then MOVE 'ACCOUNT FILTER,IF SUPPLIED MUST BE A 11 DIGIT NUMBER' to WS-RETURN-MSG; MOVE ZERO to CDEMO-ACCT-ID; GO TO 2210-EDIT-ACCOUNT-EXIT | 2210-EDIT-ACCOUNT lines 665-674 |
| 15 | Account number accepted | CC-ACCT-ID passes all checks (non-blank, numeric) | MOVE CC-ACCT-ID to CDEMO-ACCT-ID; Set FLG-ACCTFILTER-ISVALID | 2210-EDIT-ACCOUNT lines 675-678 |

### Input Validation -- Card Number (2220-EDIT-CARD)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 16 | Card number is mandatory -- blank/zero check | CC-CARD-NUM = LOW-VALUES OR SPACES OR CC-CARD-NUM-N = ZEROS | Set INPUT-ERROR, Set FLG-CARDFILTER-BLANK; if WS-RETURN-MSG-OFF then SET WS-PROMPT-FOR-CARD TO TRUE (message: 'Card number not provided'); MOVE ZEROES to CDEMO-CARD-NUM; GO TO 2220-EDIT-CARD-EXIT. NOTE: INPUT-ERROR is raised for a blank card -- card number is effectively mandatory in the current code path even though 9150 provides an account-only read | 2220-EDIT-CARD lines 691-702 |
| 17 | Card number must be numeric (16 digits) | CC-CARD-NUM IS NOT NUMERIC | Set INPUT-ERROR, Set FLG-CARDFILTER-NOT-OK; if WS-RETURN-MSG-OFF then MOVE 'CARD ID FILTER,IF SUPPLIED MUST BE A 16 DIGIT NUMBER' to WS-RETURN-MSG; MOVE ZERO to CDEMO-CARD-NUM; GO TO 2220-EDIT-CARD-EXIT | 2220-EDIT-CARD lines 706-715 |
| 18 | Card number accepted | CC-CARD-NUM passes all checks (non-blank, numeric) | MOVE CC-CARD-NUM-N to CDEMO-CARD-NUM; Set FLG-CARDFILTER-ISVALID | 2220-EDIT-CARD lines 716-718 |

### Cross-Field Validation (2200-EDIT-MAP-INPUTS)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 19 | At least one search criterion must be supplied | FLG-ACCTFILTER-BLANK AND FLG-CARDFILTER-BLANK (both fields empty after individual edits) | SET NO-SEARCH-CRITERIA-RECEIVED TO TRUE; this sets WS-RETURN-MSG = 'No input received' and INPUT-ERROR implicitly (FLG-ACCTFILTER-BLANK implies INPUT-ERROR was already set) | 2200-EDIT-MAP-INPUTS lines 637-640 |
| 20 | Asterisk or spaces treated as blank account | ACCTSIDI OF CCRDSLAI = '*' OR SPACES | MOVE LOW-VALUES to CC-ACCT-ID; validated fields will then fail the mandatory check | 2200-EDIT-MAP-INPUTS lines 615-620 |
| 21 | Asterisk or spaces treated as blank card | CARDSIDI OF CCRDSLAI = '*' OR SPACES | MOVE LOW-VALUES to CC-CARD-NUM; validated fields will then fail the mandatory check | 2200-EDIT-MAP-INPUTS lines 622-627 |
| 22 | Validation flags reset before each validation pass | Always at entry to 2200-EDIT-MAP-INPUTS | SET INPUT-OK, FLG-CARDFILTER-ISVALID, FLG-ACCTFILTER-ISVALID all set TRUE before individual field edits begin | 2200-EDIT-MAP-INPUTS lines 610-612 |
| 23 | After validation, CCARD-NEXT-PROG/MAPSET/MAP are set | Always at exit of 2000-PROCESS-INPUTS | MOVE LIT-THISPGM to CCARD-NEXT-PROG ('COCRDSLC'), LIT-THISMAPSET to CCARD-NEXT-MAPSET ('COCRDSL '), LIT-THISMAP to CCARD-NEXT-MAP ('CCRDSLA'); WS-RETURN-MSG moved to CCARD-ERROR-MSG | 2000-PROCESS-INPUTS lines 587-590 |

### Map Receive (2100-RECEIVE-MAP)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 52 | Map receive does not check RESP | EXEC CICS RECEIVE MAP stores RESP to WS-RESP-CD and RESP2 to WS-REAS-CD, but neither is tested after the RECEIVE | If MAPFAIL occurs (e.g., user presses PF3 or Clear from a blank screen), execution continues with whatever stale data is in CCRDSLAI from the prior SEND; no MAPFAIL guard is present. This means a MAPFAIL will cause input validation to run against the previous screen contents | 2100-RECEIVE-MAP lines 597-603 |

### Screen Attribute Rules (1300-SETUP-SCREEN-ATTRS)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 24 | Protect input fields when navigated from card list | CDEMO-LAST-MAPSET = LIT-CCLISTMAPSET ('COCRDLI') AND CDEMO-FROM-PROGRAM = LIT-CCLISTPGM ('COCRDLIC') | Move DFHBMPRF to ACCTSIDA and CARDSIDA of CCRDSLAI (fields protected, not enterable) | 1300-SETUP-SCREEN-ATTRS lines 505-508 |
| 25 | Allow input when entered directly | NOT (from COCRDLIC with mapset COCRDLI) | Move DFHBMFSE to ACCTSIDA and CARDSIDA of CCRDSLAI (unprotected, MDT set) | 1300-SETUP-SCREEN-ATTRS lines 509-511 |
| 26 | Cursor on account field when account invalid or blank | FLG-ACCTFILTER-NOT-OK OR FLG-ACCTFILTER-BLANK | Move -1 to ACCTSIDL of CCRDSLAI (positions cursor on account input field) | 1300-SETUP-SCREEN-ATTRS lines 516-518 |
| 27 | Cursor on card field when card invalid or blank | FLG-CARDFILTER-NOT-OK OR FLG-CARDFILTER-BLANK | Move -1 to CARDSIDL of CCRDSLAI | 1300-SETUP-SCREEN-ATTRS lines 519-521 |
| 28 | Default cursor position | WHEN OTHER (no field error) | Move -1 to ACCTSIDL of CCRDSLAI (defaults cursor to account field) | 1300-SETUP-SCREEN-ATTRS lines 522-523 |
| 29 | Default colour for fields from card list | CDEMO-LAST-MAPSET = 'COCRDLI' AND CDEMO-FROM-PROGRAM = 'COCRDLIC' | Move DFHDFCOL to ACCTSIDC and CARDSIDC of CCRDSLAO (default colour for protected fields) | 1300-SETUP-SCREEN-ATTRS lines 527-531 |
| 30 | Colour account field red when invalid | FLG-ACCTFILTER-NOT-OK | Move DFHRED to ACCTSIDC of CCRDSLAO | 1300-SETUP-SCREEN-ATTRS lines 533-535 |
| 31 | Colour card field red when invalid | FLG-CARDFILTER-NOT-OK | Move DFHRED to CARDSIDC of CCRDSLAO | 1300-SETUP-SCREEN-ATTRS lines 537-539 |
| 32 | Show asterisk placeholder and red for blank account on re-entry | FLG-ACCTFILTER-BLANK AND CDEMO-PGM-REENTER | Move '*' to ACCTSIDO and DFHRED to ACCTSIDC of CCRDSLAO | 1300-SETUP-SCREEN-ATTRS lines 541-545 |
| 33 | Show asterisk placeholder and red for blank card on re-entry | FLG-CARDFILTER-BLANK AND CDEMO-PGM-REENTER | Move '*' to CARDSIDO and DFHRED to CARDSIDC of CCRDSLAO | 1300-SETUP-SCREEN-ATTRS lines 547-551 |
| 34 | Dim info message area when no informational message | WS-NO-INFO-MESSAGE (SPACES or LOW-VALUES) | Move DFHBMDAR to INFOMSGC of CCRDSLAO | 1300-SETUP-SCREEN-ATTRS lines 553-554 |
| 35 | Neutral colour for info message when message present | NOT WS-NO-INFO-MESSAGE | Move DFHNEUTR to INFOMSGC of CCRDSLAO | 1300-SETUP-SCREEN-ATTRS lines 555-556 |

### Screen Variable Population (1200-SETUP-SCREEN-VARS)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 36 | Prompt for input on initial entry (no commarea) | EIBCALEN = 0 | SET WS-PROMPT-FOR-INPUT TO TRUE (message: 'Please enter Account and Card Number') placed in WS-INFO-MSG; account/card output fields not populated | 1200-SETUP-SCREEN-VARS lines 459-461 |
| 37 | Show account ID on screen if non-zero | EIBCALEN > 0 AND CDEMO-ACCT-ID != 0 | Move CC-ACCT-ID to ACCTSIDO of CCRDSLAO | 1200-SETUP-SCREEN-VARS lines 462-466 |
| 38 | Blank account ID field if zero | EIBCALEN > 0 AND CDEMO-ACCT-ID = 0 | Move LOW-VALUES to ACCTSIDO of CCRDSLAO | 1200-SETUP-SCREEN-VARS line 463 |
| 39 | Show card number on screen if non-zero | EIBCALEN > 0 AND CDEMO-CARD-NUM != 0 | Move CC-CARD-NUM to CARDSIDO of CCRDSLAO | 1200-SETUP-SCREEN-VARS lines 468-472 |
| 40 | Blank card number field if zero | EIBCALEN > 0 AND CDEMO-CARD-NUM = 0 | Move LOW-VALUES to CARDSIDO of CCRDSLAO | 1200-SETUP-SCREEN-VARS line 469 |
| 41 | Populate card detail fields when card found | FOUND-CARDS-FOR-ACCOUNT (WS-INFO-MSG = '   Displaying requested details') | Move CARD-EMBOSSED-NAME to CRDNAMEO; move CARD-EXPIRAION-DATE to CARD-EXPIRAION-DATE-X; move CARD-EXPIRY-MONTH to EXPMONO; move CARD-EXPIRY-YEAR to EXPYEARO; move CARD-ACTIVE-STATUS to CRDSTCDO | 1200-SETUP-SCREEN-VARS lines 474-485 |
| 42 | Default prompt when no info message set | WS-NO-INFO-MESSAGE (spaces or LOW-VALUES) | SET WS-PROMPT-FOR-INPUT TO TRUE (overwrites blank WS-INFO-MSG with 'Please enter Account and Card Number') | 1200-SETUP-SCREEN-VARS lines 490-492 |
| 43 | Always move WS-RETURN-MSG and WS-INFO-MSG to screen | Unconditional at end of 1200-SETUP-SCREEN-VARS | Move WS-RETURN-MSG to ERRMSGO of CCRDSLAO; move WS-INFO-MSG to INFOMSGO of CCRDSLAO | 1200-SETUP-SCREEN-VARS lines 494-496 |

### Data Retrieval Rules (9100-GETCARD-BYACCTCARD)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 44 | Read card by card number (primary key) | Always when 9000-READ-DATA is called | MOVE CC-CARD-NUM to WS-CARD-RID-CARDNUM; EXEC CICS READ FILE(LIT-CARDFILENAME = 'CARDDAT ') RIDFLD(WS-CARD-RID-CARDNUM) KEYLENGTH(LENGTH OF WS-CARD-RID-CARDNUM) INTO(CARD-RECORD) | 9100-GETCARD-BYACCTCARD lines 740-750 |
| 45 | Card found | DFHRESP(NORMAL) | SET FOUND-CARDS-FOR-ACCOUNT TO TRUE (sets WS-INFO-MSG = '   Displaying requested details'); card details available for screen population | 9100-GETCARD-BYACCTCARD lines 753-754 |
| 46 | Card not found | DFHRESP(NOTFND) | Set INPUT-ERROR, FLG-ACCTFILTER-NOT-OK, FLG-CARDFILTER-NOT-OK; if WS-RETURN-MSG-OFF then SET DID-NOT-FIND-ACCTCARD-COMBO TO TRUE (WS-RETURN-MSG = 'Did not find cards for this search condition') | 9100-GETCARD-BYACCTCARD lines 755-761 |
| 47 | File read error (any other CICS response) | WS-RESP-CD not NORMAL or NOTFND | Set INPUT-ERROR; if WS-RETURN-MSG-OFF then set FLG-ACCTFILTER-NOT-OK; MOVE 'READ' to ERROR-OPNAME, LIT-CARDFILENAME to ERROR-FILE, WS-RESP-CD to ERROR-RESP, WS-REAS-CD to ERROR-RESP2; MOVE WS-FILE-ERROR-MESSAGE to WS-RETURN-MSG (format: 'File Error: READ on CARDDAT  returned RESP nnn ,RESP2 nnn') | 9100-GETCARD-BYACCTCARD lines 762-771 |

### Alternate Index Read (9150-GETCARD-BYACCT -- coded but not invoked by current 9000-READ-DATA)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 48 | Read card by account ID (alternate index) | Called explicitly (not reachable via 9000-READ-DATA in current code) | EXEC CICS READ FILE(LIT-CARDFILENAME-ACCT-PATH = 'CARDAIX ') RIDFLD(WS-CARD-RID-ACCT-ID) KEYLENGTH(LENGTH OF WS-CARD-RID-ACCT-ID) INTO(CARD-RECORD) | 9150-GETCARD-BYACCT lines 783-791 |
| 49 | Card found via account index | DFHRESP(NORMAL) | SET FOUND-CARDS-FOR-ACCOUNT TO TRUE | 9150-GETCARD-BYACCT line 795 |
| 50 | Account not found in card cross-reference | DFHRESP(NOTFND) | Set INPUT-ERROR, FLG-ACCTFILTER-NOT-OK; SET DID-NOT-FIND-ACCT-IN-CARDXREF TO TRUE (WS-RETURN-MSG = 'Did not find this account in cards database') -- NOTE: no WS-RETURN-MSG-OFF guard here, unlike the CARDDAT path | 9150-GETCARD-BYACCT lines 796-799 |
| 51 | File read error on alternate index | WS-RESP-CD not NORMAL or NOTFND | Set INPUT-ERROR, FLG-ACCTFILTER-NOT-OK; compose and MOVE WS-FILE-ERROR-MESSAGE to WS-RETURN-MSG -- no WS-RETURN-MSG-OFF guard | 9150-GETCARD-BYACCT lines 800-807 |

## Calculations

| Calculation | Formula / Logic | Input Fields | Output Field | Source Location |
| --- | --- | --- | --- | --- |
| Date formatting | FUNCTION CURRENT-DATE returns 21-char string; extract WS-CURDATE-MONTH (positions 5-6), WS-CURDATE-DAY (7-8), WS-CURDATE-YEAR(3:2) into WS-CURDATE-MM, WS-CURDATE-DD, WS-CURDATE-YY; compose MM/DD/YY string | WS-CURDATE-DATA (FUNCTION CURRENT-DATE) | WS-CURDATE-MM-DD-YY moved to CURDATEO of CCRDSLAO | 1100-SCREEN-INIT lines 430-443 |
| Time formatting | From same FUNCTION CURRENT-DATE result; extract WS-CURTIME-HOURS, WS-CURTIME-MINUTE, WS-CURTIME-SECOND into WS-CURTIME-HH, WS-CURTIME-MM, WS-CURTIME-SS; compose HH:MM:SS display string | WS-CURDATE-DATA (FUNCTION CURRENT-DATE, called twice at lines 430 and 437) | WS-CURTIME-HH-MM-SS moved to CURTIMEO of CCRDSLAO | 1100-SCREEN-INIT lines 445-449 |
| Expiry date parsing | REDEFINE overlay: CARD-EXPIRAION-DATE-X (10 chars) is redefined with CARD-EXPIRY-YEAR (4), FILLER (1), CARD-EXPIRY-MONTH (2), FILLER (1), CARD-EXPIRY-DAY (2); copy raw string then extract sub-fields by position | CARD-EXPIRAION-DATE from CARD-RECORD (10-char string, format YYYY-MM-DD inferred) | EXPMONO (month), EXPYEARO (year) fields in CCRDSLAO | 1200-SETUP-SCREEN-VARS lines 477-482 |
| Commarea length arithmetic | WS-THIS-PROGCOMMAREA placed at offset LENGTH OF CARDDEMO-COMMAREA + 1 within WS-COMMAREA (2000 bytes total) | CARDDEMO-COMMAREA, WS-THIS-PROGCOMMAREA | WS-COMMAREA (2000 bytes) passed to EXEC CICS RETURN LENGTH(LENGTH OF WS-COMMAREA) | COMMON-RETURN lines 397-405 |

## Error Handling

| Condition | Action | Return Code | Source Location |
| --- | --- | --- | --- |
| CICS ABEND (any) | EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE) set at program entry; ABEND-ROUTINE: if ABEND-MSG = LOW-VALUES move 'UNEXPECTED ABEND OCCURRED.' to ABEND-MSG; MOVE LIT-THISPGM to ABEND-CULPRIT; EXEC CICS SEND FROM(ABEND-DATA) NOHANDLE; EXEC CICS HANDLE ABEND CANCEL; EXEC CICS ABEND ABCODE('9999') | ABEND code '9999' | 0000-MAIN line 250; ABEND-ROUTINE lines 857-877 |
| Unexpected EVALUATE branch (none of entry scenarios matched) | MOVE LIT-THISPGM to ABEND-CULPRIT ('COCRDSLC'); MOVE '0001' to ABEND-CODE; MOVE SPACES to ABEND-REASON; MOVE 'UNEXPECTED DATA SCENARIO' to WS-RETURN-MSG; PERFORM SEND-PLAIN-TEXT (debug: EXEC CICS SEND TEXT FROM WS-RETURN-MSG ERASE FREEKB; EXEC CICS RETURN) | '0001' in ABEND-CODE | 0000-MAIN lines 373-380; SEND-PLAIN-TEXT lines 838-848 |
| Account number blank/zero | SET INPUT-ERROR; SET WS-PROMPT-FOR-ACCT TO TRUE (if no prior message): WS-RETURN-MSG = 'Account number not provided'; MOVE ZEROES to CDEMO-ACCT-ID | INPUT-ERROR (WS-INPUT-FLAG = '1') | 2210-EDIT-ACCOUNT lines 651-658 |
| Account number not numeric | SET INPUT-ERROR; MOVE 'ACCOUNT FILTER,IF SUPPLIED MUST BE A 11 DIGIT NUMBER' to WS-RETURN-MSG (if no prior message); MOVE ZERO to CDEMO-ACCT-ID | INPUT-ERROR | 2210-EDIT-ACCOUNT lines 665-674 |
| Card number blank/zero | SET INPUT-ERROR; SET WS-PROMPT-FOR-CARD TO TRUE (if no prior message): WS-RETURN-MSG = 'Card number not provided'; MOVE ZEROES to CDEMO-CARD-NUM | INPUT-ERROR | 2220-EDIT-CARD lines 691-701 |
| Card number not numeric | SET INPUT-ERROR; MOVE 'CARD ID FILTER,IF SUPPLIED MUST BE A 16 DIGIT NUMBER' to WS-RETURN-MSG (if no prior message); MOVE ZERO to CDEMO-CARD-NUM | INPUT-ERROR | 2220-EDIT-CARD lines 706-714 |
| Both account and card blank | SET NO-SEARCH-CRITERIA-RECEIVED TO TRUE: WS-RETURN-MSG = 'No input received' (INPUT-ERROR already set from individual blank checks) | INPUT-ERROR | 2200-EDIT-MAP-INPUTS lines 637-640 |
| CARDDAT READ -- record not found | SET INPUT-ERROR, FLG-ACCTFILTER-NOT-OK, FLG-CARDFILTER-NOT-OK; if WS-RETURN-MSG-OFF: WS-RETURN-MSG = 'Did not find cards for this search condition' | INPUT-ERROR | 9100-GETCARD-BYACCTCARD lines 755-761 |
| CARDDAT READ -- unexpected CICS response | SET INPUT-ERROR; compose WS-FILE-ERROR-MESSAGE = 'File Error: READ on CARDDAT  returned RESP [nnn] ,RESP2 [nnn]'; move to WS-RETURN-MSG | INPUT-ERROR | 9100-GETCARD-BYACCTCARD lines 762-771 |
| CARDAIX READ -- record not found (9150 path) | SET INPUT-ERROR, FLG-ACCTFILTER-NOT-OK; SET DID-NOT-FIND-ACCT-IN-CARDXREF TO TRUE: WS-RETURN-MSG = 'Did not find this account in cards database' -- no WS-RETURN-MSG-OFF guard (unconditionally overwrites any prior error message) | INPUT-ERROR | 9150-GETCARD-BYACCT lines 796-799 |
| CARDAIX READ -- unexpected CICS response (9150 path) | SET INPUT-ERROR, FLG-ACCTFILTER-NOT-OK; compose and MOVE WS-FILE-ERROR-MESSAGE to WS-RETURN-MSG -- no WS-RETURN-MSG-OFF guard | INPUT-ERROR | 9150-GETCARD-BYACCT lines 800-807 |
| ABEND-MSG blank at abend entry | MOVE 'UNEXPECTED ABEND OCCURRED.' to ABEND-MSG (default fallback message) | n/a | ABEND-ROUTINE lines 859-861 |
| CICS RECEIVE MAP failure (MAPFAIL not trapped) | 2100-RECEIVE-MAP stores RESP/RESP2 but does not test them; if map receive fails, stale CCRDSLAI data is silently used; no error message or re-display is triggered | None (silent failure) | 2100-RECEIVE-MAP lines 597-603 |
| CICS SEND MAP failure (response not tested) | 1400-SEND-SCREEN captures RESP in WS-RESP-CD but does not test it after the EXEC CICS SEND MAP; any CICS error sending the map (e.g., TERMERR) is silently ignored; execution falls through to COMMON-RETURN and issues EXEC CICS RETURN normally | None (silent failure) | 1400-SEND-SCREEN line 575 |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. 0000-MAIN -- entry point; EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE); INITIALIZE CC-WORK-AREA, WS-MISC-STORAGE, WS-COMMAREA; MOVE LIT-THISTRANID to WS-TRANID; SET WS-RETURN-MSG-OFF
2. Commarea copy -- IF EIBCALEN=0 or first menu entry: INITIALIZE both commareas; ELSE split DFHCOMMAREA into CARDDEMO-COMMAREA and WS-THIS-PROGCOMMAREA by length offset
3. YYYY-STORE-PFKEY (via CSSTRPFY COPY at line 855) -- maps EIBAID to CCARD-AID-xxx flag; PF13-PF24 remapped to PF01-PF12
4. PFK-INVALID guard -- non-Enter/PF3 AID forced to CCARD-AID-ENTER
5. EVALUATE dispatch (EVALUATE TRUE):
   - CCARD-AID-PFK03: build return target; EXEC CICS XCTL to calling program or main menu
   - CDEMO-PGM-ENTER AND from COCRDLIC: skip validation; PERFORM 9000-READ-DATA then 1000-SEND-MAP; GO TO COMMON-RETURN
   - CDEMO-PGM-ENTER (other): PERFORM 1000-SEND-MAP (first-time display); GO TO COMMON-RETURN
   - CDEMO-PGM-REENTER: PERFORM 2000-PROCESS-INPUTS; if INPUT-ERROR PERFORM 1000-SEND-MAP; else PERFORM 9000-READ-DATA then 1000-SEND-MAP; GO TO COMMON-RETURN
   - WHEN OTHER: PERFORM SEND-PLAIN-TEXT (debug exit)
6. INPUT-ERROR slip-through guard (lines 386-391) -- catches any error not already dispatched
7. 2000-PROCESS-INPUTS -- PERFORM 2100-RECEIVE-MAP; PERFORM 2200-EDIT-MAP-INPUTS; set CCARD-NEXT-PROG/MAPSET/MAP and CCARD-ERROR-MSG
8. 2100-RECEIVE-MAP -- EXEC CICS RECEIVE MAP(CCRDSLA) MAPSET(COCRDSL) INTO(CCRDSLAI); RESP stored but NOT tested
9. 2200-EDIT-MAP-INPUTS -- reset flags; normalise '*'/spaces to LOW-VALUES; PERFORM 2210-EDIT-ACCOUNT; PERFORM 2220-EDIT-CARD; cross-field blank check
10. 2210-EDIT-ACCOUNT -- mandatory + numeric check on 11-digit account number; GO TO exit on failure
11. 2220-EDIT-CARD -- mandatory + numeric check on 16-digit card number; GO TO exit on failure
12. 9000-READ-DATA -- PERFORM 9100-GETCARD-BYACCTCARD only (9150-GETCARD-BYACCT is not called)
13. 9100-GETCARD-BYACCTCARD -- MOVE CC-CARD-NUM to WS-CARD-RID-CARDNUM; EXEC CICS READ CARDDAT by primary key; EVALUATE WS-RESP-CD (NORMAL / NOTFND / OTHER)
14. 1000-SEND-MAP -- PERFORM 1100-SCREEN-INIT, 1200-SETUP-SCREEN-VARS, 1300-SETUP-SCREEN-ATTRS, 1400-SEND-SCREEN in sequence
15. 1100-SCREEN-INIT -- MOVE LOW-VALUES to CCRDSLAO; populate titles, tranid, pgmname, date, time from FUNCTION CURRENT-DATE (called twice)
16. 1200-SETUP-SCREEN-VARS -- conditionally populate account/card/card-detail output fields; set info message; MOVE WS-RETURN-MSG to ERRMSGO and WS-INFO-MSG to INFOMSGO
17. 1300-SETUP-SCREEN-ATTRS -- set field protection, cursor position (-1), field colours based on validation flags and navigation context
18. 1400-SEND-SCREEN -- MOVE LIT-THISMAPSET/MAP to CCARD-NEXT-MAPSET/MAP; SET CDEMO-PGM-REENTER; EXEC CICS SEND MAP CCRDSLA MAPSET COCRDSL FROM CCRDSLAO CURSOR ERASE FREEKB; RESP captured but NOT tested
19. COMMON-RETURN -- MOVE WS-RETURN-MSG to CCARD-ERROR-MSG; assemble WS-COMMAREA from CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA; EXEC CICS RETURN TRANSID(LIT-THISTRANID = 'CCDL') COMMAREA(WS-COMMAREA) LENGTH(LENGTH OF WS-COMMAREA)
20. ABEND-ROUTINE -- triggered by CICS HANDLE ABEND; default message if ABEND-MSG blank; set ABEND-CULPRIT; EXEC CICS SEND ABEND-DATA NOHANDLE; EXEC CICS HANDLE ABEND CANCEL; EXEC CICS ABEND ABCODE('9999')

### Debug / Utility Paragraphs (not called in normal flow)

- SEND-LONG-TEXT (lines 820-830): EXEC CICS SEND TEXT FROM(WS-LONG-MSG) LENGTH(500) ERASE FREEKB; EXEC CICS RETURN. This paragraph is defined but has no PERFORM reference anywhere in the PROCEDURE DIVISION -- it is dead code in the current program.
- SEND-PLAIN-TEXT (lines 838-848): EXEC CICS SEND TEXT FROM(WS-RETURN-MSG) ERASE FREEKB; EXEC CICS RETURN. Called only from the WHEN OTHER branch of the main EVALUATE (line 379). Intended for debugging.

### Data Division Notes

- WS-THIS-PROGCOMMAREA contains CA-FROM-PROGRAM (PIC X(08)) and CA-FROM-TRANID (PIC X(04)), but these sub-fields are never individually referenced in the PROCEDURE DIVISION -- the entire WS-THIS-PROGCOMMAREA group is moved en-bloc.
- LIT-CCLISTMAP is defined as VALUE 'CCRDSLA' (line 178) -- the same value as LIT-THISMAP. This appears to be a copy-paste error in the DATA DIVISION (should refer to the card list map, not the detail map). However, LIT-CCLISTMAP is never referenced in the PROCEDURE DIVISION, so it has no runtime impact.
- LIT-CCLISTTRANID (VALUE 'CCLI', line 173), LIT-MENUMAPSET (VALUE 'COMEN01', line 183), and LIT-MENUMAP (VALUE 'COMEN1A', line 185) are defined in WS-LITERALS but are never referenced in the PROCEDURE DIVISION -- dead-code literals with no runtime effect.
- 88-level condition WS-EXIT-MESSAGE is defined as VALUE 'PF03 pressed.Exiting              ' but is never SET in the PROCEDURE DIVISION -- the PF3 branch issues XCTL directly without setting this message.
- Five additional 88-level conditions on WS-RETURN-MSG are defined but never SET or tested anywhere in the PROCEDURE DIVISION (dead code): SEARCHED-ACCT-ZEROES (VALUE 'Account number must be a non zero 11 digit number'), SEARCHED-ACCT-NOT-NUMERIC (same VALUE as SEARCHED-ACCT-ZEROES -- duplicate literal), SEARCHED-CARD-NOT-NUMERIC (VALUE 'Card number if supplied must be a 16 digit number'), XREF-READ-ERROR (VALUE 'Error reading Card Data File'), CODING-TO-BE-DONE (VALUE 'Looks Good.... so far'). The actual error messages used at runtime are MOVE literals in the procedure code, not these 88-level condition names.
- Edit paragraphs 2210-EDIT-ACCOUNT (line 648) and 2220-EDIT-CARD (line 688) both unconditionally SET FLG-ACCTFILTER-NOT-OK / FLG-CARDFILTER-NOT-OK to TRUE as their first action before any condition test, then only SET ISVALID if all checks pass -- a defensive fail-safe pattern ensuring a field is never left in an ambiguous state on an unexpected code path.
