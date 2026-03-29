"""
eClinicalWorks Demographics Integration (Endgame)
Platform: caoshae8e528d1yp90app.ecwcloud.com

Actions: read, edit-demographics, read-combos, read-sliding-fee, calculate,
         search-provider, get-contacts, add-contact, update-contact,
         set-responsible-party, edit-income, read-sogi, save-sogi,
         read-lrte, lrte-lookup, save-lrte, read-parent-info, save-parent-info

Converted from action_handler.py for Lambda execution:
  - httpx → requests
  - run(auth_headers, input_data) entry point
  - session_did from auth_headers["X-Session-DID"] or fallback 297477
"""

import hashlib
import json
import re
import time
import urllib.parse
from datetime import datetime
from html import escape as html_escape
from xml.etree import ElementTree as ET

import requests

# Prefer runtime-injected BASE_URL from generic executor, fallback to hardcoded
BASE_URL = globals().get("BASE_URL") or "https://caoshae8e528d1yp90app.ecwcloud.com"
DEFAULT_SESSION_DID = "297477"


# ── Endgame Entry Point ─────────────────────────────────────────────────────

def run(auth_headers: dict, input_data: dict = None) -> dict:
    """Endgame integration entry point.

    input_data:
      action (str): One of the supported actions (see below).
      patient_id (str): Required for all actions.
      ... action-specific fields (see each action's docstring).

    Actions:
      read                  - Read full patient record
      edit-demographics     - Read-modify-write demographics (changes dict)
      read-combos           - Read dropdown/combo values
      read-sliding-fee      - Read current sliding fee assignment
      calculate             - Calculate sliding fee from income/dependants/unit
      search-provider       - Search providers by name
      get-contacts          - Read patient contacts
      add-contact           - Create a new contact
      update-contact        - Update an existing contact
      set-responsible-party - Set guarantor/responsible party
      edit-income           - Calculate + assign sliding fee schedule
      read-sogi             - Read SOGI data + dropdown lists
      save-sogi             - Save SOGI (orientation, gender identity, pronouns)
      read-lrte             - Read structured LRTE data for patient
      lrte-lookup           - Search LRTE values (race/language/ethnicity)
      save-lrte             - Save structured LRTE data
      read-parent-info      - Read parent info (mother/father/other)
      save-parent-info      - Save parent info
    """
    input_data = input_data or {}
    action = input_data.get("action", "read")
    patient_id = input_data.get("patient_id")

    if not patient_id:
        return {"status_code": 400, "body": {"error": "patient_id is required"}}

    session = _build_session_from_headers(auth_headers)

    with requests.Session() as client:
        client.cookies.update(session["cookies"])

        if action == "read":
            return get_patient_info(client, session, patient_id)

        elif action == "edit-demographics":
            changes = input_data.get("changes", {})
            if not changes:
                return {"status_code": 400,
                        "body": {"error": "changes dict is required"}}
            return edit_demographics(client, session, patient_id, changes)

        elif action == "read-combos":
            return get_demographics_combos(client, session, patient_id)

        elif action == "read-sliding-fee":
            return get_sliding_fee_schedule(client, session, patient_id)

        elif action == "calculate":
            return calculate_sliding_fee(
                client, session,
                input_data.get("Income", "0"),
                input_data.get("Dependants", "1"),
                input_data.get("Unit", "Monthly"),
            )

        elif action == "search-provider":
            search = input_data.get("search", "")
            lastname, firstname = "", ""
            if "," in search:
                parts = search.split(",", 1)
                lastname, firstname = parts[0].strip(), parts[1].strip()
            else:
                lastname = search.strip()
            return {"providers": search_providers(
                client, session, lastname, firstname)}

        elif action == "get-contacts":
            emergency_only = input_data.get("emergency_only", False)
            return {"contacts": get_contacts(
                client, session, patient_id, emergency_only)}

        elif action == "add-contact":
            contact = input_data.get("contact", {})
            if not contact:
                return {"status_code": 400,
                        "body": {"error": "contact dict is required"}}
            return add_contact(client, session, patient_id, contact)

        elif action == "update-contact":
            contact_id = input_data.get("contact_id")
            contact = input_data.get("contact", {})
            if not contact_id or not contact:
                return {"status_code": 400,
                        "body": {"error": "contact_id and contact are required"}}
            return update_contact(
                client, session, patient_id, contact_id, contact)

        elif action == "set-responsible-party":
            gr_id = input_data.get("gr_id", patient_id)
            gr_rel = input_data.get("gr_rel", "1")
            is_gr_pt = input_data.get("is_gr_pt", "1")
            return set_responsible_party(
                client, session, patient_id, gr_id, gr_rel, is_gr_pt)

        elif action == "edit-income":
            income_data = input_data.get("income_data", {})
            if not income_data:
                return {"status_code": 400,
                        "body": {"error": "income_data dict is required"}}
            return edit_income(client, session, patient_id, income_data)

        elif action == "read-sogi":
            return get_sogi_details(client, session, patient_id)

        elif action == "save-sogi":
            sogi_data = input_data.get("sogi_data", {})
            if not sogi_data:
                return {"status_code": 400,
                        "body": {"error": "sogi_data dict is required"}}
            return save_sogi(client, session, patient_id, sogi_data)

        elif action == "read-parent-info":
            return get_parent_info(client, session, patient_id)

        elif action == "save-parent-info":
            parent_data = input_data.get("parent_data", {})
            if not parent_data:
                return {"status_code": 400,
                        "body": {"error": "parent_data dict is required"}}
            return save_parent_info(
                client, session, patient_id, parent_data)

        elif action == "read-lrte":
            return get_patient_lrte(client, session, patient_id)

        elif action == "lrte-lookup":
            lrte_type = input_data.get("lrte_type", "race")
            search = input_data.get("search", "")
            return get_lrte_lookup(client, session, lrte_type, search)

        elif action == "save-lrte":
            lrte_type = input_data.get("lrte_type")
            entries = input_data.get("entries", [])
            decline = input_data.get("decline_to_specify", False)
            translator = input_data.get("translator")
            if not lrte_type:
                return {"status_code": 400,
                        "body": {"error": "lrte_type is required (race/language/ethnicity)"}}
            return save_lrte(client, session, patient_id, lrte_type,
                             entries, decline_to_specify=decline,
                             translator=translator)

        elif action == "read-structured-data":
            return get_structured_data(client, session, patient_id)

        elif action == "save-structured-data":
            fields = input_data.get("structured_data", {})
            if not fields:
                return {"status_code": 400,
                        "body": {"error": "structured_data dict is required"}}
            return save_structured_data(client, session, patient_id, fields)

        elif action == "upload-insurance-card":
            image_b64 = input_data.get("image_base64", "")
            if not image_b64:
                return {"status_code": 400,
                        "body": {"error": "image_base64 is required"}}
            import base64 as _b64
            image_bytes = _b64.b64decode(image_b64)
            fname = input_data.get("filename", "insurance_card.png")
            desc = input_data.get("description", "")
            return upload_insurance_card(
                client, session, patient_id, image_bytes, fname, desc)

        elif action == "upload-profile-picture":
            image_b64 = input_data.get("image_base64", "")
            if not image_b64:
                return {"status_code": 400,
                        "body": {"error": "image_base64 is required"}}
            import base64 as _b64
            image_bytes = _b64.b64decode(image_b64)
            return upload_profile_picture(client, session, patient_id, image_bytes)

        elif action == "save-communication-notes":
            notes = input_data.get("notes", "")
            return save_communication_notes(client, session, patient_id, notes)

        elif action == "save-communication-settings":
            return save_communication_settings(client, session, patient_id, input_data)

        elif action == "send-sms":
            message = input_data.get("message", "")
            if not message:
                return {"status_code": 400,
                        "body": {"error": "message is required"}}
            return send_sms(client, session, patient_id, message)

        elif action == "create-telephone-encounter":
            return create_telephone_encounter(client, session, patient_id, input_data)

        else:
            return {"status_code": 400,
                    "body": {"error": f"Unknown action: {action}",
                             "valid_actions": [
                                 "read", "edit-demographics", "read-combos",
                                 "read-sliding-fee", "calculate",
                                 "search-provider", "get-contacts",
                                 "add-contact", "update-contact",
                                 "set-responsible-party", "edit-income",
                                 "read-sogi", "save-sogi",
                                 "read-lrte", "lrte-lookup", "save-lrte",
                                 "read-parent-info", "save-parent-info",
                                 "read-structured-data", "save-structured-data",
                                 "upload-insurance-card", "upload-profile-picture",
                                 "save-communication-notes", "save-communication-settings",
                                 "send-sms",
                                 "create-telephone-encounter",
                             ]}}


# === PRIVATE ===

# ── XML Helpers ──────────────────────────────────────────────────────────────

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
    url = f"{BASE_URL}{path}"
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


def _add_element(name: str, value, xsi_type: str = "xsd:string",
                 cdata: bool = False) -> str:
    val = str(value) if value is not None else ""
    if cdata:
        inner = f"<![CDATA[{val}]]>"
    else:
        inner = _escape_xml(val)
    return f'<{name} xsi:type="{xsi_type}">{inner}</{name}>'


def _add_element_raw(name: str, value) -> str:
    val = str(value) if value is not None else ""
    return f'<{name}>{_escape_xml(val)}</{name}>'


def _parse_soap_xml(text: str) -> dict:
    text = text.strip()
    if not text:
        return {}
    try:
        cleaned = re.sub(
            r'<(/?)(?:SOAP-ENV|S|soapenv):',
            lambda m: f'<{m.group(1)}',
            text,
        )
        cleaned = re.sub(r'xmlns:[^=]+="[^"]*"', '', cleaned)
        root = ET.fromstring(cleaned)
        body = root.find('.//Body')
        if body is None:
            body = root.find('.//return')
        if body is None:
            return {}
        return _xml_to_dict(body)
    except ET.ParseError:
        return {"_raw": text}


def _soap_result(r, extra: dict = None) -> dict:
    """Standard return for SOAP write operations. Checks <status> in response."""
    parsed = _parse_soap_xml(r.text)
    ret = parsed.get("return", parsed)
    soap_status = ret.get("status", "") if isinstance(ret, dict) else ""
    result = {"status_code": 400 if soap_status == "failed" else r.status_code,
              "body": ret if isinstance(ret, dict) else r.text[:500]}
    if extra:
        result.update(extra)
    return result


