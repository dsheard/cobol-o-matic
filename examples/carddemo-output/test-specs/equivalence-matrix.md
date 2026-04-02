---
type: test-specifications
subtype: equivalence-matrix
status: draft
confidence: high
last_pass: 7
---

# Equivalence Matrix

Traceability from test scenarios back to business rules and source programs. This matrix is a reference for auditors and SMEs -- it does not dictate test organization (tests are organized by capability, not by program).

---

## Traceability

| Test ID | Capability | Scenario | Business Rules | Source Programs | Source Paragraphs |
| ------- | ---------- | -------- | -------------- | --------------- | ----------------- |
| T-001 | User Authentication and Session Management | Successful admin login routes to admin menu | BR-COSGN00C-12, BR-COSGN00C-13 | COSGN00C | READ-USER-SEC-FILE line 223-234 |
| T-002 | User Authentication and Session Management | Successful regular user login routes to main menu | BR-COSGN00C-12, BR-COSGN00C-14 | COSGN00C | READ-USER-SEC-FILE line 223-240 |
| T-003 | User Authentication and Session Management | Login rejected when user ID is blank | BR-COSGN00C-6 | COSGN00C | PROCESS-ENTER-KEY line 118-122 |
| T-004 | User Authentication and Session Management | Login rejected when password is blank | BR-COSGN00C-7 | COSGN00C | PROCESS-ENTER-KEY line 123-127 |
| T-005 | User Authentication and Session Management | Login rejected for unknown user ID | BR-COSGN00C-16 | COSGN00C | READ-USER-SEC-FILE line 247-251 |
| T-006 | User Authentication and Session Management | Login rejected when password does not match | BR-COSGN00C-15 | COSGN00C | READ-USER-SEC-FILE line 242-245 |
| T-007 | User Authentication and Session Management | Credentials matched case-insensitively | BR-COSGN00C-9, BR-COSGN00C-10 | COSGN00C | PROCESS-ENTER-KEY line 132-136 |
| T-008 | User Authentication and Session Management | Session terminated on explicit exit | BR-COSGN00C-4, BR-COSGN00C-25 | COSGN00C | MAIN-PARA line 88-90; SEND-PLAIN-TEXT line 171-172 |
| T-009 | User Authentication and Session Management | Unsupported function keys rejected | BR-COSGN00C-5 | COSGN00C | MAIN-PARA line 91-94 |
| T-010 | User Authentication and Session Management | Unexpected system error shows generic message | BR-COSGN00C-17 | COSGN00C | READ-USER-SEC-FILE line 252-256 |
| T-011 | User Authentication and Session Management | Max 8-character user ID accepted (boundary) | BR-COSGN00C-18, BR-COSGN00C-19 | COSGN00C | READ-USER-SEC-FILE line 211-219 |
| T-012 | User Authentication and Session Management | User type other than 'A' routes to regular menu | BR-COSGN00C-22 | COSGN00C | READ-USER-SEC-FILE line 235-239 |
| T-013 | Navigation and Menu Routing | Admin user sees admin menu | BR-COSGN00C-13 | COSGN00C, COADM01C | READ-USER-SEC-FILE line 230-234 |
| T-014 | Navigation and Menu Routing | Regular user sees standard menu | BR-COSGN00C-14 | COSGN00C, COMEN01C | READ-USER-SEC-FILE line 235-239 |
| T-015 | Navigation and Menu Routing | Menu option dispatches to correct program | BR-COMEN01C-dispatch | COMEN01C | PROCESS-ENTER-KEY lines 177-187 (WHEN OTHER XCTL dispatch) |
| T-016 | Navigation and Menu Routing | Invalid menu option rejected | BR-COMEN01C-invalid | COMEN01C | PROCESS-ENTER-KEY lines 127-134 |
| T-017 | Navigation and Menu Routing | PF3 from menu returns to sign-on | BR-COMEN01C-pf3 | COMEN01C, COADM01C | MAIN-PARA PF3 handler |
| T-018 | Account Inquiry and Update | Account details displayed for valid account number | BR-COACTUPC-106 | COACTUPC | 2000-DECIDE-ACTION line 15-27 |
| T-019 | Account Inquiry and Update | Account number is mandatory | BR-COACTUPC-39 | COACTUPC | 1210-EDIT-ACCOUNT lines 381-390 |
| T-020 | Account Inquiry and Update | Account number must be numeric | BR-COACTUPC-40 | COACTUPC | 1210-EDIT-ACCOUNT lines 396-407 |
| T-021 | Account Inquiry and Update | Account number zero rejected | BR-COACTUPC-41 | COACTUPC | 1210-EDIT-ACCOUNT lines 397-407 |
| T-022 | Account Inquiry and Update | Update requires PF5 confirmation before write | BR-COACTUPC-103, BR-COACTUPC-111 | COACTUPC | 1200-EDIT-MAP-INPUTS lines 265-269; 0000-MAIN lines 56-62 |
| T-023 | Account Inquiry and Update | PF5 confirmation triggers write | BR-COACTUPC-111, BR-COACTUPC-115 | COACTUPC | 2000-DECIDE-ACTION lines 49-62 |
| T-024 | Account Inquiry and Update | No-change submission does not advance to confirmation | BR-COACTUPC-36, BR-COACTUPC-108 | COACTUPC | 1205-COMPARE-OLD-NEW line 363; 2000-DECIDE-ACTION lines 32-38 |
| T-025 | Account Inquiry and Update | Concurrent modification detected and surfaced | BR-COACTUPC-114 | COACTUPC | 2000-DECIDE-ACTION lines 58-59 |
| T-026 | Account Inquiry and Update | Account lock failure reported | BR-COACTUPC-112 | COACTUPC | 2000-DECIDE-ACTION lines 54-55 |
| T-027 | Account Inquiry and Update | FICO score below 300 rejected | BR-COACTUPC-99 | COACTUPC | 1275-EDIT-FICO-SCORE lines 1108-1123 |
| T-028 | Account Inquiry and Update | FICO score 300 accepted (boundary) | BR-COACTUPC-99 | COACTUPC | 1275-EDIT-FICO-SCORE lines 1108-1123 |
| T-029 | Account Inquiry and Update | FICO score 850 accepted (boundary) | BR-COACTUPC-99 | COACTUPC | 1275-EDIT-FICO-SCORE lines 1108-1123 |
| T-030 | Account Inquiry and Update | FICO score 851 rejected (boundary) | BR-COACTUPC-99 | COACTUPC | 1275-EDIT-FICO-SCORE lines 1108-1123 |
| T-031 | Account Inquiry and Update | FICO score 0 rejected (boundary) | BR-COACTUPC-65, BR-COACTUPC-66 | COACTUPC | 1245-EDIT-NUM-REQD lines 750-765 |
| T-032 | Account Inquiry and Update | Active status must be Y or N | BR-COACTUPC-46, BR-COACTUPC-47 | COACTUPC | 1220-EDIT-YESNO lines 472-486 |
| T-033 | Account Inquiry and Update | SSN Part 1 value 000 rejected | BR-COACTUPC-94 | COACTUPC | 1265-EDIT-US-SSN lines 1042-1058 |
| T-034 | Account Inquiry and Update | SSN Part 1 value 900 rejected (boundary) | BR-COACTUPC-94 | COACTUPC | 1265-EDIT-US-SSN lines 1042-1058 |
| T-035 | Account Inquiry and Update | SSN Part 1 value 666 rejected | BR-COACTUPC-94 | COACTUPC | 1265-EDIT-US-SSN lines 1044-1054 |
| T-036 | Account Inquiry and Update | Invalid US state code rejected | BR-COACTUPC-97 | COACTUPC | 1270-EDIT-US-STATE-CD lines 1087-1104 |
| T-037 | Account Inquiry and Update | Invalid state/zip combination rejected | BR-COACTUPC-101 | COACTUPC | 1280-EDIT-US-STATE-ZIP-CD lines 1130-1150 |
| T-038 | Account Inquiry and Update | Invalid North America area code rejected | BR-COACTUPC-83, BR-COACTUPC-84 | COACTUPC | EDIT-AREA-CODE lines 890-906 |
| T-039 | Account Inquiry and Update | Credit limit non-numeric rejected | BR-COACTUPC-70, BR-COACTUPC-71 | COACTUPC | 1250-EDIT-SIGNED-9V2 lines 795-809 |
| T-040 | Account Inquiry and Update | Invalid calendar date rejected | BR-COACTUPC-76 | COACTUPC | EDIT-DATE-CCYYMMDD paragraph |
| T-041 | Account Inquiry and Update | Only first error message shown | BR-COACTUPC-105 | COACTUPC | All 1210/1220/.../1280 paragraphs (IF WS-RETURN-MSG-OFF guard) |
| T-042 | Account Inquiry and Update | Optional middle name blank accepted | BR-COACTUPC-58 | COACTUPC | 1235-EDIT-ALPHA-OPT lines 611-619 |
| T-043 | Account Inquiry and Update | Optional middle name with non-alpha rejected | BR-COACTUPC-57 | COACTUPC | 1235-EDIT-ALPHA-OPT lines 625-647 |
| T-044 | Account Inquiry and Update | 11-digit account ID boundary accepted | BR-COACTUPC-39, BR-COACTUPC-42 | COACTUPC | 1210-EDIT-ACCOUNT lines 409-411 |
| T-045 | Credit Card Management | Admin sees all cards | BR-COCRDLIC-1 | COCRDLIC | 0000-MAIN lines 315-325; 9000-READ-FORWARD line 1129 |
| T-046 | Credit Card Management | Account filter narrows card list | BR-COCRDLIC-26 | COCRDLIC | 9500-FILTER-RECORDS lines 1385-1391 |
| T-047 | Credit Card Management | Account filter must be numeric | BR-COCRDLIC-17 | COCRDLIC | 2210-EDIT-ACCOUNT lines 1017-1025 |
| T-048 | Credit Card Management | Card number filter must be numeric | BR-COCRDLIC-20 | COCRDLIC | 2220-EDIT-CARD lines 1052-1062 |
| T-049 | Credit Card Management | Only one row may be selected | BR-COCRDLIC-23 | COCRDLIC | 2250-EDIT-ARRAY lines 1079-1095 |
| T-050 | Credit Card Management | Invalid row action code rejected | BR-COCRDLIC-24 | COCRDLIC | 2250-EDIT-ARRAY lines 1099-1115 |
| T-051 | Credit Card Management | 'S' navigates to detail view | BR-COCRDLIC-13 | COCRDLIC | 0000-MAIN lines 517-541 |
| T-052 | Credit Card Management | 'U' navigates to update screen | BR-COCRDLIC-14 | COCRDLIC | 0000-MAIN lines 545-569 |
| T-053 | Credit Card Management | PF8 pages forward | BR-COCRDLIC-11 | COCRDLIC | 0000-MAIN lines 486-497 |
| T-054 | Credit Card Management | PF7 pages backward | BR-COCRDLIC-12 | COCRDLIC | 0000-MAIN lines 501-513 |
| T-055 | Credit Card Management | PF7 on first page shows info message | BR-COCRDLIC-39 | COCRDLIC | 1400-SETUP-MESSAGE lines 901-904 |
| T-056 | Credit Card Management | No records found message | BR-COCRDLIC-32 | COCRDLIC | 9000-READ-FORWARD lines 1241-1245 |
| T-057 | Credit Card Management | 7-card-per-page boundary | BR-COCRDLIC-29 | COCRDLIC | 9000-READ-FORWARD lines 1191-1231 |
| T-058 | Transaction Inquiry and Manual Entry | New transaction added with account ID lookup | BR-COTRN02C-11, BR-COTRN02C-15, BR-COTRN02C-52 | COTRN02C | VALIDATE-INPUT-KEY-FIELDS line 204-209; WRITE-TRANSACT-FILE line 724-734 |
| T-059 | Transaction Inquiry and Manual Entry | New transaction added with card number lookup | BR-COTRN02C-17, BR-COTRN02C-52 | COTRN02C | VALIDATE-INPUT-KEY-FIELDS line 218-223; WRITE-TRANSACT-FILE line 724-734 |
| T-060 | Transaction Inquiry and Manual Entry | Neither account nor card rejected | BR-COTRN02C-18 | COTRN02C | VALIDATE-INPUT-KEY-FIELDS line 224-229 |
| T-061 | Transaction Inquiry and Manual Entry | Account ID must be numeric | BR-COTRN02C-14 | COTRN02C | VALIDATE-INPUT-KEY-FIELDS line 196-203 |
| T-062 | Transaction Inquiry and Manual Entry | Amount sign character required | BR-COTRN02C-32 | COTRN02C | VALIDATE-INPUT-DATA-FIELDS line 340-348 |
| T-063 | Transaction Inquiry and Manual Entry | Amount decimal position validated | BR-COTRN02C-33, BR-COTRN02C-34, BR-COTRN02C-35 | COTRN02C | VALIDATE-INPUT-DATA-FIELDS line 341-343 |
| T-064 | Transaction Inquiry and Manual Entry | Origination date calendar validation | BR-COTRN02C-46 | COTRN02C, CSUTLDTC | VALIDATE-INPUT-DATA-FIELDS line 389-407 |
| T-065 | Transaction Inquiry and Manual Entry | Processing date calendar validation | BR-COTRN02C-47 | COTRN02C, CSUTLDTC | VALIDATE-INPUT-DATA-FIELDS line 409-427 |
| T-066 | Transaction Inquiry and Manual Entry | Date format hyphen separators required | BR-COTRN02C-37, BR-COTRN02C-39 | COTRN02C | VALIDATE-INPUT-DATA-FIELDS line 354-363 |
| T-067 | Transaction Inquiry and Manual Entry | Confirmation 'N' cancels add | BR-COTRN02C-12 | COTRN02C | PROCESS-ENTER-KEY line 173-181 |
| T-068 | Transaction Inquiry and Manual Entry | Confirmation required before write | BR-COTRN02C-12 | COTRN02C | PROCESS-ENTER-KEY line 173-181 |
| T-069 | Transaction Inquiry and Manual Entry | Transaction ID auto-generated | BR-COTRN02C-50 | COTRN02C | ADD-TRANSACTION line 444-451 |
| T-070 | Transaction Inquiry and Manual Entry | Leap year date accepted (boundary) | BR-COTRN02C-46 | COTRN02C, CSUTLDTC | VALIDATE-INPUT-DATA-FIELDS line 389-407 |
| T-071 | Transaction Inquiry and Manual Entry | Non-leap year Feb 29 rejected (boundary) | BR-COTRN02C-46 | COTRN02C, CSUTLDTC | VALIDATE-INPUT-DATA-FIELDS line 389-407 |
| T-072 | Bill Payment Processing | Successful full-balance payment | BR-COBIL00C-14, BR-COBIL00C-16, BR-COBIL00C-24 | COBIL00C | PROCESS-ENTER-KEY line 174-235 |
| T-073 | Bill Payment Processing | Zero balance rejected | BR-COBIL00C-13 | COBIL00C | PROCESS-ENTER-KEY lines 197-205 |
| T-074 | Bill Payment Processing | Negative balance rejected | BR-COBIL00C-13 | COBIL00C | PROCESS-ENTER-KEY lines 197-205 |
| T-075 | Bill Payment Processing | Account ID mandatory | BR-COBIL00C-9 | COBIL00C | PROCESS-ENTER-KEY lines 159-164 |
| T-076 | Bill Payment Processing | Confirmation 'N' cancels payment | BR-COBIL00C-11 | COBIL00C | PROCESS-ENTER-KEY lines 178-181 |
| T-077 | Bill Payment Processing | Confirmation required before posting | BR-COBIL00C-12, BR-COBIL00C-15 | COBIL00C | PROCESS-ENTER-KEY lines 182-184; 236-240 |
| T-078 | Bill Payment Processing | Full balance always paid | BR-COBIL00C-24 | COBIL00C | PROCESS-ENTER-KEY line 224 |
| T-079 | Bill Payment Processing | Type '02' and category 2 on payment transaction | BR-COBIL00C-16, BR-COBIL00C-17 | COBIL00C | PROCESS-ENTER-KEY line 220-221 |
| T-080 | Bill Payment Processing | PF4 clears screen | BR-COBIL00C-6 | COBIL00C | MAIN-PARA line 137 |
| T-081 | Bill Payment Processing | Invalid confirmation value rejected | BR-COBIL00C-10 | COBIL00C | PROCESS-ENTER-KEY lines 185-190 |
| T-082 | Bill Payment Processing | First payment on empty TRANSACT fails (known defect) | BR-COBIL00C-29 | COBIL00C | STARTBR-TRANSACT-FILE lines 454-459 |
| T-083 | Bill Payment Processing | Balance zeroed despite transaction write failure (known defect) | BR-COBIL00C defect | COBIL00C | PROCESS-ENTER-KEY lines 233-235 |
| T-084 | Bill Payment Processing | Minimum balance $0.01 processed (boundary) | BR-COBIL00C-13, BR-COBIL00C-24 | COBIL00C | PROCESS-ENTER-KEY lines 197-205 |
| T-085 | Daily Transaction Posting | Valid transaction posted | BR-CBTRN02C-4, BR-CBTRN02C-21 | CBTRN02C | 2000-POST-TRANSACTION lines 425-442 |
| T-086 | Daily Transaction Posting | Invalid card number produces reason-100 reject | BR-CBTRN02C-9, BR-CBTRN02C-6 | CBTRN02C | 1500-A-LOOKUP-XREF lines 384-387; 2500-WRITE-REJECT-REC lines 447-448 |
| T-087 | Daily Transaction Posting | Account not found produces reason-101 reject | BR-CBTRN02C-13, BR-CBTRN02C-6 | CBTRN02C | 1500-B-LOOKUP-ACCT lines 396-399 |
| T-088 | Daily Transaction Posting | Overlimit produces reason-102 reject | BR-CBTRN02C-15, BR-CBTRN02C-6 | CBTRN02C | 1500-B-LOOKUP-ACCT lines 403-412 |
| T-089 | Daily Transaction Posting | Expired account produces reason-103 reject | BR-CBTRN02C-17, BR-CBTRN02C-6 | CBTRN02C | 1500-B-LOOKUP-ACCT lines 414-419 |
| T-090 | Daily Transaction Posting | Both overlimit and expiry: only reason 103 in reject | BR-CBTRN02C-20 | CBTRN02C | 1500-B-LOOKUP-ACCT lines 403-420 |
| T-091 | Daily Transaction Posting | Overlimit uses cycle balances only | BR-CBTRN02C-16 | CBTRN02C | 1500-B-LOOKUP-ACCT lines 403-405 |
| T-092 | Daily Transaction Posting | All valid: return code 0 | BR-CBTRN02C-6 | CBTRN02C | Main loop lines 229-231 |
| T-093 | Daily Transaction Posting | Any rejects: return code 4 | BR-CBTRN02C-5, BR-CBTRN02C-6 | CBTRN02C | Main loop lines 214-215; 229-231 |
| T-094 | Daily Transaction Posting | New TCATBAL record created for new type/category | BR-CBTRN02C-30 | CBTRN02C | 2700-A-CREATE-TCATBAL-REC lines 504-508 |
| T-095 | Daily Transaction Posting | Existing TCATBAL record updated | BR-CBTRN02C-31 | CBTRN02C | 2700-B-UPDATE-TCATBAL-REC line 527 |
| T-096 | Daily Transaction Posting | PROC-TS set from batch clock not input | BR-CBTRN02C-38 | CBTRN02C | 2000-POST-TRANSACTION lines 437-438; Z-GET-DB2-FORMAT-TIMESTAMP line 693 |
| T-097 | Daily Transaction Posting | TRANSACT truncated on each run | BR-CBTRN02C-7 | CBTRN02C | 0100-TRANFILE-OPEN line 256 |
| T-098 | Daily Transaction Posting | Empty input file: no output, return code 0 (boundary) | BR-CBTRN02C-6 | CBTRN02C | Main loop line 204 |
| T-099 | Daily Transaction Posting | Account rewrite failure: silent data inconsistency (known defect) | BR-CBTRN02C-36 | CBTRN02C | 2800-UPDATE-ACCOUNT-REC lines 554-558 |
| T-100 | Interest and Fees Calculation | Monthly interest = (balance * rate) / 1200 | BR-CBACT04C-22, BR-CBACT04C-23 | CBACT04C | 1300-COMPUTE-INTEREST line 464-465 |
| T-101 | Interest and Fees Calculation | Interest transaction type '01' category '05' | BR-CBACT04C-26, BR-CBACT04C-27 | CBACT04C | 1300-B-WRITE-TX lines 482-483 |
| T-102 | Interest and Fees Calculation | Zero rate produces no interest transaction | BR-CBACT04C-12 | CBACT04C | Main loop line 214 |
| T-103 | Interest and Fees Calculation | Fallback to DEFAULT disclosure group | BR-CBACT04C-18, BR-CBACT04C-19 | CBACT04C | 1200-GET-INTEREST-RATE lines 436-438; 1200-A-GET-DEFAULT-INT-RATE line 444 |
| T-104 | Interest and Fees Calculation | Missing DEFAULT causes abend | BR-CBACT04C-21 | CBACT04C | 1200-A-GET-DEFAULT-INT-RATE lines 455-458 |
| T-105 | Interest and Fees Calculation | Missing account causes abend | BR-CBACT04C error handling | CBACT04C | 1100-GET-ACCT-DATA lines 374-389 |
| T-106 | Interest and Fees Calculation | Cycle balances zeroed after interest | BR-CBACT04C-35, BR-CBACT04C-36 | CBACT04C | 1050-UPDATE-ACCOUNT lines 353-354 |
| T-107 | Interest and Fees Calculation | Interest accumulated across multiple categories | BR-CBACT04C-23, BR-CBACT04C-34 | CBACT04C | 1300-COMPUTE-INTEREST line 467; 1050-UPDATE-ACCOUNT line 352 |
| T-108 | Interest and Fees Calculation | Zero rate boundary | BR-CBACT04C-12 | CBACT04C | Main loop line 214 |
| T-109 | Interest and Fees Calculation | Fee stub produces no fees | BR-CBACT04C-38 | CBACT04C | 1400-COMPUTE-FEES line 518-520 |
| T-110 | User Administration | New user added with all fields | BR-COUSR01C-13, BR-COUSR01C-20 | COUSR01C | PROCESS-ENTER-KEY lines 148-160; WRITE-USER-SEC-FILE lines 251-259 |
| T-111 | User Administration | First name mandatory | BR-COUSR01C-8 | COUSR01C | PROCESS-ENTER-KEY lines 118-123 |
| T-112 | User Administration | Last name mandatory | BR-COUSR01C-9 | COUSR01C | PROCESS-ENTER-KEY lines 124-129 |
| T-113 | User Administration | User ID mandatory | BR-COUSR01C-10 | COUSR01C | PROCESS-ENTER-KEY lines 130-135 |
| T-114 | User Administration | Password mandatory | BR-COUSR01C-11 | COUSR01C | PROCESS-ENTER-KEY lines 136-141 |
| T-115 | User Administration | User type mandatory | BR-COUSR01C-12 | COUSR01C | PROCESS-ENTER-KEY lines 142-147 |
| T-116 | User Administration | Duplicate user ID rejected | BR-COUSR01C-21, BR-COUSR01C-22 | COUSR01C | WRITE-USER-SEC-FILE lines 260-266 |
| T-117 | User Administration | User type accepts any non-blank character | BR-COUSR01C-12 note | COUSR01C | PROCESS-ENTER-KEY lines 142-147 |
| T-118 | User Administration | 8-character user ID boundary | BR-COUSR01C-14 | COUSR01C | WRITE-USER-SEC-FILE lines 243-245 |
| T-119 | User Administration | Password stored as plaintext | BR-COUSR01C-17 | COUSR01C | WRITE-USER-SEC-FILE lines 243-245; CSUSR01Y SEC-USR-PWD PIC X(08) |
| T-120 | Report Request (Online to Batch) | Valid date range submits batch job | BR-CORPT00C-submit | CORPT00C | TDQ write paragraph (JCL record writes) |
| T-121 | Report Request (Online to Batch) | Invalid start date rejected | BR-CORPT00C-datevalidation | CORPT00C, CSUTLDTC | Date validation CALL to CSUTLDTC |
| T-122 | Report Request (Online to Batch) | Report runs asynchronously | BR-CORPT00C-async | CORPT00C | TDQ write paragraph (JES internal reader) |
| T-123 | Report Request (Online to Batch) | Leap year date accepted (boundary) | BR-CORPT00C-datevalidation | CORPT00C, CSUTLDTC | Date validation CALL to CSUTLDTC |
| T-124 | Data Migration Export and Import | Export produces multi-record file with all record types | BR-CBEXPORT-main | CBEXPORT | Main export loop (all five VSAM files) |
| T-125 | Data Migration Export and Import | Import splits by record type | BR-CBIMPORT-split | CBIMPORT | Import parse loop (REDEFINES type dispatch) |
| T-126 | Data Migration Export and Import | Import validates checksums | BR-CBIMPORT-checksum | CBIMPORT | Checksum validation paragraph |
| T-127 | Data Migration Export and Import | Card output DD missing (known defect) | BR-CBIMPORT card defect | CBIMPORT | SELECT CARD-OUTPUT ASSIGN TO CARDOUT (JCL omission) |
| T-128 | Batch Job Sequencing Utility | Program completes after specified delay | BR-COBSWAIT-main | COBSWAIT | Main wait paragraph (MVSWAIT call) |
| T-129 | Batch Job Sequencing Utility | Zero centisecond wait (boundary) | BR-COBSWAIT-main | COBSWAIT | Main wait paragraph line 1 (SYSIN read + MVSWAIT) |
| T-130 | Batch Job Sequencing Utility | Maximum wait duration (boundary) | BR-COBSWAIT-main | COBSWAIT | Main wait paragraph (SYSIN PIC 9(08) max value) |
| T-131 | Card Detail Update | Card details displayed for valid account and card numbers | BR-COCRDUPC-46, BR-COCRDUPC-47 | COCRDUPC | 9000-READ-DATA lines 1352-1370; 9100-GETCARD-BYACCTCARD lines 1382-1411 |
| T-132 | Card Detail Update | Account number mandatory for card search | BR-COCRDUPC-13 | COCRDUPC | 1210-EDIT-ACCOUNT lines 725-735 |
| T-133 | Card Detail Update | Account number must be numeric | BR-COCRDUPC-14 | COCRDUPC | 1210-EDIT-ACCOUNT lines 740-750 |
| T-134 | Card Detail Update | Card number mandatory for card search | BR-COCRDUPC-16 | COCRDUPC | 1220-EDIT-CARD lines 768-779 |
| T-135 | Card Detail Update | Card number must be numeric | BR-COCRDUPC-17 | COCRDUPC | 1220-EDIT-CARD lines 784-794 |
| T-136 | Card Detail Update | Both account and card blank rejected | BR-COCRDUPC-19 | COCRDUPC | 1200-EDIT-MAP-INPUTS lines 656-661 |
| T-137 | Card Detail Update | Card not found returns error | BR-COCRDUPC-48 | COCRDUPC | 9100-GETCARD-BYACCTCARD lines 1395-1401 |
| T-138 | Card Detail Update | Search fields protected; detail fields editable after fetch | BR-COCRDUPC-60 | COCRDUPC | 3300-SETUP-SCREEN-ATTRS lines 1181-1190 |
| T-139 | Card Detail Update | Card embossed name mandatory | BR-COCRDUPC-22 | COCRDUPC | 1230-EDIT-NAME lines 811-819 |
| T-140 | Card Detail Update | Card embossed name must be alphabets and spaces only | BR-COCRDUPC-23 | COCRDUPC | 1230-EDIT-NAME lines 822-836 |
| T-141 | Card Detail Update | Card active status mandatory | BR-COCRDUPC-24 | COCRDUPC | 1240-EDIT-CARDSTATUS lines 850-858 |
| T-142 | Card Detail Update | Card active status must be Y or N | BR-COCRDUPC-25 | COCRDUPC | 1240-EDIT-CARDSTATUS lines 861-872 |
| T-143 | Card Detail Update | Expiry month mandatory | BR-COCRDUPC-26 | COCRDUPC | 1250-EDIT-EXPIRY-MON lines 883-892 |
| T-144 | Card Detail Update | Expiry month out of range (>12) rejected | BR-COCRDUPC-27 | COCRDUPC | 1250-EDIT-EXPIRY-MON lines 896-907 |
| T-145 | Card Detail Update | Expiry month boundary: 1 accepted | BR-COCRDUPC-27 | COCRDUPC | 1250-EDIT-EXPIRY-MON lines 896-907 |
| T-146 | Card Detail Update | Expiry month boundary: 12 accepted | BR-COCRDUPC-27 | COCRDUPC | 1250-EDIT-EXPIRY-MON lines 896-907 |
| T-147 | Card Detail Update | Expiry year mandatory | BR-COCRDUPC-28 | COCRDUPC | 1260-EDIT-EXPIRY-YEAR lines 916-924 |
| T-148 | Card Detail Update | Expiry year 1950 accepted (boundary) | BR-COCRDUPC-29 | COCRDUPC | 1260-EDIT-EXPIRY-YEAR lines 930-943 |
| T-149 | Card Detail Update | Expiry year 2099 accepted (boundary) | BR-COCRDUPC-29 | COCRDUPC | 1260-EDIT-EXPIRY-YEAR lines 930-943 |
| T-150 | Card Detail Update | Expiry year 1949 rejected (boundary) | BR-COCRDUPC-29 | COCRDUPC | 1260-EDIT-EXPIRY-YEAR lines 930-943 |
| T-151 | Card Detail Update | Expiry year 2100 rejected (boundary) | BR-COCRDUPC-29 | COCRDUPC | 1260-EDIT-EXPIRY-YEAR lines 930-943 |
| T-152 | Card Detail Update | No-change detection bypasses write | BR-COCRDUPC-20 | COCRDUPC | 1200-EDIT-MAP-INPUTS lines 680-693 |
| T-153 | Card Detail Update | PF5 confirmation required before write | BR-COCRDUPC-30 | COCRDUPC | 1200-EDIT-MAP-INPUTS lines 710-714; 2000-DECIDE-ACTION lines 971-977 |
| T-154 | Card Detail Update | PF5 triggers card record write | BR-COCRDUPC-38, BR-COCRDUPC-42 | COCRDUPC | 2000-DECIDE-ACTION lines 988-1001; 9200-WRITE-PROCESSING lines 1427-1492 |
| T-155 | Card Detail Update | Concurrent modification detected | BR-COCRDUPC-54 | COCRDUPC | 9300-CHECK-CHANGE-IN-REC lines 1499-1519 |
| T-156 | Card Detail Update | Lock failure reported | BR-COCRDUPC-39 | COCRDUPC | 2000-DECIDE-ACTION line 994; 9200-WRITE-PROCESSING lines 1427-1449 |
| T-157 | Card Detail Update | First validation error takes priority | BR-COCRDUPC-31 | COCRDUPC | All 1230/1240/1250/1260 paragraphs (WS-RETURN-MSG-OFF guard) |
| T-158 | Card Detail Update | PF3 exits to calling program | BR-COCRDUPC-5 | COCRDUPC | 0000-MAIN lines 435-476 |
| T-159 | Card Detail Update | PF12 re-fetches card data | BR-COCRDUPC-35 | COCRDUPC | 2000-DECIDE-ACTION lines 958-965 |
| T-160 | User Administration | [KNOWN DEFECT] PF3 unconditionally navigates away regardless of update outcome | BR-COUSR02C-5 | COUSR02C | MAIN-PARA lines 111-119 (Behavioral Anomaly: PF3 Ignores Update Outcome) |
| T-161 | User Administration | PF5 stays on screen after update; distinguishable from PF3 behavior | BR-COUSR02C-8 | COUSR02C | MAIN-PARA lines 122-123; EXEC CICS RETURN line 135 |
| T-162 | Account Statement Generation (Batch) | [KNOWN DEFECT] Balance >= $1B silently truncates in statement output | BR-CBSTM03A-61 | CBSTM03A | 5000-CREATE-STATEMENT line 484 (ST-CURR-BAL PIC Z(9).99-) |
| T-163 | Account Statement Generation (Batch) | [CAPACITY LIMIT] More than 51 distinct card numbers causes array overflow | BR-CBSTM03A-array | CBSTM03A | 8500-READTRNX-READ; WS-CARD-TBL OCCURS 51 TIMES |
| T-164 | Transaction Report Generation (Batch) | Report includes transaction type and category descriptions | BR-CBTRN03C-10, BR-CBTRN03C-11 | CBTRN03C | 1500-B-LOOKUP-TRANTYPE line 494; 1500-C-LOOKUP-TRANCATG line 504; 1120-WRITE-DETAIL line 361 |
| T-165 | Transaction Report Generation (Batch) | Transactions grouped by card number with per-card subtotal | BR-CBTRN03C-4, BR-CBTRN03C-14 | CBTRN03C | Main loop lines 181-188; 1120-WRITE-ACCOUNT-TOTALS line 306 |
| T-166 | Transaction Report Generation (Batch) | Page break at 20 lines; page total and headers repeat | BR-CBTRN03C-6, BR-CBTRN03C-15 | CBTRN03C | 1100-WRITE-TRANSACTION-REPORT lines 282-285; 1110-WRITE-PAGE-TOTALS line 293; 1120-WRITE-HEADERS line 324 |
| T-167 | Transaction Report Generation (Batch) | Grand total written at end of report | BR-CBTRN03C-16 | CBTRN03C | 1110-WRITE-GRAND-TOTALS line 318 |
| T-168 | Transaction Report Generation (Batch) | Date range parameters read; only in-range transactions included | BR-CBTRN03C-1, BR-CBTRN03C-3 | CBTRN03C | 0550-DATEPARM-READ line 220; Main loop lines 173-178 |
| T-169 | Transaction Report Generation (Batch) | Unknown transaction type code causes job abend | BR-CBTRN03C error handling | CBTRN03C | 1500-B-LOOKUP-TRANTYPE line 494 (INVALID KEY branch) |
| T-170 | Transaction Report Generation (Batch) | Unknown transaction category causes job abend | BR-CBTRN03C error handling | CBTRN03C | 1500-C-LOOKUP-TRANCATG line 504 (INVALID KEY branch) |
| T-171 | Transaction Report Generation (Batch) | Card number not in cross-reference causes job abend | BR-CBTRN03C-9 | CBTRN03C | 1500-A-LOOKUP-XREF line 484 (INVALID KEY branch) |
| T-172 | Transaction Report Generation (Batch) | [KNOWN DEFECT] First out-of-range record causes all subsequent records to be skipped | BR-CBTRN03C-2 | CBTRN03C | Main loop line 177 (NEXT SENTENCE exits PERFORM UNTIL at period line 206) |
| T-173 | Transaction Report Generation (Batch) | [KNOWN DEFECT] Final totals corrupted by stale buffer value at EOF | BR-CBTRN03C calculations (EOF anomaly) | CBTRN03C | Main loop lines 200-201 (ADD TRAN-AMT TO WS-PAGE-TOTAL WS-ACCOUNT-TOTAL at EOF) |
| T-174 | Transaction Report Generation (Batch) | [KNOWN DEFECT] Last card group account total not written | BR-CBTRN03C-14 note | CBTRN03C | Main loop lines 181-188; 1120-WRITE-ACCOUNT-TOTALS line 306 (called only at card break, not at EOF) |
| T-175 | Transaction Report Generation (Batch) | Empty transaction input produces report with headers and grand total only (boundary) | BR-CBTRN03C-1, BR-CBTRN03C-16 | CBTRN03C | 0550-DATEPARM-READ line 220; 1110-WRITE-GRAND-TOTALS line 318 |
| T-176 | Reference Data Utility Operations | Account diagnostic writes all records to three output files | BR-CBACT01C-10, BR-CBACT01C-19 | CBACT01C | 1000-ACCTFILE-GET-NEXT line (loop entry); 1350-WRITE-ACCT-RECORD; 1450-WRITE-ARRY-RECORD; 1550-WRITE-VB1-RECORD |
| T-177 | Reference Data Utility Operations | Account output ZIP code silently excluded from all three output formats | BR-CBACT01C-15 | CBACT01C | 1300-POPUL-ACCT-RECORD (absence of MOVE for ACCT-ADDR-ZIP) |
| T-178 | Reference Data Utility Operations | Zero cycle debit replaced by 2525.00 in fixed output | BR-CBACT01C-17 | CBACT01C | 1300-POPUL-ACCT-RECORD line (IF ACCT-CURR-CYC-DEBIT EQUAL TO ZERO MOVE 2525.00) |
| T-179 | Reference Data Utility Operations | [KNOWN DEFECT] Non-zero cycle debit not copied; prior buffer value retained | BR-CBACT01C-18 | CBACT01C | 1300-POPUL-ACCT-RECORD (absence of ELSE branch for ACCT-CURR-CYC-DEBIT) |
| T-180 | Reference Data Utility Operations | Reissue date converted YYYY-MM-DD to YYYYMMDD in fixed output | BR-CBACT01C-16 | CBACT01C | 1300-POPUL-ACCT-RECORD (CALL 'COBDATFT'; MOVE CODATECN-0UT-DATE TO OUT-ACCT-REISSUE-DATE) |
| T-181 | Reference Data Utility Operations | Variable-length file receives two record types per account | BR-CBACT01C-31, BR-CBACT01C-32, BR-CBACT01C-37, BR-CBACT01C-39 | CBACT01C | 1500-POPUL-VBRC-RECORD; 1550-WRITE-VB1-RECORD; 1575-WRITE-VB2-RECORD |
| T-182 | Reference Data Utility Operations | Transaction dry-run validates without posting | BR-CBTRN01C-dryrun | CBTRN01C | Main validation loop (no WRITE to TRANSACT; no REWRITE to ACCTDAT) |
| T-183 | Reference Data Utility Operations | Empty account file produces zero records in all output files (boundary) | BR-CBACT01C-11, BR-CBACT01C-13 | CBACT01C | 1000-ACCTFILE-GET-NEXT (status '10' EOF branch); 9000-ACCTFILE-CLOSE |
| T-184 | Account Inquiry and Update | Account view (read-only) displays full account and customer details for valid account | BR-COACTVWC-28 | COACTVWC | 9000-READ-ACCT lines 693-699; 9200-GETCARDXREF-BYACCT; 9300-GETACCTDATA-BYACCT; 9400-GETCUSTDATA-BYCUST; 1200-SETUP-SCREEN-VARS lines 462-523 |
| T-185 | Account Inquiry and Update | Account number blank rejected on view screen | BR-COACTVWC-12 | COACTVWC | 2210-EDIT-ACCOUNT lines 653-662 |
| T-186 | Account Inquiry and Update | Account number not numeric or all-zeros rejected on view screen | BR-COACTVWC-13, BR-COACTVWC-14 | COACTVWC | 2210-EDIT-ACCOUNT lines 666-676 |
| T-187 | Account Inquiry and Update | Account not found in cross-reference shows error | BR-COACTVWC error-handling (CXACAIX NOTFND) | COACTVWC | 9200-GETCARDXREF-BYACCT lines 741-758 |
| T-188 | Account Inquiry and Update | [KNOWN DEFECT] Customer read attempted even when account master not found | BR-COACTVWC-21 | COACTVWC | 9000-READ-ACCT lines 704-706 (dead skip guard); 9300-GETACCTDATA-BYACCT line 792 (commented-out SET) |
| T-189 | Account Inquiry and Update | SSN displayed as NNN-NN-NNNN on account view screen | BR-COACTVWC-30 | COACTVWC | 1200-SETUP-SCREEN-VARS lines 496-504 (STRING with '-' delimiters) |
| T-190 | Account Inquiry and Update | PF3 exits account view to calling program or main menu | BR-COACTVWC-1, BR-COACTVWC-4 | COACTVWC | 0000-MAIN lines 324-352 |
| T-191 | Account Inquiry and Update | Any key other than Enter or PF3 silently treated as Enter on account view | BR-COACTVWC-2 | COACTVWC | 0000-MAIN lines 306-314 |
| T-192 | Credit Card Management | Card detail view displays embossed name, expiry, and status for valid account and card | BR-COCRDSLC-44, BR-COCRDSLC-45 | COCRDSLC | 9100-GETCARD-BYACCTCARD lines 740-754; 1200-SETUP-SCREEN-VARS lines 474-485 |
| T-193 | Credit Card Management | Account number blank rejected on card detail view | BR-COCRDSLC-13 | COCRDSLC | 2210-EDIT-ACCOUNT lines 651-661 |
| T-194 | Credit Card Management | Account number not numeric rejected on card detail view | BR-COCRDSLC-14 | COCRDSLC | 2210-EDIT-ACCOUNT lines 665-674 |
| T-195 | Credit Card Management | Card number blank rejected on card detail view | BR-COCRDSLC-16 | COCRDSLC | 2220-EDIT-CARD lines 691-702 |
| T-196 | Credit Card Management | Card number not numeric rejected on card detail view | BR-COCRDSLC-17 | COCRDSLC | 2220-EDIT-CARD lines 706-715 |
| T-197 | Credit Card Management | Both account and card blank returns 'No input received' on card detail view | BR-COCRDSLC-19 | COCRDSLC | 2200-EDIT-MAP-INPUTS lines 637-640 |
| T-198 | Credit Card Management | Card not found shows 'Did not find cards for this search condition' | BR-COCRDSLC-46 | COCRDSLC | 9100-GETCARD-BYACCTCARD lines 755-761 |
| T-199 | Credit Card Management | Input fields protected when navigated from card list (COCRDLIC) | BR-COCRDSLC-24 | COCRDSLC, COCRDLIC | 1300-SETUP-SCREEN-ATTRS lines 505-508 |
| T-200 | Credit Card Management | PF3 exits card detail view to calling program or main menu | BR-COCRDSLC-7 | COCRDSLC | 0000-MAIN lines 305-334 |
| T-201 | Transaction Inquiry and Manual Entry | Transaction list displays up to 10 transactions per page | BR-COTRN00C-25 | COTRN00C | PROCESS-PAGE-FORWARD lines 297-303 (WS-IDX loop) |
| T-202 | Transaction Inquiry and Manual Entry | PF8 pages forward through transaction list | BR-COTRN00C-22, BR-COTRN00C-24 | COTRN00C | PROCESS-PF8-KEY lines 259-263; PROCESS-PAGE-FORWARD lines 285-287 (skip-anchor read) |
| T-203 | Transaction Inquiry and Manual Entry | PF7 pages backward through transaction list | BR-COTRN00C-33, BR-COTRN00C-36 | COTRN00C | PROCESS-PF7-KEY lines 236-239; PROCESS-PAGE-BACKWARD lines 339-341 (skip-anchor read) |
| T-204 | Transaction Inquiry and Manual Entry | [KNOWN DEFECT] Invalid row selection error message overwritten by page refresh | BR-COTRN00C-14, BR-COTRN00C-56 | COTRN00C | PROCESS-ENTER-KEY lines 196-203 (commented-out SEND and SET TRANSACT-EOF) |
| T-205 | Transaction Inquiry and Manual Entry | STARTBR EQUAL: non-existent transaction ID returns top-of-page message | BR-COTRN00C-18, BR-COTRN00C-19 | COTRN00C | STARTBR-TRANSACT-FILE line 597 (no GTEQ); lines 605-611 (NOTFND handler) |
| T-206 | Transaction Inquiry and Manual Entry | PF7 at first page suppresses backward scroll with informational message | BR-COTRN00C-31 | COTRN00C | PROCESS-PF7-KEY lines 245-251 |
| T-207 | Transaction Inquiry and Manual Entry | PF8 at last page suppresses forward scroll with informational message | BR-COTRN00C-21 | COTRN00C | PROCESS-PF8-KEY lines 267-273 |
| T-208 | User Administration | User list displays up to 10 users per page | BR-COUSR00C-30 | COUSR00C | PROCESS-PAGE-FORWARD lines 292-306 (WS-IDX loop up to 10) |
| T-209 | User Administration | PF8 pages forward through user list | BR-COUSR00C-26, BR-COUSR00C-23 | COUSR00C | PROCESS-PF8-KEY lines 262-265; PROCESS-PAGE-FORWARD lines 288-290 (skip-anchor) |
| T-210 | User Administration | PF7 pages backward through user list | BR-COUSR00C-22, BR-COUSR00C-34 | COUSR00C | PROCESS-PF7-KEY lines 239-242; PROCESS-PAGE-BACKWARD lines 342-344 (skip-anchor) |
| T-211 | User Administration | PF7 at first page shows already-at-top message | BR-COUSR00C-21 | COUSR00C | PROCESS-PF7-KEY lines 250-254 |
| T-212 | User Administration | PF8 at last page shows already-at-bottom message | BR-COUSR00C-25 | COUSR00C | PROCESS-PF8-KEY lines 272-276 |
| T-213 | User Administration | 'U' selection on row navigates to user update | BR-COUSR00C-11 | COUSR00C, COUSR02C | PROCESS-ENTER-KEY lines 190-199 (XCTL to COUSR02C) |
| T-214 | User Administration | 'D' selection on row navigates to user delete | BR-COUSR00C-12 | COUSR00C, COUSR03C | PROCESS-ENTER-KEY lines 200-209 (XCTL to COUSR03C) |
| T-215 | User Administration | Invalid selection code shows error message in user list | BR-COUSR00C-13 | COUSR00C | PROCESS-ENTER-KEY lines 210-214 |
| T-216 | User Administration | Delete confirmation screen pre-populates user details from USRSEC | BR-COUSR03C-4, BR-COUSR03C-20 | COUSR03C | MAIN-PARA lines 99-105; READ-USER-SEC-FILE lines 269-286 |
| T-217 | User Administration | User not found on delete lookup shows error | BR-COUSR03C-21 | COUSR03C | READ-USER-SEC-FILE lines 287-292 |
| T-218 | User Administration | PF5 confirms delete; success message shown; screen cleared | BR-COUSR03C-8, BR-COUSR03C-23, BR-COUSR03C-24 | COUSR03C | MAIN-PARA lines 121-122; DELETE-USER-SEC-FILE lines 307-322 |
| T-219 | User Administration | [KNOWN DEFECT] DELETE issued even when READ UPDATE fails | BR-COUSR03C-15 | COUSR03C | DELETE-USER-INFO lines 188-192 (single ERR-FLG guard before both PERFORMs) |
| T-220 | User Administration | PF4 clears delete confirmation screen | BR-COUSR03C-7, BR-COUSR03C-27 | COUSR03C | MAIN-PARA lines 119-120; CLEAR-CURRENT-SCREEN lines 341-344 |
| T-221 | User Administration | PF3 exits delete screen to calling program | BR-COUSR03C-6 | COUSR03C | MAIN-PARA lines 111-118 (XCTL to CDEMO-FROM-PROGRAM or COADM01C) |

