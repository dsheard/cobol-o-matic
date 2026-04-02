---
type: business-rules
program: BANKDATA
program_type: subprogram
status: draft
confidence: medium
last_pass: 4
calls:
- CEEDATM
- CEEGMT
called_by: []
uses_copybooks:
- ACCDB2
- ACCTCTRL
- CONTDB2
- CUSTCTRL
- CUSTOMER
- SORTCODE
reads:
- CUSTOMER-FILE
writes:
- CUSTOMER-FILE
db_tables:
- ACCOUNT
- CONTROL
transactions: []
mq_queues: []
---

# BANKDATA -- Business Rules

## Program Purpose

BANKDATA is a batch DB2 initialisation program that populates the CBSA banking
application's two primary datastores from scratch. It accepts a JCL PARM
string specifying the customer-number range, generation step, and a random
seed. For every customer number in that range it generates a synthetic customer
record (name, address, date of birth, credit score, credit-score review date)
and writes it to the VSAM CUSTOMER file. It then generates between 1 and 5
DB2 ACCOUNT rows per customer. Before writing any data the program deletes
all existing ACCOUNT and CONTROL rows that match the configured sort code
(987654), so every run is a clean-slate reload. After all records are written
it inserts two control rows into the DB2 CONTROL table recording the last
account number used and the total count of accounts created.

## Input / Output

| Direction | Resource        | Type  | Description                                                       |
| --------- | --------------- | ----- | ----------------------------------------------------------------- |
| IN        | JCL PARM        | Batch | Comma/space-delimited: start-key, end-key, step-key, random-seed  |
| OUT       | CUSTOMER-FILE   | VSAM  | Indexed KSDS keyed on CUSTOMER-KEY; written sequentially          |
| OUT       | ACCOUNT (DB2)   | DB2   | ACCOUNT table rows inserted, one per account generated            |
| OUT       | CONTROL (DB2)   | DB2   | Two control rows: `<sortcode>-ACCOUNT-LAST` and `<sortcode>-ACCOUNT-COUNT` |
| DEL       | ACCOUNT (DB2)   | DB2   | All rows for the configured sort code deleted before reload       |
| DEL       | CONTROL (DB2)   | DB2   | `<sortcode>-ACCOUNT-LAST` and `<sortcode>-ACCOUNT-COUNT` deleted before reload |

## Business Rules

### Parameter Validation

| #  | Rule                                  | Condition                                    | Action                                                                         | Source Location       |
| -- | ------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------ | --------------------- |
| 1  | End key must not precede start key    | `IF END-KEY < START-KEY`                     | MOVE 12 TO RETURN-CODE; DISPLAY 'Final customer number cannot be smaller than first customer number'; GOBACK | A010 (line 397-402)  |
| 2  | Step key must not be zero             | `IF STEP-KEY = ZERO`                         | MOVE 12 TO RETURN-CODE; DISPLAY 'Gap between customers cannot be zero'; GOBACK | A010 (line 403-407)  |

### VSAM File Handling

| #  | Rule                                     | Condition                                          | Action                                                                   | Source Location       |
| -- | ---------------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------ | --------------------- |
| 3  | CUSTOMER file must open successfully     | `IF CUSTOMER-VSAM-STATUS NOT EQUAL '00'`           | DISPLAY 'Error opening CUSTOMER file, status=...' MOVE 12 TO RETURN-CODE; PERFORM PROGRAM-DONE | A010 (line 450-455) |
| 4  | Customer record write must succeed       | `IF CUSTOMER-VSAM-STATUS NOT EQUAL '00'` after WRITE | DISPLAY 'Error writing to VSAM file, status=...' MOVE 12 TO RETURN-CODE; PERFORM PROGRAM-DONE | A010 (line 564-569) |
| 5  | Customer control record write must succeed | `IF CUSTOMER-VSAM-STATUS NOT EQUAL '00'` after WRITE of control record | DISPLAY 'Error writing CUSTOMER-CONTROL-RECORD file, status=...' MOVE 12 TO RETURN-CODE; PERFORM PROGRAM-DONE | A010 (line 595-600) |

### Customer Record Generation Rules

