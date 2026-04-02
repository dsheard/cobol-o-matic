---
type: test-specifications
subtype: behavioral-tests
status: draft
confidence: high
last_pass: 7
---

# Behavioral Test Specifications

Stack-agnostic test scenarios derived from business rules and functional capabilities. Tests describe WHAT the system does, not HOW -- any target implementation that passes these tests preserves the legacy system's behavior.

## Test Design Principles

| Principle | Description |
| --------- | ----------- |
| Black-box coverage | Each scenario is expressed as given inputs and expected outputs; no COBOL execution path is referenced in the scenario description |
| Business-domain language | Field names use domain terms (account ID, FICO score, etc.); legacy field mappings appear only in the equivalence matrix |
| Capability-first organization | Scenarios are grouped by business capability, not by program name |
| Boundary derivation | Boundaries are derived mechanically from PIC clause definitions per the mapping table; every capability with PIC-clause fields includes at least one boundary scenario |
| Known-defect annotation | Scenarios that verify a known production defect are flagged so the implementation team can decide whether to preserve or fix the behavior |

---

## User Authentication and Session Management

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | User Authentication and Session Management |
| Source Rules | BR-COSGN00C-1 through BR-COSGN00C-26 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Successful admin login routes to admin menu | happy-path | User record exists with type 'A' and matching password | User ID: 'ADMIN001', Password: 'PASS1234' | Session established; user directed to admin menu | no | BR-COSGN00C-12, BR-COSGN00C-13 |
| 2  | Successful regular user login routes to main menu | happy-path | User record exists with type 'U' and matching password | User ID: 'USER0001', Password: 'MYPASS01' | Session established; user directed to standard main menu | no | BR-COSGN00C-12, BR-COSGN00C-14 |
| 3  | Login rejected when user ID is blank | error | Any state | User ID: blank, Password: 'ANYPASS1' | Login screen re-displayed with error message indicating user ID is required; cursor positioned on user ID field | no | BR-COSGN00C-6 |
| 4  | Login rejected when password is blank | error | Any state | User ID: 'USER0001', Password: blank | Login screen re-displayed with error message indicating password is required; cursor positioned on password field | no | BR-COSGN00C-7 |
| 5  | Login rejected for unknown user ID | error | User ID does not exist in the security store | User ID: 'NOBODY01', Password: 'ANYPASS1' | Login screen re-displayed with error message indicating user was not found; cursor on user ID field | no | BR-COSGN00C-16 |
| 6  | Login rejected when password does not match | error | User exists in security store | User ID: valid, Password: incorrect value | Login screen re-displayed with wrong-password error; cursor on password field | no | BR-COSGN00C-15 |
| 7  | Credentials are matched case-insensitively | happy-path | User record stored with uppercase credentials | User ID: 'admin001' (lowercase), Password: 'pass1234' (lowercase) | Credentials normalised to uppercase before comparison; login succeeds as if uppercase was entered | no | BR-COSGN00C-9, BR-COSGN00C-10 |
| 8  | Session terminated on explicit exit | happy-path | Active session | User presses the designated exit key (PF3) | Goodbye message displayed; session ends; no subsequent re-entry is possible under the same transaction ID | no | BR-COSGN00C-4, BR-COSGN00C-25 |
| 9  | Unsupported function keys rejected at login | error | Login screen displayed | User presses any key other than Enter or the exit key | Login screen re-displayed with invalid-key error message | no | BR-COSGN00C-5 |
| 10 | Unexpected system error during credential lookup shows generic message | error | Security store unavailable or returns unexpected error | Valid user ID and password submitted | Login screen re-displayed with a generic "unable to verify" message; the underlying system error code is not exposed to the user | no | BR-COSGN00C-17 |
| 11 | User ID boundary: maximum 8-character user ID accepted | boundary | User record with 8-character ID exists | User ID: exactly 8 characters (e.g., 'ABCDEFGH') | Login proceeds normally; full 8-character ID used as lookup key | yes | BR-COSGN00C-18, BR-COSGN00C-19 |
| 12 | User type other than 'A' routes to regular menu | happy-path | User with type 'U' exists | Valid credentials with user type 'U' | User routed to the standard (non-admin) menu | no | BR-COSGN00C-22 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| SEC-USR-ID | User ID | PIC X(08), any character | Non-blank (valid), blank/spaces (invalid), low-values (invalid) | 1-char, 8-char (max), spaces |
| SEC-USR-PWD | Password | PIC X(08), any character | Non-blank (valid), blank/spaces (invalid), low-values (invalid) | 1-char, 8-char (max) |
| SEC-USR-TYPE | User Type | PIC X(01), 'A' or 'U' | 'A' (admin), 'U' (regular), any other non-blank (routes to regular menu) | 'A', 'U', '?' |

---

## Navigation and Menu Routing

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Navigation and Menu Routing |
| Source Rules | BR-COMEN01C-*, BR-COADM01C-* |
| Confidence   | medium |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Admin user presented with admin menu after login | happy-path | User authenticated with type 'A' | Successful login as admin user | Admin menu displayed with 6 options; regular user menu not shown | no | BR-COSGN00C-13 |
| 2  | Regular user presented with standard menu after login | happy-path | User authenticated with type 'U' | Successful login as regular user | Standard menu displayed with 10 options; admin menu not shown | no | BR-COSGN00C-14 |
| 3  | Menu option dispatches to correct program | happy-path | User on main menu | Valid menu option number entered | Control transferred to the program corresponding to the selected option | no | BR-COMEN01C-dispatch |
| 4  | Invalid menu option rejected | error | User on menu screen | Option number outside the valid range | Error message displayed; menu re-displayed | no | BR-COMEN01C-invalid |
| 5  | PF3 from any menu returns to sign-on screen | happy-path | User on a menu screen | PF3 key pressed | Control returned to the sign-on screen | no | BR-COMEN01C-pf3 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| CDEMO-USER-TYPE | User Type in session | PIC X(01), 'A' or 'U' | 'A' (admin menu), 'U' or other (standard menu) | 'A', 'U' |

---

