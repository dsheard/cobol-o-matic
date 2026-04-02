---
type: test-specifications
subtype: equivalence-matrix
status: draft
confidence: high
last_pass: 5
---

# Equivalence Matrix

Traceability from test scenarios back to business rules and source programs. This matrix is a reference for auditors and SMEs -- it does not dictate test organisation (tests are organised by capability, not by program).

---

## Traceability

| Test ID | Capability | Scenario | Business Rules | Source Programs | Source Paragraphs |
| ------- | ---------- | -------- | -------------- | --------------- | ----------------- |
| T-001 | Navigation and Session Management | First-time menu display | BR-BNKMENU-1 | BNKMENU | A010 line 116 |
| T-002 | Navigation and Session Management | Select option 1 (Display Customer) | BR-BNKMENU-9 | BNKMENU | IOT010 line 386 |
| T-003 | Navigation and Session Management | Select option 2 (Display Account) | BR-BNKMENU-10 | BNKMENU | IOT010 line 458 |
| T-004 | Navigation and Session Management | Select option 3 (Create Customer) | BR-BNKMENU-11 | BNKMENU | IOT010 line 531 |
| T-005 | Navigation and Session Management | Select option 4 (Create Account) | BR-BNKMENU-12 | BNKMENU | IOT010 line 604 |
| T-006 | Navigation and Session Management | Select option 5 (Update Account) | BR-BNKMENU-13 | BNKMENU | IOT010 line 677 |
| T-007 | Navigation and Session Management | Select option 6 (Credit/Debit) | BR-BNKMENU-14 | BNKMENU | IOT010 line 750 |
| T-008 | Navigation and Session Management | Select option 7 (Fund Transfer) | BR-BNKMENU-15 | BNKMENU | IOT010 line 823 |
| T-009 | Navigation and Session Management | Select option A (Accounts by Customer) | BR-BNKMENU-16 | BNKMENU | IOT010 line 897 |
| T-010 | Navigation and Session Management | Invalid selection value | BR-BNKMENU-7 | BNKMENU | EMD010 line 360 |
| T-011 | Navigation and Session Management | Session termination via PF3 | BR-BNKMENU-3 | BNKMENU | A010 line 131, STM010 |
| T-012 | Navigation and Session Management | Session termination via PF12 | BR-BNKMENU-3 | BNKMENU | A010 line 131, STM010 |
| T-013 | Navigation and Session Management | Clear key clears screen and ends session | BR-BNKMENU-4 | BNKMENU | A010 line 141 |
| T-014 | Navigation and Session Management | PA key is a no-op | BR-BNKMENU-2 | BNKMENU | A010 line 125 |
| T-015 | Navigation and Session Management | Any unrecognised function key shows error | BR-BNKMENU-6 | BNKMENU | A010 line 158 |
| T-016 | Navigation and Session Management | Empty selection field (boundary) | BR-BNKMENU-7 | BNKMENU | EMD010 line 360 |
| T-017 | Customer Enquiry | Retrieve known customer by number | BR-INQCUST-3, BR-INQCUST-5, BR-INQCUST-25 | INQCUST | P010 lines 178-179, RCV010, P010 lines 220-238 |
| T-018 | Customer Enquiry | Customer number not found | BR-INQCUST-11 | INQCUST | RCV010 lines 339-351 |
| T-019 | Customer Enquiry | Retrieve last (highest-numbered) customer | BR-INQCUST-2 | INQCUST | P010 lines 190-198, GLCV010 |
| T-020 | Customer Enquiry | Retrieve random customer | BR-INQCUST-1, BR-INQCUST-7 | INQCUST | P010 lines 190-207, GRC010, RCV010 lines 310-315 |
| T-021 | Customer Enquiry | Random customer lookup exhausts retry limit | BR-INQCUST-8 | INQCUST | RCV010 lines 316-320 |
| T-022 | Customer Enquiry | All-nines sentinel with empty customer store causes abend | BR-INQCUST-10 | INQCUST | RCV010 lines 323-331, 357-420 (CVR1 abend path on second NOTFND) |
| T-023 | Customer Enquiry | Minimum customer number boundary | BR-INQCUST-3 | INQCUST | RCV010 lines 276-280 |
| T-024 | Customer Enquiry | Maximum customer number boundary | BR-INQCUST-3 | INQCUST | RCV010 lines 276-280 |
| T-025 | Customer Creation with Credit Scoring | Create customer with valid title and DOB | BR-CRECUST-1, BR-CRECUST-8, BR-CRECUST-29, BR-CRECUST-43 | BNK1CCS, CRECUST, CRDTAGY1-5 | P010, CC010, GLCV010, WCV010, WPD010 |
| T-026 | Customer Creation with Credit Scoring | Invalid customer title rejected | BR-CRECUST-1, BR-BNK1CCS-15 | CRECUST, BNK1CCS | P010 lines 365-412 (CRECUST), ED010 lines 604-780 (BNK1CCS) |
| T-027 | Customer Creation with Credit Scoring | Blank title is accepted | BR-CRECUST-2 | CRECUST | P010 lines 401-402 |
| T-028 | Customer Creation with Credit Scoring | All valid titles accepted | BR-CRECUST-1, BR-BNK1CCS-15 | CRECUST, BNK1CCS | P010 lines 365-412 (CRECUST), ED010 lines 607-769 (BNK1CCS normalisation) |
| T-029 | Customer Creation with Credit Scoring | Date of birth in the future rejected | BR-CRECUST-6, BR-BNK1CCS-47 | CRECUST, BNK1CCS | DOBC010 lines 1472-1475 (CRECUST), CCD010 lines 1056-1059 (BNK1CCS) |
| T-030 | Customer Creation with Credit Scoring | Date of birth year before 1601 rejected | BR-CRECUST-3, BR-BNK1CCS-46 | CRECUST, BNK1CCS | DOBC010 lines 1427-1431 (CRECUST), CCD010 lines 1052-1055 (BNK1CCS) |
| T-031 | Customer Creation with Credit Scoring | Date of birth year exactly 1601 accepted | BR-CRECUST-3 | CRECUST | DOBC010 lines 1427-1431 |
| T-032 | Customer Creation with Credit Scoring | Customer age exceeds 150 years rejected | BR-CRECUST-5, BR-BNK1CCS-46 | CRECUST, BNK1CCS | DOBC010 lines 1466-1470 (CRECUST), CCD010 lines 1052-1055 (BNK1CCS) |
| T-033 | Customer Creation with Credit Scoring | Customer age exactly 150 years accepted | BR-CRECUST-5 | CRECUST | DOBC010 lines 1466-1470 |
| T-034 | Customer Creation with Credit Scoring | Invalid date of birth (non-existent day) rejected | BR-CRECUST-4, BR-BNK1CCS-48 | CRECUST, BNK1CCS | DOBC010 lines 1437-1449 (CRECUST CEEDAYS), CCD010 lines 1060-1063 (BNK1CCS) |
| T-035 | Customer Creation with Credit Scoring | Leap year DOB is valid | BR-CRECUST-4 | CRECUST | DOBC010 lines 1437-1449 (CEEDAYS call) |
| T-036 | Customer Creation with Credit Scoring | Credit score is integer average of agency responses | BR-CRECUST-calc-1 | CRECUST | CC010 lines 757-759 |
| T-037 | Customer Creation with Credit Scoring | Credit score review date is 1-20 days in future | BR-CRECUST-calc-3 | CRECUST | CC010 lines 777-797 |
| T-038 | Customer Creation with Credit Scoring | Credit check failure returns error | BR-CRECUST-17, BR-CRECUST-19 | CRECUST | CC010 lines 722-741, 805-826 |
| T-039 | Customer Creation with Credit Scoring | Customer number is sequential | BR-CRECUST-29 | CRECUST | GLCV010 lines 1381-1416 |
| T-040 | Customer Creation with Credit Scoring | Concurrent creation serialised correctly | BR-CRECUST-26, BR-CRECUST-27 | CRECUST | ENC010 lines 504-515 (ENQ/DEQ) |
| T-041 | Customer Creation with Credit Scoring | Audit record written on success | BR-CRECUST-44, BR-CRECUST-48 | CRECUST | WPD010 lines 1195-1323 |
| T-042 | Account Enquiry | Retrieve known account by number | BR-INQACC-4, BR-INQACC-12 | INQACC | A010 line 221, RAD010, FD010 |
| T-043 | Account Enquiry | Account number not found | BR-INQACC-3, BR-INQACC-10 | INQACC | FD010 lines 450-458 |
| T-044 | Account Enquiry | Retrieve highest-numbered account (sentinel) | BR-INQACC-1, BR-INQACC-13 | INQACC | A010 line 218, GLAD010 lines 843-936 |
| T-045 | Account Enquiry | No accounts exist for sentinel lookup | BR-INQACC-15 | INQACC | GLAD010 lines 937-981 |
| T-046 | Account Enquiry | Minimum valid account number | BR-INQACC-2 | INQACC | RAD010, FD010 |
| T-047 | Account Enquiry | Maximum valid account number | BR-INQACC-2 | INQACC | RAD010, FD010 |
| T-048 | Account Enquiry | Date fields returned in day/month/year format | BR-INQACC-12 | INQACC | FD010 lines 534-572 (DB2-DATE-REFORMAT) |
| T-049 | Accounts Enquiry by Customer | Retrieve all accounts for existing customer | BR-INQACCCU-3, BR-INQACCCU-7, BR-INQACCCU-10 | INQACCCU, BNK1CCA | CC010 line 855, FD010 lines 583-631, RAD010 line 448 |
| T-050 | Accounts Enquiry by Customer | Customer with no accounts | BR-INQACCCU-9 | INQACCCU | FD010 lines 485-488 |
| T-051 | Accounts Enquiry by Customer | Customer number not found | BR-INQACCCU-3, BR-INQACCCU-4 | INQACCCU, INQCUST | CC010 lines 835-855, A010 lines 215-219 |
| T-052 | Accounts Enquiry by Customer | Customer number zero rejected | BR-INQACCCU-1 | INQACCCU | CC010 line 835 |
| T-053 | Accounts Enquiry by Customer | Customer with 20 accounts (system max) | BR-INQACCCU-5 | INQACCCU | FD010 lines 463-464 |
| T-054 | Account Creation | Create ISA account | BR-CREACC-1, BR-CREACC-5, BR-CREACC-21, BR-CREACC-28, BR-CREACC-30 | BNK1CAC, CREACC, INQCUST, INQACCCU | P010, ATC010, ENC010, FNA010, WAD010, WPD010, DNC010 |
| T-055 | Account Creation | Create MORTGAGE account | BR-CREACC-5 | CREACC | ATC010 line 1215 |
| T-056 | Account Creation | Create SAVING account | BR-CREACC-5 | CREACC | ATC010 line 1215 |
| T-057 | Account Creation | Create CURRENT account | BR-CREACC-5 | CREACC | ATC010 line 1215 |
| T-058 | Account Creation | Create LOAN account | BR-CREACC-5 | CREACC | ATC010 line 1215 |
| T-059 | Account Creation | Invalid account type rejected | BR-CREACC-5, BR-CREACC-6, BR-BNK1CAC-40 | CREACC, BNK1CAC | ATC010 line 1222, CAD010 line 911 |
| T-060 | Account Creation | Customer does not exist | BR-CREACC-1, BR-BNK1CAC-31 | CREACC, INQCUST, BNK1CAC | P010 line 314, CAD010 line 851 |
| T-061 | Account Creation | Customer at 10-account limit rejected | BR-CREACC-4, BR-BNK1CAC-38 | CREACC, INQACCCU, BNK1CAC | P010 line 347, CAD010 line 897 |
| T-062 | Account Creation | Customer with 9 accounts can create 10th | BR-CREACC-4 | CREACC, INQACCCU | P010 line 347 |
| T-063 | Account Creation | Account number is sequential | BR-CREACC-12, BR-CREACC-14 | CREACC | FNA010 lines 444-529 |
| T-064 | Account Creation | Concurrent account creation serialised | BR-CREACC-8 | CREACC | ENC010 line 390 (ENQ) |
| T-065 | Account Creation | Next statement date is 30 days after opening | BR-CREACC-24 | CREACC | WAD010 lines 808-824 |
| T-066 | Account Creation | Audit record written on creation | BR-CREACC-31, BR-CREACC-32 | CREACC | WPD010 lines 937-1006 |
| T-067 | Account Creation | Account and audit record are atomic | BR-CREACC-28, BR-CREACC-36 | CREACC | WAD010 line 883, WPD010 line 999 |
| T-068 | Account Creation | Blank account type rejected | BR-CREACC-5, BR-CREACC-6, BR-BNK1CAC-13 | CREACC, BNK1CAC | ATC010 line 1222, ED010 line 459 (BNK1CAC) |
| T-069 | Account Update | Update account type, interest rate, and overdraft limit | BR-UPDACC-3, BR-UPDACC-5 | BNK1UAC, UPDACC, INQACC | UAD010 lines 267-327 |
| T-070 | Account Update | Balances are never changed by account update | BR-UPDACC-3 | UPDACC | UAD010 lines 278-285 |
| T-071 | Account Update | No audit record written for account update | BR-UPDACC-3 | UPDACC | UAD010 lines 278-285 (absence: no PROCTRAN INSERT anywhere in UPDACC procedure division) |
| T-072 | Account Update | Account not found returns failure | BR-UPDACC-2 | UPDACC | UAD010 lines 225-233 |
| T-073 | Account Update | Blank account type rejected | BR-UPDACC-1, BR-BNK1UAC-16 | UPDACC, BNK1UAC | UAD010 lines 267-272, VD010 line 511 (BNK1UAC) |
| T-074 | Account Update | Sort code is always the installation constant | BR-UPDACC-6 | UPDACC | UAD010 line 213 (MOVE SORTCODE TO COMM-SCODE) |
| T-075 | Account Update | Statement dates are never changed by account update | BR-UPDACC-3 | UPDACC | UAD010 lines 278-285 (UPDATE only 3 fields) |
| T-076 | Account Deletion | Delete an existing account | BR-DELACC-8, BR-DELACC-9, BR-DELACC-11, BR-DELACC-14, BR-DELACC-16 | BNK1DAC, DELACC | A010, RAD010, DADB010, WP010, WPD010 |
| T-077 | Account Deletion | Audit record captures actual balance at deletion time | BR-DELACC-16 | DELACC | WPD010 line 519; RAD010 lines 411, 425 |
| T-078 | Account Deletion | Account not found returns fail code 1 with specific message | BR-DELACC-3, BR-BNK1DAC-26 | DELACC, BNK1DAC | RAD010 lines 350-357 (DELACC), DAD010 lines 733-743 (BNK1DAC) |
| T-079 | Account Deletion | Audit record transaction type is 'ODA' | BR-DELACC-14, BR-DELACC-15 | DELACC | WPD010 lines 472, 509-512 |
| T-080 | Account Deletion | Negative balance account deleted correctly | BR-DELACC-16 | DELACC | WPD010 line 519 |
| T-081 | Account Deletion | Delete requires prior successful account enquiry | BR-BNK1DAC-13, BR-BNK1DAC-14 | BNK1DAC | VD010 lines 530-538 (BNK1DAC) |
| T-082 | Customer Update | Update customer name and address | BR-UPDCUST-18, BR-UPDCUST-19, BR-UPDCUST-20 | BNK1DCS, UPDCUST | UCV010 lines 262-285 |
| T-083 | Customer Update | Update name only | BR-UPDCUST-17 | UPDCUST | UCV010 lines 277-280 |
| T-084 | Customer Update | Update address only | BR-UPDCUST-16 | UPDCUST | UCV010 lines 272-275 |
| T-085 | Customer Update | Invalid title rejected | BR-UPDCUST-1, BR-UPDCUST-14, BR-BNK1DCS-19 | UPDCUST, BNK1DCS | A010 lines 153-195 (UPDCUST), ED2010 lines (BNK1DCS) |
| T-086 | Customer Update | Both name and address blank rejected | BR-UPDCUST-15 | UPDCUST | UCV010 lines 262-270 |
| T-087 | Customer Update | Customer not found returns failure | BR-UPDCUST-23 | UPDCUST | UCV010 lines 220-243 |
| T-088 | Customer Update | Date of birth is read-only | BR-UPDCUST-19 | UPDCUST | UCV010 lines 262-285 (CUSTOMER-DATE-OF-BIRTH excluded from REWRITE fields) |
| T-089 | Customer Update | Credit score is read-only | BR-UPDCUST-20 | UPDCUST | UCV010 lines 262-285 (CUSTOMER-CREDIT-SCORE excluded from REWRITE fields) |
| T-090 | Customer Update | All valid titles accepted | BR-UPDCUST-2 through BR-UPDCUST-11 | UPDCUST | A010 lines 153-195 |
| T-091 | Customer Update | No audit record written for customer update | BR-UPDCUST-18 | UPDCUST | UCV010 lines 262-285 (absence: no PROCTRAN INSERT anywhere in UPDCUST procedure division) |
| T-092 | Customer Update | Address all-spaces rejected in update | BR-BNK1DCS-21 | BNK1DCS | ED2010 line (BNK1DCS address validation: CUSTAD1I = SPACES AND CUSTAD2I = SPACES AND CUSTAD3I = SPACES) |
| T-093 | Customer Update | Customer number zero or all-nines rejected | BR-BNK1DCS-23 | BNK1DCS | VD010 line (BNK1DCS: CUSTNOI = ZERO OR CUSTNOI = '9999999999' check) |
| T-094 | Customer Deletion (Full Cascade) | Delete customer with multiple accounts | BR-DELCUS-1, BR-DELCUS-3, BR-DELCUS-4, BR-DELCUS-20, BR-DELCUS-22, BR-DELCUS-24 | BNK1DCS, DELCUS, INQCUST, INQACCCU, DELACC | A010, GAC010, DA010, DCV010, WPCD010 |
| T-095 | Customer Deletion (Full Cascade) | Delete customer with no accounts | BR-DELCUS-3 | DELCUS, INQCUST, INQACCCU | A010 lines 276-278 (NUMBER-OF-ACCOUNTS = 0 branch) |
| T-096 | Customer Deletion (Full Cascade) | Non-existent customer returns failure | BR-DELCUS-1 | DELCUS, INQCUST | A010 lines 264-269 |
| T-097 | Customer Deletion (Full Cascade) | Delete customer with 20 accounts | BR-DELCUS-6 | DELCUS, INQACCCU, DELACC | DA010 lines 306-316 |
| T-098 | Customer Deletion (Full Cascade) | Customer-deletion audit type is 'ODC' with zero amount | BR-DELCUS-22, BR-DELCUS-23, BR-DELCUS-21 | DELCUS | WPCD010 lines 606, 633 |
| T-099 | Customer Deletion (Full Cascade) | Concurrent deletion detected gracefully | BR-DELCUS-12 | DELCUS | DCV010 lines 384-389 (NOTFND treated as concurrent delete) |
| T-100 | Debit / Credit Funds | Teller withdrawal from CURRENT account | BR-DBCRFUN-10, BR-DBCRFUN-16, BR-DBCRFUN-17, BR-DBCRFUN-21 | BNK1CRA, DBCRFUN | UAD010 lines 307, 384, 386; WTPD010 line 492 |
| T-101 | Debit / Credit Funds | Teller deposit to CURRENT account | BR-DBCRFUN-16, BR-DBCRFUN-17, BR-DBCRFUN-23 | BNK1CRA, DBCRFUN | UAD010 lines 384, 386; WTPD010 line 505 |
| T-102 | Debit / Credit Funds | Payment-link credit to CURRENT account | BR-DBCRFUN-16, BR-DBCRFUN-24 | BNK1CRA, DBCRFUN | UAD010 lines 384, 386; WTPD010 line 512 |
| T-103 | Debit / Credit Funds | Payment-link debit with sufficient funds | BR-DBCRFUN-9, BR-DBCRFUN-22 | BNK1CRA, DBCRFUN | UAD010 lines 341-344; WTPD010 line 499 |
| T-104 | Debit / Credit Funds | Payment-link debit with insufficient funds | BR-DBCRFUN-9 | DBCRFUN | UAD010 lines 341-344 |
| T-105 | Debit / Credit Funds | Payment-link debit to MORTGAGE account rejected | BR-DBCRFUN-7 | DBCRFUN | UAD010 line 330 |
| T-106 | Debit / Credit Funds | Payment-link debit to LOAN account rejected | BR-DBCRFUN-8 | DBCRFUN | UAD010 line 332 |
| T-107 | Debit / Credit Funds | Payment-link credit to MORTGAGE account rejected | BR-DBCRFUN-11 | DBCRFUN | UAD010 line 368 |
| T-108 | Debit / Credit Funds | Payment-link credit to LOAN account rejected | BR-DBCRFUN-12 | DBCRFUN | UAD010 line 370 |
| T-109 | Debit / Credit Funds | Teller debit to MORTGAGE account allowed | BR-DBCRFUN-13 | DBCRFUN | UAD010 line 368 (COMM-FACILTYPE not 496) |
| T-110 | Debit / Credit Funds | Account not found returns failure | BR-DBCRFUN-5 | DBCRFUN | UAD010 line 283 |
| T-111 | Debit / Credit Funds | Teller debit bypasses available balance check | BR-DBCRFUN-10 | DBCRFUN | UAD010 line 307 (no funds check for teller) |
| T-112 | Debit / Credit Funds | Maximum signed amount (boundary) | BR-DBCRFUN-16 | DBCRFUN | UAD010 line 384 (PIC S9(10)V99) |
| T-113 | Debit / Credit Funds | Failed PROCTRAN write rolls back balance update | BR-DBCRFUN-30 | DBCRFUN | WTPD010 lines 554-569 (rollback on audit fail) |
| T-114 | Debit / Credit Funds | Audit record amount equals the transaction amount | BR-DBCRFUN-28 | DBCRFUN | WTPD010 line 492 |
| T-115 | Fund Transfer | Transfer between two valid accounts (source lower) | BR-XFRFUN-1, BR-XFRFUN-3, BR-XFRFUN-35 | BNK1TFN, XFRFUN | A010, UAD010, UADF010, UADT010, WTPD010 |
| T-116 | Fund Transfer | Transfer with higher source account number (reverse order) | BR-XFRFUN-4, BR-XFRFUN-36 | XFRFUN | UAD010 line 589 (reverse order path); UADT010 line 1044 (COMM-SUCCESS reset) |
| T-117 | Fund Transfer | Zero or negative transfer amount rejected | BR-XFRFUN-1, BR-BNK1TFN-15, BR-BNK1TFN-17 | XFRFUN, BNK1TFN | A010 line 289, VA010 line 994 (BNK1TFN) |
| T-118 | Fund Transfer | Source account not found with specific message | BR-XFRFUN-5, BR-BNK1TFN-23 | XFRFUN, BNK1TFN | UADF010 line 964 (XFRFUN), GCD010 line 587 (BNK1TFN) |
| T-119 | Fund Transfer | Target account not found triggers rollback with specific message | BR-XFRFUN-8, BR-BNK1TFN-24 | XFRFUN, BNK1TFN | UADT010 lines 1102-1116 (XFRFUN), GCD010 line 595 (BNK1TFN) |
| T-120 | Fund Transfer | Cross-sort-code transfer silently uses own sort code | BR-XFRFUN-35 | XFRFUN | A010 line 281 |
| T-121 | Fund Transfer | Audit record keyed on source account | BR-XFRFUN-27, BR-XFRFUN-26 | XFRFUN | WTPD010 lines 1581, 1610 |
| T-122 | Fund Transfer | No overdraft limit check performed | BR-XFRFUN-note-1 | XFRFUN | UADF010 lines 986-989 (no limit check) |
| T-123 | Fund Transfer | Minimum valid transfer amount (boundary) | BR-XFRFUN-1, BR-BNK1TFN-15 | XFRFUN, BNK1TFN | A010 line 289, VA010 line 1009 (BNK1TFN) |
| T-124 | Fund Transfer | Deadlock retried up to 5 times | BR-XFRFUN-10, BR-XFRFUN-13 | XFRFUN | UADT010 lines 1197-1241 |
| T-125 | Fund Transfer | FROM and TO account numbers must differ | BR-BNK1TFN-10 | BNK1TFN | ED010 line (FACCNOI = TACCNOI check, BNK1TFN) |
| T-126 | Fund Transfer | Account number 00000000 is invalid | BR-BNK1TFN-11 | BNK1TFN | ED010 line (FACCNOI = '00000000' OR TACCNOI = '00000000', BNK1TFN) |
| T-127 | Fund Transfer | Transfer amount with embedded spaces rejected | BR-BNK1TFN-18 | BNK1TFN | VA010 line 1103 (WS-NUM-COUNT-SPACE > 0, BNK1TFN) |
| T-128 | Fund Transfer | Transfer amount with more than two decimal places rejected | BR-BNK1TFN-21 | BNK1TFN | VA010 lines 1145-1186 (BNK1TFN) |
| T-129 | Fund Transfer | Transfer amount with multiple decimal points rejected | BR-BNK1TFN-20 | BNK1TFN | VA010 line 1133 (WS-NUM-COUNT-POINT > 1, BNK1TFN) |
| T-130 | Centralised Abend Logging | Abend record written on application error | BR-ABNDPROC-1 | ABNDPROC | PREMIERE/A010 lines 139-147 |
| T-131 | Centralised Abend Logging | Abend record write failure is non-fatal | BR-ABNDPROC-3 | ABNDPROC | PREMIERE/A010 lines 149-158 |
| T-132 | Centralised Abend Logging | Key uniqueness via timestamp and task number | BR-ABNDPROC-4 | ABNDPROC | PREMIERE/A010 lines 141-147 (ABND-VSAM-KEY composite) |
| T-133 | Centralised Abend Logging | All 600 bytes of freeform text preserved | BR-ABNDPROC-15 | ABNDPROC | ABNDINFO copybook ABND-FREEFORM PIC X(600) |
| T-134 | Utility Services | Retrieve company name | BR-GETCOMPY-1 | GETCOMPY | A010 line 38 |
| T-135 | Utility Services | Retrieve sort code | BR-GETSCODE-1 | GETSCODE | A010 (PREMIERE section, MOVE LITERAL-SORTCODE TO SORTCODE OF DFHCOMMAREA) |
| T-136 | Utility Services | Company name is always the same value | BR-GETCOMPY-1 | GETCOMPY | A010 line 38 (hardcoded literal 'CICS Bank Sample Application') |
| T-137 | Utility Services | Sort code is always exactly 6 characters | BR-GETSCODE-1 | GETSCODE | A010 (MOVE to PIC X(6) field in DFHCOMMAREA) |
| T-138 | Test Data Initialisation | Batch initialisation with valid parameter range | BR-BANKDATA-1, BR-BANKDATA-2, BR-BANKDATA-3 | BANKDATA | A010 (PARMCHECK section lines 397-407) |
| T-139 | Test Data Initialisation | END parameter less than START rejected | BR-BANKDATA-1 | BANKDATA | A010 lines 397-402 |
| T-140 | Test Data Initialisation | STEP parameter zero rejected | BR-BANKDATA-2 | BANKDATA | A010 lines 403-407 |
| T-141 | Test Data Initialisation | LOAN and MORTGAGE accounts have negative balances | BR-BANKDATA-29 | BANKDATA | PA010 lines 797-806 |
| T-142 | Test Data Initialisation | Fixed interest rates per account type | BR-BANKDATA-23 | BANKDATA | IA010 lines 1160-1165; PA010 lines 757-758 |
| T-143 | Test Data Initialisation | Statement dates hard-coded to 2021 | BR-BANKDATA-25, BR-BANKDATA-26 | BANKDATA | PA010 lines 769-784 |
| T-144 | Test Data Initialisation | Single customer when start equals end (boundary) | BR-BANKDATA-1 | BANKDATA | A010 (PERFORM VARYING NEXT-KEY from start BY step UNTIL > end) |
| T-145 | Test Data Initialisation | Control sentinel record in VSAM | BR-BANKDATA-33 | BANKDATA | A010 lines 588-600 |
| T-146 | Test Data Initialisation | Each customer gets 1-5 accounts | BR-BANKDATA-15 | BANKDATA | DA010 lines 701-705 |
| T-147 | Test Data Initialisation | VSAM sentinel has zero customer count and zero last-customer-number | BR-BANKDATA-34, BR-BANKDATA-35 | BANKDATA | A010 lines 588-600 (sentinel write, no population of NUMBER-OF-CUSTOMERS or LAST-CUSTOMER-NUMBER) |
| T-148 | Customer Creation with Credit Scoring | First name is mandatory on creation screen | BR-BNK1CCS-26 | BNK1CCS | ED010 lines 783-792 (BNK1CCS) |
| T-149 | Customer Creation with Credit Scoring | Surname is mandatory on creation screen | BR-BNK1CCS-27 | BNK1CCS | ED010 lines 794-803 (BNK1CCS) |
| T-150 | Customer Creation with Credit Scoring | Address line 1 is mandatory on creation screen | BR-BNK1CCS-28 | BNK1CCS | ED010 lines 805-814 (BNK1CCS) |
| T-151 | Customer Creation with Credit Scoring | DOB day field must not be blank | BR-BNK1CCS-29 | BNK1CCS | ED010 lines 816-824 (BNK1CCS) |
| T-152 | Customer Creation with Credit Scoring | Non-numeric DOB day rejected | BR-BNK1CCS-32 | BNK1CCS | ED010 lines 846-854 (BNK1CCS) |
| T-153 | Customer Creation with Credit Scoring | DOB day out of range rejected (boundary) | BR-BNK1CCS-35 | BNK1CCS | ED010 lines 876-886 (BNK1CCS, DOBDDI-NUM < 01 OR > 31) |
| T-154 | Customer Creation with Credit Scoring | DOB month out of range rejected (boundary) | BR-BNK1CCS-36 | BNK1CCS | ED010 lines 888-897 (BNK1CCS, DOBMMI-NUM < 01 OR > 12) |
| T-155 | Customer Creation with Credit Scoring | Title case-insensitive normalisation accepted | BR-BNK1CCS-16 | BNK1CCS | ED010 lines 607-620 (BNK1CCS, 'MR' MOVE to 'Mr') |
| T-156 | Customer Creation with Credit Scoring | Pre-filled customer number field causes rejection | BR-BNK1CCS-13 | BNK1CCS | ED010 lines 581-587 (BNK1CCS, CUSTNO2L > 0) |
| T-157 | Customer Creation with Credit Scoring | DOB month field must not be blank | BR-BNK1CCS-30 | BNK1CCS | ED010 lines 826-834 (BNK1CCS) |
| T-158 | Customer Creation with Credit Scoring | DOB year field must not be blank | BR-BNK1CCS-31 | BNK1CCS | ED010 lines 836-844 (BNK1CCS) |
| T-159 | Account Creation | Negative interest rate rejected | BR-BNK1CAC-24 | BNK1CAC | ED010 line 663 (BNK1CAC, INTRTI-COMP-1 < 0) |
| T-160 | Account Creation | Interest rate above maximum rejected | BR-BNK1CAC-25 | BNK1CAC | ED010 line 673 (BNK1CAC, INTRTI-COMP-1 > 9999.99) |
| T-161 | Account Creation | Interest rate with multiple decimal points rejected | BR-BNK1CAC-22 | BNK1CAC | ED010 line 594 (BNK1CAC, WS-NUM-COUNT-POINT > 1) |
| T-162 | Account Creation | Overdraft limit defaults to zero when omitted | BR-BNK1CAC-27 | BNK1CAC | ED010 line 717 (BNK1CAC, MOVE ZERO TO OVERDRI) |
| T-163 | Account Creation | Lowercase account type accepted and normalised | BR-BNK1CAC-15, BR-BNK1CAC-16 | BNK1CAC | ED010 lines 475, 486 (BNK1CAC normalisation to canonical padded form) |
| T-164 | Account Creation | Interest rate at maximum boundary (9999.99) accepted | BR-BNK1CAC-25 | BNK1CAC | ED010 line 673 (BNK1CAC, boundary at 9999.99) |
| T-165 | Customer Update | Address all-spaces rejected in update | BR-BNK1DCS-21 | BNK1DCS | ED2010 line (BNK1DCS, CUSTAD1I = SPACES AND CUSTAD2I = SPACES AND CUSTAD3I = SPACES) |
| T-166 | Customer Update | Customer number zero or all-nines rejected | BR-BNK1DCS-23 | BNK1DCS | VD010 line (BNK1DCS, CUSTNOI = ZERO OR CUSTNOI = '9999999999') |
| T-167 | Accounts Enquiry by Customer | Screen display limited to 10 rows for customers with 11-20 accounts | BR-BNK1CCA-19 | BNK1CCA | GCD010 line 552 (UNTIL WS-INDEX > NUMBER-OF-ACCOUNTS OR WS-INDEX > 10) |
| T-168 | Accounts Enquiry by Customer | Non-numeric customer number rejected on enquiry screen | BR-BNK1CCA-9 | BNK1CCA | ED010 line 411 (BNK1CCA, CUSTNOI NOT NUMERIC) |
| T-169 | Account Update | LOAN account with zero interest rate rejected on update screen | BR-BNK1UAC-23 | BNK1UAC | VD010 line 667 (BNK1UAC, ACTYPEI = 'LOAN    ' AND INTRTI = '0000.00') |
| T-170 | Account Update | MORTGAGE account with zero interest rate rejected on update screen | BR-BNK1UAC-23 | BNK1UAC | VD010 line 667 (BNK1UAC, ACTYPEI = 'MORTGAGE' AND INTRTI = '0000.00') |
| T-171 | Account Update | Last statement date day 0 or month 0 rejected | BR-BNK1UAC-27 | BNK1UAC | VD010 lines 709-717 (BNK1UAC, WS-LSTMTDDI = 0 OR WS-LSTMTMMI = 0) |
| T-172 | Account Update | Last statement date day 31 and month April rejected | BR-BNK1UAC-28 | BNK1UAC | VD010 lines 719-727 (BNK1UAC, WS-LSTMTDDI=31 AND WS-LSTMTMMI=4) |
| T-173 | Account Update | Last statement date day 30 and month February rejected | BR-BNK1UAC-28 | BNK1UAC | VD010 lines 719-727 (BNK1UAC, WS-LSTMTDDI>29 AND WS-LSTMTMMI=2) |
| T-174 | Account Update | Next statement date day 31 and month June rejected | BR-BNK1UAC-29 | BNK1UAC | VD010 lines 733-741 (BNK1UAC, WS-NSTMTDDI=31 AND WS-NSTMTMMI=6) |
| T-175 | Account Update | Interest rate with non-numeric characters rejected on update screen | BR-BNK1UAC-18 | BNK1UAC | VD010 lines 536-546 (BNK1UAC, INTRTI NOT NUMERIC after INSPECT) |
| T-176 | Account Update | Negative interest rate rejected on update screen | BR-BNK1UAC-21 | BNK1UAC | VD010 line 646 (BNK1UAC, INTRTI-COMP-1 < 0) |
| T-177 | Account Update | Interest rate above maximum rejected on update screen | BR-BNK1UAC-22 | BNK1UAC | VD010 line 656 (BNK1UAC, INTRTI-COMP-1 > 9999.99) |
| T-178 | Account Update | Interest rate at maximum boundary 9999.99 accepted on update screen | BR-BNK1UAC-22 | BNK1UAC | VD010 line 656 (BNK1UAC, boundary at 9999.99) |
| T-179 | Account Update | Overdraft limit must be numeric for update | BR-BNK1UAC-24 | BNK1UAC | VD010 lines 679-684 (BNK1UAC, OVERDRI NOT NUMERIC) |
| T-180 | Debit / Credit Funds | Account number zero rejected on debit/credit screen | BR-BNK1CRA-11 | BNK1CRA | ED010 lines 457-462 (BNK1CRA, ACCNOI = ZERO) |
| T-181 | Debit / Credit Funds | Invalid sign character rejected | BR-BNK1CRA-12 | BNK1CRA | ED010 lines 464-469 (BNK1CRA, SIGNI NOT = '+' AND SIGNI NOT = '-' AND SIGNL = 1) |
| T-182 | Debit / Credit Funds | Empty sign field silently treated as credit | BR-BNK1CRA-12a | BNK1CRA | ED010 line 464 (SIGNL = 1 condition false for empty field); UCD010 lines 494-496 (negation skipped) |
| T-183 | Debit / Credit Funds | Zero amount rejected on debit/credit screen | BR-BNK1CRA-20 | BNK1CRA | VA010 lines 1136-1145 (BNK1CRA, WS-AMOUNT-AS-FLOAT = ZERO) |
| T-184 | Account Deletion | Datastore error returns fail code 2 with specific message | BR-BNK1DAC-27 | BNK1DAC | DAD010 lines 745-755 (BNK1DAC: PARMS-SUBPGM-DEL-FAIL-CD = '2', message 'Sorry, but a datastore error occurred.') |
| T-185 | Account Deletion | Delete operation error returns fail code 3 with specific message | BR-BNK1DAC-28 | BNK1DAC | DAD010 lines 757-767 (BNK1DAC: PARMS-SUBPGM-DEL-FAIL-CD = '3', message 'Sorry, but a delete error occurred.') |
| T-186 | Account Deletion | Account number field blank on display screen | BR-BNK1DAC-11 | BNK1DAC | ED010 lines 503-509 (BNK1DAC: ACCNOI = LOW-VALUES OR ACCNOL = 0) |
| T-187 | Fund Transfer | Transfer amount zero after NUMVAL conversion rejected | BR-BNK1TFN-22 | BNK1TFN | VA010 line 1193 (BNK1TFN: WS-AMOUNT-AS-FLOAT = ZERO after NUMVAL) |
| CC-1 | Cross-capability | Create customer then immediately enquire | BR-CRECUST-43, BR-INQCUST-25 | CRECUST, INQCUST | WCV010 (CRECUST customer write), P010 lines 220-238 (INQCUST output fields) |
| CC-2 | Cross-capability | Create account for newly created customer | BR-CREACC-1, BR-CREACC-5 | CREACC, INQCUST | P010 line 314 (customer existence check), ATC010 line 1215, WAD010 (CREACC account write) |
| CC-3 | Cross-capability | Create 10 accounts then attempt 11th | BR-CREACC-4 | CREACC, INQACCCU | P010 line 347 (account count check), FD010 lines 463-464 (INQACCCU ODO limit) |
| CC-4 | Cross-capability | Debit then verify balance via enquiry | BR-DBCRFUN-16, BR-INQACC-4 | DBCRFUN, INQACC | UAD010 lines 384-386 (balance update), FD010 lines 534-572 (INQACC balance read) |
| CC-5 | Cross-capability | Transfer then verify both balances | BR-XFRFUN-3, BR-INQACC-4 | XFRFUN, INQACC | UADF010 lines 986-989, UADT010 lines 1357-1359, RAD010 (INQACC read) |
| CC-6 | Cross-capability | Delete customer then confirm all gone | BR-DELCUS-1, BR-INQCUST-11 | DELCUS, INQCUST, INQACCCU | DCV010 lines 384-389 (DELCUS VSAM delete), RCV010 lines 339-351 (INQCUST not-found path) |
| CC-7 | Cross-capability | Transfer creates PROCTRAN audit | BR-XFRFUN-23 through BR-XFRFUN-27 | XFRFUN | WTPD010 lines 1581-1646 |
| CC-8 | Cross-capability | Full customer lifecycle | BR-CRECUST-43, BR-UPDCUST-18, BR-INQCUST-25, BR-DELCUS-24 | CRECUST, UPDCUST, INQCUST, DELCUS | WCV010 (CRECUST write), UCV010 lines 262-285 (UPDCUST REWRITE), P010 lines 220-238 (INQCUST output), DCV010 lines 384-389 (DELCUS delete) |
| CC-9 | Cross-capability | Reverse-order fund transfer verifies both balances | BR-XFRFUN-4, BR-XFRFUN-36, BR-INQACC-4 | XFRFUN, INQACC | UAD010 line 589 (reverse path), UADT010 line 1044 (COMM-SUCCESS reset), RAD010 (INQACC read) |
| CC-10 | Cross-capability | Create customer with uppercase title then enquire | BR-BNK1CCS-16, BR-CRECUST-43, BR-INQCUST-3 | BNK1CCS, CRECUST, INQCUST | ED010 lines 607-620 (BNK1CCS normalisation), WCV010 (CRECUST write), P010 lines 220-238 (INQCUST output) |
| CC-11 | Cross-capability | Account enquiry then delete without re-enquiring | BR-BNK1DAC-13, BR-BNK1DAC-14, BR-DELACC-2 | BNK1DAC, DELACC | VD010 lines 530-538 (BNK1DAC pre-delete validation), RAD010 (DELACC SELECT) |
| CC-12 | Cross-capability | Customer with 15 accounts: all retrieved, only 10 displayed | BR-BNK1CCA-19, BR-INQACCCU-5 | BNK1CCA, INQACCCU | GCD010 line 552 (BNK1CCA, UNTIL WS-INDEX > 10), FD010 lines 583-631 (INQACCCU cursor fetch) |

