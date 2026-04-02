---
type: business-rules
program: COACTVWC
program_type: online
status: draft
confidence: high
last_pass: 5
calls: []
called_by: []
uses_copybooks:
- COACTVW
- COCOM01Y
- COTTL01Y
- CSDAT01Y
- CSMSG01Y
- CSMSG02Y
- CSSTRPFY
- CSUSR01Y
- CVACT01Y
- CVACT02Y
- CVACT03Y
- CVCRD01Y
- CVCUS01Y
reads:
- ACCTDAT
- CUSTDAT
- CXACAIX
writes: []
db_tables: []
transactions:
- CAVW
mq_queues: []
---

# COACTVWC -- Business Rules

## Program Purpose

COACTVWC is an online CICS program that implements the Account View screen (transaction CAVW). It accepts an account number entered by the user, validates it, reads the account cross-reference (CXACAIX), account master (ACCTDAT), and customer master (CUSTDAT) files in sequence, then displays the full account and associated customer details on map CACTVWA (mapset COACTVW). The program follows the standard pseudo-conversational pattern: it returns to CICS after every screen send, and re-enters at 0000-MAIN with the commarea context flag (CDEMO-PGM-REENTER) set to distinguish a first-entry display from a re-entry with user input.

## Input / Output

| Direction | Resource   | Type | Description                                                           |
| --------- | ---------- | ---- | --------------------------------------------------------------------- |
| IN        | CACTVWA    | CICS | BMS map (mapset COACTVW) receiving account number entered by user     |
| IN        | CXACAIX    | CICS | VSAM alternate-index file; keyed by account ID; yields card/customer cross-reference |
| IN        | ACCTDAT    | CICS | VSAM account master file; keyed by account ID; yields account record  |
| IN        | CUSTDAT    | CICS | VSAM customer master file; keyed by customer ID; yields customer record |
| IN/OUT    | DFHCOMMAREA | CICS | Commarea carrying CARDDEMO-COMMAREA + WS-THIS-PROGCOMMAREA context    |
| OUT       | CACTVWA    | CICS | BMS map sent back to terminal with account and customer display data  |

## Business Rules

### PF-Key Routing

| #  | Rule                            | Condition                                                                   | Action                                                                                                                                       | Source Location         |
| -- | ------------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| 1  | PF3 exits to calling program    | CCARD-AID-PFK03 is TRUE                                                     | If CDEMO-FROM-TRANID is LOW-VALUES or spaces, route to menu (LIT-MENUTRANID = 'CM00', LIT-MENUPGM = 'COMEN01C'); otherwise route back to calling program/tranid via EXEC CICS XCTL | 0000-MAIN lines 324-352 |
| 2  | Only Enter and PF3 are valid    | Any AID key other than Enter or PF3 received                                | Force AID to CCARD-AID-ENTER (treat as Enter); invalid keys are silently remapped rather than rejected                                        | 0000-MAIN lines 306-314 |
| 3  | PF13-PF24 aliased to PF01-PF12  | EIBAID = DFHPF13 through DFHPF24                                            | Paragraph YYYY-STORE-PFKEY (CSSTRPFY copybook) maps shifted PF keys back to their PF01-PF12 equivalents in CCARD-AID-PFKxx flags            | YYYY-STORE-PFKEY (CSSTRPFY) |
| 4  | PF3 routing: TRANID and PROGRAM checked independently | CDEMO-FROM-TRANID tested separately from CDEMO-FROM-PROGRAM at lines 328-338 | TRANID: if LOW-VALUES or spaces move LIT-MENUTRANID ('CM00') to CDEMO-TO-TRANID, else move CDEMO-FROM-TRANID. PROGRAM: if LOW-VALUES or spaces move LIT-MENUPGM ('COMEN01C') to CDEMO-TO-PROGRAM, else move CDEMO-FROM-PROGRAM. The two checks are independent -- a mismatch is possible if commarea is partially populated | 0000-MAIN lines 328-339 |

### Program State Routing

