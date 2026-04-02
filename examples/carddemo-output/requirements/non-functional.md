---
type: requirements
subtype: non-functional
status: draft
confidence: high
last_pass: 5
---

# Non-Functional Requirements

Derived non-functional requirements observed in the COBOL source code.

## Error Handling

| Program        | Pattern                          | Approach              | Evidence              |
| -------------- | -------------------------------- | --------------------- | --------------------- |
| CBTRN02C | FILE STATUS checks on all six files | ABEND via CEE3ABD (code 999) for I/O errors; graceful reject record for business validation failures | 9999-ABEND-PROGRAM calls CALL 'CEE3ABD'; reject path writes to DALYREJS with reason codes 100-103 |
| CBACT04C | FILE STATUS checks on all five files | ABEND via CEE3ABD (code 999) for all I/O failures including record-not-found on account and xref | 9999-ABEND-PROGRAM; INVALID KEY on ACCOUNT-FILE and XREF-FILE both result in APPL-RESULT=12 and abend |
| CBSTM03A | FILE STATUS / CALL parameter checks | ABEND via CEE3ABD; abend paragraph is 9999-GOBACK with CALL 'CEE3ABD' | 9999-GOBACK paragraph |
| CBEXPORT | FILE STATUS checks | ABEND via CEE3ABD (called without USING) | 9999-ABEND-PROGRAM; CALL 'CEE3ABD' without USING |
| CBIMPORT | FILE STATUS checks | ABEND via CEE3ABD (called without USING) | 9999-ABEND-PROGRAM; CALL 'CEE3ABD' without USING |
| CBTRN01C | FILE STATUS checks | ABEND via CEE3ABD | CALL 'CEE3ABD' USING ABCODE, TIMING |
| CBACT01C | FILE STATUS checks | ABEND via CEE3ABD; also calls COBDATFT for date errors | CALL 'CEE3ABD'; CALL 'COBDATFT' USING CODATECN-REC |
| CBACT02C | FILE STATUS checks | ABEND via CEE3ABD | CALL 'CEE3ABD' USING ABCODE, TIMING |
| CBACT03C | FILE STATUS checks | ABEND via CEE3ABD | CALL 'CEE3ABD' USING ABCODE, TIMING |
| COSGN00C | CICS RESP code checks (WS-RESP-CD) | Graceful: all errors displayed as user-facing messages; no ABEND | HANDLE CONDITION / RESP evaluation; re-display signon screen on RESP=13 (NOTFND) or other errors |
| COACTUPC | CICS HANDLE ABEND + RESP code checks | Graceful for known errors; CICS abend trapped at program entry via EXEC CICS HANDLE ABEND LABEL(ABEND-ROUTINE) | 0000-MAIN lines 12-14; DFHRESP comparisons; ERR-FLG mechanism; unexpected state in 2000-DECIDE-ACTION triggers ABEND-ROUTINE with code '0001' |
| COACTVWC | CICS RESP code checks | Graceful: errors displayed on-screen | DFHRESP comparisons |
| COBIL00C | CICS RESP code checks | Graceful: errors displayed on-screen for most CICS operations; RECEIVE screen RESP captured but not evaluated | DFHRESP comparisons on ACCTDAT, TRANSACT, CXACAIX reads; RECEIVE-BILLPAY-SCREEN does not evaluate WS-RESP-CD |
| COBIL00C | ENDBR without RESP clause | Silent: EXEC CICS ENDBR has no RESP clause; any CICS exception on ENDBR propagates unhandled | ENDBR-TRANSACT-FILE lines 503-505 |
| COCRDLIC | CICS RESP code checks | Graceful: errors displayed on-screen | DFHRESP on CARDXREF browse |
| COCRDSLC | CICS RESP code checks | Graceful: errors displayed on-screen | DFHRESP comparisons |
| COCRDUPC | CICS RESP code checks | Graceful: errors displayed on-screen | DFHRESP comparisons |
| COTRN02C | CICS RESP code checks + CALL CSUTLDTC | Graceful: field-level validation errors shown on-screen; date validation via CSUTLDTC/CEEDAYS | DFHRESP; CSUTLDTC returns date validity flag |
| COUSR01C | CICS RESP code checks | Graceful: duplicate key detected (RESP=DUPREC), displayed as user message | DFHRESP on USRSEC WRITE |
| COUSR01C | CICS RECEIVE MAP — RESP not checked | Silent: EXEC CICS RECEIVE RESP captured in WS-RESP-CD/WS-REAS-CD but never evaluated; BMS receive failures silently ignored; processing continues with stale/partial COUSR1AI data | RECEIVE-USRADD-SCREEN lines 203-209 |
| COUSR02C | CICS RESP code checks | Graceful: READ/REWRITE errors displayed; however PF3 navigates away even when UPDATE-USER-INFO sets ERR-FLG-ON | DFHRESP comparisons; MAIN-PARA lines 111-119: UPDATE-USER-INFO called, then unconditional XCTL on PF3 regardless of ERR-FLG state |
| COUSR02C | CICS RECEIVE MAP — RESP not checked | Silent: EXEC CICS RECEIVE RESP stored in WS-RESP-CD/WS-REAS-CD but never evaluated; BMS receive failures silently ignored | RECEIVE-USRUPD-SCREEN lines 285-291 |
| COUSR03C | CICS RESP code checks | Graceful: READ/DELETE errors displayed; but DELETE issued even when prior READ fails | READ-USER-SEC-FILE NOTFND/OTHER sets ERR-FLG-ON but DELETE-USER-SEC-FILE still called (single IF block at lines 188-192); DELETE NOTFND response then handled gracefully |
| COUSR03C | CICS RECEIVE MAP — RESP not checked | Silent: EXEC CICS RECEIVE response codes stored but never evaluated; stale map input processed silently on receive failure | RECEIVE-USRDEL-SCREEN lines 232-238 |
| CORPT00C | CICS RESP code checks | Graceful: date validation via CSUTLDTC; TDQ write errors displayed | DFHRESP on WRITEQ TD |
| CBTRN02C | Account REWRITE INVALID KEY | Silent data loss (defect): reason code 109 set but no reject written and no abend | 2800-UPDATE-ACCOUNT-REC lines 554-558; WS-VALIDATION-FAIL-REASON=109 but no subsequent action |
| COBIL00C | Account balance update after failed TRANSACT write | Silent data integrity defect: COMPUTE ACCT-CURR-BAL and UPDATE-ACCTDAT-FILE execute unconditionally after WRITE-TRANSACT-FILE, regardless of whether the write succeeded | PROCESS-ENTER-KEY lines 233-235; ERR-FLG-ON is not checked before the COMPUTE and PERFORM UPDATE-ACCTDAT-FILE |
| COBIL00C | First payment on empty TRANSACT | Logic defect: STARTBR NOTFND on empty TRANSACT sets ERR-FLG-ON and aborts payment; the READPREV ENDFILE seed path (intended to initialise transaction ID = 1) is never reached | STARTBR-TRANSACT-FILE lines 454-459 |
| COSGN00C | CICS RECEIVE error | Silently ignored: WS-RESP-CD from RECEIVE is overwritten by the subsequent READ RESP | PROCESS-ENTER-KEY lines ~110-115 |
| CSUTLDTC | Post-call VString overwrite corrupts date echo | Defect: MOVE WS-DATE-TO-TEST TO WS-DATE at line 122 moves the entire VString group (binary 2-byte length prefix + text) into a PIC X(10) field, corrupting bytes 1-2 of WS-DATE with binary data | A000-MAIN line 122; callers CORPT00C and COTRN02C are unaffected because they do not parse the TstDate sub-field of LS-RESULT, but future callers reading the date echo will receive garbled data |
| COBSWAIT | SYSIN value — no validation | Silent: non-numeric SYSIN causes undefined or zero wait; missing SYSIN produces spaces and undefined result; no error path coded | PROCEDURE DIVISION: ACCEPT then MOVE with no IF; no ON EXCEPTION on CALL 'MVSWAIT' |