| #  | Rule                                            | Condition / Logic                                                                                          | Action                                                               | Source Location       |
| -- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- | --------------------- |
| 6  | Customer eyecatcher must be set to 'CUST'       | `SET CUSTOMER-EYECATCHER-VALUE TO TRUE` (88-level condition)                                               | Assigns literal 'CUST' to CUSTOMER-EYECATCHER field                  | A010 (line 473)       |
| 7  | Customer number equals the loop key             | `MOVE NEXT-KEY TO CUSTOMER-NUMBER`                                                                         | CUSTOMER-NUMBER is assigned the value of NEXT-KEY for each iteration | A010 (line 475)       |
| 8  | Customer name is composed from random arrays    | Title (1-36 from TITLE-ALPHABET), forename (1-50), initial (1-30), surname (1-50) selected via FUNCTION RANDOM | STRING into CUSTOMER-NAME delimited by SPACE                        | A010 (line 481-507)   |
| 9  | Title selection uses a weighted 36-element array | TITLE-ALPHABET has 36 entries (indices 1-36): positions 1-20 are Mr/Mrs/Miss/Ms (4 repeating cycles of 5), positions 21-28 are Dr/Drs/Dr/Ms/Dr/Ms/Dr/Ms, positions 29-31 are Professor (3x), position 32 is Lord, positions 33-34 are Sir, positions 35-36 are Lady. Mr/Mrs/Miss/Ms are each represented 5 times giving them ~14% probability each. | TITLE-NUMBER = ((36-1) * FUNCTION RANDOM) + 1; title lookup from TITLE-ALPHABET | A010 (line 481-482); WS (line 178-213) |
| 10 | Customer address is composed from random arrays | House number 1-99, street tree name (1-26), street road type (1-19), town (1-50) selected via FUNCTION RANDOM | STRING into CUSTOMER-ADDRESS                                        | A010 (line 509-521)   |
| 11 | Customer date of birth is fully random          | Day 1-28; Month 1-12; Year 1900-2000 (all via FUNCTION RANDOM)                                             | Stored in CUSTOMER-BIRTH-DAY, CUSTOMER-BIRTH-MONTH, CUSTOMER-BIRTH-YEAR | A010 (line 523-528) |
| 12 | Customer sort code is the configured sort code  | `MOVE SORTCODE TO CUSTOMER-SORTCODE`; SORTCODE literal VALUE 987654 (from SORTCODE copybook)               | CUSTOMER-SORTCODE is set to 987654                                   | A010 (line 530-532)   |
| 13 | Customer credit score is random 1-999           | `COMPUTE CUSTOMER-CREDIT-SCORE = ((999-1) * FUNCTION RANDOM) + 1`                                          | Credit score stored in CUSTOMER-CREDIT-SCORE                         | A010 (line 534-535)   |
| 14 | Credit score review date is 1-21 days from today | `COMPUTE WS-REVIEW-DATE-ADD = ((21-1) * FUNCTION RANDOM) + 1`; integer date arithmetic; then DATE-OF-INTEGER | CUSTOMER-CS-REVIEW-YEAR/MONTH/DAY populated                        | A010 (line 542-560)   |

### Account Count per Customer

| #  | Rule                                         | Condition / Logic                                                       | Action                                                              | Source Location     |
| -- | -------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------- |
| 15 | Each customer gets 1-5 accounts              | `COMPUTE NO-OF-ACCOUNTS = ((5-1) * FUNCTION RANDOM) + 1`               | PERFORM POPULATE-ACC iterated NO-OF-ACCOUNTS times                 | DA010 (line 701-705) |
| 16 | Maximum accounts per customer is 10          | Comment: "maximum is 10 at the moment dictated by the alternate key index" | Design constraint documented in comments; loop capped at 5 in practice | DA010 (line 697-699) |

### Account Record Generation Rules

