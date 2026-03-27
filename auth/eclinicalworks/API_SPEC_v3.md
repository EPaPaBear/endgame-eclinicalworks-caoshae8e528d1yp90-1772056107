# eClinicalWorks Integration API Spec

Platform: `caoshae8e528d1yp90app.ecwcloud.com`

## Invocation

All requests go to the **Endgame backend** (not the eClinicalWorks platform URL).

```
POST https://api.integuru.ai/integrations/invoke
Authorization: Bearer <API key>
Content-Type: application/json

{
  "integration_id": "<uuid>",
  "account_id": "<uuid>",
  "input": {
    "action": "<action-name>",
    ...action-specific fields...
  }
}
```

**Example (curl) — read patient demographics:**
```bash
curl -X POST "https://api.integuru.ai/integrations/invoke" \
  -H "Authorization: Bearer egm_..." \
  -H "Content-Type: application/json" \
  -d '{
    "integration_id": "10e5714d-76bb-4f91-906a-f93bf5c75bbe",
    "account_id": "98c16453-be1f-4c9f-b942-dcdfa8e526f3",
    "input": {
      "action": "read",
      "patient_id": "298724"
    }'
```

## Integrations

| Integration | ID | Purpose |
|---|---|---|
| `ecw_demographics` | `65afea2f-a46b-40f9-b831-abdb21b01738` | Patient demographics, contacts, providers, sliding fee |
| `ecw_sfdp` | `c38fcfb6-4848-4443-88b3-dcec9e0e5f8f` | Sliding fee workflows, insurance management, scenarios |
| `ecw_create_patient` | `2f0ae558-0b1a-4b75-af7a-1f72cf1aa44c` | Create new patient via Quick Registration |

## IDs & Resources

| Resource | Value |
|----------|-------|
| Platform ID | `06230071-c18e-4b99-9a28-948f9c0bb8dc` |
| Account ID | `98c16453-be1f-4c9f-b942-dcdfa8e526f3` |
| Username | `wedge.ai` |
| Password | `**************` |
| Login URL | `https://caoshae8e528d1yp90app.ecwcloud.com` |
| 2FA Method | `email` (push notification — verify link, not numeric code) |
| 2FA Email | `a68c8f5f3b12@inbox.integuru.ai` |
| Repo | `EPaPaBear/endgame-eclinicalworks-caoshae8e528d1yp90-1772056107` |
| Chat Session ID | `42a8c5c6-5dfc-4259-9039-2d6f2ee2a6f5` |

### Test Patient

| Field | Value |
|-------|-------|
| Name | Test Wedge |
| Patient ID | `298724` |
| DOB | 07/07/2000 |
| SSN | 123-45-6789 |
| Doctor | `1st, Attempt` (ID: 254134) |

---

# ecw_demographics

## Common Fields

Every request requires:

| Field | Type | Required | Description |
|---|---|---|---|
| `action` | string | **Yes** | Action to perform |
| `patient_id` | string | **Yes** | eCW patient ID (e.g. `"298724"`) |

---

## Actions

### `edit-demographics`

Read-modify-write: reads the current record, merges your changes, and saves. Everything goes inside `changes` — only include fields you want to change, everything else is preserved.

