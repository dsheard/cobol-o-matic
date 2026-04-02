---
type: inventory
subtype: jcl-jobs
status: draft
confidence: high
last_pass: 2
---

# JCL Job Inventory

Catalog of all JCL jobs found in the source directory.

## Jobs

### buildjcl -- Procedures

| Job Name | Source File | Steps | Programs Executed | Purpose |
| -------- | ----------- | ----- | ----------------- | ------- |
| CICS (proc) | buildjcl/CICS.jcl | 2 | IGYCRCTL, IEWL | Reusable JCL procedure for compiling and link-editing CICS COBOL programs (CICS translator option enabled). Referenced by all individual CICS program build jobs. |
| BATCH (proc) | buildjcl/BATCH.jcl | 2 | IGYCRCTL, IEWL | Reusable JCL procedure for compiling and link-editing batch COBOL programs (no CICS translator). Referenced by batch program build jobs. |
| DEFAULT (vars) | buildjcl/DEFAULT.jcl | 0 | (none) | JCL SET statements defining site HLQs: CICSHLQ, CBSAHLQ, LEHLQ, COBOLHLQ, DB2HLQ. Included by all build jobs. |
| MAPGEN (proc) | buildjcl/MAPGEN.jcl | 1 | DFHEAP1$ (BMS Assembler) | Procedure to assemble BMS map source members and link-edit map load modules. |

### buildjcl -- COBOL Program Build Jobs

| Job Name | Source File | Steps | Programs Executed | Purpose |
| -------- | ----------- | ----- | ----------------- | ------- |
| COMPALL | buildjcl/COMPALL.jcl | 35+ | IGYCRCTL (COBOL), IEWL (Linkage Editor) | Compile-and-link all CBSA programs and BMS maps in one job; invokes CICS and BATCH compile procedures for each program. |
| ABNDPROC (build) | buildjcl/ABNDPROC.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS ABNDPROC program. |
| ACCLOAD (build) | buildjcl/ACCLOAD.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit batch program ACCLOAD (source not in base cobol_src; referenced build job only). |
| ACCOFFL (build) | buildjcl/ACCOFFL.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit batch program ACCOFFL (source not in base cobol_src; referenced build job only). |
| BANKDATA (build) | buildjcl/BANKDATA.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the batch BANKDATA program using the BATCH procedure. |
| BNK1CAC (build) | buildjcl/BNK1CAC.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS BNK1CAC program. |
| BNK1CCA (build) | buildjcl/BNK1CCA.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS BNK1CCA program. |
| BNK1CCS (build) | buildjcl/BNK1CCS.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS BNK1CCS program. |
| BNK1CRA (build) | buildjcl/BNK1CRA.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS BNK1CRA program. |
| BNK1DAC (build) | buildjcl/BNK1DAC.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS BNK1DAC program. |
| BNK1DCS (build) | buildjcl/BNK1DCS.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS BNK1DCS program. |
| BNK1TFN (build) | buildjcl/BNK1TFN.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS BNK1TFN program. |
| BNK1UAC (build) | buildjcl/BNK1UAC.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS BNK1UAC program. |
| BNKMENU (build) | buildjcl/BNKMENU.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS BNKMENU program. |
| CRDTAGY1 (build) | buildjcl/CRDTAGY1.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit CRDTAGY1. |
| CRDTAGY2 (build) | buildjcl/CRDTAGY2.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit CRDTAGY2. |
| CRDTAGY3 (build) | buildjcl/CRDTAGY3.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit CRDTAGY3. |
| CRDTAGY4 (build) | buildjcl/CRDTAGY4.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit CRDTAGY4. |
| CRDTAGY5 (build) | buildjcl/CRDTAGY5.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit CRDTAGY5. |
| CREACC (build) | buildjcl/CREACC.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS CREACC program using the CICS procedure. |
| CRECUST (build) | buildjcl/CRECUST.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS CRECUST program using the CICS procedure. |
| DBCRFUN (build) | buildjcl/DBCRFUN.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS DBCRFUN program using the CICS procedure. |
| DELACC (build) | buildjcl/DELACC.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS DELACC program using the CICS procedure. |
| DELCUS (build) | buildjcl/DELCUS.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS DELCUS program using the CICS procedure. |
| EXTDCUST (build) | buildjcl/EXTDCUST.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit batch program EXTDCUST (source not in base cobol_src; referenced build job only). |
| GETCOMPY (build) | buildjcl/GETCOMPY.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS GETCOMPY program. |
| GETSCODE (build) | buildjcl/GETSCODE.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS GETSCODE program. |
| INQACC (build) | buildjcl/INQACC.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS INQACC program using the CICS procedure. |
| INQACCCU (build) | buildjcl/INQACCCU.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS INQACCCU program using the CICS procedure. |
| INQCUST (build) | buildjcl/INQCUST.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS INQCUST program using the CICS procedure. |
| UPDACC (build) | buildjcl/UPDACC.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS UPDACC program using the CICS procedure. |
| UPDCUST (build) | buildjcl/UPDCUST.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS UPDCUST program using the CICS procedure. |
| XFRFUN (build) | buildjcl/XFRFUN.jcl | 2 | IGYCRCTL, IEWL | Compile and link-edit the CICS XFRFUN program using the CICS procedure. |

