---
type: data
subtype: database-operations
status: draft
confidence: high
last_pass: 2
---

# Database Operations

All database access patterns extracted from EXEC SQL statements and CICS file commands.

---

## DB2 Operations

| Program    | Table    | Operation | Key Columns                              | Host Variables                                                                                                | Cursor      |
| ---------- | -------- | --------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ----------- |
| BANKDATA   | ACCOUNT  | INSERT    | ACCOUNT_SORTCODE, ACCOUNT_NUMBER         | :HV-ACCOUNT-EYECATCHER, :HV-ACCOUNT-CUST-NO, :HV-ACCOUNT-SORT-CODE, :HV-ACCOUNT-NUMBER, :HV-ACCOUNT-TYPE, :HV-ACCOUNT-INTEREST-RATE, :HV-ACCOUNT-OPENED, :HV-ACCOUNT-OVERDRAFT-LIMIT, :HV-ACCOUNT-LAST-STMT-DATE, :HV-ACCOUNT-NEXT-STMT-DATE, :HV-ACCOUNT-AVAILABLE-BALANCE, :HV-ACCOUNT-ACTUAL-BALANCE | --         |
| BANKDATA   | ACCOUNT  | DELETE    | ACCOUNT_SORTCODE                         | :HV-ACCOUNT-SORT-CODE                                                                                         | --          |
| BANKDATA   | CONTROL  | INSERT    | CONTROL_NAME                             | :HV-CONTROL-NAME ('&lt;sortcode&gt;-ACCOUNT-LAST'), :HV-CONTROL-VALUE-NUM (last account number), :HV-CONTROL-VALUE-STR | --   |
| BANKDATA   | CONTROL  | INSERT    | CONTROL_NAME                             | :HV-CONTROL-NAME ('&lt;sortcode&gt;-ACCOUNT-COUNT'), :HV-CONTROL-VALUE-NUM (account count), :HV-CONTROL-VALUE-STR | --    |
| BANKDATA   | CONTROL  | DELETE    | CONTROL_NAME                             | :HV-CONTROL-NAME ('&lt;sortcode&gt;-ACCOUNT-LAST')                                                            | --          |
| BANKDATA   | CONTROL  | DELETE    | CONTROL_NAME                             | :HV-CONTROL-NAME ('&lt;sortcode&gt;-ACCOUNT-COUNT')                                                           | --          |
| BANKDATA   | (commit) | COMMIT WORK | --                                     | -- (every ~1000 ACCOUNT inserts and at end of job)                                                            | --          |
| CREACC     | CONTROL  | SELECT    | CONTROL_NAME                             | :HV-CONTROL-NAME, :HV-CONTROL-VALUE-NUM, :HV-CONTROL-VALUE-STR                                               | --          |
| CREACC     | CONTROL  | UPDATE    | CONTROL_NAME                             | :HV-CONTROL-VALUE-NUM, :HV-CONTROL-NAME                                                                       | --          |
| CREACC     | ACCOUNT  | INSERT    | ACCOUNT_SORTCODE, ACCOUNT_NUMBER         | :HV-ACCOUNT-EYECATCHER, :HV-ACCOUNT-CUST-NO, :HV-ACCOUNT-SORTCODE, :HV-ACCOUNT-ACC-NO, :HV-ACCOUNT-ACC-TYPE, :HV-ACCOUNT-INT-RATE, :HV-ACCOUNT-OPENED, :HV-ACCOUNT-OVERDRAFT-LIM, :HV-ACCOUNT-LAST-STMT, :HV-ACCOUNT-NEXT-STMT, :HV-ACCOUNT-AVAIL-BAL, :HV-ACCOUNT-ACTUAL-BAL | --         |
| CREACC     | PROCTRAN | INSERT    | PROCTRAN_SORTCODE, PROCTRAN_NUMBER       | :HV-PROCTRAN-EYECATCHER, :HV-PROCTRAN-SORT-CODE, :HV-PROCTRAN-ACC-NUMBER, :HV-PROCTRAN-DATE, :HV-PROCTRAN-TIME, :HV-PROCTRAN-REF, :HV-PROCTRAN-TYPE, :HV-PROCTRAN-DESC, :HV-PROCTRAN-AMOUNT | --         |
| CRECUST    | PROCTRAN | INSERT    | PROCTRAN_SORTCODE, PROCTRAN_NUMBER       | :HV-PROCTRAN-EYECATCHER, :HV-PROCTRAN-SORT-CODE, :HV-PROCTRAN-ACC-NUMBER, :HV-PROCTRAN-DATE, :HV-PROCTRAN-TIME, :HV-PROCTRAN-REF, :HV-PROCTRAN-TYPE, :HV-PROCTRAN-DESC, :HV-PROCTRAN-AMOUNT | --         |
| DELACC     | ACCOUNT  | SELECT    | ACCOUNT_SORTCODE, ACCOUNT_NUMBER         | :HV-ACCOUNT-EYECATCHER, :HV-ACCOUNT-CUST-NO, :HV-ACCOUNT-SORTCODE, :HV-ACCOUNT-ACC-NO, all account columns   | --          |
| DELACC     | ACCOUNT  | DELETE    | ACCOUNT_SORTCODE, ACCOUNT_NUMBER         | :HV-ACCOUNT-SORTCODE, :HV-ACCOUNT-ACC-NO                                                                      | --          |
| DELACC     | PROCTRAN | INSERT    | PROCTRAN_SORTCODE, PROCTRAN_NUMBER       | :HV-PROCTRAN-* (all columns)                                                                                   | --          |
| DELCUS     | PROCTRAN | INSERT    | PROCTRAN_SORTCODE, PROCTRAN_NUMBER       | :HV-PROCTRAN-* (all columns)                                                                                   | --          |
| INQACC     | ACCOUNT  | SELECT    | ACCOUNT_SORTCODE, ACCOUNT_NUMBER         | :HV-ACCOUNT-EYECATCHER, :HV-ACCOUNT-CUST-NO, :HV-ACCOUNT-SORTCODE, :HV-ACCOUNT-ACC-NO, all account columns   | ACC-CURSOR  |
| INQACC     | ACCOUNT  | SELECT    | ACCOUNT_SORTCODE, ACCOUNT_NUMBER         | All :HV-ACCOUNT-* columns (singleton SELECT without cursor)                                                   | --          |
| INQACCCU   | ACCOUNT  | SELECT    | ACCOUNT_CUSTOMER_NUMBER, ACCOUNT_SORTCODE| :HV-ACCOUNT-* (all columns via cursor fetch)                                                                  | ACC-CURSOR  |
| DBCRFUN    | ACCOUNT  | SELECT    | ACCOUNT_SORTCODE, ACCOUNT_NUMBER         | :HV-ACCOUNT-* (all columns)                                                                                   | --          |
| DBCRFUN    | ACCOUNT  | UPDATE    | ACCOUNT_SORTCODE, ACCOUNT_NUMBER         | :HV-ACCOUNT-EYECATCHER, :HV-ACCOUNT-CUST-NO, :HV-ACCOUNT-SORTCODE, :HV-ACCOUNT-ACC-NO, :HV-ACCOUNT-AVAILABLE-BALANCE, :HV-ACCOUNT-ACTUAL-BALANCE | --         |
| DBCRFUN    | PROCTRAN | INSERT    | PROCTRAN_SORTCODE, PROCTRAN_NUMBER       | :HV-PROCTRAN-* (all columns)                                                                                   | --          |
| UPDACC     | ACCOUNT  | SELECT    | ACCOUNT_SORTCODE, ACCOUNT_NUMBER         | :HV-ACCOUNT-* (all columns)                                                                                   | --          |
| UPDACC     | ACCOUNT  | UPDATE    | ACCOUNT_SORTCODE, ACCOUNT_NUMBER         | :HV-ACCOUNT-ACC-TYPE, :HV-ACCOUNT-INT-RATE, :HV-ACCOUNT-OVERDRAFT-LIM, :HV-ACCOUNT-AVAIL-BAL, :HV-ACCOUNT-ACTUAL-BAL | --         |
| XFRFUN     | ACCOUNT  | SELECT    | ACCOUNT_SORTCODE, ACCOUNT_NUMBER         | :HV-ACCOUNT-* (all columns; from-account)                                                                     | --          |
| XFRFUN     | ACCOUNT  | UPDATE    | ACCOUNT_SORTCODE, ACCOUNT_NUMBER         | All :HV-ACCOUNT-* (from-account balance update)                                                               | --          |
| XFRFUN     | ACCOUNT  | SELECT    | ACCOUNT_SORTCODE, ACCOUNT_NUMBER         | :HV-ACCOUNT-* (all columns; to-account)                                                                       | --          |
| XFRFUN     | ACCOUNT  | UPDATE    | ACCOUNT_SORTCODE, ACCOUNT_NUMBER         | All :HV-ACCOUNT-* (to-account balance update)                                                                 | --          |
| XFRFUN     | PROCTRAN | INSERT    | PROCTRAN_SORTCODE, PROCTRAN_NUMBER       | :HV-PROCTRAN-* (all columns)                                                                                   | --          |