## Data Integrity

| Program        | Pattern                          | Mechanism             | Evidence              |
| -------------- | -------------------------------- | --------------------- | --------------------- |
| COBIL00C | CICS READ UPDATE / REWRITE | Optimistic CICS file lock held between READ UPDATE and REWRITE on ACCTDAT; no SYNCPOINT; commit occurs implicitly on CICS RETURN | EXEC CICS READ UPDATE DATASET('ACCTDAT'); EXEC CICS REWRITE; EXEC CICS RETURN at end of MAIN-PARA |
| COBIL00C | TRANSACT WRITE then unconditional balance update | Defect: account balance reduced to zero even if TRANSACT WRITE fails (DUPKEY or other error); produces zero-balance account with no payment record | PROCESS-ENTER-KEY lines 233-235; no ERR-FLG check between WRITE and COMPUTE/UPDATE |
| COACTUPC | CICS READ UPDATE / REWRITE with compare-before-write and concurrent modification detection | CICS file locking on ACCTDAT and CUSTDAT before rewrite; 29-field old-vs-new comparison; concurrent modification detected by compare of stored vs fetched data; state machine (ACUP-CHANGE-ACTION) gates PF5 confirmation; SYNCPOINT issued on PF3 exit | EXEC CICS READ UPDATE on both ACCTDAT and CUSTDAT; 1205-COMPARE-OLD-NEW paragraph; 2000-DECIDE-ACTION DATA-WAS-CHANGED-BEFORE-UPDATE state; 0000-MAIN PF3 branch EXEC CICS SYNCPOINT |
| COACTUPC | Partial-update risk on dual VSAM write | ACCTDAT REWRITE and CUSTDAT REWRITE are sequential with no spanning SYNCPOINT between them; if ACCTDAT write succeeds but CUSTDAT write fails the account and customer records are inconsistent | 9600-WRITE-PROCESSING: REWRITE ACCTDAT then REWRITE CUSTDAT; only one SYNCPOINT on PF3 exit, not between writes |
| COUSR02C | CICS READ UPDATE / REWRITE with compare-before-write | READ UPDATE locks record; all four editable fields compared to stored values; REWRITE issued only when at least one field changed; no-change guard prevents unnecessary writes | UPDATE-USER-INFO lines 215-243; USR-MODIFIED flag set per field; REWRITE guarded by USR-MODIFIED-YES |
| COUSR03C | Position-based DELETE after READ UPDATE | DELETE issued without RIDFLD, relying on file position set by prior READ UPDATE; if READ fails, DELETE is still called on same task file position — CICS returns NOTFND/INVREQ, no data is corrupted | DELETE-USER-SEC-FILE lines 307-311; single IF block at DELETE-USER-INFO lines 188-192 does not re-check ERR-FLG after READ |
| CBTRN02C | No transaction boundary | TRANSACT-FILE, TCATBALF, and ACCOUNT-FILE are updated sequentially without a commit point; a failure after account update but before transaction write leaves data inconsistent | Open OUTPUT (destructive) on TRANSACT-FILE; no SYNCPOINT or checkpoint between 2700, 2800, 2900 |
| CBACT04C | No explicit locking | ACCOUNT-FILE is READ (not READ UPDATE) then held in memory across many TCATBAL records before REWRITE; concurrent access could cause lost update | READ FD-ACCTFILE-REC (not READ ... UPDATE); REWRITE occurs much later at account boundary |
| CBTRN02C | TRANSACT-FILE destructive open | OPEN OUTPUT on TRANSACT-FILE at job start truncates the file; a mid-job abend leaves TRANSACT empty | 0100-TRANFILE-OPEN OPEN OUTPUT TRANSACT-FILE |
| CBTRN02C | DALYREJS-FILE destructive open | OPEN OUTPUT on DALYREJS-FILE at job start; prior run rejects are destroyed | 0300-DALYREJS-OPEN OPEN OUTPUT DALYREJS-FILE |
| COTRN02C | Transaction ID generation race | Next transaction ID derived from a backwards browse; concurrent online adds could generate duplicate IDs | EXEC CICS STARTBR / READPREV to find max ID; no locking during generation |
| COBIL00C | Transaction ID generation race | Same backwards-browse pattern for ID generation; shared with COTRN02C on same TRANSACT file | EXEC CICS STARTBR / READPREV on TRANSACT |
| CBTRN02C | Category balance create-or-update | Read-then-write on TCATBALF (with create on INVALID KEY) is protected by the sequential batch model; no concurrent online writes to TCATBALF | Batch-only file; CICS programs do not write TCATBALF |
| CBSTM03A | Read-only batch | All file access is read-only through CBSTM03B; no integrity risk | CBSTM03B parameters include only read operations |
| CBTRN02C | Missing account ID in TRAN-RECORD | TRAN-RECORD (CVTRA05Y) has no TRAN-ACCT-ID field; account linkage in TRANSACT requires re-join via XREF using TRAN-CARD-NUM at query time | CVTRA05Y copybook; TRAN-ACCT-ID field is absent from the layout |

