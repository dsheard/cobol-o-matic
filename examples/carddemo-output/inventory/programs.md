---
type: inventory
subtype: programs
status: draft
confidence: high
last_pass: 5
---

# Program Inventory

Catalog of all COBOL programs found in the source directory.

## Programs

| Program | Source File | Type | LOC | Copybooks Used | Purpose |
| -------------- | -------------- | ------------------------- | --- | -------------- | --------------- |
| CBACT01C | CBACT01C.cbl | batch | 431 | CVACT01Y, CODATECN | Read account VSAM file and write to output, array, and variable-length record files |
| CBACT02C | CBACT02C.cbl | batch | 179 | CVACT02Y | Read and print card data VSAM file |
| CBACT03C | CBACT03C.cbl | batch | 179 | CVACT03Y | Read and print account cross-reference VSAM file |
| CBACT04C | CBACT04C.cbl | batch | 652 | CVTRA01Y, CVACT03Y, CVTRA02Y, CVACT01Y, CVTRA05Y | Interest and fees calculator; reads transaction category balance file and updates accounts |
| CBCUS01C | CBCUS01C.cbl | batch | 179 | CVCUS01Y | Read and print customer data VSAM file |
| CBEXPORT | CBEXPORT.cbl | batch | 583 | CVCUS01Y, CVACT01Y, CVACT03Y, CVTRA05Y, CVACT02Y, CVEXPORT | Export customer, account, card, xref and transaction data to multi-record export file for branch migration |
| CBIMPORT | CBIMPORT.cbl | batch | 488 | CVCUS01Y, CVACT01Y, CVACT03Y, CVTRA05Y, CVACT02Y, CVEXPORT | Import multi-record export file and split into separate normalised VSAM target files |
| CBSTM03A | CBSTM03A.CBL | batch | 925 | COSTM01, CVACT03Y, CUSTREC, CVACT01Y | Generate account statements in plain text and HTML formats; reads XREF, CUST, ACCT, and TRNX VSAM files via CBSTM03B subroutine; uses TIOT control block addressing |
| CBSTM03B | CBSTM03B.CBL | subprogram | 231 | (none) | File I/O subroutine for CBSTM03A; handles open/read/close for TRNXFILE, XREFFILE, CUSTFILE, and ACCTFILE VSAM files via LINKAGE parameter |
| CBTRN01C | CBTRN01C.cbl | batch | 495 | CVTRA06Y, CVCUS01Y, CVACT03Y, CVACT02Y, CVACT01Y, CVTRA05Y | Read daily transaction file, verify card cross-reference, and look up account |
| CBTRN02C | CBTRN02C.cbl | batch | 731 | CVTRA06Y, CVTRA05Y, CVACT03Y, CVACT01Y, CVTRA01Y | Post daily transaction file records; update transaction category balance and transaction master VSAM |
| CBTRN03C | CBTRN03C.cbl | batch | 649 | CVTRA05Y, CVACT03Y, CVTRA03Y, CVTRA04Y, CVTRA07Y | Print formatted transaction detail report |
| COACTUPC | COACTUPC.cbl | online (CICS) | 3860 | CVCRD01Y, CSLKPCDY, COTTL01Y, COACTUP, CSDAT01Y, CSMSG01Y, CSMSG02Y, CSUSR01Y, CVACT01Y, CVACT03Y, CVCUS01Y, COCOM01Y, CSSETATY, CSSTRPFY, CSUTLDPY, CSUTLDWY | Accept and process account update via CICS screen; full field editing and VSAM updates; transaction CAUP |
| COACTVWC | COACTVWC.cbl | online (CICS) | 940 | CVCRD01Y, COCOM01Y, COTTL01Y, COACTVW, CSDAT01Y, CSMSG01Y, CSMSG02Y, CSUSR01Y, CVACT01Y, CVACT02Y, CVACT03Y, CVCUS01Y, CSSTRPFY | Accept and process account view request via CICS screen; transaction CAVW |
| COADM01C | COADM01C.cbl | online (CICS) | 286 | COCOM01Y, COADM02Y, COADM01, COTTL01Y, CSDAT01Y, CSMSG01Y, CSUSR01Y | Admin menu for admin users; transaction CA00 |
| COBIL00C | COBIL00C.cbl | online (CICS) | 499 | COCOM01Y, COBIL00, COTTL01Y, CSDAT01Y, CSMSG01Y, CVACT01Y, CVACT03Y, CVTRA05Y | Bill payment screen; pay account balance and post transaction; transaction CB00 |
| COBSWAIT | COBSWAIT.cbl | batch | 41 | (none) | Utility program to pause execution; accepts wait time in centiseconds via SYSIN |
| COCRDLIC | COCRDLIC.cbl | online (CICS) | 1458 | CVCRD01Y, COCOM01Y, COTTL01Y, COCRDLI, CSDAT01Y, CSMSG01Y, CSUSR01Y, CVACT02Y, CSSTRPFY | List credit cards; all cards for admin users, or only cards linked to account in COMMAREA; transaction CCLI |
| COCRDSLC | COCRDSLC.cbl | online (CICS) | 887 | CVCRD01Y, COCOM01Y, COTTL01Y, COCRDSL, CSDAT01Y, CSMSG01Y, CSMSG02Y, CSUSR01Y, CVACT02Y, CVCUS01Y, CSSTRPFY | Accept and process credit card detail request (card select/view); transaction CCDL |
| COCRDUPC | COCRDUPC.cbl | online (CICS) | 1560 | CVCRD01Y, COCOM01Y, COTTL01Y, COCRDUP, CSDAT01Y, CSMSG01Y, CSMSG02Y, CSUSR01Y, CVACT02Y, CVCUS01Y, CSSTRPFY | Accept and process credit card detail update; transaction CCUP |
| COMEN01C | COMEN01C.cbl | online (CICS) | 266 | COCOM01Y, COMEN02Y, COMEN01, COTTL01Y, CSDAT01Y, CSMSG01Y, CSUSR01Y | Main menu for regular users; transaction CM00 |
| CORPT00C | CORPT00C.cbl | online (CICS) | 561 | COCOM01Y, CORPT00, COTTL01Y, CSDAT01Y, CSMSG01Y, CVTRA05Y | Print transaction reports by submitting a batch job via extra-partition TDQ (JOBS); transaction CR00 |
| COSGN00C | COSGN00C.cbl | online (CICS) | 221 | COCOM01Y, COSGN00, COTTL01Y, CSDAT01Y, CSMSG01Y, CSUSR01Y | Signon screen for CardDemo application; transaction CC00 |
| COTRN00C | COTRN00C.cbl | online (CICS) | 611 | COCOM01Y, COTRN00, COTTL01Y, CSDAT01Y, CSMSG01Y, CVTRA05Y | List transactions from TRANSACT VSAM file; transaction CT00 |
| COTRN01C | COTRN01C.cbl | online (CICS) | 288 | COCOM01Y, COTRN01, COTTL01Y, CSDAT01Y, CSMSG01Y, CVTRA05Y | View a single transaction from TRANSACT file; transaction CT01 |
| COTRN02C | COTRN02C.cbl | online (CICS) | 699 | COCOM01Y, COTRN02, COTTL01Y, CSDAT01Y, CSMSG01Y, CVTRA05Y, CVACT01Y, CVACT03Y | Add a new transaction to TRANSACT VSAM file; transaction CT02 |
| COUSR00C | COUSR00C.cbl | online (CICS) | 612 | COCOM01Y, COUSR00, COTTL01Y, CSDAT01Y, CSMSG01Y, CSUSR01Y | List all users from USRSEC VSAM file; transaction CU00 |
| COUSR01C | COUSR01C.cbl | online (CICS) | 259 | COCOM01Y, COUSR01, COTTL01Y, CSDAT01Y, CSMSG01Y, CSUSR01Y | Add a new regular or admin user to USRSEC file; transaction CU01 |
| COUSR02C | COUSR02C.cbl | online (CICS) | 366 | COCOM01Y, COUSR02, COTTL01Y, CSDAT01Y, CSMSG01Y, CSUSR01Y | Update an existing user in USRSEC file; transaction CU02 |
| COUSR03C | COUSR03C.cbl | online (CICS) | 315 | COCOM01Y, COUSR03, COTTL01Y, CSDAT01Y, CSMSG01Y, CSUSR01Y | Delete a user from USRSEC file; transaction CU03 |
| CSUTLDTC | CSUTLDTC.cbl | subprogram | 158 | (none) | Date validation utility; wraps the CEEDAYS LE API to validate and convert date strings; called by COTRN02C, CORPT00C |