---

## Coverage Summary

| Capability | Total Tests | Happy Path | Error | Boundary | Confidence |
| ---------- | ----------- | ---------- | ----- | -------- | ---------- |
| User Authentication and Session Management | 12 | 5 | 6 | 1 | high |
| Navigation and Menu Routing | 5 | 4 | 1 | 0 | medium |
| Account Inquiry and Update | 35 | 9 | 20 | 6 | high |
| Credit Card Management | 24 | 12 | 10 | 2 | high |
| Card Detail Update | 29 | 7 | 16 | 6 | high |
| Transaction Inquiry and Manual Entry | 25 | 11 | 12 | 2 | high |
| Bill Payment Processing | 14 | 6 | 7 | 1 | high |
| Daily Transaction Posting (Batch) | 16 | 8 | 6 | 2 | high |
| Interest and Fees Calculation (Batch) | 12 | 8 | 2 | 2 | high |
| Account Statement Generation (Batch) | 8 | 5 | 2 | 1 | medium |
| Transaction Report Generation (Batch) | 13 | 5 | 7 | 1 | high |
| User Administration | 29 | 18 | 10 | 1 | high |
| Report Request (Online to Batch) | 5 | 2 | 2 | 1 | medium |
| Data Migration Export and Import | 6 | 4 | 2 | 0 | medium |
| Reference Data Utility Operations (Batch Diagnostics) | 10 | 8 | 1 | 1 | medium |
| Batch Job Sequencing Utility | 3 | 1 | 0 | 2 | low |
| Cross-capability End-to-End | 8 | 8 | 0 | 0 | high |
| **Total** | **254** | **121** | **104** | **29** | **high** |
## Untested Rules