| #  | Rule                                 | Condition                                                                   | Action                                                                                      | Source Location         |
| -- | ------------------------------------ | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ----------------------- |
| 5  | First-entry or menu-entry clears commarea | EIBCALEN = 0, OR (CDEMO-FROM-PROGRAM = 'COMEN01C' AND NOT CDEMO-PGM-REENTER) | INITIALIZE CARDDEMO-COMMAREA and WS-THIS-PROGCOMMAREA; start fresh                          | 0000-MAIN lines 282-293 |
| 6  | WS-COMMAREA always re-initialised at entry | Unconditional INITIALIZE WS-COMMAREA at line 270                        | WS-COMMAREA is zeroed out on every program entry before being conditionally repopulated from DFHCOMMAREA at lines 288-292; prior commarea content is always discarded first | 0000-MAIN lines 268-292 |
| 7  | First-entry sends blank input screen | CDEMO-PGM-ENTER is TRUE (initial entry state)                               | PERFORM 1000-SEND-MAP; return to CICS with TRANSID CAVW so next AID re-enters this program   | 0000-MAIN lines 353-360 |
| 8  | Re-entry processes user input        | CDEMO-PGM-REENTER is TRUE                                                   | PERFORM 2000-PROCESS-INPUTS; if INPUT-ERROR, send map with error; otherwise PERFORM 9000-READ-ACCT then send map with data | 0000-MAIN lines 361-374 |
| 9  | Unexpected state triggers plain-text error | WHEN OTHER in EVALUATE (not PF3, not ENTER, not REENTER state)         | Set ABEND-CULPRIT = 'COACTVWC', ABEND-CODE = '0001', WS-RETURN-MSG = 'UNEXPECTED DATA SCENARIO'; PERFORM SEND-PLAIN-TEXT | 0000-MAIN lines 375-382 |
| 10 | Fallthrough INPUT-ERROR catch after EVALUATE | INPUT-ERROR is TRUE at lines 387-392 after END-EVALUATE          | If an INPUT-ERROR slipped through the EVALUATE without being dispatched to COMMON-RETURN, lines 387-392 catch it: move WS-RETURN-MSG to CCARD-ERROR-MSG, PERFORM 1000-SEND-MAP, GO TO COMMON-RETURN | 0000-MAIN lines 387-392 |

### Input Validation

| #  | Rule                                     | Condition                                                                    | Action                                                                                                                    | Source Location               |
| -- | ---------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| 11 | Account ID asterisk / spaces normalised  | ACCTSIDI = '*' OR ACCTSIDI = SPACES                                          | Move LOW-VALUES to CC-ACCT-ID (treated as not supplied)                                                                   | 2200-EDIT-MAP-INPUTS line 628 |
| 12 | Account ID mandatory                     | CC-ACCT-ID = LOW-VALUES OR CC-ACCT-ID = SPACES after normalisation           | Set INPUT-ERROR, set FLG-ACCTFILTER-BLANK; if no prior error message set WS-RETURN-MSG = 'Account number not provided'; zero CDEMO-ACCT-ID; exit validation | 2210-EDIT-ACCOUNT lines 653-662 |
| 13 | Account ID must be numeric               | CC-ACCT-ID IS NOT NUMERIC                                                    | Set INPUT-ERROR, set FLG-ACCTFILTER-NOT-OK; if no prior error set WS-RETURN-MSG = 'Account Filter must  be a non-zero 11 digit number'; zero CDEMO-ACCT-ID | 2210-EDIT-ACCOUNT lines 666-676 |
| 14 | Account ID must be non-zero              | CC-ACCT-ID = ZEROES (all zeros, even if numeric)                             | Same as rule 13 -- combined in single IF; error message = 'Account Filter must  be a non-zero 11 digit number'            | 2210-EDIT-ACCOUNT lines 666-676 |
| 15 | Cross-field: at least one search criterion | FLG-ACCTFILTER-BLANK after individual field edit                            | Set NO-SEARCH-CRITERIA-RECEIVED (WS-RETURN-MSG = 'No input received')                                                    | 2200-EDIT-MAP-INPUTS lines 640-642 |
| 16 | Error message is write-once              | WS-RETURN-MSG-OFF is TRUE before setting any new error message               | First error message wins; subsequent validation failures do not overwrite the first message                               | 2210-EDIT-ACCOUNT lines 657-659, 670-673 |
| 17 | 2210-EDIT-ACCOUNT always initialises flag to NOT-OK | Unconditional SET at paragraph entry                            | SET FLG-ACCTFILTER-NOT-OK TO TRUE at line 650 before any tests; valid account flips it to ISVALID only in the ELSE branch at line 679 | 2210-EDIT-ACCOUNT line 650 |
| 18 | Runtime error text differs from 88-level definition | SEARCHED-ACCT-ZEROES and SEARCHED-ACCT-NOT-NUMERIC defined with VALUE 'Account number must be a non zero 11 digit number' | Actual runtime text moved at line 672 is 'Account Filter must  be a non-zero 11 digit number' (different wording: "Filter" vs "number", "non-zero" vs "non zero"). The 88-level definitions are never SET and are dead; the displayed message text is the literal at line 672, not the 88-level values | 2210-EDIT-ACCOUNT line 672; WS-RETURN-MSG lines 125-128 |

