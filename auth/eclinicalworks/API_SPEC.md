# eClinicalWorks Integration API Spec

Platform: `caoshae8e528d1yp90app.ecwcloud.com`

## Invocation

All requests go to the **Endgame backend** (not the eClinicalWorks platform URL).

```
POST https://app.integuru.ai/integrations/invoke
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
curl -X POST "https://app.integuru.ai/integrations/invoke" \
  -H "Authorization: Bearer egm_..." \
  -H "Content-Type: application/json" \
  -d '{
    "integration_id": "10e5714d-76bb-4f91-906a-f93bf5c75bbe",
    "account_id": "a68c8f5f-3b12-4769-a836-9a19c1aebc23",
    "input": {
      "action": "read",
      "patient_id": "298724"
    }
  }'
```

## Integrations

| Integration | ID | Purpose |
|---|---|---|
| `ecw_demographics` | `10e5714d-76bb-4f91-906a-f93bf5c75bbe` | Patient demographics, contacts, providers, sliding fee |
| `ecw_sfdp` | `c38fcfb6-4848-4443-88b3-dcec9e0e5f8f` | Sliding fee workflows, insurance management, scenarios |
| `ecw_create_patient` | `2f0ae558-0b1a-4b75-af7a-1f72cf1aa44c` | Create new patient via Quick Registration |

## IDs & Resources

| Resource | Value |
|----------|-------|
| Platform ID | `06230071-c18e-4b99-9a28-948f9c0bb8dc` |
| Account ID | `a68c8f5f-3b12-4769-a836-9a19c1aebc23` |
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
| `action` | string | No | Action to perform. Default: `"read"` |
| `patient_id` | string | **Yes** | eCW patient ID (e.g. `"298724"`) |

---

## Actions

### `read`

Read the full patient demographics record.

**Input:**
```json
{
  "patient_id": "298724"
}
```

**Response:** Flat dict of all demographics fields (`fname`, `lname`, `dob`, `address`, `phone`, `email`, `ssn`, `sex`, `race`, `Ethnicity`, `doctorId`, `maritalStatus`, etc.)

---

### `edit-demographics`