## Performance

| Program        | Pattern                          | Indicator             | Evidence              |
| -------------- | -------------------------------- | --------------------- | --------------------- |
| CBTRN02C | Sequential read of DALYTRAN | Entire daily transaction file processed in one pass | PERFORM UNTIL END-OF-FILE on DALYTRAN-FILE |
| CBACT04C | Sequential read of TCATBALF + random lookups | N reads of TCATBALF; per-account random reads of ACCOUNT-FILE, XREF-FILE, DISCGRP-FILE; no buffering hint | Sequential read drives main loop; random I/O per account boundary |
| CBACT04C | Unconditional DISPLAY every record | High-volume SYSOUT output; potential performance impact on large files | Line 193: unconditional DISPLAY TRAN-CAT-BAL-RECORD with no guard |
| CBSTM03A | In-memory transaction array | CBSTM03A loads transactions into a two-dimensional COMP array; array bounds limit the number of transactions per card per statement | WS-TRNX-ARRAY (COMP variables); statement generation depends on JCL pre-sort |
| CREASTMT JCL | SORT step (STEP010) | TRANSACT VSAM is sorted by card number + transaction ID before CBSTM03A runs; sort volume proportional to total transaction count | CREASTMT.JCL STEP010: SORT on TRANSACT.VSAM.KSDS |
| TRANREPT JCL | Multiple SORT and REPROC steps | 3-step pipeline: unload, filter+sort, report; each step processes the full or filtered transaction dataset | TRANREPT.jcl STEP05R (REPROC), SORT, STEP10R (CBTRN03C) |
| COMBTRAN JCL | SORT merge of backup and system transactions | Merges TRANSACT.BKUP GDG and SYSTRAN GDG before reloading to VSAM | COMBTRAN.jcl STEP05R SORT with two SORTINnn inputs |
| COBSWAIT | Configurable wait via SYSIN | JCL batch sequencing delay in centiseconds | COBSWAIT reads SYSIN for wait duration; passes to MVS MVSWAIT service |
| CBSTM03A | No checkpoint logic | Long-running statement generation with no restart capability; abend requires full re-run | No SYNCPOINT or checkpoint paragraphs |
| CBTRN02C | No checkpoint logic | Long-running transaction posting with no intermediate commit | No SYNCPOINT; all changes held in VSAM buffers until normal end |
| COCRDLIC | CICS browse with paging | Card list screen pages through CARDXREF/CARDAIX using CICS STARTBR/READNEXT; page size constrained by BMS map display capacity | EXEC CICS STARTBR / READNEXT on CARDAIX or CXACAIX |
| COTRN00C | CICS browse with paging | Transaction list pages through TRANSACT using STARTBR/READNEXT; high-volume TRANSACT file may produce slow initial page load | EXEC CICS STARTBR / READNEXT on TRANSACT VSAM |
| COACTUPC | 29-field compare-before-write | OLD vs NEW comparison of all editable account and customer fields before issuing REWRITE; prevents unnecessary I/O when no change has occurred | 1205-COMPARE-OLD-NEW paragraph; REWRITE only issued when CHANGE-HAS-OCCURRED is true |
| COUSR02C | Double or triple BMS SEND on normal path | On PF5 or first-entry, READ-USER-SEC-FILE unconditionally sends the screen with a prompt message; subsequent logic in UPDATE-USER-INFO or PROCESS-ENTER-KEY sends the screen again with the final message; the intermediate send is overwritten by the final ERASE, but represents unnecessary BMS I/O | READ-USER-SEC-FILE lines 335-338 (unconditional SEND on NORMAL); MAIN-PARA line 105 (unconditional SEND after PROCESS-ENTER-KEY) |
| COUSR03C | Redundant BMS SEND on ENTER key | READ-USER-SEC-FILE sends screen with blank name fields, then PROCESS-ENTER-KEY populates fields and sends again; only the second is visible | READ-USER-SEC-FILE lines 282-286; PROCESS-ENTER-KEY lines 164-169 |
| COUSR03C | Unnecessary READ UPDATE on ENTER key | ENTER key for display purposes acquires an UPDATE lock on USRSEC; lock released on CICS RETURN; re-acquired on PF5 (correct lock sequence) but the ENTER lock is unneeded overhead for a read-only display | READ-USER-SEC-FILE uses CICS READ ... UPDATE for both display (ENTER) and delete (PF5) paths |