| #  | Rule                                            | Condition / Logic                                                                                                               | Action                                                                     | Source Location       |
| -- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | --------------------- |
| 17 | Account eyecatcher must be 'ACCT'               | `MOVE 'ACCT' TO HV-ACCOUNT-EYECATCHER`                                                                                          | Eye-catcher field set on every account row                                 | PA010 (line 740-741)  |
| 18 | Account opened date must be after date of birth | Loop: `PERFORM GENERATE-OPENED-DATE UNTIL OPENED-DATE-VALID = 'Y'`; flag set 'Y' only when `HV-ACCOUNT-OPENED-YEAR > CUSTOMER-BIRTH-YEAR` | Date generation retried until valid                                       | PA010 (line 726-732); GOD010 (line 912-916) |
| 19 | Opened-date retry cap at 100 attempts           | `IF OPENED-DATE-ATTEMPTS > 100` in GENERATE-OPENED-DATE                                                                         | Force OPENED-DATE-VALID='Y'; set opened date equal to customer birth date (fallback) | GOD010 (line 917-922) |
| 20 | Account opened year range: birth year to 2014  | `COMPUTE WS-ACCOUNT-OPENED-YEAR = ((2014 - CUSTOMER-BIRTH-YEAR) * FUNCTION RANDOM) + CUSTOMER-BIRTH-YEAR`                       | Opened year is between customer birth year and 2014                        | GOD010 (line 891-895) |
| 21 | Account opened date stored in DD.MM.YYYY format | HV-ACCOUNT-OPENED-GROUP REDEFINES HV-ACCOUNT-OPENED: fields ordered DAY(XX), DELIM1(X), MONTH(XX), DELIM2(X), YEAR(X4). Generated values written as day/month/year into the group, so stored string is 'DD.MM.YYYY' | GOD010 MOVEs day/month/year into OPENED-GROUP sub-fields; delimiters set to '.' in PA010 (lines 759-760) | PA010 (line 759-760); GOD010 (line 886-896); WS (line 92-97) |
| 22 | Account type is drawn from fixed 5-type table  | ACCOUNT-TYPES-COUNT = 5; types: ISA, SAVING, CURRENT, LOAN, MORTGAGE; indexed by WS-CNT (account loop counter)                  | `MOVE WS-ACCOUNT-TYPE(WS-CNT) TO HV-ACCOUNT-TYPE`                         | IA010 (line 1151-1157); PA010 (line 755-756) |
| 23 | Fixed interest rates per account type          | ISA=2.10, SAVING=1.75, CURRENT=0.00, LOAN=17.90, MORTGAGE=5.25; indexed by WS-CNT                                               | `MOVE WS-ACCOUNT-INT-RATE(WS-CNT) TO HV-ACCOUNT-INTEREST-RATE`            | IA010 (line 1160-1165); PA010 (line 757-758) |
| 24 | Fixed overdraft limits per account type        | ISA=0, SAVING=0, CURRENT=100, LOAN=0, MORTGAGE=0; indexed by WS-CNT                                                             | `MOVE WS-OVERDRAFT-CONVERSION TO HV-ACCOUNT-OVERDRAFT-LIMIT`               | IA010 (line 1168-1174); PA010 (line 765-768) |
| 25 | Last statement date hard-coded to 01.07.2021  | Literal MOVEs into HV-ACCOUNT-LAST-STMT-GROUP sub-fields: DAY='01', DELIM='.',  MONTH='07', DELIM='.', YEAR='2021'. Stored string is '01.07.2021' (DD.MM.YYYY format) | All accounts initialised with last statement date of 01.07.2021 | PA010 (line 769-776) |
| 26 | Next statement date hard-coded to 01.08.2021  | Literal MOVEs into HV-ACCOUNT-NEXT-STMT-GROUP sub-fields: DAY='01', DELIM='.', MONTH='08', DELIM='.', YEAR='2021'. Stored string is '01.08.2021' (DD.MM.YYYY format) | All accounts initialised with next statement date of 01.08.2021 | PA010 (line 777-784) |
| 27 | Account available balance is random 1-999999  | `COMPUTE HV-ACCOUNT-AVAILABLE-BALANCE = ((999999-1) * FUNCTION RANDOM) + 1`                                                      | Available balance randomly generated                                        | PA010 (line 785-787)  |
| 28 | Actual balance equals available balance initially | `MOVE HV-ACCOUNT-AVAILABLE-BALANCE TO HV-ACCOUNT-ACTUAL-BALANCE`                                                              | Actual balance starts equal to available balance before sign adjustment    | PA010 (line 788-789)  |
| 29 | LOAN and MORTGAGE balances must be negative   | `IF HV-ACCOUNT-TYPE = 'LOAN    ' OR 'MORTGAGE'`: negate both available and actual balance                                        | `COMPUTE HV-ACCOUNT-ACTUAL-BALANCE = 0 - HV-ACCOUNT-ACTUAL-BALANCE`; same for available balance | PA010 (line 797-806) |
| 30 | Account number is a sequential integer counter | WS-ACCOUNT-NUMBER starts at 1 (VALUE 1), set into LAST-ACCOUNT-NUMBER at line 749 (before INSERT) and again at line 870 (after successful INSERT); incremented at line 872 only after a successful INSERT | `ADD 1 TO WS-ACCOUNT-NUMBER` after each insert; LAST-ACCOUNT-NUMBER reflects most-recently-attempted account number | PA010 (line 749, 870-872) |

