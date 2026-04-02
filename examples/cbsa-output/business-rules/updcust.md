---
type: business-rules
program: UPDCUST
program_type: online
status: reviewed
confidence: high
last_pass: 4
calls: []
called_by:
- BNK1DCS
uses_copybooks:
- ABNDINFO
- CUSTOMER
- SORTCODE
- UPDCUST
reads:
- CUSTOMER
writes:
- CUSTOMER
db_tables: []
transactions: []
mq_queues: []
---

# UPDCUST -- Business Rules

## Program Purpose

UPDCUST is a CICS online program that updates an existing customer record in the CUSTOMER VSAM file. It is called by BNK1DCS (the customer update screen handler) with a COMMAREA containing the new customer field values. The program validates the customer's title, then performs a locked READ UPDATE / REWRITE cycle on the CUSTOMER file. Only the customer name and address are updatable fields; date of birth, credit score, and credit score review date are not modified by this program. No PROCTRAN record is written because only a limited set of fields can be changed.

## Input / Output

| Direction | Resource | Type | Description |
| --------- | -------- | ---- | ----------- |
| IN | DFHCOMMAREA | CICS | Input/output COMMAREA (UPDCUST copybook): customer number, sort code, name, address, DOB, credit score, update success/fail fields |
| IN/OUT | CUSTOMER | CICS VSAM FILE | Customer master record read with UPDATE lock and rewritten with new name/address |
| IN | SORTCODE | Copybook constant | Bank sort code used to key the CUSTOMER record lookup |

## Business Rules

### Title Validation

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 1 | Customer title must be a valid value | EVALUATE WS-UNSTR-TITLE (first word of COMM-NAME) against allowed list | If title not in valid list, set COMM-UPD-SUCCESS = 'N', COMM-UPD-FAIL-CD = 'T', GOBACK immediately | A010, lines 153-195 |
| 2 | Valid title: Professor | WS-UNSTR-TITLE = 'Professor' | WS-TITLE-VALID = 'Y' | A010, line 154 |
| 3 | Valid title: Mr | WS-UNSTR-TITLE = 'Mr       ' (padded to 9 chars) | WS-TITLE-VALID = 'Y' | A010, line 157 |
| 4 | Valid title: Mrs | WS-UNSTR-TITLE = 'Mrs      ' (padded) | WS-TITLE-VALID = 'Y' | A010, line 160 |
| 5 | Valid title: Miss | WS-UNSTR-TITLE = 'Miss     ' (padded) | WS-TITLE-VALID = 'Y' | A010, line 163 |
| 6 | Valid title: Ms | WS-UNSTR-TITLE = 'Ms       ' (padded) | WS-TITLE-VALID = 'Y' | A010, line 166 |
| 7 | Valid title: Dr | WS-UNSTR-TITLE = 'Dr       ' (padded) | WS-TITLE-VALID = 'Y' | A010, line 169 |
| 8 | Valid title: Drs | WS-UNSTR-TITLE = 'Drs      ' (padded) | WS-TITLE-VALID = 'Y' | A010, line 172 |
| 9 | Valid title: Lord | WS-UNSTR-TITLE = 'Lord     ' (padded) | WS-TITLE-VALID = 'Y' | A010, line 175 |
| 10 | Valid title: Sir | WS-UNSTR-TITLE = 'Sir      ' (padded) | WS-TITLE-VALID = 'Y' | A010, line 178 |
| 11 | Valid title: Lady | WS-UNSTR-TITLE = 'Lady     ' (padded) | WS-TITLE-VALID = 'Y' | A010, line 181 |
| 12 | Valid title: blank/spaces (no title present) | WS-UNSTR-TITLE = '         ' (9 spaces) | WS-TITLE-VALID = 'Y' | A010, line 184 |
| 13 | Invalid title (any other value) | WHEN OTHER | WS-TITLE-VALID = 'N' | A010, line 187-188 |
| 14 | Title validation failure -- early exit | WS-TITLE-VALID = 'N' | COMM-UPD-SUCCESS = 'N', COMM-UPD-FAIL-CD = 'T', GOBACK (no VSAM I/O performed) | A010, lines 191-195 |

