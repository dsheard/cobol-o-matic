---
type: business-rules
program: XFRFUN
program_type: online
status: draft
confidence: high
last_pass: 5
calls:
- ABNDPROC
called_by:
- BNK1TFN
uses_copybooks:
- ABNDINFO
- ACCDB2
- ACCOUNT
- PROCDB2
- PROCTRAN
- SORTCODE
- XFRFUN
reads: []
writes: []
db_tables:
- ACCOUNT
- PROCTRAN
transactions: []
mq_queues: []
---

# XFRFUN -- Business Rules

## Program Purpose

XFRFUN performs inter-account fund transfers on behalf of the CICS Banking Sample Application. It is called by BNK1TFN (the transfer UI program) and operates entirely through DB2. Given a FROM account (sort code + account number), a TO account (sort code + account number), and a transfer amount, the program:

1. Validates that the transfer amount is positive and that the FROM and TO accounts are not the same.
2. Selects and updates ACCOUNT rows for both the FROM account (debit) and the TO account (credit) in a deadlock-safe order (lower account number first).
3. Writes a processed-transaction record to PROCTRAN.
4. Returns updated available and actual balances for both accounts to the caller via COMMAREA.

No overdraft-limit checking is performed -- the program comment explicitly states "No checking is made on overdraft limits."

## Input / Output

| Direction | Resource  | Type | Description                                                                        |
| --------- | --------- | ---- | ---------------------------------------------------------------------------------- |
| IN        | DFHCOMMAREA (XFRFUN.cpy) | CICS COMMAREA | FROM account (COMM-FACCNO/COMM-FSCODE), TO account (COMM-TACCNO/COMM-TSCODE), transfer amount (COMM-AMT) |
| IN/OUT    | ACCOUNT   | DB2  | Account rows; selected for balance read, updated with new balances                 |
| OUT       | PROCTRAN  | DB2  | Processed-transaction record inserted for the transfer                             |
| OUT       | DFHCOMMAREA | CICS COMMAREA | Updated balances (COMM-FAVBAL, COMM-FACTBAL, COMM-TAVBAL, COMM-TACTBAL), COMM-SUCCESS flag, COMM-FAIL-CODE |

## Business Rules

### Validation

| #  | Rule                             | Condition                                                          | Action                                                                                    | Source Location |
| -- | -------------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- | --------------- |
| 1  | Transfer amount must be positive | `IF COMM-AMT <= ZERO`                                              | Set COMM-SUCCESS='N', COMM-FAIL-CODE='4', immediately return to caller (GET-ME-OUT-OF-HERE) | A010 (line 289) |
| 2  | FROM and TO accounts must differ | `IF COMM-FACCNO = COMM-TACCNO AND COMM-FSCODE = COMM-TSCODE`      | Populate ABNDINFO-REC, EXEC CICS LINK ABNDPROC, EXEC CICS ABEND ABCODE('SAME') NODUMP CANCEL | UAD010 (line 316) |
| 35 | Both accounts must be on the application's own sort code | A010 unconditionally MOVEs SORTCODE (from SORTCODE copybook) to both COMM-FSCODE and COMM-TSCODE at line 281, overwriting any values passed by the caller | Both DB2 SELECTs will use the application's own sort code regardless of input; transfers to/from external sort codes are silently redirected to the local bank and will fail with COMM-FAIL-CODE='1' or '2' if the account does not exist | A010 (line 281) |

### Deadlock-Safe Update Ordering

| #  | Rule                                            | Condition                          | Action                                                                                                           | Source Location  |
| -- | ----------------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ---------------- |
| 3  | Lower account number updated first to prevent deadlocks | `IF COMM-FACCNO < COMM-TACCNO`     | PERFORM UPDATE-ACCOUNT-DB2-FROM first, then (if COMM-SUCCESS='Y') PERFORM UPDATE-ACCOUNT-DB2-TO                  | UAD010 (line 378) |
| 4  | Higher TO account number: reverse the order     | `ELSE` (COMM-FACCNO >= COMM-TACCNO) | PERFORM UPDATE-ACCOUNT-DB2-TO first, then (if COMM-SUCCESS='Y') PERFORM UPDATE-ACCOUNT-DB2-FROM                  | UAD010 (line 589) |

