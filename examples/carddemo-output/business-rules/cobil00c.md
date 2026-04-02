---
type: business-rules
program: COBIL00C
program_type: online
status: draft
confidence: high
last_pass: 5
calls: []
called_by: []
uses_copybooks:
- COBIL00
- COCOM01Y
- COTTL01Y
- CSDAT01Y
- CSMSG01Y
- CVACT01Y
- CVACT03Y
- CVTRA05Y
reads:
- ACCTDAT
- CXACAIX
- TRANSACT
writes:
- ACCTDAT
- TRANSACT
db_tables: []
transactions:
- CB00
mq_queues: []
---

# COBIL00C -- Business Rules

## Program Purpose

COBIL00C is the online bill payment program for the CardDemo Credit Card Management System. It allows a cardholder to pay their account balance in full by: reading the current account balance from ACCTDAT, looking up the card number from the CXACAIX cross-reference index, generating the next sequential transaction ID by reading backwards through TRANSACT, writing a new bill payment transaction record to TRANSACT, and reducing the account balance to zero via a REWRITE to ACCTDAT. The program operates under CICS transaction CB00 and communicates with other programs via CARDDEMO-COMMAREA.

## Input / Output

| Direction | Resource | Type | Description |
| --------- | -------- | ---- | ----------- |
| IN        | ACCTDAT  | CICS VSAM (READ UPDATE) | Account master record keyed by ACCT-ID (11-digit account number) |
| IN/OUT    | ACCTDAT  | CICS VSAM (REWRITE)     | Account balance reduced by payment amount after confirmation |
| IN        | CXACAIX  | CICS VSAM (READ)        | Card cross-reference alternate index, keyed by XREF-ACCT-ID, returns XREF-CARD-NUM |
| IN        | TRANSACT | CICS VSAM (STARTBR / READPREV / ENDBR) | Transaction file browsed backwards from HIGH-VALUES to find highest existing transaction ID |
| OUT       | TRANSACT | CICS VSAM (WRITE)       | New bill payment transaction record written with type '02', category 2 |
| IN/OUT    | COBIL0A  | CICS BMS Map (COBIL00)  | Bill payment screen -- receives account ID and confirmation flag, sends balance and messages |
| IN/OUT    | CARDDEMO-COMMAREA | CICS COMMAREA | Cross-program communication area for navigation and context |

## Business Rules

### Screen Entry and Navigation

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 1 | No communication area on entry | `EIBCALEN = 0` | Transfer control to sign-on program `COSGN00C` via XCTL -- session not initialised | MAIN-PARA lines 107-109 |
| 2 | First entry (not re-entering) | `NOT CDEMO-PGM-REENTER` | Set re-enter flag, initialise screen to LOW-VALUES, set cursor to Account ID field (`ACTIDINL = -1`), then optionally pre-populate from commarea | MAIN-PARA lines 112-122 |
| 3 | Pre-populate from commarea on first entry | `CDEMO-CB00-TRN-SELECTED NOT = SPACES AND LOW-VALUES` | Move `CDEMO-CB00-TRN-SELECTED` to `ACTIDINI` and immediately perform PROCESS-ENTER-KEY to auto-process the pre-selected account | MAIN-PARA lines 116-121 |
| 4 | PF3 key pressed -- navigate back | `EIBAID = DFHPF3` and `CDEMO-FROM-PROGRAM = SPACES OR LOW-VALUES` | Route to `COMEN01C` (main menu) | MAIN-PARA lines 129-130 |
| 5 | PF3 key pressed -- return to caller | `EIBAID = DFHPF3` and `CDEMO-FROM-PROGRAM` is populated | Route to the program stored in `CDEMO-FROM-PROGRAM` | MAIN-PARA lines 132-134 |
| 6 | PF4 key pressed -- clear screen | `EIBAID = DFHPF4` | Perform CLEAR-CURRENT-SCREEN: reinitialise all input fields and resend the screen | MAIN-PARA line 137 |
| 7 | Invalid function key pressed | `EIBAID = OTHER` (not ENTER, PF3, or PF4) | Set error flag, move `CCDA-MSG-INVALID-KEY` to WS-MESSAGE, resend screen with error | MAIN-PARA lines 139-141 |
| 8 | RETURN to same transaction | Always, at end of MAIN-PARA | `EXEC CICS RETURN TRANSID(WS-TRANID)` with commarea -- keeps transaction CB00 active | MAIN-PARA lines 146-149 |