### Name and Address Presence Check

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 15 | Both name and address empty -- reject | (COMM-NAME = SPACES OR COMM-NAME(1:1) = ' ') AND (COMM-ADDR = SPACES OR COMM-ADDR(1:1) = ' ') | COMM-UPD-SUCCESS = 'N', COMM-UPD-FAIL-CD = '4', GO TO UCV999 (no rewrite) | UCV010, lines 262-270 |
| 16 | Name empty, address supplied -- address-only update | (COMM-NAME = SPACES OR COMM-NAME(1:1) = ' ') AND (COMM-ADDR NOT = SPACES OR COMM-ADDR(1:1) NOT = ' ') | Copy COMM-ADDR to CUSTOMER-ADDRESS only; CUSTOMER-NAME is not changed | UCV010, lines 272-275 |
| 17 | Address empty, name supplied -- name-only update | (COMM-ADDR = SPACES OR COMM-ADDR(1:1) = ' ') AND (COMM-NAME NOT = SPACES OR COMM-NAME(1:1) NOT = ' ') | Copy COMM-NAME to CUSTOMER-NAME only; CUSTOMER-ADDRESS is not changed | UCV010, lines 277-280 |
| 18 | Both name and address supplied -- full update | COMM-ADDR(1:1) NOT = ' ' AND COMM-NAME(1:1) NOT = ' ' | Copy COMM-ADDR to CUSTOMER-ADDRESS and COMM-NAME to CUSTOMER-NAME | UCV010, lines 282-285 |

### Fields Not Updatable

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 19 | Date of birth is read-only | No condition -- COMM-DOB is never written back to the VSAM record | CUSTOMER-DATE-OF-BIRTH is not modified by this program; comment states only limited fields are changeable | Program header comment, lines 17-18 |
| 20 | Credit score is read-only | No condition -- COMM-CREDIT-SCORE is never written back | CUSTOMER-CREDIT-SCORE is not modified; value is echoed back from the VSAM record after the rewrite | Program header comment; UCV010 lines 316-333 |
| 21 | Credit score review date is read-only | No condition | CUSTOMER-CS-REVIEW-DATE is not modified; value is echoed back after rewrite | UCV010, lines 330-331 |
| 22 | Sort code is derived from system constant, not caller | SORTCODE copybook constant is moved to COMM-SCODE and DESIRED-SORT-CODE at entry | Caller's COMM-SCODE value is overridden; caller cannot specify a different sort code | A010, lines 140-141 |

### VSAM Record Lock and Update

| # | Rule | Condition | Action | Source Location |
| --- | --- | --- | --- | --- |
| 23 | Customer record must exist in VSAM | EXEC CICS READ FILE('CUSTOMER') ... UPDATE -- record keyed by DESIRED-SORT-CODE + DESIRED-CUSTNO | If DFHRESP(NOTFND): COMM-UPD-SUCCESS = 'N', COMM-UPD-FAIL-CD = '1', GO TO UCV999 | UCV010, lines 220-243 |
| 24 | VSAM READ UPDATE acquires exclusive lock | READ issued with UPDATE keyword | Record is locked for update; no other task can modify it until REWRITE or UNLOCK | UCV010, lines 220-226 |
| 25 | Any non-NOTFND READ failure | WS-CICS-RESP NOT = DFHRESP(NORMAL) AND NOT DFHRESP(NOTFND) | COMM-UPD-SUCCESS = 'N', COMM-UPD-FAIL-CD = '2', GO TO UCV999 | UCV010, lines 238-243 |
| 26 | REWRITE failure | WS-CICS-RESP NOT = DFHRESP(NORMAL) after EXEC CICS REWRITE | COMM-UPD-SUCCESS = 'N', COMM-UPD-FAIL-CD = '3', GO TO UCV999 | UCV010, lines 306-310 |
| 27 | Successful update | EXEC CICS REWRITE completes with DFHRESP(NORMAL) | All customer fields echoed back to COMMAREA; COMM-UPD-SUCCESS = 'Y' | UCV010, lines 316-333 |

## Calculations

| Calculation | Formula / Logic | Input Fields | Output Field | Source Location |
| --- | --- | --- | --- | --- |
| Customer record length | COMPUTE WS-CUST-REC-LEN = LENGTH OF WS-CUST-DATA | WS-CUST-DATA (01 group) | WS-CUST-REC-LEN (PIC S9(4) COMP) | UCV010, line 292 |
| Title extraction | UNSTRING COMM-NAME DELIMITED BY SPACE INTO WS-UNSTR-TITLE | COMM-NAME (PIC X(60)) | WS-UNSTR-TITLE (PIC X(9)) -- first space-delimited word = title token | A010, lines 148-149 |

## Error Handling