### FROM Account Update (UPDATE-ACCOUNT-DB2-FROM)

| #  | Rule                                                   | Condition                          | Action                                                                                       | Source Location    |
| -- | ------------------------------------------------------ | ---------------------------------- | -------------------------------------------------------------------------------------------- | ------------------ |
| 5  | FROM account must exist in ACCOUNT table               | `IF SQLCODE NOT = 0` after SELECT  | Set COMM-SUCCESS='N'; if SQLCODE=+100 set COMM-FAIL-CODE='1', else COMM-FAIL-CODE='3'; PERFORM CHECK-FOR-STORM-DRAIN-DB2; GO TO UADF999 | UADF010 (line 964) |
| 6  | FROM account UPDATE must succeed                       | `IF SQLCODE NOT = 0` after UPDATE  | Set COMM-SUCCESS='N', COMM-FAIL-CODE='3'; PERFORM CHECK-FOR-STORM-DRAIN-DB2; GO TO UADF999 | UADF010 (line 1014) |
| 7  | Successful FROM update stores balances in COMMAREA     | After successful UPDATE             | MOVE HV-ACCOUNT-AVAIL-BAL TO COMM-FAVBAL; MOVE HV-ACCOUNT-ACTUAL-BAL TO COMM-FACTBAL; COMM-SUCCESS='Y' | UADF010 (line 1033) |

### TO Account Update (UPDATE-ACCOUNT-DB2-TO)

| #  | Rule                                                    | Condition                               | Action                                                                                                          | Source Location     |
| -- | ------------------------------------------------------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------- |
| 8  | TO account not found triggers rollback                  | `IF SQLCODE = +100` after SELECT         | Set COMM-FAIL-CODE='2'; DISPLAY diagnostic; EXEC CICS SYNCPOINT ROLLBACK; GO TO UADT999. If ROLLBACK itself fails (CICS RESP <> NORMAL): LINK ABNDPROC; EXEC CICS ABEND ABCODE('HROL') | UADT010 (lines 1102, 1116) |
| 9  | TO account SELECT fails for non-not-found reason        | `ELSE` (SQLCODE <> 0 and <> +100)        | Set COMM-FAIL-CODE='3'; check for DB2 deadlock (-911 / SQLERRD(3)=13172872); if retry < 6: rollback, delay 1 second, GO TO UPDATE-ACCOUNT-DB2; else ABEND('RUF2') | UADT010 (line 1188) |
| 10 | DB2 deadlock (-911, SQLERRD(3)=13172872) on TO SELECT: retry up to 5 times | `IF SQLCODE = -911 AND SQLERRD(3) = 13172872 AND DB2-DEADLOCK-RETRY < 6` | ADD 1 TO DB2-DEADLOCK-RETRY; SYNCPOINT ROLLBACK; EXEC CICS DELAY FOR SECONDS(1); GO TO UPDATE-ACCOUNT-DB2 | UADT010 (line 1197) |
| 11 | DB2 timeout detected (SQLERRD(3)=13172894) on TO SELECT | `IF SQLERRD(3) = 13172894`              | DISPLAY 'TIMEOUT DETECTED!'; populate ABNDINFO-REC with 'RUF2'; LINK ABNDPROC; EXEC CICS ABEND ABCODE('RUF2')   | UADT010 (line 1288) |
| 12 | TO account UPDATE fails (any SQLCODE <> 0)              | `IF SQLCODE NOT = 0` after UPDATE        | DISPLAY diagnostic; PERFORM CHECK-FOR-STORM-DRAIN-DB2; if deadlock and retry < 6: SYNCPOINT ROLLBACK, DELAY 1s, GO TO UPDATE-ACCOUNT-DB2; else LINK ABNDPROC; EXEC CICS ABEND ABCODE('RUF3') | UADT010 (line 1384) |
| 13 | DB2 deadlock (-911, SQLERRD(3)=13172872) on TO UPDATE: retry up to 5 times | `IF SQLCODE = -911 AND SQLERRD(3) = 13172872 AND DB2-DEADLOCK-RETRY < 6` | ADD 1 TO DB2-DEADLOCK-RETRY; SYNCPOINT ROLLBACK; DELAY 1 second; GO TO UPDATE-ACCOUNT-DB2 | UADT010 (line 1397) |
| 14 | Successful TO update stores balances in COMMAREA        | After successful UPDATE                  | MOVE HV-ACCOUNT-AVAIL-BAL TO COMM-TAVBAL; MOVE HV-ACCOUNT-ACTUAL-BAL TO COMM-TACTBAL; COMM-SUCCESS='Y'          | UADT010 (line 1554) |
| 36 | UADT010 resets COMM-SUCCESS='N' on entry regardless of prior state | MOVE 'N' TO COMM-SUCCESS at line 1044 | When called as the second sub-paragraph (reverse-order path: FROM updated first, then TO), UADT010 resets COMM-SUCCESS to 'N' before doing its own work; COMM-SUCCESS='Y' is only restored after its own successful UPDATE at line 1554 | UADT010 (line 1044) |
| 37 | Storm drain check fires before SQLCODE discrimination in UADT010 SELECT failure path | PERFORM CHECK-FOR-STORM-DRAIN-DB2 at line 1097, before IF SQLCODE = +100 at line 1102 | CHECK-FOR-STORM-DRAIN-DB2 is called for all non-zero SQLCODEs including +100 (not found); since CFSDD010 only triggers display for SQLCODE=923, this has no side-effect for +100 but confirms storm drain logging always precedes routing decisions in UADT010 | UADT010 (line 1097) |

