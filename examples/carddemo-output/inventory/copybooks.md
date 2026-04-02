---
type: inventory
subtype: copybooks
status: draft
confidence: high
last_pass: 5
---

# Copybook Inventory

Catalog of all copybooks (COPY members) found in the source directory.

## Copybooks

### Data Copybooks (cpy/)

| Copybook | Source File | Used By | Fields | Purpose |
| ----------- | -------------- | -------------- | ------ | --------------- |
| COADM02Y | COADM02Y.cpy | COADM01C | ~5 | Admin screen working-storage variables |
| COCOM01Y | COCOM01Y.cpy | COADM01C, COBIL00C, COACTUPC, COACTVWC, COCRDLIC, COCRDSLC, COCRDUPC, COMEN01C, CORPT00C, COSGN00C, COTRN00C, COTRN01C, COTRN02C, COUSR00C, COUSR01C, COUSR02C, COUSR03C | 15 | CICS communication area (COMMAREA) layout shared by all online programs; carries navigation context, user ID, user type, customer and account info |
| CODATECN | CODATECN.cpy | CBACT01C | ~5 | Date conversion input/output record passed to the COBDATFT assembler routine |
| COMEN02Y | COMEN02Y.cpy | COMEN01C | ~5 | Main menu working-storage or screen field definitions for regular-user menu |
| COSTM01 | COSTM01.CPY | CBSTM03A | ~15 | Transaction record layout for statement reporting (TRNX-RECORD with card number, transaction ID, type, category, description, amount, merchant, and timestamp fields) |
| COTTL01Y | COTTL01Y.cpy | COADM01C, COACTUPC, COACTVWC, COBIL00C, COCRDLIC, COCRDSLC, COCRDUPC, COMEN01C, CORPT00C, COSGN00C, COTRN00C, COTRN01C, COTRN02C, COUSR00C, COUSR01C, COUSR02C, COUSR03C | ~10 | Screen title and header line definitions shared by online programs |
| CSDAT01Y | CSDAT01Y.cpy | COADM01C, COACTUPC, COACTVWC, COBIL00C, COCRDLIC, COCRDSLC, COCRDUPC, COMEN01C, CORPT00C, COSGN00C, COTRN00C, COTRN01C, COTRN02C, COUSR00C, COUSR01C, COUSR02C, COUSR03C | ~10 | Date working-storage fields used by online programs for display and validation |
| CSLKPCDY | CSLKPCDY.cpy | COACTUPC | ~5 | Lookup code working-storage fields used in account update |
| CSMSG01Y | CSMSG01Y.cpy | COADM01C, COACTUPC, COACTVWC, COBIL00C, COCRDLIC, COCRDSLC, COCRDUPC, COMEN01C, CORPT00C, COSGN00C, COTRN00C, COTRN01C, COTRN02C, COUSR00C, COUSR01C, COUSR02C, COUSR03C | ~5 | Standard message area (primary message line) for online screens |
| CSMSG02Y | CSMSG02Y.cpy | COACTUPC, COACTVWC, COCRDSLC, COCRDUPC | ~5 | Secondary message area for online screens |
| CSSETATY | CSSETATY.cpy | COACTUPC | ~3 | Screen attribute setting code snippet, used repeatedly via COPY REPLACING in COACTUPC |
| CSSTRPFY | CSSTRPFY.cpy | COACTUPC, COACTVWC, COCRDLIC, COCRDSLC, COCRDUPC | ~10 | String pad/format procedure division code shared by several CICS programs |
| CSUSR01Y | CSUSR01Y.cpy | COADM01C, COACTUPC, COACTVWC, COCRDLIC, COCRDSLC, COCRDUPC, COMEN01C, COSGN00C, COUSR00C, COUSR01C, COUSR02C, COUSR03C | ~10 | User security record layout (USRSEC file) |
| CSUTLDPY | CSUTLDPY.cpy | COACTUPC | ~20 | Procedure division date utility paragraphs (working storage counterpart) |
| CSUTLDWY | CSUTLDWY.cpy | COACTUPC | ~10 | Working-storage fields for the date utility (CSUTLDTC support area); included via single-quoted COPY syntax |
| CUSTREC | CUSTREC.cpy | CBSTM03A | ~20 | Customer record layout used by CBSTM03A for statement address and name fields |
| CVACT01Y | CVACT01Y.cpy | CBACT01C, CBEXPORT, CBIMPORT, CBTRN01C, CBTRN02C, CBACT04C, COACTUPC, COACTVWC, COBIL00C, COTRN02C, CBSTM03A | 12 | Account record layout (ACCTDAT VSAM, 300 bytes) |
| CVACT02Y | CVACT02Y.cpy | CBACT02C, CBEXPORT, CBIMPORT, CBTRN01C, COACTVWC, COCRDLIC, COCRDSLC, COCRDUPC | 6 | Card record layout (CARDDATA VSAM, 150 bytes) |
| CVACT03Y | CVACT03Y.cpy | CBACT03C, CBEXPORT, CBIMPORT, CBTRN01C, CBTRN02C, CBTRN03C, CBACT04C, COACTUPC, COACTVWC, COBIL00C, COTRN02C, CBSTM03A | 4 | Card cross-reference record layout (CARDXREF VSAM, 50 bytes) |
| CVCRD01Y | CVCRD01Y.cpy | COACTUPC, COACTVWC, COCRDLIC, COCRDSLC, COCRDUPC | ~8 | Credit card entity working-storage fields used by card-related CICS programs |
| CVCUS01Y | CVCUS01Y.cpy | CBCUS01C, CBEXPORT, CBIMPORT, CBTRN01C, COACTUPC, COACTVWC, COCRDSLC, COCRDUPC | 18 | Customer record layout (CUSTDATA VSAM, 500 bytes) |
| CVEXPORT | CVEXPORT.cpy | CBEXPORT, CBIMPORT | ~40 | Multi-record export file layout with REDEFINES structure for types C/A/X/T/D (500 bytes) |
| CVTRA01Y | CVTRA01Y.cpy | CBACT04C, CBTRN02C | ~10 | Transaction category balance record layout |
| CVTRA02Y | CVTRA02Y.cpy | CBACT04C | ~10 | Secondary transaction category balance layout |
| CVTRA03Y | CVTRA03Y.cpy | CBTRN03C | ~10 | Transaction report format record layout |
| CVTRA04Y | CVTRA04Y.cpy | CBTRN03C | ~10 | Transaction type code table record layout |
| CVTRA05Y | CVTRA05Y.cpy | CBEXPORT, CBIMPORT, CBTRN01C, CBTRN02C, CBTRN03C, CBACT04C, COBIL00C, CORPT00C, COTRN00C, COTRN01C, COTRN02C | ~15 | Transaction master record layout (TRANSACT VSAM, 350 bytes) |
| CVTRA06Y | CVTRA06Y.cpy | CBTRN01C, CBTRN02C | ~10 | Daily transaction input record layout (DALYTRAN sequential file) |
| CVTRA07Y | CVTRA07Y.cpy | CBTRN03C | ~10 | Transaction category code table record layout |
| UNUSED1Y | UNUSED1Y.cpy | (none) | 6 | User data record layout -- not referenced by any program in the source set |

