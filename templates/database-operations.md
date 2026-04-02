---
type: data
subtype: database-operations
status: draft
confidence: medium
last_pass: 1
---

# Database Operations

All database access patterns extracted from EXEC SQL, EXEC DLI, and CALL CBLTDLI statements.

## DB2 Operations

| Program        | Table          | Operation                          | Key Columns     | Host Variables       | Cursor   |
| -------------- | -------------- | ---------------------------------- | --------------- | -------------------- | -------- |
| [PROGRAM-NAME] | [TABLE-NAME]   | [SELECT/INSERT/UPDATE/DELETE]      | [columns]       | [host vars]          | [name]   |

## IMS/DB Operations

| Program        | Segment        | Operation         | PCB Reference | SSA Qualifications   |
| -------------- | -------------- | ----------------- | ------------- | -------------------- |
| [PROGRAM-NAME] | [SEGMENT-NAME] | [GU/GN/ISRT/REPL/DLET] | [PCB]   | [Segment Search Args] |

## Indexed File Operations

| Program        | File Name      | Operation                    | Key Fields      | Access Pattern          |
| -------------- | -------------- | ---------------------------- | --------------- | ----------------------- |
| [PROGRAM-NAME] | [FILE-NAME]    | [READ/WRITE/REWRITE/DELETE/START] | [key fields] | [Sequential/Random/Dynamic] |

## Cursors and Batch Access

| Program        | Cursor Name    | Table          | Purpose              | Fetch Pattern        |
| -------------- | -------------- | -------------- | -------------------- | -------------------- |
| [PROGRAM-NAME] | [CURSOR-NAME]  | [TABLE-NAME]   | [Batch read purpose] | [FETCH NEXT/bulk]    |
