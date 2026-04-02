---
type: flow
subtype: batch-flows
status: draft
confidence: medium
last_pass: 1
---

# Batch Job Flows

JCL job step sequences showing program execution order and data flow between steps.

## Job Flows

### [JOB-NAME]

```mermaid
graph LR
    Step1["Step 1: PROG-A"] -->|"FILE-X"| Step2["Step 2: PROG-B"]
    Step2 -->|"FILE-Y"| Step3["Step 3: PROG-C"]
```

| Step | Program   | Input DD          | Output DD         | Condition        |
| ---- | --------- | ----------------- | ----------------- | ---------------- |
| 1    | [PROG-A]  | [DD1, DD2]        | [DD3]             | [COND= if any]  |
| 2    | [PROG-B]  | [DD3]             | [DD4]             | [COND= if any]  |

## Step Dependencies

| Job Name   | Step   | Depends On | Via Dataset         | Dependency Type         |
| ---------- | ------ | ---------- | ------------------- | ----------------------- |
| [JOB-NAME] | [STEP] | [STEP]     | [dataset.name]      | [Output-to-Input/COND=] |

## Conditional Execution

| Job Name   | Step   | Condition          | Effect                   |
| ---------- | ------ | ------------------ | ------------------------ |
| [JOB-NAME] | [STEP] | [COND=(0,NE,STEP)] | [Skip if STEP RC != 0]  |