### BMS-Generated Copybooks (cpy-bms/)

| Copybook | Source File | Used By | Fields | Purpose |
| ----------- | -------------- | -------------- | ------ | --------------- |
| COACTUP | COACTUP.CPY | COACTUPC | ~80 | BMS-generated symbolic map for account update screen (COACTUPS mapset) |
| COACTVW | COACTVW.CPY | COACTVWC | ~60 | BMS-generated symbolic map for account view screen (COACTVWS mapset) |
| COADM01 | COADM01.CPY | COADM01C | ~30 | BMS-generated symbolic map for admin menu screen |
| COBIL00 | COBIL00.CPY | COBIL00C | ~40 | BMS-generated symbolic map for bill payment screen |
| COCRDLI | COCRDLI.CPY | COCRDLIC | ~60 | BMS-generated symbolic map for credit card list screen |
| COCRDSL | COCRDSL.CPY | COCRDSLC | ~60 | BMS-generated symbolic map for credit card select/detail screen |
| COCRDUP | COCRDUP.CPY | COCRDUPC | ~60 | BMS-generated symbolic map for credit card update screen |
| COMEN01 | COMEN01.CPY | COMEN01C | ~30 | BMS-generated symbolic map for regular-user main menu |
| CORPT00 | CORPT00.CPY | CORPT00C | ~30 | BMS-generated symbolic map for report request screen |
| COSGN00 | COSGN00.CPY | COSGN00C | ~20 | BMS-generated symbolic map for signon screen |
| COTRN00 | COTRN00.CPY | COTRN00C | ~50 | BMS-generated symbolic map for transaction list screen |
| COTRN01 | COTRN01.CPY | COTRN01C | ~40 | BMS-generated symbolic map for transaction view screen |
| COTRN02 | COTRN02.CPY | COTRN02C | ~40 | BMS-generated symbolic map for add-transaction screen |
| COUSR00 | COUSR00.CPY | COUSR00C | ~40 | BMS-generated symbolic map for user list screen |
| COUSR01 | COUSR01.CPY | COUSR01C | ~30 | BMS-generated symbolic map for add-user screen |
| COUSR02 | COUSR02.CPY | COUSR02C | ~30 | BMS-generated symbolic map for update-user screen |
| COUSR03 | COUSR03.CPY | COUSR03C | ~30 | BMS-generated symbolic map for delete-user screen |

## Orphan Copybooks

Copybooks in the source directory not referenced by any analysed program:

- UNUSED1Y

## Missing Copybooks

Copybooks referenced by COPY statements but not found in the source directory:

| Copybook | Referenced By |
| ----------- | -------------- |
| (none) | -- |

> Note: All referenced copybooks resolve to either cpy/ or cpy-bms/. CUSTREC was previously flagged as an orphan but is used by CBSTM03A. CODATECN.cpy exists in the cpy/ directory and resolves correctly. CSUTLDWY is included via single-quoted syntax (`COPY 'CSUTLDWY'`) in COACTUPC and resolves correctly. System copybooks DFHAID and DFHBMSCA are excluded as standard CICS-supplied members. COCRDLIC was confirmed in iteration 4 to use CSDAT01Y (corrected from iteration 3 omission).
