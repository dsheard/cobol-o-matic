---
type: test-specifications
subtype: data-contracts
status: draft
confidence: medium
last_pass: 1
---

# Data Contract Tests

Data format, invariant, and boundary tests for each data store. These tests verify that the modernized system preserves data semantics regardless of storage technology changes (e.g. VSAM to database, flat file to API).

## File Contracts

| File / Dataset | Business Purpose | Record Layout | Producers | Consumers | Key Fields |
| -------------- | ---------------- | ------------- | --------- | --------- | ---------- |
| [Name]         | [Purpose]        | [Copybook]    | [Programs] | [Programs] | [Fields]  |

### [File Name] Contract Tests

| #   | Invariant              | Test                         | Derived From     |
| --- | ---------------------- | ---------------------------- | ---------------- |
| 1   | [Data rule]            | [How to verify]              | [Source evidence] |

## Database Contracts

| Table / Segment | Business Purpose | Writers        | Readers        | Key Columns |
| --------------- | ---------------- | -------------- | -------------- | ----------- |
| [Name]          | [Purpose]        | [Programs]     | [Programs]     | [Columns]   |

### [Table Name] Contract Tests

| #   | Invariant              | Test                         | Derived From     |
| --- | ---------------------- | ---------------------------- | ---------------- |
| 1   | [Data rule]            | [How to verify]              | [Source evidence] |

## Message Contracts

| Queue / Channel | Business Purpose | Producers | Consumers | Message Format |
| --------------- | ---------------- | --------- | --------- | -------------- |
| [Name]          | [Purpose]        | [Programs] | [Programs] | [Layout]      |

### [Queue Name] Contract Tests

| #   | Invariant              | Test                         | Derived From     |
| --- | ---------------------- | ---------------------------- | ---------------- |
| 1   | [Data rule]            | [How to verify]              | [Source evidence] |

## Data Invariants

Cross-store consistency rules that must hold across the modernized system:

| #   | Invariant                | Stores Involved | Test                         | Derived From     |
| --- | ------------------------ | --------------- | ---------------------------- | ---------------- |
| 1   | [Consistency rule]       | [Store1, Store2] | [How to verify]             | [Source evidence] |
