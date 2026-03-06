# Scrape Summary

## Platform
eClinicalWorks EMR - tenant `caoshae8e528d1yp90`

## Assets Collected

| Category | Count | Location |
|----------|-------|----------|
| JS controllers/services | 569 files | `mobiledoc/` |
| Combined bundle | 1 file | `mobiledoc/combined.js` |
| Auth network capture | 1 file | `../auth/network_capture.json` -> moved to `auth/eclinicalworks/` |
| Auth session dump | 1 file | `../auth/auth_dump.json` |

## Key Source Files

### Demographics & Patient Info
- `mobiledoc/jsp/webemr/toppanel/patientInfo/ptInfoController.js` - Patient info CRUD
- `mobiledoc/jsp/webemr/toppanel/patientInfo/contactController.js` - Contact management
- `mobiledoc/jsp/webemr/toppanel/patientInfo/addUpdateInsurance.js` - Insurance add/update (116KB)

### Sliding Fee Schedule
- `mobiledoc/jsp/webemr/toppanel/patientInfo/slidingfeescheduleController.js` - SFDP controller (55KB)

### Auth
- `mobiledoc/combined.js` - Contains login bundle with RSA/AES ceremony

### Provider Search
- `mobiledoc/jsp/webemr/toppanel/patientInfo/ProviderLookupPickListController.js`

## Scrape Method
- Chrome TLS impersonation via `curl_cffi` (surface_recon.py)
- Authenticated session cookies used for post-login asset download
- `fetch_resource.py` for bulk authenticated resource fetching
