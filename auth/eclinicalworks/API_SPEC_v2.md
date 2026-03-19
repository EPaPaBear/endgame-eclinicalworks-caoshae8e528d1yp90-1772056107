# eClinicalWorks Demographics — Integration API Spec v2

Platform: `caoshae8e528d1yp90app.ecwcloud.com`
Integration ID: `65afea2f-a46b-40f9-b831-abdb21b01738` (prod, Stevens)

## Invocation

```json
{
  "integration_id": "<uuid>",
  "account_id": "<uuid>",
  "input": {
    "action": "<action-name>",
    "patient_id": "<ecw-patient-id>",
    ...action-specific fields...
  }
}
```

## Test Patients

| Name | Patient ID | Notes |
|------|-----------|-------|
| **Beta Wedge** | `299227` | Primary test patient |
| Test Wedge | `298724` | Legacy test patient |

---

# Read Actions

## `read`

Read full patient demographics.

```json
{ "action": "read", "patient_id": "299227" }
```

Returns flat dict: `fname`, `lname`, `dob`, `sex`, `phone`, `email`, `address`, `maritalStatus`, `language`, `race`, `Ethnicity`, `GrId`, `GrRel`, `IsGrPt`, etc.

---

## `read-combos`

Read dropdown options for demographics form (marital status codes, employment status, etc).

```json
{ "action": "read-combos", "patient_id": "299227" }
```

---

## `read-sliding-fee`

Read current sliding fee schedule assignment.

```json
{ "action": "read-sliding-fee", "patient_id": "299227" }
```

Returns: `Income`, `Dependants`, `Unit`, `FeeSchedule`, `PovertyLevel`, `AssignedDate`, `ExpiryDate`, etc.

---

## `calculate`

Preview sliding fee calculation without saving.

```json
{ "action": "calculate", "patient_id": "299227", "Income": "3000", "Dependants": "2", "Unit": "Monthly" }
```

---

## `search-provider`

Search providers by name.

```json
{ "action": "search-provider", "patient_id": "299227", "search": "LastName, FirstName" }
```

Returns: `{ "providers": [...] }`

---

## `get-contacts`

Read patient contacts.

```json
{ "action": "get-contacts", "patient_id": "299227" }
{ "action": "get-contacts", "patient_id": "299227", "emergency_only": true }
```

Returns: `{ "contacts": [...] }`

---

## `read-sogi`

Read SOGI data + option lists with IDs.

```json
{ "action": "read-sogi", "patient_id": "299227" }
```

Returns: `patient_options` (current values) + `so_list`, `gi_list`, `pp_list` (lookup tables with IDs for save-sogi).

---

## `read-parent-info`

Read parent/guardian info.

```json
{ "action": "read-parent-info", "patient_id": "299227" }
```

Returns: `Mom1`, `Mom1Ph`, `Mom1Email`, `Mom2`..., `Dad1`..., `Dad2`..., `Other`..., `OtherPh`, `OtherEmail`

---

## `read-lrte`

Read current language, race, ethnicity data for the patient.

```json
{ "action": "read-lrte", "patient_id": "299227" }
```

---

## `lrte-lookup`

Search race/language/ethnicity dropdown values.

```json
{ "action": "lrte-lookup", "patient_id": "299227", "lrte_type": "race", "search": "White" }
{ "action": "lrte-lookup", "patient_id": "299227", "lrte_type": "language", "search": "Spanish" }
{ "action": "lrte-lookup", "patient_id": "299227", "lrte_type": "ethnicity", "search": "Hispanic" }
```

Returns array of `{ id, name, code, source }` objects.

---

## `read-structured-data`

Read Additional Information structured data fields (Homeless, Veteran, etc).

```json
{ "action": "read-structured-data", "patient_id": "299227" }
```

Returns flat dict: `{ "Homeless": "Yes", "Veteran": "No", "Public Housing": "Yes", ... }`

---

# Write Actions

## `edit-demographics`

Read-modify-write. Only include fields you want to change in `changes`.

```json
{
  "action": "edit-demographics",
  "patient_id": "299227",
  "changes": {
    "fname": "Jane",
    "lname": "Doe",
    "phone": "555-123-1111",
    "maritalStatus": "Married",
    "language": "English",
    "race": "Asian",
    "Ethnicity": "Hispanic or Latino",
    "sogi_data": { ... },
    "parent_data": { ... },
    "income_data": { ... },
    "contact": { ... },
    "GrId": "299227",
    "GrRel": "1",
    "IsGrPt": "1"
  }
}
```

Everything goes inside `changes`. Sub-objects (`sogi_data`, `parent_data`, `income_data`, `contact`, `update_contact`) are extracted and dispatched to their respective endpoints.

### Personal Info