## Program Type Distribution

| Type | Count |
| ---------- | ----- |
| Batch | 11 |
| Online (CICS) | 17 |
| Subprogram | 2 |
| **Total** | **31** |

## CICS Transaction Map

Transaction IDs from CARDDEMO.CSD:

| Transaction ID | Program | Description |
| -------------- | ------- | ----------- |
| CC00 | COSGN00C | Signon / entry point |
| CM00 | COMEN01C | Main menu (regular users) |
| CA00 | COADM01C | Admin menu |
| CB00 | COBIL00C | Bill payment |
| CCLI | COCRDLIC | Credit card list |
| CCDL | COCRDSLC | Credit card detail view |
| CCUP | COCRDUPC | Credit card update |
| CAVW | COACTVWC | Account view |
| CAUP | COACTUPC | Account update |
| CR00 | CORPT00C | Report request |
| CT00 | COTRN00C | Transaction list |
| CT01 | COTRN01C | Transaction view |
| CT02 | COTRN02C | Add transaction |
| CU00 | COUSR00C | User list |
| CU01 | COUSR01C | Add user |
| CU02 | COUSR02C | Update user |
| CU03 | COUSR03C | Delete user |
| CDV1 | COCRDSEC | Developer transaction (program not in source) |

## Unresolved References

Programs referenced via CALL but not found in the source directory:

| Called Program | Called From |
| -------------- | ----------------- |
| COBDATFT | CBACT01C |
| MVSWAIT | COBSWAIT |
| CEE3ABD | CBACT01C, CBACT02C, CBACT03C, CBACT04C, CBCUS01C, CBEXPORT, CBIMPORT, CBTRN01C, CBTRN02C, CBTRN03C, CBSTM03A |
| CEEDAYS | CSUTLDTC (internal LE call) |

## CSD-Defined Programs With No Source

Programs defined in CARDDEMO.CSD but no matching .cbl source file found:

| Program | Transaction | Description |
| ------- | ----------- | ----------- |
| COCRDSEC | CDV1 | Credit card search -- developer transaction; source not present in cbl/ directory |