## Account Inquiry and Update

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Account Inquiry and Update |
| Source Rules | BR-COACTUPC-1 through BR-COACTUPC-119, BR-COACTVWC-* |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Account details displayed for valid account number | happy-path | Account exists; customer record linked | Account ID: valid 11-digit number | Account master and linked customer record displayed on screen | no | BR-COACTUPC-106 |
| 2  | Account number is mandatory | error | Any state | Account ID: blank or spaces submitted | Rejected with error message requiring account number; cursor on account ID field | no | BR-COACTUPC-39 |
| 3  | Account number must be numeric | error | Any state | Account ID: contains non-numeric characters | Rejected with message that account number must be numeric | no | BR-COACTUPC-40 |
| 4  | Account number zero rejected | error | Any state | Account ID: all zeros | Rejected with error message indicating non-zero account number required | no | BR-COACTUPC-41 |
| 5  | Update requires PF5 confirmation before write | happy-path | Account details displayed; valid changes entered | Changes submitted without pressing PF5 | Changes displayed with confirmation prompt; no data written until PF5 is pressed | no | BR-COACTUPC-103, BR-COACTUPC-111 |
| 6  | PF5 confirmation triggers account and customer record write | happy-path | Valid changes in confirmed-but-not-written state | PF5 pressed | Both account and customer records updated; success state displayed | no | BR-COACTUPC-111, BR-COACTUPC-115 |
| 7  | No-change submission does not advance to confirmation | happy-path | Account details displayed | All fields resubmitted without any change | System detects no change; screen re-displayed with informational message; no write initiated | no | BR-COACTUPC-36, BR-COACTUPC-108 |
| 8  | Concurrent modification detected and surfaced | error | Another actor modifies the account record between the initial fetch and the PF5 write | PF5 pressed to write changes | System detects that the stored record differs from the re-fetched record; changes NOT written; current values re-displayed with message indicating the record was changed; user must review before retrying | no | BR-COACTUPC-114 |
| 9  | Account lock failure reported to user | error | Account record cannot be locked for update (e.g., record locked by concurrent process) | PF5 pressed to write | Error message indicating account could not be locked; update not performed | no | BR-COACTUPC-112 |
| 10 | FICO score must be in range 300-850 | error | Account details displayed; changes submitted | FICO score: 299 | Rejected with message that FICO score must be between 300 and 850 | no | BR-COACTUPC-99 |
| 11 | FICO score boundary: 300 accepted | boundary | Account details displayed | FICO score: 300 | Validation passes; score accepted | yes | BR-COACTUPC-99 |
| 12 | FICO score boundary: 850 accepted | boundary | Account details displayed | FICO score: 850 | Validation passes; score accepted | yes | BR-COACTUPC-99 |
| 13 | FICO score boundary: 851 rejected | boundary | Account details displayed | FICO score: 851 | Rejected with out-of-range message | yes | BR-COACTUPC-99 |
| 14 | FICO score boundary: 0 rejected at numeric check | boundary | Account details displayed | FICO score: 0 | Rejected as zero is not permitted | yes | BR-COACTUPC-65, BR-COACTUPC-66 |
| 15 | Account active status must be Y or N | error | Account details displayed | Active status: any value other than 'Y' or 'N' | Rejected with message that value must be Y or N | no | BR-COACTUPC-46, BR-COACTUPC-47 |
| 16 | SSN Part 1 of 000 rejected | error | Account details displayed | SSN first three digits: 000 | Rejected with SSN validation error | no | BR-COACTUPC-94 |
| 17 | SSN Part 1 in range 900-999 rejected | boundary | Account details displayed | SSN first three digits: 900 | Rejected with SSN validation error | yes | BR-COACTUPC-94 |
| 18 | SSN Part 1 of 666 rejected | error | Account details displayed | SSN first three digits: 666 | Rejected with SSN validation error | no | BR-COACTUPC-94 |
| 19 | State code must be valid US state code | error | Account details displayed | State code: 'XX' (not a US state) | Rejected with message that the state code is invalid | no | BR-COACTUPC-97 |
| 20 | Zip code must be valid for the given state | error | Account details displayed; valid state code entered | State: 'CA', Zip: '00001' (invalid for California) | Rejected with message indicating invalid zip code for the state | no | BR-COACTUPC-101 |
| 21 | Phone area code must be valid North America code | error | Account details displayed | Phone 1 area code: 000 | Rejected with message that area code is not a valid North America general purpose code | no | BR-COACTUPC-83, BR-COACTUPC-84 |
| 22 | Credit limit field must be a valid signed decimal | error | Account details displayed | Credit limit: 'ABC' (non-numeric) | Rejected with message that the field is not valid | no | BR-COACTUPC-70, BR-COACTUPC-71 |
| 23 | Date fields must be valid calendar dates | error | Account details displayed | Open date: '2024-02-30' (invalid calendar date) | Rejected with date validation error | no | BR-COACTUPC-76 |
| 24 | First error message takes priority; subsequent field errors do not overwrite it | error | Account details displayed; multiple invalid fields submitted | Multiple invalid fields (e.g., invalid FICO score AND invalid SSN simultaneously) | Only the first error message encountered during validation is displayed | no | BR-COACTUPC-105 |
| 25 | Optional middle name accepted when blank | happy-path | Account details displayed | Middle name: blank | No validation error; blank middle name accepted | no | BR-COACTUPC-58 |
| 26 | Optional middle name with non-alpha characters rejected | error | Account details displayed | Middle name: 'John2' (contains digit) | Rejected with message that the field may contain alphabets only | no | BR-COACTUPC-57 |
| 27 | Account ID boundary: 11-digit maximum accepted | boundary | Account with 11-digit ID exists | Account ID: 99999999999 (maximum 11-digit value) | Account fetched and displayed | yes | BR-COACTUPC-39, BR-COACTUPC-42 |
| 28 | Account view (read-only) displays full account and customer details for valid account | happy-path | Account and linked customer exist; cross-reference file populated | Valid 11-digit account ID entered | Account master fields (status, balance, credit limit, cash limit, cycle credit/debit, open/expiry/reissue dates, group ID) and all customer fields (name, address, SSN, FICO, phones, etc.) displayed; no editable fields | no | BR-COACTVWC-28 |
| 29 | Account number blank rejected with 'Account number not provided' | error | Any state | Account ID: blank or spaces | Error message 'Account number not provided'; account ID field highlighted red; cursor positioned on account input | no | BR-COACTVWC-12 |
| 30 | Account number not numeric or all-zeros rejected with filter message | error | Any state | Account ID: non-numeric characters or all zeros | Error message 'Account Filter must  be a non-zero 11 digit number'; account ID field highlighted; cursor on account input | no | BR-COACTVWC-13, BR-COACTVWC-14 |
| 31 | Account not found in cross-reference shows error message | error | Account ID does not exist in cross-reference file | Valid numeric non-zero account ID that has no cross-reference entry | Error message including account ID and response codes; account and customer data not displayed | no | BR-COACTVWC error-handling (CXACAIX NOTFND) |
| 32 | [KNOWN DEFECT] Customer read attempted even when account master is not found | error | Account ID is in cross-reference but not in account master | Valid account ID found in cross-reference, not in ACCTDAT | Error for account master not found; customer read is still attempted (defensive skip guard is inoperative); observable as an extra file-read operation even under error conditions | no | BR-COACTVWC-21 |
| 33 | SSN displayed with dashes in format NNN-NN-NNNN | happy-path | Customer record exists with 9-digit SSN | Valid account ID; customer has SSN value '123456789' | SSN displayed as '123-45-6789' (formatted with hyphens); raw unformatted SSN is never shown | no | BR-COACTVWC-30 |
| 34 | PF3 exits to calling program or main menu | happy-path | User on account view screen; entered from COMEN01C or other program | PF3 pressed | XCTL to the calling program/transaction if one was set; otherwise XCTL to main menu (COMEN01C / CM00) | no | BR-COACTVWC-1, BR-COACTVWC-4 |
| 35 | Any key other than Enter or PF3 silently treated as Enter | happy-path | Account view screen displayed | Any attention key other than Enter or PF3 pressed | Key remapped to Enter; input processing proceeds as if Enter was pressed; no invalid-key message | no | BR-COACTVWC-2 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| ACCT-ID | Account ID | PIC 9(11), 1 to 99999999999 | Blank/spaces (error), zero (error), valid 11-digit numeric, non-numeric (error) | 1, 99999999999 |
| CUST-FICO-CREDIT-SCORE | FICO Score | PIC 9(03), 300-850 | Below 300 (error), 300-850 (valid), above 850 (error), zero (error at numeric check) | 0, 299, 300, 850, 851, 999 |
| ACCT-ACTIVE-STATUS | Account Active Status | PIC X(01), 'Y' or 'N' | 'Y' (valid), 'N' (valid), other non-blank (error), blank (error) | 'Y', 'N', 'X' |
| CUST-ADDR-STATE-CD | State Code | PIC X(02), valid US state | Valid 2-letter state code, invalid code (error), blank (error) | 'CA', 'XX' |
| ACCT-CREDIT-LIMIT | Credit Limit | PIC S9(10)V99 | Valid signed decimal, blank (error), non-numeric (error) | 0.00, -9999999999.99, 9999999999.99 |

---

## Credit Card Management

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Credit Card Management |
| Source Rules | BR-COCRDLIC-1 through BR-COCRDLIC-57, BR-COCRDSLC-*, BR-COCRDUPC-* |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Admin user sees all cards in card list | happy-path | Multiple card records exist; user is admin type | Admin user navigates to card list screen with no filter | All cards in the system displayed (paginated, up to 7 per page) | no | BR-COCRDLIC-1 |
| 2  | Regular user sees only cards for their account | happy-path | Multiple card records exist; user is regular type; account set in session | Regular user navigates to card list | Only cards linked to the user's account displayed | no | BR-COCRDLIC-3 |
| 3  | Account filter narrows card list | happy-path | Multiple accounts exist with cards | Valid account ID entered in filter field | Only cards belonging to specified account displayed | no | BR-COCRDLIC-26 |
| 4  | Account filter must be numeric | error | Card list displayed | Non-numeric value in account filter field | Error message displayed; card list not filtered by invalid value | no | BR-COCRDLIC-17 |
| 5  | Card number filter must be numeric | error | Card list displayed | Non-numeric value in card number filter field | Error message displayed; card list not filtered by invalid value | no | BR-COCRDLIC-20 |
| 6  | Only one row may be selected at a time | error | Card list showing multiple cards | Action code entered on two or more rows simultaneously | Error message indicating only one selection is permitted; no navigation occurs | no | BR-COCRDLIC-23 |
| 7  | Invalid row action code rejected | error | Card list displayed | Action code other than 'S' (select) or 'U' (update) entered | Error message indicating invalid action code | no | BR-COCRDLIC-24 |
| 8  | Selecting 'S' on a row navigates to card detail view | happy-path | Card list with at least one card | Action code 'S' entered on a row; Enter pressed | Card detail view displayed for the selected card | no | BR-COCRDLIC-13 |
| 9  | Selecting 'U' on a row navigates to card update screen | happy-path | Card list with at least one card | Action code 'U' entered on a row; Enter pressed | Card update screen displayed for the selected card | no | BR-COCRDLIC-14 |
| 10 | PF8 pages forward through card list | happy-path | More than 7 card records exist | PF8 pressed | Next page of cards displayed | no | BR-COCRDLIC-11 |
| 11 | PF7 pages backward through card list | happy-path | User has navigated past first page | PF7 pressed | Previous page of cards displayed | no | BR-COCRDLIC-12 |
| 12 | PF7 on first page shows informational message | happy-path | Card list on first page | PF7 pressed | Informational message that there are no previous pages; first page re-displayed | no | BR-COCRDLIC-39 |
| 13 | No records found message when filter matches nothing | happy-path | No cards match the applied filter | Valid but non-matching filter applied | Message indicating no records found for the search condition | no | BR-COCRDLIC-32 |
| 14 | Card list pagination: boundary of 7 cards per page | boundary | Exactly 7 card records exist | Navigate to card list | All 7 cards displayed on a single page; no next-page indicator | yes | BR-COCRDLIC-29 |
| 15 | Card number boundary: 16-digit maximum accepted in filter | boundary | Any state | 16-digit card number entered in card filter | Filter applied; card list filtered accordingly | yes | BR-COCRDLIC-19, BR-COCRDLIC-21 |
| 16 | Card detail view displays embossed name, expiry month/year, and active status for valid account and card | happy-path | Card record exists for the given account and card number | Account ID: valid 11-digit; Card number: valid 16-digit | Card detail screen shown with embossed name, expiry month, expiry year, and card active status; no editable fields | no | BR-COCRDSLC-44, BR-COCRDSLC-45 |
| 17 | Account number blank rejected with 'Account number not provided' | error | Any state (user manually entered from CCDL transaction) | Account ID: blank or spaces | Rejected with message 'Account number not provided'; cursor on account field | no | BR-COCRDSLC-13 |
| 18 | Account number not numeric rejected | error | Any state | Account ID: non-numeric characters | Rejected with message 'ACCOUNT FILTER,IF SUPPLIED MUST BE A 11 DIGIT NUMBER' | no | BR-COCRDSLC-14 |
| 19 | Card number blank rejected with 'Card number not provided' | error | Any state | Card number: blank | Rejected with message 'Card number not provided'; cursor on card field | no | BR-COCRDSLC-16 |
| 20 | Card number not numeric rejected | error | Any state | Card number: non-numeric characters | Rejected with message 'CARD ID FILTER,IF SUPPLIED MUST BE A 16 DIGIT NUMBER' | no | BR-COCRDSLC-17 |
| 21 | Both account and card blank returns 'No input received' | error | Any state | Account ID: blank; Card number: blank | Rejected with message 'No input received' | no | BR-COCRDSLC-19 |
| 22 | Card not found returns 'Did not find cards for this search condition' | error | Account and card do not match any card record | Valid numeric account and card number that has no match in CARDDAT | Error message 'Did not find cards for this search condition'; both account and card fields highlighted | no | BR-COCRDSLC-46 |
| 23 | Account and card input fields are protected when navigated from card list | happy-path | User arrived at card detail from COCRDLIC via XCTL | Screen displayed | Account ID and card number fields are read-only (protected); card detail data pre-populated from commarea passed by COCRDLIC | no | BR-COCRDSLC-24 |
| 24 | PF3 exits to calling program or main menu | happy-path | User on card detail screen | PF3 pressed | XCTL to the program that invoked COCRDSLC; if none, XCTL to COMEN01C / CM00 | no | BR-COCRDSLC-7 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| CARD-NUM | Card Number | PIC X(16) | Valid 16-digit numeric, non-numeric (error), blank (no filter) | Spaces, '0000000000000001', '9999999999999999' |
| CARD-ACCT-ID | Card Account ID filter | PIC 9(11) | Valid 11-digit numeric, non-numeric (error), blank (no filter) | 0, 1, 99999999999 |
| CARD-ACTIVE-STATUS | Card Active Status | PIC X(01), 'Y'/'N' | 'Y' (active), 'N' (inactive), other (implementation-defined) | 'Y', 'N' |