**Input:**
```json
{
  "integration_id": "<uuid>",
  "account_id": "<uuid>",
  "input": {
    "action": "edit-demographics",
    "patient_id": "298724",
    "changes": {
      "fname": "Jane",
      "lname": "Doe",
      "phone": "555-123-1111",
      "maritalstatus": "Married",
      "language": "English",
      "race": "Asian",
      "sogi_data": {
        "birthsex": "F",
        "transgender": "N",
        "so_id": 5,
        "gi_ids": [2],
        "pp_ids": [3],
        "birthsex_changed": true,
        "transgender_changed": true
      },
      "parent_data": {
        "Mom1": "Mary Smith",
        "Mom1Ph": "555-123-4567",
        "Dad1": "John Smith"
      },
      "income_data": {
        "Income": "50000",
        "Dependants": "4",
        "Unit": "Annual"
      },
      "GrId": "298724",
      "GrRel": "1",
      "IsGrPt": "1"
    }
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `changes` | object | **Yes** | Dict of field names to new values. Only changed fields needed. |

**Personal info fields** (inside `changes`):

| Field | Type | Description |
|---|---|---|
| `fname` | string | First name |
| `lname` | string | Last name |
| `mname` | string | Middle name |
| `PreferredName` | string | Preferred name / nickname |
| `PreviousName` | string | Previous / maiden name |
| `prefix` | `""` `"Mr."` `"Mrs."` `"Ms."` `"Dr."` | Name prefix |
| `suffix` | `""` `"Jr."` `"Sr."` `"II"` `"III"` `"IV"` | Name suffix |
| `dob` | `MM/DD/YYYY` | Date of birth |
| `tob` | time | Time of birth |
| `sex` | `"Male"` `"Female"` `"Unknown"` | Administrative sex |
| `ssn` | `999-99-9999` | Social security number |
| `status` | `"0"` Active, `"1"` Inactive, `"2"` Deceased | Patient status |
| `gestationalAge` | string | Gestational age |
| `tob` | time | Time of birth |
| `primaryServiceLocation` | string | Service location ID |
| `mflag` | string | Home phone message flag (legacy field, prefer `phonePreferences`) |
| `HomeMsgType` | string | Home phone leave message type (legacy field, prefer `phonePreferences`) |
| `CellMsgType` | string | Cell phone leave message type (legacy field, prefer `phonePreferences`) |
| `WorkMsgType` | string | Work phone leave message type (legacy field, prefer `phonePreferences`) |

> **Phone preferences:** Voice/Text checkboxes, leave message settings, and extensions are now writable via `phonePreferences` inside `changes`. See [Phone Preferences](#phone-preferences-via-edit-demographics) section.
| `SsnReason` | string | SSN reason code |
| `SsnReasonNotes` | string | SSN reason notes |

**Contact fields** (inside `changes`):

| Field | Type | Description |
|---|---|---|
| `phone` | `999-999-9999` | Home phone |
| `mobile` | `999-999-9999` | Cell phone |
| `workPhone` | `999-999-9999` | Work phone (shows in Manage Phone List) |
| `workPhoneExt` | string | Work phone extension (digits/hyphens only) |
| `email` | string | Patient email |
| `emailReason` | string | Email opt-out reason code |
| `phonePreferences` | object | Phone contact preferences — see [Phone Preferences](#phone-preferences-via-edit-demographics) section below |

**Address fields** (inside `changes`):

| Field | Type | Description |
|---|---|---|
| `address1` | string | Street address line 1 |
| `address2` | string | Street address line 2 |
| `city` | string | City |
| `state` | 2-letter code (`"CA"`, `"NY"`) | State |
| `zip` | `"90210"` or `"90210-1234"` | ZIP code |
| `Country` | 2-letter code (`"US"`) | Country |

**Demographics fields** (inside `changes`):

| Field | Type | Description |
|---|---|---|
| `maritalstatus` | `"Single"` `"Married"` `"Divorced"` `"Widowed"` `"Separated"` `"Life Partner"` `"Legally Separated"` `"Unknown"` | Marital status (also accepts `maritalStatus`) |
| `race` | `"White"` `"Asian"` `"Asian,White"` or `[{name, code, id}]` | Race — pass display name(s), comma-separated for multiple, or array of objects. Auto-resolved via LRTE |
| `language` | `"English"` `"Spanish"` `"French"` `"Chinese"` `"Vietnamese"` etc. | Language — pass the display name, auto-looked up. Auto-sets translator for non-English |
| `Ethnicity` | `"Hispanic or Latino"` `"Not Hispanic or Latino"` | Ethnicity — pass the display name, auto-looked up |
| `TransGender` | `"Y"` or `"N"` | Transgender flag |
| `Translator` | `"0"` or `"1"` | Needs translator |
| `BirthOrder` | `""` `"1"` `"2"` etc. | Birth order (for multiples) |
| `VFC` | string | VFC eligibility |

**Employment fields** (inside `changes`):

| Field | Type | Description |
|---|---|---|
| `empName` | string | Employer name |
| `empAddress` | string | Employer address |
| `empCity` | string | Employer city |
| `empState` | 2-letter code | Employer state |
| `empZip` | ZIP | Employer ZIP |
| `empPhone` | phone | Employer phone |
| `empId` | string | Employer ID |
| `empAddress2` | string | Employer address line 2 |
| `EmpStatus` | `"1"` Employed full-time, `"2"` Employed part-time, `"3"` Not employed, `"4"` Self-employed, `"5"` Retired, `"6"` On active military duty, `"9"` Unknown | Employment status |
| `StudentStatus` | `"F"` Full-time, `"P"` Part-time, `"N"` Not a student | Student status |
| `StAddress` | string | Student address |
| `StAddress2` | string | Student address line 2 |
| `stCity` | string | Student city |
| `stState` | string | Student state |
| `stZip` | string | Student ZIP |
| `stCountry` | string | Student country |

**Provider fields** (inside `changes`):

| Field | Type | Description |
|---|---|---|
| `doctorId` | provider ID | Primary care physician (use `search-provider` action to find IDs) |
| `refPrId` | provider ID | Referring provider |
| `rendPrId` | provider ID | Rendering provider |

**Responsible party / guarantor fields** (inside `changes`). For "Self", pass the patient's own ID as `GrId`:

| Field | Type | Description |
|---|---|---|
| `GrId` | patient ID | Guarantor patient ID |
| `GrRel` | `"1"` Self, `"2"` Spouse, `"3"` Parent | Relationship to patient |
| `IsGrPt` | `"0"` or `"1"` | Is the guarantor a patient in the system |

**`sogi_data`** — Sexual Orientation, Gender Identity, and Pronouns. Use `read-sogi` action first to get option lists with IDs.

```json
"sogi_data": {
  "birthsex": "F",
  "transgender": "N",
  "so_id": 5,
  "gi_ids": [2],
  "pp_ids": [3]
}
```

| Field | Type | Description |
|---|---|---|
| `birthsex` | `"M"` `"F"` `""` | Sex assigned at birth |
| `transgender` | `"Y"` or `"N"` | Transgender status |
| `so_id` | integer | Sexual orientation ID (from `read-sogi` → `so_list`) |
| `gi_ids` | list of integers | Gender identity IDs (from `read-sogi` → `gi_list`). Supports multiple |
| `pp_ids` | list of integers | Pronoun IDs (from `read-sogi` → `pp_list`). Supports multiple |
| `so_reason` | string | Reason for SO selection |
| `gi_reason` | string | Reason for GI selection |
| `pp_reason` | string | Reason for pronoun selection |
| `so_date` | `MM/YYYY` | Date for SO |
| `gi_date` | `MM/YYYY` | Date for GI |
| `so_changed` | boolean | SO was modified (default `true`) |
| `gi_changed` | boolean | GI was modified (default `true`) |
| `pp_changed` | boolean | Pronouns were modified (default `true`) |
| `birthsex_changed` | boolean | Birth sex was modified (default `false`) |
| `transgender_changed` | boolean | Transgender was modified (default `false`) |

> **Important:** `so_changed`, `gi_changed`, and `pp_changed` default to `true`. Any SOGI field you **omit** will be **cleared** unless you explicitly set its `*_changed` to `false`. To update only specific fields while keeping others unchanged:
> ```json
> "sogi_data": {
>   "birthsex": "M",
>   "transgender": "Y",
>   "so_changed": false,
>   "gi_changed": false,
>   "pp_ids": "3"
> }
> ```
> This updates birthsex, transgender, and pronouns, but leaves sexual orientation and gender identity untouched.

**`parent_data`** — Mother, father, and other guardian info. Only include fields you want to change. Field names are ECW's internal names (e.g. `Mom1`, not `motherFirstName`).

```json
"parent_data": {
  "Mom1": "Mary Smith",
  "Mom1Ph": "555-123-4567",
  "Mom1Email": "mary@example.com",
  "Dad1": "John Smith",
  "Dad1Ph": "555-987-6543",
  "Dad1Email": "john@example.com",
  "Other": "Jane Doe",
  "OtherPh": "555-111-2222",
  "OtherEmail": "jane@example.com"
}
```

| Field | Type | Description |
|---|---|---|
| `Mom1` | string | Mother 1 name |
| `Mom1Ph` | `999-999-9999` | Mother 1 phone |
| `Mom1Email` | email | Mother 1 email |
| `Mom2` | string | Mother 2 name |
| `Mom2Ph` | `999-999-9999` | Mother 2 phone |
| `Mom2Email` | email | Mother 2 email |
| `Dad1` | string | Father 1 name |
| `Dad1Ph` | `999-999-9999` | Father 1 phone |
| `Dad1Email` | email | Father 1 email |
| `Dad2` | string | Father 2 name |
| `Dad2Ph` | `999-999-9999` | Father 2 phone |
| `Dad2Email` | email | Father 2 email |
| `Other` | string | Other guardian name |
| `OtherPh` | `999-999-9999` | Other guardian phone |
| `OtherEmail` | email | Other guardian email |

**`income_data`** — Set income and auto-calculate sliding fee schedule assignment.

```json
"income_data": {
  "Income": "50000",
  "Dependants": "4",
  "Unit": "Annual"
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `Income` | string | No | `"0"` | Income amount |
| `Dependants` | string | No | `"1"` | Number of dependants |
| `Unit` | string | No | `"Monthly"` | `"Monthly"` or `"Annual"` |
| `AssignedDate` | `YYYY-MM-DD` | No | Today | Override start date |
| `ExpiryDate` | `YYYY-MM-DD` | No | +1 year | Override expiry date |
| `DocProof` | `"0"` or `"1"` | No | | Proof of income documented |
| `NonProofOfIncome` | `"0"` or `"1"` | No | | No proof of income |
| `NoProofReason` | string | No | | Reason for no proof |

**`contact`** — Add a new emergency contact in the same call.

```json
"contact": {
  "Fname": "Jane",
  "Lname": "Doe",
  "relation": "Spouse",
  "homePhone": "555-987-6543",
  "isEmergencyContact": "1"
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `Fname` | string | **Yes** | | First name |
| `Lname` | string | **Yes** | | Last name |
| `relation` | `"Spouse"` `"Parent"` `"Child"` `"Sibling"` `"Other"` | No | `""` | Relationship |
| `homePhone` | phone | No | `""` | Home phone |
| `workPhone` | phone | No | `""` | Work phone |
| `CellPhone` | phone | No | `""` | Cell phone |
| `Email` | email | No | `""` | Email |
| `address` | string | No | `""` | Address |
| `city` | string | No | `""` | City |
| `state` | 2-letter code | No | `""` | State |
| `zip` | ZIP | No | `""` | ZIP code |
| `sex` | `"male"` or `"female"` | No | `""` | Sex (must be **lowercase**) |
| `dob` | date | No | `""` | Date of birth |
| `isEmergencyContact` | `"0"` or `"1"` | No | `"0"` | Is emergency contact |
| `Guardian` | `"0"` or `"1"` | No | `"0"` | Is guardian |
| `IsHippa` | `"0"` or `"1"` | No | `"0"` | HIPAA authorized |

**`update_contact`** — Update an existing contact. Same fields as `contact` above, plus `contact_id` (get it from `get-contacts` action).

```json
"update_contact": {
  "contact_id": "12345",
  "homePhone": "555-111-2222",
  "isEmergencyContact": "1"
}
```

**Other fields** (inside `changes`):

| Field | Type | Description |
|---|---|---|
| `deceased` | `""` or `"Y"` | Deceased flag |
| `deceasedDate` | date | Date of death |
| `deceasedNotes` | string | Death notes |
| `causeOfDeath` | string | Cause of death |
| `SelfPay` | `"0"` or `"1"` | Self-pay flag |
| `nostatements` | `"0"` or `"1"` | No statements flag |
| `OptOutOfPtStmt` | `"0"` or `"1"` | Opt out of patient statements |
| `FinanceChargeFlag` | `"0"` or `"1"` | Finance charge flag |
| `excludecollection` | `"0"` or `"1"` | Exclude from collections |
| `notes` | string | Patient notes |
| `pmcId` | string | PMC ID |
| `FeeSchId` | string | Fee schedule ID |
| `RelInfo` | `"Y"` or `"N"` | Release info consent |
| `RxConsent` | `"Y"` or `"N"` | Rx consent |
| `Consent` | `"1"` or `"0"` | General consent |
| `ReceivedConsent` | `"0"` or `"1"` | Received consent |
| `DateConsentSigned` | date | Date consent was signed |
| `eCROptInOption` | `"OptOut"` or `"OptIn"` | eCR opt-in option |
| `AlertStatus` | string | Alert status |
| `AlertNotes` | string | Alert notes |

---

### `read`

Read the full patient demographics record.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "read"
}
```

**Response:** Flat dict wrapped in `{ "status_code": 200, "body": { ... }, "success": true }`.

> **Note on read vs write field names:** Some fields use different keys when reading vs writing. The table below shows confirmed read response keys. Write keys (used in `edit-demographics` → `changes`) may differ — see the field reference above.

| Read key | Write key | Notes |
|---|---|---|
| `address` | `address1` | Write uses `address1`, read returns `address` |
| `maritalStatus` | `maritalstatus` | Casing differs |
| `umobileno` | `mobile` | Write uses `mobile`, read returns `umobileno` |
| `upreferredname` | `PreferredName` | Write uses `PreferredName` |
| `upreviousname` | `PreviousName` | Write uses `PreviousName` |
| `stAddress1` | `StAddress` | Casing differs — **unconfirmed, needs testing** |
| `stAddress2` | `StAddress2` | **Unconfirmed, needs testing** |
| `Ethnicity` | `Ethnicity` | Read returns the code (e.g. `"2186-5"`); `EthnicityName` has the display name. Write accepts display name |
| `sex` | `sex` | Read may return `"unknown"` for legacy data; write accepts `"M"` or `"F"` |

Key response fields (confirmed from live response):

| Field | Example | Description |
|---|---|---|
| `fname` | `"Test"` | First name |
| `lname` | `"WEDGE"` | Last name |
| `mname` | `"M"` | Middle name |
| `upreferredname` | `""` | Preferred name |
| `upreviousname` | `""` | Previous name |
| `prefix` | `""` | Name prefix |
| `suffix` | `""` | Name suffix |
| `namewithsuffix` | `"WEDGE, Test, M"` | Formatted full name |
| `dob` | `"01/23/1998"` | Date of birth |
| `tob` | `"1900-01-01"` | Time of birth |
| `sex` | `"unknown"` | Sex (may differ from write values) |
| `ssn` | `"719-27-4102"` | SSN |
| `status` | `"0"` | Patient status |
| `TransGender` | `"Y"` | Transgender flag |
| `phone` | `"555-123-1111"` | Home phone |
| `umobileno` | `""` | Cell phone |
| `email` | `"vinz@opsam.health"` | Email |
| `emailReason` | `"0"` | Email opt-out reason |
| `address` | `"637 3rd Avenue"` | Street address (note: key is `address`, not `address1`) |
| `address2` | `"Suite 400"` | Address line 2 |
| `city` | `"Chula Vista"` | City |
| `state` | `"CA"` | State |
| `zip` | `"91910"` | ZIP |
| `Country` | `"US"` | Country |
| `CountyName` | `"San Diego"` | County name |
| `CountyCode` | `""` | County code |
| `MailCountyName` | `"San Diego County"` | Mailing county name |
| `MailCountyCode` | `"06073"` | Mailing county code |
| `maritalStatus` | `"Married"` | Marital status (camelCase on read) |
| `race` | `"Asian"` | Race (display name) |
| `language` | `"English"` | Language (display name) |
| `Ethnicity` | `"2186-5"` | Ethnicity code (see `EthnicityName` for display) |
| `EthnicityName` | `"Not Hispanic or Latino"` | Ethnicity display name |
| `Translator` | `"0"` | Translator needed |
| `BirthOrder` | `"0"` | Birth order |
| `VFC` | `""` | VFC eligibility |
| `empId` | `"0"` | Employer ID |
| `empName` | `""` | Employer name |
| `empAddress` | `""` | Employer address |
| `empAddress2` | `""` | Employer address line 2 |
| `empCity` | `""` | Employer city |
| `empState` | `""` | Employer state |
| `empZip` | `""` | Employer ZIP |
| `empPhone` | `""` | Employer phone |
| `EmpStatus` | `""` | Employment status |
| `StudentStatus` | `"N"` | Student status |
| `stAddress1` | `""` | Student address (read key — write key unconfirmed) |
| `stAddress2` | `""` | Student address line 2 |
| `stCity` | `""` | Student city |
| `stState` | `""` | Student state |
| `stZip` | `""` | Student ZIP |
| `doctorId` | `"254134"` | Primary doctor ID |
| `doctorName` | `"1st, Attempt"` | Primary doctor name (read-only) |
| `refPrId` | `"0"` | Referring provider ID |
| `rendPrId` | `"0"` | Rendering provider ID |
| `GrId` | `"298724"` | Guarantor patient ID |
| `GrRel` | `"1"` | Guarantor relationship |
| `IsGrPt` | `"1"` | Guarantor is patient |
| `notes` | `""` | Patient notes |
| `mflag` | `""` / `"Brief"` / `"Extended"` | Home phone — Leave Message setting |
| `primaryServiceLocation` | `"22"` | Service location ID |
| `gestationalAge` | `""` | Gestational age |
| `deceased` | `"0"` | Deceased flag |
| `deceasedDate` | `""` | Date of death |
| `deceasedNotes` | `""` | Death notes |
| `SelfPay` | `"1"` | Self-pay flag |
| `FeeSchId` | `"76"` | Fee schedule ID |
| `nostatements` | `"0"` | No statements |
| `excludecollection` | `"0"` | Exclude from collections |
| `FinanceChargeFlag` | `"0"` | Finance charge flag |
| `RelInfo` | `"Y"` | Release info consent |
| `RxConsent` | `"Y"` | Rx consent |
| `Consent` | `"1"` | General consent |
| `pmcId` | `"0"` | PMC ID |
| `SelfPay` | `"1"` | Self-pay |
| `regdate` | `"2026-02-26 11:51:53"` | Registration date (read-only) |
| `patientId` | `"298724"` | Patient ID (read-only) |
| `ControlNo` | `"298724"` | Control number (read-only) |
| `uname` | `"steve@gmail.com"` | Portal username (read-only) |

---

### `read-combos`

Read dropdown/combo values for the demographics form (race, ethnicity, language, marital status options, etc.)

**Input:**
```json
{
  "patient_id": "298724",
  "action": "read-combos"
}
```

**Response:** JSON object with combo field options.

---

### `read-sliding-fee`

Read the current sliding fee schedule assignment for a patient.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "read-sliding-fee"
}
```

**Response:** Sliding fee assignment details (income, dependants, fee schedule, poverty level, dates).

---

### `read-sogi`

Read SOGI data plus option lists with IDs for sexual orientation, gender identity, and pronouns.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "read-sogi"
}
```