Read-modify-write: reads the current record, merges your changes, saves both tabs.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "edit-demographics",
  "changes": {
    "email": "new@example.com",
    "phone": "512-555-9999"
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `changes` | object | **Yes** | Dict of field names to new values. Only changed fields needed. |

**Editable fields (Tab 1 — Personal Info):**

| Field | Description | Example |
|---|---|---|
| `prefix` | Name prefix | `"Mr"` |
| `suffix` | Name suffix | `"Jr"` |
| `fname` | First name | `"Test"` |
| `lname` | Last name | `"Wedge"` |
| `mname` | Middle name | `""` |
| `address1` | Street address line 1 | `"123 Main Street"` |
| `address2` | Street address line 2 | `"Suite 400"` |
| `city` | City | `"Austin"` |
| `state` | State code | `"TX"` |
| `zip` | ZIP code | `"78701"` |
| `Country` | Country code | `"US"` |
| `CountyCode` | County code | `""` |
| `CountyName` | County name | `""` |
| `MailCountyCode` | Mailing county code | `""` |
| `MailCountyName` | Mailing county name | `""` |
| `phone` | Home phone | `"512-555-1234"` |
| `mobile` | Cell phone | `""` |
| `PreviousName` | Previous name | `""` |
| `email` | Email address | `"test.wedge@example.com"` |
| `emailReason` | Email opt-out reason code | `"0"` |
| `dob` | Date of birth (MM/DD/YYYY) | `"07/07/2000"` |
| `tob` | Time of birth | `"1900-01-01"` |
| `ssn` | SSN (XXX-XX-XXXX) | `"123-45-6789"` |
| `sex` | Sex | `"male"` / `"female"` |
| `TransGender` | Transgender flag | `"N"` / `"Y"` / `"n"` |
| `status` | Patient status | `"0"` |
| `mflag` | Message flag | `""` |
| `primaryServiceLocation` | Service location ID | `"22"` |
| `gestationalAge` | Gestational age | `""` |
| `PreferredName` | Preferred name | `""` |

**Editable fields (Tab 2 — Employment/Misc):**

| Field | Description | Example |
|---|---|---|
| `empId` | Employer ID | `"0"` |
| `empName` | Employer name | `""` |
| `empAddress` | Employer address | `""` |
| `empAddress2` | Employer address line 2 | `""` |
| `empCity` | Employer city | `""` |
| `empState` | Employer state | `""` |
| `empZip` | Employer ZIP | `""` |
| `empPhone` | Employer phone | `""` |
| `StAddress` | Student address | `""` |
| `StAddress2` | Student address line 2 | `""` |
| `stCity` | Student city | `""` |
| `stState` | Student state | `""` |
| `stZip` | Student ZIP | `""` |
| `notes` | Patient notes | `""` |
| `maritalstatus` | Marital status (display name or code) | `"Single"`, `"Married"`, `"Divorced"`, `"Widowed"`, `"S"`, `"M"`, `"D"`, `"W"` |
| `doctorId` | Primary doctor ID | `"254134"` |
| `refPrId` | Referring provider ID | `"0"` |
| `rendPrId` | Rendering provider ID | `"0"` |
| `pmcId` | PMC ID | `""` |
| `Translator` | Translator flag | `1` (required) / `0` (not required) |
| `deceased` | Deceased flag | `"0"` / `"1"` |
| `deceasedDate` | Date of death | `""` |
| `deceasedNotes` | Death notes | `""` |
| `Ethnicity` | Ethnicity code | `"2186-5"` (Not Hispanic), `"2135-2"` (Hispanic), `"ASKU"` (Declined) |
| `EmpStatus` | Employment status | `"1"` (Full-time) |
| `StudentStatus` | Student status | `"N"` / `"F"` / `"P"` |
| `SelfPay` | Self-pay flag | `"0"` / `"1"` |
| `FeeSchId` | Fee schedule ID | `"0"` |
| `RelInfo` | Release info consent | `"Y"` / `"N"` |
| `RxConsent` | Rx consent | `"Y"` / `"N"` |
| `Consent` | General consent | `"1"` / `"0"` |

**LRTE fields** (saved via dedicated REST endpoints, not Tab 2 XML):

| Field | Description | Example |
|---|---|---|
| `language` | Primary language (name or `{name, code, id}` object) | `"English"`, `"Spanish"`, `"French"` |
| `race` | Race (comma-separated names, array of strings, or array of `{name, code}` objects) | `"White"`, `"Asian,White"`, `[{"name": "Asian", "code": "2028-9"}]` |
| `Translator` | Translator required flag (used with language save) | `1` / `0` |

Built-in race lookups: `White` (2106-3), `Asian` (2028-9), `Black or African American` (2054-5), `American Indian or Alaska Native` (1002-5), `Native Hawaiian or Other Pacific Islander` (2076-8).

Built-in language lookups: `English` (en), `Spanish` (es), `French` (fr), `Chinese` (zh), `Vietnamese` (vi), `Korean` (ko), `Portuguese` (pt), `Arabic` (ar), `Russian` (ru), `Tagalog` (tl), `German` (de), `Japanese` (ja), `Hindi` (hi).

**Responsible party fields** (saved separately if included in `changes`):

| Field | Description | Example |
|---|---|---|
| `GrId` | Guarantor patient ID | `"298724"` |
| `GrRel` | Guarantor relationship | `"1"` (Self) |
| `IsGrPt` | Guarantor is patient | `"1"` / `"0"` |

**Response:**
```json
{
  "tab1": { "status_code": 200, "body": "..." },
  "tab2": { "status_code": 200, "body": "..." },
  "language": { "statusCode": 200, "message": null, "result": null },
  "race": { "statusCode": 200, "message": null, "result": null },
  "responsible_party": { "status_code": 200, "body": "..." }
}
```
Only keys for changed fields are returned.

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

### `read-lrte`

Read LRTE (Language, Race, Tribal, Ethnicity) dropdown values from ECW.

**Input (language search):**
```json
{
  "patient_id": "298724",
  "action": "read-lrte",
  "option": "language",
  "search": "French"
}
```

**Input (full race list):**
```json
{
  "patient_id": "298724",
  "action": "read-lrte",
  "option": "race"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `option` | string | **Yes** | `"language"` or `"race"` |
| `search` | string | No | Typeahead search term (language only) |

**Response (language):**
```json
{
  "languages": [
    { "id": 234, "name": "French", "code": "fr", "source": "System-Defined" },
    { "id": 575, "name": "French, Middle (ca.1400-1600)", "code": "frm", "source": "System-Defined" }
  ]
}
```

**Response (race):**
```json
{
  "races": [
    { "id": 1749, "name": "Asian", "code": "2028-9", "source": "System-Defined (CDC)" },
    { "id": 1043, "name": "White", "code": "2106-3", "source": "System-Defined (CDC)" }
  ]
}
```

When setting language or race via `edit-demographics`, unknown strings are automatically resolved against these endpoints. Static lookups cover common values; ECW is queried as fallback.

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

### `calculate`

Calculate sliding fee schedule from income/dependants without saving.

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
| `sex` | string | No | `""` | Sex |
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

Update an existing contact.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "update-contact",
  "contact_id": "12345",
  "contact": {
    "Fname": "Jane",
    "Lname": "Doe-Smith",
    "homePhone": "512-555-1111"
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

Calculate sliding fee from income data and assign it to the patient.

**Ceremony:** 1) Expire existing assignment (if any) → 2) Calculate new fee → 3) Save new assignment.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "edit-income",
  "income_data": {
    "Income": "3000",
    "Dependants": "2",
    "Unit": "Monthly"
  }
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `income_data` | object | **Yes** | | Income details (see below) |

**income_data fields:**

| Field | Type | Required | Default |
|---|---|---|---|
| `Income` | string | No | `"0"` |
| `Dependants` | string | No | `"1"` |
| `Unit` | string | No | `"Monthly"` (`"Annual"`, `"Weekly"`, `"Bi-Weekly"`) |
| `AssignedDate` | string | No | Auto-calculated |
| `ExpiryDate` | string | No | Auto-calculated |
| `IncomeInfo` | object | No | `{}` |
| `MemberInfo` | array | No | `[]` |

**Response:**
```json
{
  "expired": { "status_code": 200, "body": "..." },
  "calculated": {
    "status": "success",
    "Type": "D",
    "PovertyLevel": "171.0",
    "FeeSchId": "76",
    "FeeSchedule": "2025 Slide D",
    "MedicalDiscount": "50",
    "DentalDiscount": "60",
    "CopayDiscount": "100.00",
    "AssignedDate": "2026-03-17",
    "ExpiryDate": "2027-03-17"
  },
  "assigned": { "status_code": 200, "body": "..." }
}
```

---

### `upload-insurance-card`

Upload an insurance card image to the patient's Insurance document folder.

Validates file type (extension + magic bytes) before uploading. Accepted formats: PNG, JPG, GIF, PDF, BMP, TIFF.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "upload-insurance-card",
  "image_base64": "<base64-encoded image data>",
  "filename": "front_of_card.png",
  "description": "Front of insurance card"
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `image_base64` | string | **Yes** | | Base64-encoded image data |
| `filename` | string | No | `"insurance_card.png"` | Filename with extension |
| `description` | string | No | `""` | Document description |

**Response:**
```json
{
  "status_code": 200,
  "documentId": "yrERLeay6R",
  "fileName": "uuid_298724.png"
}
```

**Error (invalid file type):**
```json
{
  "status_code": 400,
  "body": { "error": "File content doesn't match PNG signature ..." }
}
```

---

### `get-parent-info`

Read parent info (Mother x2, Father x2, Other — name, phone, email each).

**Input:**
```json
{
  "patient_id": "298724",
  "action": "get-parent-info"
}
```

**Response:**
```json
{
  "Mom1": "Jane Doe", "Mom1Ph": "555-100-2000", "Mom1Email": "jane@example.com",
  "Mom2": "", "Mom2Ph": "", "Mom2Email": "",
  "Dad1": "John Doe", "Dad1Ph": "555-200-3000", "Dad1Email": "john@example.com",
  "Dad2": "", "Dad2Ph": "", "Dad2Email": "",
  "Other": "", "OtherPh": "", "OtherEmail": ""
}
```

---

### `save-parent-info`

Save parent info. All 15 fields must be present (empty string for blank).

**Input:**
```json
{
  "patient_id": "298724",
  "action": "save-parent-info",
  "parent_info": {
    "Mom1": "Jane Doe", "Mom1Ph": "555-100-2000", "Mom1Email": "jane@example.com",
    "Mom2": "", "Mom2Ph": "", "Mom2Email": "",
    "Dad1": "John Doe", "Dad1Ph": "555-200-3000", "Dad1Email": "john@example.com",
    "Dad2": "", "Dad2Ph": "", "Dad2Email": "",
    "Other": "", "OtherPh": "", "OtherEmail": ""
  }
}
```

**Response:** `{ "status_code": 200, "saved": true }`

---

### `get-sogi`

Read SOGI (Sexual Orientation & Gender Identity) data. Also returns full lookup lists for all options.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "get-sogi"
}
```

**Response:**
```json
{
  "birthsex": "M",
  "transgender": "N",
  "pronouns": [{ "id": 1, "name": "he/him/his/his/himself" }],
  "sexual_orientation": { "id": 2, "snomed": "20430005" },
  "gender_identity": [{ "id": 1, "name": "Male", "snomed": "446151000124109" }],
  "pp_list": [{ "id": 1, "name": "he/him/his/his/himself" }, ...],
  "so_list": [{ "id": 1, "name": "Lesbian, gay or homosexual" }, ...],
  "gi_list": [{ "id": 1, "name": "Male" }, ...]
}
```

Use `pp_list`, `so_list`, `gi_list` to get valid IDs for `save-sogi`.

---

### `save-sogi`

Save SOGI settings. Use IDs from `get-sogi` lookup lists. Multiple IDs as comma-separated.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "save-sogi",
  "birthsex": "M",
  "transgender": "N",
  "pp_ids": "1",
  "so_id": "2",
  "gi_ids": "1",
  "pp_reason": "",
  "so_reason": "",
  "gi_reason": "",
  "so_date": "",
  "gi_date": "",
  "birthsex_changed": true,
  "transgender_changed": true
}
```

| Field | Description | Example |
|---|---|---|
| `birthsex` | Sex assigned at birth | `"M"`, `"F"`, `"UNK"` |
| `transgender` | Transgender flag | `"Y"` / `"N"` |
| `pp_ids` | Pronoun IDs (comma-separated) | `"1,3"` (he/him + they/them) |
| `so_id` | Sexual orientation ID | `"2"` (Straight) |
| `gi_ids` | Gender identity IDs (comma-separated) | `"1"` (Male) |
| `pp_reason` | Custom pronoun text | `"custom/pronoun"` |
| `so_reason` | Custom SO text | `""` |
| `gi_reason` | Custom GI text | `""` |
| `*_changed` | Only update fields marked true | `true` / `false` |

**Response:** `{ "status_code": 200, "body": "{}" }`

---

### `search-guarantor`

Search for patients or guarantors to set as responsible party.

**Input (search patients):**
```json
{
  "patient_id": "298724",
  "action": "search-guarantor",
  "search": "Test",
  "type": "patient"
}
```

**Input (search guarantors):**
```json
{
  "patient_id": "298724",
  "action": "search-guarantor",
  "search": "Test",
  "type": "guarantor"
}
```

**Response:** `{ "patients": [...] }` or `{ "guarantors": [...] }`

---

### `get-guarantor-info`

Get details for a specific guarantor/patient by ID.

**Input:**
```json
{
  "patient_id": "298724",
  "action": "get-guarantor-info",
  "gr_id": "298724"
}
```

**Response:**
```json
{
  "patientId": "298724",
  "fname": "Test",
  "lname": "WEDGE",
  "dob": "01/23/1998",
  "sex": "unknown",
  "phone": "917-401-7419"
}
```

Use with `set-responsible-party` to link as guarantor: pass `gr_id`, `gr_rel` (`"1"` = Self, `"0"` = Other), `is_gr_pt` (`"1"` = patient, `"0"` = non-patient guarantor).

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
| `search` | string | **Yes** | Carrier name |
| `ins_type` | string | No | Insurance type filter |

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
    "InsuranceId": "12345",
    "...": "..."
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `insurance_data` | object | **Yes** | Must include `InsuranceId` |

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
    "account_id": "a68c8f5f-3b12-4769-a836-9a19c1aebc23",
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