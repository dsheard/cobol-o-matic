---
type: integration
subtype: io-map
status: draft
confidence: high
last_pass: 2
---

# I/O Map

Complete mapping of every program to every external resource it accesses, with direction and access pattern.

## Program I/O Summary

| Program | Files Read | Files Written | DB Tables | MQ Queues | Screens |
| ------- | ---------- | ------------- | --------- | --------- | ------- |
| ABNDPROC | 0 | 1 (ABNDFILE) | 0 | 0 | 0 |
| BANKDATA | 0 | 1 (CUSTOMER-FILE) | 2 (ACCOUNT, CONTROL) | 0 | 0 |
| BNK1CAC | 0 | 0 | 0 | 0 | 1 (BNK1CA/BNK1CAM) |
| BNK1CCA | 0 | 0 | 0 | 0 | 1 (BNK1ACC/BNK1ACC) |
| BNK1CCS | 0 | 0 | 0 | 0 | 1 (BNK1CC/BNK1CCM) |
| BNK1CRA | 0 | 0 | 0 | 0 | 1 (BNK1CD/BNK1CDM) |
| BNK1DAC | 0 | 0 | 0 | 0 | 1 (BNK1DA/BNK1DAM) |
| BNK1DCS | 0 | 0 | 0 | 0 | 1 (BNK1DC/BNK1DCM) |
| BNK1TFN | 0 | 0 | 0 | 0 | 1 (BNK1TF/BNK1TFM) |
| BNK1UAC | 0 | 0 | 0 | 0 | 1 (BNK1UA/BNK1UAM) |
| BNKMENU | 0 | 0 | 0 | 0 | 1 (BNK1ME/BNK1MAI) |
| CRDTAGY1 | 0 | 0 | 0 | 0 | 0 |
| CRDTAGY2 | 0 | 0 | 0 | 0 | 0 |
| CRDTAGY3 | 0 | 0 | 0 | 0 | 0 |
| CRDTAGY4 | 0 | 0 | 0 | 0 | 0 |
| CRDTAGY5 | 0 | 0 | 0 | 0 | 0 |
| CREACC | 0 | 0 | 3 (ACCOUNT, PROCTRAN, CONTROL) | 0 | 0 |
| CRECUST | 1 (CUSTOMER read/update) | 1 (CUSTOMER write) | 1 (PROCTRAN) | 0 | 0 |
| DBCRFUN | 0 | 0 | 2 (ACCOUNT, PROCTRAN) | 0 | 0 |
| DELACC | 0 | 0 | 2 (ACCOUNT, PROCTRAN) | 0 | 0 |
| DELCUS | 1 (CUSTOMER read/delete) | 0 | 1 (PROCTRAN) | 0 | 0 |
| GETCOMPY | 0 | 0 | 0 | 0 | 0 |
| GETSCODE | 0 | 0 | 0 | 0 | 0 |
| INQACC | 0 | 0 | 1 (ACCOUNT) | 0 | 0 |
| INQACCCU | 0 | 0 | 1 (ACCOUNT) | 0 | 0 |
| INQCUST | 1 (CUSTOMER read/browse) | 0 | 0 | 0 | 0 |
| UPDACC | 0 | 0 | 1 (ACCOUNT) | 0 | 0 |
| UPDCUST | 1 (CUSTOMER read/update) | 0 | 0 | 0 | 0 |
| XFRFUN | 0 | 0 | 2 (ACCOUNT, PROCTRAN) | 0 | 0 |

> Note: BANKDATA accesses ACCOUNT and CONTROL tables plus CUSTOMER-FILE. CRECUST DB table count is PROCTRAN only; CUSTOMER is a VSAM file not a DB2 table. Screen program DB counts are 0 because all DB2 access is delegated to back-end programs via EXEC CICS LINK. CREACC and CRECUST also acquire CICS ENQ resource locks (HBNKACCT{sortcode} and HBNKCUST{sortcode} respectively) before reading/updating the counter; these are not shown in the MQ Queues column as they are synchronisation primitives, not data channels.

## Detailed I/O Map