### Control Record Population

| #  | Rule                                          | Condition / Logic                                                                            | Action                                                                   | Source Location        |
| -- | --------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ---------------------- |
| 31 | ACCOUNT-LAST control row key format           | `STRING SORTCODE '-' 'ACCOUNT-LAST' INTO HV-CONTROL-NAME`; e.g. `987654-ACCOUNT-LAST`       | INSERT INTO CONTROL with LAST-ACCOUNT-NUMBER as CONTROL_VALUE_NUM        | A010 (line 606-633)    |
| 32 | ACCOUNT-COUNT control row key format          | `STRING SORTCODE '-' 'ACCOUNT-COUNT' INTO HV-CONTROL-NAME`; e.g. `987654-ACCOUNT-COUNT`      | INSERT INTO CONTROL with NUMBER-OF-ACCOUNTS as CONTROL_VALUE_NUM         | A010 (line 635-662)    |
| 33 | Customer control sentinel record written to VSAM | Sortcode='000000', number='9999999999', eyecatcher='CTRL' (88-level CUSTOMER-CONTROL-EYECATCHER-V) | Written as last record to CUSTOMER-FILE to mark end of data            | A010 (line 588-600)    |
| 34 | Sentinel does not carry customer count or last customer number | CUSTOMER-CONTROL-RECORD fields NUMBER-OF-CUSTOMERS and LAST-CUSTOMER-NUMBER are never populated before the sentinel write | Both fields will be zero in the written sentinel record; the corresponding DB2 CONTROL table does NOT receive analogous customer-count rows (only account-count and account-last are inserted) | A010 (line 588-600) |
| 35 | NUMBER-OF-CUSTOMERS is tallied but never written to DB2 | `ADD 1 TO NUMBER-OF-CUSTOMERS GIVING NUMBER-OF-CUSTOMERS` in the main loop (line 477); no corresponding INSERT INTO CONTROL for customers | Only the account-count and account-last are written to DB2 CONTROL; customer count is silently discarded | A010 (line 477, 635-662) |

### Commit Frequency (Data Integrity)

| #  | Rule                                     | Condition                               | Action                                           | Source Location       |
| -- | ---------------------------------------- | --------------------------------------- | ------------------------------------------------ | --------------------- |
| 36 | COMMIT every 1,000 customer/account cycles | `IF COMMIT-COUNT > 1000`               | `EXEC SQL COMMIT WORK`; MOVE ZERO TO COMMIT-COUNT | A010 (line 579-585)  |
| 37 | COMMIT after each customer's accounts     | Unconditional in DEFINE-ACC after POPULATE-ACC loop | `EXEC SQL COMMIT WORK` executed per customer    | DA010 (line 706-708)  |
| 38 | COMMIT at end of DELETE-DB2-ROWS          | Unconditional after all three deletes   | `EXEC SQL COMMIT WORK`                            | DBR010 (line 1375-1377) |

### Reference Data Defects