### buildjcl -- BMS Map Assembly Jobs

| Job Name | Source File | Steps | Programs Executed | Purpose |
| -------- | ----------- | ----- | ----------------- | ------- |
| BNK1ACC (mapbld) | buildjcl/BNK1ACC.jcl | 1 | DFHEAP1$ | Assemble and link-edit BMS map BNK1ACC (account-list map for BNK1CCA). |
| BNK1CAM (mapbld) | buildjcl/BNK1CAM.jcl | 1 | DFHEAP1$ | Assemble and link-edit BMS map BNK1CAM (create-account map for BNK1CAC). |
| BNK1CCM (mapbld) | buildjcl/BNK1CCM.jcl | 1 | DFHEAP1$ | Assemble and link-edit BMS map BNK1CCM (create-customer map for BNK1CCS). |
| BNK1CDM (mapbld) | buildjcl/BNK1CDM.jcl | 1 | DFHEAP1$ | Assemble and link-edit BMS map BNK1CDM (credit/debit map for BNK1CRA). |
| BNK1DAM (mapbld) | buildjcl/BNK1DAM.jcl | 1 | DFHEAP1$ | Assemble and link-edit BMS map BNK1DAM (display-account map for BNK1DAC). |
| BNK1DCM (mapbld) | buildjcl/BNK1DCM.jcl | 1 | DFHEAP1$ | Assemble and link-edit BMS map BNK1DCM (display-customer map for BNK1DCS). |
| BNK1MAI (mapbld) | buildjcl/BNK1MAI.jcl | 1 | DFHEAP1$ | Assemble and link-edit BMS map BNK1MAI (main menu map for BNKMENU). |
| BNK1TFM (mapbld) | buildjcl/BNK1TFM.jcl | 1 | DFHEAP1$ | Assemble and link-edit BMS map BNK1TFM (transfer-funds map for BNK1TFN). |
| BNK1UAM (mapbld) | buildjcl/BNK1UAM.jcl | 1 | DFHEAP1$ | Assemble and link-edit BMS map BNK1UAM (update-account map for BNK1UAC). |

### db2jcl -- DB2 Schema Creation Jobs

