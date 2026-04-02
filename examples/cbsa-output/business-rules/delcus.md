---
type: business-rules
program: DELCUS
program_type: online
status: draft
confidence: high
last_pass: 5
calls: []
called_by:
- BNK1DCS
uses_copybooks:
- ABNDINFO
- ACCOUNT
- CUSTOMER
- DELCUS
- INQACCCU
- INQCUST
- PROCDB2
- PROCTRAN
- SORTCODE
reads:
- CUSTOMER
writes: []
db_tables:
- PROCTRAN
transactions: []
mq_queues: []
---

# DELCUS -- Business Rules

## Program Purpose

DELCUS is a CICS online program that deletes a customer and all of their associated accounts from the CBSA banking system. It accepts a customer number via DFHCOMMAREA, verifies the customer exists (via INQCUST), retrieves all accounts for that customer (via INQACCCU), deletes each account one-by-one (via DELACC), deletes the CUSTOMER VSAM record, and writes a transaction audit record to the PROCTRAN DB2 table. The design principle is: once any deletion has started, any subsequent failure is treated as fatal and causes an ABEND -- no partial deletes are permitted. The one exception is if a customer VSAM record is already absent when the delete is attempted (concurrent deletion), in which case processing continues.

Note: The program header comment (lines 9-14) states that DELCUS "writes a PROCTRAN delete account record out for each deleted account." This is inaccurate as written. Examining the PROCEDURE DIVISION, DELCUS does NOT write PROCTRAN records for account deletions -- it only LINKs to DELACC for each account (which handles its own audit trail) and then writes a single customer-level 'ODC' record to PROCTRAN. Account-level PROCTRAN records are the responsibility of DELACC, not DELCUS.

Called by BNK1DCS (the delete-customer screen handler).

## Input / Output

| Direction | Resource     | Type | Description                                                                 |
| --------- | ------------ | ---- | --------------------------------------------------------------------------- |
| IN        | DFHCOMMAREA  | CICS | Input commarea (DELCUS copybook): COMM-CUSTNO is the customer number to delete |
| IN/OUT    | CUSTOMER     | CICS VSAM FILE | Read-with-UPDATE then DELETE for the target customer record            |
| IN        | INQCUST      | CICS LINK | Called program: verifies the customer exists before deletion begins     |
| IN        | INQACCCU     | CICS LINK | Called program: returns all accounts (up to 20) for the customer        |
| OUT       | DELACC       | CICS LINK | Called program: deletes each individual account                         |
| OUT       | PROCTRAN     | DB2 TABLE | Audit INSERT: one 'ODC' (Online Delete Customer) row per customer deleted |
| OUT       | ABNDPROC     | CICS LINK | Abend handler program called on any unrecoverable error                 |
| OUT       | DFHCOMMAREA  | CICS | Output: COMM-DEL-SUCCESS ('Y'/'N') and COMM-DEL-FAIL-CD set on return  |

## Business Rules

### Customer Existence Validation

| #  | Rule                                | Condition                                      | Action                                                                                                    | Source Location        |
| -- | ----------------------------------- | ---------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ---------------------- |
| 1  | Customer must exist before deletion | INQCUST-INQ-SUCCESS = 'N' after LINK to INQCUST | Set COMM-DEL-SUCCESS = 'N', copy INQCUST-INQ-FAIL-CD to COMM-DEL-FAIL-CD, EXEC CICS RETURN (abort)      | A010, lines 264-269    |
| 2  | Customer verified before processing | INQCUST-INQ-SUCCESS != 'N'                     | Continue processing: retrieve accounts, delete accounts, delete customer record                            | A010, lines 264-292    |

### Account Deletion Routing