---

## Card Detail Update

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Card Detail Update |
| Source Rules | BR-COCRDUPC-1 through BR-COCRDUPC-96 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Card details displayed for valid account and card numbers | happy-path | Card record exists linked to the specified account | Account ID: valid 11-digit; Card number: valid 16-digit | Card detail screen shown with embossed name, status, expiry; account/card fields protected; editable fields enabled | no | BR-COCRDUPC-46, BR-COCRDUPC-47 |
| 2  | Account number is mandatory for card search | error | Any state | Account ID: blank; Card number: valid | Rejected with error indicating account number not provided | no | BR-COCRDUPC-13 |
| 3  | Account number must be numeric | error | Any state | Account ID: contains non-numeric characters | Rejected with message that account filter must be an 11-digit number | no | BR-COCRDUPC-14 |
| 4  | Card number is mandatory for card search | error | Any state | Account ID: valid; Card number: blank | Rejected with error indicating card number not provided | no | BR-COCRDUPC-16 |
| 5  | Card number must be numeric | error | Any state | Card number: contains non-numeric characters | Rejected with message that card ID filter must be a 16-digit number | no | BR-COCRDUPC-17 |
| 6  | Both account and card blank rejected with no-input message | error | Any state | Account ID: blank; Card number: blank | Rejected with 'No input received' message | no | BR-COCRDUPC-19 |
| 7  | Card not found returns error for both account and card filters | error | Account ID and card number do not match any card record | Valid numeric account ID and card number that does not exist | Error 'Did not find cards for this search condition'; both search fields highlighted | no | BR-COCRDUPC-48 |
| 8  | After successful card fetch, search fields are protected and detail fields become editable | happy-path | Card found for search keys | Card details displayed | Account ID and card number fields are read-only; embossed name, active status, expiry month, expiry year fields are user-enterable | no | BR-COCRDUPC-60 |
| 9  | Card embossed name is mandatory for update | error | Card details displayed | Card name: blank or spaces | Rejected with message 'Card name not provided' | no | BR-COCRDUPC-22 |
| 10 | Card embossed name must contain only alphabetic characters and spaces | error | Card details displayed | Card name: 'JOHN2 DOE' (contains digit) | Rejected with message 'Card name can only contain alphabets and spaces' | no | BR-COCRDUPC-23 |
| 11 | Card active status is mandatory for update | error | Card details displayed | Active status: blank | Rejected with message 'Card Active Status must be Y or N' | no | BR-COCRDUPC-24 |
| 12 | Card active status must be Y or N | error | Card details displayed | Active status: 'X' (invalid) | Rejected with message 'Card Active Status must be Y or N' | no | BR-COCRDUPC-25 |
| 13 | Expiry month is mandatory | error | Card details displayed | Expiry month: blank | Rejected with message that expiry month must be between 1 and 12 | no | BR-COCRDUPC-26 |
| 14 | Expiry month must be in range 1 to 12 | error | Card details displayed | Expiry month: 13 | Rejected with out-of-range error | no | BR-COCRDUPC-27 |
| 15 | Expiry month boundary: 1 accepted | boundary | Card details displayed | Expiry month: 1 | Validation passes | yes | BR-COCRDUPC-27 |
| 16 | Expiry month boundary: 12 accepted | boundary | Card details displayed | Expiry month: 12 | Validation passes | yes | BR-COCRDUPC-27 |
| 17 | Expiry year is mandatory | error | Card details displayed | Expiry year: blank | Rejected with message 'Invalid card expiry year' | no | BR-COCRDUPC-28 |
| 18 | Expiry year boundary: 1950 accepted | boundary | Card details displayed | Expiry year: 1950 | Validation passes | yes | BR-COCRDUPC-29 |
| 19 | Expiry year boundary: 2099 accepted | boundary | Card details displayed | Expiry year: 2099 | Validation passes | yes | BR-COCRDUPC-29 |
| 20 | Expiry year 1949 rejected (below range) | boundary | Card details displayed | Expiry year: 1949 | Rejected with invalid year error | yes | BR-COCRDUPC-29 |
| 21 | Expiry year 2100 rejected (above range) | boundary | Card details displayed | Expiry year: 2100 | Rejected with invalid year error | yes | BR-COCRDUPC-29 |
| 22 | No-change submission bypasses validation and write | happy-path | Card details displayed; all fields as originally fetched | All fields resubmitted unchanged | 'No change detected' message; screen re-displayed; no write initiated | no | BR-COCRDUPC-20 |
| 23 | Valid changes require PF5 confirmation before write | happy-path | Card details displayed; valid changes entered | Changes submitted without PF5 | 'Changes validated. Press F5 to save' prompt displayed; fields protected; no write yet | no | BR-COCRDUPC-30 |
| 24 | PF5 confirmation triggers card record write to CARDDAT | happy-path | Changes validated and pending PF5 | PF5 pressed | Card record written to CARDDAT; success message 'Changes committed to database' shown | no | BR-COCRDUPC-38, BR-COCRDUPC-42 |
| 25 | Concurrent modification detected: write aborted; current values refreshed on screen | error | Changes pending PF5; another actor modifies the card record between fetch and PF5 | PF5 pressed | Write not performed; screen refreshed with current database values; message 'Record changed by some one else. Please review' | no | BR-COCRDUPC-54 |
| 26 | Record lock failure reported with retry message | error | Changes pending PF5; card record locked by concurrent process | PF5 pressed | Lock error; message 'Changes unsuccessful. Please try again' | no | BR-COCRDUPC-39 |
| 27 | First validation error takes priority; subsequent errors suppressed | error | Card details displayed; multiple invalid fields submitted | Card name blank AND expiry month 0 simultaneously | Only the first error encountered in the validation sequence is displayed; other errors not visible | no | BR-COCRDUPC-31 |
| 28 | PF3 exits to the calling program (e.g., card list) | happy-path | Card detail update screen active; entered from COCRDLIC | PF3 pressed | XCTL to the calling program; account and card cleared from session when entered from card list | no | BR-COCRDUPC-5 |
| 29 | PF12 forces a re-fetch of card data | happy-path | Card detail update screen active with details shown | PF12 pressed | Card record re-read from CARDDAT; current database values displayed | no | BR-COCRDUPC-35 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| CC-ACCT-ID | Account ID | PIC 9(11), non-zero | Blank/spaces (error), zero (error), valid 11-digit numeric, non-numeric (error) | 1, 99999999999 |
| CC-CARD-NUM | Card Number | PIC X(16), numeric | Blank (error), non-numeric (error), valid 16-digit | '0000000000000001', '9999999999999999' |
| CCUP-NEW-CRDNAME | Embossed Name | PIC X(50), alpha and spaces only | Blank (error), alpha only (valid), contains digit or special char (error) | Spaces, 'JOHN DOE', 'JOHN2 DOE' |
| CCUP-NEW-CRDSTCD | Card Active Status | PIC X(01), 'Y' or 'N' | 'Y' (valid), 'N' (valid), blank (error), other (error) | 'Y', 'N', ' ', 'X' |
| CCUP-NEW-EXPMON | Expiry Month | PIC X(02), 1-12 | Blank (error), 0 (error), 1-12 (valid), 13+ (error) | 0, 1, 12, 13 |
| CCUP-NEW-EXPYEAR | Expiry Year | PIC X(04), 1950-2099 | Blank (error), 1949 (error), 1950-2099 (valid), 2100+ (error) | 1949, 1950, 2099, 2100 |

