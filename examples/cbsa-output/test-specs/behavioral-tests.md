---
type: test-specifications
subtype: behavioral-tests
status: draft
confidence: high
last_pass: 5
---

# Behavioral Test Specifications

Stack-agnostic test scenarios derived from business rules and functional capabilities. Tests describe WHAT the system does, not HOW -- any target implementation that passes these tests preserves the legacy system's behavior.

## Test Design Principles

| Principle | Description |
| --------- | ----------- |
| Black-box behavioral coverage | Every scenario is expressed as inputs + expected outputs only; no COBOL paragraph names appear in scenario descriptions |
| Capability-first organization | Tests are grouped by business capability (from capabilities.md), never by program or transaction ID |
| Equivalence class coverage | For each field with a PIC clause, valid and invalid equivalence classes are identified; at least one boundary scenario is derived per capability |
| Rule completeness | Every business rule with an explicit condition/action pair generates at least one happy-path and one error scenario |
| Atomicity and audit | Scenarios that mutate data verify both the mutation result and the corresponding audit record (PROCTRAN row or ABNDFILE entry) |

---

## Navigation and Session Management

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Navigation and Session Management |
| Source Rules | BR-BNKMENU-1 through BR-BNKMENU-23 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | First-time menu display | happy-path | No prior session state (COMMAREA is empty / zero length) | User connects to banking menu transaction | Menu is displayed with all fields cleared and cursor positioned on the selection field; no error message shown | no | BR-BNKMENU-1 |
| 2  | Select option 1 (Display Customer) | happy-path | Menu is displayed | User enters '1' in selection field | System transfers to the Display Customer transaction | no | BR-BNKMENU-9 |
| 3  | Select option 2 (Display Account) | happy-path | Menu is displayed | User enters '2' in selection field | System transfers to the Display Account transaction | no | BR-BNKMENU-10 |
| 4  | Select option 3 (Create Customer) | happy-path | Menu is displayed | User enters '3' in selection field | System transfers to the Create Customer transaction | no | BR-BNKMENU-11 |
| 5  | Select option 4 (Create Account) | happy-path | Menu is displayed | User enters '4' in selection field | System transfers to the Create Account transaction | no | BR-BNKMENU-12 |
| 6  | Select option 5 (Update Account) | happy-path | Menu is displayed | User enters '5' in selection field | System transfers to the Update Account transaction | no | BR-BNKMENU-13 |
| 7  | Select option 6 (Credit/Debit) | happy-path | Menu is displayed | User enters '6' in selection field | System transfers to the Credit/Debit transaction | no | BR-BNKMENU-14 |
| 8  | Select option 7 (Fund Transfer) | happy-path | Menu is displayed | User enters '7' in selection field | System transfers to the Fund Transfer transaction | no | BR-BNKMENU-15 |
| 9  | Select option A (Accounts by Customer) | happy-path | Menu is displayed | User enters 'A' in selection field | System transfers to the Accounts by Customer transaction | no | BR-BNKMENU-16 |
| 10 | Invalid selection value | error | Menu is displayed | User enters 'X' (unrecognised letter) | Error message displayed; alarm activated; menu remains on screen | no | BR-BNKMENU-7 |
| 11 | Session termination via PF3 | happy-path | Menu is displayed | User presses PF3 | 'Session Ended' message displayed; session terminates; no return to menu | no | BR-BNKMENU-3 |
| 12 | Session termination via PF12 | happy-path | Menu is displayed | User presses PF12 | 'Session Ended' message displayed; session terminates | no | BR-BNKMENU-3 |
| 13 | Clear key clears screen and ends session | happy-path | Menu is displayed | User presses CLEAR | Screen clears and session ends without a 'Session Ended' message | no | BR-BNKMENU-4 |
| 14 | PA key is a no-op | happy-path | Menu is displayed | User presses PA1, PA2, or PA3 | No navigation occurs; menu transaction simply continues (re-enters with same COMMAREA) | no | BR-BNKMENU-2 |
| 15 | Any unrecognised function key shows error | error | Menu is displayed | User presses PF1 (or any PF key not PF3/PF12) | 'Invalid key pressed.' error message shown; menu redisplayed | no | BR-BNKMENU-6 |
| 16 | Empty selection field (boundary) | boundary | Menu is displayed | User presses ENTER with no selection typed | Error message or menu redisplay (empty input does not route to any capability) | yes | BR-BNKMENU-7 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| Selection field (PIC X(1)) | Menu option | '1'-'7' and 'A' | Valid: 9 specific values ('1','2','3','4','5','6','7','A'); Invalid: any other single character including space | space (boundary-empty), '8' (outside range), 'a' (lower-case) |
| EIBCALEN | Session state indicator | 0 (first call) or 1 (returning call) | First time: 0 -- display blank menu; Returning: non-zero -- receive input | 0 (first entry), 1 (minimum returning value) |

---

## Customer Enquiry

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Customer Enquiry |
| Source Rules | BR-INQCUST-1 through BR-INQCUST-25 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Retrieve known customer by number | happy-path | Customer exists | Specific customer number | All customer fields returned (name, address, DOB, credit score, review date); success indicator positive | no | BR-INQCUST-3, BR-INQCUST-5, BR-INQCUST-25 |
| 2  | Customer number not found | error | No customer record exists for the requested number | Valid-format customer number with no matching record | Success indicator negative; fail code '1'; name and address fields blanked | no | BR-INQCUST-11 |
| 3  | Retrieve last (highest-numbered) customer | happy-path | At least one customer exists | Special sentinel value 9999999999 | Customer record with the highest customer number in the system returned; success indicator positive | no | BR-INQCUST-2 |
| 4  | Retrieve random customer | happy-path | At least one customer exists | Special sentinel value 0000000000 | A valid customer record is returned; success indicator positive | no | BR-INQCUST-1, BR-INQCUST-7 |
| 5  | Random customer lookup exhausts retry limit | error | Customer store is sparse (many gaps in key range) | 0000000000 with all 1000 random-pick attempts failing | Success indicator negative; fail code '1' | no | BR-INQCUST-8 |
| 6  | All-nines sentinel with no customers causes abend | error | Customer store is completely empty | 9999999999 and empty VSAM file | Unrecoverable error (abend CVR1) on second failed lookup attempt | no | BR-INQCUST-10 |
| 7  | Minimum customer number boundary | boundary | Customer with number 1 exists | Customer number 0000000001 | Customer record returned with correct data | yes | BR-INQCUST-3 |
| 8  | Maximum valid customer number boundary | boundary | Customer with number 9999999998 exists | Customer number 9999999998 | Customer record returned with correct data | yes | BR-INQCUST-3 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| Customer Number (PIC 9(10)) | Customer identifier | 0000000001 to 9999999998 | Existing customer: success; Non-existent: fail code '1'; Sentinel 0 (random): random pick; Sentinel 9999999999 (last): VSAM browse | 0 (random sentinel), 1 (minimum real customer), 9999999998 (maximum real customer), 9999999999 (last-customer sentinel / control record) |

---