| #  | Rule                                            | Condition                        | Action                                                              | Source Location       |
| -- | ----------------------------------------------- | -------------------------------- | ------------------------------------------------------------------- | --------------------- |
| 3  | Skip account deletion if no accounts found      | NUMBER-OF-ACCOUNTS = 0           | PERFORM DELETE-ACCOUNTS is skipped; proceed directly to DEL-CUST-VSAM | A010, lines 276-278 |
| 4  | Delete all accounts if any exist                | NUMBER-OF-ACCOUNTS > 0           | PERFORM DELETE-ACCOUNTS: iterate through all accounts and delete each via DELACC | A010, lines 276-278 |
| 5  | Accounts are deleted one at a time              | WS-INDEX from 1 to NUMBER-OF-ACCOUNTS | EXEC CICS LINK PROGRAM('DELACC  ') for each account in the INQACCCU-COMMAREA array (COMM-ACCNO(WS-INDEX)) | DA010, lines 306-316 |
| 6  | Maximum 20 accounts supported per customer      | INQACCCU commarea ACCOUNT-DETAILS OCCURS 1 TO 20 DEPENDING ON NUMBER-OF-ACCOUNTS | INQACCCU is called with NUMBER-OF-ACCOUNTS set to 20 (maximum) before the LINK | GAC010, line 330 |
| 7  | DELACC return code is not checked by DELCUS     | No IF after EXEC CICS LINK to DELACC | DELCUS trusts DELACC to handle its own errors and ABEND if necessary. Per program header comment: "The only failure excluded from this, is where we go to delete an account and it had already been deleted (if this happens then we can just continue)" -- but DELCUS itself does not inspect DELACC-COMM-DEL-SUCCESS | DA010, lines 312-316 |
| 8  | APPLID is passed to DELACC (defect: always spaces) | Always before each DELACC LINK | WS-APPLID is moved to DELACC-COMM-APPLID in the DELACC commarea before the LINK. However WS-APPLID (PIC X(8), line 165) is never populated via EXEC CICS ASSIGN APPLID(WS-APPLID) anywhere in DELCUS -- all ASSIGN APPLID statements only populate ABND-APPLID. Therefore DELACC-COMM-APPLID is always spaces/low-values. | DA010, line 309; WS-APPLID declared line 165 |
| 9  | PCB pointer threaded from DELACC commarea to INQACCCU | Always in GET-ACCOUNTS | SET COMM-PCB-POINTER OF INQACCCU-COMMAREA TO DELACC-COMM-PCB1 -- the IMS PCB1 pointer from the DELACC commarea is passed into the INQACCCU commarea before the LINK to INQACCCU, allowing INQACCCU to access the IMS PCB if needed. PCB2 (DELACC-COMM-PCB2, line 213) is declared but never populated or used within DELCUS. | GAC010, lines 331-332 |

### Customer VSAM Delete Logic

| #  | Rule                                                     | Condition                                         | Action                                                                                           | Source Location        |
| -- | -------------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ---------------------- |
| 10 | Customer record is read with update lock before deletion | Always in DEL-CUST-VSAM                           | EXEC CICS READ FILE('CUSTOMER') ... UPDATE TOKEN(WS-TOKEN) -- record locked before delete       | DCV010, lines 353-360  |
| 11 | SYSIDERR on READ is retried up to 100 times              | WS-CICS-RESP = DFHRESP(SYSIDERR) on READ          | PERFORM VARYING SYSIDERR-RETRY FROM 1 BY 1 UNTIL > 100: delay 3 seconds, retry READ each iteration | DCV010, lines 362-382 |
| 12 | NOTFND on READ is treated as concurrent deletion         | WS-CICS-RESP = DFHRESP(NOTFND) after READ         | GO TO DCV999 (exit section silently -- another task already deleted the record)                  | DCV010, lines 384-389  |
| 13 | Any other non-NORMAL response on READ causes ABEND       | WS-CICS-RESP NOT = DFHRESP(NORMAL)                | Populate ABNDINFO-REC, LINK to ABNDPROC, DISPLAY diagnostic, EXEC CICS ABEND ABCODE('WPV6')     | DCV010, lines 391-452  |
| 14 | Customer data is captured into COMMAREA before deletion  | After successful READ                             | Customer eye-catcher, sortcode, number, name, address, DOB, credit score, CS review date are all copied to WS-STOREDC-* and DFHCOMMAREA COMM-* fields | DCV010, lines 454-489 |
| 15 | Date-of-birth reformatted DD/MM/YYYY for output          | Always on READ success                            | Raw CUSTOMER-DATE-OF-BIRTH (DDMMYYYY 8 bytes) is split and '/' separators inserted into WS-STOREDC-DATE-OF-BIRTH and COMM-BIRTH-* fields | DCV010, lines 464-475 |
| 16 | CS review date reformatted DD/MM/YYYY for output         | Always on READ success                            | Raw CUSTOMER-CS-REVIEW-DATE (8 bytes) is split and '/' separators inserted into WS-STOREDC-CS-REVIEW-DATE and COMM-CS-REVIEW-* fields | DCV010, lines 479-489 |
| 17 | Customer VSAM DELETE uses token from prior UPDATE READ   | Always after successful READ with UPDATE          | EXEC CICS DELETE FILE('CUSTOMER') TOKEN(WS-TOKEN) -- uses optimistic locking token from the READ | DCV010, lines 491-496 |
| 18 | SYSIDERR on DELETE is retried up to 100 times            | WS-CICS-RESP = DFHRESP(SYSIDERR) on DELETE        | PERFORM VARYING SYSIDERR-RETRY FROM 1 BY 1 UNTIL > 100: delay 3 seconds, retry DELETE each iteration | DCV010, lines 498-515 |
| 19 | Any non-NORMAL response on DELETE causes ABEND           | WS-CICS-RESP NOT = DFHRESP(NORMAL) after DELETE   | Populate ABNDINFO-REC, LINK to ABNDPROC, DISPLAY diagnostic, EXEC CICS ABEND ABCODE('WPV7')     | DCV010, lines 517-578  |

