# endgame-eclinicalworks-caoshae8e528d1yp90

Endgame integration for **eClinicalWorks** (tenant `caoshae8e528d1yp90`).

## Platform

| Field | Value |
|-------|-------|
| Platform | eClinicalWorks EMR |
| Tenant URL | `https://caoshae8e528d1yp90app.ecwcloud.com` |
| Auth Type | Multi-step RSA+AES encrypted login with email 2FA |
| Framework | AngularJS SPA, Java backend, SOAP XML API |

## Integrations

| Integration | File | Actions |
|-------------|------|---------|
| Demographics | `integrations/ecw_demographics.py` | read, edit-demographics, read-combos, read-sliding-fee, calculate, search-provider, get-contacts, add-contact, update-contact, set-responsible-party, edit-income |
| SFDP | `integrations/ecw_sfdp.py` | sliding-history, sliding-detail, other-income-reasons, find-members, get-insurance, search-carriers, delete-insurance, add-insurance, update-insurance, scenario-1/2/5/6/7 |

## Structure

```
auth/
  eclinicalworks/
    login_script.py          # Encrypted login ceremony + 2FA
    ANALYSIS_DOC.md          # Auth flow documentation
    QUIRKS.md                # Crypto and session gotchas
    flow.json                # Machine-readable ceremony steps
    network_capture.json     # Captured auth network requests
extractors/                  # (placeholder)
integrations/
  ecw_demographics.py        # Patient demographics + income CRUD
  ecw_sfdp.py                # Sliding Fee Discount Program orchestrator
scraped_data/
  assets/
    mobiledoc/               # 569 JS source files (controllers, services)
    SCRAPE_SUMMARY.md        # Asset inventory summary
    api_endpoints.txt        # Discovered API endpoints
  auth/
    auth_dump.json           # Session cookies/storage dump
validation/
  eclinicalworks_check.py    # Session validity checker
```

## Auth Ceremony (Summary)

1. GET login page -> CSRF + JSESSIONID
2. GET RSA public key (2048-bit)
3. Generate AES-256-GCM key, RSA-encrypt it (PKCS1v15), POST to setAESKey
4. AES-GCM(username) -> POST verifyUname
5. Re-register AES key
6. AES-GCM(SHA1(MD5(password))) -> POST processLoginRequest
7. 2FA: Poll email inbox for confirmation link
8. Follow redirects to dashboard, capture session

## API Pattern

All post-login API calls use SOAP XML wrapped in `FormData=` POST parameters.
URLs are constructed with `makeURL()` appending `sessionDID`, `TrUserId`, `timestamp`,
`clientTimezone`, and a `pd` SHA-256 integrity hash.

See `auth/eclinicalworks/ANALYSIS_DOC.md` and `auth/eclinicalworks/QUIRKS.md` for details.
