---
type: business-rules
program: GETSCODE
program_type: online
status: draft
confidence: high
last_pass: 4
calls: []
called_by: []
uses_copybooks:
- GETSCODE
- SORTCODE
reads: []
writes: []
db_tables: []
transactions: []
mq_queues: []
---

# GETSCODE -- Business Rules

## Program Purpose

GETSCODE is a minimal CICS utility subprogram whose sole responsibility is to return the bank's configured sort code to its caller. It accepts a DFHCOMMAREA structured as the GETSCODE copybook (a single 6-character field named SORTCODE), moves the hard-coded literal sort code value (987654, defined in the SORTCODE copybook as `77 SORTCODE PIC 9(6) VALUE 987654`) into that field, and immediately issues EXEC CICS RETURN. There is no input validation, no file or database I/O, and no branching logic. The sort code is a compile-time constant; changing it requires recompiling the program.

Note: GETSCODE is invoked from outside the COBOL tier -- `SortCodeResource.java` calls it via the JCICS `Program` API. There are no COBOL programs in the codebase that CALL GETSCODE directly.

## Input / Output

| Direction | Resource       | Type | Description                                                                                  |
| --------- | -------------- | ---- | -------------------------------------------------------------------------------------------- |
| IN        | DFHCOMMAREA    | CICS | Caller passes a COMMAREA laid out per GETSCODE.cpy; the SORTCODE field is the only member.  |
| OUT       | DFHCOMMAREA    | CICS | On return, SORTCODE (PIC X(6)) is populated with the literal value `987654`.                |

## Business Rules

### Sort Code Provisioning

| #  | Rule                      | Condition                      | Action                                                                                                                          | Source Location     |
| -- | ------------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| 1  | Return configured sort code | Always (unconditional)        | MOVE `LITERAL-SORTCODE` (resolved from `SORTCODE.cpy`: `77 SORTCODE PIC 9(6) VALUE 987654`) TO `SORTCODE OF DFHCOMMAREA`.     | A010                |
| 2  | Immediate CICS return      | Always (unconditional)        | EXEC CICS RETURN -- control passes back to the invoking task immediately after populating the sort code; no further processing. | A010                |

**Note on the REPLACING clause:** The COPY of SORTCODE.cpy uses `REPLACING ==SORTCODE== BY ==LITERAL-SORTCODE==`. This renames the standalone level-77 item from `SORTCODE` to `LITERAL-SORTCODE` in WORKING-STORAGE, avoiding a name clash with the `SORTCODE` field inside DFHCOMMAREA (from GETSCODE.cpy). At runtime `LITERAL-SORTCODE` holds the value `987654`.

**Note on DFHCOMMAREA layout:** GETSCODE.cpy defines `03 GETSORTCODEOperation` as a group item, with `06 SORTCODE PIC X(6)` as its only child. The MOVE is qualified as `SORTCODE OF DFHCOMMAREA` to resolve this hierarchy unambiguously.

## Calculations

| Calculation | Formula / Logic               | Input Fields        | Output Field              | Source Location |
| ----------- | ----------------------------- | ------------------- | ------------------------- | --------------- |
| Sort code assignment | Simple MOVE; no arithmetic | `LITERAL-SORTCODE` (compile-time constant `987654`, PIC 9(6)) | `SORTCODE OF DFHCOMMAREA` (PIC X(6)) | A010 |

## Error Handling

| Condition         | Action                     | Return Code | Source Location |
| ----------------- | -------------------------- | ----------- | --------------- |
| None defined      | No error checks are coded. CICS RETURN is unconditional; no RESP/RESP2 handling, no file-status checks, no SQLCODE tests, no ABEND calls. | N/A | A010 |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. **PREMIERE SECTION / A010** -- entry point; the only paragraph in the program.
2. MOVE `LITERAL-SORTCODE` TO `SORTCODE OF DFHCOMMAREA` -- populates the single output field with the hard-coded sort code `987654`.
3. EXEC CICS RETURN -- returns control to CICS; the GOBACK that follows is unreachable dead code included as a structural safety net.