| #  | Rule                                          | Condition / Logic                                                                            | Action / Impact                                                          | Source Location        |
| -- | --------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ---------------------- |
| 39 | SURNAME array index 24 is assigned twice      | In INITIALISE-ARRAYS (IA010), `MOVE 'Ramsbottom' TO SURNAME(24)` at line 1017 is immediately overwritten by `MOVE 'Lloyd' TO SURNAME(24)` at line 1018 | 'Ramsbottom' is never reachable; SURNAME(24) will always be 'Lloyd'. Note that SURNAME(34) is also 'Lloyd' (line 1028), making 'Lloyd' appear at two separate indices | IA010 (line 1017-1018) |
| 40 | SURNAME(27) contains misspelling 'Higins'     | `MOVE 'Higins' TO SURNAME(27)` at line 1021 -- 'Higins' is a likely typo for 'Higgins'      | All generated customers that happen to select SURNAMES-PTR=27 will have the surname 'Higins' written to the database | IA010 (line 1021) |
| 41 | INITIALS alphabet has 'L' and 'K' transposed  | `MOVE 'ABCDEFGHIJLKMNOPQRSTUVWXYZ    ' TO INITIALS` at line 990 -- positions 11 and 12 are 'L' then 'K' instead of 'K' then 'L' | Generated customer initials using INITIALS-PTR=11 will be 'L' and INITIALS-PTR=12 will be 'K'; the normal alphabetic order is reversed for those two positions | IA010 (line 990) |

## Calculations

| Calculation                      | Formula / Logic                                                                                                    | Input Fields                                 | Output Field                    | Source Location        |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------ | -------------------------------------------- | ------------------------------- | ---------------------- |
| Random array seed initialisation | First COMPUTE uses `FUNCTION RANDOM(RANDOM-SEED-NUMERIC)` to seed the sequence; six further COMPUTEs call `FUNCTION RANDOM` (no argument) to advance it. The 7 COMPUTEs initialise: FORENAMES-PTR, INITIALS-PTR, SURNAMES-PTR, TOWN-PTR, STREET-NAME-R-PTR, STREET-NAME-T-PTR, ACCOUNT-TYPES-PTR | RANDOM-SEED-NUMERIC, array count fields     | 7 *-PTR pointer fields          | A010 (line 428-443)    |
| Title selection                  | `TITLE-NUMBER = ((36-1) * FUNCTION RANDOM) + 1`                                                                    | FUNCTION RANDOM                              | TITLE-NUMBER (1-36)             | A010 (line 481-482)    |
| Forename pointer                 | `((FORENAMES-CNT-1) * FUNCTION RANDOM) + 1`                                                                        | FORENAMES-CNT (50)                           | FORENAMES-PTR (1-50)            | A010 (line 483-484)    |
| Initials pointer                 | `((INITIALS-CNT-1) * FUNCTION RANDOM) + 1`                                                                         | INITIALS-CNT (30)                            | INITIALS-PTR (1-30)             | A010 (line 485-486)    |
| Surname pointer                  | `((SURNAMES-CNT-1) * FUNCTION RANDOM) + 1`                                                                         | SURNAMES-CNT (50)                            | SURNAMES-PTR (1-50)             | A010 (line 487-488)    |
| House number                     | `(99 * FUNCTION RANDOM) + 1`                                                                                       | FUNCTION RANDOM                              | HOUSE-NUMBER (1-99)             | A010 (line 489-490)    |
| Customer birth day               | `((28-1) * FUNCTION RANDOM) + 1`                                                                                   | FUNCTION RANDOM                              | CUSTOMER-BIRTH-DAY (1-28)       | A010 (line 523-524)    |
| Customer birth month             | `((12-1) * FUNCTION RANDOM) + 1`                                                                                   | FUNCTION RANDOM                              | CUSTOMER-BIRTH-MONTH (1-12)     | A010 (line 525-526)    |
| Customer birth year              | `((2000-1900) * FUNCTION RANDOM) + 1900`                                                                           | FUNCTION RANDOM                              | CUSTOMER-BIRTH-YEAR (1900-2000) | A010 (line 527-528)    |
| Credit score                     | `((999-1) * FUNCTION RANDOM) + 1`                                                                                  | FUNCTION RANDOM                              | CUSTOMER-CREDIT-SCORE (1-999)   | A010 (line 534-535)    |
| Credit review date offset        | `((21-1) * FUNCTION RANDOM) + 1`                                                                                   | FUNCTION RANDOM                              | WS-REVIEW-DATE-ADD (1-21 days)  | A010 (line 542-543)    |
| Credit review date (integer)     | `WS-TODAY-INT + WS-REVIEW-DATE-ADD`                                                                                | WS-TODAY-INT, WS-REVIEW-DATE-ADD             | WS-NEW-REVIEW-DATE-INT          | A010 (line 545-546)    |
| Credit review date (calendar)    | `FUNCTION DATE-OF-INTEGER (WS-NEW-REVIEW-DATE-INT)`                                                                | WS-NEW-REVIEW-DATE-INT                       | WS-NEW-REVIEW-YYYYMMDD          | A010 (line 552-553)    |
| Today's date as integer          | `FUNCTION INTEGER-OF-DATE (WS-CURRENT-DATE-9)`                                                                     | WS-CURRENT-DATE-9 (YYYYMMDD)                 | WS-TODAY-INT                    | GTD010 (line 1400-1401) |
| Number of accounts per customer  | `((5-1) * FUNCTION RANDOM) + 1`                                                                                    | FUNCTION RANDOM                              | NO-OF-ACCOUNTS (1-5)            | DA010 (line 701-702)   |
| Account opened day               | `((28-1) * FUNCTION RANDOM) + 1`                                                                                   | FUNCTION RANDOM                              | WS-ACCOUNT-OPENED-DAY (1-28)   | GOD010 (line 883-885)  |
| Account opened month             | `((12-1) * FUNCTION RANDOM) + 1`                                                                                   | FUNCTION RANDOM                              | WS-ACCOUNT-OPENED-MONTH (1-12) | GOD010 (line 887-889)  |
| Account opened year              | `((2014 - CUSTOMER-BIRTH-YEAR) * FUNCTION RANDOM) + CUSTOMER-BIRTH-YEAR`                                          | CUSTOMER-BIRTH-YEAR, FUNCTION RANDOM         | WS-ACCOUNT-OPENED-YEAR          | GOD010 (line 891-895)  |
| LOAN/MORTGAGE balance negation   | `0 - HV-ACCOUNT-ACTUAL-BALANCE` and `0 - HV-ACCOUNT-AVAILABLE-BALANCE`                                            | HV-ACCOUNT-ACTUAL-BALANCE, HV-ACCOUNT-AVAILABLE-BALANCE | Both balance fields (negated) | PA010 (line 799-804)  |
| Account available balance        | `((999999-1) * FUNCTION RANDOM) + 1`                                                                               | FUNCTION RANDOM                              | HV-ACCOUNT-AVAILABLE-BALANCE (1-999999) | PA010 (line 785-787) |
| Day-of-week calculation (DEAD CODE) | `DIVIDE WS-CURRENT-DATE-9 BY 7 GIVING WS-DT REMAINDER WS-DT-REM`; if remainder=0 force to 7; MOVE WS-WEEKDAY(WS-DT-REM) TO WS-DAY-TODAY | WS-CURRENT-DATE-9 | WS-DT-REM (1-7), WS-DAY-TODAY | CDW010 (line 1426-1433) -- **NOTE: CDW010 section is never called (no PERFORM CDW010 or PERFORM CALC-DAY-OF-WEEK anywhere in the program); this is dead code** |
| GMT timestamp conversion         | CALL CEEGMT to get Lilian date + seconds; truncate via integer MOVE; CALL CEEDATM to format as 'YYYYMMDDHHMISS'    | gmt-lilian, gmt-seconds                      | datm-conv (formatted timestamp) | TIMESTAMP (line 1442-1463) |