def _xml_to_dict(elem) -> dict:
    result = {}
    for child in elem:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if len(child) > 0:
            result[tag] = _xml_to_dict(child)
        else:
            result[tag] = (child.text or "").strip()
    if not result and elem.text:
        return elem.text.strip()
    return result


# ── Session ──────────────────────────────────────────────────────────────────

def _build_session_from_headers(auth_headers: dict) -> dict:
    """Build session dict from Endgame auth_headers."""
    cookie_str = auth_headers.get("Cookie", "")
    csrf_token = auth_headers.get("X-CSRF-TOKEN", "")
    session_did = auth_headers.get("X-Session-DID", DEFAULT_SESSION_DID)

    cookies = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()

    cip = auth_headers.get("cip", "null")

    return {
        "cookies": cookies,
        "csrf_token": csrf_token,
        "session_did": session_did,
        "tr_user_id": session_did,
        "ecwappprocessid": "0",
        "timezone": "Atlantic/Reykjavik",
        "cip": cip,
    }


def _get_headers(session: dict) -> dict:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/145.0.0.0 Safari/537.36",
        "X-CSRF-TOKEN": session["csrf_token"],
        "X-Requested-With": "XMLHttpRequest",
        "isAjaxRequest": "true",
        "cip": session.get("cip", "null"),
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/mobiledoc/jsp/webemr/index.jsp",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }


def _post(client: requests.Session, session: dict, path: str,
          data: dict, headers: dict = None) -> requests.Response:
    hdrs = headers or _get_headers(session)
    post_body = urllib.parse.urlencode(data)
    url = _make_url(path, session, post_body=post_body)
    return client.post(url, data=data, headers=hdrs)


# ── READ Operations ──────────────────────────────────────────────────────────

def get_patient_info(client: requests.Session, session: dict,
                     patient_id: str) -> dict:
    url = _make_url(
        f"/mobiledoc/jsp/catalog/xml/getPatientInfo.jsp"
        f"?patientId={patient_id}&logView=true&AddlInfo=EthInfo",
        session,
    )
    r = client.get(url, headers=_get_headers(session))
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    if isinstance(parsed, dict):
        for key in ("return", "patient"):
            if key in parsed:
                parsed = parsed[key]

    # Enrich with phone list data (cell, home, work with database IDs)
    if isinstance(parsed, dict) and parsed:
        try:
            phones = fetch_phone_numbers(client, session, patient_id)
            phone_list = {}
            for ptype, obj in phones.items():
                if isinstance(obj, dict) and obj.get("phoneNumber"):
                    phone_list[ptype] = {
                        "id": obj.get("id"),
                        "phoneNumber": obj.get("phoneNumber", ""),
                        "ext": obj.get("ext"),
                        "voiceEnabled": obj.get("voiceEnabled", False),
                        "textEnabled": obj.get("textEnabled", False),
                        "leaveMessage": obj.get("leaveMessage"),
                        "description": obj.get("description", ""),
                    }
            parsed["phoneList"] = phone_list
        except Exception:
            pass

    return parsed


def get_demographics_combos(client: requests.Session, session: dict,
                            patient_id: str) -> dict:
    data = {"ptid": patient_id, "sessionDID": session["session_did"],
            "TrUserId": session["tr_user_id"]}
    r = _post(client, session,
              "/mobiledoc/jsp/webemr/toppanel/patientInfo/fetchdemographicsdata.jsp",
              data)
    r.raise_for_status()
    return r.json()


def fetch_phone_numbers(client: requests.Session, session: dict,
                        patient_id: str) -> dict:
    """Fetch existing phone number records with their database IDs.

    Returns dict with CELL_PHONE, HOME_PHONE, WORK_PHONE objects.
    Each object has 'id' field which is the database primary key.
    """
    data = {"patientId": patient_id}
    r = _post(client, session,
              "/mobiledoc/emr/patient/phonenumber/fetch",
              data)
    r.raise_for_status()
    result = r.json()
    return result.get("phoneNumberData", {})


def get_sliding_fee_schedule(client: requests.Session, session: dict,
                             patient_id: str) -> dict:
    r = _post(client, session,
              f"/mobiledoc/jsp/catalog/xml/edi/getSlidingFeeScheduleForPatient.jsp"
              f"?PatientId={patient_id}",
              {"FormData": ""})
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    if isinstance(parsed, dict) and "return" in parsed:
        return parsed["return"]
    return parsed


def get_contacts(client: requests.Session, session: dict,
                 patient_id: str, emergency_only: bool = False) -> list:
    path = f"/mobiledoc/jsp/catalog/xml/getContacts.jsp?patientId={patient_id}"
    if emergency_only:
        path += "&emergencyContactFlag=1"
    url = _make_url(path, session)
    r = client.post(url, headers=_get_headers(session))
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    ret = parsed.get("return", parsed)
    if isinstance(ret, dict):
        contact = ret.get("contact", None)
        if contact is None:
            return []
        if isinstance(contact, dict):
            return [contact]
        if isinstance(contact, list):
            return contact
    return []


def search_providers(client: requests.Session, session: dict,
                     lastname: str = "", firstname: str = "",
                     provider_type: str = "0",
                     max_count: int = 15) -> list:
    hdrs = _get_headers(session)
    url = _make_url(
        "/mobiledoc/jsp/catalog/xml/edi/getProviderList.jsp", session)
    data = {
        "ProviderType": provider_type,
        "speciality": "",
        "lastname": lastname,
        "firstname": firstname,
        "myFav": "0",
        "startPos": "0",
        "MAXCOUNT": str(max_count),
        "providerStatus": "true",
        "uid": "",
    }
    r = client.post(url, headers=hdrs, data=data)
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    ret = parsed.get("return", parsed)
    if isinstance(ret, dict):
        providers = ret.get("Providers", {})
        if isinstance(providers, dict):
            prov_list = providers.get("Provider", [])
            if isinstance(prov_list, dict):
                return [prov_list]
            if isinstance(prov_list, list):
                return prov_list
    return []


def get_patient_lrte(client: requests.Session, session: dict,
                     patient_id: str) -> dict:
    r = _post(client, session,
              "/mobiledoc/emr/patient/demographics/lrte/get-patient-lrte",
              {"patientId": patient_id})
    r.raise_for_status()
    return r.json()


def get_lrte_lookup(client: requests.Session, session: dict,
                    lrte_type: str, search: str = "") -> list:
    """Lookup LRTE values. lrte_type: 'race', 'language', or 'ethnicity'."""
    type_to_path = {
        "language": "/mobiledoc/emr/patient/demographics/lrte/get-language-list",
        "race": "/mobiledoc/emr/patient/demographics/lrte/get-race-list",
        "ethnicity": "/mobiledoc/emr/patient/demographics/lrte/get-ethnicity-list",
    }
    path = type_to_path.get(lrte_type)
    if not path:
        return []
    hdrs = _get_headers(session)
    hdrs["Content-Type"] = "application/json"
    params = {
        "counter": 1, "name": search, "code": "", "mappedValue": "",
        "source": "All", "pin": "All", "sortOrder": "ASC",
    }
    post_body = json.dumps(params)
    url = _make_url(path, session, post_body=post_body)
    r = client.post(url, headers=hdrs, data=post_body)
    r.raise_for_status()
    data = r.json()
    result = data.get("result", {})
    list_key = {
        "language": "LanguageList",
        "race": "RaceList",
        "ethnicity": "EthnicityList",
    }.get(lrte_type, "")
    return result.get(list_key, [])


def get_sogi_details(client: requests.Session, session: dict,
                     patient_id: str) -> dict:
    url = _make_url(
        f"/mobiledoc/jsp/catalog/xml/getSOGIdetails.jsp"
        f"?trigger=getSOGI&patientId={patient_id}",
        session)
    r = client.post(url, headers=_get_headers(session))
    r.raise_for_status()
    return r.json()


def calculate_sliding_fee(client: requests.Session, session: dict,
                          income: str, dependants: str,
                          unit: str) -> dict:
    r = _post(client, session,
              f"/mobiledoc/jsp/catalog/xml/edi/calculateSlidingFeeSchedule.jsp"
              f"?Income={income}&Dependant={dependants}&Unit={unit}",
              {"FormData": ""})
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    if isinstance(parsed, dict) and "return" in parsed:
        return parsed["return"]
    return parsed


# ── WRITE: LRTE (Language, Race, Tribe, Ethnicity) ─────────────────────────

def save_lrte(client: requests.Session, session: dict,
              patient_id: str, lrte_type: str, entries: list,
              decline_to_specify: bool = False,
              translator: bool = None) -> dict:
    """Save structured LRTE data.

    lrte_type: 'race', 'language', or 'ethnicity'
    entries: list of dicts from get_lrte_lookup (id, name, code, etc.)
    decline_to_specify: True to mark "declined to specify"
    translator: bool, only for language — sets translator flag
    """
    hdrs = _get_headers(session)
    hdrs["Content-Type"] = "application/json"
    payload = {
        "patientId": int(patient_id),
        "declineToSpecify": 1 if decline_to_specify else 0,
    }
    if not decline_to_specify:
        payload["selectedValueList"] = entries
    if lrte_type == "language" and translator is not None:
        payload["translator"] = 1 if translator else 0
    post_body = json.dumps(payload)
    url = _make_url(
        f"/mobiledoc/emr/patient/demographics/lrte/{lrte_type}/save",
        session, post_body=post_body)
    r = client.post(url, headers=hdrs, data=post_body)
    r.raise_for_status()
    return {"status_code": r.status_code, "body": r.text[:500]}


# ── WRITE: SOGI ────────────────────────────────────────────────────────────

