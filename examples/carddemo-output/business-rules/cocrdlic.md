---
type: business-rules
program: COCRDLIC
program_type: online
status: draft
confidence: high
last_pass: 5
calls: []
called_by: []
uses_copybooks:
- COCOM01Y
- COCRDLI
- COTTL01Y
- CSDAT01Y
- CSMSG01Y
- CSSTRPFY
- CSUSR01Y
- CVACT02Y
- CVCRD01Y
reads:
- CARDDAT
writes: []
db_tables: []
transactions:
- CCLI
mq_queues: []
---

# COCRDLIC -- Business Rules

## Program Purpose

COCRDLIC is a CICS online program that displays a paginated list of credit cards
stored in the CARDDAT VSAM file. It supports two display modes:

- **All cards** -- shown when no account/card filter is supplied and the user is
  an admin (or the context is a fresh start).
- **Filtered cards** -- shown when an account ID and/or card number filter is
  supplied in the search fields, restricting the list to matching records.

The screen holds up to 7 card rows. The user can page forward (PF8) and backward
(PF7), select a row for **view** (action code `S`) to transfer to the card detail
program COCRDSLC (transaction CCDL), or select a row for **update** (action code
`U`) to transfer to the card update program COCRDUPC (transaction CCUP). PF3
returns the user to the main menu (COMEN01C, transaction CM00).

The program uses a COMMAREA split: the first portion is the shared
`CARDDEMO-COMMAREA`, and the second portion is a program-private
`WS-THIS-PROGCOMMAREA` that holds pagination state (first/last card key seen,
current screen number, last-page indicator, next-page indicator, and
return flag).

---

## Input / Output

| Direction | Resource       | Type | Description                                               |
| --------- | -------------- | ---- | --------------------------------------------------------- |
| IN        | CCRDLIAI       | CICS | BMS map input (account filter, card filter, 7 action fields) |
| OUT       | CCRDLIAO       | CICS | BMS map output (7 card rows, messages, cursor position)   |
| IN/OUT    | CARDDEMO-COMMAREA | CICS | Shared application commarea (user type, program routing, account/card IDs) |
| IN/OUT    | WS-THIS-PROGCOMMAREA | CICS | Private commarea: pagination keys, screen number, page flags |
| IN        | CARDDAT        | CICS VSAM | Card master file, browsed forward (STARTBR/READNEXT/ENDBR) and backward (STARTBR/READPREV/ENDBR) |
| OUT       | COCRDSLC (XCTL) | CICS | Transfer to card detail view                             |
| OUT       | COCRDUPC (XCTL) | CICS | Transfer to card update program                          |
| OUT       | COMEN01C (XCTL) | CICS | Transfer to main menu on PF3                             |

---

## Business Rules

### Initialisation and Context Detection

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 1  | Fresh-start initialisation | `EIBCALEN = 0` (no commarea) | Initialise `CARDDEMO-COMMAREA` and `WS-THIS-PROGCOMMAREA`; set `CDEMO-FROM-TRANID = 'CCLI'`, `CDEMO-FROM-PROGRAM = 'COCRDLIC'`, user type = user, program state = ENTER, last map = 'CCRDLIA', last mapset = 'COCRDLI'; set CA-FIRST-PAGE and CA-LAST-PAGE-NOT-SHOWN | 0000-MAIN (lines 315-325) |
| 2  | Re-entry from another program | `EIBCALEN > 0` | Restore `CARDDEMO-COMMAREA` from `DFHCOMMAREA(1:len)` and `WS-THIS-PROGCOMMAREA` from the second portion of `DFHCOMMAREA` | 0000-MAIN (lines 326-332) |
| 3  | Reset state on entry from menu | `CDEMO-PGM-ENTER` is true AND `CDEMO-FROM-PROGRAM <> 'COCRDLIC'` | Re-initialise `WS-THIS-PROGCOMMAREA`; reset CA-FIRST-PAGE and CA-LAST-PAGE-NOT-SHOWN | 0000-MAIN (lines 336-343) |
| 50 | Screen input not received on fresh entry | `EIBCALEN = 0` OR `CDEMO-FROM-PROGRAM <> 'COCRDLIC'` | 2000-RECEIVE-MAP is NOT PERFORMed; no CICS RECEIVE MAP is issued; the program proceeds directly to pagination dispatch using stored/initialised pagination state | 0000-MAIN (lines 357-362) |