### Input Validation (PROCESS-ENTER-KEY)

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 9  | Account ID is mandatory | `ACTIDINI OF COBIL0AI = SPACES OR LOW-VALUES` | Set error flag, message: `'Acct ID can NOT be empty...'`, set cursor to account ID field, resend screen | PROCESS-ENTER-KEY lines 159-164 |
| 10 | Confirmation flag must be Y, y, N, n, SPACES, or LOW-VALUES | `CONFIRMI OF COBIL0AI` evaluated against those values | If any other value: set error flag, message: `'Invalid value. Valid values are (Y/N)...'`, set cursor to confirm field, resend screen | PROCESS-ENTER-KEY lines 185-190 |
| 11 | Confirmation 'N' or 'n' cancels payment | `CONFIRMI = 'N'` or `'n'` | Perform CLEAR-CURRENT-SCREEN (reinitialise fields and resend), then set `WS-ERR-FLG = 'Y'` -- payment not processed | PROCESS-ENTER-KEY lines 178-181 |
| 12 | Confirmation SPACES or LOW-VALUES -- display balance only | `CONFIRMI = SPACES OR LOW-VALUES` | Perform READ-ACCTDAT-FILE to retrieve and display balance, do not proceed to payment | PROCESS-ENTER-KEY lines 182-184 |
| 13 | Account balance must be positive to make a payment | `ACCT-CURR-BAL <= ZEROS AND ACTIDINI NOT = SPACES AND LOW-VALUES` | Set error flag, message: `'You have nothing to pay...'`, set cursor to account ID field, resend screen | PROCESS-ENTER-KEY lines 197-205 |

### Payment Confirmation and Processing

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 14 | Confirmation 'Y' or 'y' triggers full payment | `CONFIRMI = 'Y'` or `'y'`; `CONF-PAY-YES` flag set | Read CXACAIX for card number, obtain next transaction ID, build transaction record, write to TRANSACT, reduce account balance to zero, update ACCTDAT | PROCESS-ENTER-KEY lines 174-235 |
| 15 | No confirmation provided -- prompt user | `CONF-PAY-YES` is false and no error | Message: `'Confirm to make a bill payment...'`, cursor to confirm field; screen is resent awaiting Y/N | PROCESS-ENTER-KEY lines 236-240 |
| 16 | Transaction type for bill payment | Hardcoded at write time | `TRAN-TYPE-CD = '02'` | PROCESS-ENTER-KEY line 220 |
| 17 | Transaction category for bill payment | Hardcoded at write time | `TRAN-CAT-CD = 2` | PROCESS-ENTER-KEY line 221 |
| 18 | Transaction source for bill payment | Hardcoded at write time | `TRAN-SOURCE = 'POS TERM'` | PROCESS-ENTER-KEY line 222 |
| 19 | Transaction description for bill payment | Hardcoded at write time | `TRAN-DESC = 'BILL PAYMENT - ONLINE'` | PROCESS-ENTER-KEY line 223 |
| 20 | Merchant ID for bill payment | Hardcoded at write time | `TRAN-MERCHANT-ID = 999999999` (sentinel value -- no real merchant) | PROCESS-ENTER-KEY line 226 |
| 21 | Merchant name for bill payment | Hardcoded at write time | `TRAN-MERCHANT-NAME = 'BILL PAYMENT'` | PROCESS-ENTER-KEY line 227 |
| 22 | Merchant city for bill payment | Hardcoded at write time | `TRAN-MERCHANT-CITY = 'N/A'` | PROCESS-ENTER-KEY line 228 |
| 23 | Merchant ZIP for bill payment | Hardcoded at write time | `TRAN-MERCHANT-ZIP = 'N/A'` | PROCESS-ENTER-KEY line 229 |
| 24 | Transaction amount equals current balance | `TRAN-AMT = ACCT-CURR-BAL` | The entire current balance is used as the payment amount -- this is a full-balance payment only, no partial payments | PROCESS-ENTER-KEY line 224 |
| 25 | Card number copied from cross-reference | `TRAN-CARD-NUM = XREF-CARD-NUM` (from READ-CXACAIX-FILE result) | The card number associated with the account is stored on the transaction record | PROCESS-ENTER-KEY line 225 |
| 26 | Transaction timestamps set at processing time | `GET-CURRENT-TIMESTAMP` performed | Both `TRAN-ORIG-TS` and `TRAN-PROC-TS` receive the same current timestamp (no deferred processing) | PROCESS-ENTER-KEY lines 230-232 |

