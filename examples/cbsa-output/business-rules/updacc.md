---
type: business-rules
program: UPDACC
program_type: online
status: draft
confidence: high
last_pass: 5
calls: []
called_by:
- BNK1UAC
uses_copybooks:
- ABNDINFO
- ACCDB2
- ACCOUNT
- SORTCODE
- UPDACC
reads: []
writes: []
db_tables:
- ACCOUNT
transactions: []
mq_queues: []
---

# UPDACC -- Business Rules

## Program Purpose

UPDACC updates a limited set of fields on an existing Account record in the DB2 ACCOUNT table. It is called by BNK1UAC (the BMS update-account screen handler) and by REST API consumers. The only fields that may be changed are Account Type, Interest Rate, and Overdraft Limit. The balance (available and actual) cannot be amended via this program; no transaction record is written to PROCTRAN as a result. The program receives the full COMMAREA from the caller, selects the current account row to verify it exists, applies the three mutable fields, and returns a success/failure flag in COMM-SUCCESS.

**Note on program header comment vs. active code:** The program header comment (lines 22-28) states that "the last and next statement dates" can also be amended. However the active UPDATE SQL (lines 278-285) does NOT update statement dates; only ACCOUNT_TYPE, ACCOUNT_INTEREST_RATE, and ACCOUNT_OVERDRAFT_LIMIT are written. The header comment is inaccurate with respect to the current implementation.

## Input / Output

| Direction | Resource                 | Type | Description                                                                 |
| --------- | ------------------------ | ---- | --------------------------------------------------------------------------- |
| IN        | DFHCOMMAREA (UPDACC.cpy) | CICS | Full account record passed by the caller; key fields COMM-ACCNO, COMM-SCODE |
| IN/OUT    | ACCOUNT (DB2)            | DB   | Account table: read then updated within same task                           |
| OUT       | DFHCOMMAREA (UPDACC.cpy) | CICS | Updated account data returned to caller; COMM-SUCCESS = 'Y' or 'N'          |

## Business Rules

### Input Validation

| #   | Rule                              | Condition                                                                   | Action                                                                        | Source Location          |
| --- | --------------------------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------ |
| 1   | Account type must not be blank    | `IF (COMM-ACC-TYPE = SPACES OR COMM-ACC-TYPE(1:1) = ' ')`                   | Set COMM-SUCCESS = 'N', DISPLAY error message, branch to UAD999 (exit)       | UAD010 (line 267--272)   |

**Note:** The program comment (lines 240--265) explicitly documents that validation of interest rate and overdraft limit is delegated to the presentation layer (BNK1UAC / Customer Service interface). UPDACC itself only enforces the account type non-blank rule. An API caller that passes zero values for interest rate or overdraft limit while supplying a valid account type will have those zeros written to the database -- this is a documented design limitation.

### Account Lookup

| #   | Rule                         | Condition                         | Action                                                                    | Source Location        |
| --- | ---------------------------- | --------------------------------- | -------------------------------------------------------------------------- | ---------------------- |
| 2   | Account must exist in DB2    | `IF SQLCODE NOT = 0` after SELECT | Set COMM-SUCCESS = 'N', display SQLCODE, branch to UAD999 (bypass UPDATE) | UAD010 (line 225--233) |

### Update Application

| #   | Rule                                         | Condition                         | Action                                                                                                                                                                                                                    | Source Location         |
| --- | -------------------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| 3   | Only three fields are updated                | After successful SELECT           | Only ACCOUNT_TYPE, ACCOUNT_INTEREST_RATE, ACCOUNT_OVERDRAFT_LIMIT are written; balance, last-statement date, and next-statement date are read-only                                                                        | UAD010 (lines 278--285) |
| 4   | Update must succeed                          | `IF SQLCODE NOT = 0` after UPDATE | Set COMM-SUCCESS = 'N', display SQLCODE, branch to UAD999                                                                                                                                                                 | UAD010 (line 290--296)  |
| 5   | COMMAREA fully populated before success flag | SQLCODE = 0 after UPDATE          | All host variable fields are MOVEd back into COMMAREA (lines 302-325), then COMM-SUCCESS = 'Y' is set last (line 327). The success flag is the final write; a caller seeing 'Y' is guaranteed a fully populated COMMAREA. | UAD010 (lines 302--327) |

### Sort Code Enforcement

| #   | Rule                                          | Condition             | Action                                                                                                          | Source Location       |
| --- | --------------------------------------------- | --------------------- | --------------------------------------------------------------------------------------------------------------- | --------------------- |
| 6   | Sort code is always the installation constant | Unconditional at A010 | SORTCODE (value 987654 from SORTCODE copybook) is moved to COMM-SCODE and DESIRED-SORT-CODE before any DB2 access | A010 (lines 161--162) |

## Calculations