### Rollback Rules in UPDATE-ACCOUNT-DB2 (UAD010)

| #  | Rule                                                                        | Condition                                                   | Action                                                                 | Source Location   |
| -- | --------------------------------------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------------------- | ----------------- |
| 15 | FROM update fails (FAIL-CODE='1'): roll back, return to caller              | `IF COMM-FAIL-CODE = '1'` (FACCNO < TACCNO path)           | EXEC CICS SYNCPOINT ROLLBACK; if ROLLBACK fails (CICS RESP <> NORMAL): DISPLAY then EXEC CICS ABEND ABCODE('HROL') NODUMP (no LINK ABNDPROC); otherwise GO TO UAD999 | UAD010 (lines 501, 512) |
| 16 | FROM update fails with unexpected code: abend                               | `ELSE` (FAIL-CODE not '1', FACCNO < TACCNO path)           | LINK ABNDPROC; EXEC CICS ABEND ABCODE('FROM') NODUMP CANCEL            | UAD010 (line 527) |
| 17 | TO update fails (FAIL-CODE='2'): roll back, return to caller                | `IF COMM-FAIL-CODE = '2'` (FACCNO < TACCNO path)           | EXEC CICS SYNCPOINT ROLLBACK; if ROLLBACK fails: LINK ABNDPROC; EXEC CICS ABEND ABCODE('HROL') NODUMP CANCEL; otherwise GO TO UAD999 | UAD010 (lines 406, 413) |
| 18 | TO update fails with unexpected code: abend (no ABNDPROC call)              | `ELSE` (FAIL-CODE not '2', FACCNO < TACCNO path)           | DISPLAY 'Error updating TO account'; EXEC CICS ABEND ABCODE('TO  ') NODUMP. NOTE: no LINK ABNDPROC / ABNDINFO population before this abend, unlike Rules 16, 20, 21 | UAD010 (line 486) |
| 19 | FROM update fails (FAIL-CODE='1') in reverse-order path: roll back          | `ELSE` (FAIL-CODE IS '1', FACCNO >= TACCNO path)           | EXEC CICS SYNCPOINT ROLLBACK; if ROLLBACK fails: LINK ABNDPROC; EXEC CICS ABEND ABCODE('HROL') NODUMP CANCEL; otherwise GO TO UAD999 | UAD010 (lines 679, 687) |
| 20 | FROM update fails with unexpected code in reverse path: abend               | `IF COMM-FAIL-CODE NOT = '1'` (FACCNO >= TACCNO path)     | LINK ABNDPROC; EXEC CICS ABEND ABCODE('FROM') NODUMP CANCEL            | UAD010 (line 624) |
| 21 | TO update fails (FAIL-CODE NOT='2') in reverse-order path: abend            | `IF COMM-FAIL-CODE NOT = '2'` (FACCNO >= TACCNO path)      | LINK ABNDPROC; EXEC CICS ABEND ABCODE('TO  ') CANCEL NODUMP            | UAD010 (line 766) |
| 22 | TO update fails (FAIL-CODE='2') in reverse-order path: roll back            | `ELSE` (FAIL-CODE IS '2', FACCNO >= TACCNO path)           | EXEC CICS SYNCPOINT ROLLBACK; if ROLLBACK fails: LINK ABNDPROC; EXEC CICS ABEND ABCODE('HROL') NODUMP CANCEL; otherwise GO TO UAD999 | UAD010 (lines 826, 832) |