Business rules from the analysis artifacts that are not covered by any test scenario. These represent gaps requiring SME review or additional test design:

| Rule ID | Program | Rule Description | Reason Untested | Priority |
| ------- | ------- | ---------------- | --------------- | -------- |
| BR-COACTUPC-1 | COACTUPC | Fresh entry initializes COMMAREA when EIBCALEN=0 or entering from COMEN01C with CDEMO-PGM-ENTER | Infrastructure/session setup behavior; covered implicitly by all happy-path scenarios that require a fresh session | Low |
| BR-COACTUPC-2 | COACTUPC | Continuation entry restores COMMAREA from DFHCOMMAREA | Internal CICS session continuation; not directly observable as a black-box test input/output pair | Low |
| BR-COACTUPC-9 | COACTUPC | Invalid AID key overridden to ENTER behavior | Edge behavior for non-standard terminal keys; may be difficult to exercise in a modernized system with different UI | Medium |
| BR-COACTUPC-116 | COACTUPC | Confirmation not given without PF5: re-display for confirmation | Partially covered by T-022; the specific WHEN OTHER re-display (not via PF5) path is implicit | Low |
| BR-COACTUPC-119 | COACTUPC | Unexpected program state causes abend with code 0001 | Cannot be exercised in normal flow; requires a state machine corruption that is not reachable through valid inputs | Low |
| BR-COBIL00C-26 | COBIL00C | Transaction origination and processing timestamps set to same value (no deferred processing) | Internal timestamp semantics; the equality of TRAN-ORIG-TS and TRAN-PROC-TS is verifiable but low-priority | Low |
| BR-CBTRN02C-37 | CBTRN02C | TRAN-RECORD contains no TRAN-ACCT-ID field; account linkage requires re-join via XREF | Data model structural constraint documented in data-contracts.md invariant 4; not a runtime test scenario | Low |
| BR-CBACT04C-3 | CBACT04C | Unconditional DISPLAY of every TCATBAL record (debug artifact) | Functional behavior of debug output to SYSOUT; observable but not a correctness test; SME should decide whether to preserve or remove | Low |
| BR-CBACT04C-33 | CBACT04C | Both timestamps (ORIG and PROC) set to current system time for interest transactions | Internal record-keeping; verifiable as data contract but not a separate behavioral scenario | Low |
| BR-CBSTM03A-tiot | CBSTM03A | MVS TIOT pointer arithmetic to enumerate DD names at runtime | z/OS-specific; has no equivalent in a modernized system; technique should be replaced by a stack-appropriate mechanism. Capacity limits and balance truncation defects now covered by T-162/T-163; TIOT display behavior itself is non-functional in a modernized system | Low |
| BR-CBACT04C-overflow | CBACT04C | Interest COMPUTE has no ON SIZE ERROR; overflow silently truncates result for very large balances x high rates | Overflow scenario requires crafting extreme-value test data; risk is low in practice but should be tested for financial accuracy compliance | Medium |
| BR-COBSWAIT-nonnum | COBSWAIT | No error handling for non-numeric or missing SYSIN; program behavior with invalid input is undefined | Low operational risk; modernized implementation should define this behavior explicitly | Low |
| BR-COTRN02C-55 | COTRN02C | PF5 STARTBR always executes even when key-field error is set (unnecessary I/O) | Anomaly documented in business rules; functionally harmless; no separate scenario needed unless I/O cost is a concern | Low |
| BR-CBTRN02C-defect1 | CBTRN02C | Copy-paste error in DALYREJS close displays XREFFILE status instead of DALYREJS status | Diagnostic display defect; not observable as a functional test failure unless error handling paths are explicitly tested | Low |
| BR-COMEN01C-copaus | COMEN01C | Optional dispatch to COPAUS0C (pending authorization) via CICS INQUIRE if extension module is installed | Extension module; scenarios for Pending Authorization Management (ext) capability not included in this spec due to low confidence in rule coverage | Low |
| BR-CBTRN03C-7 | CBTRN03C | Page size hard-coded to 20 lines; WS-LINE-COUNTER counts all written lines including headers and totals | Non-parameterisable constant; page break behavior is covered by T-166; the line-counter semantics are an implementation detail verified implicitly | Low |
| BR-CBTRN03C-8 | CBTRN03C | First-call MOD check ordering: first-time headers written before MOD check to avoid spurious page break | Implementation ordering detail; correct page-break behavior is verified by T-166 which requires no spurious break on first transaction | Low |
| BR-CBTRN03C-5 | CBTRN03C | First-record flag WS-FIRST-TIME controls one-time header write and date copy | Covered implicitly by T-164 (headers present) and T-168 (date range parameters in report); explicit flag-state scenario not required | Low |
| BR-CBACT01C-8 | CBACT01C | Raw 300-byte account record displayed to SYSOUT after each successful read (twice: raw dump + labeled fields) | Debug display artifact; correctness of output files is tested by T-176; SYSOUT display volume is a non-functional concern | Low |
| BR-CBACT01C-43 | CBACT01C | OUT-FILE, ARRY-FILE, and VBRC-FILE are never explicitly closed; rely on implicit OS close at GOBACK | Implicit-close behavior is OS/JCL managed; a modernized implementation must explicitly close output files; this is a migration note, not a functional test scenario | Medium |
| BR-COUSR00C-15 | COUSR00C | STARTBR EQUAL positioning: exact user ID match required; non-existent filter ID returns NOTFND treated as EOF | STARTBR NOTFND behavior on user list is an implementation detail analogous to T-205 (COTRN00C); the general browse-from-filter behavior is covered by T-208; exact-match-vs-GTEQ semantics are an internal navigation detail | Low |
| BR-COACTVWC-33 | COACTVWC | WS-INFORM-OUTPUT 88-level defined but never set; success path never shows 'Displaying details of given Account' | Dead constant; not observable as a test scenario; the absence of an informational message on success is confirmed by T-184 (no info-message precondition) | Low |
| BR-COACTUPC-113 | COACTUPC | 9600-WRITE-PROCESSING issues EXEC CICS SYNCPOINT ROLLBACK (line 4100) when REWRITE fails after acquiring the record lock (LOCKED-BUT-UPDATE-FAILED path); the SYNCPOINT ROLLBACK call has no RESP clause — if CICS fails to roll back (e.g., due to syncpoint scope constraints), the failure is unhandled | The LOCKED-BUT-UPDATE-FAILED scenario itself (record locked but REWRITE rejected) is not covered by any test; SYNCPOINT ROLLBACK failure within that path is therefore doubly untested | Medium |