### Data Retrieval Sequencing

| #  | Rule                                         | Condition                                                                   | Action                                                                                                           | Source Location               |
| -- | -------------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| 19 | Card cross-reference must be found first     | Always executed when input passes validation                                | PERFORM 9200-GETCARDXREF-BYACCT; reads CXACAIX by account ID (WS-CARD-RID-ACCT-ID-X, 11 bytes)                  | 9000-READ-ACCT lines 693-699  |
| 20 | Account data read only if xref found         | FLG-ACCTFILTER-NOT-OK after xref read means xref failed                     | GO TO 9000-READ-ACCT-EXIT; skip account and customer reads; this guard works correctly                           | 9000-READ-ACCT lines 697-699  |
| 21 | Customer data read only if account found (DEFECTIVE -- see note) | `IF DID-NOT-FIND-ACCT-IN-ACCTDAT` at line 704 -- but the SET statement that activates this 88-level is commented out (line 792). The 9300 NOTFND path uses STRING to write a different message text, so this 88-level is never true. The GO TO at line 705 is dead code. | GO TO 9000-READ-ACCT-EXIT is intended to skip customer read, but is never reached when account is not found | 9000-READ-ACCT lines 704-706, 9300-GETACCTDATA-BYACCT line 792 |
| 22 | Customer skip also defective (DEFECTIVE -- see note) | `IF DID-NOT-FIND-CUST-IN-CUSTDAT` at line 713 -- same pattern; SET is commented out at line 842; 88-level is never true | GO TO 9000-READ-ACCT-EXIT is dead code | 9000-READ-ACCT lines 713-715, 9400-GETCUSTDATA-BYCUST line 842 |
| 23 | Customer ID sourced from xref record         | After successful xref read                                                  | XREF-CUST-ID moved to CDEMO-CUST-ID; XREF-CARD-NUM moved to CDEMO-CARD-NUM; CDEMO-CUST-ID then used as key for customer read | 9200-GETCARDXREF-BYACCT lines 739-740, 9000-READ-ACCT line 708 |

**Note on rules 21 and 22:** The intended intent is clear from the commented-out SET statements and the comment at line 696 (`*    IF DID-NOT-FIND-ACCT-IN-CARDXREF`). The developer refactored the skip guard for the xref step to use `FLG-ACCTFILTER-NOT-OK` (correct), but left the account and customer skip guards referencing 88-level conditions defined on WS-RETURN-MSG whose SET statements were commented out. As a result, when ACCTDAT or CUSTDAT returns NOTFND, the program proceeds to attempt the next read in sequence rather than skipping it. The NOTFND path still sets INPUT-ERROR and FLG-ACCTFILTER-NOT-OK, so subsequent display logic is not affected, but the customer read will still be attempted even when the account read failed.

