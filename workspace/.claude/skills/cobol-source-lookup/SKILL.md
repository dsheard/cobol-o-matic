---
name: cobol-source-lookup
description: >-
  Find factual metadata in COBOL source files including transaction IDs,
  file/dataset names, copybook references, CALL targets, XCTL targets,
  and record layouts. Use when extracting program dependencies, building
  frontmatter, or looking up COBOL naming conventions.
---

# COBOL Source Lookup Recipes

Use these recipes to find factual metadata in COBOL source. Each recipe
gives the grep pattern, where to look, and common pitfalls.

## Transaction ID

The transaction ID is the 4-character identifier for the program (CICS or IMS).

**Where to look:**

1. Any variable with TRANID or TRANSID in its name, with a VALUE clause in WORKING-STORAGE:

   ```
   Grep pattern: "TRANID|TRANSID" on the source file
   ```

   The VALUE clause contains the actual transaction ID (e.g., `VALUE 'XXXX'`).
   Common names: `LIT-THISTRANID`, `WS-TRANID`, `LIT-TRANID`, `WS-TRANSACTION-ID`.

2. `EXEC CICS RETURN TRANSID(x)` in PROCEDURE DIVISION:

   ```
   Grep pattern: "RETURN.*TRANSID" on the source file
   ```

   Resolve the variable `x` by looking up its VALUE in DATA DIVISION.

3. CSD definition files (`.csd`):
   ```
   Grep pattern: "DEFINE TRANSACTION" in CSD files
   ```
   Maps transaction ID to program name authoritatively.

**Pitfalls:**

- Do NOT infer transaction ID from SEND MAP or RECEIVE MAP -- those are screen operations, not transaction identifiers.
- Some programs reference multiple transaction IDs (e.g., menu programs that START other transactions). The program's OWN transaction ID is typically in a variable with "THIS" in the name (e.g., `LIT-THISTRANID`).
- Variables like `*NEXTTRANID` or `*RETURNTRANID` are NOT this program's transaction -- they reference the next program to invoke.

## File / Dataset Names

**CICS programs:**

```
Grep pattern: "EXEC CICS.*(READ|WRITE|REWRITE|DELETE)" on the source file
```

Then find `FILE(x)` or `DATASET(x)` in the same EXEC CICS block. Resolve `x`
against DATA DIVISION if it's a variable name (e.g., `FILE(LIT-ACCTFILENAME)` --
look up `LIT-ACCTFILENAME` VALUE to get `ACCTDAT`).

**Batch programs:**

```
Grep pattern: "OPEN (INPUT|OUTPUT|I-O|EXTEND)" on the source file
```

The file name follows the OPEN keyword. Cross-reference with `SELECT ... ASSIGN TO`
in ENVIRONMENT DIVISION for physical file mapping.

**Pitfalls:**

- VALUE clauses defining file names do NOT prove the file is accessed. Verify the
  literal appears in an actual I/O statement (READ/WRITE/OPEN/EXEC CICS).
- Programs may define file name literals they never use (dead code).

## Copybooks

```
Grep pattern: "COPY " on the source file
```

Syntaxes to match:

- `COPY COPYNAME.` (unquoted, most common)
- `COPY 'COPYNAME'` (single-quoted)
- `EXEC SQL INCLUDE COPYNAME END-EXEC` (DB2 includes)

**Pitfalls:**

- COPY statements can appear in any division, not just DATA DIVISION.
- System copybooks (DFHAID, DFHBMSCA, SQLCA) are standard IBM includes -- exclude from
  application-specific copybook lists unless specifically relevant.

## CALL / XCTL Targets

**Static CALL:**

```
Grep pattern: "CALL '" on the source file
```

Extracts `CALL 'PROGNAME'` with the literal program name.

**Dynamic CALL:**

```
Grep pattern: "CALL " on the source file
```

Look for `CALL variable-name` where variable-name is a data item. Resolve its VALUE
in DATA DIVISION. Common pattern: `MOVE 'PROGNAME' TO WS-PROG-NAME` followed by
`CALL WS-PROG-NAME`.

**CICS XCTL:**

```
Grep pattern: "XCTL" on the source file
```

Extracts `EXEC CICS XCTL PROGRAM(x)`. Resolve `x` if it's a variable.

**CICS LINK:**

```
Grep pattern: "EXEC CICS LINK" on the source file
```

Same resolution logic as XCTL but the call returns to the caller.

## Menu Navigation

Menu programs often use copybooks containing program name and transaction ID
tables that define the application's navigation structure. Look for copybooks
referenced from menu/navigation paragraphs:

```
Grep pattern: "COPY " on the menu program source file
```

Cross-reference the included copybooks for arrays of program names and
transaction IDs.

## Record Lengths

To compute record length from PIC clauses:

| PIC Type                            | Bytes                                      |
| ----------------------------------- | ------------------------------------------ |
| `X(n)`                              | n                                          |
| `9(n)` DISPLAY                      | n                                          |
| `9(n)` COMP-3 / PACKED-DECIMAL      | ceil((n+1)/2)                              |
| `9(n)` COMP / BINARY (1-4 digits)   | 2                                          |
| `9(n)` COMP / BINARY (5-9 digits)   | 4                                          |
| `9(n)` COMP / BINARY (10-18 digits) | 8                                          |
| `S9(n)`                             | same as unsigned + sign handling per USAGE |

**Pitfalls:**

- REDEFINES does NOT add bytes -- it overlays the same storage.
- OCCURS adds bytes: `OCCURS 10 TIMES` multiplies the item's length by 10.
- Group items are the sum of their children (no padding unless SYNCHRONIZED).

## COBOL Naming Conventions

| Prefix/Pattern              | Meaning                                       |
| --------------------------- | --------------------------------------------- |
| `LIT-*`                     | Literal constants in WORKING-STORAGE          |
| `WS-*`                      | Working storage variables                     |
| `FLG-*` or 88-levels        | Boolean flags                                 |
| `*-EXIT`                    | PERFORM THRU exit paragraphs                  |
| `-N` suffix                 | Numeric redefine of alphanumeric field        |
| `*TRANID` / `*TRANSID`     | Transaction ID variables                      |
| `*THISPGM` / `*THISPROG`   | This program's name                           |
| `*FILENAME` / `*FILNAM`    | File/dataset name constants                   |
| `*PGM` / `*PROG` (in LIT-) | Program name constants                        |

Note: COMMAREA field prefixes are application-specific (e.g., some apps use
`CDEMO-*`, others use `COMM-*` or `CA-*`). Check the application's copybooks
to identify the convention in use.