### Transaction ID Generation

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 27 | Highest transaction ID located by backward browse | Before writing new transaction | Set `TRAN-ID = HIGH-VALUES`, STARTBR from that position, then READPREV to read the last (highest) record | PROCESS-ENTER-KEY lines 212-215 |
| 28 | New transaction ID is highest existing + 1 | `WS-TRAN-ID-NUM = TRAN-ID (numeric); ADD 1 TO WS-TRAN-ID-NUM` | Next transaction ID is sequential increment of the maximum existing ID | PROCESS-ENTER-KEY lines 216-219 |
| 29 | Empty transaction file -- STARTBR NOTFND blocks first payment | `DFHRESP(NOTFND)` on STARTBR when TRANSACT has no records | Sets ERR-FLG-ON and message `'Transaction ID NOT found...'` -- processing aborts. The READPREV ENDFILE path (which would set TRAN-ID=ZEROS to seed the first ID) is unreachable when the file is truly empty because STARTBR fails first. **Code defect: the program cannot successfully process the very first bill payment on an empty TRANSACT file.** | STARTBR-TRANSACT-FILE lines 454-459 |
| 30 | Empty transaction file -- READPREV ENDFILE path (conditional) | `DFHRESP(ENDFILE)` on READPREV | Sets `TRAN-ID = ZEROS` so that ADD 1 produces transaction ID 1. This path is only reachable if STARTBR succeeded (meaning at least one record already exists), so in practice it handles the case where STARTBR positioned past the end of available records, not a truly empty file. | READPREV-TRANSACT-FILE lines 487-488 |

### Successful Payment Confirmation Message

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 31 | Payment success notification | `DFHRESP(NORMAL)` on WRITE-TRANSACT-FILE | Error message area coloured GREEN (`DFHGREEN`); message composed via STRING as: `'Payment successful. '` + `' Your Transaction ID is '` + TRAN-ID (DELIMITED BY SPACE) + `'.'` -- note the two adjacent literals produce a double space between "successful." and "Your" | WRITE-TRANSACT-FILE lines 523-532 |
| 32 | Screen cleared after successful payment | On WRITE-TRANSACT-FILE NORMAL response | `INITIALIZE-ALL-FIELDS` performed before building success message -- clears `ACTIDINI`, `CURBALI`, `CONFIRMI`, and `WS-MESSAGE`; sets cursor to account ID field (`ACTIDINL = -1`) | WRITE-TRANSACT-FILE line 524 |