### Screen Display Rules

| #  | Rule                                             | Condition                                                                   | Action                                                                                                           | Source Location               |
| -- | ------------------------------------------------ | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| 24 | Account field highlighted red if invalid         | FLG-ACCTFILTER-NOT-OK is TRUE                                               | Move DFHRED to ACCTSIDC of CACTVWAO                                                                              | 1300-SETUP-SCREEN-ATTRS line 558 |
| 25 | Account field shows asterisk and red if blank on re-entry | FLG-ACCTFILTER-BLANK AND CDEMO-PGM-REENTER                        | Move '*' to ACCTSIDO and DFHRED to ACCTSIDC                                                                      | 1300-SETUP-SCREEN-ATTRS lines 561-565 |
| 26 | Default prompt shown when no info message        | WS-NO-INFO-MESSAGE (SPACES or LOW-VALUES) on screen setup                   | SET WS-PROMPT-FOR-INPUT = 'Enter or update id of account to display'                                             | 1200-SETUP-SCREEN-VARS line 528 |
| 27 | Account ID cleared on blank filter               | FLG-ACCTFILTER-BLANK is TRUE                                                | Move LOW-VALUES to ACCTSIDO of CACTVWAO (field blanked on screen)                                                | 1200-SETUP-SCREEN-VARS line 466 |
| 28 | Account data displayed only when read succeeds   | FOUND-ACCT-IN-MASTER OR FOUND-CUST-IN-MASTER; guarded by EIBCALEN != 0      | Move account fields (status, balance, credit limit, cash limit, cycle credit/debit, open/expiry/reissue dates, group ID) to output map; entire display block is skipped when EIBCALEN = 0 | 1200-SETUP-SCREEN-VARS lines 462-491 |
| 29 | Customer data displayed only when customer read succeeds | FOUND-CUST-IN-MASTER                                                | Move customer fields (ID, SSN formatted, FICO score, DOB, name parts, address lines, state, zip, country, phones, govt ID, EFT account ID, primary card holder flag) to output map | 1200-SETUP-SCREEN-VARS lines 493-523 |
| 30 | SSN formatted with dashes for display            | Always when customer data is displayed                                      | STRING CUST-SSN(1:3) '-' CUST-SSN(4:2) '-' CUST-SSN(6:4) DELIMITED BY SIZE INTO ACSTSSNO; raw SSN is never shown unformatted | 1200-SETUP-SCREEN-VARS lines 496-504 |
| 31 | Info message colour neutral when present         | NOT WS-NO-INFO-MESSAGE                                                      | Move DFHNEUTR to INFOMSGC; when no message present move DFHBMDAR (dark) to INFOMSGC                              | 1300-SETUP-SCREEN-ATTRS lines 567-571 |
| 32 | Cursor always positioned on account input field  | All display cases (WHEN FLG-ACCTFILTER-NOT-OK, WHEN FLG-ACCTFILTER-BLANK, WHEN OTHER) | Move -1 to ACCTSIDL of CACTVWAI to position cursor; EVALUATE WHEN OTHER also falls to same action so cursor positioning is universal | 1300-SETUP-SCREEN-ATTRS lines 546-551 |
| 33 | WS-INFORM-OUTPUT 88-level is defined but never set | 88 WS-INFORM-OUTPUT VALUE 'Displaying details of given Account' on WS-INFO-MSG | Dead constant; WS-INFO-MSG is set to SPACES in 9000-READ-ACCT (line 689 via SET WS-NO-INFO-MESSAGE TO TRUE) but WS-INFORM-OUTPUT is never explicitly set; success path never shows 'Displaying details of given Account' | WS-INFO-MSG / 9000-READ-ACCT line 689 |

### Pseudo-Conversational Return