### PF Key Routing

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 4  | Valid keys accepted | `EIBAID` = ENTER, PF3, PF7, or PF8 | Set PFK-VALID flag | 0000-MAIN (lines 370-376); CSSTRPFY.cpy maps PF13-PF20 to PF1-PF8 equivalents |
| 5  | Invalid key defaults to Enter | `PFK-INVALID` is true | Force `CCARD-AID-ENTER` to true; continue processing as if Enter was pressed | 0000-MAIN (lines 378-380) |
| 6  | PF3 exits to main menu | `CCARD-AID-PFK03` AND `CDEMO-FROM-PROGRAM = 'COCRDLIC'` | Set exit message 'PF03 PRESSED.EXITING'; XCTL to `COMEN01C` (mapset `COMEN01`, map `COMEN1A`) passing `CARDDEMO-COMMAREA` | 0000-MAIN (lines 384-405) |
| 7  | PF8 not pressed resets last-page flag | NOT `CCARD-AID-PFK08` | Set CA-LAST-PAGE-NOT-SHOWN to true | 0000-MAIN (lines 410-414) |

### Pagination Dispatch (EVALUATE in 0000-MAIN)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 8  | Input error redisplay | `INPUT-ERROR` | Move error message to screen; if account filter and card filter are not in error state, perform 9000-READ-FORWARD to reload data; perform 1000-SEND-MAP; GO TO COMMON-RETURN | 0000-MAIN (lines 419-438) |
| 9  | PF7 on first page (no-op) | `CCARD-AID-PFK07` AND `CA-FIRST-PAGE` | Set start key to WS-CA-FIRST-CARD-NUM; perform 9000-READ-FORWARD; perform 1000-SEND-MAP; GO TO COMMON-RETURN. Note: the EVALUATE contains two consecutive WHEN clauses for this condition (lines 439-445) -- the first is empty (falls through) and the second carries the action statements; this is a code anomaly but functionally harmless | 0000-MAIN (lines 439-454) |
| 10 | PF3 or re-entry from another program | `CCARD-AID-PFK03` OR (`CDEMO-PGM-REENTER` AND `CDEMO-FROM-PROGRAM <> 'COCRDLIC'`) | Re-initialise commarea context; reset to first page; set start key to WS-CA-FIRST-CARD-NUM; perform 9000-READ-FORWARD; perform 1000-SEND-MAP; GO TO COMMON-RETURN | 0000-MAIN (lines 458-482) |
| 11 | PF8 page-down | `CCARD-AID-PFK08` AND `CA-NEXT-PAGE-EXISTS` | Set start key to WS-CA-LAST-CARD-NUM; increment WS-CA-SCREEN-NUM by 1; perform 9000-READ-FORWARD; perform 1000-SEND-MAP; GO TO COMMON-RETURN | 0000-MAIN (lines 486-497) |
| 12 | PF7 page-up (not first page) | `CCARD-AID-PFK07` AND NOT `CA-FIRST-PAGE` | Set start key to WS-CA-FIRST-CARD-NUM; subtract 1 from WS-CA-SCREEN-NUM; perform 9100-READ-BACKWARDS; perform 1000-SEND-MAP; GO TO COMMON-RETURN | 0000-MAIN (lines 501-513) |
| 13 | View card detail | `CCARD-AID-ENTER` AND `VIEW-REQUESTED-ON(I-SELECTED)` (action = 'S') AND `CDEMO-FROM-PROGRAM = 'COCRDLIC'` | Copy selected row's account ID and card number to `CDEMO-ACCT-ID` / `CDEMO-CARD-NUM`; XCTL to COCRDSLC (mapset COCRDSL, map CCRDSLA) | 0000-MAIN (lines 517-541) |
| 14 | Update card | `CCARD-AID-ENTER` AND `UPDATE-REQUESTED-ON(I-SELECTED)` (action = 'U') AND `CDEMO-FROM-PROGRAM = 'COCRDLIC'` | Copy selected row's account ID and card number to `CDEMO-ACCT-ID` / `CDEMO-CARD-NUM`; XCTL to COCRDUPC (mapset COCRDUP, map CCRDUPA) | 0000-MAIN (lines 545-569) |
| 15 | Default / other key combinations | WHEN OTHER | Set start key to WS-CA-FIRST-CARD-NUM; perform 9000-READ-FORWARD; perform 1000-SEND-MAP; GO TO COMMON-RETURN | 0000-MAIN (lines 572-582) |
| 51 | INPUT-ERROR fallback after EVALUATE (unreachable in normal flow) | `INPUT-ERROR` is true after END-EVALUATE | Set routing fields (`CDEMO-FROM-PROGRAM`, `CDEMO-LAST-MAPSET`, etc.) and GO TO COMMON-RETURN without calling 1000-SEND-MAP; the screen is NOT refreshed in this path -- the user sees the current screen contents with no update | 0000-MAIN (lines 586-598) |