## Security

| Program        | Pattern                          | Mechanism             | Evidence              |
| -------------- | -------------------------------- | --------------------- | --------------------- |
| COSGN00C | Username/password authentication | Compares SEC-USR-PWD (8 bytes) from USRSEC against terminal-entered password (UPPER-CASE normalized) | READ USRSEC by WS-USER-ID; compare SEC-USR-PWD = WS-USER-PWD |
| COSGN00C | Role-based routing | User type 'A' → COADM01C; all other types → COMEN01C | CDEMO-USRTYP-ADMIN 88 VALUE 'A'; CICS XCTL based on user type |
| COSGN00C | No account lockout | No failed-attempt counter or lockout policy detected | No WS-FAIL-COUNT or similar field in COSGN00C or CSUSR01Y |
| COSGN00C | Password stored in plaintext | SEC-USR-PWD is PIC X(08) in USRSEC; no encryption or hashing evidence | CSUSR01Y copybook; comparison is direct character equality |
| COBIL00C | Session validation | On cold start (EIBCALEN=0), control is transferred to COSGN00C; prevents unauthenticated access | EXEC CICS XCTL PROGRAM('COSGN00C') when EIBCALEN=0 |
| COTRN02C | Session validation | Cold start redirects to COSGN00C | EXEC CICS XCTL PROGRAM('COSGN00C') when EIBCALEN=0 |
| COUSR01C | Session validation | Cold start redirects to COSGN00C | EXEC CICS XCTL to COSGN00C when EIBCALEN=0 |
| COUSR02C | Session validation | Cold start redirects to COSGN00C | EXEC CICS XCTL PROGRAM('COSGN00C') when EIBCALEN=0 (MAIN-PARA lines 90-92) |
| COUSR03C | Session validation | Cold start redirects to COSGN00C | EXEC CICS XCTL PROGRAM('COSGN00C') when EIBCALEN=0 (MAIN-PARA lines 90-92) |
| COADM01C | Admin-only access | Admin menu (CA00) is only reachable from COSGN00C after 'A'-type user authentication | COSGN00C XCTL to COADM01C only when CDEMO-USRTYP-ADMIN; no menu entry from COMEN01C |
| COCRDLIC | Role-based card filtering | Admin users see all cards; regular users see only cards linked to the account in COMMAREA | COMMAREA CDEMO-USER-TYPE check; admin bypasses account filter |
| All online programs | Authorization check via COMMAREA | User type and user ID are propagated in CARDDEMO-COMMAREA (COCOM01Y) throughout the session | CDEMO-USER-ID, CDEMO-USER-TYPE fields carried in all XCTL transfers |
| All programs | No field-level encryption | Customer SSN (CUST-SSN PIC 9(09)), card number (PIC X(16)), and password (PIC X(08)) are stored and transmitted as plain DISPLAY characters | CVCUS01Y, CVACT02Y, CSUSR01Y copybooks |
| All online programs | No CICS RACF or external authorization check | Authorization relies solely on COMMAREA user type; no EXEC CICS QUERY SECURITY or ESM call is present | No EXEC CICS QUERY SECURITY in any online program source |
| COACTUPC | SSN validation rules enforced at data entry | Parts 1-3 of SSN validated for format, range (000/666/900-999 rejected for part 1), and non-zero; FICO score range enforced (300-850); state code validated against lookup table; state/zip cross-validated | 1265-EDIT-US-SSN, 1275-EDIT-FICO-SCORE, 1270-EDIT-US-STATE-CD, 1280-EDIT-US-STATE-ZIP-CD |
| COUSR01C | User type not validated at input | User Type field is accepted as any non-blank single character; no 88-level constraint enforces 'A' or 'U' at entry time | PROCESS-ENTER-KEY lines 142-147: only blank/LOW-VALUES check; no domain validation |