### Navigation Back Fallback

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 33 | Default back-navigation target | `CDEMO-TO-PROGRAM = LOW-VALUES OR SPACES` at time of RETURN-TO-PREV-SCREEN | Defaults to `COSGN00C` if no destination was set | RETURN-TO-PREV-SCREEN lines 275-277 |
| 34 | Commarea updated before XCTL | Always on RETURN-TO-PREV-SCREEN | `CDEMO-FROM-TRANID = WS-TRANID` ('CB00'), `CDEMO-FROM-PROGRAM = WS-PGMNAME` ('COBIL00C'), `CDEMO-PGM-CONTEXT = ZEROS` | RETURN-TO-PREV-SCREEN lines 278-280 |

## Calculations

| Calculation | Formula / Logic | Input Fields | Output Field | Source Location |
| --- | --- | --- | --- | --- |
| New account balance after payment | `ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT` (no ROUNDED, no ON SIZE ERROR) | `ACCT-CURR-BAL` (PIC S9(10)V99), `TRAN-AMT` (PIC S9(09)V99, set equal to ACCT-CURR-BAL) | `ACCT-CURR-BAL` -- result is always zero since TRAN-AMT equals ACCT-CURR-BAL | PROCESS-ENTER-KEY line 234 |
| Next transaction ID | `WS-TRAN-ID-NUM = numeric value of TRAN-ID from last record; ADD 1 TO WS-TRAN-ID-NUM` | `TRAN-ID` (PIC X(16)) from last READPREV record | `WS-TRAN-ID-NUM` (PIC 9(16)), then moved back to `TRAN-ID` | PROCESS-ENTER-KEY lines 216-219 |
| Current timestamp assembly | CICS ASKTIME -> FORMATTIME (YYYYMMDD with '-' separator, HH:MM:SS with ':' separator); assembled as `WS-TIMESTAMP(01:10) = date`, `WS-TIMESTAMP(12:08) = time`, `WS-TIMESTAMP-TM-MS6 = ZEROS`. Character position 11 of WS-TIMESTAMP (the separator between the date and time substrings) is not explicitly set; it retains whatever INITIALIZE WS-TIMESTAMP produced (low-values / spaces). | `WS-ABS-TIME` (CICS absolute time PIC S9(15) COMP-3) | `WS-TIMESTAMP` (used for both TRAN-ORIG-TS and TRAN-PROC-TS) | GET-CURRENT-TIMESTAMP lines 251-266 |

## Error Handling

