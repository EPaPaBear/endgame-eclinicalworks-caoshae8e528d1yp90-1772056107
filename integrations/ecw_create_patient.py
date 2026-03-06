"""
eClinicalWorks Create Patient Integration
Platform: caoshae8e528d1yp90app.ecwcloud.com

Creates a new patient via the Patient Quick Registration flow.
Returns the newly created patient ID.

Two-step process:
  1. POST setPatient.jsp?patientId=0 → returns new patient ID
  2. POST saveUnseenPatient.jsp?patientId={newId} → finalizes the record
"""

import hashlib
import re
import time
import urllib.parse
from datetime import datetime
from html import escape as html_escape
from xml.etree import ElementTree as ET

import requests

# Runtime-injected BASE_URL from generic executor
base_url = globals().get("BASE_URL") or "https://caoshae8e528d1yp90app.ecwcloud.com"
DEFAULT_SESSION_DID = "297477"


def run(headers: dict, user_input: dict = None) -> dict:
    """Create a new patient in eClinicalWorks.

    Required fields:
      fname (str): Patient's first name
      lname (str): Patient's last name
      dob   (str): Date of birth in YYYY-MM-DD format
      sex   (str): 'Male', 'Female', or 'Unknown'

    Optional fields:
      mname    (str): Middle name
      phone    (str): Phone number in XXX-XXX-XXXX format
      email    (str): Email address
      address1 (str): Street address line 1
      address2 (str): Street address line 2
      city     (str): City (letters and spaces only)
      state    (str): 2-letter state code (e.g. 'CA')
      zip      (str): ZIP code (e.g. '90210' or '90210-1234')
      country  (str): 2-letter country code (e.g. 'US')

    Returns:
      {"status_code": 200, "body": {"patient_id": "...", "message": "..."}}
    """
    user_input = user_input or {}

    # --- Validate required fields ---
    fname = (user_input.get("fname") or "").strip()
    lname = (user_input.get("lname") or "").strip()
    dob_raw = (user_input.get("dob") or "").strip()
    sex = (user_input.get("sex") or "").strip()

    if not fname:
        return {"status_code": 400, "body": {"error": "fname (first name) is required"}}
    if not lname:
        return {"status_code": 400, "body": {"error": "lname (last name) is required"}}
    if not dob_raw:
        return {"status_code": 400, "body": {"error": "dob (date of birth) is required"}}
    if not sex:
        return {"status_code": 400, "body": {"error": "sex is required ('Male', 'Female', or 'Unknown')"}}

    if sex not in ("Male", "Female", "Unknown"):
        return {"status_code": 400, "body": {"error": "sex must be 'Male', 'Female', or 'Unknown'"}}

    # Convert YYYY-MM-DD → MM/DD/YYYY for the platform
    try:
        dob_parsed = datetime.strptime(dob_raw, "%Y-%m-%d")
        dob = dob_parsed.strftime("%m/%d/%Y")
    except ValueError:
        return {"status_code": 400, "body": {"error": "dob must be in YYYY-MM-DD format"}}

    if dob_parsed.date() > datetime.now().date():
        return {"status_code": 400, "body": {"error": "dob cannot be a future date"}}

    # --- Optional fields ---
    mname = (user_input.get("mname") or "").strip()
    phone = (user_input.get("phone") or "").strip()
    email = (user_input.get("email") or "").strip()
    address1 = (user_input.get("address1") or "").strip()
    address2 = (user_input.get("address2") or "").strip()
    city = (user_input.get("city") or "").strip()
    state = (user_input.get("state") or "").strip()
    zip_code = (user_input.get("zip") or "").strip()
    country = (user_input.get("country") or "").strip()

    # --- Build session ---
    session = _build_session_from_headers(headers)

    with requests.Session() as client:
        client.cookies.update(session["cookies"])

        # --- STEP 1: Create patient via setPatient.jsp ---
        xml_step1 = _build_patient_xml(
            fname=fname, lname=lname, mname=mname, phone=phone,
            email=email, dob=dob, sex=sex, address1=address1,
            address2=address2, city=city, state=state, zip_code=zip_code,
            country=country, urefid="0",
        )

        r1 = _post(client, session,
                    "/mobiledoc/jsp/catalog/xml/setPatient.jsp?patientId=0",
                    {"FormData": xml_step1})

        # Check for auth failure
        if r1.status_code in (401, 403):
            return {"status_code": 401, "body": {"error": "Session expired"}}
        if "login" in r1.url.lower() or "newLogin.jsp" in r1.text:
            return {"status_code": 401, "body": {"error": "Session expired"}}

        r1.raise_for_status()

        # Extract patient ID from response
        patient_id = _extract_patient_id(r1.text)
        if not patient_id or not patient_id.isdigit():
            return {"status_code": 500, "body": {
                "error": "Failed to extract patient ID from response",
                "raw_response": r1.text[:500],
            }}

        # --- STEP 2: Finalize with saveUnseenPatient.jsp ---
        xml_step2 = _build_patient_xml(
            fname=fname, lname=lname, mname=mname, phone=phone,
            email=email, dob=dob, sex=sex, address1=address1,
            address2=address2, city=city, state=state, zip_code=zip_code,
            country=country, urefid=patient_id,
        )

        r2 = _post(client, session,
                    f"/mobiledoc/jsp/catalog/xml/saveUnseenPatient.jsp?patientId={patient_id}",
                    {"FormData": xml_step2})

        if r2.status_code in (401, 403):
            return {"status_code": 401, "body": {"error": "Session expired"}}

        r2.raise_for_status()

        return {
            "status_code": 200,
            "body": {
                "patient_id": patient_id,
                "message": f"Patient created successfully",
            },
        }