### Notes on XFRFUN Dynamic SQL

XFRFUN also includes `EXEC SQL INCLUDE SQLDA END-EXEC` (SQL Descriptor Area) and defines `STMTBUF`/`STMTBUF2` (78- and 81-byte VARCHAR buffers) and `WS-WANTED`/`WS-WANTED2` structures, indicating support for dynamic SQL execution. The variable `WS-TESTING-DB-NAME` contains schema prefix `STTESTER.` and table name `PLOP`, suggesting these dynamic SQL paths are test scaffolding and not part of the production data flow.

### Notes on BANKDATA CONTROL Table

BANKDATA inserts exactly two rows into the CONTROL table during initialisation:
- `<sortcode>-ACCOUNT-LAST`: stores the last account number allocated (CONTROL_VALUE_NUM)
- `<sortcode>-ACCOUNT-COUNT`: stores the total number of accounts created (CONTROL_VALUE_NUM)

Both rows are deleted first if they exist, then re-inserted. CREACC subsequently reads and updates the `<sortcode>-ACCOUNT-LAST` row via SELECT and UPDATE to manage account number sequencing when the NCS (Named Counter Service) is unavailable.

---

## IMS/DB Operations

No EXEC DLI or CALL 'CBLTDLI' statements were found in the COBOL source programs. The IMS-related programs (CRDTAGY1-CRDTAGY5) receive IMS PCB pointers through their LINKAGE SECTION and COMMAREA structures (PROCISRT-PCB-POINTER, DELACC-DEL-PCB1/2/3, INQACC-PCB1-POINTER, INQCUST-PCB-POINTER, INQACCCU COMM-PCB-POINTER, UPDCUST/UPDACC), indicating integration points with an IMS environment, but the actual DL/I calls are not present in the source base examined.