def save_sogi(client: requests.Session, session: dict,
              patient_id: str, sogi_data: dict) -> dict:
    """Save SOGI data (sexual orientation, gender identity, pronouns, birth sex).

    All parameters go in URL query string; POST body is empty.
    Source: SOGICtrl.js saveSOGIDetails().

    sogi_data fields:
      birthsex: str ("M", "F", or "")
      transgender: str ("Y" or "N")
      so_id: str/int (sexual orientation id from so_list)
      gi_ids: list[int] or str (gender identity ids, comma-separated)
      pp_ids: list[int] or str (pronoun ids, comma-separated)
      so_reason: str (reason text for sexual orientation)
      gi_reason: str (reason text for gender identity)
      pp_reason: str (reason text for pronouns)
      so_date: str (MM/YYYY format)
      gi_date: str (MM/YYYY format)
      so_changed: bool (whether SO was modified)
      gi_changed: bool (whether GI was modified)
      pp_changed: bool (whether PP was modified)
      birthsex_changed: bool (whether birth sex was modified)
      transgender_changed: bool (whether transgender was modified)
    """
    def _bool(v):
        return "true" if v else "false"

    def _ids(v):
        if isinstance(v, list):
            return ",".join(str(x) for x in v)
        return str(v) if v else ""

    so_id = sogi_data.get("so_id", "")
    gi_ids = _ids(sogi_data.get("gi_ids", ""))
    pp_ids = _ids(sogi_data.get("pp_ids", ""))
    transgender = sogi_data.get("transgender", "N")
    birthsex = sogi_data.get("birthsex", "")

    so_reason = urllib.parse.quote(str(sogi_data.get("so_reason", "")))
    gi_reason = urllib.parse.quote(str(sogi_data.get("gi_reason", "")))
    pp_reason = urllib.parse.quote(str(sogi_data.get("pp_reason", "")))

    so_date = sogi_data.get("so_date", "")
    gi_date = sogi_data.get("gi_date", "")

    so_changed = _bool(sogi_data.get("so_changed", True))
    gi_changed = _bool(sogi_data.get("gi_changed", True))
    pp_changed = _bool(sogi_data.get("pp_changed", True))
    birthsex_changed = _bool(sogi_data.get("birthsex_changed",
                              "birthsex" in sogi_data))
    transgender_changed = _bool(sogi_data.get("transgender_changed",
                                 "transgender" in sogi_data))

    path = (
        f"/mobiledoc/jsp/catalog/xml/getSOGIdetails.jsp"
        f"?trigger=saveSOGI"
        f"&patientId={patient_id}"
        f"&trUserId={session['tr_user_id']}"
        f"&transgender={transgender}"
        f"&so_id={so_id}"
        f"&gi_ids={gi_ids}"
        f"&pp_ids={pp_ids}"
        f"&so_reason={so_reason}"
        f"&gi_reason={gi_reason}"
        f"&pp_reason={pp_reason}"
        f"&so_date={so_date}"
        f"&gi_date={gi_date}"
        f"&so_changed={so_changed}"
        f"&gi_changed={gi_changed}"
        f"&pp_changed={pp_changed}"
        f"&birthsex={birthsex}"
        f"&transgender_changed={transgender_changed}"
        f"&birthsex_changed={birthsex_changed}"
        f"&modality=WEB"
    )
    url = _make_url(path, session, post_body="")
    r = client.post(url, headers=_get_headers(session))
    r.raise_for_status()
    return {"status_code": r.status_code, "body": r.text[:500]}


# ── Parent Info ─────────────────────────────────────────────────────────────

def get_parent_info(client: requests.Session, session: dict,
                    patient_id: str) -> dict:
    """Read parent info (mother/father/other name, phone, email)."""
    r = _post(client, session,
              "/mobiledoc/jsp/webemr/toppanel/patientInfo/getSetParentInfo.jsp",
              {"accessParam": "load", "patientId": patient_id})
    r.raise_for_status()
    text = r.text.strip()
    if text:
        return json.loads(text)
    return {}


def save_parent_info(client: requests.Session, session: dict,
                     patient_id: str, parent_data: dict) -> dict:
    """Save parent info.

    parent_data fields (all optional, empty string to clear):
      Mom1, Mom1Ph, Mom1Email, Mom2, Mom2Ph, Mom2Email,
      Dad1, Dad1Ph, Dad1Email, Dad2, Dad2Ph, Dad2Email,
      Other, OtherPh, OtherEmail
    """
    # Read current to preserve unset fields
    current = get_parent_info(client, session, patient_id)
    all_fields = [
        "Mom1", "Mom1Ph", "Mom1Email", "Mom2", "Mom2Ph", "Mom2Email",
        "Dad1", "Dad1Ph", "Dad1Email", "Dad2", "Dad2Ph", "Dad2Email",
        "Other", "OtherPh", "OtherEmail",
    ]
    payload = {}
    for f in all_fields:
        if f in parent_data:
            payload[f] = parent_data[f]
        else:
            payload[f] = current.get(f, "")

    form_data = json.dumps(payload)
    r = _post(client, session,
              "/mobiledoc/jsp/webemr/toppanel/patientInfo/getSetParentInfo.jsp",
              {"accessParam": "save", "patientId": patient_id,
               "FormData": form_data})
    r.raise_for_status()
    return {"status_code": r.status_code, "body": r.text[:500]}


# ── WRITE: Demographics Tab 1 ───────────────────────────────────────────────

def save_demographics_tab1(client: requests.Session, session: dict,
                           patient_id: str, fields: dict) -> dict:
    elements = []
    elements.append(_add_element("prefix", fields.get("prefix", "")))
    elements.append(_add_element("suffix", fields.get("suffix", "")))
    elements.append(_add_element("fname", fields.get("fname", ""), cdata=True))
    elements.append(_add_element("lname", fields.get("lname", ""), cdata=True))
    elements.append(_add_element("mname", fields.get("mname", "")))
    elements.append(_add_element("address1", fields.get("address1", "")))
    elements.append(_add_element("address2", fields.get("address2", "")))
    elements.append(_add_element("city", fields.get("city", "")))
    elements.append(_add_element("state", fields.get("state", "")))
    elements.append(_add_element("zip", fields.get("zip", "")))
    elements.append(_add_element("Country", fields.get("Country", "")))
    elements.append(_add_element("CountyCode", fields.get("CountyCode", "")))
    elements.append(_add_element("CountyName", fields.get("CountyName", "")))
    elements.append(_add_element("MailCountyCode",
                                 fields.get("MailCountyCode", "")))
    elements.append(_add_element("MailCountyName",
                                 fields.get("MailCountyName", "")))
    elements.append(_add_element("phone", fields.get("phone", "")))
    elements.append(_add_element("mobile", fields.get("mobile", "")))
    elements.append(_add_element("PreviousName",
                                 fields.get("PreviousName", "")))
    elements.append(_add_element("email", fields.get("email", "")))
    elements.append(_add_element("emailReason",
                                 fields.get("emailReason", "")))
    elements.append(_add_element("dob", fields.get("dob", "")))
    elements.append(_add_element("tob", fields.get("tob", "00:00:00")))
    elements.append(_add_element("ssn", fields.get("ssn", "")))
    elements.append(_add_element("sex", fields.get("sex", "")))
    elements.append(_add_element("TransGender",
                                 fields.get("TransGender", "N")))
    elements.append(_add_element("status", fields.get("status", "0")))
    elements.append(_add_element("updateFace", "false"))
    elements.append(_add_element("statusscreen", ""))
    elements.append(_add_element("mflag", fields.get("mflag", "")))
    elements.append(_add_element("primaryServiceLocation",
                                 fields.get("primaryServiceLocation", "1")))
    elements.append(_add_element("gestationalAge",
                                 fields.get("gestationalAge", "")))
    elements.append(_add_element("PreferredName",
                                 fields.get("PreferredName", "")))
    elements.append(_add_element("demoChangedFields1",
                                 fields.get("demoChangedFields1", "")))
    phone_arr = fields.get("phoneNumbersArr", "[]")
    elements.append(_add_element("phoneNumbersArr", phone_arr))

    patient_xml = f'<patient>{"".join(elements)}</patient>'
    full_xml = _soap_envelope(patient_xml)

    r = _post(client, session,
              f"/mobiledoc/jsp/catalog/xml/setPatient.jsp?patientId={patient_id}",
              {"FormData": full_xml})
    r.raise_for_status()
    return _soap_result(r)


# ── WRITE: Demographics Tab 2 ───────────────────────────────────────────────