### Input Validation -- Account Filter (2210-EDIT-ACCOUNT)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 16 | Account filter is optional | `CC-ACCT-ID = LOW-VALUES` OR `SPACES` OR numeric value zero | Set FLG-ACCTFILTER-BLANK; move 0 to CDEMO-ACCT-ID; bypass further account edits | 2210-EDIT-ACCOUNT (lines 1007-1013) |
| 17 | Account filter must be numeric | `CC-ACCT-ID IS NOT NUMERIC` | Set INPUT-ERROR, FLG-ACCTFILTER-NOT-OK, FLG-PROTECT-SELECT-ROWS-YES; move error message 'ACCOUNT FILTER,IF SUPPLIED MUST BE A 11 DIGIT NUMBER' to WS-ERROR-MSG; set CDEMO-ACCT-ID = 0 | 2210-EDIT-ACCOUNT (lines 1017-1025) |
| 18 | Account filter accepted | `CC-ACCT-ID IS NUMERIC` (and not blank/zero) | Move CC-ACCT-ID to CDEMO-ACCT-ID; set FLG-ACCTFILTER-ISVALID | 2210-EDIT-ACCOUNT (lines 1026-1029) |

### Input Validation -- Card Filter (2220-EDIT-CARD)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 19 | Card filter is optional | `CC-CARD-NUM = LOW-VALUES` OR `SPACES` OR numeric value zero | Set FLG-CARDFILTER-BLANK; move 0 to CDEMO-CARD-NUM; bypass further card filter edits | 2220-EDIT-CARD (lines 1042-1047) |
| 20 | Card filter must be numeric | `CC-CARD-NUM IS NOT NUMERIC` | Set INPUT-ERROR, FLG-CARDFILTER-NOT-OK, FLG-PROTECT-SELECT-ROWS-YES; if WS-ERROR-MSG is currently blank, move 'CARD ID FILTER,IF SUPPLIED MUST BE A 16 DIGIT NUMBER' to WS-ERROR-MSG; set CDEMO-CARD-NUM = 0 | 2220-EDIT-CARD (lines 1052-1062) |
| 21 | Card filter accepted | `CC-CARD-NUM IS NUMERIC` (and not blank/zero) | Move CC-CARD-NUM-N (numeric redefine) to CDEMO-CARD-NUM; set FLG-CARDFILTER-ISVALID | 2220-EDIT-CARD (lines 1063-1065) |

### Input Validation -- Row Selection Array (2250-EDIT-ARRAY)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 22 | Skip row validation on prior error | `INPUT-ERROR` is true | GO TO 2250-EDIT-ARRAY-EXIT immediately | 2250-EDIT-ARRAY (lines 1075-1077) |
| 23 | Only one row may be selected | Count of 'S' + 'U' entries in WS-EDIT-SELECT-FLAGS > 1 | Set INPUT-ERROR; set WS-MORE-THAN-1-ACTION (message: 'PLEASE SELECT ONLY ONE RECORD TO VIEW OR UPDATE'); mark every selected row's error flag = '1' | 2250-EDIT-ARRAY (lines 1079-1095) |
| 24 | Row action code must be 'S', 'U', or blank | For each row I (1 to 7): if WS-EDIT-SELECT(I) is not 'S', 'U', SPACE, or LOW-VALUES | Set INPUT-ERROR; set WS-ROW-CRDSELECT-ERROR(I) = '1'; if WS-ERROR-MSG is blank, set message 'INVALID ACTION CODE' | 2250-EDIT-ARRAY (lines 1099-1115) |
| 25 | Record selected row index | First row (1-7) where action = 'S' or 'U' | Move row index I to I-SELECTED (used later by XCTL routing) | 2250-EDIT-ARRAY (lines 1097-1102) |