## Customer Creation with Credit Scoring

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Customer Creation with Credit Scoring |
| Source Rules | BR-CRECUST-1 through BR-CRECUST-48, BR-BNK1CCS-13 through BR-BNK1CCS-52 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Create customer with valid title and DOB | happy-path | System available; customer VSAM and PROCTRAN accessible | Customer name starting with 'Mr', address, valid DOB (e.g., 15/06/1985) | Customer created; assigned customer number returned; credit score between 1-999; credit score review date is 1-20 days from today; audit record type 'OCC' written | no | BR-CRECUST-1, BR-CRECUST-8, BR-CRECUST-29, BR-CRECUST-43, BR-CRECUST-44 |
| 2  | Invalid customer title rejected | error | None | Name starting with 'Rev' (not in allowed list), valid DOB | Request rejected; fail code 'T'; no customer record written | no | BR-CRECUST-1, BR-BNK1CCS-15 |
| 3  | Blank title is accepted | happy-path | None | Name with no title prefix (blank), valid DOB | Customer created successfully | no | BR-CRECUST-2 |
| 4  | All valid titles accepted | happy-path | None | Name starting with each of: Professor, Mr, Mrs, Miss, Ms, Dr, Drs, Lord, Sir, Lady | Customer created successfully for each title | no | BR-CRECUST-1, BR-BNK1CCS-15 |
| 5  | Date of birth in the future rejected | error | None | Valid name, DOB set to tomorrow's date | Request rejected; fail code 'Y' | no | BR-CRECUST-6, BR-BNK1CCS-47 |
| 6  | Date of birth year before 1601 rejected | error | None | Valid name, DOB year 1600 | Request rejected; fail code 'O' | no | BR-CRECUST-3, BR-BNK1CCS-46 |
| 7  | Date of birth year exactly 1601 accepted | boundary | None | Valid name, DOB year 1601 (e.g., 01/01/1601) | Customer created successfully (year 1601 is the minimum accepted birth year) | yes | BR-CRECUST-3 |
| 8  | Customer age exceeds 150 years rejected | error | None | Valid name, DOB year 150+ years ago (e.g., 1874) | Request rejected; fail code 'O' | no | BR-CRECUST-5, BR-BNK1CCS-46 |
| 9  | Customer age exactly 150 years accepted | boundary | None | Valid name, DOB exactly 150 years ago | Customer created successfully | yes | BR-CRECUST-5 |
| 10 | Invalid date of birth (non-existent day) rejected | error | None | Valid name, DOB 30/02/1990 (February 30th) | Request rejected; fail code 'Z' | no | BR-CRECUST-4, BR-BNK1CCS-48 |
| 11 | Leap year DOB is valid | boundary | None | Valid name, DOB 29/02/2000 (valid leap year) | Customer created successfully | yes | BR-CRECUST-4 |
| 12 | Credit score is integer average of agency responses | happy-path | Credit agencies respond with scores | Any valid customer creation | Final credit score = floor(sum of received scores / number of responses); no rounding | no | BR-CRECUST-calc-1 |
| 13 | Credit score review date is 1-20 days in future | happy-path | Successful customer creation | Any valid creation | Review date is between today+1 and today+20 inclusive | no | BR-CRECUST-calc-3 |
| 14 | Credit check failure returns error | error | All credit agencies fail to respond | Valid customer data | Request rejected; fail code reflects credit check failure; no customer record written | no | BR-CRECUST-17, BR-CRECUST-19 |
| 15 | Customer number is sequential | happy-path | Prior customer exists with number N | Any valid customer creation | New customer receives number N+1 | no | BR-CRECUST-29 |
| 16 | Concurrent creation is serialised correctly | happy-path | Multiple concurrent creation requests | Two simultaneous creation requests | Each receives a distinct, sequential customer number; no duplicates | no | BR-CRECUST-26, BR-CRECUST-27 |
| 17 | Audit record written on success | happy-path | Customer created | Any successful creation | Audit record type 'OCC' written; account number field is all zeros (no account yet); customer number encoded in description | no | BR-CRECUST-44, BR-CRECUST-45, BR-CRECUST-46, BR-CRECUST-48 |
| 18 | First name is mandatory on creation screen | error | Create customer screen displayed | Blank or all-spaces first name field; valid title and DOB | Request rejected; error message 'Please supply a valid First Name'; no customer creation attempted | no | BR-BNK1CCS-26 |
| 19 | Surname is mandatory on creation screen | error | Create customer screen displayed | Blank or all-spaces surname field; valid title and first name and DOB | Request rejected; error message 'Please supply a valid Surname'; no customer creation attempted | no | BR-BNK1CCS-27 |
| 20 | Address line 1 is mandatory on creation screen | error | Create customer screen displayed | Blank address line 1; valid name and DOB | Request rejected; error message 'Please supply a valid Address Line 1'; no customer creation attempted | no | BR-BNK1CCS-28 |
| 21 | DOB day field must not be blank | error | Create customer screen displayed | Valid name and address; DOB day blank | Request rejected; error message requesting valid DOB day | no | BR-BNK1CCS-29 |
| 22 | Non-numeric DOB day rejected | error | Create customer screen displayed | Valid name and address; DOB day = 'AB' | Request rejected; error message 'Non numeric Date of Birth DD entered' | no | BR-BNK1CCS-32 |
| 23 | DOB day out of range (00 or 32) rejected | boundary | Create customer screen displayed | Valid name and address; DOB day = 00 or 32 | Request rejected; error message 'Please supply a valid Date of Birth (DD)' | yes | BR-BNK1CCS-35 |
| 24 | DOB month out of range (00 or 13) rejected | boundary | Create customer screen displayed | Valid name and address; DOB month = 00 or 13 | Request rejected; error message 'Please supply a valid Date of Birth (MM)' | yes | BR-BNK1CCS-36 |
| 25 | Title case-insensitive normalisation accepted | happy-path | Create customer screen displayed | Title entered in uppercase e.g. 'MR' or mixed case 'mR' | Request accepted; title normalised to canonical form 'Mr' before creation | no | BR-BNK1CCS-16 |
| 26 | Pre-filled customer number field causes rejection | error | Create customer screen re-used without clearing | Customer number field contains a previously created customer number | Request rejected; message 'Please clear screen before creating new user'; no creation attempted | no | BR-BNK1CCS-13 |
| 27 | DOB month field must not be blank | error | Create customer screen displayed | Valid name and address; DOB month blank | Request rejected; error message requesting valid DOB month | no | BR-BNK1CCS-30 |
| 28 | DOB year field must not be blank | error | Create customer screen displayed | Valid name and address; DOB year blank | Request rejected; error message requesting valid DOB year | no | BR-BNK1CCS-31 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| Customer Title (parsed from name PIC X(60)) | Honorific | Professor, Mr, Mrs, Miss, Ms, Dr, Drs, Lord, Sir, Lady, or blank | Valid: 11 values (any case variant normalised to canonical); Invalid: any other first word | Blank (no title), single valid title, 'Rev' (invalid) |
| Date of Birth (PIC 9(8) DDMMYYYY) | Date of birth | Year 1601 to today minus 0 (must not be future) | Valid: 1601-present; Invalid future: tomorrow+; Invalid too old: > 150 years; Invalid date: non-existent day | 01011601 (minimum year), 01012000 (valid recent), 29022000 (leap year), 30021990 (non-existent, rejected), tomorrow (future, rejected) |
| Customer Name (PIC X(60)) | Full name | Non-blank, valid title | Valid: title from allowed list + name; Invalid: title not in list | All spaces (60), single char |
| Customer Address (PIC X(160)) | Postal address | Any non-blank string | Non-blank: valid | All spaces (160) |
| DOB Day (PIC 99) | Day of birth | 01-31 | Valid: 01-31 numeric; Invalid: 0, >31, non-numeric, blank | 00 (rejected), 01 (minimum), 31 (maximum), 32 (rejected) |
| DOB Month (PIC 99) | Month of birth | 01-12 | Valid: 01-12 numeric; Invalid: 0, >12, non-numeric, blank | 00 (rejected), 01 (minimum), 12 (maximum), 13 (rejected) |

---