---

## Transaction Inquiry and Manual Entry

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Transaction Inquiry and Manual Entry |
| Source Rules | BR-COTRN00C-*, BR-COTRN01C-*, BR-COTRN02C-1 through BR-COTRN02C-57 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Transaction detail displayed for valid transaction ID | happy-path | Transaction exists in transaction store | Valid transaction ID | Full transaction details displayed | no | BR-COTRN01C-read |
| 2  | New transaction added with account ID lookup | happy-path | Account exists; cross-reference for account-to-card is populated | Account ID supplied (no card number); all mandatory fields filled; confirmation 'Y' entered | Transaction written to store; success message with generated transaction ID displayed | no | BR-COTRN02C-11, BR-COTRN02C-15, BR-COTRN02C-52 |
| 3  | New transaction added with card number lookup | happy-path | Card exists; cross-reference for card-to-account is populated | Card number supplied (no account ID); all mandatory fields filled; confirmation 'Y' | Transaction written; success message with generated transaction ID | no | BR-COTRN02C-17, BR-COTRN02C-52 |
| 4  | Neither account ID nor card number rejected | error | Any state | Both account ID and card number left blank | Error message requiring either account ID or card number to be entered | no | BR-COTRN02C-18 |
| 5  | Account ID must be numeric when supplied | error | Any state | Non-numeric value in account ID field | Rejected with message that account ID must be numeric | no | BR-COTRN02C-14 |
| 6  | Account ID not found in cross-reference rejects entry | error | Account ID does not exist in cross-reference | Valid numeric account ID that does not exist | Error message indicating account not found | no | BR-COTRN02C error handling |
| 7  | Transaction amount must include sign character | error | Key validation passed | Amount field begins with digit rather than '+' or '-' | Rejected with format error message for amount | no | BR-COTRN02C-32 |
| 8  | Amount format: 8 integer digits, decimal point at position 10, 2 decimal places | error | Key validation passed | Amount field with decimal point at wrong position | Rejected with format error for amount | no | BR-COTRN02C-33, BR-COTRN02C-34, BR-COTRN02C-35 |
| 9  | Origination date must be a valid calendar date (YYYY-MM-DD) | error | Key and data presence validation passed | Origination date: '2024-02-30' | Rejected with invalid calendar date error | no | BR-COTRN02C-46 |
| 10 | Processing date must be a valid calendar date (YYYY-MM-DD) | error | Key and data presence validation passed | Processing date: '2024-13-01' | Rejected with invalid calendar date error | no | BR-COTRN02C-47 |
| 11 | Origination date must be in YYYY-MM-DD format with hyphen separators | error | Any state | Origination date: '20240101' (no hyphens) | Rejected with format error message | no | BR-COTRN02C-37, BR-COTRN02C-38, BR-COTRN02C-39, BR-COTRN02C-40 |
| 12 | Confirmation 'N' cancels add without writing | happy-path | All fields valid; system prompting for confirmation | Confirmation field: 'N' | Transaction not written; screen cleared; prompt re-displayed | no | BR-COTRN02C-12 |
| 13 | Confirmation required before write | happy-path | All fields valid | All fields submitted without confirmation value | Prompt message displayed requesting confirmation; transaction not written | no | BR-COTRN02C-12 |
| 14 | Transaction type code mandatory and numeric | error | Account/card validated | Transaction type code: blank | Rejected with mandatory-field error | no | BR-COTRN02C-19, BR-COTRN02C-30 |
| 15 | Merchant ID mandatory and numeric | error | Account/card validated | Merchant ID: blank or non-numeric | Rejected with appropriate error message | no | BR-COTRN02C-26, BR-COTRN02C-49 |
| 16 | Transaction ID is auto-generated; not supplied by user | happy-path | Transaction store has existing records | Successful confirmed add | Transaction ID displayed in success message is system-generated (highest existing + 1) | no | BR-COTRN02C-50 |
| 17 | Leap year date accepted as valid | boundary | Any state | Origination date: '2024-02-29' (valid leap year date) | Date accepted as valid | yes | BR-COTRN02C-46 |
| 18 | February 29 on non-leap year rejected | boundary | Any state | Origination date: '2023-02-29' (not a leap year) | Date rejected as invalid calendar date | yes | BR-COTRN02C-46 |
| 19 | Transaction list displays up to 10 transactions per page | happy-path | TRANSACT file has at least 10 records | User navigates to transaction list | Up to 10 transactions shown per page; each row shows transaction ID, date (MM/DD/YY), description, and signed amount | no | BR-COTRN00C-25 |
| 20 | PF8 pages forward to next page of transactions | happy-path | More than 10 transactions exist | PF8 pressed | Next 10 transactions displayed; page counter increments | no | BR-COTRN00C-22, BR-COTRN00C-24 |
| 21 | PF7 pages backward to previous page | happy-path | User has navigated past first page | PF7 pressed | Previous 10 transactions displayed; page counter decrements | no | BR-COTRN00C-33, BR-COTRN00C-36 |
| 22 | [KNOWN DEFECT] Invalid row selection code error message is overwritten by page refresh | error | Transaction list displayed | Selection code other than 'S' or 's' entered next to a row; Enter pressed | Error message 'Invalid selection. Valid value is S' set internally but both SEND-TRNLST-SCREEN and SET TRANSACT-EOF are commented out; page refreshes and overwrites the message; user sees a normal page re-display instead of the error | no | BR-COTRN00C-14, BR-COTRN00C-56 |
| 23 | STARTBR EQUAL match: non-existent transaction ID in filter returns top-of-page message | error | Transaction with supplied ID does not exist in TRANSACT | User enters a valid numeric transaction ID that does not exist in the file | Screen re-displayed with message 'You are at the top of the page...' (NOTFND treated as EOF); does NOT position at the nearest-matching record because GTEQ is disabled | no | BR-COTRN00C-18, BR-COTRN00C-19 |
| 24 | PF7 at first page suppresses backward scroll with informational message | happy-path | Transaction list showing first page (page counter = 1) | PF7 pressed | Message 'You are already at the top of the page...' displayed; screen not erased; list unchanged | no | BR-COTRN00C-31 |
| 25 | PF8 at last page suppresses forward scroll with informational message | happy-path | Transaction list showing last page | PF8 pressed | Message 'You are already at the bottom of the page...' displayed; screen not erased; list unchanged | no | BR-COTRN00C-21 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| TRAN-AMT | Transaction Amount | PIC S9(09)V99, signed decimal | Valid signed decimal with '+'/'-' prefix and decimal point at correct position; no sign (error); non-numeric parts (error) | -999999999.99, -0.01, +0.00, +0.01, +999999999.99 |
| TRAN-ORIG-TS | Origination Date | PIC X(26), YYYY-MM-DD in first 10 chars | Valid YYYY-MM-DD, invalid calendar date (error), wrong format (error), blank (error) | '1900-01-01', '2024-02-29' (leap), '9999-12-31', '2023-02-29' (non-leap error) |
| TRAN-TYPE-CD | Transaction Type Code | PIC X(02), numeric | Valid 2-digit numeric code, blank (error), non-numeric (error) | '00', '99' |
| TRAN-ID | Transaction ID | PIC X(16), auto-generated | System-assigned; not user-supplied | '0000000000000001', '9999999999999999' |

---

## Bill Payment Processing

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Bill Payment Processing |
| Source Rules | BR-COBIL00C-1 through BR-COBIL00C-34 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Successful full-balance payment | happy-path | Account exists; positive balance; transaction store has at least one existing record | Account ID: valid, confirmation: 'Y' | New payment transaction written with type '02' and amount equal to the full balance; account balance set to zero; success message with transaction ID displayed | no | BR-COBIL00C-14, BR-COBIL00C-16, BR-COBIL00C-24 |
| 2  | Payment rejected when account has zero balance | error | Account exists with balance of zero | Account ID: valid | Error message indicating nothing to pay; no transaction written | no | BR-COBIL00C-13 |
| 3  | Payment rejected when account has negative balance | error | Account exists with negative balance | Account ID: valid | Error message indicating nothing to pay; no transaction written | no | BR-COBIL00C-13 |
| 4  | Account ID is mandatory | error | Any state | Account ID: blank | Error message requiring account ID; no lookup performed | no | BR-COBIL00C-9 |
| 5  | Account not found returns error | error | Account ID does not exist in account store | Non-existent account ID | Error message indicating account not found | no | BR-COBIL00C error handling |
| 6  | Confirmation 'N' cancels payment | happy-path | Account ID valid; balance shown | Confirmation: 'N' | Screen cleared; payment not processed | no | BR-COBIL00C-11 |
| 7  | Confirmation required before posting | happy-path | Account ID valid; balance shown | Confirmation field: blank | Current balance displayed; prompt for confirmation shown; no payment posted | no | BR-COBIL00C-12, BR-COBIL00C-15 |
| 8  | Payment always clears full balance; partial payment not supported | happy-path | Account has positive balance of $5,432.10 | Account ID: valid, confirmation: 'Y' | Transaction amount equals exactly $5,432.10; account balance set to $0.00 | no | BR-COBIL00C-24 |
| 9  | Payment transaction always assigned type '02' and category 2 | happy-path | Successful payment | Valid account, confirmation: 'Y' | Transaction record in store has type code '02' and category code 2 | no | BR-COBIL00C-16, BR-COBIL00C-17 |
| 10 | PF4 clears screen without processing payment | happy-path | Account and balance displayed | PF4 pressed | Screen cleared; payment not processed | no | BR-COBIL00C-6 |
| 11 | Invalid confirmation value rejected | error | Account displayed | Confirmation: value other than Y, y, N, n, or blank | Error message indicating valid values are Y or N | no | BR-COBIL00C-10 |
| 12 | [KNOWN DEFECT] First-ever payment when transaction store is empty fails | error | Transaction store contains no records | First payment attempt on empty system | Payment fails with error indicating transaction ID not found; payment cannot be processed until at least one transaction exists | no | BR-COBIL00C-29 |
| 13 | [KNOWN DEFECT] Account balance zeroed even when transaction write fails due to duplicate ID | error | Transaction ID collision occurs (rare concurrent scenario) | Valid account with positive balance, confirmation 'Y', but transaction write encounters duplicate ID | Balance set to zero in account store despite no corresponding payment transaction being written; data inconsistency | no | BR-COBIL00C defect |
| 14 | Payment amount boundary: minimum positive balance ($0.01) | boundary | Account balance: $0.01 | Account ID: valid, confirmation: 'Y' | Payment of $0.01 processed; balance set to $0.00 | yes | BR-COBIL00C-13, BR-COBIL00C-24 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| ACCT-CURR-BAL | Account Current Balance | PIC S9(10)V99 | Positive (payment allowed), zero (rejected), negative (rejected) | -9999999999.99, -0.01, 0.00, 0.01, 9999999999.99 |
| TRAN-TYPE-CD | Payment Transaction Type | Always '02' for bill payment | '02' (bill payment); any other value indicates wrong transaction type | '02' |
| Confirmation Flag | Payment Confirmation | 'Y', 'y', 'N', 'n', blank | Y/y (proceed), N/n (cancel), blank (prompt), other (error) | 'Y', 'N', ' ', '?' |