| Job Name | Source File | Steps | Programs Executed | Purpose |
| -------- | ----------- | ----- | ----------------- | ------- |
| DEFAULT (vars) | db2jcl/DEFAULT.jcl | 0 | (none) | JCL SET statements defining DB2 site variables: DB2HLQ, DB2SYS, DB2OWNER, BANKDBRM, BANKPLAN, BANKPKGE, DSNTEPP, DSNTEPL, BANKUSER. Included by parameterised db2jcl jobs. |
| INSTDB2 | db2jcl/INSTDB2.jcl | 1 | IKJEFT01 / DSNTEP2 | Creates the CBSA DB2 database, tablespaces, tables (ACCOUNT, PROCTRAN, CONTROL) and indexes using DSNTEP2. |
| DB2BIND | db2jcl/DB2BIND.jcl | 2 | IKJEFT01 | Binds DB2 packages for all SQL programs (CREACC, CRECUST, DBCRFUN, DELACC, DELCUS, INQACC, INQACCCU, BANKDATA, UPDACC, XFRFUN) into a plan, then grants execute authority. |
| BTCHSQL | db2jcl/BTCHSQL.jcl | 1 | IKJEFT01 / DSNTEP2 | Utility job for running ad-hoc SQL statements against the CBSA DB2 subsystem. |
| CREDB00 | db2jcl/CREDB00.jcl | 1 | IKJEFT01 / DSNTEP2 | Creates the top-level CBSA DB2 database object. |
| CRESG01 | db2jcl/CRESG01.jcl | 1 | IKJEFT01 / DSNTEP2 | Creates the ACCOUNT DB2 stogroup. |
| CRESG02 | db2jcl/CRESG02.jcl | 1 | IKJEFT01 / DSNTEP2 | Creates the PROCTRAN DB2 stogroup. |
| CRESG03 | db2jcl/CRESG03.jcl | 1 | IKJEFT01 / DSNTEP2 | Creates the CONTROL DB2 stogroup. |
| CRETS01 | db2jcl/CRETS01.jcl | 1 | IKJEFT01 / DSNTEP2 | Creates the ACCOUNT tablespace in the CBSA database using stogroup ACCOUNT. |
| CRETS02 | db2jcl/CRETS02.jcl | 1 | IKJEFT01 / DSNTEP2 | Creates the PROCTRAN tablespace in the CBSA database using stogroup PROCTRAN. |
| CRETS03 | db2jcl/CRETS03.jcl | 1 | IKJEFT01 / DSNTEP2 | Creates the CONTROL tablespace in the CBSA database using stogroup CONTROL. |
| CRETB01 | db2jcl/CRETB01.jcl | 1 | IKJEFT01 / DSNTEP2 | Creates the ACCOUNT tablespace and table. |
| CRETB02 | db2jcl/CRETB02.jcl | 1 | IKJEFT01 / DSNTEP2 | Creates the PROCTRAN tablespace and table. |
| CRETB03 | db2jcl/CRETB03.jcl | 1 | IKJEFT01 / DSNTEP2 | Creates the CONTROL tablespace and table. |
| CREI101 | db2jcl/CREI101.jcl | 1 | IKJEFT01 / DSNTEP2 | Creates unique index ACCTINDX on ACCOUNT(ACCOUNT_SORTCODE, ACCOUNT_NUMBER). |
| CREI201 | db2jcl/CREI201.jcl | 1 | IKJEFT01 / DSNTEP2 | Creates index ACCTCUST on ACCOUNT(ACCOUNT_SORTCODE, ACCOUNT_CUSTOMER_NUMBER). |
| CREI301 | db2jcl/CREI301.jcl | 1 | IKJEFT01 / DSNTEP2 | Creates unique index CONTINDX on CONTROL(CONTROL_NAME). |

### db2jcl -- DB2 Schema Drop Jobs