### PROCTRAN Write

| #  | Rule                                                              | Condition                    | Action                                                                                    | Source Location   |
| -- | ----------------------------------------------------------------- | ---------------------------- | ----------------------------------------------------------------------------------------- | ----------------- |
| 23 | PROCTRAN record is written only after both account updates succeed | After both succeed (falls through to PERFORM past all IF blocks) | PERFORM WRITE-TO-PROCTRAN (calls WRITE-TO-PROCTRAN-DB2); MOVE 'Y' TO COMM-SUCCESS | UAD010 (line 911) |
| 24 | PROCTRAN INSERT failure is fatal (data inconsistency)             | `IF SQLCODE NOT = 0`         | DISPLAY 'DATA INCONSISTENCY, DATA UPDATED ON ACCOUNT'; LINK ABNDPROC; PERFORM CHECK-FOR-STORM-DRAIN-DB2; EXEC CICS ABEND ABCODE('WPCD') | WTPD010 (line 1646) |
| 25 | PROCTRAN transaction type set to Transfer                         | `SET PROC-TY-TRANSFER IN PROCTRAN-AREA TO TRUE` | Transaction type code for transfers loaded from 88-level in PROCTRAN copybook | WTPD010 (line 1603) |
| 26 | PROCTRAN description includes TO sort code and TO account number  | Always on successful transfer | PROC-TRAN-DESC-XFR-SORTCODE = COMM-TSCODE; PROC-TRAN-DESC-XFR-ACCOUNT = COMM-TACCNO     | WTPD010 (line 1610) |
| 27 | PROCTRAN is keyed on FROM account (sort code + account number)    | Always                       | HV-PROCTRAN-SORT-CODE = COMM-FSCODE; HV-PROCTRAN-ACC-NUMBER = COMM-FACCNO                | WTPD010 (line 1581) |
| 28 | PROCTRAN reference number is the CICS task number                 | Always                       | MOVE EIBTASKN TO WS-EIBTASKN12; MOVE WS-EIBTASKN12 TO HV-PROCTRAN-REF                   | WTPD010 (line 1583) |
| 29 | PROCTRAN date and time populated from CICS clock at write time    | Always                       | EXEC CICS ASKTIME; EXEC CICS FORMATTIME DDMMYYYY DATESEP('.') TIME(HV-PROCTRAN-TIME)      | WTPD010 (line 1589) |

### Storm Drain / Abend Handling

| #  | Rule                                                                | Condition                               | Action                                                        | Source Location    |
| -- | ------------------------------------------------------------------- | --------------------------------------- | ------------------------------------------------------------- | ------------------ |
| 30 | SQLCODE 923 (DB2 connection lost) triggers Storm Drain notification | `WHEN 923` in EVALUATE SQLCODE          | MOVE 'DB2 Connection lost' TO STORM-DRAIN-CONDITION; DISPLAY diagnostic | CFSDD010 (line 1746) |
| 31 | VSAM RLS abend codes (AFCR, AFCS, AFCT) treated as Storm Drain     | `WHEN 'AFCR' WHEN 'AFCS' WHEN 'AFCT'` in ABEND-HANDLING | Set WS-STORM-DRAIN='Y'; SYNCPOINT ROLLBACK; set COMM-SUCCESS='N', COMM-FAIL-CODE='2'; EXEC CICS RETURN | AH010 (line 1807) |
| 32 | DB2 AD2Z abend: display diagnostics only, then re-abend             | `WHEN 'AD2Z'` in ABEND-HANDLING         | DISPLAY SQLCODE, SQLSTATE, SQLERRMC, SQLERRD(1-6); fall through to EVALUATE end, then re-abend if WS-STORM-DRAIN='N' | AH010 (line 1791) |
| 33 | Non-storm-drain abends are re-raised                                | `IF WS-STORM-DRAIN = 'N'`              | EXEC CICS ABEND ABCODE(MY-ABEND-CODE) NODUMP                  | AH010 (line 1897) |
| 34 | SYNCPOINT ROLLBACK failure during VSAM RLS handling causes abend   | `IF WS-CICS-RESP NOT = DFHRESP(NORMAL)` | LINK ABNDPROC; EXEC CICS ABEND ABCODE('HROL')                  | AH010 (line 1821) |