# === PRIVATE ===

def _escape_xml(value: str) -> str:
    if not value:
        return value or ""
    return html_escape(str(value), quote=True)


def _generate_pd_hash(query_string: str, post_body: str) -> str:
    concatenated = query_string + post_body
    decoded = urllib.parse.unquote(concatenated)
    replaced = decoded.replace("+", " ")
    return hashlib.sha256(replaced.encode()).hexdigest()


def _make_url(path: str, session: dict, post_body: str = None) -> str:
    url = f"{base_url}{path}"
    parsed = urllib.parse.urlparse(url)
    q = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)

    ts = str(int(time.time() * 1000))
    q.append(("sessionDID", session["session_did"]))
    q.append(("TrUserId", session["tr_user_id"]))
    q.append(("Device", "webemr"))
    q.append(("ecwappprocessid", session.get("ecwappprocessid", "0")))
    q.append(("timestamp", ts))
    q.append(("clientTimezone", "Atlantic/Reykjavik"))

    query_string = urllib.parse.urlencode(q, quote_via=urllib.parse.quote)

    if post_body is not None:
        pd_hash = _generate_pd_hash(query_string, post_body)
        q.append(("pd", pd_hash))

    new_query = urllib.parse.urlencode(q, quote_via=urllib.parse.quote)
    return urllib.parse.urlunparse(parsed._replace(query=new_query))


def _soap_envelope(body_xml: str) -> str:
    return (
        '<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" '
        'S:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" '
        'xmlns:xsd="http://www.w3.org/1999/XMLSchema" '
        'xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance">'
        f'<Body><m:NOOP xmlns:m="NOOP">{body_xml}</m:NOOP></Body>'
        '</S:Envelope>'
    )


def _add_element(name: str, value, xsi_type: str = "xsd:string") -> str:
    val = str(value) if value is not None else ""
    inner = _escape_xml(val)
    return f'<{name} xsi:type="{xsi_type}">{inner}</{name}>'


