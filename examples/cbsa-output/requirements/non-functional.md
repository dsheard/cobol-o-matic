---
type: requirements
subtype: non-functional
status: draft
confidence: high
last_pass: 1
---

# Non-Functional Requirements

Derived non-functional requirements observed in the COBOL source code.

---

## Error Handling

| Program        | Pattern                              | Approach                                  | Evidence                                                                                                                           |
| -------------- | ------------------------------------ | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| CRECUST        | DFHRESP checks on all CICS calls     | Graceful (fail code + EXEC CICS RETURN) for most; ABEND HWPT on PROCTRAN INSERT failure | COMM-FAIL-CODE 'A'-'H' and '1'-'5' set on each failure type; GET-ME-OUT-OF-HERE used as common exit; PROCTRAN failure escalates to ABEND |
| CREACC         | SQLCODE checks + DFHRESP checks      | Graceful for account-level errors; ABEND HNCS / HWPT for CONTROL and PROCTRAN failures | COMM-FAIL-CODE '1'-'9', 'A', '3', '5', '7', '8', '9' returned to caller; CONTROL table failures unconditionally ABEND HNCS NODUMP |
| DBCRFUN        | SQLCODE + DFHRESP + HANDLE ABEND     | Graceful for not-found / balance errors; SYNCPOINT ROLLBACK + ABEND HROL on rollback failure; VSAM RLS abends trapped with soft return | COMM-FAIL-CODE '1'-'4', '02'; AFCR/AFCS/AFCT storm-drain path rolls back and returns; AD2Z re-abends after diagnostic display |
| XFRFUN         | SQLCODE + deadlock retry + HANDLE ABEND | Graceful for not-found (fail codes '1','2'); ABEND for unexpected errors; SYNCPOINT ROLLBACK on TO-account not-found; deadlock retry up to 5 times | GO TO UPDATE-ACCOUNT-DB2 retry loop; ABEND codes SAME, FROM, TO, HROL, RUF2, RUF3, WPCD; VSAM RLS storm-drain path |
| DELACC         | SQLCODE checks                       | Graceful for DELETE failure (fail code '3'); ABEND HRAC on unexpected SELECT error; ABEND HWPT (no NODUMP) on PROCTRAN failure | HRAC ABEND does not call ABNDPROC (asymmetry defect); HWPT generates dump |
| DELCUS         | DFHRESP + SQLCODE + HANDLE ABEND logic | SYSIDERR retry (100 attempts); NOTFND treated as concurrent delete (silent skip); all other non-NORMAL responses cause ABEND WPV6/WPV7 | PERFORM VARYING SYSIDERR-RETRY FROM 1 BY 1 UNTIL > 100 at DCV010; ABEND codes WPV6, WPV7, HWPT |
| INQACC         | SQLCODE + DFHRESP + HANDLE ABEND     | Graceful for SQLCODE +100 (not found); ABEND HRAC/HNCS for all other errors; VSAM RLS storm-drain soft return | CHECK-FOR-STORM-DRAIN-DB2 called before ABEND on standard path; GLAD010 last-account path skips storm drain check |
| INQCUST        | DFHRESP checks                       | Graceful (INQACC-SUCCESS='N') for NOTFND; ABEND on unexpected CICS error | VSAM CICS FILE READ with RESP checking |
| UPDACC         | SQLCODE checks                       | Graceful only (COMM-SUCCESS='N' + RETURN); no ABEND issued; dead abend infrastructure in WORKING-STORAGE | ABNDPROC and ABNDINFO-REC declared but never referenced in PROCEDURE DIVISION; errors are soft-fail |
| UPDCUST        | DFHRESP checks                       | Graceful only (COMM-SUCCESS='N'); no ABEND                                | Similar to UPDACC; abend scaffolding present but unwired                                                                           |
| ABNDPROC       | DFHRESP on VSAM WRITE                | Silent on ABNDFILE write failure (DISPLAY + RETURN; no re-abend)          | If ABNDFILE write fails, diagnostic messages go to CICS log and record is silently abandoned                                       |
| BNKMENU        | DFHRESP on all CICS SEND/RECEIVE     | ABEND HBNK via ABND-THIS-TASK paragraph for most failures; MAPFAIL is benign (redisplay) | LINK ABNDPROC before every ABEND-THIS-TASK; MAPFAIL fall-through causes spurious validation message (UX defect) |
| BNK1CCS, BNK1CAC, BNK1CRA, BNK1DAC, BNK1DCS, BNK1TFN, BNK1UAC, BNK1CCA | DFHRESP on all CICS MAP/LINK calls | ABEND via ABND-THIS-TASK or direct LINK ABNDPROC + ABEND on failures; user-facing validation errors shown via SEND DATAONLY ALARM | All screen programs follow same abend pattern using ABNDINFO copybook and LINK to ABNDPROC |
| CRDTAGY1-5     | DFHRESP on DELAY, GET/PUT CONTAINER  | DELAY failure causes ABEND 'PLOP' via ABNDPROC; GET/PUT failures return silently (DISPLAY + RETURN only) | Silent GET/PUT failure means parent CRECUST proceeds without that agency's score |
| BANKDATA       | VSAM status codes + SQLCODE          | Graceful: RETURN-CODE=12 + GOBACK on fatal errors; CONTROL INSERT failures are logged but not fatal | File I/O uses VSAM-STATUS '00' check; DB2 CONTROL INSERT failure only DISPLAYs SQLCODE (no GOBACK) |