| Condition | Action | Return Code | Source Location |
| ----------------- | -------------------------- | ----------- | --------------- |
| ACCTDAT READ -- account not found (`DFHRESP(NOTFND)`) | Set `WS-ERR-FLG = 'Y'`, message: `'Account ID NOT found...'`, cursor to account ID field, resend screen | WS-RESP-CD = DFHRESP(NOTFND) | READ-ACCTDAT-FILE lines 359-364 |
| ACCTDAT READ -- unexpected CICS error | DISPLAY `'RESP:' WS-RESP-CD 'REAS:' WS-REAS-CD`, set error flag, message: `'Unable to lookup Account...'`, resend screen | WS-RESP-CD = OTHER | READ-ACCTDAT-FILE lines 365-371 |
| ACCTDAT REWRITE -- account not found (`DFHRESP(NOTFND)`) | Set error flag, message: `'Account ID NOT found...'`, cursor to account ID field, resend screen | WS-RESP-CD = DFHRESP(NOTFND) | UPDATE-ACCTDAT-FILE lines 390-395 |
| ACCTDAT REWRITE -- unexpected CICS error | DISPLAY resp/reason codes, set error flag, message: `'Unable to Update Account...'`, resend screen | WS-RESP-CD = OTHER | UPDATE-ACCTDAT-FILE lines 396-402 |
| CXACAIX READ -- xref record not found (`DFHRESP(NOTFND)`) | Set error flag, message: `'Account ID NOT found...'`, cursor to account ID field, resend screen | WS-RESP-CD = DFHRESP(NOTFND) | READ-CXACAIX-FILE lines 423-428 |
| CXACAIX READ -- unexpected CICS error | DISPLAY resp/reason codes, set error flag, message: `'Unable to lookup XREF AIX file...'`, resend screen | WS-RESP-CD = OTHER | READ-CXACAIX-FILE lines 429-435 |
| TRANSACT STARTBR -- no transactions found (`DFHRESP(NOTFND)`) | Set error flag, message: `'Transaction ID NOT found...'`, cursor to account ID field, resend screen -- also blocks first-ever payment (see Rule 29) | WS-RESP-CD = DFHRESP(NOTFND) | STARTBR-TRANSACT-FILE lines 454-459 |
| TRANSACT STARTBR -- unexpected CICS error | DISPLAY resp/reason codes, set error flag, message: `'Unable to lookup Transaction...'`, resend screen | WS-RESP-CD = OTHER | STARTBR-TRANSACT-FILE lines 460-466 |
| TRANSACT READPREV -- end of file | Set `TRAN-ID = ZEROS` (treated as "no prior transactions above start position") -- processing continues normally to generate transaction ID 1 | WS-RESP-CD = DFHRESP(ENDFILE) | READPREV-TRANSACT-FILE lines 487-488 |
| TRANSACT READPREV -- unexpected CICS error | DISPLAY resp/reason codes, set error flag, message: `'Unable to lookup Transaction...'`, resend screen | WS-RESP-CD = OTHER | READPREV-TRANSACT-FILE lines 489-495 |
| TRANSACT WRITE -- duplicate key (`DFHRESP(DUPKEY)` or `DFHRESP(DUPREC)`) | Set error flag, message: `'Tran ID already exist...'`, cursor to account ID field, resend screen | WS-RESP-CD = DFHRESP(DUPKEY) or DFHRESP(DUPREC) | WRITE-TRANSACT-FILE lines 533-539 |
| TRANSACT WRITE -- unexpected CICS error | DISPLAY resp/reason codes, set error flag, message: `'Unable to Add Bill pay Transaction...'`, resend screen | WS-RESP-CD = OTHER | WRITE-TRANSACT-FILE lines 540-546 |
| RECEIVE-BILLPAY-SCREEN -- CICS error | RESP/RESP2 are captured but no explicit error handling is coded; a CICS exception on RECEIVE would propagate unhandled | WS-RESP-CD captured but not evaluated | RECEIVE-BILLPAY-SCREEN lines 308-314 |
| ENDBR-TRANSACT-FILE -- CICS error | No RESP clause on EXEC CICS ENDBR; any CICS error on ENDBR propagates as an unhandled exception | No RESP captured | ENDBR-TRANSACT-FILE lines 503-505 |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. MAIN-PARA -- entry point; checks EIBCALEN, loads commarea, dispatches by first-entry vs re-entry, then by EIBAID
2. RETURN-TO-PREV-SCREEN -- called when EIBCALEN = 0 (no session) or PF3 pressed; performs EXEC CICS XCTL to navigate away
3. PROCESS-ENTER-KEY -- called on DFHENTER or on first-entry with pre-selected account; contains all validation and payment logic
4. CLEAR-CURRENT-SCREEN -- called on PF4 or on confirmation 'N'; reinitialises fields then calls SEND-BILLPAY-SCREEN
5. RECEIVE-BILLPAY-SCREEN -- called at start of re-entry path; reads screen input into COBIL0AI (RESP/RESP2 captured but not evaluated)
6. SEND-BILLPAY-SCREEN -- calls POPULATE-HEADER-INFO then issues EXEC CICS SEND MAP with ERASE and CURSOR; called from multiple error paths and on success
7. POPULATE-HEADER-INFO -- fills title, transaction name, program name, date, and time into screen output area COBIL0AO using FUNCTION CURRENT-DATE
8. READ-ACCTDAT-FILE -- called from PROCESS-ENTER-KEY when CONFIRMI = 'Y'/'y' or SPACES/LOW-VALUES; reads ACCTDAT with UPDATE lock
9. READ-CXACAIX-FILE -- called only when CONF-PAY-YES is true (confirmation given); retrieves card number for the account
10. STARTBR-TRANSACT-FILE -- called only when CONF-PAY-YES; starts browse of TRANSACT from HIGH-VALUES
11. READPREV-TRANSACT-FILE -- reads backwards one record to find highest TRAN-ID
12. ENDBR-TRANSACT-FILE -- ends the browse immediately after one READPREV (no RESP clause, no error handling)
13. GET-CURRENT-TIMESTAMP -- uses EXEC CICS ASKTIME / FORMATTIME to build WS-TIMESTAMP
14. WRITE-TRANSACT-FILE -- writes new TRAN-RECORD; on success sets green success message and sends screen; on failure sets error flag and sends error screen
15. COMPUTE ACCT-CURR-BAL and UPDATE-ACCTDAT-FILE -- executed unconditionally after WRITE-TRANSACT-FILE returns, regardless of whether the write succeeded or failed (see Code Defect below)
16. INITIALIZE-ALL-FIELDS -- clears `ACTIDINI`, `CURBALI OF COBIL0AI`, `CONFIRMI`, and `WS-MESSAGE`; sets cursor to account ID field (`ACTIDINL = -1`)
17. EXEC CICS RETURN TRANSID('CB00') -- always executed at end of MAIN-PARA to keep the transaction alive for the next interaction