---

## Daily Transaction Posting (Batch)

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Daily Transaction Posting (Batch) |
| Source Rules | BR-CBTRN02C-1 through BR-CBTRN02C-38 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Valid transaction posted to transaction store | happy-path | Card in cross-reference; account exists; transaction within credit limit; account not expired | Single valid daily transaction record | Transaction written to permanent transaction store; account balance updated; category balance updated; no reject written | no | BR-CBTRN02C-4, BR-CBTRN02C-21 through BR-CBTRN02C-25 |
| 2  | Card number not in cross-reference produces reason-100 reject | error | Card number not present in card/account cross-reference | Daily transaction record with invalid card number | Transaction not posted; reject record written with reason code 100 ('INVALID CARD NUMBER FOUND'); job return code set to 4 | no | BR-CBTRN02C-9, BR-CBTRN02C-6 |
| 3  | Account not found produces reason-101 reject | error | Card exists in cross-reference but resolved account ID not in account master | Daily transaction with valid card but no matching account | Transaction not posted; reject record with reason code 101 ('ACCOUNT RECORD NOT FOUND'); return code 4 | no | BR-CBTRN02C-13, BR-CBTRN02C-6 |
| 4  | Transaction exceeding credit limit produces reason-102 reject | error | Card and account exist; adding transaction amount to cycle net balance would exceed credit limit | Transaction amount that would push cycle net balance over credit limit | Transaction not posted; reject record with reason code 102 ('OVERLIMIT TRANSACTION'); return code 4 | no | BR-CBTRN02C-15, BR-CBTRN02C-6 |
| 5  | Transaction after account expiration produces reason-103 reject | error | Card and account exist; account expiration date is before the transaction origination date | Transaction origination date after account expiration | Transaction not posted; reject record with reason code 103 ('TRANSACTION RECEIVED AFTER ACCT EXPIRATION'); return code 4 | no | BR-CBTRN02C-17, BR-CBTRN02C-6 |
| 6  | When both overlimit and expiry conditions fail, reason 103 is recorded | error | Transaction fails both overlimit and expiry checks | Transaction that exceeds credit limit AND is after expiration date | Reject record records only reason code 103 (last failing check wins); reason 102 not visible in output | no | BR-CBTRN02C-20 |
| 7  | Overlimit check uses cycle-to-date balances only | happy-path | Account has large carry-forward balance from prior cycles but current cycle net is within limit | Transaction that would exceed total balance but not current-cycle net balance | Transaction accepted (not rejected for overlimit) | no | BR-CBTRN02C-16 |
| 8  | All-valid batch produces return code 0 | happy-path | All transactions valid | Daily transaction file with only valid transactions | All transactions posted; return code 0 | no | BR-CBTRN02C-6 |
| 9  | Mixed valid/invalid batch returns code 4 | happy-path | Mix of valid and invalid transactions | Daily transaction file with at least one reject | Valid transactions posted; invalid transactions in reject file; return code 4 | no | BR-CBTRN02C-5, BR-CBTRN02C-6 |
| 10 | New category balance record created when first transaction for type/category | happy-path | No existing category balance record for this account/type/category combination | First transaction for this combination | New category balance record created with amount of this transaction | no | BR-CBTRN02C-30 |
| 11 | Existing category balance record updated by adding transaction amount | happy-path | Category balance record already exists | Subsequent transaction for existing account/type/category | Category balance updated by adding new transaction amount | no | BR-CBTRN02C-31 |
| 12 | Processing timestamp always set from batch runtime clock | happy-path | Transaction input record contains a processing timestamp field | Valid transaction posted | TRAN-PROC-TS in output reflects batch execution time, not the timestamp from the input record | no | BR-CBTRN02C-38 |
| 13 | Transaction store truncated on each batch run | happy-path | Transaction store has records from prior run | Batch job executed | Prior contents of transaction store replaced by today's valid transactions only | no | BR-CBTRN02C-7 |
| 14 | Zero-record input file produces no output and return code 0 | boundary | Transaction store exists and is empty after open | Empty daily transaction input file | No records written; return code 0 | yes | BR-CBTRN02C-6 |
| 15 | Transaction amount boundary: maximum signed 9-digit value accepted | boundary | Valid card and account exist within limits | Transaction amount: +999999999.99 (if within credit limit) | Transaction accepted and posted | yes | BR-CBTRN02C-33 |
| 16 | [KNOWN DEFECT] Account rewrite failure sets internal reason code but does not produce reject record | error | Account rewrite fails after transaction is already written | Valid transaction that causes account REWRITE to fail | Transaction exists in permanent store; account balance not updated; no reject record written; no abend; data inconsistency | no | BR-CBTRN02C-36 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| DALYTRAN-CARD-NUM | Card Number | PIC X(16) | In cross-reference (valid), not in cross-reference (reason 100) | All spaces, valid 16-char, unknown card |
| DALYTRAN-AMT | Transaction Amount | PIC S9(09)V99 | Positive charge, negative payment/credit; overlimit (reason 102) | -999999999.99, -0.01, 0.00, +0.01, +999999999.99 |
| ACCT-EXPIRAION-DATE | Account Expiration Date | PIC X(10), CCYYMMDD | Not expired (valid), expired (reason 103) | Expiry = transaction date (edge), expiry 1 day before (reject) |
| WS-VALIDATION-FAIL-REASON | Reject Reason Code | PIC 9(04) | 0 (valid), 100 (bad card), 101 (bad account), 102 (overlimit), 103 (expired), 109 (account rewrite failure - defect) | 0, 100, 101, 102, 103 |

---

## Interest and Fees Calculation (Batch)

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Interest and Fees Calculation (Batch) |
| Source Rules | BR-CBACT04C-1 through BR-CBACT04C-38 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Monthly interest computed as annual rate divided by 1200 | happy-path | Category balance record exists; disclosure group rate record exists | Category balance of $1,200.00; annual rate of 24.00% | Monthly interest = $24.00 (1200 * 24 / 1200); interest transaction written | no | BR-CBACT04C-22, BR-CBACT04C-23 |
| 2  | Interest transaction written with system-generated transaction ID | happy-path | Category balance and rate exist | Any non-zero category balance with non-zero rate | Interest transaction written to transaction output with ID constructed from run date + suffix counter | no | BR-CBACT04C-25 |
| 3  | Interest transaction type code is always '01' | happy-path | Interest calculation triggered | Any valid account with interest to compute | Interest transaction record has type code '01' and category code '05' | no | BR-CBACT04C-26, BR-CBACT04C-27 |
| 4  | Zero-rate category produces no interest transaction | happy-path | Category balance exists; disclosure group rate is 0 | Category balance with 0% interest rate | No interest transaction written for this category; balance unchanged | no | BR-CBACT04C-12 |
| 5  | Fallback to DEFAULT disclosure group when specific group not found | happy-path | Account belongs to group with no specific rate; DEFAULT rate exists for same type/category | Category balance with account group having no disclosure group record | DEFAULT rate used for calculation; interest computed and posted | no | BR-CBACT04C-18, BR-CBACT04C-19 |
| 6  | Missing DEFAULT rate for type/category combination causes job abend | error | No DEFAULT disclosure group record for this transaction type and category | Category balance record where neither specific nor DEFAULT rate exists | Job abends; no partial output produced | no | BR-CBACT04C-21 |
| 7  | Missing account record causes job abend | error | Account ID referenced in cross-reference has no account master record | Category balance referencing a non-existent account | Job abends immediately; not a soft skip | no | BR-CBACT04C error handling |
| 8  | Cycle credit and debit balances zeroed after interest posting | happy-path | Account has non-zero cycle credit and debit balances | Interest calculation run completes for account | Account record updated with accumulated interest; cycle credit balance set to zero; cycle debit balance set to zero | no | BR-CBACT04C-35, BR-CBACT04C-36 |
| 9  | Interest accumulated across multiple categories before posting | happy-path | Account has multiple transaction category balance records | Multiple category balance records for same account with non-zero rates | Total interest for the account = sum of per-category monthly interests; single account update with total | no | BR-CBACT04C-23, BR-CBACT04C-34 |
| 10 | Interest rate boundary: zero rate produces no interest | boundary | Category balance exists | Annual interest rate: 0.00% | No interest transaction generated; no account update | yes | BR-CBACT04C-12 |
| 11 | Interest rate boundary: maximum rate | boundary | Category balance exists | Annual interest rate: 9999.99% (max S9(04)V99) | Interest calculated; if computation overflows S9(09)V99 result may be silently truncated | yes | BR-CBACT04C-22 |
| 12 | Fee computation stub produces no fees | happy-path | Any account processed | Any state | No fee transactions written; fee stub is inactive | no | BR-CBACT04C-38 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| DIS-INT-RATE | Annual Interest Rate | PIC S9(04)V99 | Zero (no interest), positive non-zero (interest computed), missing record (fallback or abend) | 0.00, 0.01, 9999.99 |
| TRAN-CAT-BAL | Category Balance | PIC S9(09)V99 | Positive, zero, negative | -999999999.99, 0.00, 999999999.99 |
| ACCT-GROUP-ID | Account Group ID | PIC X(10) | Group with specific rate, group with no specific rate (fallback to DEFAULT), 'DEFAULT' itself | Any 10-char string; 'DEFAULT' |