| Condition | Action | Return Code | Source Location |
| --- | --- | --- | --- |
| Title not in valid list | COMM-UPD-SUCCESS = 'N', COMM-UPD-FAIL-CD = 'T', GOBACK | COMM-UPD-FAIL-CD = 'T' | A010, lines 191-195 |
| VSAM READ -- customer not found (DFHRESP NOTFND) | COMM-UPD-SUCCESS = 'N', COMM-UPD-FAIL-CD = '1', GO TO UCV999 | COMM-UPD-FAIL-CD = '1' | UCV010, lines 236-237 |
| VSAM READ -- other CICS error | COMM-UPD-SUCCESS = 'N', COMM-UPD-FAIL-CD = '2', GO TO UCV999 | COMM-UPD-FAIL-CD = '2' | UCV010, lines 238-243 |
| Both name and address empty in COMMAREA | COMM-UPD-SUCCESS = 'N', COMM-UPD-FAIL-CD = '4', GO TO UCV999 (VSAM lock released via UCV999 EXIT without REWRITE -- note: implicit UNLOCK on task end) | COMM-UPD-FAIL-CD = '4' | UCV010, lines 264-268 |
| VSAM REWRITE fails | COMM-UPD-SUCCESS = 'N', COMM-UPD-FAIL-CD = '3', GO TO UCV999 | COMM-UPD-FAIL-CD = '3' | UCV010, lines 306-310 |
| Successful update | COMM-UPD-SUCCESS = 'Y', all customer fields echoed in COMMAREA | COMM-UPD-SUCCESS = 'Y' | UCV010, lines 333 |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. A010 (PREMIERE SECTION) -- Entry point: moves SORTCODE constant to COMM-SCODE and DESIRED-SORT-CODE; extracts title from COMM-NAME via UNSTRING; validates title against EVALUATE; exits with GOBACK if title invalid
2. PERFORM UPDATE-CUSTOMER-VSAM (UCV010) -- Reads CUSTOMER VSAM record with UPDATE lock keyed by sort code + customer number; enforces name/address presence rules; conditionally updates name and/or address fields; computes record length; REWRITEs the record; echoes result fields back to COMMAREA
3. PERFORM GET-ME-OUT-OF-HERE (GMOOH010) -- Issues EXEC CICS RETURN to return control to CICS; program terminates
4. POPULATE-TIME-DATE (PTD010) -- Utility section that obtains current date/time via EXEC CICS ASKTIME / FORMATTIME; defined but NOT called from the main flow in this program (dead code in current version)

### Failure Code Summary

| COMM-UPD-FAIL-CD | Meaning |
| --- | --- |
| 'T' | Invalid customer title |
| '1' | Customer record not found in VSAM |
| '2' | VSAM READ error (non-NOTFND) |
| '3' | VSAM REWRITE error |
| '4' | Both name and address are blank/empty in COMMAREA |

### Data Integrity Note

The program uses a CICS READ ... UPDATE / REWRITE pattern, which holds an exclusive record lock on the CUSTOMER record between the READ and the REWRITE. If the validation at lines 262-270 (both name and address empty) causes a GO TO UCV999 exit before the REWRITE is issued, the UPDATE lock is held until CICS releases it at task end (via the EXEC CICS RETURN in GMOOH010). There is no explicit EXEC CICS UNLOCK issued in the failure path.

### Dead Code Note

Four WORKING-STORAGE items are defined but never referenced in the PROCEDURE DIVISION:

- `WS-ABEND-PGM PIC X(8) VALUE 'ABNDPROC'` (line 127) -- the abend handler program name literal is unused; no CALL to ABNDPROC exists in this program
- `ABNDINFO-REC` (lines 129-130, COPY ABNDINFO) -- the abend information record structure is populated in other CBSA programs but is not read or written here
- `SYSIDERR-RETRY PIC 999` (line 47) -- a counter variable, likely for SYSIDERR retry loop logic; no retry loop exists in UPDCUST's PROCEDURE DIVISION
- `STORM-DRAIN-CONDITION PIC X(20)` (line 115) -- a diagnostic/flow-control label variable present in other CBSA programs; not read or set anywhere in this program

The ABNDINFO copybook appears in `uses_copybooks` because it is COPYed into WORKING-STORAGE, but it has no runtime effect in UPDCUST. The SYSIDERR-RETRY and STORM-DRAIN-CONDITION variables, together with WS-ABEND-PGM and ABNDINFO-REC, are consistent with a copy-paste template pattern used across the CBSA suite where error-handling and retry boilerplate is included but not wired up in every program.

There are also two commented-out MOVE statements at lines 288-289 that represent the original unconditional name/address update logic, replaced by the conditional logic at lines 262-285:

```
*     MOVE COMM-NAME TO CUSTOMER-NAME OF WS-CUST-DATA.
*     MOVE COMM-ADDR TO CUSTOMER-ADDRESS OF WS-CUST-DATA.
```

These confirm that the partial-update capability (address-only or name-only) was a deliberate enhancement over an earlier version that always overwrote both fields.