| #  | Rule                                         | Condition                | Action                                                                                               | Source Location          |
| -- | -------------------------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------- | ------------------------ |
| 34 | Program always returns with own transaction  | COMMON-RETURN paragraph  | EXEC CICS RETURN TRANSID(LIT-THISTRANID = 'CAVW') COMMAREA(WS-COMMAREA) LENGTH(LENGTH OF WS-COMMAREA = 2000); ensures next terminal input re-enters COACTVWC; commarea length is always 2000 bytes because WS-COMMAREA is declared PIC X(2000) | COMMON-RETURN lines 402-406 |
| 35 | Commarea packs both application and program context | On every return   | CARDDEMO-COMMAREA packed into WS-COMMAREA at offset 1; WS-THIS-PROGCOMMAREA packed immediately after | COMMON-RETURN lines 397-400 |
| 36 | Error message propagated to map before return | Always at COMMON-RETURN  | WS-RETURN-MSG moved to CCARD-ERROR-MSG before commarea packing and RETURN                            | COMMON-RETURN line 395   |

## Calculations

| Calculation         | Formula / Logic                                                                 | Input Fields                              | Output Field         | Source Location             |
| ------------------- | ------------------------------------------------------------------------------- | ----------------------------------------- | -------------------- | --------------------------- |
| SSN display format  | Concatenate SSN(1:3) + '-' + SSN(4:2) + '-' + SSN(6:4) using STRING DELIMITED BY SIZE | CUST-SSN (9-char raw field from CVCUS01Y) | ACSTSSNO of CACTVWAO | 1200-SETUP-SCREEN-VARS lines 496-504 |
| Commarea offset pack | WS-THIS-PROGCOMMAREA starts at byte (LENGTH OF CARDDEMO-COMMAREA + 1) in WS-COMMAREA | CARDDEMO-COMMAREA, WS-THIS-PROGCOMMAREA | WS-COMMAREA          | COMMON-RETURN lines 398-400 |
| Date/time display   | FUNCTION CURRENT-DATE split into MM/DD/YY and HH:MM:SS sub-fields              | WS-CURDATE-DATA (from CSDAT01Y)           | CURDATEO, CURTIMEO on CACTVWAO | 1100-SCREEN-INIT lines 443-453 |

## Error Handling