### Asymmetric ABNDPROC Coverage

Rule 18 (TO account fails with unexpected FAIL-CODE in the FACCNO < TACCNO path, line 486) issues `EXEC CICS ABEND ABCODE('TO  ') NODUMP` with only a DISPLAY beforehand and no ABNDINFO-REC population or LINK ABNDPROC. By contrast, Rules 16, 20, and 21 (the FROM unexpected-code and the reverse-path TO unexpected-code) all populate ABNDINFO-REC and LINK ABNDPROC before ABENDing. This asymmetry means the ABNDPROC handler will receive no pre-populated ABNDINFO for the specific case of an unexpected TO-account failure code in the forward-order update path.

Similarly, the SYNCPOINT ROLLBACK failure in Rule 15 (FACCNO < TACCNO, FROM fails, line 512) abends with ABCODE('HROL') and NODUMP but does NOT call LINK ABNDPROC -- it uses only a DISPLAY statement. All other HROL abends in the program (Rules 17, 19, 22, Rule 34, and the TO-not-found ROLLBACK failure in Rule 8) do call LINK ABNDPROC.

## Source Code Defect Notes

### Defect 1: SQLERRD(3) deadlock code misidentified as timeout in UADT010 UPDATE path

At UADT010 line 1485, when the TO account UPDATE fails with SQLCODE=-911 and retries are exhausted (DB2-DEADLOCK-RETRY >= 6), the code evaluates `IF SQLERRD(3) = 13172872` and DISPLAYs 'TIMEOUT DETECTED!'. This is factually incorrect: SQLERRD(3)=13172872 is the DB2 **deadlock** indicator, not a timeout. The timeout code is 13172894 (checked correctly at line 1288 in the SELECT path). This appears to be a copy-paste defect in the source -- the DISPLAY message and ABND-FREEFORM text at line 1529-1537 use the word "timeout" while testing the deadlock SQLERRD value. The program still abends with 'RUF3' in all exhausted-retry cases regardless of this DISPLAY inaccuracy.

### Defect 2: ABND-TIME seconds field always contains minutes value (pervasive copy-paste bug)

Every STRING statement that builds `ABND-TIME` in the program (at least 14 occurrences across all paragraphs in UAD010, UADT010, WTPD010, and AH010) uses `WS-TIME-NOW-GRP-MM` twice -- once for the minutes position and once for the position that should hold seconds (`WS-TIME-NOW-GRP-SS`). The field `WS-TIME-NOW-GRP-SS` is defined in WORKING-STORAGE at line 255 but is never referenced anywhere in the PROCEDURE DIVISION. As a result, every abend diagnostic record written to ABNDINFO-REC carries a time in the format `HH:MM:MM` instead of `HH:MM:SS`. This does not affect transaction correctness but means all abend timestamps will have an incorrect seconds field, potentially complicating post-incident analysis. Affected locations include lines 339-345, 435-441, 548-554, 639-645, 709-715, 788-794, 854-860, 1138-1144, 1235-1241, 1313-1319, 1432-1438, 1513-1519, 1670-1676, and 1843-1849.

### Defect 3: Missing ABNDPROC call before HROL abend in Rule 15 (FACCNO < TACCNO, FROM rollback failure)