---

## Account Statement Generation (Batch)

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Account Statement Generation (Batch) |
| Source Rules | BR-CBSTM03A-*, BR-CBSTM03B-* |
| Confidence   | medium |

Note: Statement formatting details are inferred from code; no formal business specification was found in the analysed source. Scenarios cover observable input/output contracts.

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Statement generated for every card/account in cross-reference | happy-path | Cross-reference, account, customer, and transaction files all populated | Batch statement job executed | One statement section produced per card in the cross-reference; no cards skipped | no | BR-CBSTM03A-main |
| 2  | Statement includes account summary and customer details | happy-path | Account and customer records linked | Statement run for populated accounts | Each statement contains account balance, credit limit, and customer name and address | no | BR-CBSTM03A-main |
| 3  | Statement includes itemised transaction list | happy-path | Transactions present for the card | Statement run | Each transaction for the card period listed with amount, date, merchant details | no | BR-CBSTM03A-main |
| 4  | Both plain text and HTML formats produced | happy-path | Any populated data | Statement run | Plain text output file and HTML output file both written; neither is empty | no | BR-CBSTM03A-formats |
| 5  | Input transactions must be pre-sorted by card number before run | happy-path | Transactions in SORT step output are ordered by card number then transaction ID | Statement batch submitted after required SORT step | Statements correctly grouped by card; no transaction appears in the wrong card's statement | no | BR-CBSTM03A-sort |
| 6  | Account with no transactions produces statement body with no transaction lines | boundary | Account/card exists in cross-reference; no transactions for this card in sorted input | Statement run | Statement header and summary generated; transaction section is empty | yes | BR-CBSTM03A-main |
| 7  | [KNOWN DEFECT] Account balance >= $1,000,000,000.00 silently truncates leading digit in statement | error | Account with ACCT-CURR-BAL >= 1,000,000,000.00 exists | Statement batch run | Plain-text and HTML statements display a truncated balance value (leading integer digit dropped due to S9(10)V99 → Z(9).99- width mismatch); no error raised | no | BR-CBSTM03A-61 |
| 8  | [CAPACITY LIMIT] Statement batch fails or produces corrupted output when transaction input has more than 51 distinct card numbers | error | TRNXFILE sorted input contains > 51 distinct card numbers | Statement batch run | Array subscript CR-CNT overflows the 51-slot WS-CARD-TBL; behavior is undefined (possible abend or silent data corruption); verified safe below 51 cards | yes | BR-CBSTM03A-array |

---

## Transaction Report Generation (Batch)

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Transaction Report Generation (Batch) |
| Source Rules | BR-CBTRN03C-1 through BR-CBTRN03C-16 |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Report includes transaction type and category descriptions | happy-path | Transaction type and category reference data populated; all transactions within the date range | Sorted transaction file with mixed types; date parameter file with matching range | Report output includes human-readable type description (up to 15 chars) and category description (up to 29 chars) from reference tables next to each transaction | no | BR-CBTRN03C-10, BR-CBTRN03C-11 |
| 2  | Transactions are grouped by card number with per-card subtotal line | happy-path | Multiple transactions for at least two distinct card numbers within date range | In-range transaction file ordered by card number | Report groups all transactions for a given card number together; a subtotal line for each completed card group is printed at each card-number boundary | no | BR-CBTRN03C-4, BR-CBTRN03C-14 |
| 3  | Page break occurs every 20 lines; page total and headers repeat | happy-path | At least 21 in-range transaction detail lines to be written | Transaction file with sufficient in-range records | After every 20 written lines (including header and total lines), a page total line is written, then headers repeat on the next page; page total resets to zero | no | BR-CBTRN03C-6, BR-CBTRN03C-15 |
| 4  | Grand total written at end of report | happy-path | At least one in-range transaction | Any in-range transaction file | Grand total line written at end of report reflecting sum of all page totals | no | BR-CBTRN03C-16 |
| 5  | Date range parameters read from parameter file; only in-range transactions included | happy-path | DATE-PARMS-FILE present; contains valid start and end dates in YYYY-MM-DD format | Parameter file with start date '2024-01-01' and end date '2024-01-31'; transaction file with records inside and outside that range | Report contains only transactions whose processing timestamp date component falls within [start, end] | no | BR-CBTRN03C-1, BR-CBTRN03C-3 |
| 6  | Unknown transaction type code causes job abend | error | TRANTYPE reference file does not contain an entry for a code used in a transaction | Transaction with an unrecognised type code within the date range | Job abends with message 'INVALID TRANSACTION TYPE'; processing halts | no | BR-CBTRN03C error handling |
| 7  | Unknown transaction category combination causes job abend | error | TRANCATG reference file does not contain an entry for a type/category pair used in a transaction | Transaction with an unrecognised type/category combination within the date range | Job abends with message 'INVALID TRAN CATG KEY'; processing halts | no | BR-CBTRN03C error handling |
| 8  | Card number not in cross-reference causes job abend | error | XREF-FILE does not contain the card number on a transaction | Transaction with an unrecognised card number within the date range | Job abends with message 'INVALID CARD NUMBER'; processing halts | no | BR-CBTRN03C-9 |
| 9  | [KNOWN DEFECT] First out-of-range transaction encountered causes all subsequent transactions to be skipped | error | Transaction file contains a mix of in-range and out-of-range records; an out-of-range record appears before the last in-range record | Date parameter range that does not cover all records; out-of-range record encountered mid-file | Report is incomplete: all transactions following the first out-of-range record are absent from the report regardless of their dates; no error raised | no | BR-CBTRN03C-2 |
| 10 | [KNOWN DEFECT] Final page total and grand total are corrupted by stale buffer value at end-of-file | error | Transaction file with at least one in-range record | Normal in-range transaction file; batch run proceeds to EOF | Final page total and grand total reflect an additional arbitrary amount from the stale record buffer at EOF; totals do not match the sum of reported transactions | no | BR-CBTRN03C calculations (EOF anomaly) |
| 11 | [KNOWN DEFECT] Account total not written for the last card group in the report | error | Transaction file with at least two distinct card numbers in range | Two or more card numbers with transactions in range; last card group has at least one transaction | All card groups except the final one receive a per-card subtotal line; the final card group's transactions are included in the grand total but no per-card subtotal line appears | no | BR-CBTRN03C-14 note |
| 12 | Date parameter file missing or unreadable causes job abend | error | DATE-PARMS-FILE unavailable on job start | Batch job run without DATE-PARMS-FILE | Job abends; no report output produced | no | BR-CBTRN03C error handling |
| 13 | Empty transaction input file produces report with headers and grand total only | boundary | DATE-PARMS-FILE present; TRANSACT-FILE contains no records | Empty transaction file | Report headers written; no detail lines; grand total of zero written; job completes with return code 0 | yes | BR-CBTRN03C-1, BR-CBTRN03C-16 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| WS-START-DATE / WS-END-DATE | Report Date Range | PIC X(10), YYYY-MM-DD | Valid date range (end >= start), invalid date string (error), empty parameter file (abend) | '0001-01-01', '9999-12-31', same start and end date |
| TRAN-PROC-TS(1:10) | Transaction Date Component | First 10 chars of PIC X(26) timestamp | Within range (included), before start (excluded or defect), after end (excluded or defect) | Exactly start date, exactly end date |
| WS-PAGE-SIZE | Lines Per Page | VALUE 20 (fixed literal) | Always 20; cannot be parameterised | 20 |

---