**Response:** Current SOGI values and `so_list`, `gi_list`, `pp_list` with IDs for use in `edit-demographics`.

---

### `read-lrte`

Read structured race, language, and ethnicity data.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "read-lrte"
}
```

---

### `read-parent-info`

Read parent/guardian info.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "read-parent-info"
}
```

---

### `read-structured-data`

Read Additional Information structured data fields (Homeless, Veteran, etc).

**Input:**
```json
{
  "patient_id": "298724",
  "action": "read-structured-data"
}
```

**Response:** Flat dict: `{ "Homeless": "Yes", "Veteran": "No", "Public Housing": "Yes", ... }`

---

### `calculate`

Preview sliding fee calculation without saving.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "calculate",
  "Income": "30000",
  "Dependants": "2",
  "Unit": "Annual"
}
```

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `Income` | string | No | `"0"` | Numeric amount |
| `Dependants` | string | No | `"1"` | Count |
| `Unit` | string | No | `"Monthly"` | `"Monthly"`, `"Annual"`, `"Weekly"`, `"Bi-Weekly"` |

**Response:** Calculated fee schedule (Type, PovertyLevel, FeeSchId, discounts).

---

### `search-provider`

Search providers by name.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "search-provider",
  "search": "Smith, John"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `search` | string | **Yes** | Provider name. Format: `"LastName"` or `"LastName, FirstName"` |

**Response:**
```json
{
  "providers": [
    { "ProviderId": "...", "ProviderName": "...", ... }
  ]
}
```

---

### `lrte-lookup`

Search race, language, or ethnicity values by display name.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "lrte-lookup",
  "lrte_type": "race",
  "search": "Asian"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `lrte_type` | string | **Yes** | `"race"`, `"language"`, or `"ethnicity"` |
| `search` | string | **Yes** | Display name to search |

**Response:** Array of `{ id, name, code, source }` objects.

---

### `get-contacts`

Read patient contacts (emergency contacts, family members).

**Input:**
```json
{
  "patient_id": "298724",
  "action": "get-contacts",
  "emergency_only": false
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `emergency_only` | bool | No | `false` | Filter to emergency contacts only |

**Response:**
```json
{
  "contacts": [
    { "Fname": "...", "Lname": "...", "relation": "...", ... }
  ]
}
```

---

### `add-contact`

Create a new contact for a patient.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "add-contact",
  "contact": {
    "Fname": "Jane",
    "Lname": "Doe",
    "relation": "Spouse",
    "homePhone": "512-555-0000",
    "Email": "jane@example.com",
    "isEmergencyContact": "1",
    "Guardian": "0"
  }
}
```

| Contact Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `Fname` | string | **Yes** | | First name |
| `Lname` | string | **Yes** | | Last name |
| `MI` | string | No | `""` | Middle initial |
| `relation` | string | No | `""` | Relationship to patient |
| `address` | string | No | `""` | Address line 1 |
| `address2` | string | No | `""` | Address line 2 |
| `city` | string | No | `""` | City |
| `state` | string | No | `""` | State |
| `zip` | string | No | `""` | ZIP |
| `homePhone` | string | No | `""` | Home phone |
| `CellPhone` | string | No | `""` | Cell phone |
| `workPhone` | string | No | `""` | Work phone |
| `Email` | string | No | `""` | Email |
| `dob` | string | No | `""` | Date of birth |
| `sex` | `"male"` or `"female"` | No | `""` | Sex (must be **lowercase**) |
| `workPhoneExt` | string | No | `""` | Work phone extension (digits/hyphens only) |
| `isEmergencyContact` | string | No | `"0"` | `"1"` = emergency contact |
| `Guardian` | string | No | `"0"` | `"1"` = guardian |
| `IsHippa` | string | No | `"0"` | `"1"` = HIPAA authorized |
| `isFamilyMember` | string | No | `"0"` | `"1"` = family member |
| `IsResponsibleParty` | string | No | `"0"` | `"1"` = responsible party |
| `MaidenName` | string | No | `""` | Maiden name |

**Response:**
```json
{
  "status_code": 200,
  "contactId": "12345",
  "body": "..."
}
```

---

### `update-contact`

Update an existing contact. Get `contact_id` from `get-contacts`.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "update-contact",
  "contact_id": "12345",
  "contact": {
    "homePhone": "555-999-8888"
  }
}
```