| Field | Format | Description |
|---|---|---|
| `fname` | text | First name |
| `lname` | text | Last name |
| `mname` | text | Middle name |
| `PreferredName` | text | Preferred name |
| `prefix` | `""` `"Mr."` `"Mrs."` `"Ms."` `"Dr."` | Prefix |
| `suffix` | `""` `"Jr."` `"Sr."` `"II"` `"III"` | Suffix |
| `dob` | `MM/DD/YYYY` | Date of birth |
| `sex` | `"male"` / `"female"` | Sex |
| `ssn` | `999-99-9999` | SSN |
| `status` | `"0"` Active, `"1"` Inactive | Patient status |

### Contact

| Field | Format |
|---|---|
| `phone` | `999-999-9999` (home) |
| `mobile` | `999-999-9999` (cell) |
| `email` | email address |

### Address

| Field | Format |
|---|---|
| `address1` | Street line 1 |
| `address2` | Street line 2 |
| `city` | City |
| `state` | 2-letter code |
| `zip` | `"90210"` or `"90210-1234"` |
| `Country` | 2-letter code |

### Demographics

| Field | Format | Description |
|---|---|---|
| `maritalStatus` | `"Single"` `"Married"` `"Divorced"` `"Widowed"` | Also accepts `maritalstatus` |
| `race` | `"White"` `"Asian"` `"Asian,White"` or `[{name, code, id}]` | Auto-resolved via LRTE |
| `language` | `"English"` `"Spanish"` `"French"` etc. | Auto-resolved. Sets translator for non-English |
| `Ethnicity` | `"Hispanic or Latino"` `"Not Hispanic or Latino"` | Auto-resolved via LRTE |
| `TransGender` | `"Y"` / `"N"` | Transgender flag |
| `Translator` | `"0"` / `"1"` | Needs translator |

### Employment

| Field | Format |
|---|---|
| `empName` | Employer name |
| `empAddress` / `empCity` / `empState` / `empZip` / `empPhone` | Employer address |
| `EmpStatus` | `"1"` Employed, `"2"` Unemployed, `"3"` Retired |
| `StudentStatus` | `"F"` Full, `"P"` Part, `"N"` Not |

### Providers

| Field | Description |
|---|---|
| `doctorId` | PCP ID (use `search-provider` to find) |
| `refPrId` | Referring provider |
| `rendPrId` | Rendering provider |

### Responsible Party / Guarantor

| Field | Format | Description |
|---|---|---|
| `GrId` | patient ID | Guarantor ID |
| `GrRel` | `"1"` Self, `"2"` Spouse, `"3"` Parent | Relationship |
| `IsGrPt` | `"0"` / `"1"` | Guarantor is a patient |

### SOGI (`sogi_data`)

Use `read-sogi` to get option lists with IDs first.

```json
"sogi_data": {
  "birthsex": "F",
  "transgender": "N",
  "so_id": 3,
  "gi_ids": [2],
  "pp_ids": [2]
}
```

| Field | Format | Description |
|---|---|---|
| `birthsex` | `"M"` `"F"` `""` | Sex assigned at birth. Auto-sets `birthsex_changed=true` when present. |
| `transgender` | `"Y"` / `"N"` | Auto-sets `transgender_changed=true` when present. |
| `so_id` | int | Sexual orientation ID (from `so_list`) |
| `gi_ids` | list of ints or comma-separated | Gender identity IDs (from `gi_list`) |
| `pp_ids` | list of ints or comma-separated | Pronoun IDs (from `pp_list`) |
| `so_reason` / `gi_reason` / `pp_reason` | text | Custom reason text |
| `so_date` / `gi_date` | `MM/YYYY` | Date |

### Parent Info (`parent_data`)

```json
"parent_data": {
  "Mom1": "Mary Smith", "Mom1Ph": "555-123-4567", "Mom1Email": "mary@example.com",
  "Dad1": "John Smith", "Dad1Ph": "555-987-6543"
}
```

| Field | Description |
|---|---|
| `Mom1` / `Mom1Ph` / `Mom1Email` | Mother 1 |
| `Mom2` / `Mom2Ph` / `Mom2Email` | Mother 2 |
| `Dad1` / `Dad1Ph` / `Dad1Email` | Father 1 |
| `Dad2` / `Dad2Ph` / `Dad2Email` | Father 2 |
| `Other` / `OtherPh` / `OtherEmail` | Other guardian |

### Income (`income_data`)

Expires previous assignment, calculates, assigns new.

```json
"income_data": {
  "Income": "50000",
  "Dependants": "4",
  "Unit": "Annual"
}
```

| Field | Format |
|---|---|
| `Income` | Numeric string |
| `Dependants` | Numeric string |
| `Unit` | `"Monthly"` / `"Annual"` / `"Weekly"` / `"Bi-Weekly"` |
| `AssignedDate` | `YYYY-MM-DD` (default: today) |
| `ExpiryDate` | `YYYY-MM-DD` (default: +1 year) |