At UAD010 lines 512-522, when the SYNCPOINT ROLLBACK fails after the FROM account update fails with FAIL-CODE='1' (forward-order path), the code issues `EXEC CICS ABEND ABCODE('HROL') NODUMP` after only a DISPLAY -- no ABNDINFO-REC is populated and LINK ABNDPROC is not called. Every other HROL abend site in the program performs the full ABNDINFO setup and LINK before ABENDing. This means the ABNDPROC handler and any post-hoc analysis tooling will have no structured diagnostic record for this specific failure scenario.

### Defect 4: PROCTRAN INSERT abend does not suppress dump (missing NODUMP)

At WTPD010 line 1716, the PROCTRAN INSERT failure issues `EXEC CICS ABEND ABCODE('WPCD')` without the `NODUMP` keyword. Every other explicit ABEND in the program (SAME, FROM, TO  , HROL, RUF2, RUF3) includes `NODUMP`. The absence of `NODUMP` on the WPCD abend means CICS will produce a transaction dump when the PROCTRAN INSERT fails. This is inconsistent with the rest of the program and may generate unexpected dump output in the CICS dump dataset. The inconsistency is almost certainly unintentional.

### Defect 5: ABND-DATE separator format inconsistent between abend records and PROCTRAN records

POPULATE-TIME-DATE (PTD010, line 1916) calls `EXEC CICS FORMATTIME DATESEP` without specifying a separator character, meaning the date stored in `WS-ORIG-DATE` (and subsequently in `ABND-DATE` in all abend diagnostic records) uses the CICS system-default date separator. WRITE-TO-PROCTRAN-DB2 (WTPD010, line 1593) calls `EXEC CICS FORMATTIME DATESEP('.')` with an explicit dot separator, meaning `HV-PROCTRAN-DATE` always uses a dot. If the system default separator differs from '.', abend diagnostic dates will use a different format than PROCTRAN transaction dates for the same transaction. This is a minor inconsistency but may complicate post-incident correlation between ABNDINFO records and PROCTRAN records.

## Calculations

| Calculation                        | Formula / Logic                                          | Input Fields                              | Output Field                | Source Location      |
| ---------------------------------- | -------------------------------------------------------- | ----------------------------------------- | --------------------------- | -------------------- |
| FROM account available balance debit | `HV-ACCOUNT-AVAIL-BAL = HV-ACCOUNT-AVAIL-BAL - COMM-AMT` | HV-ACCOUNT-AVAIL-BAL (current), COMM-AMT  | HV-ACCOUNT-AVAIL-BAL (new)  | UADF010 (line 986)   |
| FROM account actual balance debit  | `HV-ACCOUNT-ACTUAL-BAL = HV-ACCOUNT-ACTUAL-BAL - COMM-AMT` | HV-ACCOUNT-ACTUAL-BAL (current), COMM-AMT | HV-ACCOUNT-ACTUAL-BAL (new) | UADF010 (line 989)   |
| TO account available balance credit | `HV-ACCOUNT-AVAIL-BAL = HV-ACCOUNT-AVAIL-BAL + COMM-AMT` | HV-ACCOUNT-AVAIL-BAL (current), COMM-AMT  | HV-ACCOUNT-AVAIL-BAL (new)  | UADT010 (line 1357)  |
| TO account actual balance credit   | `HV-ACCOUNT-ACTUAL-BAL = HV-ACCOUNT-ACTUAL-BAL + COMM-AMT` | HV-ACCOUNT-ACTUAL-BAL (current), COMM-AMT | HV-ACCOUNT-ACTUAL-BAL (new) | UADT010 (line 1359)  |

Notes:
- Both available balance and actual balance are updated by the full transfer amount on both accounts.
- No overdraft limit is checked before applying the debit.
- No rounding (ROUNDED) is used; PIC S9(10)V99 COMP-3 arithmetic is used throughout.

## Error Handling

