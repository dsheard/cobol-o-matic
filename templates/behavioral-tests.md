---
type: test-specifications
subtype: behavioral-tests
status: draft
confidence: medium
last_pass: 1
---

# Behavioral Test Specifications

Stack-agnostic test scenarios derived from business rules and functional capabilities. Tests describe WHAT the system does, not HOW -- any target implementation that passes these tests preserves the legacy system's behavior.

## Test Design Principles

| Principle | Description |
| --------- | ----------- |
| [Name]    | [How this principle guides test design] |

## [Capability Name]

### Overview

| Property     | Value                       |
| ------------ | --------------------------- |
| Capability   | [From capabilities.md]      |
| Source Rules | [Rule IDs, not paragraphs]  |
| Confidence   | [high/medium/low]           |

### Scenarios

| #   | Scenario     | Category                      | Preconditions       | Input                     | Expected Output             | Boundary | Source Rules |
| --- | ------------ | ----------------------------- | ------------------- | ------------------------- | --------------------------- | -------- | ------------ |
| 1   | [Name]       | [happy-path/error/boundary]   | [State before test] | [Business-domain inputs]  | [Business-domain outputs]   | [yes/no] | [BR-nnn]     |

### Data Equivalence Classes

| Field    | Business Name   | Valid Range          | Equivalence Classes           | Boundary Values      |
| -------- | --------------- | -------------------- | ----------------------------- | -------------------- |
| [Name]   | [Domain term]   | [From PIC / domain]  | [Partitions of valid/invalid] | [Edge values]        |

## Cross-Capability Scenarios

End-to-end tests that span multiple capabilities, verifying correct behavior across capability boundaries:

| #   | Scenario     | Capabilities Involved | Preconditions       | Input                    | Expected Output            | Source Rules |
| --- | ------------ | --------------------- | ------------------- | ------------------------ | -------------------------- | ------------ |
| 1   | [Name]       | [Cap1, Cap2]          | [State before test] | [Business-domain inputs] | [Business-domain outputs]  | [BR-nnn]     |