| Program | Resource | Type | Direction | Access Pattern |
| ------- | -------- | ---- | --------- | -------------- |
| ABNDPROC | ABNDFILE | File (VSAM KSDS) | OUT | Keyed write (EXEC CICS WRITE FILE); key = ABND-VSAM-KEY (utime + taskno) |
| BANKDATA | CUSTOMER-FILE | File (VSAM KSDS) | OUT | Sequential load -- OPEN OUTPUT, WRITE CUSTOMER-RECORD-STRUCTURE using batch FD |
| BANKDATA | ACCOUNT | DB2 | OUT | INSERT (batch population); DELETE (purge by sort code) |
| BANKDATA | CONTROL | DB2 | OUT | INSERT (seed control counters); DELETE (purge) |
| BNK1CAC | BNK1CA / BNK1CAM | CICS BMS Map | BOTH | EXEC CICS RECEIVE MAP('BNK1CA') MAPSET('BNK1CAM'); EXEC CICS SEND MAP('BNK1CA') MAPSET('BNK1CAM') |
| BNK1CAC | CREACC | CICS Program Link | BOTH | EXEC CICS LINK PROGRAM('CREACC') -- create account |
| BNK1CCA | BNK1ACC / BNK1ACC | CICS BMS Map | BOTH | EXEC CICS SEND MAP('BNK1ACC') MAPSET('BNK1ACC') |
| BNK1CCA | INQACCCU | CICS Program Link | BOTH | EXEC CICS LINK PROGRAM(INQACCCU-PROGRAM) -- fetch accounts for customer |
| BNK1CCS | BNK1CC / BNK1CCM | CICS BMS Map | BOTH | EXEC CICS SEND MAP('BNK1CC') MAPSET('BNK1CCM') and RECEIVE MAP |
| BNK1CCS | CRECUST | CICS Program Link | BOTH | EXEC CICS LINK PROGRAM('CRECUST') -- create customer |
| BNK1CRA | BNK1CD / BNK1CDM | CICS BMS Map | BOTH | EXEC CICS SEND MAP('BNK1CD') MAPSET('BNK1CDM') and RECEIVE MAP |
| BNK1CRA | DBCRFUN | CICS Program Link | BOTH | EXEC CICS LINK PROGRAM('DBCRFUN') -- credit/debit function |
| BNK1DAC | BNK1DA / BNK1DAM | CICS BMS Map | BOTH | EXEC CICS SEND MAP('BNK1DA') MAPSET('BNK1DAM') and RECEIVE MAP |
| BNK1DAC | INQACC | CICS Program Link | BOTH | EXEC CICS LINK PROGRAM('INQACC') -- display account |
| BNK1DAC | DELACC | CICS Program Link | BOTH | EXEC CICS LINK PROGRAM('DELACC') -- delete account |
| BNK1DCS | BNK1DC / BNK1DCM | CICS BMS Map | BOTH | EXEC CICS SEND MAP('BNK1DC') MAPSET('BNK1DCM') and RECEIVE MAP |
| BNK1DCS | INQCUST | CICS Program Link | BOTH | EXEC CICS LINK PROGRAM('INQCUST') -- display customer |
| BNK1DCS | DELCUS | CICS Program Link | BOTH | EXEC CICS LINK PROGRAM('DELCUS') -- delete customer |
| BNK1DCS | UPDCUST | CICS Program Link | BOTH | EXEC CICS LINK PROGRAM('UPDCUST') -- update customer |
| BNK1TFN | BNK1TF / BNK1TFM | CICS BMS Map | BOTH | EXEC CICS SEND MAP('BNK1TF') MAPSET('BNK1TFM') and RECEIVE MAP |
| BNK1TFN | XFRFUN | CICS Program Link | BOTH | EXEC CICS LINK PROGRAM('XFRFUN') -- transfer funds |
| BNK1UAC | BNK1UA / BNK1UAM | CICS BMS Map | BOTH | EXEC CICS SEND MAP('BNK1UA') MAPSET('BNK1UAM') and RECEIVE MAP |
| BNK1UAC | INQACC | CICS Program Link | BOTH | EXEC CICS LINK PROGRAM('INQACC') -- fetch current account data |
| BNK1UAC | UPDACC | CICS Program Link | BOTH | EXEC CICS LINK PROGRAM('UPDACC') -- update account |
| BNKMENU | BNK1ME / BNK1MAI | CICS BMS Map | BOTH | EXEC CICS SEND MAP('BNK1ME') MAPSET('BNK1MAI') and RECEIVE MAP |
| BNKMENU | (transaction router) | CICS RETURN TRANSID | OUT | EXEC CICS RETURN TRANSID(ODCS/ODAC/OCCS/OCAC/OUAC/OCRA/OTFN/OCCA) |
| CRDTAGY1 | CIPCREDCHANN (container CIPA) | CICS Channel | BOTH | EXEC CICS GET CONTAINER('CIPA') CHANNEL('CIPCREDCHANN'); EXEC CICS PUT CONTAINER('CIPA') -- reads input customer data, writes back generated credit score |
| CRDTAGY2 | CIPCREDCHANN (container CIPB) | CICS Channel | BOTH | EXEC CICS GET CONTAINER('CIPB') CHANNEL('CIPCREDCHANN'); EXEC CICS PUT CONTAINER('CIPB') |
| CRDTAGY3 | CIPCREDCHANN (container CIPC) | CICS Channel | BOTH | EXEC CICS GET CONTAINER('CIPC') CHANNEL('CIPCREDCHANN'); EXEC CICS PUT CONTAINER('CIPC') |
| CRDTAGY4 | CIPCREDCHANN (container CIPD) | CICS Channel | BOTH | EXEC CICS GET CONTAINER('CIPD') CHANNEL('CIPCREDCHANN'); EXEC CICS PUT CONTAINER('CIPD') |
| CRDTAGY5 | CIPCREDCHANN (container CIPE) | CICS Channel | BOTH | EXEC CICS GET CONTAINER('CIPE') CHANNEL('CIPCREDCHANN'); EXEC CICS PUT CONTAINER('CIPE') |
| CREACC | ACCOUNT | DB2 | OUT | INSERT INTO ACCOUNT -- account creation |
| CREACC | PROCTRAN | DB2 | OUT | INSERT INTO PROCTRAN -- records account creation event |
| CREACC | CONTROL | DB2 | BOTH | SELECT FROM CONTROL (get last account number, key = '{sortcode}-ACCOUNT-LAST'); UPDATE CONTROL (increment counter) |
| CREACC | HBNKACCT{sortcode} | CICS ENQ Resource | BOTH | EXEC CICS ENQ RESOURCE(NCS-ACC-NO-NAME) LENGTH(16) -- acquires exclusive lock before reading/updating CONTROL; EXEC CICS DEQ releases lock on success or failure |
| CREACC | INQCUST | CICS Program Link | IN | EXEC CICS LINK PROGRAM('INQCUST ') -- verify customer exists before creating account |
| CREACC | INQACCCU | CICS Program Link | IN | EXEC CICS LINK PROGRAM('INQACCCU') -- check existing account count for customer |
| CRECUST | CUSTOMER | File (VSAM KSDS) | BOTH | EXEC CICS WRITE FILE('CUSTOMER') -- create new customer record (keyed by RIDFLD); EXEC CICS READ FILE('CUSTOMER') UPDATE + REWRITE -- update control record (key 0000009999999999) to increment customer counter |
| CRECUST | PROCTRAN | DB2 | OUT | INSERT INTO PROCTRAN -- records customer creation event |
| CRECUST | CIPCREDCHANN | CICS Channel | OUT | EXEC CICS PUT CONTAINER (containers CIPA-CIPE) with customer data; EXEC CICS RUN TRANSID (OCR1-OCR5 constructed at runtime) -- fires async credit scoring tasks |
| CRECUST | CIPCREDCHANN | CICS Channel | IN | EXEC CICS GET CONTAINER -- collect credit score results from child transactions after timeout |
| CRECUST | HBNKCUST{sortcode} | CICS ENQ Resource | BOTH | EXEC CICS ENQ RESOURCE(NCS-CUST-NO-NAME) LENGTH(16) -- acquires exclusive lock before reading/updating CUSTOMER control record; EXEC CICS DEQ releases lock on success or failure |
| DBCRFUN | ACCOUNT | DB2 | BOTH | SELECT FROM ACCOUNT (read balance and details); UPDATE ACCOUNT (apply debit/credit to available and actual balances) |
| DBCRFUN | PROCTRAN | DB2 | OUT | INSERT INTO PROCTRAN -- records debit/credit transaction |
| DELACC | ACCOUNT | DB2 | BOTH | SELECT FROM ACCOUNT (validate account exists and retrieve details); DELETE FROM ACCOUNT |
| DELACC | PROCTRAN | DB2 | OUT | INSERT INTO PROCTRAN -- records account deletion |
| DELCUS | CUSTOMER | File (VSAM KSDS) | BOTH | EXEC CICS READ FILE('CUSTOMER') UPDATE -- read with update lock; EXEC CICS DELETE FILE('CUSTOMER') TOKEN -- delete customer record |
| DELCUS | PROCTRAN | DB2 | OUT | INSERT INTO PROCTRAN -- records customer deletion |
| DELCUS | INQCUST | CICS Program Link | IN | EXEC CICS LINK PROGRAM(INQCUST-PROGRAM) -- verify customer before delete |
| DELCUS | INQACCCU | CICS Program Link | IN | EXEC CICS LINK PROGRAM('INQACCCU') -- get list of accounts to be deleted |
| DELCUS | DELACC | CICS Program Link | OUT | EXEC CICS LINK PROGRAM('DELACC  ') -- delete each account before removing customer |
| GETCOMPY | DFHCOMMAREA | CICS Commarea | OUT | Populates company-name PIC X(40) with literal 'CICS Bank Sample Application'; EXEC CICS RETURN; called from Java web layer only |
| GETSCODE | DFHCOMMAREA | CICS Commarea | OUT | Populates SORTCODE PIC X(6) with literal 987654; EXEC CICS RETURN; called from Java web layer only |
| INQACC | ACCOUNT | DB2 | IN | EXEC SQL DECLARE ACC-CURSOR + OPEN + FETCH -- cursor read by sort code + account number (loop until SQLCODE=100); also singleton SELECT for specific account lookup |
| INQACCCU | ACCOUNT | DB2 | IN | EXEC SQL DECLARE ACC-CURSOR + OPEN + FETCH -- cursor read by customer number + sort code (up to 20 accounts fetched) |
| INQACCCU | INQCUST | CICS Program Link | IN | EXEC CICS LINK PROGRAM('INQCUST ') -- cross-reference customer details |
| INQCUST | CUSTOMER | File (VSAM KSDS) | IN | EXEC CICS READ FILE('CUSTOMER') keyed direct (RIDFLD = sort code + customer number); EXEC CICS STARTBR / READPREV / ENDBR -- backward browse for last customer lookup |
| UPDACC | ACCOUNT | DB2 | BOTH | SELECT FROM ACCOUNT (read current values); UPDATE ACCOUNT (update type, interest rate, overdraft limit, statement dates) |
| UPDCUST | CUSTOMER | File (VSAM KSDS) | BOTH | EXEC CICS READ FILE('CUSTOMER') UPDATE -- read with update lock using DESIRED-CUST-KEY; EXEC CICS REWRITE FILE('CUSTOMER') -- update customer fields in place |
| XFRFUN | ACCOUNT | DB2 | BOTH | SELECT FROM ACCOUNT x2 (from-account and to-account); UPDATE ACCOUNT x2 (debit source balance, credit destination balance) |
| XFRFUN | PROCTRAN | DB2 | OUT | INSERT INTO PROCTRAN -- records funds transfer |