## Error Handling

| Condition                                                              | Action                                                                                                    | Return Code | Source Location         |
| ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ----------- | ----------------------- |
| END-KEY < START-KEY                                                    | DISPLAY 'Final customer number cannot be smaller than first customer number'; GOBACK                      | 12          | A010 (line 397-402)     |
| STEP-KEY = ZERO                                                        | DISPLAY 'Gap between customers cannot be zero'; GOBACK                                                    | 12          | A010 (line 403-407)     |
| CUSTOMER-FILE open failure (VSAM-STATUS not '00')                      | DISPLAY 'Error opening CUSTOMER file, status=...'; PERFORM PROGRAM-DONE                                   | 12          | A010 (line 450-455)     |
| WRITE to CUSTOMER-FILE fails (VSAM-STATUS not '00')                    | DISPLAY 'Error writing to VSAM file, status=...'; PERFORM PROGRAM-DONE                                    | 12          | A010 (line 564-569)     |
| WRITE of CUSTOMER-CONTROL-RECORD fails (VSAM-STATUS not '00')          | DISPLAY 'Error writing CUSTOMER-CONTROL-RECORD file, status=...'; PERFORM PROGRAM-DONE                    | 12          | A010 (line 595-600)     |
| INSERT INTO CONTROL (ACCOUNT-LAST) fails (SQLCODE not 0)               | DISPLAY 'Error inserting last account control record' + SQLCODE; continues (no GOBACK)                    | none set    | A010 (line 625-633)     |
| INSERT INTO CONTROL (ACCOUNT-COUNT) fails (SQLCODE not 0)              | DISPLAY 'Error inserting account count control record' + SQLCODE; continues (no GOBACK)                   | none set    | A010 (line 654-662)     |
| DELETE FROM ACCOUNT fails (SQLCODE not 0 and not +100)                 | DISPLAY error with SORTCODE, SQLCODE, SQLSTATE, SQLERRMC, SQLERRD(1-6); PERFORM PROGRAM-DONE              | 12          | DBR010 (line 1205-1239) |
| DELETE FROM CONTROL (ACCOUNT-LAST) fails (SQLCODE not 0 and not +100)  | DISPLAY error with CONTROL_NAME, SQLCODE, SQLSTATE, SQLERRMC, SQLERRD(1-6); PERFORM PROGRAM-DONE          | 12          | DBR010 (line 1271-1305) |
| DELETE FROM CONTROL (ACCOUNT-COUNT) fails (SQLCODE not 0 and not +100) | DISPLAY error with CONTROL_NAME, SQLCODE, SQLSTATE, SQLERRMC, SQLERRD(1-6); PERFORM PROGRAM-DONE          | 12          | DBR010 (line 1337-1371) |
| INSERT INTO ACCOUNT fails (SQLCODE not 0)                              | DISPLAY full SQL diagnostics; PERFORM PROGRAM-DONE                                                        | 12          | PA010 (line 841-867)    |
| DB2 error reason code = 13172878 (0x00C900E)                           | EVALUATE branch: MOVE 'TIMEOUT  (00C900E)' TO DISP-REASON-CODE                                            | (display only) | Multiple paragraphs  |
| DB2 error reason code = 13172872 (0x00C9088)                           | EVALUATE branch: MOVE 'DEADLOCK (00C9088)' TO DISP-REASON-CODE                                            | (display only) | Multiple paragraphs  |
| DB2 error reason code is any other value                               | EVALUATE OTHER: MOVE 'Unknown ReasonCode' TO DISP-REASON-CODE                                             | (display only) | Multiple paragraphs  |
| SQLCODE = +100 on DELETE                                               | Tolerated; treated as success (no rows to delete is acceptable)                                            | none          | DBR010 (line 1205, 1271, 1337) |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. **A010 (PREMIERE SECTION)** -- entry point; parses PARM, validates parameters, orchestrates all processing
2. **PERFORM INITIALISE-ARRAYS** -- loads all reference data arrays into WORKING-STORAGE (names, addresses, account types, rates, overdraft limits)
3. PARM parsing -- UNSTRING PARM into START-KEY, END-KEY, STEP-KEY, RANDOM-SEED delimited by SPACE or comma
4. Parameter validation -- END-KEY >= START-KEY; STEP-KEY != 0; else GOBACK with RC=12
5. **PERFORM GET-TODAYS-DATE** -- captures today's date as an integer for credit-review-date arithmetic
6. **PERFORM DELETE-DB2-ROWS** -- DELETE FROM ACCOUNT WHERE SORTCODE matches; DELETE FROM CONTROL for both ACCOUNT-LAST and ACCOUNT-COUNT keys; COMMIT
7. Random seed initialisation -- 7 sequential COMPUTE FUNCTION RANDOM calls: first uses RANDOM-SEED-NUMERIC as seed argument (seeding the sequence), remaining 6 use no argument (advancing the sequence) to initialise FORENAMES-PTR, INITIALS-PTR, SURNAMES-PTR, TOWN-PTR, STREET-NAME-R-PTR, STREET-NAME-T-PTR, ACCOUNT-TYPES-PTR
8. OPEN OUTPUT CUSTOMER-FILE -- if status != '00' terminates with RC=12
9. **PERFORM ... VARYING NEXT-KEY FROM START-KEY BY STEP-KEY UNTIL NEXT-KEY > END-KEY** -- main generation loop over customer key range
   - INITIALIZE customer record; set eyecatcher 'CUST'
   - Generate name, address, DOB via random arrays
   - Generate credit score (1-999) and credit review date (today+1 to today+21)
   - WRITE CUSTOMER-RECORD-STRUCTURE to VSAM (terminate on error)
   - **PERFORM DEFINE-ACC** -- generates 1-5 accounts per customer
   - COMMIT every 1,000 iterations