| Condition                                           | Action                                                                                                    | Return Code         | Source Location               |
| --------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------- | ----------------------------- |
| Account ID is blank / not supplied                  | Set INPUT-ERROR; set WS-RETURN-MSG = 'Account number not provided'; zero CDEMO-ACCT-ID                    | INPUT-ERROR = '1'   | 2210-EDIT-ACCOUNT lines 653-662 |
| Account ID is not numeric or is zero                | Set INPUT-ERROR; set WS-RETURN-MSG = 'Account Filter must  be a non-zero 11 digit number'                 | INPUT-ERROR = '1'   | 2210-EDIT-ACCOUNT lines 666-676 |
| No search criteria (account field blank after edit) | Set NO-SEARCH-CRITERIA-RECEIVED; WS-RETURN-MSG = 'No input received'                                     | INPUT-ERROR = '1'   | 2200-EDIT-MAP-INPUTS lines 640-642 |
| EXEC CICS RECEIVE MAP response not checked          | 2100-RECEIVE-MAP captures WS-RESP-CD and WS-REAS-CD from the RECEIVE but never evaluates them; a MAPFAIL or other CICS error on the RECEIVE is silently ignored and processing continues with whatever data is in CACTVWAI | None (silent)       | 2100-RECEIVE-MAP lines 611-617 |
| CXACAIX READ DFHRESP(NOTFND)                        | Set INPUT-ERROR, FLG-ACCTFILTER-NOT-OK; build message 'Account:[id] not found in Cross ref file.  Resp:[r] Reas:[r2]' into WS-RETURN-MSG | INPUT-ERROR = '1' | 9200-GETCARDXREF-BYACCT lines 741-758 |
| CXACAIX READ DFHRESP(OTHER)                         | Set INPUT-ERROR, FLG-ACCTFILTER-NOT-OK; build WS-FILE-ERROR-MESSAGE = 'File Error: READ on CXACAIX  returned RESP [r] ,RESP2 [r2]' into WS-RETURN-MSG | INPUT-ERROR = '1' | 9200-GETCARDXREF-BYACCT lines 759-767 |
| ACCTDAT READ DFHRESP(NOTFND)                        | Set INPUT-ERROR, FLG-ACCTFILTER-NOT-OK; build message 'Account:[id] not found in Acct Master file.Resp:[r] Reas:[r2]' into WS-RETURN-MSG; NOTE: DID-NOT-FIND-ACCT-IN-ACCTDAT SET is commented out so skip guard at line 704 is ineffective | INPUT-ERROR = '1' | 9300-GETACCTDATA-BYACCT lines 789-807 |
| ACCTDAT READ DFHRESP(OTHER)                         | Set INPUT-ERROR, FLG-ACCTFILTER-NOT-OK; build WS-FILE-ERROR-MESSAGE into WS-RETURN-MSG (file = 'ACCTDAT ') | INPUT-ERROR = '1' | 9300-GETACCTDATA-BYACCT lines 809-816 |
| CUSTDAT READ DFHRESP(NOTFND)                        | Set INPUT-ERROR, FLG-CUSTFILTER-NOT-OK; ERROR-RESP/ERROR-RESP2 always populated (outside WS-RETURN-MSG-OFF guard -- see note); build message 'CustId:[id] not found in customer master.Resp:[r] REAS:[r2]' into WS-RETURN-MSG only if WS-RETURN-MSG-OFF; NOTE: DID-NOT-FIND-CUST-IN-CUSTDAT SET is commented out so skip guard at line 713 is ineffective | INPUT-ERROR = '1' | 9400-GETCUSTDATA-BYCUST lines 839-857 |
| CUSTDAT READ DFHRESP(OTHER)                         | Set INPUT-ERROR, FLG-CUSTFILTER-NOT-OK; build WS-FILE-ERROR-MESSAGE into WS-RETURN-MSG (file = 'CUSTDAT ') | INPUT-ERROR = '1' | 9400-GETCUSTDATA-BYCUST lines 858-865 |
| Unexpected program state (EVALUATE WHEN OTHER)      | Set ABEND-CULPRIT = 'COACTVWC', ABEND-CODE = '0001'; WS-RETURN-MSG = 'UNEXPECTED DATA SCENARIO'; PERFORM SEND-PLAIN-TEXT (sends text then EXEC CICS RETURN) | Abend code '0001' | 0000-MAIN lines 375-382 |
| Any CICS ABEND (handled via HANDLE ABEND)           | ABEND-ROUTINE: if ABEND-MSG is LOW-VALUES set it to 'UNEXPECTED ABEND OCCURRED.'; move LIT-THISPGM to ABEND-CULPRIT; EXEC CICS SEND ABEND-DATA; cancel HANDLE ABEND; EXEC CICS ABEND ABCODE('9999') | ABEND code '9999' | ABEND-ROUTINE lines 916-934 |
| SEND-LONG-TEXT paragraph exists but is dead code    | SEND-LONG-TEXT (lines 896-906) performs EXEC CICS SEND TEXT FROM(WS-LONG-MSG) then EXEC CICS RETURN; comment block explicitly notes it is for debugging and should not be used in regular course; all PERFORM SEND-LONG-TEXT calls within error handlers are commented out; paragraph is never invoked | N/A | SEND-LONG-TEXT lines 896-906; commented calls at lines 767-768, 817-818, 866-867 |

**Note on CUSTDAT NOTFND error path:** Unlike the equivalent error paths in 9200 and 9300 where ERROR-RESP and ERROR-RESP2 are moved inside the `IF WS-RETURN-MSG-OFF` block, in 9400 (lines 843-844) these moves occur unconditionally before the IF test. This means WS-FILE-ERROR-MESSAGE sub-fields ERROR-RESP and ERROR-RESP2 are always overwritten when CUSTDAT returns NOTFND, even when a prior error message is already set. This is a minor inconsistency with the other file read paragraphs but has no observable impact on displayed messages.