### Emergency Contact (`contact`)

```json
"contact": {
  "Fname": "Jane", "Lname": "Doe", "relation": "Spouse",
  "homePhone": "555-987-6543", "isEmergencyContact": "1"
}
```

| Field | Format |
|---|---|
| `Fname` / `Lname` | Name |
| `relation` | `"Spouse"` `"Parent"` `"Child"` `"Friend"` `"Other"` |
| `homePhone` / `CellPhone` / `workPhone` | Phone |
| `Email` | Email |
| `isEmergencyContact` | `"0"` / `"1"` |
| `Guardian` | `"0"` / `"1"` |

### Update Contact (`update_contact`)

```json
"update_contact": {
  "contact_id": "12345",
  "homePhone": "555-111-2222"
}
```

---

## `add-contact`

Standalone contact creation (outside of edit-demographics).

```json
{
  "action": "add-contact",
  "patient_id": "299227",
  "contact": { "Fname": "Jane", "Lname": "Doe", "relation": "Friend", "homePhone": "555-000-1111" }
}
```

Returns `{ "status_code": 200, "contactId": "12345" }`. Returns `status_code: 400` if duplicate or failed.

---

## `update-contact`

```json
{
  "action": "update-contact",
  "patient_id": "299227",
  "contact_id": "12345",
  "contact": { "homePhone": "555-999-8888" }
}
```

---

## `set-responsible-party`

```json
{
  "action": "set-responsible-party",
  "patient_id": "299227",
  "gr_id": "299227", "gr_rel": "1", "is_gr_pt": "1"
}
```

---

## `edit-income`

Standalone income edit (outside of edit-demographics). Expires previous → calculates → assigns.

```json
{
  "action": "edit-income",
  "patient_id": "299227",
  "income_data": { "Income": "3000", "Dependants": "2", "Unit": "Monthly" }
}
```

---

## `save-sogi`

Standalone SOGI save.

```json
{
  "action": "save-sogi",
  "patient_id": "299227",
  "sogi_data": { "birthsex": "F", "transgender": "N", "pp_ids": "2", "so_id": "3", "gi_ids": "2" }
}
```

---

## `save-parent-info`

```json
{
  "action": "save-parent-info",
  "patient_id": "299227",
  "parent_data": {
    "Mom1": "Test Mom", "Mom1Ph": "555-100-0001", "Mom1Email": "mom@test.com",
    "Mom2": "", "Mom2Ph": "", "Mom2Email": "",
    "Dad1": "", "Dad1Ph": "", "Dad1Email": "",
    "Dad2": "", "Dad2Ph": "", "Dad2Email": "",
    "Other": "", "OtherPh": "", "OtherEmail": ""
  }
}
```

---

## `save-lrte`

Direct LRTE save (race/language/ethnicity).

```json
{
  "action": "save-lrte",
  "patient_id": "299227",
  "lrte_type": "race",
  "entries": [{ "id": 1043, "name": "White", "code": "2106-3" }]
}
```

---

## `save-structured-data`

Save Additional Information structured data fields. Only include fields to change — others are preserved.

```json
{
  "action": "save-structured-data",
  "patient_id": "299227",
  "structured_data": {
    "Homeless": "Yes",
    "Veteran": "No",
    "Public Housing": "Yes",
    "Uninsured": "No"
  }
}
```

Valid field names: `Homeless`, `Seasonal Agricultural Worker`, `Migrant Agricultural Worker`, `Veteran`, `Public Housing`, `Uninsured`, `Last Registration Update` (MM-YYYY), `Monthly Estimated Income` (number), `Family Size` (number), `Primary Dentist` (text).

Values: `"Yes"` / `"No"` for checkbox fields, text/number for others. Supports notes: `{ "value": "Yes", "notes": "Some comment" }`.

---

## `upload-insurance-card`

Upload insurance card image to Patient Docs → Insurance folder.

```json
{
  "action": "upload-insurance-card",
  "patient_id": "299227",
  "image_base64": "<base64-encoded image>",
  "filename": "front_of_card.png",
  "description": "Front of insurance card"
}
```

Accepts: PNG, JPG, GIF, PDF, BMP, TIFF.

Returns: `{ "status_code": 200, "documentId": "abc123", "fileName": "uuid_299227.png" }`

---

## `upload-profile-picture`

Upload patient profile picture.

```json
{
  "action": "upload-profile-picture",
  "patient_id": "299227",
  "image_base64": "<base64-encoded JPEG>"
}
```

Image is saved as `{patientId}.jpg` in `/mobiledoc/Patients/`.

Returns: `{ "status_code": 200, "body": "success", "fileName": "299227.jpg" }`