def _build_patient_xml(*, fname, lname, mname, phone, email, dob, sex,
                       address1, address2, city, state, zip_code, country,
                       urefid) -> str:
    """Build the SOAP XML envelope for the patient quick registration."""
    elements = []
    elements.append(_add_element("fname", fname))
    elements.append(_add_element("lname", lname))
    elements.append(_add_element("mname", mname))
    elements.append(_add_element("phone", phone))
    elements.append(_add_element("email", email))
    elements.append(_add_element("dob", dob))
    elements.append(_add_element("sex", sex))
    elements.append(_add_element("address1", address1))
    elements.append(_add_element("address2", address2))
    elements.append(_add_element("city", city))
    elements.append(_add_element("state", state))
    elements.append(_add_element("Country", country))
    elements.append(_add_element("zip", zip_code))
    elements.append(_add_element("primaryservicelocation", ""))
    elements.append(_add_element("ptseen", "yes"))
    elements.append(_add_element("ptsentto", ""))
    elements.append(_add_element("cc", ""))
    elements.append(_add_element("reason", ""))
    elements.append(_add_element("urefid", urefid))

    patient_xml = f'<patient>{"".join(elements)}</patient>'
    return _soap_envelope(patient_xml)


def _build_session_from_headers(auth_headers: dict) -> dict:
    cookie_str = auth_headers.get("Cookie", "")
    csrf_token = auth_headers.get("X-CSRF-TOKEN", "")
    session_did = auth_headers.get("X-Session-DID", DEFAULT_SESSION_DID)

    cookies = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()

    return {
        "cookies": cookies,
        "csrf_token": csrf_token,
        "session_did": session_did,
        "tr_user_id": session_did,
        "ecwappprocessid": "0",
        "timezone": "Atlantic/Reykjavik",
    }


def _get_headers(session: dict) -> dict:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/145.0.0.0 Safari/537.36",
        "X-CSRF-TOKEN": session["csrf_token"],
        "X-Requested-With": "XMLHttpRequest",
        "isAjaxRequest": "true",
        "cip": "null",
        "Origin": base_url,
        "Referer": f"{base_url}/mobiledoc/jsp/webemr/index.jsp",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }


def _post(client: requests.Session, session: dict, path: str,
          data: dict, headers: dict = None) -> requests.Response:
    hdrs = headers or _get_headers(session)
    post_body = urllib.parse.urlencode(data)
    url = _make_url(path, session, post_body=post_body)
    return client.post(url, data=data, headers=hdrs, timeout=30)


def _extract_patient_id(response_text: str) -> str:
    """Extract patient ID from setPatient.jsp XML response.

    The response is typically a SOAP XML where the patient ID appears
    as the text content before the first closing XML tag.
    """
    text = response_text.strip()
    if not text:
        return ""

    # Try to extract from SOAP XML response
    try:
        cleaned = re.sub(
            r'<(/?)(?:SOAP-ENV|S|soapenv):',
            lambda m: f'<{m.group(1)}',
            text,
        )
        cleaned = re.sub(r'xmlns:[^=]+="[^"]*"', '', cleaned)
        root = ET.fromstring(cleaned)

        # Look for return element which typically contains the patient ID
        ret = root.find('.//return')
        if ret is not None:
            ret_text = (ret.text or "").strip()
            if ret_text and ret_text.isdigit():
                return ret_text
            # Check child elements
            pid_elem = ret.find('.//id') or ret.find('.//patientId') or ret.find('.//Id')
            if pid_elem is not None:
                pid_text = (pid_elem.text or "").strip()
                if pid_text.isdigit():
                    return pid_text

        # Try Body element
        body = root.find('.//Body')
        if body is not None:
            body_text = (body.text or "").strip()
            if body_text and body_text.isdigit():
                return body_text
    except ET.ParseError:
        pass

    # Fallback: JS code extracts via strpt.substring(0, strpt.indexOf('</'))
    # This gets everything before the first closing XML tag
    match = re.match(r'^[^<]*?(\d+)', text)
    if match:
        return match.group(1)

    # Try finding a number before the first </
    close_idx = text.find("</")
    if close_idx > 0:
        candidate = text[:close_idx].strip()
        if candidate.isdigit():
            return candidate

    return ""
