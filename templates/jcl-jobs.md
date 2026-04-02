---
type: inventory
subtype: jcl-jobs
status: draft
confidence: medium
last_pass: 1
---

# JCL Job Inventory

Catalog of all JCL jobs found in the source directory.

## Jobs

| Job Name   | Source File    | Steps | Programs Executed | Purpose         |
| ---------- | ------------- | ----- | ----------------- | --------------- |
| [JOB-NAME] | [filename.jcl] | [n]   | [PROG1, PROG2]   | [Brief purpose] |

## Job Steps

| Job Name   | Step Name   | Program     | DD Statements        | Condition        |
| ---------- | ----------- | ----------- | -------------------- | ---------------- |
| [JOB-NAME] | [STEP-NAME] | [PGM=PROG]  | [DD1, DD2]           | [COND= if any]  |

## DD Assignments

| Job Name   | Step Name   | DD Name    | Dataset / File          | Disposition     |
| ---------- | ----------- | ---------- | ----------------------- | --------------- |
| [JOB-NAME] | [STEP-NAME] | [DD-NAME]  | [dataset.name]          | [SHR/NEW/MOD]  |

## Unresolved Programs

Programs referenced in EXEC PGM= but not found in the program inventory:

| Program        | Referenced In     |
| -------------- | ----------------- |
| [PROGRAM-NAME] | [JOB.STEP]        |