10. Write CUSTOMER-CONTROL-RECORD sentinel (sortcode='000000', number='9999999999', eyecatcher='CTRL'); NUMBER-OF-CUSTOMERS and LAST-CUSTOMER-NUMBER fields within the sentinel are NOT populated (they remain zeroes)
11. INSERT INTO CONTROL: `<sortcode>-ACCOUNT-LAST` with LAST-ACCOUNT-NUMBER
12. INSERT INTO CONTROL: `<sortcode>-ACCOUNT-COUNT` with NUMBER-OF-ACCOUNTS
13. CLOSE CUSTOMER-FILE
14. **PERFORM TIMESTAMP** (wraps CALL CEEGMT + CALL CEEDATM) -- called at start, before/after DELETE, and at end for progress logging
15. **GOBACK** via PROGRAM-DONE (PD010) on any fatal error; on the normal (success) exit path the PREMIERE SECTION falls through to A999 EXIT and then into the PROGRAM-DONE SECTION which executes GOBACK unconditionally

**DEFINE-ACC (DA010):** Randomly selects account count 1-5; PERFORMs POPULATE-ACC that many times using WS-CNT as loop counter (VARYING WS-CNT FROM 1 BY 1 UNTIL WS-CNT > NO-OF-ACCOUNTS); WS-CNT also serves as the index into the account-type, interest-rate, and overdraft arrays; then COMMITs.