## Account Enquiry

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Account Enquiry |
| Source Rules | BR-INQACC-1 through BR-INQACC-15 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Retrieve known account by number | happy-path | Account exists | Specific account number | All 12 account fields returned; success indicator positive; dates in day/month/year format | no | BR-INQACC-4, BR-INQACC-12 |
| 2  | Account number not found | error | No account for the requested number | Non-existent account number | Success indicator negative | no | BR-INQACC-3, BR-INQACC-10 |
| 3  | Retrieve highest-numbered account (sentinel) | happy-path | At least one account exists | Sentinel value 99999999 | Account with the highest account number in the system returned; success indicator positive | no | BR-INQACC-1, BR-INQACC-13 |
| 4  | No accounts exist for sentinel lookup | error | Account table is empty | Sentinel value 99999999 | Success indicator negative | no | BR-INQACC-15 |
| 5  | Minimum valid account number | boundary | Account 00000001 exists | Account number 00000001 | Account data returned successfully | yes | BR-INQACC-2 |
| 6  | Maximum valid account number | boundary | Account 99999998 exists | Account number 99999998 | Account data returned successfully | yes | BR-INQACC-2 |
| 7  | Date fields returned in day/month/year format | happy-path | Account with known dates exists | Account number | Opened date, last statement date, and next statement date each returned as separate day, month, year components in DD/MM/YYYY order | no | BR-INQACC-12 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| Account Number (PIC 9(8)) | Account to retrieve | 00000001 to 99999998 | Existing account: all fields returned; Non-existent: fail; Sentinel 99999999: last-account lookup | 00000001 (minimum), 99999998 (maximum real), 99999999 (last-account sentinel) |

---

## Accounts Enquiry by Customer

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Accounts Enquiry by Customer |
| Source Rules | BR-INQACCCU-1 through BR-INQACCCU-10, BR-BNK1CCA-9 through BR-BNK1CCA-23 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Retrieve all accounts for existing customer | happy-path | Customer with 3 accounts exists | Customer number | 3 account records returned; account count = 3; success indicator positive; customer-found indicator positive | no | BR-INQACCCU-3, BR-INQACCCU-7, BR-INQACCCU-10 |
| 2  | Customer with no accounts | happy-path | Customer exists but has no accounts | Customer number | Account count = 0; success indicator positive (customer found); no account data returned | no | BR-INQACCCU-9 |
| 3  | Customer number not found | error | No customer for the requested number | Non-existent customer number | Customer-found indicator negative; account count = 0; success indicator negative | no | BR-INQACCCU-3, BR-INQACCCU-4 |
| 4  | Customer number zero rejected | boundary | None | Customer number 0000000000 | Customer-found indicator negative; account count = 0; request does not attempt any lookup | yes | BR-INQACCCU-1 |
| 5  | Customer with 20 accounts (system maximum) | boundary | Customer with exactly 20 accounts | Customer number | 20 account records returned; account count = 20 | yes | BR-INQACCCU-5 |
| 6  | Screen display limited to 10 rows for customers with 11-20 accounts | happy-path | Customer with 15 accounts exists | Customer number | Backend returns all 15 accounts; presentation layer displays only the first 10; message shows the actual account count (15) | no | BR-BNK1CCA-19 |
| 7  | Non-numeric customer number rejected on enquiry screen | error | None | Customer number field containing alphabetic characters | Request rejected with message 'Please enter a customer number.'; no backend lookup performed | no | BR-BNK1CCA-9 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| Customer Number (PIC 9(10)) | Customer to look up | 0000000001 to 9999999998 | Existing with accounts; Existing without accounts; Non-existent; Zero (special reject) | 0 (rejected), 1 (minimum), 9999999999 (control record sentinel -- rejected by rule 2) |
| Accounts returned (ODO 1 TO 20) | Account count per customer | 0 to 20 | Zero accounts (customer exists, empty); 1-19 accounts (normal); 20 accounts (system max) | 0, 1, 20 |
| Screen display rows | Visible account rows | 0 to 10 | Screen shows at most 10 rows regardless of backend count | 0, 10 (display maximum), 11+ (truncated to 10 on screen) |

---

## Account Creation

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Account Creation |
| Source Rules | BR-CREACC-1 through BR-CREACC-39, BR-BNK1CAC-11 through BR-BNK1CAC-43 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Create ISA account for existing customer | happy-path | Customer exists; customer has fewer than 10 accounts | Customer number, account type 'ISA', interest rate, overdraft limit | Account created; new account number returned; opened date = today; next statement date = today + 30 days; audit record type 'OCA' written with amount zero | no | BR-CREACC-1, BR-CREACC-5, BR-CREACC-21, BR-CREACC-26, BR-CREACC-31, BR-CREACC-32 |
| 2  | Create MORTGAGE account | happy-path | Customer exists with fewer than 10 accounts | Account type 'MORTGAGE' | Account created successfully with 'ACCT' eye-catcher | no | BR-CREACC-5, BR-CREACC-21 |
| 3  | Create SAVING account | happy-path | Customer exists with fewer than 10 accounts | Account type 'SAVING' | Account created successfully | no | BR-CREACC-5 |
| 4  | Create CURRENT account | happy-path | Customer exists with fewer than 10 accounts | Account type 'CURRENT' | Account created successfully | no | BR-CREACC-5 |
| 5  | Create LOAN account | happy-path | Customer exists with fewer than 10 accounts | Account type 'LOAN' | Account created successfully | no | BR-CREACC-5 |
| 6  | Non-existent customer rejected | error | Customer does not exist | Non-existent customer number, valid account type | Request rejected; fail code '1' | no | BR-CREACC-1, BR-BNK1CAC-31 |
| 7  | Invalid account type rejected | error | Customer exists | Customer number, account type 'BONDS' (not in allowed list) | Request rejected; fail code 'A' | no | BR-CREACC-5, BR-CREACC-6, BR-BNK1CAC-40 |
| 8  | Blank account type rejected | error | Customer exists | Customer number, blank account type | Request rejected with fail code 'A' | yes | BR-CREACC-5, BR-CREACC-6, BR-BNK1CAC-13 |
| 9  | Tenth account (at limit) creation succeeds | boundary | Customer exists with exactly 9 accounts | Customer number with 9 accounts, valid account type | Account number 10 created successfully | yes | BR-CREACC-4 |
| 10 | Eleventh account rejected (exceeds 10-account limit) | boundary | Customer exists with exactly 10 accounts | Customer number with 10 accounts, valid account type | Request rejected; fail code '8' | yes | BR-CREACC-4, BR-BNK1CAC-38 |
| 11 | Concurrent account number allocation is sequential and unique | happy-path | Two concurrent creation requests for same branch | Two simultaneous requests | Each receives a distinct, sequential account number | no | BR-CREACC-8, BR-CREACC-12, BR-CREACC-14 |
| 12 | Audit record amount is zero for account creation | happy-path | Account created | Any valid account creation | Audit record in transaction log has amount = 0 | no | BR-CREACC-32 |
| 13 | Next statement date is today plus 30 days | happy-path | Account created today | Any valid account creation | Next statement date in COMMAREA is today's date + 30 days | no | BR-CREACC-24 |
| 14 | Negative interest rate rejected on creation screen | error | Create account screen displayed | Customer number, valid account type, interest rate = -1.50 | Request rejected; error message 'Please supply a zero or positive interest rate'; no account created | no | BR-BNK1CAC-24 |
| 15 | Interest rate above maximum rejected | boundary | Create account screen displayed | Customer number, valid account type, interest rate = 10000.00 | Request rejected; error message indicating rate must be less than 9999.99 | yes | BR-BNK1CAC-25 |
| 16 | Interest rate with multiple decimal points rejected | error | Create account screen displayed | Customer number, valid account type, interest rate = '5..2' | Request rejected; error message 'Use one decimal point for interest rate only' | no | BR-BNK1CAC-22 |
| 17 | Overdraft limit defaults to zero when omitted | happy-path | Customer exists with fewer than 10 accounts | Customer number, valid account type, interest rate; overdraft limit field left blank | Account created successfully with overdraft limit = 0 | no | BR-BNK1CAC-27 |
| 18 | Lowercase account type accepted and normalised | happy-path | Customer exists with fewer than 10 accounts | Account type entered in lowercase 'isa' or 'current' | Account created successfully; stored with canonical uppercase value ('ISA     ' or 'CURRENT ') | no | BR-BNK1CAC-15, BR-BNK1CAC-16 |
| 19 | Interest rate at maximum boundary (9999.99) accepted | boundary | Customer exists with fewer than 10 accounts | Account type, interest rate = 9999.99 | Account created successfully | yes | BR-BNK1CAC-25 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| Account Type (PIC X(8)) | Account category | 'ISA', 'MORTGAGE', 'SAVING', 'CURRENT', 'LOAN' | Valid: 5 specific types (any case normalised); Invalid: any other string including blank | 'ISA' (3-char, shortest), 'MORTGAGE' (8-char, longest), blank |
| Account Count per Customer | Accounts held | 0 to 10 | Under limit: 0-9; At limit: 10 (succeeds for last); Over limit: > 10 (rejected) | 0, 9, 10 |
| Interest Rate (PIC 9(4)V99) | Annual interest rate | 0.00 to 9999.99 | Zero: valid (CURRENT); Positive: normal; Negative: rejected; > 9999.99: rejected | 0.00, 9999.99, -0.01 (rejected), 10000.00 (rejected) |
| Overdraft Limit (PIC 9(8)) | Overdraft allowance | 0 to 99999999 | Zero or blank: defaults to 0; Positive integer: valid | 0 (default), 1, 99999999 |

