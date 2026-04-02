---
type: inventory
subtype: programs
status: draft
confidence: high
last_pass: 1
---

# Program Inventory

Catalog of all COBOL programs found in the source directory.

## Programs

| Program | Source File | Type | LOC | Copybooks Used | Purpose |
| ------- | ----------- | ---- | --- | -------------- | ------- |
| ABNDPROC | ABNDPROC.cbl | online-cics | 129 | ABNDINFO | Processes application abends and writes them to a centralised KSDS (VSAM) datastore so abend details can be viewed from one place. |
| BANKDATA | BANKDATA.cbl | batch + DB2 | 1235 | CUSTOMER, SORTCODE, CUSTCTRL, ACCTCTRL | Batch program to initialise the bank application data; populates the CUSTOMER VSAM file and the ACCOUNT DB2 table with generated random data. |
| BNK1CAC | BNK1CAC.cbl | online-cics | 1093 | BNK1CAM, DFHAID, ABNDINFO | BMS create-account front-end; validates input and links to CREACC to add the account to the datastore. |
| BNK1CCA | BNK1CCA.cbl | online-cics | 784 | BNK1ACC, DFHAID, INQACCCU, ABNDINFO | BMS program that lists all accounts belonging to a specified customer number. |
| BNK1CCS | BNK1CCS.cbl | online-cics | 1379 | BNK1CCM, DFHAID, ABNDINFO | BMS create-customer screen handler; captures customer details and invokes CRECUST to create the customer record. |
| BNK1CRA | BNK1CRA.cbl | online-cics | 969 | BNK1CDM, DFHAID, ABNDINFO | BMS credit/debit screen; accepts account number and amount then links to DBCRFUN to apply the transaction. |
| BNK1DAC | BNK1DAC.cbl | online-cics | 966 | BNK1DAM, DFHAID, INQACC, ABNDINFO | BMS display-account screen; retrieves account details and also handles account-delete requests. |
| BNK1DCS | BNK1DCS.cbl | online-cics | 1684 | BNK1DCM, DFHAID, DFHBMSCA, INQCUST, DELCUS, UPDCUST, ABNDINFO | BMS display-customer screen; shows customer details and provides delete (PF5) and update (PF10) options. |
| BNK1TFN | BNK1TFN.cbl | online-cics | 1027 | BNK1TFM, DFHAID, ABNDINFO | BMS transfer-funds screen; accepts source and target account details and links to XFRFUN to execute the transfer. |
| BNK1UAC | BNK1UAC.cbl | online-cics | 1181 | BNK1UAM, DFHAID, ABNDINFO | BMS update-account screen; allows amendment of account type, interest rate, overdraft limit and statement dates. |
| BNKMENU | BNKMENU.cbl | online-cics | 1066 | BNK1MAI, DFHAID, ABNDINFO | Bank main menu program; displays the BMS menu map and routes the user to the appropriate transaction based on their selection. |
| CRDTAGY1 | CRDTAGY1.cbl | online-cics | 215 | SORTCODE, ABNDINFO | Dummy credit-agency stub 1; invoked asynchronously via CICS Async API, returns a random credit score after a random delay. |
| CRDTAGY2 | CRDTAGY2.cbl | online-cics | 215 | SORTCODE, ABNDINFO | Dummy credit-agency stub 2; identical behaviour to CRDTAGY1 – random delay plus random credit score via Async API. |
| CRDTAGY3 | CRDTAGY3.cbl | online-cics | 215 | SORTCODE, ABNDINFO | Dummy credit-agency stub 3; identical behaviour to CRDTAGY1. |
| CRDTAGY4 | CRDTAGY4.cbl | online-cics | 215 | SORTCODE, ABNDINFO | Dummy credit-agency stub 4; identical behaviour to CRDTAGY1. |
| CRDTAGY5 | CRDTAGY5.cbl | online-cics | 215 | SORTCODE, ABNDINFO | Dummy credit-agency stub 5; identical behaviour to CRDTAGY1. |
| CREACC | CREACC.cbl | online-cics + DB2 | 1000 | SORTCODE, ACCDB2, PROCTRAN, ACCOUNT, CUSTOMER, INQCUST, INQACCCU, ACCTCTRL, ABNDINFO, CREACC | Creates a new bank account record in the DB2 ACCOUNT table, manages a named counter for account numbering, and writes a PROCTRAN record on success. |
| CRECUST | CRECUST.cbl | online-cics + DB2 | 1203 | SORTCODE, PROCTRAN, ABNDINFO, CUSTOMER, CUSTCTRL, CRECUST | Creates a new customer record; runs parallel credit checks via CICS Async API against five credit agencies, averages the scores, and writes to VSAM/DB2 plus PROCTRAN. |
| DBCRFUN | DBCRFUN.cbl | online-cics + DB2 | 701 | SORTCODE, ACCOUNT, PROCTRAN, ABNDINFO, PAYDBCR | Debit/credit function; retrieves the account from DB2, applies the cash amount, updates balances, and writes a PROCTRAN record. |
| DELACC | DELACC.cbl | online-cics + DB2 | 526 | SORTCODE, ACCDB2, ACCOUNT, PROCTRAN, ACCTCTRL, ABNDINFO, DELACC | Deletes an account record from the DB2 ACCOUNT table by customer number and account type, and writes a PROCTRAN delete record. |
| DELCUS | DELCUS.cbl | online-cics + DB2 | 603 | SORTCODE, ACCOUNT, CUSTOMER, PROCTRAN, INQACCCU, INQCUST, ABNDINFO, DELCUS | Deletes all accounts for a customer one by one (writing PROCTRAN records), then deletes the customer VSAM record and writes a customer-delete PROCTRAN record. |
| GETCOMPY | GETCOMPY.cbl | online-cics | 28 | GETCOMPY | Utility service; returns the bank company name ('CICS Bank Sample Application') to the caller via DFHCOMMAREA. |
| GETSCODE | GETSCODE.cbl | online-cics | 30 | SORTCODE, GETSCODE | Utility service; returns the configured sort code literal to the caller via DFHCOMMAREA. |
| INQACC | INQACC.cbl | online-cics + DB2 | 820 | SORTCODE, ACCDB2, ACCOUNT, ABNDINFO, INQACC | Retrieves a single account record from the DB2 ACCOUNT table by account number and type, and returns it to the caller. |
| INQACCCU | INQACCCU.cbl | online-cics + DB2 | 707 | SORTCODE, ACCDB2, ACCOUNT, CUSTOMER, INQCUST, ABNDINFO, INQACCCU | Retrieves all accounts associated with a given customer number from the DB2 ACCOUNT table and returns them as an array. |
| INQCUST | INQCUST.cbl | online-cics | 578 | SORTCODE, CUSTOMER, ABNDINFO, INQCUST | Retrieves a single customer record from the VSAM CUSTOMER file by customer number and returns it to the caller. |
| UPDACC | UPDACC.cbl | online-cics + DB2 | 337 | SORTCODE, ACCDB2, ACCOUNT, ABNDINFO, UPDACC | Updates non-balance account fields (type, interest rate, overdraft limit, statement dates) in the DB2 ACCOUNT table. |
| UPDCUST | UPDCUST.cbl | online-cics | 280 | SORTCODE, CUSTOMER, ABNDINFO, UPDCUST | Updates customer record fields (name, address, DOB, credit score) in the VSAM CUSTOMER file. |
| XFRFUN | XFRFUN.cbl | online-cics + DB2 | 1559 | SORTCODE, ACCOUNT, PROCTRAN, ABNDINFO, XFRFUN | Fund-transfer function; debits the source account and credits the target account in DB2, then writes a PROCTRAN transfer record. |

## Program Type Distribution

| Type | Count |
| ---- | ----- |
| Batch | 1 |
| Online (CICS) | 28 |
| Subprogram | 0 |
| **Total** | **29** |

## Unresolved References

Programs referenced via CALL but not found in the source directory:

| Called Program | Called From |
| -------------- | ----------- |
| CEEGMT | BANKDATA |
| CEEDATM | BANKDATA |