---

## Data Integrity

| Program        | Pattern                                  | Mechanism                                                                   | Evidence                                                                                                                              |
| -------------- | ---------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| DBCRFUN        | ACCOUNT UPDATE + PROCTRAN INSERT in same CICS UoW | SYNCPOINT ROLLBACK on PROCTRAN INSERT failure undoes the ACCOUNT balance update | WTPD010: EXEC CICS SYNCPOINT ROLLBACK issued when SQLCODE NOT = 0 on INSERT INTO PROCTRAN; ROLLBACK failure triggers ABEND HROL |
| XFRFUN         | Two-account UPDATE + PROCTRAN INSERT in same CICS UoW | SYNCPOINT ROLLBACK when TO account not found (after FROM already updated); deadlock retry re-runs entire two-account update sequence | UAD010/UADT010: EXEC CICS SYNCPOINT ROLLBACK on TO-not-found; GO TO UPDATE-ACCOUNT-DB2 on deadlock retry resets full sequence |
| DELCUS         | CUSTOMER READ with UPDATE + TOKEN locking | CICS token-based optimistic locking on CUSTOMER VSAM record prevents concurrent modification | DCV010: EXEC CICS READ FILE('CUSTOMER') UPDATE TOKEN(WS-TOKEN); EXEC CICS DELETE FILE('CUSTOMER') TOKEN(WS-TOKEN) |
| DELCUS         | INQACCCU called with SYNCONRETURN        | CICS SYNCONRETURN commits prior work before INQACCCU returns              | GAC010: EXEC CICS LINK PROGRAM('INQACCCU') SYNCONRETURN; syncpoint taken at INQACCCU return |
| DELCUS         | No rollback on partial cascade delete    | By design: any failure after deletions start causes ABEND to prevent inconsistent state | Source comment: 'if there is a failure at any time after we have started to delete things then abend (or else the records will be out of step)' |
| CRECUST        | CICS ENQ/DEQ serialises CUSTOMER number counter | CICS ENQ on 'CBSACUST'+sortcode ensures one-at-a-time access to VSAM control record | ENC010 / DNC010: EXEC CICS ENQ RESOURCE(NCS-CUST-NO-NAME) LENGTH(16); DEQ on both success and failure paths |
| CREACC         | CICS ENQ/DEQ serialises ACCOUNT number counter | CICS ENQ on 'CBSAACCT'+sortcode ensures one-at-a-time access to CONTROL DB2 counter | ENC010 / DNC010: EXEC CICS ENQ RESOURCE(NCS-ACC-NO-NAME) LENGTH(16); counter incremented only within ENQ scope |
| BANKDATA       | SQL COMMIT every 1,000 customer iterations | Periodic commit during bulk load prevents long DB2 UoW and reduces rollback exposure | A010 line 579: IF COMMIT-COUNT > 1000 EXEC SQL COMMIT WORK; also committed after each customer's accounts in DA010 |
| CRECUST        | Counter not decremented on failure (defect) | When CRECUST fails after incrementing the VSAM customer counter, the counter value is not restored | Business-rules rule 36: 'Counter value is permanently incremented even when customer write fails; only DEQ is issued' |
| CRECUST        | Control record update has no error check (defect) | Post-WRITE control record REWRITE (count update) has no RESP clause; failure is silent | Business-rules rule 42: WCV010 lines 1133-1146 have no RESP/RESP2 clauses |
| DBCRFUN        | Balance values copied to COMMAREA before SQLCODE check (defect) | If ACCOUNT UPDATE fails, caller receives modified in-memory balances despite COMM-SUCCESS='N' | UAD010 lines 416-419: COMM-AV-BAL/COMM-ACT-BAL set before UPDATE SQLCODE test at line 425 |