### PROCTRAN Audit Record

| #  | Rule                                          | Condition         | Action                                                                                                    | Source Location       |
| -- | --------------------------------------------- | ----------------- | --------------------------------------------------------------------------------------------------------- | --------------------- |
| 20 | Audit record eye-catcher is 'PRTR'            | Always            | HV-PROCTRAN-EYECATCHER = 'PRTR'                                                                           | WPCD010, line 603     |
| 21 | Account number field is zero for customer delete | Always          | HV-PROCTRAN-ACC-NUMBER = ZEROS -- no specific account for a customer-level delete                         | WPCD010, line 606     |
| 22 | Transaction type is 'ODC'                     | Always            | HV-PROCTRAN-TYPE = 'ODC' (Online Delete Customer)                                                        | WPCD010, line 632     |
| 23 | Transaction amount is zero                    | Always            | HV-PROCTRAN-AMOUNT = ZEROS -- no monetary amount for a delete event                                       | WPCD010, line 633     |

### Successful Completion

| #  | Rule                                   | Condition                  | Action                                                               | Source Location     |
| -- | -------------------------------------- | -------------------------- | -------------------------------------------------------------------- | ------------------- |
| 24 | Success flag set after all deletions   | All deletions completed normally | MOVE 'Y' TO COMM-DEL-SUCCESS; MOVE ' ' TO COMM-DEL-FAIL-CD      | A010, lines 289-290 |

## Calculations

| Calculation | Formula / Logic | Input Fields | Output Field | Source Location |
| ----------- | --------------- | ------------ | ------------ | --------------- |
| PROCTRAN reference number | EIBTASKN (4-byte task number) moved to 12-digit field WS-EIBTASKN12 | EIBTASKN | HV-PROCTRAN-REF (PIC X(12)) | WPCD010, lines 607-608 |
| PROCTRAN description assembly | Concatenation of sortcode (bytes 1-6), customer number (bytes 7-16), name truncated to 14 chars (bytes 17-30), date-of-birth formatted (bytes 31-40) into 40-byte HV-PROCTRAN-DESC | WS-STOREDC-SORTCODE, WS-STOREDC-NUMBER, WS-STOREDC-NAME, WS-STOREDC-DATE-OF-BIRTH | HV-PROCTRAN-DESC PIC X(40) | WPCD010, lines 627-630 |
| PROCTRAN date formatting | EXEC CICS ASKTIME -> FORMATTIME DDMMYYYY with DATESEP('.') produces DD.MM.YYYY in WS-ORIG-DATE; then MOVE to WS-ORIG-DATE-GRP-X (which has hardcoded '.' FILLER separators) produces final DD.MM.YYYY in HV-PROCTRAN-DATE | WS-U-TIME (ABSTIME) | HV-PROCTRAN-DATE PIC X(10) | WPCD010, lines 613-625 |
| PROCTRAN time field | EXEC CICS FORMATTIME TIME(HV-PROCTRAN-TIME) -- the 6-byte time field HHMMSS is populated directly by FORMATTIME in the same ASKTIME/FORMATTIME call used for the date; no manual STRING assembly | WS-U-TIME (ABSTIME) | HV-PROCTRAN-TIME PIC X(6) | WPCD010, lines 617-622 |
| ABEND time assembly (defect) | STRING concatenation of HH:MM:MM into ABND-TIME -- the seconds field incorrectly reuses WS-TIME-NOW-GRP-MM (minutes) instead of WS-TIME-NOW-GRP-SS. This is a source code bug present in all three ABEND error paths (DCV010 READ failure, DCV010 DELETE failure, WPCD010 INSERT failure). | WS-TIME-NOW-GRP-HH, WS-TIME-NOW-GRP-MM | ABND-TIME | DCV010 lines 413-418, 539-545; WPCD010 lines 689-694 |