## Shared Resources

Resources accessed by multiple programs:

| Resource | Type | Read By | Written By |
| -------- | ---- | ------- | ---------- |
| CUSTOMER | File (VSAM KSDS) | INQCUST, DELCUS, UPDCUST, CRECUST (control record read) | CRECUST (new customer + control record rewrite), UPDCUST (rewrite), BANKDATA (batch initialisation) |
| CUSTOMER (delete) | File (VSAM KSDS) | -- | DELCUS (EXEC CICS DELETE) |
| ACCOUNT | DB2 Table | INQACC, INQACCCU, UPDACC, DELACC, DBCRFUN, XFRFUN, CREACC | BANKDATA, CREACC, UPDACC, DELACC, DBCRFUN, XFRFUN |
| PROCTRAN | DB2 Table | (none in source -- audit log, read externally for reporting) | CRECUST, CREACC, DELACC, DELCUS, DBCRFUN, XFRFUN |
| CONTROL | DB2 Table | CREACC (SELECT to get last account number) | BANKDATA (INSERT seed, DELETE purge), CREACC (UPDATE increment) |
| ABNDFILE | File (VSAM KSDS) | (none in source -- diagnostic read only) | ABNDPROC |
| CIPCREDCHANN | CICS Channel | CRECUST (GET results), CRDTAGY1-5 (GET input data) | CRECUST (PUT input data), CRDTAGY1-5 (PUT credit score results) |
| HBNKACCT{sortcode} | CICS ENQ Resource | -- | CREACC (ENQ before counter read; DEQ after update) |
| HBNKCUST{sortcode} | CICS ENQ Resource | -- | CRECUST (ENQ before counter read; DEQ after update) |