| Job Name | Source File | Steps | Programs Executed | Purpose |
| -------- | ----------- | ----- | ----------------- | ------- |
| DRPDB00 | db2jcl/DRPDB00.jcl | 1 | IKJEFT01 / DSNTEP2 | Drops the CBSA DB2 database. |
| DROPDB2 | db2jcl/DROPDB2.jcl | 1 | IKJEFT01 / DSNTEP2 | Drops the entire CBSA DB2 database (destructive uninstall). |
| DRPSG01 | db2jcl/DRPSG01.jcl | 1 | IKJEFT01 / DSNTEP2 | Drops the ACCOUNT stogroup. |
| DRPSG02 | db2jcl/DRPSG02.jcl | 1 | IKJEFT01 / DSNTEP2 | Drops the PROCTRAN stogroup. |
| DRPSG03 | db2jcl/DRPSG03.jcl | 1 | IKJEFT01 / DSNTEP2 | Drops the CONTROL stogroup. |
| DRPTS01 | db2jcl/DRPTS01.jcl | 1 | IKJEFT01 / DSNTEP2 | Drops the ACCOUNT tablespace. |
| DRPTS02 | db2jcl/DRPTS02.jcl | 1 | IKJEFT01 / DSNTEP2 | Drops the PROCTRAN tablespace. |
| DRPTS03 | db2jcl/DRPTS03.jcl | 1 | IKJEFT01 / DSNTEP2 | Drops the CONTROL tablespace. |
| DRPTB01 | db2jcl/DRPTB01.jcl | 1 | IKJEFT01 / DSNTEP2 | Drops the ACCOUNT table and tablespace. |
| DRPTB02 | db2jcl/DRPTB02.jcl | 1 | IKJEFT01 / DSNTEP2 | Drops the PROCTRAN table and tablespace. |
| DRPTB03 | db2jcl/DRPTB03.jcl | 1 | IKJEFT01 / DSNTEP2 | Drops the CONTROL table and tablespace. |
| DRPI101 | db2jcl/DRPI101.jcl | 1 | IKJEFT01 / DSNTEP2 | Drops index ACCTINDX on ACCOUNT. |
| DRPI201 | db2jcl/DRPI201.jcl | 1 | IKJEFT01 / DSNTEP2 | Drops index ACCTCUST on ACCOUNT. |
| DRPI301 | db2jcl/DRPI301.jcl | 1 | IKJEFT01 / DSNTEP2 | Drops index CONTINDX on CONTROL. |

### installjcl -- Library Setup Jobs

| Job Name | Source File | Steps | Programs Executed | Purpose |
| -------- | ----------- | ----- | ----------------- | ------- |
| CREL001 | installjcl/CREL001.jcl | 2 | IEFBR14, ICEGENER | Creates the CICSBSA.BUILDJCL PDSE and writes an empty member placeholder. |
| CREL003 | installjcl/CREL003.jcl | 1 | IEFBR14 | Creates the CICSBSA.LOADLIB PDSE (U-format, load module library). |
| CREL004 | installjcl/CREL004.jcl | 1 | IEFBR14 | Creates the CICSBSA.DBRM PDSE (DB2 DBRM library). |
| CREL005 | installjcl/CREL005.jcl | 1 | IEFBR14 | Creates the CICSBSA.LKED PDSE (linkage editor input library). |
| CREL006 | installjcl/CREL006.jcl | 1 | IEFBR14 | Creates an additional CBSA PDSE library (CREL006 series). |
| CREL008 | installjcl/CREL008.jcl | 1 | IEFBR14 | Creates an additional CBSA PDSE library (CREL008 series). |
| CREL009 | installjcl/CREL009.jcl | 1 | IEFBR14 | Creates an additional CBSA PDSE library (CREL009 series). |
| CREL010 | installjcl/CREL010.jcl | 1 | IEFBR14 | Creates an additional CBSA PDSE library (CREL010 series). |
| CREL011 | installjcl/CREL011.jcl | 1 | IEFBR14 | Creates an additional CBSA PDSE library (CREL011 series). |
| CRELIBS | installjcl/CRELIBS.jcl | 1 | IEFBR14 / IDCAMS | Creates all CBSA PDS/PDSE libraries (COBOL, COPYBOOK, LOADLIB, DBRM, etc.). |

### installjcl -- Application Install Jobs