### Row Filter Logic (9500-FILTER-RECORDS)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 26 | Account filter applied to each record | `FLG-ACCTFILTER-ISVALID` AND `CARD-ACCT-ID <> CC-ACCT-ID` | Set WS-EXCLUDE-THIS-RECORD; skip record | 9500-FILTER-RECORDS (lines 1385-1391) |
| 27 | Card number filter applied to each record | `FLG-CARDFILTER-ISVALID` AND `CARD-NUM <> CC-CARD-NUM-N` | Set WS-EXCLUDE-THIS-RECORD; skip record | 9500-FILTER-RECORDS (lines 1396-1402) |
| 28 | Record passes filter | Neither account nor card filter excludes the record | Set WS-DONOT-EXCLUDE-THIS-RECORD; include record in screen array | 9500-FILTER-RECORDS (line 1383) |

### Pagination State Management

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 29 | Maximum 7 rows per screen | `WS-SCRN-COUNTER = WS-MAX-SCREEN-LINES` (constant = 7) | Set READ-LOOP-EXIT; record last card key; do one extra READNEXT to check if more pages exist | 9000-READ-FORWARD (lines 1191-1231) |
| 30 | Next page exists flag | Extra READNEXT after full page returns DFHRESP(NORMAL) or DFHRESP(DUPREC) | Set CA-NEXT-PAGE-EXISTS; save that next record's card number as WS-CA-LAST-CARD-NUM | 9000-READ-FORWARD (lines 1208-1214) |
| 31 | End of file -- no next page | Extra READNEXT returns DFHRESP(ENDFILE) | Set CA-NEXT-PAGE-NOT-EXISTS; set message 'NO MORE RECORDS TO SHOW' | 9000-READ-FORWARD (lines 1215-1221) |
| 32 | No records found on first page | DFHRESP(ENDFILE) on first page AND WS-CA-SCREEN-NUM = 1 AND WS-SCRN-COUNTER = 0 | Set WS-NO-RECORDS-FOUND (message: 'NO RECORDS FOUND FOR THIS SEARCH CONDITION.') | 9000-READ-FORWARD (lines 1241-1245) |
| 33 | Screen number incremented on first forward read | First record received (WS-SCRN-COUNTER = 1) AND WS-CA-SCREEN-NUM = 0 | Increment WS-CA-SCREEN-NUM by 1 | 9000-READ-FORWARD (lines 1173-1181) |
| 34 | First card key saved on forward read | First record received (WS-SCRN-COUNTER = 1) | Save CARD-ACCT-ID to WS-CA-FIRST-CARD-ACCT-ID and CARD-NUM to WS-CA-FIRST-CARD-NUM | 9000-READ-FORWARD (lines 1173-1176) |
| 35 | Backward read initialises counter | Always at start of 9100-READ-BACKWARDS | Set WS-SCRN-COUNTER = WS-MAX-SCREEN-LINES + 1 (= 8); records fill positions 8 down to 1 via SUBTRACT | 9100-READ-BACKWARDS (lines 1284-1285) |
| 36 | Backward read completes when counter = 0 | WS-SCRN-COUNTER reaches 0 after SUBTRACT 1 | Set READ-LOOP-EXIT; save first card key of new page to WS-CA-FIRST-CARD-NUM | 9100-READ-BACKWARDS (lines 1347-1353) |
| 37 | Screen number decremented on page-up | PF7 pressed and not on first page | Subtract 1 from WS-CA-SCREEN-NUM before calling 9100-READ-BACKWARDS | 0000-MAIN (line 508) |
| 38 | Screen number incremented on page-down | PF8 pressed | Add 1 to WS-CA-SCREEN-NUM before calling 9000-READ-FORWARD | 0000-MAIN (line 492) |