**Note on RECEIVE MAP response ignored:** 2100-RECEIVE-MAP captures WS-RESP-CD and WS-REAS-CD but the paragraph contains no EVALUATE or IF on those values. If CICS raises MAPFAIL (e.g. no data entered), the program silently proceeds to validate empty input data rather than handling the condition distinctly. This means MAPFAIL and a blank-but-sent form are handled identically -- both produce an "Account number not provided" validation error -- which is functionally acceptable but not explicitly coded.

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. 0000-MAIN -- Entry point; unconditionally initialises CC-WORK-AREA, WS-MISC-STORAGE, and WS-COMMAREA (WS-COMMAREA is always zeroed before being repopulated); sets up HANDLE ABEND to ABEND-ROUTINE; stores PF key; routes on program state
2. YYYY-STORE-PFKEY (CSSTRPFY copybook) -- Maps EIBAID to CCARD-AID-PFKxx flags; PF13-PF24 aliased to PF01-PF12
3. EVALUATE on CCARD-AID-PFK03 / CDEMO-PGM-ENTER / CDEMO-PGM-REENTER -- Main dispatch
4. If CDEMO-PGM-ENTER: PERFORM 1000-SEND-MAP THRU 1000-SEND-MAP-EXIT then GO TO COMMON-RETURN
5. If CDEMO-PGM-REENTER: PERFORM 2000-PROCESS-INPUTS THRU 2000-PROCESS-INPUTS-EXIT
6.   2000-PROCESS-INPUTS -- Calls 2100-RECEIVE-MAP then 2200-EDIT-MAP-INPUTS; copies WS-RETURN-MSG to CCARD-ERROR-MSG; sets CCARD-NEXT-PROG (LIT-THISPGM = 'COACTVWC'), CCARD-NEXT-MAPSET (LIT-THISMAPSET = 'COACTVW '), CCARD-NEXT-MAP (LIT-THISMAP = 'CACTVWA') -- self-referential navigation pointers
7.     2100-RECEIVE-MAP -- EXEC CICS RECEIVE MAP(CACTVWA) INTO(CACTVWAI); RESP captured but not evaluated (see error handling note)
8.     2200-EDIT-MAP-INPUTS -- Normalises account field, calls 2210-EDIT-ACCOUNT, checks cross-field blank
9.       2210-EDIT-ACCOUNT -- Validates account ID: mandatory, numeric, non-zero; sets flags and error messages
10. If INPUT-ERROR after process-inputs: PERFORM 1000-SEND-MAP then GO TO COMMON-RETURN
11. If INPUT-OK: PERFORM 9000-READ-ACCT THRU 9000-READ-ACCT-EXIT
12.   9000-READ-ACCT -- Orchestrates three-file read sequence; clears info message at entry
13.     9200-GETCARDXREF-BYACCT -- EXEC CICS READ CXACAIX by account ID; on success extracts XREF-CUST-ID and XREF-CARD-NUM; on failure sets INPUT-ERROR; FLG-ACCTFILTER-NOT-OK guard is operative
14.     9300-GETACCTDATA-BYACCT -- EXEC CICS READ ACCTDAT by account ID (only if xref succeeded); on success sets FOUND-ACCT-IN-MASTER; DID-NOT-FIND-ACCT-IN-ACCTDAT skip guard is inoperative (defect)
15.     9400-GETCUSTDATA-BYCUST -- EXEC CICS READ CUSTDAT by customer ID from xref; also attempted even when ACCTDAT failed (defect); on success sets FOUND-CUST-IN-MASTER
16. PERFORM 1000-SEND-MAP THRU 1000-SEND-MAP-EXIT -- sends results (or errors) to screen
17.   1000-SEND-MAP -- Calls 1100-SCREEN-INIT, 1200-SETUP-SCREEN-VARS, 1300-SETUP-SCREEN-ATTRS, 1400-SEND-SCREEN
18.     1100-SCREEN-INIT -- Blanks map, populates titles, transaction/program name, current date/time; FUNCTION CURRENT-DATE called twice (lines 434, 441) -- redundant but harmless
19.     1200-SETUP-SCREEN-VARS -- Moves account and customer data fields to output map; formats SSN with dashes; sets info/return messages
20.     1300-SETUP-SCREEN-ATTRS -- Sets account field to unprotected; positions cursor on account input; sets red colour on validation errors
21.     1400-SEND-SCREEN -- EXEC CICS SEND MAP(CACTVWA) CURSOR ERASE FREEKB; sets CDEMO-PGM-REENTER for next entry
22. COMMON-RETURN -- Packs commarea, EXEC CICS RETURN TRANSID('CAVW') LENGTH(LENGTH OF WS-COMMAREA) -- program suspends awaiting next user action

