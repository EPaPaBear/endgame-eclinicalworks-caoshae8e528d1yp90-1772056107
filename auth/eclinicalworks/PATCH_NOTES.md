# eClinicalWorks Integration — Patch Notes

## 2026-03-20

### Bug Fixes

**Insurance: SubscriberId / GroupNo not saving**
- `SubscriberId` in input now correctly maps to ECW's `SubscriberNo` XML field (applies to both `add-insurance` and `update-insurance`)
- `add-insurance` now uses `Id=-1` for new records (was `0`, which ECW silently ignored)
- `CopayMethod` defaults to `"$"` matching browser behavior
- **Important**: `InsuranceId` must be a valid carrier ID. Use `list-carriers` or `search-carriers` to get valid IDs.

### New Features

**`workPhone` field in edit-demographics**
- Set patient work phone: `"changes": { "workPhone": "555-999-7777" }`
- Visible in the Phone List (click "Manage Phone List")
- Note: `read` returns work phone under `empPhone` only if set via Tab 2 employment fields; phone-list work phone is a separate record

**`list-carriers` action (ecw_sfdp)**
- Returns full list of insurance carriers without requiring a search term
- `search-carriers` also now accepts empty search to return all
- Use the `Id` from results as `InsuranceId` in `add-insurance`

```json
{ "action": "list-carriers", "patient_id": "299227" }
```

Returns: `{ "carriers": [{ "Id": "217", "Name": "Anthem Blue Cross - COMM", ... }, ...] }`
