---
type: business-rules
program: GETCOMPY
program_type: online
status: draft
confidence: high
last_pass: 5
calls: []
called_by: []
uses_copybooks:
- GETCOMPY
reads: []
writes: []
db_tables: []
transactions: []
mq_queues: []
---

# GETCOMPY -- Business Rules

## Program Purpose

GETCOMPY is a minimal CICS service program that returns the application company name to any caller via DFHCOMMAREA. It accepts a COMMAREA containing a 40-character `company-name` field (defined in copybook GETCOMPY under group `GETCompanyOperation`), populates it with the literal string `'CICS Bank Sample Application'`, and immediately returns control to CICS. The program performs no validation, no database access, and no file I/O. Its sole purpose is to provide a central, updateable source of truth for the application name used by other programs.

The program is invoked via EXEC CICS LINK from the Java web UI layer (`CompanyNameResource.java` in the CBSA web application). No COBOL programs in the source base call GETCOMPY directly.

## Input / Output

| Direction | Resource     | Type  | Description                                                                               |
| --------- | ------------ | ----- | ----------------------------------------------------------------------------------------- |
| IN/OUT    | DFHCOMMAREA  | CICS  | Communication area containing `company-name` PIC X(40) (group `GETCompanyOperation`); field is populated on return |

## Business Rules

### Company Name Assignment

| #   | Rule                       | Condition          | Action                                                                                    | Source Location |
| --- | -------------------------- | ------------------ | ----------------------------------------------------------------------------------------- | --------------- |
| 1   | Populate company name      | Unconditional      | MOVE `'CICS Bank Sample Application'` TO `company-name` (DFHCOMMAREA field, PIC X(40))   | A010 (line 38)  |
| 2   | Return to caller           | Unconditional      | EXEC CICS RETURN -- passes the populated COMMAREA back to the calling program             | A010 (line 40)  |

## Calculations

| Calculation | Formula / Logic              | Input Fields | Output Field | Source Location |
| ----------- | ---------------------------- | ------------ | ------------ | --------------- |
| None        | No calculations performed    | N/A          | N/A          | N/A             |

## Error Handling

| Condition | Action                                                                                    | Return Code | Source Location |
| --------- | ----------------------------------------------------------------------------------------- | ----------- | --------------- |
| None      | No error handling present; program assumes EXEC CICS RETURN will always succeed           | N/A         | A010            |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. **A010** (PREMIERE SECTION) -- Entry point. Moves the literal company name `'CICS Bank Sample Application'` into the `company-name` field of DFHCOMMAREA.
2. **EXEC CICS RETURN** -- Returns control to CICS, passing the populated COMMAREA back to the calling program. No explicit COMMAREA or TRANSID parameters are coded; the COMMAREA is passed implicitly.
3. **GOBACK** -- Unreachable dead code following the CICS RETURN; acts as a program terminator safety net.

## Notes

- **COMMAREA field hierarchy**: The DFHCOMMAREA is structured as `01 DFHCOMMAREA / 03 GETCompanyOperation / 06 company-name PIC X(40)`. The MOVE statement references `company-name` directly by its level-06 name.
- **Caller**: GETCOMPY is linked to from the Java web UI layer via EXEC CICS LINK (`CompanyNameResource.java`). No COBOL callers exist in the CBSA source base; `called_by` remains empty.
- **Literal value**: The company name literal is exactly 30 characters: `'CICS Bank Sample Application'`. It is stored in a 40-character field, so it will be padded with 10 trailing spaces on return.
- **CBL option**: Compiled with `CICS('SP,EDF')` -- SP enables structured programming checks; EDF enables the Execution Diagnostic Facility for debugging.
- **PROCEDURE DIVISION USING**: The program is declared as `PROCEDURE DIVISION USING DFHCOMMAREA`, making the COMMAREA explicitly addressable by name within the program.