---

## Account Update

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Account Update |
| Source Rules | BR-UPDACC-1 through BR-UPDACC-6, BR-BNK1UAC-15 through BR-BNK1UAC-29 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Update account type, interest rate, and overdraft limit | happy-path | Account exists | Account number, new type 'SAVING', new interest rate, new overdraft limit | Account type, interest rate, and overdraft limit updated in the account store; balances unchanged; statement dates unchanged; success indicator positive | no | BR-UPDACC-3, BR-UPDACC-5 |
| 2  | Balances are never modified by account update | happy-path | Account with known balances | Account number, new type and rates | Available and actual balances remain unchanged after update | no | BR-UPDACC-3 |
| 3  | No audit record written for account update | happy-path | Account exists | Any valid account update | No new entry in the transaction audit log (PROCTRAN) for this operation | no | BR-UPDACC-3 |
| 4  | Account not found returns failure | error | Account does not exist | Non-existent account number | Success indicator negative; no update performed | no | BR-UPDACC-2 |
| 5  | Blank account type rejected | error | Account exists | Account number, blank account type | Update rejected; success indicator negative | yes | BR-UPDACC-1, BR-BNK1UAC-16 |
| 6  | Sort code is always the installation constant | happy-path | Account exists | Any account update request regardless of sort code supplied in input | Sort code silently overridden to 987654; update proceeds against the local bank's account record | no | BR-UPDACC-6 |
| 7  | Statement dates are never changed by account update | happy-path | Account with known statement dates | Any valid account update | Last statement date and next statement date remain unchanged | no | BR-UPDACC-3 |
| 8  | LOAN account with zero interest rate rejected on update screen | error | LOAN account exists; update screen displayed with valid account enquired | Account number; account type 'LOAN', interest rate '0000.00' | Update rejected; error message 'Interest rate cannot be 0 with this account type. Correct and press PF5.' | no | BR-BNK1UAC-23 |
| 9  | MORTGAGE account with zero interest rate rejected on update screen | error | MORTGAGE account exists; update screen displayed | Account number; account type 'MORTGAGE', interest rate '0000.00' | Update rejected; error message 'Interest rate cannot be 0 with this account type. Correct and press PF5.' | no | BR-BNK1UAC-23 |
| 10 | Last statement date with day 31 and month April rejected | boundary | Account exists; update screen displayed | Account number; last statement day = 31, month = 04 (April) | Update rejected; error message 'Incorrect date for LAST STATEMENT.' | yes | BR-BNK1UAC-28 |
| 11 | Last statement date with day 30 and month February rejected | boundary | Account exists; update screen displayed | Account number; last statement day = 30, month = 02 (February) | Update rejected; error message 'Incorrect date for LAST STATEMENT.' | yes | BR-BNK1UAC-28 |
| 12 | Last statement date with day 0 or month 0 rejected | boundary | Account exists; update screen displayed | Account number; last statement day = 00 or month = 00 | Update rejected; error message 'Incorrect date for LAST STATEMENT.' | yes | BR-BNK1UAC-27 |
| 13 | Next statement date with day 31 and month June rejected | boundary | Account exists; update screen displayed | Account number; next statement day = 31, month = 06 (June) | Update rejected; error message 'Incorrect date for NEXT STATEMENT.' | yes | BR-BNK1UAC-29 |
| 14 | Interest rate with non-numeric characters rejected | error | Account exists; update screen displayed | Account number; interest rate containing letters | Update rejected; error message 'Please supply a numeric interest rate' | no | BR-BNK1UAC-18 |
| 15 | Negative interest rate rejected on update screen | error | Account exists; update screen displayed | Account number; interest rate = -0.01 | Update rejected; error message 'Please supply a zero or positive interest rate' | yes | BR-BNK1UAC-21 |
| 16 | Interest rate above maximum rejected on update screen | boundary | Account exists; update screen displayed | Account number; interest rate = 10000.00 | Update rejected; error message 'Please supply an interest rate less than 9999.99%' | yes | BR-BNK1UAC-22 |
| 17 | Interest rate at maximum boundary 9999.99 accepted on update screen | boundary | Account exists; update screen displayed | Account number; interest rate = 9999.99 | Update accepted and stored | yes | BR-BNK1UAC-22 |
| 18 | Overdraft limit must be numeric for update | error | Account exists; update screen displayed | Account number; overdraft field containing letters | Update rejected; error message 'Overdraft must be numeric.' | no | BR-BNK1UAC-24 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| Account Type (PIC X(8)) | Account category | Non-blank string | Valid: non-blank from the 5 allowed types; Invalid: blank or spaces; Invalid on screen: any value not in allowed list | Single space, single non-space character |
| Interest Rate (PIC 9(4)V99) | Annual interest rate | 0.00 to 9999.99 (0.00 disallowed for LOAN/MORTGAGE) | Zero: valid for CURRENT/SAVING/ISA only; Positive: normal; Negative: rejected; > 9999.99: rejected; Zero with LOAN/MORTGAGE: rejected | 0.00 (context-dependent), -0.01 (rejected), 9999.99 (maximum), 10000.00 (rejected) |
| Last Statement Date (PIC 9(8)) | Last statement date | Valid calendar date | Valid day 1-31 per month, valid month 1-12; calendar-aware month-end check | Day 00 (rejected), month 00 (rejected), day 31 April (rejected), day 29+ February (rejected) |
| Next Statement Date (PIC 9(8)) | Next statement date | Valid calendar date | Same calendar checks; note: day=0 or month=0 passes validation (known defect in legacy) | Day 31 June (rejected), valid boundaries same as last statement date |

---