def save_demographics_tab2(client: requests.Session, session: dict,
                           patient_id: str, fields: dict) -> dict:
    elements = []
    elements.append(_add_element("empId", fields.get("empId", "0")))
    elements.append(_add_element("empName", fields.get("empName", "")))
    elements.append(_add_element("empAddress", fields.get("empAddress", "")))
    elements.append(_add_element("empAddress2", fields.get("empAddress2", "")))
    elements.append(_add_element("empCity", fields.get("empCity", "")))
    elements.append(_add_element("empState", fields.get("empState", "")))
    elements.append(_add_element("empZip", fields.get("empZip", "")))
    elements.append(_add_element("empPhone", fields.get("empPhone", "")))
    elements.append(_add_element("StAddress", fields.get("StAddress", "")))
    elements.append(_add_element("StAddress2", fields.get("StAddress2", "")))
    elements.append(_add_element("city", fields.get("stCity", "")))
    elements.append(_add_element("state", fields.get("stState", "")))
    elements.append(_add_element("zip", fields.get("stZip", "")))
    elements.append(_add_element("notes", fields.get("notes", "")))
    elements.append(_add_element("maritalstatus",
                                 fields.get("maritalstatus", "")))
    elements.append(_add_element("doctorId", fields.get("doctorId", "0")))
    elements.append(_add_element("refPrId", fields.get("refPrId", "0")))
    elements.append(_add_element("rendPrId", fields.get("rendPrId", "0")))
    elements.append(_add_element("refHygienistId",
                                 fields.get("refHygienistId", "0")))
    elements.append(_add_element("primaryDentistId",
                                 fields.get("primaryDentistId", "0")))
    elements.append(_add_element("pmcId", fields.get("pmcId", "")))
    elements.append(_add_element("Translator", fields.get("Translator", "0")))
    elements.append(_add_element("MailOrderPharmacyId",
                                 fields.get("MailOrderPharmacyId", "0")))
    elements.append(_add_element("MOMemberId", fields.get("MOMemberId", "")))
    elements.append(_add_element("msgflag", fields.get("msgflag", "")))
    elements.append(_add_element("msgCellflag",
                                 fields.get("msgCellflag", "")))
    elements.append(_add_element("deceased", fields.get("deceased", "")))
    elements.append(_add_element("hl7Id", fields.get("hl7Id", "")))
    elements.append(_add_element("DefaultLab", fields.get("DefaultLab", "")))
    elements.append(_add_element("DefaultDI", fields.get("DefaultDI", "")))
    elements.append(_add_element("nostatements",
                                 fields.get("nostatements", "0")))
    elements.append(_add_element("isNative", fields.get("isNative", "0")))
    elements.append(_add_element("date", fields.get("deceasedDate", "")))
    elements.append(_add_element("deceasedNotes",
                                 fields.get("deceasedNotes", "")))
    elements.append(_add_element("characterestic",
                                 fields.get("characterestic", "")))
    elements.append(_add_element("language", fields.get("language", "")))
    elements.append(_add_element("HomeMsgType",
                                 fields.get("HomeMsgType", "")))
    elements.append(_add_element("CellMsgType",
                                 fields.get("CellMsgType", "")))
    elements.append(_add_element("WorkMsgType",
                                 fields.get("WorkMsgType", "")))
    elements.append(_add_element("ControlNo", fields.get("ControlNo", "")))
    elements.append(_add_element("ResType", fields.get("ResType", "")))
    elements.append(_add_element("OptOutOfPtStmt",
                                 fields.get("OptOutOfPtStmt", "")))
    elements.append(_add_element("EmpStatus", fields.get("EmpStatus", "")))
    elements.append(_add_element("StudentStatus",
                                 fields.get("StudentStatus", "")))
    elements.append(_add_element("picFileName",
                                 fields.get("picFileName", "")))
    elements.append(_add_element("RelInfo", fields.get("RelInfo", "")))
    elements.append(_add_element("RxConsent", fields.get("RxConsent", "")))
    elements.append(_add_element("RelInfoDate",
                                 fields.get("RelInfoDate", "")))
    elements.append(_add_element("SelfPay", fields.get("SelfPay", "0")))
    elements.append(_add_element("FeeSchId", fields.get("FeeSchId", "")))
    elements.append(_add_element("PrevFeeSchId",
                                 fields.get("PrevFeeSchId", "")))
    elements.append(_add_element("race", fields.get("race", "")))
    elements.append(_add_element("Consent", fields.get("Consent", "")))
    elements.append(_add_element("FinanceChargeFlag",
                                 fields.get("FinanceChargeFlag", "0")))
    elements.append(_add_element("excludecollection",
                                 fields.get("excludecollection", "0")))
    elements.append(_add_element("BirthOrder",
                                 fields.get("BirthOrder", "")))
    elements.append(_add_element("Ethnicity", fields.get("Ethnicity", "")))
    elements.append(_add_element("VFC", fields.get("VFC", "")))
    elements.append(_add_element("teamMember",
                                 fields.get("teamMember", "0")))
    elements.append(_add_element("emailReason",
                                 fields.get("emailReason", "")))
    elements.append(_add_element("ssnReason", fields.get("ssnReason", "0"),
                                 xsi_type="xsd:int"))
    elements.append(_add_element("ssnReasonNotes",
                                 fields.get("ssnReasonNotes", "")))
    elements.append(_add_element("UseStreetAddressForRxFlag",
                                 fields.get("UseStreetAddressForRxFlag", "")))
    elements.append(_add_element("PreferredName",
                                 fields.get("PreferredName", "")))
    if fields.get("demoChangedFields2"):
        elements.append(_add_element("demoChangedFields2",
                                     fields["demoChangedFields2"]))
    elements.append(_add_element("stCountry", fields.get("stCountry", "")))
    if not fields.get("stCountry"):
        elements.append(_add_element("stDefaultCountry",
                                     fields.get("stDefaultCountry", "US")))
    elements.append(_add_element("SkipLRE", "yes"))
    elements.append(_add_element("updateFace", "false"))

    patient_xml = f'<patient>{"".join(elements)}</patient>'
    full_xml = _soap_envelope(patient_xml)

    r = _post(client, session,
              f"/mobiledoc/jsp/catalog/xml/setPatient1.jsp"
              f"?context=demographics&patientId={patient_id}&Id={patient_id}",
              {"FormData": full_xml})
    r.raise_for_status()
    return _soap_result(r)


# ── WRITE: Sliding Fee Schedule (Income) ─────────────────────────────────────