---

## Performance

| Program        | Pattern                          | Indicator                                                                         | Evidence                                                                                                            |
| -------------- | -------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| BANKDATA       | Bulk batch load with periodic COMMIT | DB2 COMMIT every 1,000 customer/account cycles plus per-customer commit          | A010 line 579: COMMIT-COUNT > 1000 triggers EXEC SQL COMMIT WORK; DA010 commits unconditionally after each customer |
| BANKDATA       | Clean-slate DELETE before INSERT | Full DELETE of ACCOUNT + CONTROL rows before bulk INSERT                         | DBR010: DELETE FROM ACCOUNT WHERE ACCOUNT_SORTCODE = :sortcode; COMMIT after all three DELETEs                      |
| BANKDATA       | JCL PARM-controlled data volume  | PARM='1,10000,1,seed' generates 10,000 customers with 1-5 accounts each           | BANKDATA JCL BANKDAT5 step PARM specification                                                                       |
| CRECUST        | Async parallel credit checks with bounded wait | Five concurrent CICS RUN TRANSID child tasks plus 3-second DELAY THEN FETCH ANY NOSUSPEND | CC010: EXEC CICS DELAY FOR SECONDS(3) followed by FETCH ANY NOSUSPEND loop; each agency has 1-3 second random delay |
| XFRFUN         | Deadlock retry with 1-second backoff | DB2 deadlock retry loop up to 5 times with EXEC CICS DELAY FOR SECONDS(1) + SYNCPOINT ROLLBACK | UADT010: DB2-DEADLOCK-RETRY counter; IF SQLCODE=-911 AND SQLERRD(3)=13172872 AND DB2-DEADLOCK-RETRY < 6 |
| DELCUS         | SYSIDERR retry with 3-second backoff | VSAM SYSIDERR on CUSTOMER READ or DELETE retried up to 100 times with 3-second delay | DCV010: PERFORM VARYING SYSIDERR-RETRY FROM 1 BY 1 UNTIL > 100 with EXEC CICS DELAY FOR SECONDS(3) |
| CRECUST        | SYSIDERR retry with 3-second backoff | VSAM SYSIDERR on CUSTOMER counter READ or WRITE retried up to 100 times          | GLCV010/WCV010: retry loops up to 100 iterations with 3-second delay each                                           |
| INQACC         | DB2 cursor-based single fetch     | OPEN cursor, single FETCH, CLOSE cursor for standard account lookup              | RAD010/FD010: ACC-CURSOR declared FOR FETCH ONLY; single FETCH then immediate CLOSE                                 |
| INQACCCU       | DB2 cursor fetching up to 20 rows | Cursor loop fetching all customer accounts up to array maximum of 20             | INQACCCU source: ODO array OCCURS 1 TO 20 DEPENDING ON NUMBER-OF-ACCOUNTS                                           |