## Account Deletion

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Account Deletion |
| Source Rules | BR-DELACC-1 through BR-DELACC-19, BR-BNK1DAC-11 through BR-BNK1DAC-32 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Delete existing account | happy-path | Account exists with known balance | Account number | Account deleted from account store; success indicator positive; audit record type 'ODA' written with the account's actual balance at time of deletion | no | BR-DELACC-2, BR-DELACC-8, BR-DELACC-9, BR-DELACC-11, BR-DELACC-14, BR-DELACC-16 |
| 2  | Audit record captures actual balance at deletion | happy-path | Account with known non-zero balance | Account number | Audit record amount field equals the account's actual balance immediately before deletion | no | BR-DELACC-16 |
| 3  | Account not found returns fail code 1 | error | Account does not exist | Non-existent account number | Success indicator negative; fail code '1' returned; no audit record written; message 'Sorry, but that account number was not found. Account NOT deleted.' shown | no | BR-DELACC-3, BR-BNK1DAC-26 |
| 4  | Datastore error returns fail code 2 | error | Account store temporarily unavailable (simulated datastore error) | Valid account number when backend returns datastore error | Success indicator negative; fail code '2'; message 'Sorry, but a datastore error occurred. Account NOT deleted.' shown | no | BR-BNK1DAC-27 |
| 5  | Delete operation error returns fail code 3 | error | Account record exists but delete fails at the data layer | Valid account number | Success indicator negative; fail code '3'; message 'Sorry, but a delete error occurred. Account NOT deleted.' shown | no | BR-BNK1DAC-28 |
| 6  | Audit record transaction type is 'ODA' | happy-path | Account deleted | Any successful deletion | Audit record transaction type = 'ODA'; description includes customer number, account type, last/next statement dates | no | BR-DELACC-14, BR-DELACC-15 |
| 7  | Negative balance account deleted correctly | boundary | LOAN or MORTGAGE account with negative balance | Account number | Account deleted; audit record amount is negative (the actual balance) | yes | BR-DELACC-16 |
| 8  | Delete requires prior successful account enquiry on same screen session | error | User navigates directly to delete key (PF5) without first enquiring an account | PF5 pressed with no prior account enquiry (sort code and account number fields absent from session state) | Request rejected; error message 'Please enter an account number.'; no deletion performed | no | BR-BNK1DAC-13, BR-BNK1DAC-14 |
| 9  | Account number field blank on display screen | error | Display account screen shown | User submits ENTER with account number field empty | Request rejected; error message 'Please enter an account number.'; no backend lookup performed | yes | BR-BNK1DAC-11 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| Account Number (PIC 9(8)) | Account to delete | 00000001 to 99999998 | Existing: valid; Non-existent: fail code '1'; Blank/zero: rejected at screen | 00000001, 99999998, 00000000 (rejected) |
| Actual Balance at deletion (PIC S9(10)V99) | Balance in audit | Any signed decimal | Positive (savings/current); Negative (LOAN/MORTGAGE); Zero | -9999999999.99, 0.00, 9999999999.99 |
| Delete fail code | Failure reason | '1', '2', '3' | Account not found (1); Datastore error (2); Delete error (3); Any other failure (also shows delete error message) | All four branches |

---

## Customer Update

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Customer Update |
| Source Rules | BR-UPDCUST-1 through BR-UPDCUST-27, BR-BNK1DCS-19 through BR-BNK1DCS-23 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Update customer name and address | happy-path | Customer exists | Customer number, new name with valid title 'Mrs', new address | Name and address updated; date of birth, credit score, and review date are unchanged; success indicator positive | no | BR-UPDCUST-1, BR-UPDCUST-15, BR-UPDCUST-18, BR-UPDCUST-19, BR-UPDCUST-20, BR-UPDCUST-21 |
| 2  | Update name only (address supplied as blank) | happy-path | Customer exists | Customer number, new name, blank address | Name updated; address unchanged in stored record | no | BR-UPDCUST-17 |
| 3  | Update address only (name supplied as blank) | happy-path | Customer exists | Customer number, blank name, new address | Address updated; name unchanged in stored record | no | BR-UPDCUST-16 |
| 4  | Invalid title rejected | error | None | Customer number, name starting with 'Rev', valid address | Update rejected; fail code 'T'; no change to customer record | no | BR-UPDCUST-1, BR-UPDCUST-14, BR-BNK1DCS-19 |
| 5  | Both name and address blank rejected | error | Customer exists | Customer number, blank name, blank address | Update rejected; fail code '4' | no | BR-UPDCUST-15 |
| 6  | Customer not found returns failure | error | Customer does not exist | Non-existent customer number, valid name | Success indicator negative; fail code '1' | no | BR-UPDCUST-23 |
| 7  | Date of birth is read-only | happy-path | Customer exists | Customer number, valid name/address | DOB in stored record is unchanged after update | no | BR-UPDCUST-19 |
| 8  | Credit score is read-only | happy-path | Customer exists | Customer number, valid name/address | Credit score in stored record is unchanged after update | no | BR-UPDCUST-20 |
| 9  | All valid titles accepted (10 titles) | happy-path | Customer exists | Customer number, name with each valid title in turn | Each update succeeds | no | BR-UPDCUST-2 through BR-UPDCUST-11 |
| 10 | No audit record written for customer update | happy-path | Customer exists | Any valid customer update | No new entry in the transaction audit log for this operation | no | BR-UPDCUST-18 |
| 11 | Address all-spaces rejected in update | error | Customer exists | Customer number, valid name, address with all three lines blank | Update rejected; error message 'Address must not be all spaces - please reenter' | no | BR-BNK1DCS-21 |
| 12 | Customer number zero or all-nines rejected for update and delete | error | User attempts update or delete with customer number = 0 or 9999999999 | Customer number = 0000000000 or 9999999999 | Request rejected; message 'The customer number is not VALID.'; no update or deletion performed | no | BR-BNK1DCS-23 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| Customer Name (PIC X(60)) | Full name with title | Non-blank string with valid title | Valid: 10 specific titles + blank-title; Invalid title: any other first word; Blank: only valid if address supplied | Single space (60 chars), minimum 'Mr Name' |
| Customer Address (PIC X(160)) | Postal address | Non-blank; any characters | Supplied: update applies; Blank: address-only path; Both blank: rejected; All three lines blank: rejected | All spaces (160 chars), 1 non-space character |

---

## Customer Deletion (Full Cascade)

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Customer Deletion (Full Cascade) |
| Source Rules | BR-DELCUS-1 through BR-DELCUS-24 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Delete customer with multiple accounts | happy-path | Customer exists with 3 accounts | Customer number | All 3 account records deleted; individual 'ODA' audit records written per account (by account deletion service); single 'ODC' customer-level audit record written; customer record deleted; success indicator positive | no | BR-DELCUS-1, BR-DELCUS-4, BR-DELCUS-5, BR-DELCUS-17, BR-DELCUS-20, BR-DELCUS-22, BR-DELCUS-24 |
| 2  | Delete customer with no accounts | happy-path | Customer exists with zero accounts | Customer number | Customer record deleted; single 'ODC' audit record written; no account deletions attempted; success indicator positive | yes | BR-DELCUS-3, BR-DELCUS-24 |
| 3  | Non-existent customer returns failure | error | Customer does not exist | Non-existent customer number | Success indicator negative; no deletions performed | no | BR-DELCUS-1 |
| 4  | Delete customer with maximum 20 accounts | boundary | Customer exists with 20 accounts | Customer number | All 20 accounts deleted; 20 'ODA' audit records written; 1 'ODC' audit record written | yes | BR-DELCUS-5, BR-DELCUS-6 |
| 5  | Customer-deletion audit type is 'ODC' with zero amount | happy-path | Customer deleted | Any successful customer deletion | Customer-level audit record type = 'ODC'; audit amount = zero; account number field = zero | no | BR-DELCUS-22, BR-DELCUS-23, BR-DELCUS-21 |
| 6  | Concurrent deletion detected gracefully | happy-path | Another process has already deleted the same customer between retrieval and delete | Customer number from concurrent process | Operation completes without error (treats missing record as successful concurrent delete) | no | BR-DELCUS-12 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| Customer Number (PIC 9(10)) | Customer to delete | 0000000001 to 9999999998 | Existing with accounts; Existing no accounts; Non-existent | Customer with 0 accounts, customer with 1 account, customer with 20 accounts |
| Account cascade count | Accounts deleted per customer | 0 to 20 | Zero: skip account deletion phase; 1-19: normal cascade; 20: maximum cascade | 0, 1, 20 |