def save_sliding_fee_schedule(client: requests.Session, session: dict,
                              patient_id: str, fields: dict,
                              expire: bool = False) -> dict:
    expired_status = "1" if expire else "0"

    income_info = fields.get("IncomeInfo", {})
    income_elements = []
    income_elements.append(_add_element("IncomeDetailId",
                                        income_info.get("Id", "")))
    income_elements.append(_add_element("GrHrRate",
                                        income_info.get("GrHrRate", "")))
    income_elements.append(_add_element("GrHrPerWeek",
                                        income_info.get("GrHrPerWeek", "")))
    income_elements.append(_add_element("GrGrossAmt",
                                        income_info.get("GrGrossAmt", "")))
    income_elements.append(_add_element("GrBiIncome",
                                        income_info.get("GrBiIncome", "")))
    income_elements.append(_add_element("GrBiGrossAmt",
                                        income_info.get("GrBiGrossAmt", "")))
    income_elements.append(_add_element("SpHrRate",
                                        income_info.get("SpHrRate", "")))
    income_elements.append(_add_element("SpHrPerWeek",
                                        income_info.get("SpHrPerWeek", "")))
    income_elements.append(_add_element("SpGrossAmt",
                                        income_info.get("SpGrossAmt", "")))
    income_elements.append(_add_element("SpBiIncome",
                                        income_info.get("SpBiIncome", "")))
    income_elements.append(_add_element("SpBiGrossAmt",
                                        income_info.get("SpBiGrossAmt", "")))
    income_elements.append(
        f'<UserId xsi:type="xsd:int">{session["tr_user_id"]}</UserId>')
    income_elements.append(_add_element("UserName",
                                        fields.get("UserName", "")))
    income_elements.append(_add_element("OtherIncomeTypes",
                                        income_info.get("OtherIncomeTypes", "")))
    other_amts = income_info.get("OtherIncomeAmt", "0,0,0,0")
    income_elements.append(_add_element("OtherIncome", other_amts))
    income_elements.append(_add_element("OtherIncomeGrossAmt",
                                        income_info.get("OtherIncomeGrossAmt", "")))
    income_elements.append(_add_element("ProofOfIncome",
                                        income_info.get("ProofOfIncome", "")))
    income_elements.append(_add_element("OtherIncomeReason",
                                        _escape_xml(income_info.get("OtherIncomeReason", ""))))
    income_elements.append(_add_element("MemberNotes",
                                        income_info.get("MemberNotes", "")))

    income_xml = (f'<IncomeInfo xsi:type="xsd:string">'
                  f'{"".join(income_elements)}</IncomeInfo>')

    members = fields.get("MemberInfo", [])
    member_details = ""
    for m in members:
        member_details += (f'<MemberDetailInfo>'
                           f'<MemberId>{m.get("MemberId", "")}</MemberId>'
                           f'</MemberDetailInfo>')
    member_xml = f'<MemberInfo xsi:type="xsd:string">{member_details}</MemberInfo>'

    def _date_to_yyyymmdd(date_str: str) -> str:
        if not date_str:
            return ""
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            return date_str
        try:
            dt = datetime.strptime(date_str, "%m/%d/%Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return date_str

    info_elements = []
    info_elements.append(_add_element("ItemId",
                                      fields.get("ItemId", "-1")))
    info_elements.append(_add_element("PatientId", patient_id))
    info_elements.append(_add_element("Income",
                                      fields.get("Income", "0")))
    info_elements.append(_add_element("Unit",
                                      fields.get("Unit", "Monthly")))
    info_elements.append(_add_element("Dependant",
                                      fields.get("Dependants", "1")))
    info_elements.append(_add_element("PovertyLevel",
                                      fields.get("PovertyLevel", "")))
    info_elements.append(
        f'<AssignedStatus xsi:type="xsd:int">1</AssignedStatus>')
    info_elements.append(_add_element("AssignedDate",
                                      _date_to_yyyymmdd(fields.get("AssignedDate", ""))))
    info_elements.append(_add_element("ExpiryDate",
                                      _date_to_yyyymmdd(fields.get("ExpiryDate", ""))))
    info_elements.append(_add_element("AssignedType",
                                      fields.get("AssignedType", "")))
    info_elements.append(_add_element("FeeSchId",
                                      fields.get("FeeSchId", "")))
    info_elements.append(_add_element("FeeSchedule",
                                      fields.get("FeeSchedule", "")))
    info_elements.append(_add_element("DocProof",
                                      fields.get("DocProof", "0")))
    info_elements.append(_add_element("NonProofOfIncome",
                                      fields.get("NonProofOfIncome", "0")))
    info_elements.append(_add_element("MedicalDiscount",
                                      fields.get("MedicalDiscount", "")))
    info_elements.append(_add_element("DentalDiscount",
                                          fields.get("DentalDiscount", "")))
    info_elements.append(_add_element("CopayDiscount",
                                      fields.get("CopayDiscount", "")))
    info_elements.append(
        f'<CopayDiscountType xsi:type="xsd:int">'
        f'{fields.get("CopayDiscountType", "1")}</CopayDiscountType>')
    info_elements.append(_add_element("Expired", expired_status))
    no_proof_reason = fields.get("NoProofReason", "")
    if fields.get("NonProofOfIncome") == "1" and no_proof_reason:
        info_elements.append(_add_element("NoProofReason", no_proof_reason))
    else:
        info_elements.append(_add_element("NoProofReason", ""))

    info_xml = f'<Info xsi:type="xsd:string">{"".join(info_elements)}</Info>'

    body_xml = f'{income_xml}{member_xml}{info_xml}'
    full_xml = _soap_envelope(body_xml)

    r = _post(client, session,
              "/mobiledoc/jsp/catalog/xml/edi/setSlidingFeeScheduleForPatient.jsp",
              {"FormData": full_xml})
    r.raise_for_status()
    return _soap_result(r)


# ── WRITE: Contacts ──────────────────────────────────────────────────────────

def _build_contact_xml(patient_id: str, contact: dict) -> tuple:
    e = []
    fname = _escape_xml(contact.get("Fname", ""))
    lname = _escape_xml(contact.get("Lname", ""))

    e.append(_add_element("pid", patient_id))
    e.append(_add_element("Fname", fname))
    e.append(_add_element("Lname", lname))
    mi = contact.get("MI", "")
    e.append(_add_element("MI", _escape_xml(mi) if mi else ""))
    addr = contact.get("address", "")
    if addr:
        e.append(f'<address xsi:type="xsd:string"><![CDATA[{addr}]]></address>')
    else:
        e.append(_add_element("address", ""))
    addr2 = contact.get("address2", "")
    if addr2:
        e.append(f'<address2 xsi:type="xsd:string"><![CDATA[{addr2}]]></address2>')
    else:
        e.append(_add_element("address2", ""))
    e.append(_add_element("city", _escape_xml(contact.get("city", ""))))
    e.append(_add_element("state", contact.get("state", "")))
    e.append(_add_element("zip", contact.get("zip", "")))
    e.append(_add_element("Country", ""))
    e.append(_add_element("homePhone", contact.get("homePhone", "")))
    e.append(_add_element("Email", contact.get("Email", "")))
    e.append(_add_element("dob", contact.get("dob", "")))
    e.append(_add_element("sex", contact.get("sex", "")))
    work_phone = contact.get("workPhone", "")
    work_ext = contact.get("workPhoneExt", "")
    if work_ext and work_phone:
        work_phone = f"{work_phone}-{work_ext}"
    e.append(_add_element("workPhone", work_phone))
    e.append(_add_element("Guardian", contact.get("Guardian", "0")))
    e.append(_add_element("IsHippa", contact.get("IsHippa", "0")))
    e.append(_add_element("isEmergencyContact",
                          contact.get("isEmergencyContact", "0")))
    name = contact.get("name", "")
    if not name:
        name = f"{lname},{fname}" if lname else fname
    e.append(_add_element("name", name))
    e.append(_add_element("relation", contact.get("relation", "")))
    e.append(_add_element("MaidenName", contact.get("MaidenName", "")))
    e.append(_add_element("CellPhone", contact.get("CellPhone", "")))
    e.append(_add_element("CountryCode", contact.get("CountryCode", "")))
    e.append(_add_element("isFamilyMember",
                          contact.get("isFamilyMember", "0")))
    for flag in ("homePhoneVoiceFlag", "homePhoneTextFlag",
                 "cellPhoneVoiceFlag", "cellPhoneTextFlag",
                 "workPhoneVoiceFlag", "workPhoneTextFlag"):
        e.append(_add_element(flag, contact.get(flag, "0")))
    e.append(_add_element("familyMemberRelation",
                          contact.get("familyMemberRelation", "")))
    e.append(_add_element("isRelPtFamilyMember",
                          contact.get("isRelPtFamilyMember", "0")))
    e.append(_add_element("RelatedPtId",
                          contact.get("RelatedPtId", "0")))
    e.append(_add_element("preferredPhone",
                          contact.get("preferredPhone", "")))
    e.append(_add_element("RelatedPtId",
                          contact.get("RelatedPtId", "0")))
    e.append(_add_element("IsResponsibleParty",
                          contact.get("IsResponsibleParty", "0")))

    contact_xml = f'<contact>{"".join(e)}</contact>'
    full_xml = _soap_envelope(contact_xml)
    return full_xml, name


def add_contact(client: requests.Session, session: dict,
                patient_id: str, contact: dict) -> dict:
    full_xml, name = _build_contact_xml(patient_id, contact)
    contact_name = name if contact.get("isEmergencyContact") == "1" else ""
    data = {
        "FormData": full_xml,
        "PatientId": patient_id,
        "ContactName": contact_name,
    }
    r = _post(client, session,
              "/mobiledoc/jsp/catalog/xml/newContact.jsp", data)
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    ret = parsed.get("return", parsed)
    contact_id = ret.get("contactId", "") if isinstance(ret, dict) else ""
    return _soap_result(r, {"contactId": contact_id})


def update_contact(client: requests.Session, session: dict,
                   patient_id: str, contact_id: str,
                   contact: dict) -> dict:
    full_xml, name = _build_contact_xml(patient_id, contact)
    contact_name = name if contact.get("isEmergencyContact") == "1" else ""
    r = _post(client, session,
              f"/mobiledoc/jsp/catalog/xml/updateContact.jsp"
              f"?contactId={contact_id}&PatientId={patient_id}"
              f"&ContactName={urllib.parse.quote(contact_name)}",
              {"FormData": full_xml})
    r.raise_for_status()
    return _soap_result(r)


# ── WRITE: Responsible Party ─────────────────────────────────────────────────

def set_responsible_party(client: requests.Session, session: dict,
                          patient_id: str, gr_id: str,
                          gr_rel: str = "1",
                          is_gr_pt: str = "1") -> dict:
    if gr_id == patient_id:
        gr_rel = "1"
        is_gr_pt = "1"

    current = get_patient_info(client, session, patient_id)
    prim_ins = ""
    record_number = ""
    if isinstance(current, dict):
        prim_ins = current.get("PrimIns", "")
        record_number = current.get("RecordNumber", "")

    elements = []
    elements.append(_add_element("PrimIns", prim_ins))
    elements.append(
        f'<ResponsibleParty>'
        f'{_add_element("GrId", gr_id)}'
        f'{_add_element("GrRel", gr_rel)}'
        f'{_add_element("IsGrPt", is_gr_pt)}'
        f'{_add_element("RecordNumber", record_number)}'
        f'</ResponsibleParty>'
    )
    elements.append('<insurances/>')
    full_xml = _soap_envelope("".join(elements))
    data = {"FormData": full_xml}
    r = _post(client, session,
              f"/mobiledoc/jsp/catalog/xml/setInsDetail.jsp"
              f"?patientId={patient_id}",
              data)
    r.raise_for_status()
    return _soap_result(r)


# ── Convenience: Read-Modify-Write ───────────────────────────────────────────

def edit_demographics(client: requests.Session, session: dict,
                      patient_id: str, changes: dict) -> dict:
    if "maritalStatus" in changes and "maritalstatus" not in changes:
        changes["maritalstatus"] = changes.pop("maritalStatus")

    # Extract sub-action data before processing tab fields
    sogi_data = changes.pop("sogi_data", None)
    parent_data = changes.pop("parent_data", None)
    income_data = changes.pop("income_data", None)
    contact_data = changes.pop("contact", None)
    update_contact_data = changes.pop("update_contact", None)

    rp_keys = {"GrId", "GrRel", "IsGrPt"}
    rp_changes = {k: changes.pop(k) for k in rp_keys if k in changes}

    current = get_patient_info(client, session, patient_id)
    if isinstance(current, dict) and "patient" in current:
        current = current["patient"]

    tab1_fields = {
        "prefix", "suffix", "fname", "lname", "mname",
        "address1", "address2", "city", "state", "zip",
        "Country", "CountyCode", "CountyName", "MailCountyCode", "MailCountyName",
        "phone", "mobile", "workPhone", "PreviousName", "email", "emailReason",
        "dob", "tob", "ssn", "sex", "TransGender", "status",
        "primaryServiceLocation", "gestationalAge", "PreferredName",
        "mflag", "demoChangedFields1", "phoneNumbersArr",
    }
    field_map = {"address1": "address"}

    tab1 = {}
    for f in tab1_fields:
        src = field_map.get(f, f)
        if f in changes:
            tab1[f] = changes[f]
        elif src in current:
            tab1[f] = current[src]

    tab2_fields = {
        "empId", "empName", "empAddress", "empAddress2", "empCity", "empState",
        "empZip", "empPhone", "StAddress", "StAddress2", "stCity", "stState",
        "stZip", "notes", "maritalstatus", "doctorId", "refPrId", "rendPrId",
        "pmcId", "Translator", "deceased", "hl7Id", "DefaultLab", "DefaultDI",
        "nostatements", "isNative", "deceasedDate", "deceasedNotes",
        "characterestic", "language", "HomeMsgType", "CellMsgType",
        "WorkMsgType", "ControlNo", "ResType", "OptOutOfPtStmt", "EmpStatus",
        "StudentStatus", "picFileName", "RelInfo", "RxConsent", "RelInfoDate",
        "SelfPay", "FeeSchId", "PrevFeeSchId", "race", "Consent",
        "FinanceChargeFlag", "excludecollection", "BirthOrder", "Ethnicity",
        "VFC", "teamMember", "emailReason", "ssnReason", "ssnReasonNotes",
        "UseStreetAddressForRxFlag", "PreferredName",
    }
    tab2_map = {"maritalstatus": "maritalStatus", "stCity": "stCity",
                "stState": "stState", "stZip": "stZip"}
    tab2 = {}
    for f in tab2_fields:
        src = tab2_map.get(f, f)
        if f in changes:
            tab2[f] = changes[f]
        elif src in current:
            tab2[f] = current[src]

    phone_prefs = changes.pop("phonePreferences", None)
    phone_fields_changed = ("phone" in changes or "mobile" in changes
                            or "workPhone" in changes or phone_prefs)
    if phone_fields_changed:
        existing_phones = fetch_phone_numbers(client, session, patient_id)

        def _default_phone_obj(ptype, patient_id_val):
            return {
                "id": 0,
                "patientId": int(patient_id_val),
                "phoneNumberType": ptype,
                "description": ptype,
                "phoneNumber": "",
                "ext": None,
                "phoneNumberWithExt": "",
                "leaveMessage": None,
                "voiceEnabled": False,
                "textEnabled": False,
                "updatedOnlyNumber": False,
                "updated": False,
            }

        cell_obj = existing_phones.get("CELL_PHONE") or _default_phone_obj(
            "Cell Phone", patient_id)
        home_obj = existing_phones.get("HOME_PHONE") or _default_phone_obj(
            "Home Phone", patient_id)
        work_obj = existing_phones.get("WORK_PHONE") or _default_phone_obj(
            "Work Phone", patient_id)

        new_cell = changes.get("mobile")
        new_home = changes.get("phone")
        new_work = changes.get("workPhone")

        if new_cell is not None and new_cell != cell_obj.get("phoneNumber", ""):
            cell_obj["phoneNumber"] = new_cell
            cell_obj["phoneNumberWithExt"] = new_cell
            cell_obj["updated"] = True

        if new_home is not None and new_home != home_obj.get("phoneNumber", ""):
            home_obj["phoneNumber"] = new_home
            home_obj["phoneNumberWithExt"] = new_home
            home_obj["updated"] = True

        if new_work is not None and new_work != work_obj.get("phoneNumber", ""):
            work_obj["phoneNumber"] = new_work
            ext = changes.get("workPhoneExt", work_obj.get("ext") or "")
            work_obj["ext"] = ext if ext else None
            work_obj["phoneNumberWithExt"] = (
                f"{new_work} X {ext}" if ext else new_work)
            work_obj["updated"] = True

        # Apply phone preferences (voice, text, leaveMessage, ext, description)
        if phone_prefs and isinstance(phone_prefs, dict):
            type_map = {"cell": cell_obj, "home": home_obj, "work": work_obj}
            for ptype, prefs in phone_prefs.items():
                obj = type_map.get(ptype)
                if not obj or not isinstance(prefs, dict):
                    continue
                if "voiceEnabled" in prefs:
                    obj["voiceEnabled"] = bool(prefs["voiceEnabled"])
                    obj["updated"] = True
                if "textEnabled" in prefs:
                    obj["textEnabled"] = bool(prefs["textEnabled"])
                    obj["updated"] = True
                if "leaveMessage" in prefs:
                    obj["leaveMessage"] = prefs["leaveMessage"]
                    obj["updated"] = True
                if "ext" in prefs:
                    obj["ext"] = prefs["ext"] if prefs["ext"] else None
                    num = obj.get("phoneNumber", "")
                    obj["phoneNumberWithExt"] = (
                        f"{num} X {prefs['ext']}" if prefs["ext"] else num)
                    obj["updated"] = True
                if "description" in prefs:
                    obj["description"] = prefs["description"][:15]
                    obj["updated"] = True

        arr = [cell_obj, home_obj, work_obj]
        tab1["phoneNumbersArr"] = json.dumps(arr)

    tab1_changed = any(f in changes for f in tab1_fields) or phone_fields_changed
    tab2_changed = any(f in changes for f in tab2_fields)

    results = {}
    if tab1_changed:
        results["tab1"] = save_demographics_tab1(
            client, session, patient_id, tab1)
    if tab2_changed:
        results["tab2"] = save_demographics_tab2(
            client, session, patient_id, tab2)

    lrte_fields = {"race", "language", "Ethnicity"}
    lrte_changed = {f for f in lrte_fields if f in changes}
    if lrte_changed:
        results["lrte"] = {}
        for field in lrte_changed:
            lrte_type = "ethnicity" if field == "Ethnicity" else field
            value = changes[field]
            translator = None
            if isinstance(value, list):
                entries = value
            elif isinstance(value, dict):
                entries = value.get("selectedValueList", [])
                translator = value.get("translator")
            elif isinstance(value, str) and value:
                lookup = get_lrte_lookup(client, session, lrte_type, value)
                if isinstance(lookup, list) and lookup:
                    exact = [x for x in lookup
                             if x.get("name", "").lower() == value.lower()]
                    entries = [exact[0] if exact else lookup[0]]
                else:
                    entries = [{"id": 0, "code": "", "name": value}]
                if lrte_type == "language" and value.lower() != "english":
                    translator = True
            else:
                entries = []
            results["lrte"][lrte_type] = save_lrte(
                client, session, patient_id, lrte_type, entries,
                translator=translator)

    if not tab1_changed and not tab2_changed and not rp_changes and not lrte_changed:
        results["message"] = "No changes detected"

    if rp_changes:
        gr_id = rp_changes.get("GrId", patient_id)
        gr_rel = rp_changes.get("GrRel", "1")
        is_gr_pt = rp_changes.get("IsGrPt", "1")
        results["responsible_party"] = set_responsible_party(
            client, session, patient_id, gr_id, gr_rel, is_gr_pt)

    if sogi_data:
        results["sogi"] = save_sogi(client, session, patient_id, sogi_data)

    if parent_data:
        results["parent_info"] = save_parent_info(
            client, session, patient_id, parent_data)

    if income_data:
        results["income"] = edit_income(
            client, session, patient_id, income_data)

    if contact_data:
        results["contact"] = add_contact(
            client, session, patient_id, contact_data)

    if update_contact_data:
        uc_id = update_contact_data.get("contact_id", "")
        uc_fields = {k: v for k, v in update_contact_data.items()
                     if k != "contact_id"}
        if uc_id and uc_fields:
            results["update_contact"] = update_contact(
                client, session, patient_id, uc_id, uc_fields)

    return results


def edit_income(client: requests.Session, session: dict,
                patient_id: str, income_data: dict) -> dict:
    income = income_data.get("Income", "0")
    dependants = income_data.get("Dependants", "1")
    unit = income_data.get("Unit", "Monthly")

    calc = calculate_sliding_fee(client, session, income, dependants, unit)

    fields = {**income_data}
    fields["AssignedType"] = calc.get("Type", calc.get("AssignedType", ""))
    fields["PovertyLevel"] = calc.get("PovertyLevel", "")
    fields["FeeSchId"] = calc.get("FeeSchId", "")
    fields["FeeSchedule"] = calc.get("FeeSchedule", "")
    fields["MedicalDiscount"] = calc.get("MedicalDiscount", "")
    fields["DentalDiscount"] = calc.get("DentalDiscount", "")
    fields["CopayDiscount"] = calc.get("CopayDiscount", "")
    fields["CopayDiscountType"] = calc.get("CopayDiscountType", "1")
    if not fields.get("AssignedDate"):
        fields["AssignedDate"] = calc.get("AssignedDate", "")
    if not fields.get("ExpiryDate"):
        fields["ExpiryDate"] = calc.get("ExpiryDate", "")

    current = get_sliding_fee_schedule(client, session, patient_id)
    has_existing = isinstance(current, dict) and current.get("Id")

    # Expire existing assignment before creating new one (matches browser HAR)
    if has_existing:
        expire_fields = {**current}
        expire_fields["ItemId"] = current["Id"]
        expire_fields.setdefault("IncomeInfo", {})
        expire_fields.setdefault("MemberInfo", [])
        save_sliding_fee_schedule(client, session, patient_id, expire_fields, expire=True)

    if has_existing and "IncomeInfo" not in fields and "IncomeInfo" in current:
        fields["IncomeInfo"] = current["IncomeInfo"]

    fields["ItemId"] = "-1"

    fields.setdefault("IncomeInfo", {})
    fields.setdefault("MemberInfo", [])

    result = save_sliding_fee_schedule(
        client, session, patient_id, fields, expire=False)
    result["calculated"] = {
        "AssignedType": calc.get("Type", calc.get("AssignedType", "")),
        "PovertyLevel": calc.get("PovertyLevel", ""),
        "FeeSchId": calc.get("FeeSchId", ""),
        "FeeSchedule": calc.get("FeeSchedule", ""),
        "MedicalDiscount": calc.get("MedicalDiscount", ""),
        "DentalDiscount": calc.get("DentalDiscount", ""),
        "AssignedDate": calc.get("AssignedDate", ""),
        "ExpiryDate": calc.get("ExpiryDate", ""),
    }
    return result


# ── Structured Data (Additional Information) ──────────────────────────────────

def _fetch_struct_detail(client: requests.Session, session: dict,
                         patient_id: str) -> list:
    """Fetch full structured data definitions with IDs, types, and parent/child relationships."""
    r = _post(client, session,
              f"/mobiledoc/jsp/catalog/xml/getStructDataDetail.jsp"
              f"?itemId=0&catId=0&encId={patient_id}&dataTable=structDemographics"
              f"&community=yes&PmtPlanId=0&woundId=1&data=yes",
              {"StructData": ""})
    r.raise_for_status()
    # Parse items via regex — _parse_soap_xml collapses duplicate <item> tags
    items = []
    for m in re.finditer(r'<item>(.*?)</item>', r.text, re.DOTALL):
        chunk = m.group(1)
        item = {}
        for field in ('Id', 'name', 'type', 'parentId', 'value', 'valueId', 'notes'):
            fm = re.search(rf'<{field}>(.*?)</{field}>', chunk, re.DOTALL)
            if fm:
                val = fm.group(1).strip()
                if field == 'name':
                    val = val.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                item[field] = val
        if item.get('Id') and item.get('name'):
            items.append(item)
    return items


def get_structured_data(client: requests.Session, session: dict,
                        patient_id: str) -> dict:
    hdrs = _get_headers(session)
    hdrs["Content-Type"] = "application/json"
    url = _make_url(
        f"/mobiledoc/emr/patienthub/structuredata?patientId={patient_id}",
        session)
    r = client.post(url, headers=hdrs)
    r.raise_for_status()
    items = r.json() if r.text.strip() else []
    result = {}
    for item in items:
        if not isinstance(item, dict) or "item" not in item:
            continue
        name = item["item"]
        value = item.get("value", "")
        parent = item.get("parentId", "0")
        if parent and parent != "0":
            # Child field — nest under parent
            if name not in result:
                result[name] = value
        else:
            result[name] = value
    return result


def save_structured_data(client: requests.Session, session: dict,
                         patient_id: str, fields: dict) -> dict:
    # Fetch all field definitions dynamically (gets IDs, including new fields)
    detail_items = _fetch_struct_detail(client, session, patient_id)

    # Build name→(id, type) map and parent→triggerFlag map for valueId resolution
    name_to_id = {}
    name_to_type = {}
    id_to_name = {}  # for resolving parent names
    parent_trigger_map = {}  # parent_id → {trigger_value: triggerFlag}

    # First pass: build id→name map
    for item in detail_items:
        if isinstance(item, dict):
            name = item.get("name", "")
            detail_id = item.get("Id", "")
            if name and detail_id:
                id_to_name[detail_id] = name

    # Second pass: build name→id with parent-qualified names for duplicates
    seen_names = set()
    for item in detail_items:
        if isinstance(item, dict):
            name = item.get("name", "")
            detail_id = item.get("Id", "")
            field_type = item.get("type", "0")
            parent_id = item.get("parentId", "0")
            if not name or not detail_id:
                continue

            # Register under plain name (first wins for top-level, last wins for children)
            if parent_id == "0":
                name_to_id[name] = detail_id
                name_to_type[name] = field_type
                seen_names.add(name)
            else:
                # Child field — also register under "Parent > Child" qualified name
                parent_name = id_to_name.get(parent_id, "")
                qualified = f"{parent_name} > {name}" if parent_name else name
                name_to_id[qualified] = detail_id
                name_to_type[qualified] = field_type
                # Only use plain name if no collision
                if name not in seen_names:
                    name_to_id[name] = detail_id
                    name_to_type[name] = field_type
                    seen_names.add(name)
                # If collision, remove the plain name mapping (force qualified)
                elif name in name_to_id and name_to_id[name] != detail_id:
                    del name_to_id[name]
                    if name in name_to_type:
                        del name_to_type[name]
            # Child items have triggerFlag — map parent→value→triggerFlag
            parent_id = item.get("parentId", "0")
            trigger_flag = item.get("triggerFlag", "")
            trigger_val = item.get("trigger", "")
            if parent_id and parent_id != "0" and trigger_flag and trigger_flag != "-1":
                if parent_id not in parent_trigger_map:
                    parent_trigger_map[parent_id] = {}
                # Map the trigger value (e.g. "Yes") to its triggerFlag ID
                if trigger_val:
                    parent_trigger_map[parent_id][trigger_val] = trigger_flag
                else:
                    parent_trigger_map[parent_id]["_default"] = trigger_flag

    # Must send ALL items — ECW replaces entire structured data on save.
    # Read current values and merge caller's changes.
    current = get_structured_data(client, session, patient_id)

    # Also read current values from detail (more complete, includes children)
    current_detail = {}
    for item in detail_items:
        if isinstance(item, dict) and item.get("value"):
            current_detail[item.get("Id", "")] = item["value"]

    # Merge: caller's fields override current
    merged = dict(current)
    for name, value in fields.items():
        merged[name] = value

    items_xml = []
    for name, detail_id in name_to_id.items():
        # Value priority: caller's merged value > detail's stored value
        value = merged.get(name, "")
        if not value:
            value = current_detail.get(detail_id, "")
        notes = ""
        if isinstance(value, dict):
            notes = value.get("notes", "")
            value = value.get("value", "")
        if not value:
            continue
        # Normalize date values based on field type (confirmed from source)
        field_type = name_to_type.get(name, "0")
        if field_type == "4" and value:
            # Type 4 = month-year picker: MM-YYYY (hyphen, no day)
            # Source: closeMonthYearPicker → month + "-" + year
            value = value.replace("/", "-")
            parts = value.split("-")
            if len(parts) == 3:
                if len(parts[0]) == 4:
                    value = f"{parts[1]}-{parts[0]}"  # YYYY-MM-DD -> MM-YYYY
                else:
                    value = f"{parts[0]}-{parts[2]}"  # MM-DD-YYYY -> MM-YYYY
        elif field_type == "2" and value:
            # Type 2 = full date: MM/DD/YYYY (slashes)
            # Source: validateStructDataDate → moment(value, ["MM/DD/YYYY"], true)
            value = value.replace("-", "/")
            parts = value.split("/")
            if len(parts) == 3 and len(parts[0]) == 4:
                value = f"{parts[1]}/{parts[2]}/{parts[0]}"  # YYYY/MM/DD -> MM/DD/YYYY
        # Resolve valueId for parent fields with Yes/No children
        value_id = ""
        triggers = parent_trigger_map.get(detail_id, {})
        if triggers:
            value_id = triggers.get(str(value), triggers.get("_default", ""))
        items_xml.append(
            f'<item xsi:type="xsd:string">'
            f'<detailId xsi:type="xsd:string">{detail_id}</detailId>'
            f'<value xsi:type="xsd:string"><![CDATA[{value}]]></value>'
            f'<notes xsi:type="xsd:string"><![CDATA[{notes}]]></notes>'
            f'<valueId xsi:type="xsd:string">{value_id}</valueId>'
            f'</item>')

    full_xml = _soap_envelope("".join(items_xml))
    data = {"FormData": full_xml, "StructData": ""}
    r = _post(client, session,
              f"/mobiledoc/jsp/catalog/xml/setStructData.jsp"
              f"?encId={patient_id}&catId=0&itemId=0&table=structDemographics",
              data)
    r.raise_for_status()
    return _soap_result(r)


# ── Insurance Card Upload ─────────────────────────────────────────────────────

def upload_insurance_card(client: requests.Session, session: dict,
                          patient_id: str, image_bytes: bytes,
                          filename: str = "insurance_card.png",
                          description: str = "") -> dict:
    import uuid as _uuid
    from datetime import datetime as _dt

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
    custom_name = filename.rsplit(".", 1)[0] if "." in filename else filename
    generated_name = f"{_uuid.uuid4()}_{patient_id}.{ext}"
    now = _dt.now()
    dir_path = f"/mobiledoc/{now.year}/{now.strftime('%m%d%Y')}"
    scanned_date = f"{now.year}-{now.month}-{now.day}"

    doc_xml = (
        f'<Document>'
        f'<PatientId xsi:type="xsd:string">{patient_id}</PatientId>'
        f'<FileName xsi:type="xsd:string">{generated_name}</FileName>'
        f'<catid xsi:type="xsd:string">202</catid>'
        f'<CustomName xsi:type="xsd:string">{_escape_xml(custom_name)}</CustomName>'
        f'<ScannedDate xsi:type="xsd:string">{scanned_date}</ScannedDate>'
        f'<ScannedBy xsi:type="xsd:string"></ScannedBy>'
        f'<Description xsi:type="xsd:string">{_escape_xml(description)}</Description>'
        f'<Review xsi:type="xsd:string">0</Review>'
        f'<ReviewerId xsi:type="xsd:string">{session["tr_user_id"]}</ReviewerId>'
        f'<ReviewerName xsi:type="xsd:string"></ReviewerName>'
        f'<Priority xsi:type="xsd:string">0</Priority>'
        f'<encId xsi:type="xsd:string">0</encId>'
        f'<refID xsi:type="xsd:string">0</refID>'
        f'<AttachTo xsi:type="xsd:string"></AttachTo>'
        f'<DocAndLabReview xsi:type="xsd:string">0</DocAndLabReview>'
        f'<PublishToeHX xsi:type="xsd:string">0</PublishToeHX>'
        f'<FacilityId xsi:type="xsd:string">0</FacilityId>'
        f'<DirPath xsi:type="xsd:string">{dir_path}</DirPath>'
        f'<FtpServer xsi:type="xsd:string"></FtpServer>'
        f'<Tags xsi:type="xsd:string"></Tags>'
        f'<refReqId xsi:type="xsd:string">0</refReqId>'
        f'<scanById xsi:type="xsd:string">{session["tr_user_id"]}</scanById>'
        f'</Document>')
    form_data_xml = _soap_envelope(doc_xml)

    query_params = urllib.parse.urlencode({
        "scan": "no", "operation": "upload",
        "filename": generated_name, "filepath": dir_path,
        "transformInput": "", "moduleName": "patientDocuments",
    })

    content_type_map = {
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "gif": "image/gif", "pdf": "application/pdf",
        "tif": "image/tiff", "tiff": "image/tiff", "bmp": "image/bmp",
    }
    mime = content_type_map.get(ext, "application/octet-stream")

    url = _make_url(f"/mobiledoc/ecwimage?{query_params}", session)
    hdrs = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-CSRF-TOKEN": session["csrf_token"],
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/mobiledoc/jsp/webemr/index.jsp",
    }
    r = client.post(url, files={filename: (filename, image_bytes, mime)},
                    data={"callingForm": "patientDocuments", "nact": "2",
                          "PatientId": patient_id, "FormData": form_data_xml,
                          "triggerEventModuleName": "patientDocuments"},
                    headers=hdrs)
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    ret = parsed.get("return", parsed)
    doc_id = ret.get("documentId", "") if isinstance(ret, dict) else ""
    return _soap_result(r, {"documentId": doc_id, "fileName": generated_name})


