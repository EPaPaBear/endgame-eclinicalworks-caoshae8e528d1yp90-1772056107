# eClinicalWorks Authentication Analysis

## Platform
- **Tenant:** `caoshae8e528d1yp90app.ecwcloud.com`
- **Type:** Multi-step encrypted login with 2FA
- **Framework:** AngularJS SPA (Java backend)

## Auth Ceremony

### Step 1: Session Bootstrap
- `GET /mobiledoc/jsp/webemr/login.jsp`
- Extracts: `JSESSIONID` (cookie), `X-CSRF-TOKEN` (meta tag), ApplicationGateway affinity cookies

### Step 2: RSA Key Exchange
- `GET /mobiledoc/jsp/webemr/getRsaPublicKey.jsp`
- Returns RSA-2048 public key (PEM)
- Used to encrypt a client-generated AES-256-GCM key

### Step 3: AES Key Registration
- Generate 32-byte AES key + 12-byte IV
- RSA-encrypt the AES key (PKCS1v15 padding, NOT OAEP)
- `POST /mobiledoc/jsp/webemr/setAESKey.jsp` with `{key: base64(rsa_encrypted_key)}`

### Step 4: Username Verification
- AES-GCM encrypt the username
- `POST /mobiledoc/jsp/webemr/verifyUname.jsp` with encrypted username
- Response: 302 redirect to `/getPwdPage.jsp` on success

### Step 5: Turnstile CAPTCHA (conditional)
- NOT enforced on this tenant as of testing
- If `turnstile_enforced` flag changes, sitekey + 2captcha solver is ready

### Step 6: Re-register AES Key
- Fresh AES key + IV for the password step
- Same RSA encrypt + POST to `setAESKey.jsp`

### Step 7: Password Submission
- Hash chain: `plaintext -> MD5(hex) -> SHA1(hex_string) -> AES-GCM encrypt`
- `POST /mobiledoc/jsp/webemr/processLoginRequest.jsp`
- Body includes encrypted password + metadata (practiceId, timezone, device info)
- Response: 302 chain -> `loginSuccess.jsp` -> `OTPVerification.jsp`

### Step 8: 2FA (Email Push)
- Server sends email to user's registered address via Mailgun
- Poll inbox for confirmation link or OTP code
- Follow confirmation link to complete auth

### Step 9: Session Capture
- Follow redirects to authenticated dashboard
- Capture final `JSESSIONID`, CSRF token, gateway affinity cookies

## Crypto Details

| Component | Algorithm | Notes |
|-----------|-----------|-------|
| RSA encryption | PKCS1v15 | JSEncrypt library = PKCS1v15, NOT OAEP |
| AES encryption | AES-256-GCM | forge library; output = `base64(iv + ciphertext + tag)` |
| Password hash | MD5 -> SHA1 | `MD5(password).hexdigest()` -> `SHA1(md5_hex_string).hexdigest()` |

## Session Output

```json
{
  "Cookie": "JSESSIONID=...; ApplicationGatewayAffinityCORS=...; ApplicationGatewayAffinity=...",
  "X-CSRF-TOKEN": "uuid-string",
  "X-Session-DID": "297477"
}
```

## Dependencies

- `httpx` (HTTP client with redirect control)
- `cryptography` (RSA + AES-GCM)
- Standard library: `hashlib`, `base64`, `json`, `re`