### Notable Data Integrity Pattern

The program uses a CICS READ with UPDATE on ACCTDAT (READ-ACCTDAT-FILE) before the REWRITE in UPDATE-ACCTDAT-FILE. CICS holds the record lock between the READ UPDATE and the REWRITE within the same task, preventing concurrent modification. However, there is no explicit SYNCPOINT issued; the commit occurs implicitly when EXEC CICS RETURN is executed at the end of MAIN-PARA. This means if WRITE-TRANSACT-FILE succeeds but UPDATE-ACCTDAT-FILE fails, the transaction record will exist in TRANSACT but the account balance will not be reduced -- a partial-update risk that is not explicitly handled.

### Code Defect: First Payment on Empty TRANSACT File

When the TRANSACT file contains no records, EXEC CICS STARTBR with RIDFLD(HIGH-VALUES) returns DFHRESP(NOTFND). The program treats this as an error, sets ERR-FLG-ON, and displays 'Transaction ID NOT found...' without processing the payment. The READPREV ENDFILE branch -- which was intended to seed the first transaction ID as 1 -- is never reached because STARTBR fails first. As a result the program cannot write the first-ever bill payment transaction to an empty file.

### Code Defect: Account Balance Reduced Even When Transaction Write Fails

In PROCESS-ENTER-KEY, the sequence at lines 233-235 is:

```
PERFORM WRITE-TRANSACT-FILE
COMPUTE ACCT-CURR-BAL = ACCT-CURR-BAL - TRAN-AMT
PERFORM UPDATE-ACCTDAT-FILE
```

WRITE-TRANSACT-FILE sets WS-ERR-FLG = 'Y' on DUPKEY, DUPREC, or any unexpected error, but the calling code does NOT check ERR-FLG-ON before executing the COMPUTE and UPDATE-ACCTDAT-FILE PERFORM. As a result, if the WRITE fails (e.g., duplicate transaction ID), the CICS REWRITE is still issued, reducing the account balance to zero in ACCTDAT despite no transaction record being written. This can produce an account balance of zero with no corresponding payment transaction -- a data integrity defect.

Additionally, when the write fails, WRITE-TRANSACT-FILE sends the error screen internally (lines 539 or 546), and then PROCESS-ENTER-KEY falls through to the unconditional `PERFORM SEND-BILLPAY-SCREEN` at line 242, sending the screen a second time in the same task.