---

## Debit / Credit Funds

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Debit / Credit Funds |
| Source Rules | BR-DBCRFUN-1 through BR-DBCRFUN-39, BR-BNK1CRA-10 through BR-BNK1CRA-29 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Teller withdrawal from CURRENT account | happy-path | CURRENT account with available balance $500 | Account number, amount -$100 (debit), facility type = teller (non-496) | Available and actual balances both reduced by $100; transaction type 'DEB' audit record written; success indicator positive | no | BR-DBCRFUN-10, BR-DBCRFUN-16, BR-DBCRFUN-17, BR-DBCRFUN-21, BR-DBCRFUN-29 |
| 2  | Teller deposit to CURRENT account | happy-path | CURRENT account | Account number, amount +$200 (credit), facility type = teller | Both balances increased by $200; transaction type 'CRE' audit record written | no | BR-DBCRFUN-16, BR-DBCRFUN-17, BR-DBCRFUN-23, BR-DBCRFUN-29 |
| 3  | Payment-link debit to CURRENT account with sufficient funds | happy-path | CURRENT account with available balance $500 | Account number, amount -$100, facility type = 496 | Both balances reduced by $100; transaction type 'PDR' audit record written; success indicator positive | no | BR-DBCRFUN-9, BR-DBCRFUN-14, BR-DBCRFUN-22 |
| 4  | Payment-link credit to CURRENT account | happy-path | CURRENT account | Account number, amount +$300, facility type = 496 | Both balances increased by $300; transaction type 'PCR' audit record written | no | BR-DBCRFUN-14, BR-DBCRFUN-24, BR-DBCRFUN-29 |
| 5  | Payment-link debit rejected when insufficient funds | error | CURRENT account with available balance $50 | Account number, amount -$100 (debit), facility type = 496 | Request rejected; fail code '3'; balances unchanged | no | BR-DBCRFUN-9 |
| 6  | Payment-link debit to MORTGAGE account rejected | error | MORTGAGE account | Account number, amount -$100 (debit), facility type = 496 | Request rejected; fail code '4' | no | BR-DBCRFUN-7 |
| 7  | Payment-link debit to LOAN account rejected | error | LOAN account | Account number, amount -$100 (debit), facility type = 496 | Request rejected; fail code '4' | no | BR-DBCRFUN-8 |
| 8  | Payment-link credit to MORTGAGE account rejected | error | MORTGAGE account | Account number, amount +$100 (credit), facility type = 496 | Request rejected; fail code '4' | no | BR-DBCRFUN-11 |
| 9  | Payment-link credit to LOAN account rejected | error | LOAN account | Account number, amount +$100 (credit), facility type = 496 | Request rejected; fail code '4' | no | BR-DBCRFUN-12 |
| 10 | Teller debit to MORTGAGE account is allowed | happy-path | MORTGAGE account | Account number, amount -$500 (debit), facility type = teller | Both balances updated; 'DEB' audit record written; no account-type restriction for teller | no | BR-DBCRFUN-13 |
| 11 | Account not found returns failure | error | No account exists | Non-existent account number | Fail code '1'; success indicator negative | no | BR-DBCRFUN-5 |
| 12 | Teller debit bypasses available balance check | happy-path | CURRENT account with balance $0 | Account number, teller debit of $100 (facility non-496) | Debit applied; balance goes negative; no insufficient-funds rejection | no | BR-DBCRFUN-10 |
| 13 | Maximum signed amount (boundary) | boundary | Account with large balance | Account number, maximum possible amount (PIC S9(10)V99 = 9999999999.99) | Balances updated correctly | yes | BR-DBCRFUN-16 |
| 14 | Failed PROCTRAN write rolls back balance update | error | DB2 PROCTRAN insert fails | Any debit/credit | Balance update is rolled back; success indicator negative | no | BR-DBCRFUN-30 |
| 15 | Audit record amount equals the transaction amount | happy-path | Any successful debit/credit | Account number, amount $123.45 (debit) | Audit record amount = -123.45; transaction type matches facility and direction | no | BR-DBCRFUN-28 |
| 16 | Account number zero rejected on debit/credit screen | error | None | Account number = 00000000 in the debit/credit entry screen | Request rejected with message 'Please enter a non zero account number.'; no backend call made | no | BR-BNK1CRA-11 |
| 17 | Invalid sign character rejected | error | Debit/credit screen displayed | Account number valid; sign character = 'X' (not '+' or '-') | Request rejected with message 'Please enter + or - preceding the amount'; no transaction applied | no | BR-BNK1CRA-12 |
| 18 | Empty sign field silently treated as credit | happy-path | Debit/credit screen displayed | Account number valid; sign field left blank; amount = 100.00 | Amount of +100.00 applied as a credit; no error message shown; this is legacy behaviour -- a blank sign defaults to credit without warning | no | BR-BNK1CRA-12a |
| 19 | Zero amount rejected on debit/credit screen | error | None | Account number valid, sign valid, amount = 0.00 | Request rejected with message 'Please supply a non-zero amount.' | yes | BR-BNK1CRA-20 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| Transaction Amount (PIC S9(10)V99) | Signed transaction amount | -(9999999999.99) to +9999999999.99 | Negative (debit); Zero (rejected); Positive (credit) | -9999999999.99, -0.01, 0.00 (rejected), 0.01, 9999999999.99 |
| Facility Type (PIC 9(3)) | Transaction source | Teller (any value except 496) or Payment Link (496) | Teller: unrestricted debit/credit; Payment link (496): MORTGAGE/LOAN blocked; funds check applies | 496 (payment link threshold) |
| Account Type restriction | Account category for payment link | ISA, SAVING, CURRENT: unrestricted; LOAN, MORTGAGE: blocked for payment link | Unrestricted types; Restricted types (LOAN/MORTGAGE) | LOAN and MORTGAGE |
| Sign character (PIC X(1)) | Debit/credit direction | '+' or '-'; blank defaults to credit | Valid: '+' (credit), '-' (debit); Invalid: any other single char when field length = 1; Blank/omitted: silently defaults to credit | '+', '-', ' ' (blank defaults to credit), 'X' (rejected) |

---