---

## Security

| Program        | Pattern                          | Mechanism                                                                         | Evidence                                                                                                            |
| -------------- | -------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| All online     | CICS transaction-level security  | All user actions go through named CICS transactions (OMEN, ODCS, ODAC, etc.); transaction-to-program mapping held in CICS CSD | CICS CSD loaded via DFHCSDUP in CBSACSD.jcl; BANK group defines all program/transaction/file/mapset definitions |
| CRECUST        | Child transaction security error handling | CICS FETCH ANY COMPSTATUS = DFHVALUE(SECERROR) triggers fail code 'G' and GOBACK | CC010 rule 23: SECERROR compstatus causes COMM-SUCCESS='N', COMM-FAIL-CODE='G', GET-ME-OUT-OF-HERE |
| All programs   | Hardcoded sort code prevents cross-bank access | SORTCODE literal (987654) is unconditionally applied, preventing programs from accessing accounts at other sort codes | XFRFUN A010 lines 281: MOVE SORTCODE to COMM-FSCODE and COMM-TSCODE, overwriting any caller-supplied values; DBCRFUN, INQACC, UPDACC, DELACC all behave identically |
| No programs    | No user ID or role validation found | No EXEC CICS ASSIGN USERID or role-based access checks in any COBOL program      | No CICS RACF or ASSIGN USERID calls observed; access control is at transaction level only, not within program logic |

---

## Audit and Logging

| Program        | Pattern                          | Mechanism                                                                         | Evidence                                                                                                            |
| -------------- | -------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| CRECUST        | PROCTRAN INSERT type 'OCC'       | Audit row for every customer creation; includes sortcode, customer number, name, DOB | WPD010: HV-PROCTRAN-TYPE = 'OCC'; DESC contains sortcode, custno, name, DOB                                        |
| CREACC         | PROCTRAN INSERT type 'OCA'       | Audit row for every account creation; amount = zero; includes customer and account IDs | WPD010: HV-PROCTRAN-TYPE = 'OCA'; HV-PROCTRAN-AMOUNT = 0; EIBTASKN as reference                                   |
| DELACC         | PROCTRAN INSERT type 'ODA'       | Audit row for every account deletion; amount = actual balance at deletion         | WPD010: PROC-TY-BRANCH-DELETE-ACCOUNT (88-level 'ODA'); ACCOUNT-ACT-BAL-STORE as amount                            |
| DELCUS         | PROCTRAN INSERT type 'ODC'       | Single audit row per customer deletion; amount = zero; includes customer details in description | WPCD010: HV-PROCTRAN-TYPE = 'ODC'; HV-PROCTRAN-AMOUNT = ZEROS                                                     |
| DBCRFUN        | PROCTRAN INSERT types 'DEB', 'CRE', 'PDR', 'PCR' | Four transaction type codes distinguish teller vs. payment-link debits/credits | WTPD010: EVALUATE COMM-AMT/COMM-FACILTYPE to select 'DEB', 'CRE', 'PDR', or 'PCR'; amount stored signed            |
| XFRFUN         | PROCTRAN INSERT Transfer type    | Audit row keyed on FROM account; description includes TO sort code and account number | WTPD010: PROC-TY-TRANSFER (88-level); PROC-TRAN-DESC-XFR-SORTCODE = COMM-TSCODE; PROC-TRAN-DESC-XFR-ACCOUNT = COMM-TACCNO |
| ABNDPROC       | ABNDFILE VSAM WRITE              | Centralised abend log; records APPLID, TRANID, date, time, abend code, program, RESP, RESP2, SQLCODE, 600-byte freeform | ABNDINFO copybook defines full 681-byte record; key = UNIX microsecond timestamp + CICS task number                 |
| All programs   | DISPLAY to CICS log on errors    | Diagnostic DISPLAY statements on every significant error path                    | Every abend path includes DISPLAY of error context before calling ABNDPROC and issuing ABEND                        |
| All programs   | ABND-TIME seconds defect         | Abend timestamps written with HH:MM:MM instead of HH:MM:SS across all programs  | STRING defect using WS-TIME-NOW-GRP-MM twice; WS-TIME-NOW-GRP-SS never referenced in any program's PROCEDURE DIVISION |
| All programs   | EIBTASKN as PROCTRAN reference   | CICS task number is the reference key for every PROCTRAN row                     | All PROCTRAN writers: MOVE EIBTASKN TO WS-EIBTASKN12; MOVE WS-EIBTASKN12 TO HV-PROCTRAN-REF                        |