### Screen Message Rules (1400-SETUP-MESSAGE)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 52 | Filter-error suppresses message override | `FLG-ACCTFILTER-NOT-OK` OR `FLG-CARDFILTER-NOT-OK` (first WHEN in the EVALUATE) | CONTINUE -- the message area is not touched; the validation error message already written to WS-ERROR-MSG during 2210/2220-EDIT-* remains in place and is not overridden by any page-navigation or informational message | 1400-SETUP-MESSAGE (lines 897-900) |
| 39 | No previous page message | `CCARD-AID-PFK07` AND `CA-FIRST-PAGE` | Move 'NO PREVIOUS PAGES TO DISPLAY' to WS-ERROR-MSG | 1400-SETUP-MESSAGE (lines 901-904) |
| 40 | No more pages message (already seen) | `CCARD-AID-PFK08` AND `CA-NEXT-PAGE-NOT-EXISTS` AND `CA-LAST-PAGE-SHOWN` | Move 'NO MORE PAGES TO DISPLAY' to WS-ERROR-MSG | 1400-SETUP-MESSAGE (lines 905-909) |
| 41 | Last page first view -- inform user | `CCARD-AID-PFK08` AND `CA-NEXT-PAGE-NOT-EXISTS` | Set WS-INFORM-REC-ACTIONS (message: 'TYPE S FOR DETAIL, U TO UPDATE ANY RECORD'); if CA-LAST-PAGE-NOT-SHOWN AND CA-NEXT-PAGE-NOT-EXISTS then set CA-LAST-PAGE-SHOWN | 1400-SETUP-MESSAGE (lines 910-916) |
| 42 | More pages exist -- inform user | `WS-NO-INFO-MESSAGE` OR `CA-NEXT-PAGE-EXISTS` | Set WS-INFORM-REC-ACTIONS (message: 'TYPE S FOR DETAIL, U TO UPDATE ANY RECORD') | 1400-SETUP-MESSAGE (lines 917-919) |
| 53 | WHEN OTHER clears info message | No prior WHEN matched | Set WS-NO-INFO-MESSAGE to true; this ensures the INFOMSG field stays blank when no specific message condition applies | 1400-SETUP-MESSAGE (lines 920-921) |
| 54 | Info message suppressed when no-records-found | NOT WS-NO-INFO-MESSAGE AND NOT WS-NO-RECORDS-FOUND | Move WS-INFO-MSG to INFOMSGO and apply DFHNEUTR colour; if either flag is active the info message is suppressed (both conditions must be absent for the message to display) | 1400-SETUP-MESSAGE (lines 926-930) |

### Screen Attribute Rules (1300-SETUP-SCREEN-ATTRS, 1250-SETUP-ARRAY-ATTRIBS)

| #  | Rule | Condition | Action | Source Location |
| -- | ---- | --------- | ------ | --------------- |
| 43 | Account filter redisplayed after validation | `FLG-ACCTFILTER-ISVALID` or `FLG-ACCTFILTER-NOT-OK` | Move CC-ACCT-ID to ACCTSIDO; set field attribute to FSET (unprotected, modified) | 1300-SETUP-SCREEN-ATTRS (lines 844-848) |
| 55 | Account filter display from commarea when CDEMO-ACCT-ID = 0 | `CDEMO-ACCT-ID = 0` (WHEN in the account-display EVALUATE, filter not valid or invalid) | Move LOW-VALUES to ACCTSIDO -- field appears blank on screen | 1300-SETUP-SCREEN-ATTRS (lines 849-850) |
| 56 | Account filter display from commarea -- other re-entry | WHEN OTHER (filter flags not set, CDEMO-ACCT-ID <> 0) | Move CDEMO-ACCT-ID to ACCTSIDO and set attribute to FSET; the commarea account ID is used as the displayed value rather than CC-ACCT-ID from the last screen read | 1300-SETUP-SCREEN-ATTRS (lines 851-853) |
| 57 | Filter fields not redisplayed on fresh entry or menu entry | `EIBCALEN = 0` OR (`CDEMO-PGM-ENTER` AND `CDEMO-FROM-PROGRAM = LIT-MENUPGM`) | The entire filter-redisplay EVALUATE (lines 844-867) is skipped; both ACCTSIDO and CARDSIDO remain blank (LOW-VALUES from 1100-SCREEN-INIT) | 1300-SETUP-SCREEN-ATTRS (lines 839-842) |
| 44 | Account filter in error -- red highlight | `FLG-ACCTFILTER-NOT-OK` | Move DFHRED to ACCTSIDC; move -1 to ACCTSIDL (cursor positioned here) | 1300-SETUP-SCREEN-ATTRS (lines 872-875) |
| 45 | Card filter in error -- red highlight | `FLG-CARDFILTER-NOT-OK` | Move DFHRED to CARDSIDC; move -1 to CARDSIDL (cursor positioned here) | 1300-SETUP-SCREEN-ATTRS (lines 877-880) |
| 46 | Default cursor position | `INPUT-OK` | Move -1 to ACCTSIDL (cursor on account filter field) | 1300-SETUP-SCREEN-ATTRS (lines 884-886) |
| 47 | Empty row or protect-rows flag -- selection field protected | Row data = LOW-VALUES OR `FLG-PROTECT-SELECT-ROWS-YES` | Move DFHBMPRF (row 1) or DFHBMPRO (rows 2-7) to CRDSELnA -- field is protected | 1250-SETUP-ARRAY-ATTRIBS (lines 751-831) |
| 48 | Row selection error -- red field | `WS-ROW-CRDSELECT-ERROR(n) = '1'` | Move DFHRED to CRDSELnC; move -1 to CRDSELnL; if field is blank/LOW-VALUES also display '*' | 1250-SETUP-ARRAY-ATTRIBS (lines 755-760, 768-771, etc.) |
| 49 | Populated row -- selection field enabled | Row data not LOW-VALUES AND protect flag not set | Move DFHBMFSE (unprotected, stopper) to CRDSELnA | 1250-SETUP-ARRAY-ATTRIBS (lines 761, 772, 784, 796, 807, 819, 830) |

