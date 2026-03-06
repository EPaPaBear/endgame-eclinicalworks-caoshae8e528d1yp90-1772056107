"""
eClinicalWorks login script for tenant caoshae8e528d1yp90.
Endgame contract: def login(credentials, twofa_config=None) -> dict

Ceremony (from P3 trace of login_bundle_4.js):
1. GET login page -> CSRF + JSESSIONID
2. GET /getRsaPublicKey -> RSA 2048 public key
3. Generate AES-256-GCM key(32b) + IV(12b) -> RSA-encrypt key -> POST /setAESKey
4. AES-GCM(username) -> POST /verifyUname -> 302 /getPwdPage
5. Turnstile: NOT enforced on this tenant (handled if flag changes)
6. Re-register AES key for step 2
7. AES-GCM(SHA1(MD5(password))) + metadata -> POST /processLoginRequest
8. 302 -> loginSuccess.jsp -> 302 -> OTPVerification.jsp
9. 2FA: Email push notification; poll mailgun for confirm link or OTP
10. Follow to authenticated dashboard, extract session cookies

Password hash chain: plaintext -> MD5(hex) -> SHA1(hex_string) -> AES-GCM encrypt
"""

import base64
import hashlib
import json
import os
import re
import time
import urllib.request
import urllib.parse
from datetime import datetime

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding as rsa_padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


BASE_URL = "https://caoshae8e528d1yp90app.ecwcloud.com"
MAILGUN_DOMAIN = "inbox.integuru.ai"

# 2captcha key (ASCII85 encoded) â€” used only if Turnstile is enforced
_CAPTCHA_KEY_ENC = "1cREP11Xm)2e-8OAMZ;(AiDDU@qIGU2DI.!2dp/U"


# =============================================================================
# CRYPTO
# =============================================================================

def _gen_aes():
    """Generate AES-256-GCM key (32 bytes) + IV (12 bytes) as base64 strings."""
    return base64.b64encode(os.urandom(32)).decode(), base64.b64encode(os.urandom(12)).decode()


def _rsa_encrypt(data: str, rsa_pub_b64: str) -> str:
    """RSA-encrypt with PKCS1v15 (matches JSEncrypt). Returns base64."""
    pub = serialization.load_der_public_key(base64.b64decode(rsa_pub_b64))
    enc = pub.encrypt(data.encode(), rsa_padding.PKCS1v15())
    return base64.b64encode(enc).decode()


def _aes_gcm_encrypt(data: str, key_b64: str, iv_b64: str) -> str:
    """AES-256-GCM encrypt. Output: base64(iv + ciphertext + tag) matching JS forge."""
    key, iv = base64.b64decode(key_b64), base64.b64decode(iv_b64)
    ct_tag = AESGCM(key).encrypt(iv, data.encode(), None)
    return base64.b64encode(iv + ct_tag).decode()


def _hash_password(pw: str) -> str:
    """Password hash chain: SHA1(MD5(plaintext)) â€” both return lowercase hex."""
    return hashlib.sha1(hashlib.md5(pw.encode()).hexdigest().encode()).hexdigest()


# =============================================================================
# HTML HELPERS
# =============================================================================

def _extract_csrf(html: str) -> str:
    m = re.search(r'<meta\s+name="_csrf"\s+content="([^"]+)"', html)
    if m:
        return m.group(1)
    m = re.search(r'name="_csrf"\s+value="([^"]+)"', html)
    return m.group(1) if m else ""


def _extract_var(html: str, name: str):
    m = re.search(rf"var\s+{name}\s*=\s*'([^']*)'", html)
    if m:
        return m.group(1)
    m = re.search(rf"var\s+{name}\s*=\s*([^;\s]+)", html)
    return m.group(1).strip("'\"") if m else None


def _extract_form_action(html: str, form_id: str) -> str:
    m = re.search(rf'<form[^>]*id="{form_id}"[^>]*action="([^"]*)"', html, re.I)
    return m.group(1) if m else ""


# =============================================================================
# TURNSTILE SOLVER
# =============================================================================

