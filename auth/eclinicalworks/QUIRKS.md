# eClinicalWorks Auth Quirks

## Crypto

- **JSEncrypt = PKCS1v15.** The JS library uses PKCS#1 v1.5 padding, not OAEP. Python `cryptography` must use `padding.PKCS1v15()`.
- **forge AES-GCM output format:** `base64(iv + ciphertext + tag)`. Python's `AESGCM.encrypt()` returns `ciphertext + tag`, so IV must be prepended manually before base64 encoding.
- **Password hash chain is hex strings, not bytes.** `MD5(password)` produces a hex string, then `SHA1` hashes that hex string (not the raw bytes). Getting this wrong produces a valid-looking but wrong hash.

## Session

- **Gateway affinity cookies required.** Azure Application Gateway sets `ApplicationGatewayAffinity` and `ApplicationGatewayAffinityCORS`. Both must be forwarded on all requests or the session becomes invalid.
- **CSRF token is per-session.** Extracted from `<meta name="_csrf" content="...">` on the login page. Must be sent as `X-CSRF-TOKEN` header on every subsequent request.
- **Session DID = TrUserId.** The `sessionDID` query parameter and `TrUserId` are the same value. Obtained from the authenticated dashboard after login.

## 2FA

- **Email push, not TOTP.** The server sends a confirmation email. No TOTP/authenticator app support on this tenant.
- **Polling required.** Must poll the email inbox (Mailgun API) for the confirmation link. Typical delivery time: 2-10 seconds.

## URL Construction

- **`pd` hash is mandatory on POST requests.** `pd = SHA256(urldecode(query_string + post_body).replace('+', ' '))`. Computed before `pd` itself is appended to the URL.
- **Timezone has raw slash.** `clientTimezone=Atlantic/Reykjavik` — the `/` must NOT be URL-encoded to `%2F`.
- **`datetime.strftime("%-m")` fails on Windows.** Use `f"{now.month}"` instead.

## Turnstile

- **Not currently enforced** on this tenant. The login flow checks a server flag; if enabled, a Cloudflare Turnstile challenge would appear on the password page.
- **2captcha integration ready** in the login script but dormant.
