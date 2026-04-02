"""Shared fixtures for COBOL reverse-engineering tests."""

from __future__ import annotations

import pytest


@pytest.fixture()
def batch_program_lines() -> list[str]:
    """A minimal batch COBOL program with file I/O and paragraphs."""
    src = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID.    TESTPROG.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT ACCTFILE ASSIGN TO ACCTFILE
                  FILE STATUS IS ACCT-STATUS.
           SELECT OUTFILE ASSIGN TO OUTFILE
                  FILE STATUS IS OUT-STATUS.

       DATA DIVISION.
       FILE SECTION.
       FD  ACCTFILE.
       01  FD-ACCT-REC               PIC X(100).
       WORKING-STORAGE SECTION.
       01  WS-VARIABLES.
           05  WS-ACCT-ID            PIC 9(11).
           05  WS-AMOUNT             PIC S9(7)V99.

       PROCEDURE DIVISION.
       0000-MAIN.
           PERFORM 1000-INIT
           PERFORM 2000-PROCESS
           PERFORM 3000-CLEANUP
           STOP RUN.

       0000-MAIN-EXIT.
           EXIT.

       1000-INIT.
           OPEN INPUT ACCTFILE
           OPEN OUTPUT OUTFILE.

       1000-INIT-EXIT.
           EXIT.

       2000-PROCESS.
           PERFORM 2100-READ-RECORD
           PERFORM 2200-VALIDATE
           IF WS-AMOUNT > 0
               PERFORM 2300-WRITE-RECORD
           END-IF.

       2000-PROCESS-EXIT.
           EXIT.

       2100-READ-RECORD.
           READ ACCTFILE INTO WS-VARIABLES.

       2200-VALIDATE.
           IF WS-ACCT-ID = ZEROS
               DISPLAY 'INVALID ACCOUNT'.

       2300-WRITE-RECORD.
           WRITE OUT-REC FROM WS-VARIABLES.

       3000-CLEANUP.
           CLOSE ACCTFILE
           CLOSE OUTFILE.

       3000-CLEANUP-EXIT.
           EXIT.
"""
    return src.splitlines(keepends=True)


@pytest.fixture()
def online_program_lines() -> list[str]:
    """A minimal online (CICS) COBOL program with EXEC CICS and XCTL."""
    src = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID.    ONLNPROG.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-VARS.
           05  LIT-THISTRANID        PIC X(4) VALUE 'ACCT'.
           05  LIT-THISPGM           PIC X(8) VALUE 'ONLNPROG'.
           05  LIT-NEXTPGM           PIC X(8) VALUE 'MENUPRG1'.
           05  WS-COMMAREA           PIC X(100).

       COPY DFHAID.
       COPY COCOM01Y.

       PROCEDURE DIVISION.
       0000-MAIN.
           EXEC CICS
               RECEIVE MAP('ACCTMAP')
                       MAPSET('ACCTSET')
                       INTO(WS-COMMAREA)
           END-EXEC
           PERFORM 1000-PROCESS-INPUT
           PERFORM 9000-RETURN.

       1000-PROCESS-INPUT.
           EXEC CICS
               READ FILE('ACCTFIL')
                    INTO(WS-COMMAREA)
                    RIDFLD(WS-ACCT-ID)
           END-EXEC
           EVALUATE TRUE
               WHEN EIBAID = DFHPF3
                   EXEC CICS XCTL PROGRAM(LIT-NEXTPGM) END-EXEC
               WHEN OTHER
                   CONTINUE
           END-EVALUATE.

       2000-SEND-SCREEN.
           EXEC CICS
               SEND MAP('ACCTMAP')
                    MAPSET('ACCTSET')
                    FROM(WS-COMMAREA)
           END-EXEC.

       9000-RETURN.
           EXEC CICS
               RETURN TRANSID(LIT-THISTRANID)
                      COMMAREA(WS-COMMAREA)
           END-EXEC.
"""
    return src.splitlines(keepends=True)


@pytest.fixture()
def db2_program_lines() -> list[str]:
    """A program with EXEC SQL blocks referencing tables."""
    src = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID.    DB2PROG.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
           EXEC SQL INCLUDE SQLCA END-EXEC.
           EXEC SQL INCLUDE DCLACCTS END-EXEC.
       01  WS-DATA.
           05  WS-ACCT-ID            PIC X(11).

       LINKAGE SECTION.
       01  DFHCOMMAREA               PIC X(100).

       PROCEDURE DIVISION.
       1000-MAIN.
           EXEC SQL
               SELECT ACCT_NAME, ACCT_BAL
               FROM ACCOUNTS
               WHERE ACCT_ID = :WS-ACCT-ID
           END-EXEC
           EXEC SQL
               UPDATE TRANSACTIONS
               SET STATUS = 'COMPLETE'
               WHERE TRAN_ID = :WS-TRAN-ID
           END-EXEC
           CALL 'DATEUTIL' USING WS-DATA.
"""
    return src.splitlines(keepends=True)


@pytest.fixture()
def perform_thru_lines() -> list[str]:
    """Program with PERFORM THRU patterns (same-line and multi-line)."""
    src = """\
       IDENTIFICATION DIVISION.
       PROGRAM-ID.    THRPROG.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-FLAG            PIC X(1).

       PROCEDURE DIVISION.
       0000-MAIN.
           PERFORM 1000-START THRU 1000-START-EXIT
           PERFORM 2000-PROCESS
               THRU 2000-PROCESS-EXIT
           STOP RUN.

       1000-START.
           MOVE 'Y' TO WS-FLAG.

       1000-START-EXIT.
           EXIT.

       2000-PROCESS.
           IF WS-FLAG = 'Y'
               DISPLAY 'PROCESSING'
           END-IF.

       2000-PROCESS-EXIT.
           EXIT.

       3000-FINAL.
           DISPLAY 'DONE'.

       3000-FINAL-EXIT.
           EXIT.
"""
    return src.splitlines(keepends=True)