def _solve_turnstile(site_key: str, page_url: str) -> str:
    """Solve Cloudflare Turnstile via 2captcha. Blocking."""
    api_key = base64.a85decode(_CAPTCHA_KEY_ENC).decode()
    # Create task
    req_data = json.dumps({
        "clientKey": api_key,
        "task": {"type": "TurnstileTaskProxyless", "websiteURL": page_url, "websiteKey": site_key},
    }).encode()
    req = urllib.request.Request("https://api.2captcha.com/createTask",
                                data=req_data, headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if resp.get("errorId") != 0:
        raise Exception(f"Turnstile submit failed: {resp.get('errorDescription')}")
    task_id = resp["taskId"]

    # Poll for result
    time.sleep(10)
    for _ in range(24):
        poll_data = json.dumps({"clientKey": api_key, "taskId": task_id}).encode()
        poll_req = urllib.request.Request("https://api.2captcha.com/getTaskResult",
                                         data=poll_data, headers={"Content-Type": "application/json"})
        result = json.loads(urllib.request.urlopen(poll_req, timeout=30).read())
        if result.get("status") == "ready":
            return result["solution"]["token"]
        if result.get("errorId") != 0:
            raise Exception(f"Turnstile solve failed: {result.get('errorDescription')}")
        time.sleep(5)
    raise Exception("Turnstile not solved within 120s")


# =============================================================================
# MAILGUN 2FA
# =============================================================================

def _poll_mailgun(email_address: str, mailgun_api_key: str, timeout: int = 120, interval: int = 5) -> dict:
    """
    Poll Mailgun accepted events for incoming email to the given address.
    Only considers emails that arrive AFTER this function is called (prevents
    stale confirm URLs from previous runs).
    Returns dict with 'otp' (if found), 'confirm_url' (if found), 'subject', 'body'.
    """
    start = time.time()
    seen_ids = set()

    while time.time() - start < timeout:
        url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/events?event=accepted&recipient={email_address}&limit=5"
        req = urllib.request.Request(url)
        credentials = base64.b64encode(f"api:{mailgun_api_key}".encode()).decode()
        req.add_header("Authorization", f"Basic {credentials}")

        try:
            resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
        except Exception:
            time.sleep(interval)
            continue

        items = resp.get("items", [])
        for item in items:
            msg_id = item.get("message", {}).get("headers", {}).get("message-id", "")
            if msg_id in seen_ids:
                continue

            # Only accept emails that arrived AFTER we started polling
            ts = item.get("timestamp", 0)
            if ts < start:
                seen_ids.add(msg_id)
                continue

            # Fetch the stored message
            storage_url = item.get("storage", {}).get("url", "")
            if not storage_url:
                seen_ids.add(msg_id)
                continue

            msg_req = urllib.request.Request(storage_url)
            msg_req.add_header("Authorization", f"Basic {credentials}")
            try:
                msg_data = json.loads(urllib.request.urlopen(msg_req, timeout=15).read())
            except Exception:
                seen_ids.add(msg_id)
                continue

            subject = msg_data.get("subject", "")
            body = msg_data.get("body-plain", "") or msg_data.get("stripped-text", "")
            body_html = msg_data.get("body-html", "")

            # Extract 6-digit OTP code
            otp_match = re.search(r'\b(\d{6})\b', body)
            otp = otp_match.group(1) if otp_match else None

            # Extract confirmation URL â€” look for the "Yes" link (verifyEmailNSMS)
            confirm_url = None
            # In HTML: the "Yes, it's me" link precedes the "No" link
            # The "Yes" JWT contains isConfirm:"yes", the "No" JWT contains isConfirm:"no"
            # Match the first verifyEmailNSMS URL (which is the "Yes" one)
            for pattern in [
                r'href="(https?://[^"]+verifyEmailNSMS\?token=[^"]+)"',
                r'(https?://[^\s"<>]+verifyEmailNSMS\?token=[^\s"<>]+)',
                r'(https?://[^\s"<>]+(?:confirm|verify|approve)[^\s"<>]*)',
            ]:
                url_match = re.search(pattern, body_html or body, re.I)
                if url_match:
                    confirm_url = url_match.group(1)
                    break

            if otp or confirm_url:
                return {"otp": otp, "confirm_url": confirm_url, "subject": subject, "body": body[:500]}

            seen_ids.add(msg_id)

        time.sleep(interval)

    raise Exception(f"No 2FA email received within {timeout}s for {email_address}")


# =============================================================================
# LOGIN
# =============================================================================

def login(username: str, password: str) -> dict:
    """
    Authenticate against eClinicalWorks and return flat dict of HTTP headers.

    Backend contract: login(username, password) -> dict
    2FA: Uses fetch_2fa_code() if available (injected by backend), falls back to
         direct mailgun polling via MAILGUN_API_KEY env var.
    """
    # Resolve mailgun API key from environment (fallback for local testing)
    mailgun_key = os.environ.get("MAILGUN_API_KEY", "")
    # Account-specific 2FA email â€” backend sets this, or derive from env
    twofa_email = os.environ.get("TWOFA_EMAIL", "")

    headers_common = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    with httpx.Client(timeout=30.0, follow_redirects=False, headers=headers_common) as client:

        # â”€â”€ Step 1: GET login page â”€â”€
        print("[1/9] Loading login page...")
        r = client.get(f"{BASE_URL}/mobiledoc/jsp/webemr/login/newLogin.jsp")
        if r.status_code != 200:
            raise Exception(f"Login page returned {r.status_code}")
        csrf = _extract_csrf(r.text)
        if not csrf:
            raise Exception("CSRF token not found")
        print(f"  CSRF: {csrf[:20]}...")

        # â”€â”€ Step 2: GET RSA public key â”€â”€
        print("[2/9] Fetching RSA key...")
        r = client.get(f"{BASE_URL}/mobiledoc/jsp/webemr/login/authenticate/getRsaPublicKey")
        rsa_key = r.json().get("publicKey", "")
        if not rsa_key:
            raise Exception("RSA key not returned")

        # â”€â”€ Step 3: Register AES-GCM key â”€â”€
        print("[3/9] Registering AES key...")
        aes_key, aes_iv = _gen_aes()
        enc_key = _rsa_encrypt(aes_key, rsa_key)
        r = client.post(
            f"{BASE_URL}/mobiledoc/jsp/webemr/login/authenticate/setAESKey?action=1043",
            data={"encKeyValue": enc_key, "isNewAlgo": "yes", "usage": "loginDataEncGCM"},
            headers={"X-CSRF-Token": csrf, "Content-Type": "application/x-www-form-urlencoded",
                     "X-Requested-With": "XMLHttpRequest", "isAjaxRequest": "true"},
        )
        if r.text.strip() != "success":
            raise Exception(f"AES key registration failed: {r.text.strip()}")

        # â”€â”€ Step 4: Verify username â”€â”€
        print("[4/9] Verifying username...")
        enc_user = _aes_gcm_encrypt(username, aes_key, aes_iv)
        r = client.post(
            f"{BASE_URL}/mobiledoc/jsp/webemr/login/authenticate/verifyUname",
            data={"username": enc_user, "_csrf": csrf},
            headers={"Content-Type": "application/x-www-form-urlencoded",
                     "Referer": f"{BASE_URL}/mobiledoc/jsp/webemr/login/newLogin.jsp"},
        )

        # Follow redirect to getPwdPage
        step2_url = f"{BASE_URL}/mobiledoc/jsp/webemr/login/authenticate/getPwdPage"
        if r.status_code in (301, 302, 303):
            loc = r.headers.get("location", "")
            step2_url = loc if loc.startswith("http") else f"{BASE_URL}{loc}"
            r = client.get(step2_url)
        elif r.status_code != 200:
            raise Exception(f"Username verification failed: {r.status_code}")

        step2_html = r.text
        step2_csrf = _extract_csrf(step2_html)
        if step2_csrf:
            csrf = step2_csrf

        # Check for errors
        err_code = _extract_var(step2_html, "newLogin_errorCode")
        if err_code and err_code not in ("-99", "null", "None"):
            err_msg = _extract_var(step2_html, "newLogin_errMsg") or f"Error {err_code}"
            raise Exception(f"Username error: {err_msg}")

        # â”€â”€ Step 5: Solve Turnstile if enforced â”€â”€
        turnstile_flag = _extract_var(step2_html, "newLogin_strCloudFlareTurnstileEnable")
        sitekey = _extract_var(step2_html, "newLogin_cloudFlareSiteKey")
        turnstile_token = ""

        if turnstile_flag == "yes" and sitekey:
            print("[5/9] Solving Turnstile...")
            turnstile_token = _solve_turnstile(sitekey, step2_url)
            print(f"  Solved: {turnstile_token[:30]}...")
        else:
            print("[5/9] Turnstile not enforced, skipping")

        # â”€â”€ Step 6: Re-register AES key for step 2 â”€â”€
        print("[6/9] Re-registering AES key...")
        aes_key, aes_iv = _gen_aes()
        enc_key = _rsa_encrypt(aes_key, rsa_key)
        r = client.post(
            f"{BASE_URL}/mobiledoc/jsp/webemr/login/authenticate/setAESKey?action=1043",
            data={"encKeyValue": enc_key, "isNewAlgo": "yes", "usage": "loginDataEncGCM"},
            headers={"X-CSRF-Token": csrf, "Content-Type": "application/x-www-form-urlencoded",
                     "X-Requested-With": "XMLHttpRequest", "isAjaxRequest": "true"},
        )
        if r.text.strip() != "success":
            raise Exception(f"AES re-registration failed: {r.text.strip()}")

        # â”€â”€ Step 7: Submit password â”€â”€
        print("[7/9] Submitting password...")
        hashed_pw = _hash_password(password)
        enc = lambda d: _aes_gcm_encrypt(d, aes_key, aes_iv)
        now = datetime.now()

        has_digit = bool(re.search(r"\d", password))
        all_digits = bool(re.match(r"^\d+$", password))
        a_param = "Y" if (has_digit and not all_digits) else "N"

        payload = {
            "username": enc(username),
            "password": enc(hashed_pw),
            "lParam": enc(str(len(password))),
            "aParam": enc(a_param),
            "guideParam": enc("yes"),
            "chasip": enc(""),
            "_csrf": csrf,
            "clientLoginTime": f"{now.year}-{now.month}-{now.day} {now.hour}:{now.minute}:{now.second}",
            "selectModuleName": "",
            "pluginParam": "",
        }
        if turnstile_token:
            payload["turnstileResponse"] = enc(turnstile_token)

        form_action = _extract_form_action(step2_html, "loginForm")
        post_url = form_action if form_action else "/mobiledoc/jsp/webemr/login/authenticate/processLoginRequest"
        if not post_url.startswith("http"):
            post_url = f"{BASE_URL}{post_url}"

        r = client.post(post_url, data=payload, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": step2_url,
        })

        # Follow redirect chain (Referer required for session validation)
        for _ in range(10):
            if r.status_code not in (301, 302, 303, 307, 308):
                break
            loc = r.headers.get("location", "")
            if not loc:
                break
            url = loc if loc.startswith("http") else f"{BASE_URL}{loc}"
            print(f"  -> {r.status_code} {url}")
            r = client.get(url, headers={"Referer": post_url})

        final_url = str(r.url)
        print(f"  Final: {final_url} ({r.status_code})")

        # â”€â”€ Step 8: Handle 2FA â”€â”€
        if "OTPVerification" in final_url or "loginSuccess" in final_url:
            print(f"[8/9] 2FA required (final status {r.status_code})")
            otp_html = r.text if r.status_code == 200 else ""
            otp_csrf = _extract_csrf(otp_html) if otp_html else ""

            if not twofa_email or not mailgun_key:
                raise Exception(
                    "2FA required but no mailgun config. "
                    f"Set MAILGUN_API_KEY env var. twofa_email={twofa_email}"
                )

            print(f"  Polling mailgun for email to {twofa_email}...")
            email_data = _poll_mailgun(twofa_email, mailgun_key, timeout=120, interval=5)

            # Extract userId from OTP page for checkSecureToken polling
            user_id = ""
            if otp_html:
                uid_match = re.search(r'var\s+userId\s*=\s*(\d+)', otp_html)
                user_id = uid_match.group(1) if uid_match else ""

            if email_data.get("confirm_url"):
                # Push notification flow: visit the confirm URL from a SEPARATE
                # client (no session cookies). The login session must NOT visit
                # this URL â€” it invalidates the session. Instead, confirm externally
                # and poll checkSecureToken from the login session.
                confirm_url = email_data["confirm_url"]
                print(f"  Found confirm URL: {confirm_url[:80]}...")

                # Confirm from a separate HTTP client (no login cookies)
                confirm_r = httpx.get(confirm_url, follow_redirects=True, timeout=15)
                print(f"  Confirm response (external): {confirm_r.status_code}")

                # Poll checkSecureToken from the login session
                if user_id:
                    print(f"  Polling checkSecureToken for userId={user_id}...")
                    for poll_i in range(60):
                        check_r = client.get(
                            f"{BASE_URL}/mobiledoc/jsp/webemr/login/authenticate/checkSecureToken",
                            params={"userId": user_id},
                            headers={"X-CSRF-Token": otp_csrf or csrf,
                                     "X-Requested-With": "XMLHttpRequest",
                                     "isAjaxRequest": "true"},
                        )
                        try:
                            check_data = check_r.json()
                            status = check_data.get("isVerified", "")
                            if poll_i == 0 or poll_i % 5 == 0:
                                print(f"    Poll {poll_i}: {check_data}")
                            if status == "yes":
                                print("  2FA verified via push notification!")
                                break
                        except (json.JSONDecodeError, AttributeError):
                            pass
                        time.sleep(2)
                    else:
                        raise Exception("checkSecureToken polling timed out (120s)")

                # Navigate to dashboard after verification
                r = client.get(
                    f"{BASE_URL}/mobiledoc/jsp/webemr/index.jsp",
                    headers={"Referer": f"{BASE_URL}/mobiledoc/jsp/webemr/login/OTPVerification.jsp"},
                )
                # Follow redirects
                for _ in range(10):
                    if r.status_code not in (301, 302, 303, 307, 308):
                        break
                    loc = r.headers.get("location", "")
                    if not loc:
                        break
                    url = loc if loc.startswith("http") else f"{BASE_URL}{loc}"
                    print(f"  -> {r.status_code} {url}")
                    r = client.get(url, headers={"Referer": post_url})
                print(f"  Dashboard: {r.status_code} -> {r.url}")

            elif email_data.get("otp"):
                # OTP code flow: submit the 6-digit code
                otp_code = email_data["otp"]
                print(f"  Found OTP code: {otp_code}")

                otp_form_action = _extract_form_action(otp_html, "OTPForm") if otp_html else ""
                if not otp_form_action:
                    otp_form_action = "/mobiledoc/jsp/webemr/login/authenticate/validateOTP"
                if not otp_form_action.startswith("http"):
                    otp_form_action = f"{BASE_URL}{otp_form_action}"

                r = client.post(otp_form_action, data={
                    "OTPCode": otp_code,
                    "_csrf": otp_csrf or csrf,
                }, headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": final_url,
                })

                # Follow redirects after OTP submission
                for _ in range(10):
                    if r.status_code not in (301, 302, 303, 307, 308):
                        break
                    loc = r.headers.get("location", "")
                    if not loc:
                        break
                    url = loc if loc.startswith("http") else f"{BASE_URL}{loc}"
                    print(f"  -> {r.status_code} {url}")
                    r = client.get(url)

            else:
                raise Exception("No OTP code or confirm URL found in email")

            final_url = str(r.url)
        else:
            print("[8/9] No 2FA required")

        # â”€â”€ Step 9: Extract session headers â”€â”€
        print("[9/9] Extracting session headers...")

        # Build Cookie header from all cookies in the jar
        cookie_parts = []
        for cookie in client.cookies.jar:
            cookie_parts.append(f"{cookie.name}={cookie.value}")

        result_headers = {}
        if cookie_parts:
            result_headers["Cookie"] = "; ".join(cookie_parts)

        # Add CSRF header for authenticated requests
        final_csrf = _extract_csrf(r.text) if r.status_code == 200 else ""
        if not final_csrf:
            final_csrf = csrf
        result_headers["X-CSRF-TOKEN"] = final_csrf
        print(f"  CSRF: {final_csrf[:30]}...")

        print(f"  Final URL: {final_url}")
        print(f"  Headers: {list(result_headers.keys())}")

        if not result_headers.get("Cookie"):
            raise Exception("No session cookies obtained")

        return result_headers


def determine_base_url(username: str, password: str) -> str:
    """Return the post-login base URL for this tenant (static â€” no login needed)."""
    return BASE_URL
