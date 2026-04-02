---
type: application
title: "[Application Name]"
status: draft
confidence: medium
last_pass: 1
total_programs: 0
total_copybooks: 0
total_jcl_jobs: 0
---

# [Application Name]

## Overview

High-level description of what this COBOL application does, its business purpose, and the domain it serves.

## Technology Stack

| Component       | Technology               |
| --------------- | ------------------------ |
| Language        | COBOL (dialect: TBD)     |
| Runtime         | TBD (z/OS, MF, GnuCOBOL) |
| Database        | TBD (DB2, IMS, VSAM)     |
| Transaction Mgr | TBD (CICS, IMS/TM, none) |
| Messaging       | TBD (MQ, none)           |
| Batch Scheduler | TBD (JES2, Control-M)    |

## Entry Points

List the main entry points into the application:

- **Batch**: key JCL jobs or main batch programs
- **Online**: CICS transactions or IMS transactions
- **Subprograms**: programs called by external systems

## Application Boundary

What is in scope (programs, copybooks, JCL analysed) and what external systems or applications are referenced but not included in this analysis.

## Key Observations

Notable patterns, technical debt, or architectural observations discovered during analysis.