## Error Handling

| Condition                                                          | Action                                                                              | Return Code / ABEND Code | Source Location        |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------------------- | ------------------------ | ---------------------- |
| INQCUST returns failure (customer not found or other error)        | Set COMM-DEL-SUCCESS='N', copy fail code to COMM-DEL-FAIL-CD, EXEC CICS RETURN     | Propagates INQCUST-INQ-FAIL-CD | A010, lines 264-269 |
| CICS READ CUSTOMER returns SYSIDERR                                | Retry loop up to 100 times with 3-second delay between each attempt               | (retry -- no abend yet)  | DCV010, lines 362-382  |
| CICS READ CUSTOMER returns NOTFND                                  | Silent skip: GO TO DCV999 (treat as concurrent deletion -- continue normally)      | No error returned        | DCV010, lines 384-389  |
| CICS READ CUSTOMER returns any other non-NORMAL response           | LINK to ABNDPROC with full diagnostic context; DISPLAY message; EXEC CICS ABEND   | ABCODE 'WPV6'            | DCV010, lines 391-452  |
| CICS DELETE CUSTOMER returns SYSIDERR                              | Retry loop up to 100 times with 3-second delay between each attempt               | (retry -- no abend yet)  | DCV010, lines 498-515  |
| CICS DELETE CUSTOMER returns any non-NORMAL response               | LINK to ABNDPROC with full diagnostic context; DISPLAY message; EXEC CICS ABEND   | ABCODE 'WPV7'            | DCV010, lines 517-578  |
| DB2 INSERT to PROCTRAN fails (SQLCODE NOT = 0)                    | LINK to ABNDPROC with SQLCODE and HOST-PROCTRAN-ROW in diagnostic; EXEC CICS ABEND NODUMP | ABCODE 'HWPT'     | WPCD010, lines 666-731 |
| Abend diagnostic message for READ failure                          | 'DCV010 - Unable to READ CUSTOMER VSAM rec for key: ... EIBRESP=... RESP2=...'    | Stored in ABND-FREEFORM  | DCV010, lines 429-437  |
| Abend diagnostic message for DELETE failure                        | 'DCV010(2) - Unbale to DELETE CUSTOMER VSAM rec for key: ... EIBRESP=... RESP2=...' (note: typo 'Unbale' in source) | Stored in ABND-FREEFORM | DCV010, lines 555-563 |
| Abend diagnostic message for PROCTRAN INSERT failure               | 'WPCD010 - Unable to WRITE to PROCTRAN DB2 datastore with the following data: ... EIBRESP=... RESP2=...' | Stored in ABND-FREEFORM | WPCD010, lines 705-715 |
| PROCTRAN ABEND uses NODUMP; CUSTOMER ABENDs do not                 | EXEC CICS ABEND ABCODE('HWPT') NODUMP -- suppresses system dump for DB2 errors; READ and DELETE CUSTOMER ABENDs do not include NODUMP and will produce a dump | ABCODE 'HWPT' NODUMP vs 'WPV6'/'WPV7' with dump | WPCD010 line 726-729 vs DCV010 lines 448-450, 574-576 |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. A010 (main entry) -- set up sort code and customer key from DFHCOMMAREA; initialize INQCUST commarea
2. EXEC CICS LINK PROGRAM('INQCUST ') -- verify the customer exists; if INQCUST returns failure, return immediately to caller with COMM-DEL-SUCCESS='N'
3. PERFORM GET-ACCOUNTS (GAC010) -- SET PCB pointer from DELACC-COMM-PCB1 into INQACCCU commarea; EXEC CICS LINK PROGRAM('INQACCCU') with SYNCONRETURN; loads up to 20 accounts into INQACCCU-COMMAREA array
4. IF NUMBER-OF-ACCOUNTS > 0: PERFORM DELETE-ACCOUNTS (DA010) -- loop VARYING WS-INDEX 1 to NUMBER-OF-ACCOUNTS: EXEC CICS LINK PROGRAM('DELACC  ') for each account
5. PERFORM DEL-CUST-VSAM (DCV010) -- READ CUSTOMER with UPDATE lock; store customer details in working storage and COMMAREA; DELETE CUSTOMER using token; PERFORM WRITE-PROCTRAN-CUST
6. WRITE-PROCTRAN-CUST (WPC010) -- delegates to WRITE-PROCTRAN-CUST-DB2 (WPCD010)
7. WRITE-PROCTRAN-CUST-DB2 (WPCD010) -- populate HOST-PROCTRAN-ROW fields; get timestamp via ASKTIME/FORMATTIME; EXEC SQL INSERT INTO PROCTRAN with transaction type 'ODC' (Online Delete Customer) and amount 0
8. MOVE 'Y' TO COMM-DEL-SUCCESS -- signal success to caller
9. PERFORM GET-ME-OUT-OF-HERE (GMOFH010) -- GOBACK

