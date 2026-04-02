---
type: inventory
subtype: copybooks
status: draft
confidence: high
last_pass: 1
---

# Copybook Inventory

Catalog of all copybooks (COPY members) found in the source directory.

## Copybooks

| Copybook | Source File | Used By | Fields | Purpose |
| -------- | ----------- | ------- | ------ | ------- |
| ABNDINFO | ABNDINFO.cpy | ABNDPROC, BNK1CAC, BNK1CCA, BNK1CCS, BNK1CRA, BNK1DAC, BNK1DCS, BNK1TFN, BNK1UAC, BNKMENU, CRDTAGY1, CRDTAGY2, CRDTAGY3, CRDTAGY4, CRDTAGY5, CREACC, CRECUST, DBCRFUN, DELACC, DELCUS, INQACC, INQACCCU, INQCUST, UPDACC, UPDCUST, XFRFUN | 10 | Abend information record written to the ABNDFILE KSDS; includes task number, APPLID, TRANID, date, time, abend code, program name, RESP/RESP2/SQLCODE, and free-form text. |
| ACCDB2 | ACCDB2.cpy | CREACC, DELACC, INQACC, INQACCCU, UPDACC | 12 | DB2 DECLARE TABLE for the ACCOUNT table; defines all 12 columns including sortcode, account number, type, interest rate, dates, overdraft limit and balances. |
| ACCOUNT | ACCOUNT.cpy | BANKDATA, CREACC, DBCRFUN, DELACC, DELCUS, INQACC, INQACCCU, UPDACC, XFRFUN | 14 | Working-storage layout of an ACCOUNT record with all data fields; used as the host variable structure for VSAM/DB2 I/O. |
| ACCTCTRL | ACCTCTRL.cpy | BANKDATA, CREACC, DELACC | 9 | Account control record structure (CTRL eyecatcher); holds account count, last account number and success/fail flags used to manage the account named counter. |
| BANKMAP | BANKMAP.cpy | (orphan) | 60 | BMS symbolic map (input/output) for the BANKDATA administration screen; contains fields for all datastore control counters. |
| BNK1DDM | BNK1DDM.cpy | (orphan) | 6 | BMS symbolic map for a generic bank display screen with company name, message and dummy fields. |
| CONTDB2 | CONTDB2.cpy | (orphan) | 3 | DB2 DECLARE TABLE for the CONTROL table; defines CONTROL_NAME, CONTROL_VALUE_NUM and CONTROL_VALUE_STR columns. |
| CONTROLI | CONTROLI.cpy | (orphan) | 4 | Working-storage layout for the CONTROL table row; holds customer count, last customer number, account count and last account number (packed-decimal). |
| CREACC | CREACC.cpy | CREACC | 14 | COMMAREA layout for the CREACC service; passes all account fields plus success/fail indicators between the BMS presentation layer and the CREACC back-end. |
| CRECUST | CRECUST.cpy | CRECUST | 12 | COMMAREA layout for the CRECUST service; passes customer key, name, address, DOB, credit score, review date and success/fail indicators. |
| CUSTCTRL | CUSTCTRL.cpy | BANKDATA, CRECUST | 8 | Customer control record structure; holds customer count, last customer number and success/fail flags for the customer named counter. |
| CUSTMAP | CUSTMAP.cpy | (orphan) | 30+ | BMS symbolic map for the customer display/update screen; defines input and output fields for all customer attributes. |
| CUSTOMER | CUSTOMER.cpy | BANKDATA, CREACC, CRECUST, DELCUS, INQACCCU, INQCUST, UPDCUST | 9 | Working-storage layout of a CUSTOMER VSAM record; includes eyecatcher, sort code, customer number, name, address, DOB, credit score and review date. |
| DELACC | DELACC.cpy | DELACC | 18 | COMMAREA layout for the DELACC service; carries account identification fields, balance fields, success/fail flags and PCB pointer fields. |
| DELACCZ | DELACCZ.cpy | (orphan) | 12 | Alternate COMMAREA layout for DELACC (z-variant); similar to DELACC.cpy but uses PIC X(4) for the PCB pointer field instead of POINTER. |
| DELCUS | DELCUS.cpy | DELCUS | 12 | COMMAREA layout for the DELCUS service; carries customer key, name, address, DOB, credit score, review date and delete success/fail indicators. |
| GETCOMPY | GETCOMPY.cpy | GETCOMPY | 1 | COMMAREA layout for the GETCOMPY service; single field COMPANY-NAME PIC X(40). |
| GETSCODE | GETSCODE.cpy | GETSCODE | 1 | COMMAREA layout for the GETSCODE service; single field SORTCODE PIC X(6). |
| INQACC | INQACC.cpy | BNK1DAC, INQACC | 13 | COMMAREA layout for the INQACC service; carries all account fields plus success flag and PCB1 pointer (POINTER type). |
| INQACCCU | INQACCCU.cpy | BNK1CCA, CREACC, DELCUS, INQACCCU | 13 | COMMAREA layout for the INQACCCU service; an ODO array of up to 20 account detail rows plus customer number, success/fail flags and PCB pointer (POINTER type). |
| INQACCCZ | INQACCCZ.cpy | (orphan) | 13 | Z-variant of INQACCCU COMMAREA; identical structure but PCB pointer is PIC X(4) instead of POINTER. |
| INQACCZ | INQACCZ.cpy | (orphan) | 13 | Z-variant of INQACC COMMAREA; identical structure but PCB pointer is PIC X(4) instead of POINTER. |
| INQCUST | INQCUST.cpy | BNK1DCS, CREACC, DELCUS, INQACCCU, INQCUST | 12 | COMMAREA layout for the INQCUST service; carries sort code, customer number, name, address, DOB, credit score, review date, success/fail and PCB pointer (POINTER type). |
| INQCUSTZ | INQCUSTZ.cpy | (orphan) | 12 | Z-variant of INQCUST COMMAREA; identical structure but PCB pointer is PIC X(4) instead of POINTER. |
| NEWACCNO | NEWACCNO.cpy | (orphan) | 5 | COMMAREA layout for an account number generation service (get-new, rollback, current functions); carries function code, account number and success/fail. |
| NEWCUSNO | NEWCUSNO.cpy | (orphan) | 5 | COMMAREA layout for a customer number generation service; mirrors NEWACCNO structure but for customer numbers. |
| PAYDBCR | PAYDBCR.cpy | DBCRFUN | 8 | COMMAREA layout for the DBCRFUN pay-debit/credit service; carries account number, amount, sort code, available/actual balances, origin details and success/fail. |
| PROCDB2 | PROCDB2.cpy | (orphan) | 9 | DB2 DECLARE TABLE for the PROCTRAN table; defines all 9 columns including eyecatcher, sortcode, number, date, time, reference, type, description and amount. |
| PROCISRT | PROCISRT.cpy | (orphan) | 40+ | COMMAREA layout for a processed-transaction insert service; function code plus union-style structs for debit, credit, transfer, delete/create customer, delete/create account. |
| PROCTRAN | PROCTRAN.cpy | CREACC, CRECUST, DBCRFUN, DELACC, DELCUS, XFRFUN | 25 | Working-storage layout of a PROCTRAN record; includes eyecatcher, sort code, number, date, time, reference, type, description (with REDEFINES for each transaction type) and amount. |
| RESPSTR | RESPSTR.cpy | (orphan) | 1 | Procedure-division paragraph EIBRESP-TOSTRING; translates a numeric EIBRESP value to a human-readable string (PIC X(40)). |
| SORTCODE | SORTCODE.cpy | BANKDATA, CRDTAGY1, CRDTAGY2, CRDTAGY3, CRDTAGY4, CRDTAGY5, CREACC, CRECUST, DBCRFUN, DELACC, DELCUS, GETSCODE, INQACC, INQACCCU, INQCUST, UPDACC, UPDCUST, XFRFUN | 1 | Defines the literal sort code constant: `77 SORTCODE PIC 9(6) VALUE 987654`. |
| STCUSTNO | STCUSTNO.cpy | (orphan) | 1 | Customer number key structure: `05 Customer-Number-Key` with `10 CNO-KEY PIC 9(10)`. |
| UPDACC | UPDACC.cpy | UPDACC | 12 | COMMAREA layout for the UPDACC service; carries all account fields plus success flag. |
| UPDCUST | UPDCUST.cpy | UPDCUST | 12 | COMMAREA layout for the UPDCUST service; carries customer key, name, address, DOB, credit score, review date and update success/fail indicators. |
| WAZI | WAZI.cpy | (orphan) | 0 | Empty copybook placeholder (comment only: "THIS IS AN EMPTY COPYBOOK"). |
| XFRFUN | XFRFUN.cpy | XFRFUN | 9 | COMMAREA layout for the XFRFUN transfer service; carries from/to account numbers and sort codes, amount, available/actual balances for both accounts, and success/fail flag. |

## Orphan Copybooks

Copybooks in the source directory not referenced by any analysed program:

- BANKMAP
- BNK1DDM
- CONTDB2
- CONTROLI
- CUSTMAP
- DELACCZ
- INQACCCZ
- INQACCZ
- INQCUSTZ
- NEWACCNO
- NEWCUSNO
- PROCDB2
- PROCISRT
- RESPSTR
- STCUSTNO
- WAZI

## Missing Copybooks

Copybooks referenced by COPY statements but not found in the source directory:

| Copybook | Referenced By |
| -------- | ------------- |
| BNK1CAM | BNK1CAC |
| BNK1ACC | BNK1CCA |
| BNK1CCM | BNK1CCS |
| BNK1CDM | BNK1CRA |
| BNK1DAM | BNK1DAC |
| BNK1DCM | BNK1DCS |
| BNK1TFM | BNK1TFN |
| BNK1UAM | BNK1UAC |
| BNK1MAI | BNKMENU |
| DFHAID | BNK1CAC, BNK1CCA, BNK1CCS, BNK1CRA, BNK1DAC, BNK1DCS, BNK1TFN, BNK1UAC, BNKMENU |
| DFHBMSCA | BNK1DCS |