---

## Recovery

| Program        | Pattern                          | Mechanism                                                                         | Evidence                                                                                                            |
| -------------- | -------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| DBCRFUN        | SYNCPOINT ROLLBACK on PROCTRAN failure | Undoes ACCOUNT balance UPDATE if PROCTRAN INSERT fails; restores atomicity     | WTPD010: EXEC CICS SYNCPOINT ROLLBACK when SQLCODE NOT = 0 on PROCTRAN INSERT                                       |
| XFRFUN         | SYNCPOINT ROLLBACK on TO account not found | Rolls back FROM account debit when TO account does not exist               | UADT010: EXEC CICS SYNCPOINT ROLLBACK at line 1102 when SQLCODE = +100 (TO account not found)                       |
| XFRFUN         | Deadlock retry with SYNCPOINT ROLLBACK + re-run | Full two-account update restarted on DB2 deadlock (-911) up to 5 times  | UADT010: DB2-DEADLOCK-RETRY counter; SYNCPOINT ROLLBACK; EXEC CICS DELAY 1 second; GO TO UPDATE-ACCOUNT-DB2        |
| XFRFUN         | HANDLE ABEND for VSAM RLS storm drain | AFCR/AFCS/AFCT abends handled with SYNCPOINT ROLLBACK and soft return       | AH010: WHEN 'AFCR'/'AFCS'/'AFCT': WS-STORM-DRAIN='Y'; SYNCPOINT ROLLBACK; COMM-SUCCESS='N'; EXEC CICS RETURN       |
| DELCUS         | SYSIDERR retry loop              | Up to 100 retries with 3-second delay for VSAM CUSTOMER READ and DELETE          | DCV010: PERFORM VARYING SYSIDERR-RETRY FROM 1 BY 1 UNTIL > 100 with DELAY FOR SECONDS(3) each retry                |
| CRECUST        | SYSIDERR retry loop              | Up to 100 retries with 3-second delay for VSAM CUSTOMER counter and record writes | GLCV010/WCV010: retry loops; SYSIDERR retry exhaustion falls through silently (defect: code continues on unread data) |
| BANKDATA       | Periodic DB2 COMMIT              | COMMIT every 1,000 iterations limits rollback scope in batch load                | A010 line 579: EXEC SQL COMMIT WORK when COMMIT-COUNT > 1000                                                        |
| BANKDATA       | IDCAMS SET MAXCC=0               | JCL BANKDAT0 and BANKDAT1 steps force MAXCC=0 so a missing VSAM cluster does not abort the job | BANKDATA.jcl: IDCAMS DELETE step with SET MAXCC=0; ensures first-time run succeeds even if datasets don't exist |
| All programs   | ABNDPROC centralised abend record | All programs link to ABNDPROC before ABEND to persist structured diagnostic record for post-incident analysis | 23 programs (all except UPDACC, UPDCUST) link to ABNDPROC on error; ABNDFILE is the recovery audit trail           |