| Condition                                               | Action                                                              | Return Code / Abend | Source Location         |
| ------------------------------------------------------- | ------------------------------------------------------------------- | ------------------- | ----------------------- |
| COMM-AMT <= 0 (non-positive transfer amount)            | COMM-SUCCESS='N', COMM-FAIL-CODE='4'; RETURN                        | COMM-FAIL-CODE='4'  | A010 (line 289)         |
| FROM = TO account (self-transfer attempted)             | LINK ABNDPROC; EXEC CICS ABEND NODUMP CANCEL                        | ABEND('SAME')       | UAD010 (line 316)       |
| FROM account not found (SELECT SQLCODE=+100)            | COMM-SUCCESS='N', COMM-FAIL-CODE='1'; return to caller              | COMM-FAIL-CODE='1'  | UADF010 (line 967)      |
| FROM account SELECT fails (SQLCODE <> 0 and <> +100)   | COMM-SUCCESS='N', COMM-FAIL-CODE='3'; return to caller              | COMM-FAIL-CODE='3'  | UADF010 (line 970)      |
| FROM account UPDATE fails (SQLCODE <> 0)                | COMM-SUCCESS='N', COMM-FAIL-CODE='3'; return to caller              | COMM-FAIL-CODE='3'  | UADF010 (line 1017)     |
| TO account not found (SELECT SQLCODE=+100)              | COMM-FAIL-CODE='2'; DISPLAY; SYNCPOINT ROLLBACK; return to caller   | COMM-FAIL-CODE='2'  | UADT010 (line 1102)     |
| TO account not found -- ROLLBACK itself fails           | LINK ABNDPROC; EXEC CICS ABEND ABCODE('HROL') NODUMP CANCEL        | ABEND('HROL')       | UADT010 (line 1116)     |
| TO account SELECT deadlock (-911/SQLERRD(3)=13172872), retry < 6 | SYNCPOINT ROLLBACK; DELAY 1s; restart at UPDATE-ACCOUNT-DB2 | Retry loop          | UADT010 (line 1197)     |
| TO account SELECT deadlock, retry >= 6 or other -911   | LINK ABNDPROC; EXEC CICS ABEND                                      | ABEND('RUF2')       | UADT010 (line 1341)     |
| TO account SELECT timeout (SQLERRD(3)=13172894)         | DISPLAY 'TIMEOUT DETECTED!'; LINK ABNDPROC; ABEND                   | ABEND('RUF2')       | UADT010 (line 1289)     |
| TO account UPDATE fails (SQLCODE <> 0, non-deadlock or exhausted retries) | DISPLAY; LINK ABNDPROC; ABEND              | ABEND('RUF3')       | UADT010 (line 1545)     |
| TO account UPDATE deadlock, retry < 6                   | SYNCPOINT ROLLBACK; DELAY 1s; restart at UPDATE-ACCOUNT-DB2        | Retry loop          | UADT010 (line 1397)     |
| TO account UPDATE deadlock retry >= 6: exhausted        | Falls through to LINK ABNDPROC; EXEC CICS ABEND ABCODE('RUF3')     | ABEND('RUF3')       | UADT010 (line 1541)     |
| SYNCPOINT ROLLBACK fails (CICS RESP <> NORMAL), most paths | LINK ABNDPROC; EXEC CICS ABEND ABCODE('HROL')                  | ABEND('HROL')       | UAD010 lines 413, 687, 832; UADT010 line 1116; AH010 line 1821 |
| SYNCPOINT ROLLBACK fails (FROM FAIL-CODE='1' forward path) | DISPLAY only (no LINK ABNDPROC); EXEC CICS ABEND ABCODE('HROL') NODUMP | ABEND('HROL') | UAD010 (line 512) -- see Defect 3 |
| PROCTRAN INSERT fails (SQLCODE <> 0)                    | DISPLAY data inconsistency message; LINK ABNDPROC; CHECK-FOR-STORM-DRAIN-DB2; ABEND (no NODUMP -- see Defect 4) | ABEND('WPCD') | WTPD010 (line 1646) |
| DB2 connection lost (SQLCODE=923)                       | DISPLAY Storm Drain condition (informational only, no rollback)     | None (logging only) | CFSDD010 (line 1746)    |
| VSAM RLS abend (AFCR/AFCS/AFCT)                         | SYNCPOINT ROLLBACK; COMM-SUCCESS='N', COMM-FAIL-CODE='2'; RETURN    | COMM-FAIL-CODE='2'  | AH010 (line 1807)       |
| DB2 AD2Z (deadlock abend)                               | DISPLAY diagnostic info then re-abend                               | ABEND(MY-ABEND-CODE) | AH010 (line 1791)      |
| Any other unhandled abend                               | EXEC CICS ABEND ABCODE(MY-ABEND-CODE) NODUMP                        | ABEND(MY-ABEND-CODE) | AH010 (line 1899)      |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. **A010** -- Entry point. Registers ABEND-HANDLING label. Initialises host variables (HV-ACCOUNT-EYECATCHER, sortcode, acc-no to '0'). Unconditionally overwrites COMM-FSCODE and COMM-TSCODE with the application's own SORTCODE (from SORTCODE copybook), making cross-bank transfers impossible regardless of caller input. Validates COMM-AMT > 0.
2. **UPDATE-ACCOUNT-DB2 (UAD010)** -- Validates FROM <> TO. Determines update order (lower account number first to prevent deadlocks). Orchestrates calls to FROM and TO update sub-paragraphs. Handles all rollback and abend scenarios. Both success paths converge at PERFORM WRITE-TO-PROCTRAN.
3. **UPDATE-ACCOUNT-DB2-FROM (UADF010)** -- Re-fetches COMM-FACCNO/COMM-FSCODE into DESIRED-ACC-NO/DESIRED-SORT-CODE (redundant with UAD010 setup but harmless). Selects FROM account row from DB2 ACCOUNT table, debits both available and actual balance by COMM-AMT, updates the row, stores new balances in COMM-FAVBAL/COMM-FACTBAL.
4. **UPDATE-ACCOUNT-DB2-TO (UADT010)** -- Initialises COMM-SUCCESS='N' on entry (resets any prior success state). Selects TO account row from DB2 ACCOUNT table, credits both available and actual balance by COMM-AMT, updates the row, stores new balances in COMM-TAVBAL/COMM-TACTBAL. Contains DB2 deadlock retry loop (up to 5 retries with 1-second delay). Deadlock retry GO TO target is UPDATE-ACCOUNT-DB2 (the whole section), resetting the entire two-account update sequence.
5. **WRITE-TO-PROCTRAN (WTP010)** -- Thin wrapper; calls WRITE-TO-PROCTRAN-DB2.
6. **WRITE-TO-PROCTRAN-DB2 (WTPD010)** -- Constructs and INSERTs a PROCTRAN row. Sets eyecatcher='PRTR', transaction type=Transfer (from 88-level PROC-TY-TRANSFER), description set via PROC-TRAN-DESC-XFR-FLAG includes TO sort code and account. Reference = EIBTASKN. Uses `DATESEP('.')` explicitly for the transaction date. Abends on INSERT failure; unlike all other explicit ABENDs in the program, the WPCD abend does not include NODUMP (see Defect 4).
7. **GET-ME-OUT-OF-HERE (GMOOH010)** -- Issues EXEC CICS RETURN to return to caller. Also contains GOBACK as a fallback.
8. **CHECK-FOR-STORM-DRAIN-DB2 (CFSDD010)** -- Evaluates SQLCODE for Storm Drain trigger conditions; logs if SQLCODE=923 (DB2 connection lost). All other codes set STORM-DRAIN-CONDITION to 'Not Storm Drain'. Called before SQLCODE discrimination in UADT010 (meaning it fires even for SQLCODE=+100), but this has no functional side effect since +100 resolves to 'Not Storm Drain' in the EVALUATE.
9. **ABEND-HANDLING (AH010)** -- CICS HANDLE ABEND target. Evaluates abend code: DB2 AD2Z (display and re-abend), VSAM RLS codes AFCR/AFCS/AFCT (rollback and soft return), all others (re-abend).
10. **POPULATE-TIME-DATE (PTD010)** -- EXEC CICS ASKTIME + FORMATTIME to get current date/time into WS-ORIG-DATE and WS-TIME-NOW for abend diagnostic records. Uses `DATESEP` without an explicit separator character (system default), which may differ from the dot separator used in WTPD010 (see Defect 5).
11. CALL **ABNDPROC** (via EXEC CICS LINK, program name literal 'ABNDPROC' in WS-ABEND-PGM) -- Called with populated ABNDINFO-REC before any explicit ABEND to record structured abend diagnostics (with the exceptions noted in Defect 3 and Rule 18).