| Program  | Segment | Operation | PCB Reference           | SSA Qualifications            |
| -------- | ------- | --------- | ----------------------- | ----------------------------- |
| CRDTAGY1 | (IMS integration point — PCB pointer passed via PROCISRT-COMMAREA; no EXEC DLI observed in source) | -- | PROCISRT-PCB-POINTER | -- |
| CRDTAGY2 | (IMS integration point) | -- | PROCISRT-PCB-POINTER | -- |
| CRDTAGY3 | (IMS integration point) | -- | PROCISRT-PCB-POINTER | -- |
| CRDTAGY4 | (IMS integration point) | -- | PROCISRT-PCB-POINTER | -- |
| CRDTAGY5 | (IMS integration point) | -- | PROCISRT-PCB-POINTER | -- |

---

## Indexed File Operations (CICS VSAM)

| Program  | File Name | Operation           | Key Fields                                 | Access Pattern           |
| -------- | --------- | ------------------- | ------------------------------------------ | ------------------------ |
| BANKDATA | CUSTOMER  | WRITE               | CUSTOMER-KEY (SORTCODE+NUMBER)             | Sequential/Random (batch FD) |
| CRECUST  | CUSTOMER  | WRITE               | CUSTOMER-KEY (RIDFLD)                      | Random                   |
| CRECUST  | CUSTOMER  | READ (UPDATE)       | CUSTOMER-CONTROL-KEY                       | Random (control record)  |
| CRECUST  | CUSTOMER  | REWRITE             | CUSTOMER-CONTROL-KEY                       | Random (control record)  |
| INQCUST  | CUSTOMER  | READ                | CUSTOMER-KY (SORTCODE+NUMBER)              | Random                   |
| INQCUST  | CUSTOMER  | STARTBR             | CUSTOMER-KY2 (partial key browse)          | Sequential browse        |
| INQCUST  | CUSTOMER  | READPREV            | CUSTOMER-KY2                               | Sequential browse (backwards) |
| UPDCUST  | CUSTOMER  | READ (UPDATE)       | DESIRED-CUST-KEY (SORTCODE+NUMBER)         | Random with update lock  |
| UPDCUST  | CUSTOMER  | REWRITE             | (implicit from READ UPDATE)                | Random                   |
| DELCUS   | CUSTOMER  | READ (UPDATE)       | DESIRED-KEY (SORTCODE+NUMBER)              | Random with update lock  |
| DELCUS   | CUSTOMER  | DELETE              | TOKEN (from READ UPDATE)                   | Random                   |
| ABNDPROC | ABNDFILE  | WRITE               | ABND-VSAM-KEY (UTIME+TASKNO)               | Random                   |