| Field | Type | Required |
|---|---|---|
| `contact_id` | string | **Yes** |
| `contact` | object | **Yes** |

Contact fields are the same as `add-contact`.

---

### `set-responsible-party`

Set the guarantor/responsible party for a patient.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "set-responsible-party",
  "gr_id": "298724",
  "gr_rel": "1",
  "is_gr_pt": "1"
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `gr_id` | string | No | `patient_id` | Guarantor patient ID |
| `gr_rel` | string | No | `"1"` | Relationship code (`"1"` = Self) |
| `is_gr_pt` | string | No | `"1"` | `"1"` if guarantor is a patient |

---

### `edit-income`

Calculate sliding fee from income data and assign it to the patient. Combines `calculate` + `save` in one step.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "edit-income",
  "income_data": {
    "Income": "2500",
    "Dependants": "3",
    "Unit": "Monthly",
    "AssignedDate": "2026-02-27",
    "ExpiryDate": "2027-02-27"
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `income_data` | object | **Yes** | Income details (see below) |

**income_data fields:**

| Field | Type | Required | Default |
|---|---|---|---|
| `Income` | string | No | `"0"` |
| `Dependants` | string | No | `"1"` |
| `Unit` | string | No | `"Monthly"` |
| `AssignedDate` | string | No | Auto-calculated |
| `ExpiryDate` | string | No | Auto-calculated |
| `IncomeInfo` | object | No | Read from current record |
| `MemberInfo` | array | No | `[]` |

**Response:**
```json
{
  "status_code": 200,
  "body": "...",
  "calculated": {
    "Type": "...",
    "PovertyLevel": "...",
    "FeeSchId": "..."
  }
}
```

---

### `save-sogi`

Standalone SOGI save (outside of `edit-demographics`).

**Input:**
```json
{
  "patient_id": "298724",
  "action": "save-sogi",
  "sogi_data": {
    "birthsex": "F",
    "transgender": "N",
    "pp_ids": "2",
    "so_id": "3",
    "gi_ids": "2"
  }
}
```

Same `sogi_data` fields as documented under `edit-demographics`. Same `*_changed` defaulting behavior applies.

---

### `save-parent-info`

Standalone parent/guardian info save.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "save-parent-info",
  "parent_data": {
    "Mom1": "Test Mom",
    "Mom1Ph": "555-100-0001",
    "Mom1Email": "mom@test.com",
    "Dad1": "",
    "Dad1Ph": "",
    "Dad1Email": ""
  }
}
```

Same `parent_data` fields as documented under `edit-demographics`.

---

### `save-lrte`

Direct race, language, or ethnicity save using resolved IDs from `lrte-lookup`.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "save-lrte",
  "lrte_type": "race",
  "entries": [{ "id": 1043, "name": "White", "code": "2106-3" }]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `lrte_type` | string | **Yes** | `"race"`, `"language"`, or `"ethnicity"` |
| `entries` | array | **Yes** | Array of `{ id, name, code }` objects from `lrte-lookup` |

---

### `save-structured-data`

Save Additional Information structured data fields. Only include fields to change — others are preserved. Field definitions are fetched dynamically from ECW, so any new fields added to the tenant work automatically.

**Input:**
```json
{
  "patient_id": "299227",
  "action": "save-structured-data",
  "structured_data": {
    "Homeless": "Yes",
    "Homeless Status": "Shelter",
    "Inc & Size Collected": "Yes",
    "Household income": "5000",
    "Income Frequency": "Monthly",
    "Family size": "4",
    "Applied for SFDP?": "Yes"
  }
}
```

**Parent fields** (Yes/No checkboxes):

| Field | Values |
|---|---|
| `Homeless` | `"Yes"` / `"No"` |
| `Seasonal Agricultural Worker` | `"Yes"` / `"No"` |
| `Migrant Agricultural Worker` | `"Yes"` / `"No"` |
| `Veteran` | `"Yes"` / `"No"` |
| `Public Housing` | `"Yes"` / `"No"` |
| `Uninsured` | `"Yes"` / `"No"` |
| `Inc & Size Collected` | `"Yes"` / `"No"` |
| `Applied for SFDP?` | `"Yes"` / `"No"` |
| `Transportation Services Needed` | `"Yes"` / `"No"` |
| `Disability` | `"Yes"` / `"No"` |
| `Substance Abuse` | `"Yes"` / `"No"` |
| `Limited English` | `"Yes"` / `"No"` |
| `Immigrant?` | `"Yes"` / `"No"` |
| `SDHC Opt-Out` | `"Yes"` / `"No"` |
| `SHC Employee` | `"Yes"` / `"No"` |
| `SHC Patient` | `"Yes"` / `"No"` |
| `Pain Management Program?:` | `"Yes"` / `"No"` |
| `Self Pay` | `"Yes"` / `"No"` |

**Child/subfields** (activated by parent's Yes/No value):

| Field | Parent | Appears when | Values |
|---|---|---|---|
| `Homeless Status` | Homeless | Yes | `"Doubled-Up"` `"Street"` `"Shelter"` `"Transitional Housing"` `"Other"` `"Unknown"` `"Permanent Supportive Housing"` |
| `Date` | Inc & Size Collected | Yes | `MM/YYYY` |
| `Household income` | Inc & Size Collected | Yes | number |
| `Income Frequency` | Inc & Size Collected | Yes | `"Monthly"` `"Annual"` etc. |
| `Family size` | Inc & Size Collected | Yes | number (1-100) |
| `Date declined` | Inc & Size Collected | No | `MM/DD/YYYY` |
| `SFDP Date declined` | Applied for SFDP? | No | `MM/DD/YYYY` |
| `Would you be interested in immigration resources?` | Immigrant? | Yes | `"Yes"` / `"No"` |
| `Would you be interested an informational workshop on immigration options?` | Immigrant? | Yes | `"Yes"` / `"No"` |

**Other fields** (text/number, no parent):

| Field | Values |
|---|---|
| `Last Registration Update` | `MM-YYYY` |
| `Monthly Estimated Income` | number |
| `Family Size` | number |
| `Primary Dentist` | text |

> **Elastic:** Field IDs are resolved dynamically at save time. New structured data fields added to the ECW tenant will work without code changes — just use the exact field name as shown in the UI.

Supports notes on any field: `{ "value": "Yes", "notes": "Some comment" }`.

---

### `upload-insurance-card`

Upload an insurance card image to Patient Docs → Insurance folder.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "upload-insurance-card",
  "image_base64": "<base64-encoded image>",
  "filename": "front_of_card.png",
  "description": "Front of insurance card"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `image_base64` | string | **Yes** | Base64-encoded image |
| `filename` | string | **Yes** | Filename with extension |
| `description` | string | No | Document description |

Accepted formats: PNG, JPG, GIF, PDF, BMP, TIFF.

**Response:** `{ "status_code": 200, "documentId": "abc123", "fileName": "uuid_298724.png" }`

---

### `upload-profile-picture`

Upload patient profile picture.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "upload-profile-picture",
  "image_base64": "<base64-encoded JPEG>"
}
```