---

## Calculations

| Calculation | Formula / Logic | Input Fields | Output Field | Source Location |
| ----------- | --------------- | ------------ | ------------ | --------------- |
| Screen counter increment (forward) | `ADD 1 TO WS-SCRN-COUNTER` on each included record | WS-SCRN-COUNTER | WS-SCRN-COUNTER | 9000-READ-FORWARD (line 1163) |
| Screen number increment (page down) | `ADD +1 TO WS-CA-SCREEN-NUM` | WS-CA-SCREEN-NUM | WS-CA-SCREEN-NUM | 0000-MAIN (line 492) |
| Screen number decrement (page up) | `SUBTRACT 1 FROM WS-CA-SCREEN-NUM` | WS-CA-SCREEN-NUM | WS-CA-SCREEN-NUM | 0000-MAIN (line 508) |
| Backward browse initial counter | `COMPUTE WS-SCRN-COUNTER = WS-MAX-SCREEN-LINES + 1` (= 8) | WS-MAX-SCREEN-LINES (constant 7) | WS-SCRN-COUNTER | 9100-READ-BACKWARDS (lines 1284-1286) |
| Backward browse counter decrement | `SUBTRACT 1 FROM WS-SCRN-COUNTER` per included record | WS-SCRN-COUNTER | WS-SCRN-COUNTER | 9100-READ-BACKWARDS (lines 1307, 1346) |
| Commarea second-part offset | `LENGTH OF CARDDEMO-COMMAREA + 1` for the start position of WS-THIS-PROGCOMMAREA in WS-COMMAREA | EIBCALEN, LENGTH OF CARDDEMO-COMMAREA | WS-THIS-PROGCOMMAREA | 0000-MAIN (lines 329-331), COMMON-RETURN (lines 610-612) |

---

## Error Handling