## Audit and Logging

| Program        | Pattern                          | Mechanism             | Evidence              |
| -------------- | -------------------------------- | --------------------- | --------------------- |
| CBACT04C | DISPLAY every TCATBAL record | Unconditional SYSOUT logging of every processed record; no guard condition | Line 193: DISPLAY TRAN-CAT-BAL-RECORD without IF |
| CBACT04C | DISPLAY program start/end | Bracketing DISPLAYs at program entry and exit | Inline DISPLAY 'START OF EXECUTION OF PROGRAM CBACT04C'; DISPLAY 'END OF EXECUTION...' |
| CBTRN02C | Transaction and reject counters displayed | End-of-job summary: WS-TRANSACTION-COUNT and WS-REJECT-COUNT to SYSOUT | Main loop lines 226-228: DISPLAY counts |
| CBTRN02C | Reject records with reason codes | Each rejected transaction written to DALYREJS with 4-digit reason code and 76-char description | 2500-WRITE-REJECT-REC; REJECT-TRAN-DATA + VALIDATION-TRAILER |
| CBTRN02C | Processing timestamp on each transaction | TRAN-PROC-TS set to FUNCTION CURRENT-DATE at post time for every transaction | Z-GET-DB2-FORMAT-TIMESTAMP paragraph; TRAN-PROC-TS = DB2-FORMAT-TS |
| CBACT04C | Transaction timestamps | TRAN-ORIG-TS and TRAN-PROC-TS both set to current system time for interest transactions | 1300-B-WRITE-TX: Z-GET-DB2-FORMAT-TIMESTAMP; both timestamps assigned |
| COTRN02C | Add-transaction timestamp | TRAN-PROC-TS set at time of online write | Z-GET-DB2-FORMAT-TIMESTAMP equivalent in COTRN02C |
| COBIL00C | Payment transaction timestamped | New TRANSACT record includes both TRAN-ORIG-TS and TRAN-PROC-TS from CICS ASKTIME/FORMATTIME at time of processing | GET-CURRENT-TIMESTAMP sets WS-TIMESTAMP used for both timestamp fields |
| COACTUPC | No audit trail for account updates | COACTUPC performs CICS REWRITE on ACCTDAT and CUSTDAT with no before-image or after-image written to an audit file; the 29-field compare detects what changed but does not persist that change log | No WRITE to audit dataset in 9600-WRITE-PROCESSING; change detection in 1205-COMPARE-OLD-NEW is transient only |
| COCRDUPC | No audit trail for card updates | COCRDUPC rewrites CARDDAT with no audit record | No WRITE to audit dataset in COCRDUPC procedure division |
| COUSR02C | No audit trail for user updates | COUSR02C performs CICS REWRITE on USRSEC with no before/after audit record; only a screen success message is shown | No WRITE to audit dataset in UPDATE-USER-SEC-FILE; no logging of who changed which user record |
| COUSR03C | No audit trail for user deletions | COUSR03C performs CICS DELETE on USRSEC with no audit record of the deleted user data | No WRITE to audit dataset in DELETE-USER-SEC-FILE |
| CBSTM03A | DISPLAY messages via CBSTM03B | CBSTM03A emits DISPLAY for file operations via CBSTM03B call returns | Parameter block return codes displayed on failure |
| All batch programs | SYSOUT and SYSPRINT DDs | All batch JCL includes SYSOUT and SYSPRINT for DISPLAY and file status output | JCL job steps include SYSOUT=* and SYSPRINT=* DD statements |
| All online programs | Header with APPLID, SYSID, date, time | Every BMS screen shows APPLID, SYSID, current date and time via EXEC CICS ASSIGN | POPULATE-HEADER-INFO paragraph (common pattern); CSDAT01Y date fields |