**Note on duplicate paragraph:** 0000-MAIN-EXIT is defined twice (lines 408 and 411), both with EXIT. The duplicate is harmless but indicates copy/paste error during development.

**Note on dead literals in WS-LITERALS:** The following data items are defined in WS-LITERALS with VALUE clauses but are never referenced anywhere in the PROCEDURE DIVISION. They appear to be scaffolding for planned navigation features that were not implemented in this program: `LIT-CCLISTPGM` ('COCRDLIC'), `LIT-CCLISTTRANID` ('CCLI'), `LIT-CCLISTMAPSET`, `LIT-CCLISTMAP`, `LIT-CARDUPDATEPGM` ('COCRDUPC'), `LIT-CARDUDPATETRANID` ('CCUP'), `LIT-CARDUPDATEMAPSET`, `LIT-CARDUPDATEMAP`, `LIT-CARDDTLPGM` ('COCRDSLC'), `LIT-CARDDTLTRANID` ('CCDL'), `LIT-CARDFILENAME` ('CARDDAT '), `LIT-CARDFILENAME-ACCT-PATH` ('CARDAIX '), `LIT-ALL-ALPHA-FROM`, `LIT-ALL-SPACES-TO`, `LIT-UPPER`, `LIT-LOWER`. None of these imply actual file reads or program calls from COACTVWC.

**Note on dead 88-level conditions on WS-RETURN-MSG:** In addition to the 88-levels already noted, the following 88-levels are defined on WS-RETURN-MSG but never SET in the PROCEDURE DIVISION: `WS-EXIT-MESSAGE` (VALUE 'PF03 pressed.Exiting              '), `SEARCHED-ACCT-ZEROES` (VALUE 'Account number must be a non zero 11 digit number'), `SEARCHED-ACCT-NOT-NUMERIC` (VALUE 'Account number must be a non zero 11 digit number'), `DID-NOT-FIND-ACCT-IN-CARDXREF`, `DID-NOT-FIND-ACCT-IN-ACCTDAT`, `DID-NOT-FIND-CUST-IN-CUSTDAT`, `XREF-READ-ERROR`, `CODING-TO-BE-DONE`. The 88-levels for SEARCHED-ACCT-ZEROES and SEARCHED-ACCT-NOT-NUMERIC define text that differs from the actual runtime message text at line 672 ('Account Filter must  be a non-zero 11 digit number'): the 88-levels say "Account number" while the code says "Account Filter". This discrepancy means any code comparison using these 88-levels would fail to match the actual error text set at runtime.

**Note on duplicate 88-level condition name:** `INPUT-PENDING` is defined twice -- once on WS-INPUT-FLAG (line 53, VALUE LOW-VALUES) and once on WS-PFK-FLAG (line 57, VALUE LOW-VALUES). This is a COBOL coding defect; both 88-levels have the same name and value. In practice `INPUT-PENDING` is never SET or tested in the PROCEDURE DIVISION, so there is no runtime impact, but the duplicate definition would cause a compiler warning and makes the code ambiguous.