| Condition | Action | Return Code | Source Location |
| --------- | ------- | ----------- | --------------- |
| RECEIVE MAP response not checked | RESP collected at line 966 but no IF or EVALUATE follows; a MAPFAIL or other receive error silently continues with whatever residual data is in CCRDLIAI (likely LOW-VALUES) -- all filters appear blank and all select fields blank, so the program will proceed as if no input was given rather than aborting | No check performed | 2100-RECEIVE-SCREEN (lines 963-967) |
| STARTBR response not evaluated (forward browse) | RESP and RESP2 are collected but no EVALUATE follows -- STARTBR failures silently fall through into the READNEXT loop, which will then return its own error | No check performed | 9000-READ-FORWARD (lines 1129-1136) |
| STARTBR response not evaluated (backward browse) | Same as above -- RESP and RESP2 collected but not tested before proceeding to READPREV | No check performed | 9100-READ-BACKWARDS (lines 1273-1280) |
| READNEXT returns DFHRESP(ENDFILE) during forward browse | Set CA-NEXT-PAGE-NOT-EXISTS; if WS-ERROR-MSG is blank set 'NO MORE RECORDS TO SHOW'; if first page and no rows set WS-NO-RECORDS-FOUND | DFHRESP(ENDFILE) | 9000-READ-FORWARD (lines 1233-1245) |
| READNEXT returns other error during forward browse (main loop) | Set READ-LOOP-EXIT; populate WS-FILE-ERROR-MESSAGE with operation 'READ', file 'CARDDAT ', RESP and RESP2 codes | DFHRESP(OTHER) | 9000-READ-FORWARD (lines 1246-1254) |
| Extra READNEXT after full page returns other error | Same file error message; set READ-LOOP-EXIT | DFHRESP(OTHER) | 9000-READ-FORWARD (lines 1222-1230) |
| READPREV returns other error during first READPREV (position step) | Set READ-LOOP-EXIT; populate WS-FILE-ERROR-MESSAGE; GO TO 9100-READ-BACKWARDS-EXIT (ENDBR still fired because it lives in EXIT paragraph) | DFHRESP(OTHER) | 9100-READ-BACKWARDS (lines 1308-1317) |
| READPREV returns other error during backward browse loop | Set READ-LOOP-EXIT; populate WS-FILE-ERROR-MESSAGE | DFHRESP(OTHER) | 9100-READ-BACKWARDS (lines 1361-1369) |
| Account filter not numeric | Set INPUT-ERROR; display 'ACCOUNT FILTER,IF SUPPLIED MUST BE A 11 DIGIT NUMBER' | INPUT-ERROR flag | 2210-EDIT-ACCOUNT (lines 1017-1025) |
| Card filter not numeric | Set INPUT-ERROR; display 'CARD ID FILTER,IF SUPPLIED MUST BE A 16 DIGIT NUMBER' (only if no prior error message) | INPUT-ERROR flag | 2220-EDIT-CARD (lines 1052-1062) |
| More than one row action selected | Set INPUT-ERROR; display 'PLEASE SELECT ONLY ONE RECORD TO VIEW OR UPDATE'; highlight all selected rows red | INPUT-ERROR flag | 2250-EDIT-ARRAY (lines 1084-1095) |
| Invalid row action code (not S, U, or blank) | Set INPUT-ERROR; set WS-ROW-CRDSELECT-ERROR(I) = '1'; if no prior error message set 'INVALID ACTION CODE' | INPUT-ERROR flag | 2250-EDIT-ARRAY (lines 1108-1113) |
| PF7 pressed on first page | Not an error flag but informational message | Message: 'NO PREVIOUS PAGES TO DISPLAY' | 1400-SETUP-MESSAGE (lines 901-904) |
| PF8 pressed when no next page and last page already seen | Informational -- no new data to show | Message: 'NO MORE PAGES TO DISPLAY' | 1400-SETUP-MESSAGE (lines 905-909) |
| INPUT-ERROR set but none of the EVALUATE WHEN branches matched (post-EVALUATE fallback) | Routing fields are set and GO TO COMMON-RETURN is executed WITHOUT calling 1000-SEND-MAP; the user sees no screen refresh -- this path is only reachable if a new INPUT-ERROR source is added without a corresponding WHEN clause in the EVALUATE | No screen sent | 0000-MAIN (lines 586-598) |

---

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. **0000-MAIN** -- entry point; initialises storage, restores commarea, evaluates AID key, dispatches to appropriate action
2. **YYYY-STORE-PFKEY** (via COPY CSSTRPFY) -- maps EIBAID to CCARD-AID-xxx flags; PF13-PF24 remapped to PF1-PF12 equivalents
3. **2000-RECEIVE-MAP** -- called only when `EIBCALEN > 0 AND CDEMO-FROM-PROGRAM = LIT-THISPGM`; skipped entirely on fresh entry or when returning from a subordinate program; reads screen and edits inputs
   - 3a. **2100-RECEIVE-SCREEN** -- EXEC CICS RECEIVE MAP CCRDLIA; extracts account filter (CC-ACCT-ID), card filter (CC-CARD-NUM), and 7 row action codes (WS-EDIT-SELECT 1-7); RESP is collected but not evaluated -- MAPFAIL silently continues
   - 3b. **2200-EDIT-INPUTS** -- dispatcher for three validators
       - **2210-EDIT-ACCOUNT** -- validates/classifies account filter field
       - **2220-EDIT-CARD** -- validates/classifies card filter field
       - **2250-EDIT-ARRAY** -- validates row selection count and action code values