# ── Profile Picture Upload ────────────────────────────────────────────────────

def upload_profile_picture(client: requests.Session, session: dict,
                           patient_id: str, image_bytes: bytes) -> dict:
    filename = f"{patient_id}.jpg"
    url = _make_url(
        f"/mobiledoc/ecwimage?operation=upload&filename={filename}"
        f"&filepath=/mobiledoc/Patients",
        session)
    hdrs = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-CSRF-TOKEN": session["csrf_token"],
        "X-Requested-With": "XMLHttpRequest",
        "isAjaxRequest": "true",
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/mobiledoc/jsp/webemr/index.jsp",
    }
    r = client.post(url,
                    files={"sampleFile": ("blob", image_bytes, "image/jpeg")},
                    data={"foldername": "", "id": "", "flag": ""},
                    headers=hdrs)
    r.raise_for_status()
    ok = "success" in r.text.lower()
    return {"status_code": 200 if ok else 400,
            "body": r.text.strip(),
            "fileName": filename}


# ── Communication Notes ───────────────────────────────────────────────────────

def save_communication_notes(client: requests.Session, session: dict,
                             patient_id: str, notes: str) -> dict:
    """Save communication notes. Requires full voiceconfig/textconfig with valid IDs.

    The config IDs are server-side records. We use id=0 to indicate
    no change to voice/text config, only updating the patient notes.
    """
    notes = notes[:255]
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    payload = json.dumps({
        "voiceconfig": {
            "prefcomm": "Voice", "appointments": "1", "contacttype": "home",
            "rx": "0", "language": "English", "healthmaintenance": "1",
            "timetocall": "Morning", "ptstatements": "0", "uid": str(patient_id),
            "primeplus": "1", "labs": "0", "datemodified": now,
            "generalnotification": "1", "id": "0",
        },
        "textconfig": {
            "appointments": "1", "contacttype": "cell", "rx": "0",
            "language": "En", "healthmaintenance": "1", "timetocall": "Morning",
            "ptstatements": "0", "uid": str(patient_id), "primeplus": "1",
            "labs": "0", "datemodified": now, "generalnotification": "1", "id": "0",
        },
        "user": {"id": str(patient_id), "emailupdated": "no"},
        "patient": {
            "id": str(patient_id),
            "lognotes": notes,
            "optout": "0",
            "textenabled": "1",
            "voiceenabled": "1",
            "isptoptsout": "0",
            "enableletters": "0",
        },
        "ptDetails": {},
        "publicityCode": 0,
        "h2hEnabled": False,
        "contacttypeoptions": [],
    })
    post_body = f"record={urllib.parse.quote(payload)}"
    hdrs = _get_headers(session)
    url = _make_url(
        "/mobiledoc/jsp/webemr/toppanel/voice/savePtCommunications.jsp",
        session, post_body=post_body)
    r = client.post(url, data={"record": payload}, headers=hdrs)
    r.raise_for_status()
    ok = "success" in r.text.lower()
    return {"status_code": 200 if ok else 400, "body": r.text.strip()}