| Field | Type | Required |
|---|---|---|
| `image_base64` | string | **Yes** |

Image is saved as `{patientId}.jpg` in `/mobiledoc/Patients/`.

**Response:** `{ "status_code": 200, "body": "success", "fileName": "298724.jpg" }`

---

### `save-communication-notes`

Save the Notes field from Patient Communication Settings (the message icon next to "Manage Phone List").

**Input:**
```json
{
  "patient_id": "298724",
  "action": "save-communication-notes",
  "notes": "Patient prefers morning calls only"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `notes` | string | **Yes** | Communication notes (max 255 characters) |

**Response:** `{ "status_code": 200, "body": "success" }`

---

### Phone Preferences (via `edit-demographics`)

Edit phone contact preferences, leave message settings, and work phone extension via `phonePreferences` inside `changes`.

**Input:**
```json
{
  "action": "edit-demographics",
  "patient_id": "298724",
  "changes": {
    "workPhone": "555-999-7777",
    "phonePreferences": {
      "cell": {
        "voiceEnabled": true,
        "textEnabled": true,
        "leaveMessage": "Brief"
      },
      "home": {
        "voiceEnabled": false,
        "textEnabled": true,
        "leaveMessage": "Do not leave message"
      },
      "work": {
        "ext": "1234",
        "voiceEnabled": true,
        "textEnabled": false,
        "leaveMessage": "Brief",
        "description": "Office Line"
      }
    }
  }
}
```

| Preference field | Type | Description |
|---|---|---|
| `voiceEnabled` | bool | Voice contact preference checkbox |
| `textEnabled` | bool | Text contact preference checkbox |
| `leaveMessage` | string | `null`, `"Brief"`, `"Extended"`, `"Do not leave message"` |
| `ext` | string | Phone extension (digits and hyphens only, work phone typically) |
| `description` | string | Phone description (max 15 chars) |

Apply to `"cell"`, `"home"`, or `"work"`. The `read` action returns these in `phoneList`:

```json
"phoneList": {
  "CELL_PHONE": {
    "id": 266968,
    "phoneNumber": "555-111-2222",
    "ext": null,
    "voiceEnabled": true,
    "textEnabled": true,
    "leaveMessage": "Brief",
    "description": "Cell Phone"
  },
  "HOME_PHONE": { ... },
  "WORK_PHONE": { ... }
}
```

---

# ecw_sfdp

Sliding Fee / Insurance management and scenario workflows.

## Common Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `action` | string | **Yes** | Action to perform (no default) |
| `patient_id` | string | Most actions | eCW patient ID |

---

## Actions

### `sliding-history`

Read sliding scale assignment history for a patient.

**Input:**
```json
{
  "action": "sliding-history",
  "patient_id": "298724"
}
```

---

### `sliding-detail`

Read detail for a specific sliding fee assignment.

**Input:**
```json
{
  "action": "sliding-detail",
  "assignment_id": "12345"
}
```

| Field | Type | Required |
|---|---|---|
| `assignment_id` | string | **Yes** |

---

### `other-income-reasons`

Load dropdown options for "other income" reasons.

**Input:**
```json
{
  "action": "other-income-reasons"
}
```

---

### `find-members`

Find household members for sliding fee calculation.

**Input:**
```json
{
  "action": "find-members",
  "patient_id": "298724"
}
```

---

### `get-insurance`

Read patient insurance information.

**Input:**
```json
{
  "action": "get-insurance",
  "patient_id": "298724"
}
```

**Response:**
```json
{
  "status_code": 200,
  "body": {
    "insurances": [
      {
        "PtInsId": "180323",
        "id": "230",
        "name": "United Healthcare - MCARE",
        "stDate": "",
        "endDate": "",
        "gpNo": "",
        "sbNo": "MEMBER-001",
        "copays": "",
        "copayType": "$",
        "insOrder": "0",
        "GrId": "298724",
        "GrName": "Livas, Aida, M",
        "GrRel": "1",
        "IsGrPt": "1",
        "Active": "A",
        "SequenceTitle": "Active Primary Insurance",
        "InsEligSts": "V"
      }
    ],
    "responsible_party": {
      "GrId": "298724",
      "GrName": "Livas, Aida M",
      "GrPhone": "111-111-1111",
      "GrRel": "1",
      "IsGrPt": "1"
    }
  },
  "success": true
}
```

> **Note:** Response uses lowercase `id` and `name` for the carrier (read), while `add-insurance` input uses `InsuranceId` (PascalCase write). These refer to the same carrier ID value.

---

### `search-carriers`

Search insurance carriers by name.

**Input:**
```json
{
  "action": "search-carriers",
  "search": "Blue Cross",
  "ins_type": ""
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `search` | string | **Yes** | Carrier name substring to search |
| `ins_type` | string | No | Insurance type filter |

**Response:** Same shape as `list-carriers`.

---

### `list-carriers`

Return all insurance carriers (no search filter).

**Input:**
```json
{
  "action": "list-carriers",
  "ins_type": ""
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `ins_type` | string | No | Insurance type filter (empty = all) |

**Response:**
```json
{
  "status_code": 200,
  "body": {
    "carriers": [
      {
        "Id": "175",
        "Name": "Aetna - COMM",
        "Addr1": "PO Box 14079",
        "City": "Lexington",
        "State": "KY",
        "Zip": "40512-4079",
        "Tel": "800-624-0756",
        "PayorID": "60054",
        "ERAPayorID": "60054",
        "Inactive": "0"
      }
    ]
  },
  "success": true
}
```

> **Note:** Field names are PascalCase (`Id`, `Name`, `PayorID`, etc.) — not camelCase. Use `Id` for `InsuranceId` when calling `add-insurance`.

---

### `delete-insurance`

Delete a patient's insurance record.

**Input:**
```json
{
  "action": "delete-insurance",
  "patient_id": "298724",
  "pt_ins_id": "67890"
}
```

| Field | Type | Required |
|---|---|---|
| `pt_ins_id` | string | **Yes** |

---

### `save-insurance-detail`

Save/update insurance details for a patient.

**Input:**
```json
{
  "action": "save-insurance-detail",
  "patient_id": "298724",
  "insurances": [ ...insurance objects... ]
}
```

| Field | Type | Required |
|---|---|---|
| `insurances` | array | **Yes** |

---

### `add-insurance`

Add a new insurance record.

**Input:**
```json
{
  "action": "add-insurance",
  "patient_id": "298724",
  "insurance_data": {
    "InsuranceId": "175",
    "insOrder": "1",
    "sbNo": "MEMBER-001",
    "gpNo": "GROUP-999",
    "GrRel": "1",
    "IsGrPt": "1",
    "GrId": "298724"
  }
}
```

> **Getting `InsuranceId`:** Call `list-carriers` first and match the carrier name to `carriers[].Id`. Do not hardcode — carrier IDs vary per ECW instance.

**`insurance_data` fields:**

**Subscriber tab:**

| Field | Type | Required | Description |
|---|---|---|---|
| `InsuranceId` | string | **Yes** | Carrier ID from `list-carriers` → `Id` |
| `SubscriberId` | string | No | Subscriber / member ID number (Sub No) |
| `GroupNo` | string | No | Group number |
| `GroupName` | string | No | Group name |
| `MedicaidId` | string | No | Medicaid ID No. |
| `SuppInsInd` | string | No | Supplemental insurance indicator |
| `CoPay` | string | No | Copay amount |
| `CopayMethod` | string | No | `"$"` or `"%"`. Default: `"$"` |
| `GrId` | string | No | Guarantor patient ID (default: patient_id) |
| `GrRel` | string | No | Patient relationship to insured: `"1"` Self, `"2"` Spouse, `"3"` Child |
| `IsGrPt` | string | No | `"1"` if guarantor is a patient, `"0"` otherwise |
| `MultipleCoPay` | `"0"` / `"1"` | No | Enable multiple co-pays |
| `PCPCoPay` | string | No | Primary care co-pay amount |
| `SpecialityCoPay` | string | No | Specialty care co-pay amount |
| `OtherCoPay` | string | No | Other co-pay amount |

**Coverage & classification:**

| Field | Type | Description |
|---|---|---|
| `SeqNo` | string | Sequence: `"1"` Primary, `"2"` Secondary, `"3"` Tertiary |
| `StartDate` | `MM/DD/YYYY` | Coverage start date |
| `EndDate` | `MM/DD/YYYY` | Coverage end date |
| `PaymentSource` | string | Source of payment code |
| `InsuranceClass` | string | Insurance class for reports |
| `InsType` | string | Insurance type |
| `DentalIns` | `"0"` / `"1"` | Dental insurance |
| `visionIns` | `"0"` / `"1"` | Vision insurance |
| `behavioralHealthIns` | `"0"` / `"1"` | Behavioral health insurance |
| `CoInsurance` | string | Co-insurance amount |

**Alternate names (Patient's Alternate Name / Insured's Alternate Name):**

| Field | Type | Description |
|---|---|---|
| `PatientAltLName` | string | Patient's alternate last name |
| `PatientAltFName` | string | Patient's alternate first name |
| `PatientAltMiddleInitial` | string | Patient's alternate MI |
| `InsuredAltLName` | string | Insured's alternate last name |
| `InsuredAltFName` | string | Insured's alternate first name |
| `InsuredAltMiddleInitial` | string | Insured's alternate MI |

**Other:**

| Field | Type | Description |
|---|---|---|
| `MedicaidSeqNo` | string | Medicaid sequence number |
| `MedicareSubId` | string | Medicare subscriber ID |
| `notes` | string | Insurance notes |

> **Note on field names:** Use `SubscriberId` (not `sbNo`) and `GroupNo` (not `gpNo`) when writing. The read response (`get-insurance`) returns these as `sbNo` and `gpNo` respectively.

**Response:**
```json
{
  "status_code": 200,
  "body": { "status": "success", "pt_ins_id": "180358" },
  "success": true
}
```

`pt_ins_id` is the newly created insurance record ID — save it if you need to call `update-insurance` or `delete-insurance` later.

---

### `update-insurance`

Update an existing insurance record.

**Input:**
```json
{
  "action": "update-insurance",
  "patient_id": "298724",
  "pt_ins_id": "67890",
  "insurance_data": { "...": "..." }
}
```

| Field | Type | Required |
|---|---|---|
| `pt_ins_id` | string | **Yes** |
| `insurance_data` | object | **Yes** |

---

## Scenario Workflows

End-to-end sliding fee lifecycle workflows. Each scenario orchestrates multiple API calls.

| Scenario | Name | Description |
|---|---|---|
| `scenario-1` | PENDING → FINAL WITH POI | Patient arrives with proof of income. Calculate, assign, mark final. |
| `scenario-2` | PENDING → PROVISIONAL | No proof of income. Assign provisional sliding fee. |
| `scenario-5` | PROVISIONAL → FINAL NO POI | 10-day grace period expired, no POI received. Remove sliding fee. |
| `scenario-6` | PROVISIONAL → FINAL WITH POI | POI arrives during provisional period. Finalize assignment. |
| `scenario-7` | FINAL NO POI → FINAL WITH POI | Patient returns later with POI. Re-assign sliding fee. |

**Input (all scenarios):**
```json
{
  "action": "scenario-1",
  "patient_id": "298724",
  "income_data": {
    "Income": "2500",
    "Dependants": "3",
    "Unit": "Monthly"
  },
  "old_pt_ins_id": null,
  "new_ins_data": null
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `income_data` | object | No | Income details for calculation |
| `old_pt_ins_id` | string | No | Insurance ID to remove (scenarios 5, 7) |
| `new_ins_data` | object | No | New insurance to add (scenario 7) |

---

# ecw_create_patient

Creates a new patient record via the eClinicalWorks Quick Registration flow.

| Integration | ID |
|---|---|
| `ecw_create_patient` | `2f0ae558-0b1a-4b75-af7a-1f72cf1aa44c` |

## Required Fields

| Field | Type | Format | Example |
|---|---|---|---|
| `fname` | string | | `"John"` |
| `lname` | string | | `"Smith"` |
| `dob` | string | `YYYY-MM-DD` | `"1990-01-15"` |
| `sex` | string | Exactly `"Male"`, `"Female"`, or `"Unknown"` | `"Male"` |

## Optional Fields

| Field | Type | Format | Example |
|---|---|---|---|
| `mname` | string | | `"Robert"` |
| `phone` | string | `XXX-XXX-XXXX` | `"555-123-4567"` |
| `email` | string | | `"john@example.com"` |
| `address1` | string | | `"123 Main St"` |
| `address2` | string | | `"Suite 400"` |
| `city` | string | Letters/spaces only | `"Austin"` |
| `state` | string | 2-letter US code | `"TX"` |
| `zip` | string | 5-digit or ZIP+4 | `"78701"` |
| `country` | string | 2-letter ISO code | `"US"` |

## Example

```bash
curl -X POST https://api.integuru.ai/integrations/invoke \
  -H "Authorization: Bearer egm_..." \
  -H "Content-Type: application/json" \
  -d '{
    "integration_id": "2f0ae558-0b1a-4b75-af7a-1f72cf1aa44c",
    "account_id": "98c16453-be1f-4c9f-b942-dcdfa8e526f3",
    "input": {
      "fname": "John",
      "lname": "Smith",
      "dob": "1990-01-15",
      "sex": "Male"
    }
  }'
```

**Response:**
```json
{
  "status_code": 200,
  "body": {
    "patient_id": "298986",
    "message": "Patient created successfully"
  },
  "success": true
}
```