## User Administration

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | User Administration |
| Source Rules | BR-COUSR01C-1 through BR-COUSR01C-28, BR-COUSR02C-*, BR-COUSR03C-*, BR-COUSR00C-* |
| Confidence   | high |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | New user added with all mandatory fields | happy-path | User ID does not already exist | First name, last name, user ID, password, user type all supplied | User record written to security store; success message with user ID displayed | no | BR-COUSR01C-13, BR-COUSR01C-20 |
| 2  | Add user rejected when first name is blank | error | Any state | First name: blank | Rejected with message that first name cannot be empty | no | BR-COUSR01C-8 |
| 3  | Add user rejected when last name is blank | error | Any state | Last name: blank | Rejected with message that last name cannot be empty | no | BR-COUSR01C-9 |
| 4  | Add user rejected when user ID is blank | error | Any state | User ID: blank | Rejected with message that user ID cannot be empty | no | BR-COUSR01C-10 |
| 5  | Add user rejected when password is blank | error | Any state | Password: blank | Rejected with message that password cannot be empty | no | BR-COUSR01C-11 |
| 6  | Add user rejected when user type is blank | error | Any state | User type: blank | Rejected with message that user type cannot be empty | no | BR-COUSR01C-12 |
| 7  | Duplicate user ID rejected | error | User with same ID already exists | All fields valid; user ID: existing ID | Rejected with message indicating user ID already exists | no | BR-COUSR01C-21, BR-COUSR01C-22 |
| 8  | User type accepts any non-blank single character | happy-path | User ID does not exist | User type: single character other than 'A' or 'U' (e.g., 'X') | User record created with user type value as supplied; no domain validation error | no | BR-COUSR01C-12 note |
| 9  | User list accessible only to admin users | happy-path | Admin user authenticated | Admin user navigates to user list | User list displayed | no | Capability BR-11 |
| 10 | User update modifies existing user record | happy-path | User exists; valid changes supplied | Valid changes submitted and confirmed | User record updated in security store | no | BR-COUSR02C-update |
| 11 | User delete requires confirmation via PF5 | happy-path | User record exists; user navigated to delete screen | PF5 pressed on delete confirmation screen | User record deleted from security store | no | BR-COUSR03C-pf5 |
| 12 | User ID boundary: maximum 8 characters accepted | boundary | No existing user with this ID | User ID: exactly 8 characters | User record created; lookup key is exactly 8 bytes | yes | BR-COUSR01C-14 |
| 13 | Password stored as plaintext without transformation | happy-path | New user added | Password: 'MYPASS01' | Password stored verbatim in security store (no hashing); authenticating with this password succeeds | no | Capability BR-11 plaintext note |
| 14 | [KNOWN DEFECT] PF3 from user update screen navigates away unconditionally regardless of update outcome | error | User update screen displayed with pending changes | PF3 pressed when a mandatory field is blank | Update validation fires (error screen briefly rendered) but program unconditionally XCTLs to prior screen; user never sees the error; save may or may not have occurred | no | BR-COUSR02C-5 |
| 15 | User update PF5 stays on screen; distinguishable from PF3 unconditional-navigate behavior | happy-path | User update screen with valid changes | PF5 pressed | Changes saved if valid; screen stays open with success or error message; no navigation away | no | BR-COUSR02C-8 |
| 16 | User list displays up to 10 users per page with user ID, first name, last name, and user type | happy-path | USRSEC file has at least one user record | Admin user navigates to user list | Up to 10 users shown per page; each row shows user ID, first name, last name, user type | no | BR-COUSR00C-30 |
| 17 | PF8 pages forward through user list | happy-path | More than 10 user records exist | PF8 pressed | Next page of users displayed; page counter increments | no | BR-COUSR00C-26, BR-COUSR00C-23 |
| 18 | PF7 pages backward through user list | happy-path | User has navigated past first page | PF7 pressed | Previous page of users displayed; page counter decrements | no | BR-COUSR00C-22, BR-COUSR00C-34 |
| 19 | PF7 at first page shows 'already at top' message without scrolling | happy-path | User list on first page (page counter <= 1) | PF7 pressed | Message 'You are already at the top of the page...' displayed; list not scrolled | no | BR-COUSR00C-21 |
| 20 | PF8 at last page shows 'already at bottom' message without scrolling | happy-path | User list showing last page (NEXT-PAGE-NO) | PF8 pressed | Message 'You are already at the bottom of the page...' displayed; list not scrolled | no | BR-COUSR00C-25 |
| 21 | 'U' selection on a row navigates to user update screen | happy-path | User list displayed | Action code 'U' or 'u' entered on a row; Enter pressed | XCTL to COUSR02C with selected user ID in commarea | no | BR-COUSR00C-11 |
| 22 | 'D' selection on a row navigates to user delete confirmation screen | happy-path | User list displayed | Action code 'D' or 'd' entered on a row; Enter pressed | XCTL to COUSR03C with selected user ID in commarea | no | BR-COUSR00C-12 |
| 23 | Invalid selection code (not U, u, D, or d) shows error message | error | User list displayed | Action code other than U/u/D/d entered on a row | Error message 'Invalid selection. Valid values are U and D' displayed; no XCTL performed | no | BR-COUSR00C-13 |
| 24 | User delete confirmation screen pre-populates user details from USRSEC for review | happy-path | User record exists; COUSR03C invoked from COUSR00C with pre-selected user | User ID passed from COUSR00C | Confirmation screen displayed with user first name, last name, and user type pre-loaded; prompt 'Press PF5 key to delete this user ...' shown | no | BR-COUSR03C-4, BR-COUSR03C-20 |
| 25 | User not found during delete lookup shows error; delete not performed | error | User ID does not exist in USRSEC | Enter key pressed with user ID that does not exist | Error message 'User ID NOT found...'; confirmation screen re-displayed with cursor on user ID field; no deletion | no | BR-COUSR03C-21 |
| 26 | PF5 confirms and executes delete; success message shown and screen cleared | happy-path | User exists; confirmation screen displayed; PF5 pressed | PF5 pressed | User record deleted from USRSEC; success message 'User [ID] has been deleted ...' shown in green; all fields cleared for next deletion | no | BR-COUSR03C-8, BR-COUSR03C-23, BR-COUSR03C-24 |
| 27 | [KNOWN DEFECT] DELETE issued even when preceding READ UPDATE fails | error | Record not found or CICS error on READ UPDATE before PF5 | PF5 pressed to delete; READ UPDATE returns NOTFND or error | ERR-FLG-ON is set by READ-USER-SEC-FILE; however, because the guard is evaluated only once before both PERFORMs, DELETE-USER-SEC-FILE still executes; DELETE with no RIDFLD and no prior READ UPDATE lock produces a CICS error; functionally harmless (no record deleted) but causes an extra unnecessary CICS call | no | BR-COUSR03C-15 |
| 28 | PF4 clears the delete confirmation screen without performing deletion | happy-path | Delete confirmation screen displayed | PF4 pressed | All fields cleared; empty delete form re-displayed; no deletion | no | BR-COUSR03C-7, BR-COUSR03C-27 |
| 29 | PF3 exits to calling program without deleting | happy-path | Delete confirmation screen displayed | PF3 pressed | XCTL back to the program that invoked COUSR03C (COUSR00C) or to COADM01C if none; no deletion | no | BR-COUSR03C-6 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| SEC-USR-ID | User ID | PIC X(08) | Non-blank (valid), blank (error), duplicate (error) | 1-char, 8-char (max) |
| SEC-USR-PWD | Password | PIC X(08) | Non-blank (valid), blank (error) | 1-char, 8-char (max) |
| SEC-USR-TYPE | User Type | PIC X(01) | Non-blank (any value accepted at entry), blank (error); 'A' routes to admin, other routes to regular menu | 'A', 'U', 'X', ' ' |

---

## Report Request (Online to Batch)

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Report Request (Online to Batch) |
| Source Rules | BR-CORPT00C-* |
| Confidence   | medium |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Valid date range submits batch report job | happy-path | JES internal reader queue available; date validation service available | Valid start date and end date in YYYY-MM-DD format | JCL records written to internal reader queue; confirmation message displayed; batch job submitted asynchronously | no | BR-CORPT00C-submit |
| 2  | Invalid start date rejected | error | Any state | Start date: '2024-13-01' (invalid month) | Rejected with date validation error; no JCL submitted | no | BR-CORPT00C-datevalidation |
| 3  | Invalid end date rejected | error | Any state | End date: '2024-02-30' | Rejected with date validation error; no JCL submitted | no | BR-CORPT00C-datevalidation |
| 4  | Report job runs asynchronously; no result returned online | happy-path | Batch job submitted successfully | Confirmation screen shown | No report output displayed online; user must check batch output separately | no | BR-CORPT00C-async |
| 5  | Leap year boundary date accepted | boundary | Any state | Date: '2024-02-29' | Date accepted as valid by date validation service | yes | BR-CORPT00C-datevalidation |

---

## Data Migration Export and Import

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Data Migration Export and Import |
| Source Rules | BR-CBEXPORT-*, BR-CBIMPORT-* |
| Confidence   | medium |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Export produces multi-record file with all record types | happy-path | All operational VSAM files populated | Export job executed | Export file contains customer records (type 'C'), account records (type 'A'), cross-reference records (type 'X'), transaction records (type 'T'), and card records (type 'D') | no | BR-CBEXPORT-main |
| 2  | Export preserves all records without filtering | happy-path | Operational files have known record counts | Export run | Record count in export file equals sum of records from all source files | no | BR-CBEXPORT-nofilter |
| 3  | Import splits export file into normalised output by record type | happy-path | Valid export file from CBEXPORT | Import job executed | Customer, account, cross-reference, and transaction records written to separate sequential output files | no | BR-CBIMPORT-split |
| 4  | Import validates checksums and reports errors to error file | error | Export file contains a record with corrupted checksum | Import executed | Corrupted record written to error output file; valid records written to appropriate output files | no | BR-CBIMPORT-checksum |
| 5  | [KNOWN DEFECT] Card output file missing from import job definition | error | Export file contains card records (type 'D') | Import job executed | Card records may fail silently or cause job abend due to missing output DD definition; other record types unaffected | no | BR-CBIMPORT card defect |
| 6  | Export sequence numbers auto-assigned | happy-path | Multiple records in source files | Export run | Each record in export file has a unique auto-assigned sequence number | no | BR-CBEXPORT-sequence |