| Job Name | Source File | Steps | Programs Executed | Purpose |
| -------- | ----------- | ----- | ----------------- | ------- |
| BANKDATA (install) | installjcl/BANKDATA.jcl | 3 | IDCAMS, IKJEFT01/BANKDATA | Defines VSAM clusters (ABNDFILE, CUSTOMER) then executes the BANKDATA batch program to populate initial data. |
| CBSACSD | installjcl/CBSACSD.jcl | 1 | DFHCSDUP | Installs CBSA CICS resource definitions (transactions, programs, files) into the CICS CSD using DFHCSDUP. |
| CICSTS56 | installjcl/CICSTS56.jcl | 1 | DFHCSDUP | CICS TS 5.6 specific CSD setup job for CBSA. |
| CREDB2L | installjcl/CREDB2L.jcl | 1 | IKJEFT01 / DSNTEP2 | Creates DB2 objects needed for the CBSA application load. |
| DFH$SIP1 | installjcl/DFH$SIP1.jcl | 0 | (none) | CICS SIT (System Initialisation Table) parameters file for CICS TS 5.6; not a JCL job -- a SYSIN data stream member. |
| RACF001 | installjcl/RACF001.jcl | 1 | IKJEFT01 | Defines RACF security profiles and grants for the CBSA application. |
| REPLCICS | installjcl/REPLCICS.jcl | 1 | IEBCOPY | Copies the CICSTS56 startup procedure from the CBSA install library to the target PROCLIB. |
| REPLSIP | installjcl/REPLSIP.jcl | 1 | IEBCOPY | Copies the DFH$SIP1 SIT parameter member from the CBSA install library to the CICS SYSIN library. |
| RESTCICS | installjcl/RESTCICS.jcl | 1 | IKJEFT01 | Restarts the CICS region after CBSA installation. |
| RESTZOSC | installjcl/RESTZOSC.jcl | 1 | IKJEFT01 | Issues an MVS START command to restart the z/OS Connect server (ZOSCSRV). |
| SHUTCICS | installjcl/SHUTCICS.jcl | 1 | IKJEFT01 | Shuts down the CICS region in preparation for installation steps. |
| SHUTZOSC | installjcl/SHUTZOSC.jcl | 1 | IKJEFT01 | Issues an MVS CANCEL command to stop the z/OS Connect server (ZOSCSRV). |
| ZOSCSEC | installjcl/ZOSCSEC.jcl | 1 | BPXBATCH | Sets Unix file permissions (chmod g+rwx) on z/OS Connect server resource directories. |

## Job Steps

| Job Name | Step Name | Program | DD Statements | Condition |
| -------- | --------- | ------- | ------------- | --------- |
| COMPALL | ABNDPROC.COBOL | IGYCRCTL | STEPLIB, SYSLIB, DBRMLIB, SYSPRINT, OUT, SYSUTn, SYSIN | - |
| COMPALL | ABNDPROC.LKED | IEWL | SYSLIB, SYSUT1, SYSPRINT, CBSAMOD, SYSLMOD, SYSLIN, IN | COND=(7,LT,COBOL) |
| BANKDATA (install) | BANKDAT0 | IDCAMS | SYSOUT, SYSPRINT, SYSIN | - |
| BANKDATA (install) | BANKDAT1 | IDCAMS | SYSOUT, SYSPRINT, SYSIN | - |
| BANKDATA (install) | BANKDAT5 | IKJEFT01 | STEPLIB, VSAM, SYSPRINT, SYSTSIN | - |
| INSTDB2 | GRANT | IKJEFT01 | JOBLIB, SYSTSPRT, SYSPRINT, SYSUDUMP, SYSTSIN, SYSIN | - |
| DB2BIND | BIND | IKJEFT01 | STEPLIB, DBRMLIB, SYSPRINT, SYSTSPRT, SYSUDUMP, SYSTSIN | - |
| DB2BIND | GRANT | IKJEFT01 | STEPLIB, SYSUDUMP, SYSPRINT, SYSTSPRT, SYSTSIN, SYSIN | - |
| CBSACSD | DFHCSDUP | DFHCSDUP | STEPLIB, DFHCSD, SYSPRINT, CBDOUT, AMSDUMP, SYSIN | - |
| REPLCICS | JOBSTEP | IEBCOPY | SYSPRINT, SYSOUT, SYSUT1, SYSUT2, SYSUT3, SYSUT4, SYSIN | - |
| REPLSIP | JOBSTEP | IEBCOPY | SYSPRINT, SYSOUT, SYSUT1, SYSUT2, SYSUT3, SYSUT4, SYSIN | - |
| RESTZOSC | STEP0001 | IKJEFT01 | SYSTSPRT, SYSTSIN | - |
| SHUTZOSC | STEP0001 | IKJEFT01 | SYSTSPRT, SYSTSIN | - |
| ZOSCSEC | BPXIT | BPXBATCH | STDOUT, STDENV | - |
| CREL001 | STEP10 | IEFBR14 | DD01 (CICSBSA.BUILDJCL) | - |
| CREL001 | STEP20 | ICEGENER | SYSUT1, SYSUT2 (CICSBSA.BUILDJCL(EMPTY)), SYSPRINT, SYSIN | - |