## Fund Transfer

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Fund Transfer |
| Source Rules | BR-XFRFUN-1 through BR-XFRFUN-37, BR-BNK1TFN-8 through BR-BNK1TFN-22 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Successful transfer between two accounts (source number lower) | happy-path | Both accounts exist; source account number < target account number | Source account number, target account number, amount $200 | Source available and actual balances reduced by $200; target balances increased by $200; transfer-type audit record written; success indicator positive; message 'Transfer successfully applied.' shown | no | BR-XFRFUN-3, BR-XFRFUN-5, BR-XFRFUN-6, BR-XFRFUN-7, BR-XFRFUN-8, BR-XFRFUN-14, BR-XFRFUN-23, BR-BNK1TFN-29 |
| 2  | Successful transfer (source number higher, reverse ordering) | happy-path | Both accounts exist; source account number > target account number | Source account (higher number), target account (lower number), amount $50 | Both account balances updated correctly; same audit behaviour as scenario 1; intermediate COMM-SUCCESS reset does not affect final result | no | BR-XFRFUN-4, BR-XFRFUN-36 |
| 3  | Zero transfer amount rejected | error | Both accounts exist | Source account, target account, amount $0.00 | Request rejected; fail code '4'; message 'Please supply an amount greater than zero.' shown | yes | BR-XFRFUN-1, BR-BNK1TFN-15, BR-BNK1TFN-22, BR-BNK1TFN-26 |
| 4  | Negative transfer amount rejected | error | Both accounts exist | Source account, target account, amount -$50 | Request rejected; error 'Please supply a positive amount.' | yes | BR-XFRFUN-1, BR-BNK1TFN-17 |
| 5  | Source account not found | error | Target exists; source does not | Non-existent source, existing target, amount $100 | Request rejected; fail code '1'; message 'Sorry the FROM ACCOUNT no was not found. Transfer not applied.' shown; no balances modified | no | BR-XFRFUN-5, BR-BNK1TFN-23 |
| 6  | Target account not found triggers rollback | error | Source exists; target does not | Existing source, non-existent target, amount $100 | Request rejected; fail code '2'; message 'Sorry the TO ACCOUNT no was not found. Transfer not applied.' shown; source account balance rolled back to original value | no | BR-XFRFUN-8, BR-BNK1TFN-24 |
| 7  | Cross-bank sort code silently redirected to local bank | error | Target on different sort code does not exist locally | Source and target on different sort codes, amount $100 | Sort code overridden to 987654; if account not found locally, fail code '1' or '2' | no | BR-XFRFUN-35 |
| 8  | Audit record keyed on source account | happy-path | Successful transfer | Any valid transfer | Audit record identifies the source account; target account sort code and number appear in the description field | no | BR-XFRFUN-27, BR-XFRFUN-26 |
| 9  | No overdraft limit check performed | happy-path | Source account with $0 balance | Source, target, amount $100 | Transfer proceeds; source balance becomes -$100; no overdraft rejection | no | BR-XFRFUN-note-1 |
| 10 | Minimum valid transfer amount | boundary | Both accounts exist | Source, target, amount $0.01 | Transfer succeeds | yes | BR-XFRFUN-1, BR-BNK1TFN-15 |
| 11 | Deadlock resolved by automatic retry | happy-path | DB2 deadlock on first attempt, resolves within 5 retries | Any valid transfer | Transfer completes successfully after automatic retry | no | BR-XFRFUN-10, BR-XFRFUN-13 |
| 12 | FROM and TO account numbers must differ | error | Both accounts exist | Same account number in both FROM and TO fields | Request rejected; error 'The FROM & TO account should be different'; no transfer performed | no | BR-BNK1TFN-10 |
| 13 | Account number 00000000 is not valid for FROM or TO | error | None | FROM account = 00000000 or TO account = 00000000 | Request rejected; error 'Account no 00000000 is not valid'; no transfer performed | no | BR-BNK1TFN-11 |
| 14 | Transfer amount with embedded spaces rejected | error | Both accounts exist | Amount value containing embedded spaces (e.g., '5 00') | Request rejected; error 'Please supply a numeric amount without embedded spaces.' | no | BR-BNK1TFN-18 |
| 15 | Transfer amount with more than two decimal places rejected | error | Both accounts exist | Amount value '100.123' (three decimal places) | Request rejected; error 'Only up to two decimal places are supported.' | no | BR-BNK1TFN-21 |
| 16 | Transfer amount with multiple decimal points rejected | error | Both accounts exist | Amount value '1.0.0' (two decimal points) | Request rejected; error 'Use one decimal point for amount only.' | no | BR-BNK1TFN-20 |
| 17 | Transfer amount zero after NUMVAL conversion rejected | error | Both accounts exist | Amount field that passes format checks but evaluates to zero (e.g., '0.00') | Request rejected; error 'Please supply a non-zero amount.' | yes | BR-BNK1TFN-22 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| Transfer Amount (PIC S9(10)V99) | Amount to transfer | 0.01 to 9999999999.99 | Valid: positive; Zero: rejected; Negative: rejected; Embedded spaces: rejected; Multiple decimals: rejected | 0.00 (rejected), 0.01 (minimum valid), 9999999999.99 (maximum) |
| Source vs Target Account | Self-transfer guard | Source must differ from target | Same: rejected at screen; Different: valid | Same account number, '00000000' (rejected for both) |
| Sort Code (overridden, PIC 9(6)) | Destination bank | Always forced to 987654 | Any input sort code is silently replaced; cross-bank transfers not supported | '987654' (only effective value) |

---

## Centralised Abend Logging

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Centralised Abend Logging |
| Source Rules | BR-ABNDPROC-1 through BR-ABNDPROC-15 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Abend record persisted successfully | happy-path | Abend file is available and writable | Complete abend record (APPLID, TRANID, date, time, abend code, program name, RESP, RESP2, SQLCODE, 600-byte freeform text) | Record written to the abend store; calling program receives control back normally (service does not raise a new error) | no | BR-ABNDPROC-1, BR-ABNDPROC-2 |
| 2  | VSAM write failure returns silently to caller | error | Abend file is unavailable or full | Any abend record | Service returns to caller without raising a new error; abend record is silently abandoned; diagnostic messages written to system log | no | BR-ABNDPROC-3 |
| 3  | Record key is unique per microsecond-timestamp plus task | happy-path | Multiple abends in rapid succession | Two abend records with different timestamps or task numbers | Each record stored under a distinct key; no duplicate-key error | no | BR-ABNDPROC-4 |
| 4  | All 600 bytes of freeform diagnostic text are preserved | boundary | Abend record with full 600-byte freeform | 600-character freeform text | Retrieved record's freeform field contains the identical 600-character string without truncation | yes | BR-ABNDPROC-15 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| Freeform text (PIC X(600)) | Diagnostic description | Any 600-char string | Full 600 chars; Partial fill; All spaces | 1 character, 600 characters |
| Abend code (PIC X(4)) | CICS abend code | Any 4-char code | Known CBSA codes (HBNK, CVR1, HWPT, HROL, WPV6, WPV7, SAME, RUF2, RUF3, HNCS, HRAC, PLOP); Unknown code | All spaces (minimum content), 4 non-space chars |

---

## Utility Services

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Utility Services |
| Source Rules | BR-GETSCODE-1, BR-GETSCODE-2, BR-GETCOMPY-1, BR-GETCOMPY-2 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Get sort code returns 987654 | happy-path | Service is available | Any call to the sort code service (empty COMMAREA) | Sort code value '987654' is returned | no | BR-GETSCODE-1, BR-GETSCODE-2 |
| 2  | Sort code is always exactly 6 characters | boundary | Service available | Any call | Returned value is exactly 6 characters; no leading zeros dropped | yes | BR-GETSCODE-1 |
| 3  | Get company name returns static value | happy-path | Company name service is available | Any call to the company name service | Returns 'CICS Bank Sample Application' padded to 40 characters | no | BR-GETCOMPY-1 |
| 4  | Company name is always the same value | happy-path | Service available | Multiple calls | All calls return the same 40-character company name string | no | BR-GETCOMPY-1 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| Sort Code (PIC X(6)) | Bank sort code | Always '987654' | Only valid value: '987654' | '987654' |
| Company Name (PIC X(40)) | Bank name | Always 'CICS Bank Sample Application' (40 chars) | Only valid value; literal is 30 chars padded to 40 with trailing spaces | 40-character padded string |

---

## Test Data Initialisation