---

## Coverage Summary

| Capability | Total Tests | Happy Path | Error | Boundary | Confidence |
| ---------- | ----------- | ---------- | ----- | -------- | ---------- |
| Navigation and Session Management | 16 | 13 | 2 | 1 | high |
| Customer Enquiry | 8 | 3 | 3 | 2 | high |
| Customer Creation with Credit Scoring | 28 | 9 | 14 | 5 | high |
| Account Enquiry | 7 | 3 | 2 | 2 | high |
| Accounts Enquiry by Customer | 7 | 3 | 2 | 2 | high |
| Account Creation | 19 | 10 | 5 | 4 | high |
| Account Update | 18 | 5 | 7 | 6 | high |
| Account Deletion | 9 | 3 | 5 | 1 | high |
| Customer Update | 12 | 7 | 5 | 0 | high |
| Customer Deletion (Full Cascade) | 6 | 4 | 1 | 1 | high |
| Debit / Credit Funds | 19 | 8 | 10 | 1 | high |
| Fund Transfer | 17 | 5 | 11 | 1 | high |
| Centralised Abend Logging | 4 | 2 | 1 | 1 | high |
| Utility Services | 4 | 3 | 0 | 1 | high |
| Test Data Initialisation | 11 | 8 | 2 | 1 | medium |
| Cross-capability End-to-End | 11 | 11 | 0 | 0 | high |
| **Total** | **196** | **97** | **70** | **29** | **high** |
## Untested Rules