4. **9000-READ-FORWARD** -- browse CARDDAT forward from start key; fills WS-SCREEN-ROWS array (up to 7 rows); applies 9500-FILTER-RECORDS to each record; sets pagination flags; ENDBR issued inline at end of paragraph (line 1258)
   - 4a. **9500-FILTER-RECORDS** -- applies account and card number filter to each READNEXT result
5. **9100-READ-BACKWARDS** -- browse CARDDAT backward from first key of current page; fills WS-SCREEN-ROWS in reverse order (positions 8 down to 1, then shifted); applies 9500-FILTER-RECORDS; ENDBR is placed in the EXIT paragraph (line 1375) so it fires for both normal completion and GO TO early-exit on error
6. **1000-SEND-MAP** -- prepares and sends the screen
   - 6a. **1100-SCREEN-INIT** -- clears output area; moves current date/time, titles, transaction/program names, and page number to map
   - 6b. **1200-SCREEN-ARRAY-INIT** -- copies WS-SCREEN-ROWS data (account number, card number, card status, selection character) to each of the 7 map rows
   - 6c. **1250-SETUP-ARRAY-ATTRIBS** -- sets BMS attributes (protected/unprotected, red on error, cursor) for each row's selection field
   - 6d. **1300-SETUP-SCREEN-ATTRS** -- redisplays filter fields; sets red/cursor on filter field errors; positions cursor on account ID if no errors; skipped on fresh/menu entry
   - 6e. **1400-SETUP-MESSAGE** -- sets informational and error messages (page navigation, no records, action hint); filter errors suppress all other message categories
   - 6f. **1500-SEND-SCREEN** -- EXEC CICS SEND MAP CCRDLIA with ERASE and FREEKB
7. **COMMON-RETURN** -- serialises both commarea portions back into WS-COMMAREA; EXEC CICS RETURN TRANSID('CCLI') COMMAREA(WS-COMMAREA)
8. **EXEC CICS XCTL PROGRAM(COMEN01C)** -- on PF3, transfer control to main menu
9. **EXEC CICS XCTL PROGRAM(COCRDSLC)** -- on Enter + 'S' row action, transfer to card detail view
10. **EXEC CICS XCTL PROGRAM(COCRDUPC)** -- on Enter + 'U' row action, transfer to card update program
11. **SEND-PLAIN-TEXT** -- diagnostic paragraph; sends WS-ERROR-MSG as plain text via EXEC CICS SEND TEXT with ERASE/FREEKB then issues unconditional EXEC CICS RETURN; not called from normal flow (no PERFORM references found in the source) -- present for debug use only
12. **SEND-LONG-TEXT** -- diagnostic paragraph; sends WS-LONG-MSG as plain text via EXEC CICS SEND TEXT then issues unconditional EXEC CICS RETURN; not called from normal flow -- comment in source states 'This is primarily for debugging and should not be used in regular course'

### Inbound XCTL paths (not captured in called_by frontmatter)

COCRDLIC has no CALL statement callers. It is reached via CICS XCTL from:
- **COMEN01C** -- menu option 3 in COMEN02Y dispatch table ('Credit Card List'); XCTL issued via `CDEMO-MENU-OPT-PGMNAME(WS-OPTION)` lookup
- **COCRDSLC** -- when user presses PF3 from card detail view and `CDEMO-FROM-PROGRAM = 'COCRDLIC'`; XCTL issues to `CDEMO-TO-PROGRAM` which is set to the original calling program
- **COCRDUPC** -- when user presses PF3 from card update view and `CDEMO-FROM-PROGRAM = 'COCRDLIC'`; same `CDEMO-TO-PROGRAM` pattern
- **COACTVWC** and **COACTUPC** -- define LIT-CCLISTPGM = 'COCRDLIC' and LIT-CCLISTTRANID = 'CCLI' in their DATA DIVISION but these are DATA DIVISION constants only; no corresponding XCTL to COCRDLIC was found in their PROCEDURE DIVISION