def _fetch_communication_data(client: requests.Session, session: dict,
                              patient_id: str) -> tuple:
    """Fetch existing communication configs. Returns (voiceconfig, textconfig, patient, user)."""
    hdrs = _get_headers(session)
    url = _make_url(
        f"/mobiledoc/jsp/webemr/toppanel/voice/fetchpatientcommunicationdata.jsp"
        f"?uid={patient_id}",
        session)
    r = client.post(url, headers=hdrs)
    r.raise_for_status()
    data = r.json() if r.text.strip() else []
    voice = data[0] if len(data) > 0 and isinstance(data[0], dict) else {}
    text = data[1] if len(data) > 1 and isinstance(data[1], dict) else {}
    patient = data[2] if len(data) > 2 and isinstance(data[2], dict) else {}
    user = data[3] if len(data) > 3 and isinstance(data[3], dict) else {}
    return voice, text, patient, user


def save_communication_settings(client: requests.Session, session: dict,
                                patient_id: str, data: dict) -> dict:
    """Save communication settings: voice/text phone assignments, notes, reminders."""
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    # Load existing configs to get record IDs and preserve unchanged fields
    cur_voice, cur_text, cur_patient, cur_user = _fetch_communication_data(
        client, session, patient_id)

    # Merge caller's changes into existing configs
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    default_cfg = {
        "appointments": "1", "contacttype": "cell", "rx": "0",
        "healthmaintenance": "1", "timetocall": "Morning", "ptstatements": "0",
        "uid": str(patient_id), "primeplus": "1", "labs": "0",
        "datemodified": now, "generalnotification": "1", "id": "0",
    }
    if cur_voice:
        voice_cfg = dict(cur_voice)
    else:
        # No existing voice record — send minimal config (ECW creates on save)
        voice_cfg = {"contacttype": "cell", "language": "English",
                     "uid": str(patient_id)}
    if cur_text:
        text_cfg = dict(cur_text)
    else:
        text_cfg = {"contacttype": "cell", "language": "En",
                    "uid": str(patient_id)}
    patient_cfg = dict(cur_patient) if cur_patient else {"id": str(patient_id)}
    user_cfg = dict(cur_user) if cur_user else {"id": str(patient_id)}

    if "voice_phone" in data:
        voice_cfg["contacttype"] = data["voice_phone"]
    if "text_phone" in data:
        text_cfg["contacttype"] = data["text_phone"]
    if "voice_language" in data:
        voice_cfg["language"] = data["voice_language"]
    if "text_language" in data:
        text_cfg["language"] = data["text_language"]
    if "time_to_call" in data:
        voice_cfg["timetocall"] = data["time_to_call"]
        text_cfg["timetocall"] = data["time_to_call"]
    if "voice_enabled" in data:
        patient_cfg["voiceenabled"] = data["voice_enabled"]
    if "text_enabled" in data:
        patient_cfg["textenabled"] = data["text_enabled"]
    if "notes" in data:
        patient_cfg["lognotes"] = data["notes"][:255]

    # Reminder types
    reminders = data.get("reminders", {})
    for key, xml_key in [("appointments", "appointments"), ("labs", "labs"),
                         ("health_maintenance", "healthmaintenance"),
                         ("rx", "rx"), ("general_notification", "generalnotification"),
                         ("primeplus", "primeplus"), ("pt_statements", "ptstatements")]:
        if key in reminders:
            voice_cfg[xml_key] = reminders[key]
            text_cfg[xml_key] = reminders[key]

    voice_cfg["datemodified"] = now
    text_cfg["datemodified"] = now
    user_cfg["emailupdated"] = "no"

    payload = json.dumps({
        "voiceconfig": voice_cfg,
        "textconfig": text_cfg,
        "user": user_cfg,
        "patient": patient_cfg,
        "ptDetails": {},
        "publicityCode": 0,
        "h2hEnabled": False,
        "contacttypeoptions": [],
    })
    post_body = f"record={urllib.parse.quote(payload)}"
    hdrs = _get_headers(session)
    url = _make_url(
        "/mobiledoc/jsp/webemr/toppanel/voice/savePtCommunications.jsp",
        session, post_body=post_body)
    r = client.post(url, data={"record": payload}, headers=hdrs)
    r.raise_for_status()
    ok = "success" in r.text.lower()
    return {"status_code": 200 if ok else 400, "body": r.text.strip()}