Business rules from the analysis artifacts that are not covered by any test scenario. These represent gaps requiring SME review or additional test design:

| Rule ID | Program | Rule Description | Reason Untested | Priority |
| ------- | ------- | ---------------- | --------------- | -------- |
| BR-CRECUST-33 | CRECUST | SYSIDERR retry exhaustion on CUSTOMER control record read falls through silently, potentially causing corruption | Defect: cannot be tested in black-box mode without infrastructure fault injection; requires chaos/fault-injection testing with SYSIDERR forced on all 100 retries | High |
| BR-CRECUST-42 | CRECUST | Control record READ/REWRITE post-WRITE has no error check; silent failure | Defect path: control record update failure is silently ignored; cannot distinguish from success in black-box test | High |
| BR-CRECUST-36 | CRECUST | NCS counter is not decremented on failure (customer number permanently consumed on failed creation) | Gap: requires observing counter value before/after a failed creation attempt; test would need access to counter state | Medium |
| BR-INQCUST-19 | INQCUST | ENDBR non-NORMAL, non-SYSIDERR initial response causes scope defect: failure check is skipped, success returned incorrectly | Defect: requires infrastructure fault injection to force ENDBR failure; difficult in black-box context | Medium |
| BR-INQCUST-Defect-5 | INQCUST | All-nines NOTFND retry uses stale NCS-CUST-NO-VALUE making retry redundant | Defect: behavioural anomaly only observable by instrumenting the random number used in the retry; no external observable difference | Low |
| BR-CREACC-40 | CREACC | CD010 next-statement date logic is not truly month-aware for 30-day months | Boundary: only manifests on the 30th or 31st of certain months; end-of-month date arithmetic; marked as business limitation | Medium |
| BR-CREACC-38 | CREACC | IMS PCB pointer set to NULL in CICS-only program | Dead code: no functional impact; not testable as a behaviour | Low |
| BR-UPDACC-note-1 | UPDACC | Negative interest rate would be silently sign-stripped on write | Edge case: no input validation prevents negative rate if caller bypasses presentation layer; requires API-level test | Medium |
| BR-UPDACC-note-2 | UPDACC | Zero values for interest rate and overdraft limit are written without validation | Design limitation: documented in source; would require negative-value business rule to be testable | Low |
| BR-BNK1UAC-defect-1 | BNK1UAC | Next statement date missing day/month range check (day=0 or month=0 passes validation) | Defect: the missing range check for NSTMTDDI/NSTMTMMI means an invalid date with day=0 or month=0 can be submitted; documented as a known defect; any black-box test sending day=0 or month=0 for NEXT statement date would expect acceptance (defect preserved) rather than rejection | Medium |
| BR-BNK1UAC-defect-2 | BNK1UAC | Interest rate decimal-places check allows 3 significant decimal digits instead of the intended 2 | Defect: off-by-one in the two-pass INSPECT at VD010 lines 593-641; a rate like '1.234' passes validation; only testable by sending a 3-decimal rate and observing absence of rejection | Medium |
| BR-BNK1UAC-defect-3 | BNK1UAC | Silent success on UPDACC non-response (COMM-SUCCESS pre-cleared to space, not 'N'; space treated as success) | Defect: only observable when UPDACC fails to populate COMM-SUCCESS; requires fault injection at UPDACC level | Low |
| BR-DBCRFUN-20 | DBCRFUN | Updated in-memory balances returned to caller even on UPDATE failure (COMM-AV-BAL/COMM-ACT-BAL set before SQLCODE check) | Defect: DB2 UPDATE failure is needed to observe incorrect balances in response while COMM-SUCCESS='N'; requires DB2 fault injection | Medium |
| BR-XFRFUN-18 | XFRFUN | Unexpected TO account failure code in forward-order path (ABCODE 'TO  ') does not call ABNDPROC before abend | Defect: asymmetric ABNDPROC coverage; observable only when an internal DB2 error code other than +100 or -911 occurs on TO account; requires fault injection | Low |
| BR-XFRFUN-Defect-1 | XFRFUN | Exhausted deadlock retries on TO account UPDATE display "TIMEOUT DETECTED" but test the deadlock SQLERRD code | Defect: diagnostic text inaccuracy only; no observable functional difference from caller perspective | Low |
| BR-XFRFUN-37 | XFRFUN | Storm drain check in UADT010 fires before SQLCODE discrimination (including for SQLCODE +100 not-found) | Implementation detail: CHECK-FOR-STORM-DRAIN-DB2 called unconditionally before routing decisions; only triggers display for SQLCODE=923 so no external observable difference for normal not-found path | Low |
| BR-BNK1TFN-25 | BNK1TFN | Transfer fail-code '3' (unexpected XFRFUN error) falls through to indeterminate-success message | Defect: GCD010 lines 603-608 lack a GO TO GCD999 after setting fail-code 3 message, causing the subsequent SUBPGM-SUCCESS check at line 629 to overwrite the message with 'unable to determine success'; the intended 'unexpected error' message is never displayed; requires XFRFUN to be faulted to return fail-code '3' | Medium |
| BR-DELCUS-7 | DELCUS | DELACC return code is not inspected by DELCUS; account-deletion failures are silently delegated to DELACC ABENDs | Design: testable only via DELACC-level fault injection; from DELCUS caller perspective, all errors manifest as ABENDs not soft failures | Medium |
| BR-DELCUS-8 | DELCUS | APPLID passed to DELACC is always spaces/low-values because WS-APPLID is never populated by EXEC CICS ASSIGN in DELCUS | Defect: pervasive in DELCUS; DELACC-COMM-APPLID will always be spaces in cascade deletes; DELACC itself uses EXEC CICS ASSIGN for its own abend records so this does not affect abend logging in DELACC; no observable difference in black-box test output | Low |
| BR-DELCUS-9 | DELCUS | IMS PCB pointer threaded from DELACC commarea into INQACCCU commarea before LINK | Dead code for CICS-only deployments: PCB pointer is undefined unless IMS environment; no observable difference in CICS-only test | Low |
| BR-DBCRFUN-31 | DBCRFUN | SYNCPOINT ROLLBACK failure after failed PROCTRAN INSERT triggers ABEND HROL | Defect path: requires CICS SYNCPOINT ROLLBACK itself to fail (RESP ≠ NORMAL) after a PROCTRAN INSERT failure; cannot be triggered in black-box mode without infrastructure fault injection forcing ROLLBACK failure; T-113 covers the ROLLBACK being issued (BR-DBCRFUN-30) but not its failure | High |
| BR-DELCUS-11 | DELCUS | SYSIDERR on CUSTOMER VSAM READ retried up to 100 times with 3-second delay; exhaustion leads to ABEND WPV6 | Requires infrastructure fault injection to force SYSIDERR on CUSTOMER file READ for all 100 attempts; not testable in black-box mode without CICS file-level fault injection | Medium |
| BR-DELCUS-18 | DELCUS | SYSIDERR on CUSTOMER VSAM DELETE retried up to 100 times with 3-second delay; any non-NORMAL response after retries causes ABEND WPV7 | Requires infrastructure fault injection to force SYSIDERR on CUSTOMER file DELETE for all 100 attempts; not testable in black-box mode without CICS file-level fault injection | Medium |
| BR-BANKDATA-34 | BANKDATA | VSAM customer control sentinel NUMBER-OF-CUSTOMERS and LAST-CUSTOMER-NUMBER fields are zero -- customer count tallied in memory but never persisted | Covered by T-147 (sentinel has zero values) and data contract test CUSTOMER-15; no additional scenario needed | Low |
| BR-BANKDATA-35 | BANKDATA | NUMBER-OF-CUSTOMERS tallied in WORKING-STORAGE but no DB2 CONTROL row is inserted for customer count (only account counters written) | Covered by T-147 and data contract test CONTROL-6; no additional scenario needed | Low |
| BR-BANKDATA-rates | BANKDATA | Fixed interest rates per account type hardcoded (ISA=2.10%, SAVING=1.75%, CURRENT=0.00%, LOAN=17.90%, MORTGAGE=5.25%) | Covered by T-142 (ISA and CURRENT rates verified); full rate table covered by contract test; remaining types follow same pattern | Low |
| BR-BANKDATA-dates | BANKDATA | Statement dates hardcoded to 01.07.2021 / 01.08.2021 | Covered by T-143; no additional scenario needed | Low |
| BR-ABNDPROC-5 | ABNDPROC | KEY-LENGTH constant WS-ABND-KEY-LEN defined in WORKING-STORAGE but never referenced in the EXEC CICS WRITE | Dead code: no functional impact; CICS uses file definition for key length; not observable as a behaviour difference | Low |
| BR-BNK1CCS-37 | BNK1CCS | No year range validation in BNK1CCS presentation layer for DOB year (DOBYYI-NUM dead code) | Defect note: year range validation is performed by CRECUST back-end (rules BR-CRECUST-3/5) but the BNK1CCS-level year check data items are dead code; any numeric 4-digit year passes through the presentation layer to CRECUST which then rejects it; functionally covered by T-029, T-030, T-032 at the back-end level | Low |
| BR-BNK1CCS-5-DEFECT | BNK1CCS | CLEAR key uses incorrect MAP parameter ('BNK1CCM' instead of 'BNK1CC') with no error check; latent defect | Defect: CLEAR key path calls EXEC CICS SEND MAP with wrong map name; CICS may reject the send silently; only manifests if a user presses CLEAR during an active session and the wrong map name causes a MAPIDERR; not testable in pure black-box mode without observing CICS map resolution | Low |
| BR-BNK1CCS-COMMAREA | BNK1CCS | EXEC CICS RETURN specifies LENGTH(248) but commarea is only 5 bytes; inconsistency | Implementation anomaly: CICS passes the LENGTH parameter to allocate storage for the next invocation; the excess bytes may contain garbage but do not affect program logic since only WS-COMM-TERM (first byte) is used; no black-box observable difference | Low |
| BR-BNK1CCA-17-defect | BNK1CCA | INQACCCU error path with non-zero account count still populates screen account rows; contradictory display (error message + account data both shown) | Defect: the account-populate loop executes as a sibling (not child) of the COMM-SUCCESS='N' branch; triggering this requires INQACCCU to return COMM-SUCCESS='N' with a non-zero account count; requires fault injection at INQACCCU level | Low |
| BR-BNK1DAC-32-defect | BNK1DAC | DATAONLY send mode overwrites any non-blank MESSAGEO with 'Account lookup successful.' (inverted condition) | Defect: the test at SM010 lines 901-905 fires when MESSAGEO is NOT spaces/LOW-VALUES; this means any error message from ED010 or GAD010 gets silently replaced by the generic success text on the next DATAONLY send; observable if account enquiry returns error but message field is repainted by a subsequent send | Medium |
| BR-BNK1DAC-int-rate-defect | BNK1DAC | DFHCOMMAREA defines COMM-INT-RATE as PIC 9(6) but WS-COMM-AREA defines it as PIC 9(4)V99; interest rate misinterpreted on re-entry | Defect: structural incompatibility between commarea layouts; on each pseudo-conversational re-entry the interest rate from the prior display is reinterpreted without the implied decimal point; creates a 100x magnitude error for any non-zero interest rate carried across turns | Medium |
| ABND-TIME-defect | All programs | ABND-TIME seconds field always contains minutes value (HH:MM:MM instead of HH:MM:SS) | Pervasive source code defect across BNKMENU, CRECUST, CREACC, DELACC, DELCUS, INQACC, INQCUST, DBCRFUN, XFRFUN, BNK1UAC, BNK1CRA, BNK1CCA, BNK1DAC; affects abend diagnostic records only; covered by ABNDFILE contract test #6 as a known defect invariant; no functional business logic impact; document as known defect for modernisation team | Low |