---

## Reference Data Utility Operations (Batch Diagnostics)

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Reference Data Utility Operations (Batch Diagnostics) |
| Source Rules | BR-CBACT01C-1 through BR-CBACT01C-43, BR-CBACT02C-*, BR-CBACT03C-*, BR-CBCUS01C-*, BR-CBTRN01C-* |
| Confidence   | medium |

Note: These programs are diagnostic utilities that read VSAM master file contents and produce derived output files or SYSOUT listings. CBACT01C additionally writes three distinct output file formats per account record. Test scenarios focus on correct output production and known behavioral anomalies.

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Account file diagnostic writes all account records to three output files | happy-path | Account file has known number of records | Account diagnostic batch program executed against populated account file | All account records written to fixed-length sequential output file, fixed-length array record file, and variable-length record file; record counts match source | no | BR-CBACT01C-10, BR-CBACT01C-19 |
| 2  | Account output ZIP code field is silently excluded from all three output formats | happy-path | Account records exist with ZIP code values | Account diagnostic batch executed | Output files contain all account fields except ZIP code; ZIP code value is not present in any output record; no error raised | no | BR-CBACT01C-15 |
| 3  | Zero cycle debit in account record is replaced by default value 2525.00 in fixed output | happy-path | Account record exists with cycle debit amount of exactly zero | Account diagnostic batch executed | Fixed output file record for that account has cycle debit value 2525.00; the zero from the source record is not preserved | no | BR-CBACT01C-17 |
| 4  | [KNOWN DEFECT] Non-zero cycle debit is NOT copied to fixed output record; prior buffer value retained | error | Account record exists with non-zero cycle debit; prior account in processing had a different cycle debit | Account diagnostic batch executed with account having non-zero cycle debit | Fixed output record for the non-zero-debit account has the cycle debit value from the previous account's buffer rather than its own cycle debit; data is incorrect but no error is raised | no | BR-CBACT01C-18 |
| 5  | Reissue date converted from YYYY-MM-DD to YYYYMMDD format in fixed output | happy-path | Account record with reissue date in YYYY-MM-DD format | Account diagnostic batch executed | Fixed output record contains reissue date in YYYYMMDD format (no hyphens); date value is semantically identical | no | BR-CBACT01C-16 |
| 6  | Variable-length record file receives two record types per account: type-1 (12 bytes) and type-2 (39 bytes) | happy-path | Account file with at least one record | Account diagnostic batch executed | Variable-length output file contains two records per source account: a 12-byte record with account ID and active status, and a 39-byte record with account ID, balance, credit limit, and reissue year | no | BR-CBACT01C-31, BR-CBACT01C-32, BR-CBACT01C-37, BR-CBACT01C-39 |
| 7  | Card file diagnostic prints all card records to SYSOUT | happy-path | Card file populated | Card file diagnostic executed | All card records printed to SYSOUT output; record count matches source file | no | BR-CBACT02C-main |
| 8  | Customer file diagnostic prints all customer records to SYSOUT | happy-path | Customer file populated | Customer file diagnostic executed | All customer records printed to SYSOUT output; record count matches source file | no | BR-CBCUS01C-main |
| 9  | Transaction dry-run validates each daily transaction without posting to any store | happy-path | DALYTRAN file populated; cross-reference and account files available | CBTRN01C executed | Validation results logged to SYSOUT; no changes to transaction store; no changes to account balances; no category balance records created or modified | no | BR-CBTRN01C-dryrun |
| 10 | Empty account file produces zero records in all three output files | boundary | Account file has no records | Account diagnostic executed against empty account file | All three output files contain zero records; batch completes normally; no abend | yes | BR-CBACT01C-11, BR-CBACT01C-13 |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| ACCT-CURR-CYC-DEBIT | Cycle Debit Amount | PIC S9(10)V99 | Zero (replaced by 2525.00 in output), non-zero (NOT copied -- prior buffer retained; known defect) | 0.00, 0.01, -0.01 |
| ACCT-REISSUE-DATE | Card Reissue Date | PIC X(10), YYYY-MM-DD | Valid date (converted to YYYYMMDD in output), spaces/zeros (passed through conversion service) | '0001-01-01', '9999-12-31' |
| WS-RECD-LEN | Variable Record Length | Literal values 12 or 39 | 12 (VBR1 type), 39 (VBR2 type) | 12, 39 |

---

## Batch Job Sequencing Utility

### Overview

| Property     | Value |
| ------------ | ----- |
| Capability   | Batch Job Sequencing Utility |
| Source Rules | BR-COBSWAIT-* |
| Confidence   | low |

### Scenarios

| #  | Scenario | Category | Preconditions | Input | Expected Output | Boundary | Source Rules |
| -- | -------- | -------- | ------------- | ----- | --------------- | -------- | ------------ |
| 1  | Program completes after specified centisecond delay | happy-path | SYSIN DD present | 8-digit centisecond duration (e.g., '00000100' for 1 second) | Program sleeps for specified duration then terminates normally with return code 0 | no | BR-COBSWAIT-main |
| 2  | Minimum wait duration (zero centiseconds) | boundary | SYSIN DD present | '00000000' (zero) | Program terminates immediately with return code 0 | yes | BR-COBSWAIT-main |
| 3  | Maximum wait duration | boundary | SYSIN DD present | '99999999' (maximum PIC 9(08)) | Program sleeps for maximum duration then terminates normally | yes | BR-COBSWAIT-main |

### Data Equivalence Classes

| Field | Business Name | Valid Range | Equivalence Classes | Boundary Values |
| ----- | ------------- | ----------- | ------------------- | --------------- |
| SYSIN wait value | Wait Duration (centiseconds) | PIC 9(08), 0 to 99999999 | Valid numeric 8-digit, non-numeric (undefined behavior - no error handling), blank (undefined) | 0, 1, 99999999 |

---

## Cross-Capability Scenarios

End-to-end tests that span multiple capabilities, verifying correct behavior across capability boundaries:

| #  | Scenario | Capabilities Involved | Preconditions | Input | Expected Output | Source Rules |
| -- | -------- | --------------------- | ------------- | ----- | --------------- | ------------ |
| 1  | Daily transaction batch feed followed by interest calculation | Daily Transaction Posting, Interest and Fees Calculation | Account and cross-reference files populated; DALYTRAN feed prepared | Run daily transaction posting batch (post transactions), then interest calculation batch (compute interest) | Transactions posted update category balance file; interest calculation batch reads category balances, computes interest, writes interest transactions, and zeros cycle balances | BR-CBTRN02C-23, BR-CBACT04C-1, BR-CBACT04C-35 |
| 2  | Online bill payment followed by account balance inquiry | Bill Payment Processing, Account Inquiry and Update | Account with positive balance; at least one prior transaction exists | Online user pays bill (balance cleared to zero); then account inquiry performed | Account inquiry shows balance of $0.00; payment transaction visible in transaction store with type '02' | BR-COBIL00C-14, BR-COBIL00C-24, BR-COACTVWC-read |
| 3  | Manual transaction add followed by transaction report | Transaction Inquiry and Manual Entry, Transaction Report Generation | Transaction store populated; reference data available | Manual transaction added; batch report job submitted and run with date range covering the added transaction | New transaction appears in report output with correct type and category descriptions from reference data | BR-COTRN02C-52, BR-CBTRN03C-10, BR-CBTRN03C-11 |
| 4  | User created by admin then signs in | User Administration, User Authentication and Session Management | Admin user authenticated | Admin adds new user with type 'U'; new user then signs in at sign-on screen | New user can authenticate; routed to standard (non-admin) menu | BR-COUSR01C-13, BR-COUSR01C-20, BR-COSGN00C-12, BR-COSGN00C-14 |
| 5  | Export then import preserves data integrity | Data Migration Export and Import | All operational VSAM files fully populated | Export job executed; then import job executed on the export file | Customer, account, cross-reference, and transaction record counts in import output files equal corresponding source file record counts; customer IDs, account IDs, and card numbers round-trip without corruption | BR-CBEXPORT-main, BR-CBIMPORT-split |
| 6  | Posted batch transactions appear in online transaction browse | Daily Transaction Posting, Transaction Inquiry and Manual Entry | Valid DALYTRAN feed processed by transaction posting batch | Transaction posting batch completes; online user browses transaction list | Transactions posted by the batch appear in online browse; transaction details match posted records | BR-CBTRN02C-25, BR-COTRN00C-browse |
| 7  | Account update followed by statement generation reflects new data | Account Inquiry and Update, Account Statement Generation | Account and customer exist; statement batch not yet run | Account holder's name updated via account update function; statement batch then run | Account statement reflects updated customer name in the customer details section | BR-COACTUPC-111, BR-CBSTM03A-main |
| 8  | Transaction report generation date filter defect: transactions sorted with out-of-range records interleaved | Transaction Report Generation, Daily Transaction Posting | Transaction store contains in-range and out-of-range records interleaved; date parameter file provided | Report batch run with date range that excludes some records appearing before the last in-range record | Due to NEXT SENTENCE defect, report is cut short at the first out-of-range record; in-range transactions after that point are absent; totals are incorrect | BR-CBTRN03C-2, BR-CBTRN03C-3 |