## Recovery

| Program        | Pattern                          | Mechanism             | Evidence              |
| -------------- | -------------------------------- | --------------------- | --------------------- |
| CBTRN02C | No checkpoint / restart logic | A mid-job abend requires full re-run from scratch; TRANSACT-FILE was already truncated at job start | OPEN OUTPUT (destructive) on TRANSACT-FILE; no WS-RESTART-POSITION or SYNCPOINT |
| CBACT04C | No checkpoint / restart logic | Long-running interest calculation with no intermediate recovery point | No SYNCPOINT or checkpoint counter |
| CBSTM03A | No checkpoint / restart logic | Statement generation is all-or-nothing; restart requires full re-run including all CREASTMT JCL pre-steps | No SYNCPOINT; CREASTMT JCL pre-steps must also be re-run |
| CBTRN02C | JCL RETURN-CODE=4 on partial success | JES can test COND=(4,LT) on subsequent steps to detect partial failure | MOVE 4 TO RETURN-CODE when WS-REJECT-COUNT > 0 |
| CBTRN02C | DALYREJS GDG captures rejects | Rejected transactions preserved for manual review and re-submission | GDG dataset DALYREJS(+1) created each run |
| COMBTRAN JCL | Combine daily and system transactions | Merges SYSTRAN (interest) with TRANSACT backup before reloading to VSAM | COMBTRAN.jcl: merge TRANSACT.BKUP + SYSTRAN into TRANSACT.COMBINED, then REPRO to VSAM |
| TRANBKP JCL | Transaction VSAM backup | TRANBKP job unloads TRANSACT VSAM to sequential GDG backup before destructive operations | TRANBKP.jcl: IDCAMS REPRO of TRANSACT to TRANSACT.BKUP GDG |
| CBIMPORT | ERROUT file for import errors | CBIMPORT writes malformed or unrecognisable records to ERROUT for review | SELECT ERROUT ASSIGN TO ... in CBIMPORT.cbl; written on parse errors |
| COBSWAIT | Batch sequencing delay | WAITSTEP job provides configurable pause between job steps where timing is critical | COBSWAIT reads centisecond delay from SYSIN; calls MVSWAIT |
| All batch programs | CEE3ABD on hard errors | Hard I/O errors invoke LE abend handler; abend code 999 triggers MVS dump | CALL 'CEE3ABD' USING ABCODE (=999), TIMING (=0) in all batch programs |
| COBIL00C | No recovery path after partial payment write failure | If TRANSACT WRITE fails, account balance is still reduced to zero with no corresponding transaction record; no rollback mechanism exists | PROCESS-ENTER-KEY lines 233-235; no conditional guard before UPDATE-ACCTDAT-FILE |
| COACTUPC | SYNCPOINT on PF3 exit | CICS SYNCPOINT issued when the user navigates away (PF3), ensuring all CICS-managed resources are committed or rolled back before the task terminates | 0000-MAIN PF3 branch: EXEC CICS SYNCPOINT before EXEC CICS XCTL |