**POPULATE-TIME-DATE (PTD010):** utility paragraph called from error-handling paths; EXEC CICS ASKTIME then FORMATTIME DDMMYYYY with DATESEP (no explicit separator argument -- uses CICS default). Used to populate ABND-DATE and ABND-TIME fields in the ABNDINFO-REC before linking to ABNDPROC. Note: the PROCTRAN path (WPCD010) calls ASKTIME/FORMATTIME directly with DATESEP('.') rather than calling PTD010.

**Data integrity notes:**
- The CUSTOMER file READ uses `UPDATE` and `TOKEN(WS-TOKEN)` to lock the record. The subsequent DELETE passes the same `TOKEN(WS-TOKEN)`, implementing CICS token-based optimistic locking. No other task can modify the record between the READ and DELETE.
- INQACCCU is called with `SYNCONRETURN`, meaning a syncpoint is taken when that program returns. This commits any prior work done by INQACCCU before DELCUS continues.
- By design, any failure after deletions have started causes an ABEND (no rollback or compensating logic). The comment in the source states: "if there is a failure at any time after we have started to delete things then abend (or else the records will be out of step)".
- The one exception: NOTFND on the CUSTOMER READ causes a silent skip (GO TO DCV999) on the assumption that another task concurrently deleted the customer.
- DELCUS does not inspect the return code from EXEC CICS LINK to DELACC. Error handling for account deletion is entirely delegated to the DELACC program.

**Source code defect -- ABEND time string:**
In all three ABEND error-handling paths (DCV010 READ failure at lines 413-418, DCV010 DELETE failure at lines 539-545, and WPCD010 INSERT failure at lines 689-694), the STRING statement that builds ABND-TIME concatenates HH:MM:MM instead of HH:MM:SS. The last two fields both reference `WS-TIME-NOW-GRP-MM` (minutes); the seconds field `WS-TIME-NOW-GRP-SS` is never used. This means the seconds component in all abend timestamps will always display the minutes value.

**Source code defect -- WS-APPLID never populated:**
`WS-APPLID` (PIC X(8), line 165) is moved to `DELACC-COMM-APPLID` on line 309 before each EXEC CICS LINK to DELACC. However, there is no `EXEC CICS ASSIGN APPLID(WS-APPLID)` anywhere in DELCUS -- all three ASSIGN APPLID statements in the program (lines 404, 530, 680) populate `ABND-APPLID` in the abend info record, not `WS-APPLID`. As a result, `DELACC-COMM-APPLID` will always contain spaces or low-values. If DELACC uses the APPLID for routing or logging, it will receive an incorrect value.

**Source code note -- misleading program header comment:**
The program-level comment (lines 9-14) states that DELCUS "writes a PROCTRAN delete account record out for each deleted account." The PROCEDURE DIVISION does not support this: DELCUS only LINKs to DELACC for each account and does not write account-level PROCTRAN records itself. The single EXEC SQL INSERT at WPCD010 writes only one customer-level 'ODC' record. Account-level PROCTRAN writes are the responsibility of DELACC. The header comment is inaccurate.

**Source code note -- DELACC-COMM-PCB2 unused:**
The DELACC commarea definition includes `DELACC-COMM-PCB2 POINTER` (line 213). This field is never populated anywhere in DELCUS. Only `DELACC-COMM-PCB1` is used (read from the commarea and threaded to INQACCCU). PCB2 will always contain a null/uninitialized pointer value.