---

## Cursors and Batch Access

| Program  | Cursor Name | Table   | Purpose                                           | Fetch Pattern         |
| -------- | ----------- | ------- | ------------------------------------------------- | --------------------- |
| INQACC   | ACC-CURSOR  | ACCOUNT | Retrieve all accounts matching sort code + account number criteria | FETCH NEXT (loop until SQLCODE=100) |
| INQACCCU | ACC-CURSOR  | ACCOUNT | Retrieve up to 20 accounts for a given customer number | FETCH NEXT (loop, max 20 iterations) |

---

## Summary of Tables Accessed per Program

| Program  | ACCOUNT         | PROCTRAN | CONTROL                | CUSTOMER (VSAM) | ABNDFILE |
| -------- | --------------- | -------- | ---------------------- | --------------- | -------- |
| BANKDATA | INSERT, DELETE  | --       | INSERT (x2), DELETE (x2) | WRITE         | --       |
| CREACC   | INSERT          | INSERT   | SELECT, UPDATE         | --              | --       |
| CRECUST  | --              | INSERT   | --                     | WRITE, READ, REWRITE | --  |
| DELACC   | SELECT, DELETE  | INSERT   | --                     | --              | --       |
| DELCUS   | --              | INSERT   | --                     | READ, DELETE    | --       |
| INQACC   | SELECT (cursor + singleton) | -- | --              | --              | --       |
| INQACCCU | SELECT (cursor) | --       | --                     | --              | --       |
| INQCUST  | --              | --       | --                     | READ, STARTBR, READPREV | --  |
| UPDACC   | SELECT, UPDATE  | --       | --                     | --              | --       |
| UPDCUST  | --              | --       | --                     | READ, REWRITE   | --       |
| DBCRFUN  | SELECT, UPDATE  | INSERT   | --                     | --              | --       |
| XFRFUN   | SELECT (x2), UPDATE (x2) | INSERT | --             | --              | --       |
| ABNDPROC | --              | --       | --                     | --              | WRITE    |