# ── Send SMS ──────────────────────────────────────────────────────────────────

def _text_to_utf16be_hex(text: str) -> str:
    """Encode text to UTF-16BE hex string (ECW's SMS message format)."""
    return text.encode("utf-16-be").hex()


def send_sms(client: requests.Session, session: dict,
             patient_id: str, message: str) -> dict:
    hex_msg = _text_to_utf16be_hex(message)
    sms_xml = (
        f'<?xml version="1.0"?>'
        f'<Templates>'
        f'<EnglishTemplate><![CDATA[{hex_msg}]]></EnglishTemplate>'
        f'<OriginalTemplate><![CDATA[{hex_msg}]]></OriginalTemplate>'
        f'<SpanishTemplate><![CDATA[{hex_msg}]]></SpanishTemplate>'
        f'</Templates>'
    )
    data = {
        "action": "sendtextsms",
        "textNotification": "1",
        "voiceNotification": "0",
        "smsMessage": sms_xml,
        "smsTemplateName": "",
        "PatientIds": patient_id,
        "TrUserId": session["tr_user_id"],
        "EncIds": "",
        "smstemplateid": "0",
        "smsMsgType": "",
        "Flag": "",
        "msgSource": "Patient Comm Settings",
        "isSecured": "",
        "msgserver": BASE_URL,
    }
    post_body = urllib.parse.urlencode(data)
    url = _make_url("/mobiledoc/jsp/webemr/singlesend/singleSend.jsp",
                    session, post_body=post_body)
    hdrs = _get_headers(session)
    r = client.post(url, data=data, headers=hdrs)
    r.raise_for_status()
    return _soap_result(r)


# ── Telephone Encounter ───────────────────────────────────────────────────────

def create_telephone_encounter(client: requests.Session, session: dict,
                               patient_id: str, data: dict) -> dict:
    from datetime import datetime as _dt
    now = _dt.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%I:%M:%S %p")

    caller = data.get("caller", "")
    reason = data.get("reason", "")
    message = data.get("message", "")
    action_taken = data.get("action_taken", "")
    notes = data.get("notes", "")
    provider_id = data.get("provider_id", session["tr_user_id"])
    facility_id = data.get("facility_id", "0")
    status = data.get("status", "")
    assigned_to_id = data.get("assigned_to_id", session["tr_user_id"])
    assigned_to_name = data.get("assigned_to_name", "")
    priority = data.get("priority", "0")

    enc_xml = (
        f'<encounter xsi:type="xsd:string">'
        f'<id xsi:type="xsd:int">{patient_id}</id>'
        f'<date xsi:type="xsd:string">{date_str}</date>'
        f'<time xsi:type="xsd:string">{time_str}</time>'
        f'<endTime xsi:type="xsd:string">{time_str}</endTime>'
        f'<DateTimeEdit xsi:type="xsd:string">true</DateTimeEdit>'
        f'<visitType xsi:type="xsd:string">TEL</visitType>'
        f'<reason xsi:type="xsd:string">{_escape_xml(reason)}</reason>'
        f'<doctorid xsi:type="xsd:int">{provider_id}</doctorid>'
        f'<status xsi:type="xsd:string">{_escape_xml(status)}</status>'
        f'<billing xsi:type="xsd:string"></billing>'
        f'<encType xsi:type="xsd:int">2</encType>'
        f'<notes xsi:type="xsd:string"></notes>'
        f'<visitSubType xsi:type="xsd:string"></visitSubType>'
        f'<facilityId xsi:type="xsd:int">{facility_id}</facilityId>'
        f'<POS xsi:type="xsd:int">50</POS>'
        f'<arrTime xsi:type="xsd:string">00:00:00</arrTime>'
        f'<depTime xsi:type="xsd:string">00:00:00</depTime>'
        f'<ptFlag xsi:type="xsd:int">0</ptFlag>'
        f'<Dx xsi:type="xsd:string"></Dx>'
        f'<visitTypeOverriden xsi:type="xsd:string"></visitTypeOverriden>'
        f'<refPrName xsi:type="xsd:string"></refPrName>'
        f'<refPrId xsi:type="xsd:string"></refPrId>'
        f'<DeptId xsi:type="xsd:int">0</DeptId>'
        f'<UserInfo xsi:type="xsd:string"></UserInfo>'
        f'<resourceId xsi:type="xsd:string"></resourceId>'
        f'<resFacFilterId xsi:type="xsd:int">0</resFacFilterId>'
        f'<practiceId xsi:type="xsd:int">0</practiceId>'
        f'<transitionofcare xsi:type="xsd:int">0</transitionofcare>'
        f'<isTelEncWeb xsi:type="xsd:int">1</isTelEncWeb>'
        f'<ptEmail xsi:type="xsd:string"></ptEmail>'
        f'<populatetelencdata xsi:type="xsd:string">true</populatetelencdata>'
        f'</encounter>')

    tel_xml = (
        f'<telencounter xsi:type="xsd:string">'
        f'<encounterid xsi:type="xsd:int">0</encounterid>'
        f'<uid xsi:type="xsd:int">{session["tr_user_id"]}</uid>'
        f'<caller xsi:type="xsd:string">{_escape_xml(caller)}</caller>'
        f'<message xsi:type="xsd:string">{_escape_xml(message)}</message>'
        f'<actiontaken xsi:type="xsd:string">{_escape_xml(action_taken)}</actiontaken>'
        f'<notes xsi:type="xsd:string">{_escape_xml(notes)}</notes>'
        f'<priority xsi:type="xsd:int">{priority}</priority>'
        f'<AssignedToId xsi:type="xsd:string">{assigned_to_id}</AssignedToId>'
        f'<assignedTo xsi:type="xsd:string">{_escape_xml(assigned_to_name)}</assignedTo>'
        f'<pmcid xsi:type="xsd:int">0</pmcid>'
        f'<LoginID xsi:type="xsd:int">{session["tr_user_id"]}</LoginID>'
        f'<virtualflag xsi:type="xsd:string">0</virtualflag>'
        f'<UIScreenName xsi:type="xsd:string">web_TJellyDetailViewid</UIScreenName>'
        f'<TopClass xsi:type="xsd:string">telenc_assignedTolookup</TopClass>'
        f'<isAddressed xsi:type="xsd:string">false</isAddressed>'
        f'</telencounter>')

    full_xml = _soap_envelope(f'{enc_xml}{tel_xml}')
    post_data = {"TrUserId": session["tr_user_id"], "FormData": full_xml}
    post_body = urllib.parse.urlencode(post_data)
    url = _make_url("/mobiledoc/jsp/catalog/xml/newEncounter.jsp",
                    session, post_body=post_body)
    hdrs = _get_headers(session)
    r = client.post(url, data=post_data, headers=hdrs)
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    ret = parsed.get("return", parsed)
    if isinstance(ret, dict):
        enc_id = ret.get("encounterID", "")
        ticket_id = ret.get("ticketId", "")
        status = ret.get("status", "")
        body = {"status": status, "encounterID": enc_id, "ticketId": ticket_id}
    else:
        body = ret
    soap_status = ret.get("status", "") if isinstance(ret, dict) else ""
    return {"status_code": 400 if soap_status == "failed" else r.status_code,
            "body": body}