**POPULATE-ACC (PA010):** Loops GENERATE-OPENED-DATE until opened year > birth year (or 100 retries); populates HOST-ACCOUNT-ROW fields; negates balances for LOAN/MORTGAGE types; executes INSERT INTO ACCOUNT; increments WS-ACCOUNT-NUMBER and NUMBER-OF-ACCOUNTS. Date fields (ACCOUNT_OPENED, ACCOUNT_LAST_STATEMENT, ACCOUNT_NEXT_STATEMENT) are stored in DD.MM.YYYY format.

**GENERATE-OPENED-DATE (GOD010):** Generates random day (1-28), month (1-12), year (birth year to 2014). Sets OPENED-DATE-VALID='Y' and exits via GO TO GOD999 when year > birth year. After 100 failed attempts forces the date equal to the customer's birth date and exits.

**DELETE-DB2-ROWS (DBR010):** Deletes all ACCOUNT rows for the sort code; deletes CONTROL rows for `<sortcode>-ACCOUNT-LAST`; deletes CONTROL rows for `<sortcode>-ACCOUNT-COUNT`; COMMITs. Each delete checks SQLCODE: 0 and +100 are acceptable; any other value terminates with RC=12.

**GET-TODAYS-DATE (GTD010):** MOVE FUNCTION CURRENT-DATE; extract YYYYMMDD; COMPUTE FUNCTION INTEGER-OF-DATE to store integer form in WS-TODAY-INT.

**TIMESTAMP (section):** CALL 'CEEGMT' to obtain GMT Lilian date and seconds; truncates seconds to integer; CALL 'CEEDATM' with format 'YYYYMMDDHHMISS' to produce a printable timestamp. Debug-mode only display.

**PROGRAM-DONE (PD010):** Unconditional GOBACK. Called on all fatal error paths and reached via section fall-through on the normal success path.

**CDW010 (CALC-DAY-OF-WEEK section) -- DEAD CODE:** This section and CDW999 exist in the source (lines 1407-1439) with full logic to calculate the day of week and populate WS-DAY-TODAY, but there is no PERFORM CDW010 anywhere in the program. The section is never reached during execution. The associated WORKING-STORAGE fields (WS-WEEKDAYS, WS-WEEKDAY-GROUP, WS-DT, WS-DT-REM, WS-DAY-OF-WEEK-VAL, WS-DAY-TODAY) are allocated but unused.