## DD Assignments

| Job Name | Step Name | DD Name | Dataset / File | Disposition |
| -------- | --------- | ------- | -------------- | ----------- |
| BANKDATA (install) | BANKDAT5 | VSAM | @BANK_PREFIX@.CUSTOMER | SHR |
| BANKDATA (install) | BANKDAT5 | STEPLIB | @BANK_LOADLIB@, @DB2_HLQ@.SDSNLOAD | SHR |
| INSTDB2 | GRANT | JOBLIB | &DB2HLQ..SDSNLOAD | SHR |
| DB2BIND | BIND | DBRMLIB | &BANKDBRM(CREACC..XFRFUN) | SHR |
| CBSACSD | DFHCSDUP | DFHCSD | @CSD_PREFIX@.DFHCSD | SHR |
| CBSACSD | DFHCSDUP | SYSIN | @CBSA_INSTALL@(BANK) | SHR |
| COMPALL (per program) | COBOL | SYSIN | &CBSAHLQ..COBOL(&MEMBER) | SHR |
| COMPALL (per program) | COBOL | DBRMLIB | &CBSAHLQ..DBRM(&MEMBER) | SHR |
| COMPALL (per program) | LKED | SYSLMOD | &CBSAHLQ..LOADLIB | SHR |
| REPLCICS | JOBSTEP | SYSUT1 | CBSA.JCL.INSTALL | SHR |
| REPLCICS | JOBSTEP | SYSUT2 | FEU.Z25A.PROCLIB | SHR,KEEP |
| REPLSIP | JOBSTEP | SYSUT2 | DFH560.SYSIN | SHR,KEEP |
| CREI101 | GRANT | JOBLIB | DSNC10.SDSNLOAD | SHR |
| CRETS01 | GRANT | JOBLIB | DSNC10.SDSNLOAD | SHR |

## Unresolved Programs

Programs referenced in EXEC PGM= but not found in the program inventory:

| Program | Referenced In |
| ------- | ------------- |
| IGYCRCTL | COMPALL.COBOL (all build JCL via CICS/BATCH proc) |
| IEWL | COMPALL.LKED (all build JCL via CICS/BATCH proc) |
| IDCAMS | BANKDATA(install).BANKDAT0, BANKDATA(install).BANKDAT1 |
| IKJEFT01 | BANKDATA(install).BANKDAT5, INSTDB2.GRANT, DB2BIND.BIND, DB2BIND.GRANT, RESTCICS, SHUTCICS, RESTZOSC, SHUTZOSC, RACF001 |
| DFHCSDUP | CBSACSD.DFHCSDUP, CICSTS56 |
| DSNTEP2 | INSTDB2 (via IKJEFT01 RUN PROGRAM), BTCHSQL, CRExx/DRPxx db2jcl jobs |
| DFHEAP1$ | MAPGEN (BMS assembler), all BMS map build jobs |
| IEFBR14 | CREL001..CREL011, CRELIBS |
| IEBCOPY | REPLCICS, REPLSIP |
| BPXBATCH | ZOSCSEC |
| ICEGENER | CREL001.STEP20 |
| ACCLOAD | buildjcl/ACCLOAD.jcl (no source in base cobol_src) |
| ACCOFFL | buildjcl/ACCOFFL.jcl (no source in base cobol_src) |
| EXTDCUST | buildjcl/EXTDCUST.jcl (no source in base cobol_src) |