> Note: This is a batch destructive-reload capability intended for test environments only. The scenarios below describe observable post-conditions after a successful batch run in an isolated test environment.

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Test Data Initialisation |
| Source Rules | BR-BANKDATA-1 through BR-BANKDATA-41 |
| Confidence   | medium |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Successful batch load with valid parameters | happy-path | Test environment; existing data may be present | JCL PARM: start=1, end=100, step=1, seed=42 | 100 customer records in VSAM; 100-500 account rows in DB2 ACCOUNT; CONTROL table rows '987654-ACCOUNT-LAST' and '987654-ACCOUNT-COUNT' exist; pre-existing ACCOUNT and CONTROL rows for sort code 987654 deleted before load | no | BR-BANKDATA-1, BR-BANKDATA-2, BR-BANKDATA-15, BR-BANKDATA-31, BR-BANKDATA-32 |
| 2  | End key less than start key rejected | error | None | JCL PARM end=50, start=100 (end < start) | Job terminates with return code 12; no data written | no | BR-BANKDATA-1 |
| 3  | Zero step key rejected | error | None | JCL PARM step=0 | Job terminates with return code 12; no data written | yes | BR-BANKDATA-2 |
| 4  | LOAN and MORTGAGE accounts have negative balances | happy-path | Batch run completed | Inspect generated LOAN and MORTGAGE accounts | All LOAN and MORTGAGE accounts have available and actual balances less than zero | no | BR-BANKDATA-29 |
| 5  | ISA accounts have fixed interest rate 2.10 | happy-path | Batch run completed | Inspect generated ISA accounts | ISA interest rate = 2.10 for all generated ISA accounts | no | BR-BANKDATA-23 |
| 6  | CURRENT accounts have zero interest rate | happy-path | Batch run completed | Inspect generated CURRENT accounts | CURRENT interest rate = 0.00 | no | BR-BANKDATA-23 |
| 7  | Statement dates are hard-coded to 2021 values | happy-path | Batch run completed (any run date) | Inspect any generated account | Last statement date = 01.07.2021; next statement date = 01.08.2021 regardless of run date | no | BR-BANKDATA-25, BR-BANKDATA-26 |
| 8  | Start key equals end key creates exactly one customer | boundary | None | JCL PARM start=500, end=500, step=1 | Exactly 1 customer record; 1-5 accounts for that customer | yes | BR-BANKDATA-1 |
| 9  | Control sentinel record exists in VSAM | happy-path | Batch run completed | Read VSAM record with sort code '000000' and number '9999999999' | Sentinel record exists with eye-catcher 'CTRL' | no | BR-BANKDATA-33 |
| 10 | Each customer gets 1 to 5 accounts | happy-path | Batch run with any valid parameters | Inspect account counts per customer | Every customer has between 1 and 5 accounts; no customer has 0 or 6+ accounts | no | BR-BANKDATA-15 |
| 11 | VSAM customer control sentinel has zero customer count and zero last-customer-number | happy-path | Batch run completed | Read the VSAM sentinel record (sort code '000000', number '9999999999') | NUMBER-OF-CUSTOMERS and LAST-CUSTOMER-NUMBER fields in the sentinel record are both zero; those counters are tallied in memory but not persisted to the sentinel or to any DB2 CONTROL row | no | BR-BANKDATA-34, BR-BANKDATA-35 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| END-KEY (PIC 9(10)) | Last customer number to generate | >= START-KEY | Valid: >= START-KEY; Invalid: < START-KEY | START-KEY - 1 (invalid), START-KEY (single customer) |
| STEP-KEY (PIC 9(10)) | Increment between customer numbers | > 0 | Valid: any positive integer; Invalid: zero | 0 (invalid), 1 (minimum valid) |

---

## Cross-Capability Scenarios

End-to-end tests that span multiple capabilities, verifying correct behavior across capability boundaries:

| #  | Scenario | Capabilities Involved | Preconditions | Input | Expected Output | Source Rules |
| -- | -------- | --------------------- | ------------- | ----- | --------------- | ------------ |
| E1 | Create customer then create account | Customer Creation with Credit Scoring, Account Creation | None | Step 1: create valid customer; Step 2: use returned customer number to create an account | Customer created with assigned number; account created under that customer; both 'OCC' and 'OCA' audit records present | BR-CRECUST-37, BR-CRECUST-44, BR-CREACC-1, BR-CREACC-26, BR-CREACC-31 |
| E2 | Create account then perform teller debit and credit | Account Creation, Debit / Credit Funds | Customer exists | Step 1: create account; Step 2: deposit $500 (teller); Step 3: withdraw $200 (teller) | Final available balance = initial + 500 - 200; three PROCTRAN records: OCA, CRE, DEB | BR-CREACC-26, BR-DBCRFUN-16, BR-DBCRFUN-21, BR-DBCRFUN-23 |
| E3 | Enquire balances then transfer and verify | Account Enquiry, Fund Transfer | Two accounts exist | Step 1: record balances via enquiry; Step 2: transfer $100 from A to B; Step 3: re-enquire both accounts | Account A balance reduced by $100; account B balance increased by $100; one transfer-type audit record | BR-XFRFUN-3, BR-XFRFUN-7, BR-XFRFUN-14, BR-XFRFUN-23, BR-INQACC-4 |
| E4 | Delete customer cascades to all accounts | Customer Deletion (Full Cascade), Account Enquiry | Customer with 3 accounts | Step 1: delete customer; Step 2: attempt to enquire each former account | All 3 accounts return not-found; customer enquiry returns not-found; 3 'ODA' records + 1 'ODC' record in audit | BR-DELCUS-1, BR-DELCUS-4, BR-DELCUS-5, BR-DELCUS-22 |
| E5 | Navigate to customer enquiry from main menu | Navigation and Session Management, Customer Enquiry | Customer exists; user at main menu | User selects '1' from menu; enters customer number | Customer details displayed including credit score and review date | BR-BNKMENU-9, BR-INQCUST-3, BR-INQCUST-25 |
| E6 | Create 10 accounts then attempt 11th | Account Creation | Customer exists | Create accounts 1 through 10 sequentially; attempt account 11 | Accounts 1-10 created successfully; account 11 request rejected with fail code '8' | BR-CREACC-4 |
| E7 | Batch initialisation produces data readable by enquiry | Test Data Initialisation, Customer Enquiry, Accounts Enquiry by Customer | Isolated test environment | Step 1: run batch initialisation; Step 2: enquire customer from generated range; Step 3: enquire accounts for that customer | Customer returned successfully; 1-5 accounts returned; CONTROL rows accessible to account creation | BR-BANKDATA-1, BR-INQCUST-3, BR-INQACCCU-7 |
| E8 | Reverse-order fund transfer verifies both balances correctly | Fund Transfer, Account Enquiry | Source account has higher account number than target | Transfer of $150 with source number > target number | Both balances updated correctly (lower-numbered account updated first internally); enquiry confirms source decreased, target increased | BR-XFRFUN-4, BR-XFRFUN-36, BR-INQACC-4 |
| E9 | Create customer with all-uppercase title then enquire | Customer Creation with Credit Scoring, Customer Enquiry | System available | Step 1: create customer with title 'MR' (uppercase); Step 2: enquire created customer by returned number | Customer found; stored name has title normalised to 'Mr' (mixed-case canonical form) | BR-BNK1CCS-16, BR-CRECUST-43, BR-INQCUST-3 |
| E10 | Account enquiry then delete without re-enquiring (delete guard) | Account Deletion | Account exists | Step 1: enquire account; Step 2: navigate away and return to account screen; Step 3: press delete (PF5) without re-enquiring | Delete rejected if session state (sort code + account number) not present; user must enquire before delete is accepted | BR-BNK1DAC-13, BR-BNK1DAC-14, BR-DELACC-2 |
| E11 | Customer with 15 accounts: all retrieved by backend, first 10 shown on screen | Accounts Enquiry by Customer | Customer with 15 accounts exists | Customer number enquiry via list-accounts screen | Backend returns 15 account rows; screen displays 10 rows; message shows count 15; remaining 5 accounts not visible without pagination | BR-BNK1CCA-19, BR-INQACCCU-5 |
