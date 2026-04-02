---
type: business-rules
program: "[PROGRAM-NAME]"
program_type: batch # batch | online | subprogram
status: draft
confidence: medium
last_pass: 1
calls: [] # programs this program CALLs
called_by: [] # programs that CALL this one
uses_copybooks: []
reads: [] # files/datasets read
writes: [] # files/datasets written
db_tables: [] # DB2/IMS tables accessed
transactions: [] # transaction IDs (if online)
mq_queues: [] # MQ queues (if any)
---

# [PROGRAM-NAME] -- Business Rules

## Program Purpose

Brief description of what this program does and its role in the application.

## Input / Output

| Direction | Resource | Type              | Description   |
| --------- | -------- | ----------------- | ------------- |
| IN        | [name]   | [File/DB/MQ/CICS] | [Description] |
| OUT       | [name]   | [File/DB/MQ/CICS] | [Description] |

## Business Rules

### [Rule Category: e.g. Validation, Calculation, Routing]

| #   | Rule        | Condition               | Action         | Source Location           |
| --- | ----------- | ----------------------- | -------------- | ------------------------- |
| 1   | [Rule name] | [IF/EVALUATE condition] | [What happens] | [PARAGRAPH or line range] |

## Calculations

| Calculation | Formula / Logic              | Input Fields | Output Field | Source Location |
| ----------- | ---------------------------- | ------------ | ------------ | --------------- |
| [Name]      | [Description of computation] | [fields]     | [field]      | [PARAGRAPH]     |

## Error Handling

| Condition         | Action                     | Return Code | Source Location |
| ----------------- | -------------------------- | ----------- | --------------- |
| [Error condition] | [DISPLAY/ABEND/SET-STATUS] | [code]      | [PARAGRAPH]     |

## Control Flow

Key PERFORM and CALL sequences in execution order:

1. [PARAGRAPH-1] -- [what it does]
2. [PARAGRAPH-2] -- [what it does]
3. CALL [PROGRAM] -- [why]