| Calculation              | Formula / Logic                                                                                                                                                                                                                                                                        | Input Fields                              | Output Field                                                                | Source Location         |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | --------------------------------------------------------------------------- | ----------------------- |
| Date format conversion   | DB2 returns dates as YYYY-MM-DD (10-char string). DB2-DATE-REFORMAT (LOCAL-STORAGE, PIC 9(4)/X/99/X/99) is overlaid via MOVE then year/month/day subfields are extracted individually. COMMAREA date fields are PIC 9(8) with REDEFINES laid out as DDMMYYYY (day/month/year packed). The code writes year, month, day components into the REDEFINES subfields, producing a packed DDMMYYYY value in COMM-OPENED, COMM-LAST-STMT-DT, COMM-NEXT-STMT-DT. | HV-ACCOUNT-OPENED, HV-ACCOUNT-LAST-STMT, HV-ACCOUNT-NEXT-STMT | COMM-OPENED (DDMMYYYY), COMM-LAST-STMT-DT (DDMMYYYY), COMM-NEXT-STMT-DT (DDMMYYYY) | UAD010 (lines 308--323) |
| Interest rate type coercion | COMM-INT-RATE is PIC 9(4)V99 (unsigned). HV-ACCOUNT-INT-RATE is PIC S9(4)V99 COMP-3 (signed COMP-3). MOVE on input (line 276) implicitly drops sign; MOVE on output (line 307) converts signed COMP-3 back to unsigned display. Negative interest rates stored in DB2 would be silently sign-stripped on write. | COMM-INT-RATE | HV-ACCOUNT-INT-RATE (write path); COMM-INT-RATE (read-back path) | UAD010 (lines 276, 307) |

No arithmetic computations (COMPUTE/ADD/SUBTRACT/MULTIPLY) are present. Overdraft limit and balance values are passed through unchanged from COMMAREA to host variables (or vice versa).

## Error Handling

| Condition                                  | Action                                                                           | Return Code        | Source Location         |
| ------------------------------------------ | -------------------------------------------------------------------------------- | ------------------ | ------------------------ |
| SELECT returns SQLCODE != 0                | COMM-SUCCESS = 'N'; DISPLAY 'ERROR: UPDACC returned \<sqlcode\> on SELECT'       | COMM-SUCCESS = 'N' | UAD010 (lines 225--232)  |
| COMM-ACC-TYPE is spaces or starts with ' ' | COMM-SUCCESS = 'N'; DISPLAY 'ERROR: UPDACC has invalid account-type'             | COMM-SUCCESS = 'N' | UAD010 (lines 267--271)  |
| UPDATE returns SQLCODE != 0                | COMM-SUCCESS = 'N'; DISPLAY 'ERROR: UPDACC returned \<sqlcode\> on UPDATE'       | COMM-SUCCESS = 'N' | UAD010 (lines 290--295)  |

All three error paths branch to UAD999 (EXIT) immediately, skipping both the COMMAREA population MOVEs and the COMM-SUCCESS = 'Y' assignment. No ABEND is issued and no CICS SYNCPOINT ROLLBACK is performed, meaning a partial DB2 update is not explicitly rolled back -- the task ends normally via EXEC CICS RETURN and CICS will handle any implicit sync-point.

**Dead abend infrastructure:** WS-ABEND-PGM (VALUE 'ABNDPROC') and ABNDINFO-REC (COPY ABNDINFO) are declared in WORKING-STORAGE (lines 148-151) but are never referenced in the PROCEDURE DIVISION. The program was provisioned with abend-handling scaffolding but it was never wired up. Errors are handled solely by setting COMM-SUCCESS = 'N' and returning normally.

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. A010 -- Entry point: move installation sort code (987654) into COMM-SCODE and DESIRED-SORT-CODE
2. PERFORM UPDATE-ACCOUNT-DB2 -- Main work: SELECT existing row, validate account type, UPDATE three fields, populate COMMAREA
3. PERFORM GET-ME-OUT-OF-HERE -- Issues EXEC CICS RETURN to end the task

Paragraphs defined but not called in the active code path:

- POPULATE-TIME-DATE (PTD010/PTD999) -- Defined but never PERFORMed; contains EXEC CICS ASKTIME / FORMATTIME logic (DDMMYYYY format, DATESEP). Likely a remnant from earlier development.

Dead / commented-out code: Lines 338--378 contain a commented-out alternative UPDATE-ACCOUNT-DB2 implementation. The commented-out MOVE statements (lines 344-347) included COMM-LAST-STMT-DT and COMM-NEXT-STMT-DT as inputs to host variables, but the commented-out UPDATE SQL still only updated the same three fields (ACCOUNT_TYPE, ACCOUNT_INTEREST_RATE, ACCOUNT_OVERDRAFT_LIMIT). The statement-date host variable population in the dead block was therefore unused even within that block. The active implementation supersedes it entirely.
