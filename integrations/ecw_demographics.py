"""
eClinicalWorks Demographics Integration (Endgame)
Platform: caoshae8e528d1yp90app.ecwcloud.com

Actions: read, edit-demographics, read-combos, read-sliding-fee, calculate,
         search-provider, get-contacts, add-contact, update-contact,
         set-responsible-party, edit-income

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

        elif action == "read-lrte":
            option = input_data.get("option", "")
            search = input_data.get("search", "")
            if option == "language":
                return {"languages": search_languages(client, session, search)}
            elif option == "race":
                return {"races": get_race_list(client, session)}
            else:
                return {"status_code": 400,
                        "body": {"error": "option must be 'language' or 'race'"}}

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

        elif action == "upload-insurance-card":
            image_b64 = input_data.get("image_base64", "")
            if not image_b64:
                return {"status_code": 400,
                        "body": {"error": "image_base64 is required (base64-encoded image)"}}
            import base64 as _b64
            image_bytes = _b64.b64decode(image_b64)
            fname = input_data.get("filename", "insurance_card.png")
            desc = input_data.get("description", "")
            return upload_insurance_card(
                client, session, patient_id, image_bytes, fname, desc)

        elif action == "get-parent-info":
            return get_parent_info(client, session, patient_id)

        elif action == "save-parent-info":
            parent_data = input_data.get("parent_info", {})
            if not parent_data:
                return {"status_code": 400,
                        "body": {"error": "parent_info dict is required"}}
            return save_parent_info(client, session, patient_id, parent_data)

        elif action == "get-sogi":
            return get_sogi(client, session, patient_id)

        elif action == "save-sogi":
            return save_sogi(client, session, patient_id, input_data)

        elif action == "search-guarantor":
            search = input_data.get("search", "")
            lastname, firstname = "", ""
            if "," in search:
                parts = search.split(",", 1)
                lastname, firstname = parts[0].strip(), parts[1].strip()
            else:
                lastname = search.strip()
            search_type = input_data.get("type", "patient")
            if search_type == "guarantor":
                return {"guarantors": search_guarantors(
                    client, session, lastname, firstname)}
            return {"patients": search_patients(
                client, session, lastname, firstname)}

        elif action == "get-guarantor-info":
            gr_id = input_data.get("gr_id", "")
            if not gr_id:
                return {"status_code": 400,
                        "body": {"error": "gr_id is required"}}
            return get_guarantor_info(client, session, gr_id)

        else:
            return {"status_code": 400,
                    "body": {"error": f"Unknown action: {action}",
                             "valid_actions": [
                                 "read", "edit-demographics", "read-combos",
                                 "read-lrte", "read-sliding-fee", "calculate",
                                 "search-provider", "get-contacts",
                                 "add-contact", "update-contact",
                                 "set-responsible-party", "edit-income",
                                 "upload-insurance-card",
                                 "get-parent-info", "save-parent-info",
                                 "get-sogi", "save-sogi",
                                 "search-guarantor", "get-guarantor-info",
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
    return {"status_code": r.status_code, "body": r.text[:500]}


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
    return {"status_code": r.status_code, "body": r.text[:500]}


# ── WRITE: Language / Race (LRTE REST endpoints) ─────────────────────────────

RACE_LOOKUP = {
    "white": ("2106-3", 1043),
    "asian": ("2028-9", 1749),
    "black or african american": ("2054-5", 1044),
    "american indian or alaska native": ("1002-5", 1042),
    "native hawaiian or other pacific islander": ("2076-8", 1805),
}

LANGUAGE_LOOKUP = {
    "english": ("en", 74),
    "spanish": ("es", 196),
    "french": ("fr", 234),
    "chinese": ("zh", 48),
    "vietnamese": ("vi", 224),
    "korean": ("ko", 120),
    "portuguese": ("pt", 169),
    "arabic": ("ar", 14),
    "russian": ("ru", 179),
    "tagalog": ("tl", 210),
    "german": ("de", 62),
    "japanese": ("ja", 113),
    "hindi": ("hi", 92),
}


def _resolve_race(race_str: str, client=None, session=None) -> dict:
    key = race_str.strip().lower()
    code, rid = RACE_LOOKUP.get(key, ("", 0))
    if not code and client and session:
        races = get_race_list(client, session)
        for r in races:
            if r.get("name", "").lower() == key:
                return {"name": r["name"], "code": r.get("code", ""),
                        "id": r.get("id", 0), "source": r.get("source", "System-Defined (CDC)"),
                        "uiFlag": 1, "checked": True}
    return {"name": race_str.strip(), "code": code, "id": rid,
            "source": "System-Defined (CDC)", "uiFlag": 1, "checked": True}


def _resolve_language(lang_str: str, client=None, session=None) -> tuple:
    key = lang_str.strip().lower()
    code, lid = LANGUAGE_LOOKUP.get(key, ("", 0))
    if not code and client and session:
        results = search_languages(client, session, lang_str.strip())
        for r in results:
            if r.get("name", "").lower() == key:
                return r["name"], r.get("code", ""), r.get("id", 0)
    return lang_str.strip(), code, lid


def search_languages(client: requests.Session, session: dict,
                     search: str = "") -> list:
    hdrs = _get_headers(session)
    hdrs["Content-Type"] = "application/json"
    url = _make_url("/mobiledoc/emr/patient/demographics/lrte/get-language-list", session)
    payload = {"counter": 1, "name": search, "code": "", "mappedValue": "",
               "source": "All", "pin": "All", "sortOrder": "ASC"}
    r = client.post(url, json=payload, headers=hdrs)
    r.raise_for_status()
    data = r.json()
    return data.get("result", {}).get("LanguageList", [])


def get_race_list(client: requests.Session, session: dict) -> list:
    hdrs = _get_headers(session)
    hdrs["Content-Type"] = "application/json"
    url = _make_url("/mobiledoc/emr/patient/demographics/lrte/getLRTEData?counter=1", session)
    r = client.post(url, headers=hdrs)
    r.raise_for_status()
    data = r.json()
    return data.get("RaceObject", {}).get("result", {}).get("RaceList", [])


def save_language(client: requests.Session, session: dict,
                  patient_id: str, language_name: str,
                  language_code: str = "", language_id: int = 0,
                  translator: int = 0) -> dict:
    hdrs = _get_headers(session)
    hdrs["Content-Type"] = "application/json"
    url = _make_url("/mobiledoc/emr/patient/demographics/lrte/language/save", session)
    payload = {
        "patientId": str(patient_id),
        "declineToSpecify": 0,
        "selectedValueList": [{
            "id": language_id,
            "mappedId": 0,
            "name": language_name,
            "code": language_code,
            "mappedValue": language_name,
            "source": "System-Defined",
            "uiFlag": 1,
            "favorite": 0,
            "checked": True,
        }],
        "translator": translator,
    }
    r = client.post(url, json=payload, headers=hdrs)
    r.raise_for_status()
    return r.json() if r.text.strip() else {"status_code": r.status_code}


def save_race(client: requests.Session, session: dict,
              patient_id: str, races: list) -> dict:
    hdrs = _get_headers(session)
    hdrs["Content-Type"] = "application/json"
    url = _make_url("/mobiledoc/emr/patient/demographics/lrte/race/save", session)
    selected = []
    for race in races:
        if isinstance(race, str):
            selected.append(_resolve_race(race, client, session))
        elif isinstance(race, dict):
            selected.append({
                "id": race.get("id", 0), "name": race.get("name", ""),
                "code": race.get("code", ""),
                "source": race.get("source", "System-Defined (CDC)"),
                "uiFlag": 1, "checked": True,
            })
    payload = {
        "patientId": str(patient_id),
        "declineToSpecify": 0,
        "selectedValueList": selected,
    }
    r = client.post(url, json=payload, headers=hdrs)
    r.raise_for_status()
    return r.json() if r.text.strip() else {"status_code": r.status_code}


# ── WRITE: Sliding Fee Schedule (Income) ─────────────────────────────────────

def save_sliding_fee_schedule(client: requests.Session, session: dict,
                              patient_id: str, fields: dict,
                              expire: bool = False) -> dict:
    expired_status = "1" if expire else "0"

    income_info = fields.get("IncomeInfo", {})
    income_elements = []
    income_elements.append(_add_element_raw("IncomeDetailId",
                                            income_info.get("IncomeDetailId",
                                            income_info.get("Id", "0"))))
    income_elements.append(_add_element_raw("GrHrRate",
                                            income_info.get("GrHrRate", "")))
    income_elements.append(_add_element_raw("GrHrPerWeek",
                                            income_info.get("GrHrPerWeek", "")))
    income_elements.append(_add_element_raw("GrGrossAmt",
                                            income_info.get("GrGrossAmt", "")))
    income_elements.append(_add_element_raw("GrBiIncome",
                                            income_info.get("GrBiRate", "")))
    income_elements.append(_add_element_raw("GrBiGrossAmt",
                                            income_info.get("GrBiGrossAmt", "")))
    income_elements.append(_add_element_raw("SpHrRate",
                                            income_info.get("SpHrRate", "")))
    income_elements.append(_add_element_raw("SpHrPerWeek",
                                            income_info.get("SpHrPerWeek", "")))
    income_elements.append(_add_element_raw("SpGrossAmt",
                                            income_info.get("SpGrossAmt", "")))
    income_elements.append(_add_element_raw("SpBiIncome",
                                            income_info.get("SpBiRate", "")))
    income_elements.append(_add_element_raw("SpBiGrossAmt",
                                            income_info.get("SpBiGrossAmt", "")))
    income_elements.append(
        f'<UserId xsi:type="xsd:int">{session["tr_user_id"]}</UserId>')
    income_elements.append(_add_element_raw("UserName",
                                            fields.get("UserName", "")))
    income_elements.append(_add_element_raw("OtherIncomeTypes",
                                            income_info.get("OtherIncomeTypes", "")))
    other_amts = income_info.get("OtherIncomeAmt", "0,0,0,0")
    income_elements.append(_add_element_raw("OtherIncome", other_amts))
    income_elements.append(_add_element_raw("OtherIncomeGrossAmt",
                                            income_info.get("OtherIncomeGrossAmt", "")))
    income_elements.append(_add_element_raw("ProofOfIncome",
                                            income_info.get("ProofOfIncome", "")))
    income_elements.append(_add_element_raw("OtherIncomeReason",
                                            _escape_xml(income_info.get("OtherIncomeReason", ""))))
    income_elements.append(_add_element_raw("MemberNotes",
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
    info_elements.append(_add_element_raw("ItemId",
                                          fields.get("ItemId", "-1")))
    info_elements.append(_add_element_raw("PatientId", patient_id))
    info_elements.append(_add_element_raw("Income",
                                          fields.get("Income", "0")))
    info_elements.append(_add_element_raw("Unit",
                                          fields.get("Unit", "Monthly")))
    info_elements.append(_add_element_raw("Dependant",
                                          fields.get("Dependants", "1")))
    info_elements.append(_add_element_raw("PovertyLevel",
                                          fields.get("PovertyLevel", "")))
    info_elements.append(
        f'<AssignedStatus xsi:type="xsd:int">1</AssignedStatus>')
    info_elements.append(_add_element_raw("AssignedDate",
                                          _date_to_yyyymmdd(fields.get("AssignedDate", ""))))
    info_elements.append(_add_element_raw("ExpiryDate",
                                          _date_to_yyyymmdd(fields.get("ExpiryDate", ""))))
    info_elements.append(_add_element_raw("AssignedType",
                                          fields.get("AssignedType", "")))
    info_elements.append(_add_element_raw("FeeSchId",
                                          fields.get("FeeSchId", "")))
    info_elements.append(_add_element_raw("FeeSchedule",
                                          fields.get("FeeSchedule", "")))
    info_elements.append(_add_element_raw("DocProof",
                                          fields.get("DocProof", "0")))
    info_elements.append(_add_element_raw("NonProofOfIncome",
                                          fields.get("NonProofOfIncome", "0")))
    info_elements.append(_add_element_raw("MedicalDiscount",
                                          fields.get("MedicalDiscount", "")))
    info_elements.append(_add_element_raw("DentalDiscount",
                                          fields.get("DentalDiscount", "")))
    info_elements.append(_add_element_raw("CopayDiscount",
                                          fields.get("CopayDiscount", "")))
    info_elements.append(
        f'<CopayDiscountType xsi:type="xsd:int">'
        f'{fields.get("CopayDiscountType", "1")}</CopayDiscountType>')
    info_elements.append(_add_element_raw("Expired", expired_status))
    no_proof_reason = fields.get("NoProofReason", "")
    if fields.get("NonProofOfIncome") == "1" and no_proof_reason:
        info_elements.append(_add_element_raw("NoProofReason", no_proof_reason))
    else:
        info_elements.append(_add_element_raw("NoProofReason", ""))

    info_xml = f'<Info xsi:type="xsd:string">{"".join(info_elements)}</Info>'

    body_xml = f'{income_xml}{member_xml}{info_xml}'
    full_xml = _soap_envelope(body_xml)

    r = _post(client, session,
              "/mobiledoc/jsp/catalog/xml/edi/setSlidingFeeScheduleForPatient.jsp",
              {"FormData": full_xml})
    r.raise_for_status()
    return {"status_code": r.status_code, "body": r.text[:500]}


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
    e.append(_add_element("workPhone", contact.get("workPhone", "")))
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
    contact_id = ""
    if isinstance(ret, dict):
        contact_id = ret.get("contactId", "")
    return {"status_code": r.status_code, "contactId": contact_id,
            "body": r.text[:500]}


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
    return {"status_code": r.status_code, "body": r.text[:500]}


# ── WRITE: Responsible Party ─────────────────────────────────────────────────

def set_responsible_party(client: requests.Session, session: dict,
                          patient_id: str, gr_id: str,
                          gr_rel: str = "1",
                          is_gr_pt: str = "1") -> dict:
    elements = []
    elements.append(_add_element("PrimIns", ""))
    elements.append(
        f'<ResponsibleParty>'
        f'{_add_element("GrId", gr_id)}'
        f'{_add_element("GrRel", gr_rel)}'
        f'{_add_element("IsGrPt", is_gr_pt)}'
        f'</ResponsibleParty>'
    )
    full_xml = _soap_envelope("".join(elements))
    data = {"FormData": full_xml}
    r = _post(client, session,
              f"/mobiledoc/jsp/catalog/xml/setInsDetail.jsp"
              f"?patientId={patient_id}",
              data)
    r.raise_for_status()
    return {"status_code": r.status_code, "body": r.text[:500]}


# ── Convenience: Read-Modify-Write ───────────────────────────────────────────

def edit_demographics(client: requests.Session, session: dict,
                      patient_id: str, changes: dict) -> dict:
    rp_keys = {"GrId", "GrRel", "IsGrPt"}
    rp_changes = {k: changes.pop(k) for k in rp_keys if k in changes}

    current = get_patient_info(client, session, patient_id)
    if isinstance(current, dict) and "patient" in current:
        current = current["patient"]

    tab1_fields = {
        "prefix", "suffix", "fname", "lname", "mname",
        "address1", "address2", "city", "state", "zip",
        "Country", "CountyCode", "CountyName", "MailCountyCode", "MailCountyName",
        "phone", "mobile", "PreviousName", "email", "emailReason",
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
    # Reverse map so callers can use either casing (e.g. "maritalStatus" or "maritalstatus")
    tab2_alias = {v: k for k, v in tab2_map.items() if v != k}
    tab2 = {}
    for f in tab2_fields:
        src = tab2_map.get(f, f)
        alias = tab2_alias.get(f)
        if f in changes:
            tab2[f] = changes[f]
        elif src in changes:
            tab2[f] = changes[src]
        elif alias and alias in changes:
            tab2[f] = changes[alias]
        elif src in current:
            tab2[f] = current[src]

    if "phone" in changes or "mobile" in changes:
        cell = changes.get("mobile", current.get("umobileno", ""))
        home = changes.get("phone", current.get("phone", ""))
        work_phone = current.get("empPhone", "")
        def _phone_obj(number, ptype, desc):
            return {"id": 0, "patientId": 0, "phoneNumberType": ptype,
                    "description": desc, "phoneNumber": number,
                    "ext": None, "phoneNumberWithExt": number,
                    "leaveMessage": None, "voiceEnabled": None}
        arr = [
            _phone_obj(cell, "Cell Phone", "Cell Phone"),
            _phone_obj(home, "Home Phone", "Home Phone"),
            _phone_obj(work_phone, "Work Phone", "Work Phone"),
        ]
        tab1["phoneNumbersArr"] = json.dumps(arr)

    tab1_changed = any(f in changes for f in tab1_fields)
    tab2_changed = any(
        f in changes or tab2_map.get(f, f) in changes
        for f in tab2_fields
    )

    # Language and race use dedicated LRTE REST endpoints, not setPatient1.jsp
    lrte_keys = {"language", "race", "Translator"}
    lrte_changes = {k: changes[k] for k in lrte_keys if k in changes}

    results = {}
    if tab1_changed:
        results["tab1"] = save_demographics_tab1(
            client, session, patient_id, tab1)
    if tab2_changed:
        results["tab2"] = save_demographics_tab2(
            client, session, patient_id, tab2)

    if "language" in lrte_changes:
        lang = lrte_changes["language"]
        translator = int(lrte_changes.get("Translator", changes.get("Translator", 0)))
        if isinstance(lang, dict):
            results["language"] = save_language(
                client, session, patient_id,
                lang.get("name", ""), lang.get("code", ""),
                lang.get("id", 0), translator)
        else:
            name, code, lid = _resolve_language(str(lang), client, session)
            results["language"] = save_language(
                client, session, patient_id, name, code, lid, translator)
    elif "Translator" in lrte_changes:
        cur_lang = current.get("language", "")
        name, code, lid = _resolve_language(cur_lang, client, session)
        results["language"] = save_language(
            client, session, patient_id, name, code, lid,
            translator=int(lrte_changes["Translator"]))

    if "race" in lrte_changes:
        race_val = lrte_changes["race"]
        if isinstance(race_val, list):
            results["race"] = save_race(client, session, patient_id, race_val)
        elif isinstance(race_val, str):
            results["race"] = save_race(client, session, patient_id,
                                        [r.strip() for r in race_val.split(",")])

    if not tab1_changed and not tab2_changed and not rp_changes and not lrte_changes:
        results["message"] = "No changes detected"

    if rp_changes:
        gr_id = rp_changes.get("GrId", patient_id)
        gr_rel = rp_changes.get("GrRel", "1")
        is_gr_pt = rp_changes.get("IsGrPt", "1")
        results["responsible_party"] = set_responsible_party(
            client, session, patient_id, gr_id, gr_rel, is_gr_pt)

    return results


def edit_income(client: requests.Session, session: dict,
                patient_id: str, income_data: dict) -> dict:
    """
    Calculate + assign sliding fee schedule.

    Browser ceremony (from HAR):
    1. If existing assignment, expire it (Expired=1)
    2. Calculate new fee from income/dependants/unit
    3. Save new assignment (ItemId=-1, Expired=0)
    """
    income = income_data.get("Income", "0")
    dependants = income_data.get("Dependants", "1")
    unit = income_data.get("Unit", "Monthly")

    results = {}

    # Step 1: Expire existing assignment if present
    current = get_sliding_fee_schedule(client, session, patient_id)
    has_existing = isinstance(current, dict) and current.get("Id")
    if has_existing:
        expire_fields = {**current}
        expire_fields["ItemId"] = current["Id"]
        expire_fields.setdefault("IncomeInfo", {})
        expire_fields.setdefault("MemberInfo", [])
        results["expired"] = save_sliding_fee_schedule(
            client, session, patient_id, expire_fields, expire=True)

    # Step 2: Calculate
    calc = calculate_sliding_fee(client, session, income, dependants, unit)
    results["calculated"] = calc

    # Step 3: Save new assignment
    fields = {**income_data}
    fields["ItemId"] = "-1"
    fields["AssignedType"] = calc.get("Type", "")
    fields["PovertyLevel"] = calc.get("PovertyLevel", "")
    fields["FeeSchId"] = calc.get("FeeSchId", "")
    fields["FeeSchedule"] = calc.get("FeeSchedule", "")
    fields["MedicalDiscount"] = calc.get("MedicalDiscount", "")
    fields["DentalDiscount"] = calc.get("DentalDiscount", "")
    fields["CopayDiscount"] = calc.get("CopayDiscount", "")
    fields["CopayDiscountType"] = calc.get("CopayDiscountType", "0")
    fields["AssignedDate"] = income_data.get("AssignedDate", calc.get("AssignedDate", ""))
    fields["ExpiryDate"] = income_data.get("ExpiryDate", calc.get("ExpiryDate", ""))
    fields.setdefault("IncomeInfo", {})
    fields.setdefault("MemberInfo", [])

    results["assigned"] = save_sliding_fee_schedule(
        client, session, patient_id, fields, expire=False)

    return results


# ── Document Upload ────────────────────────────────────────────────────────────

MAGIC_BYTES = {
    "png": (bytes.fromhex("89504E470D0A1A0A"), 0, 8),
    "jpg": (bytes.fromhex("FFD8FF"), 0, 3),
    "jpeg": (bytes.fromhex("FFD8FF"), 0, 3),
    "gif": (bytes.fromhex("474946"), 0, 3),
    "pdf": (bytes.fromhex("255044462D"), 0, 5),
    "bmp": (bytes.fromhex("424D"), 0, 2),
    "tif": (bytes.fromhex("49492A00"), 0, 4),
    "tiff": (bytes.fromhex("49492A00"), 0, 4),
}


def _validate_file_type(client: requests.Session, session: dict,
                        ext: str, file_bytes: bytes) -> dict:
    """Validate file extension with ECW server and verify magic bytes."""
    # Server-side extension check
    url = _make_url(
        f"/mobiledoc/jsp/filetransfer/fileTransferHandler.jsp"
        f"?action=FileTypeDetails&extension={ext}",
        session)
    r = client.post(url, headers=_get_headers(session))
    r.raise_for_status()
    data = r.json()
    result = data.get("result", [])
    if not result:
        return {"valid": False, "error": f"File type '{ext}' not accepted by ECW"}

    # Client-side magic byte check
    expected = result[0]
    sig = bytes.fromhex(expected.get("FileSignature", ""))
    offset = expected.get("SignatureOffSet", 0)
    num_bytes = expected.get("BytesToRead", len(sig))
    actual = file_bytes[offset:offset + num_bytes]
    if actual != sig[:num_bytes]:
        return {"valid": False,
                "error": f"File content doesn't match {ext.upper()} signature (expected {sig.hex()}, got {actual.hex()})"}

    return {"valid": True}


def upload_insurance_card(client: requests.Session, session: dict,
                          patient_id: str, image_bytes: bytes,
                          filename: str = "insurance_card.png",
                          description: str = "") -> dict:
    import uuid as _uuid
    from datetime import datetime as _dt

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"

    # Validate file type before uploading
    validation = _validate_file_type(client, session, ext, image_bytes)
    if not validation["valid"]:
        return {"status_code": 400, "body": {"error": validation["error"]}}
    custom_name = filename.rsplit(".", 1)[0] if "." in filename else filename
    generated_name = f"{_uuid.uuid4()}_{patient_id}.{ext}"
    now = _dt.now()
    dir_path = f"/mobiledoc/{now.year}/{now.strftime('%m%d%Y')}"
    scanned_date = f"{now.year}-{now.month}-{now.day}"

    # Build metadata XML
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
        f'</Document>'
    )
    form_data_xml = _soap_envelope(doc_xml)

    # Build query params (unencrypted fallback)
    query_params = urllib.parse.urlencode({
        "scan": "no",
        "operation": "upload",
        "filename": generated_name,
        "filepath": dir_path,
        "transformInput": "",
        "moduleName": "patientDocuments",
    })

    content_type_map = {
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "gif": "image/gif", "pdf": "application/pdf", "tif": "image/tiff",
        "tiff": "image/tiff", "bmp": "image/bmp",
    }
    mime = content_type_map.get(ext, "application/octet-stream")

    url = _make_url(f"/mobiledoc/ecwimage?{query_params}", session)
    files = {
        filename: (filename, image_bytes, mime),
    }
    data = {
        "callingForm": "patientDocuments",
        "nact": "2",
        "PatientId": patient_id,
        "FormData": form_data_xml,
        "triggerEventModuleName": "patientDocuments",
    }

    hdrs = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-CSRF-TOKEN": session["csrf_token"],
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/mobiledoc/jsp/webemr/index.jsp",
    }

    r = client.post(url, files=files, data=data, headers=hdrs)
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    ret = parsed.get("return", parsed)
    doc_id = ret.get("documentId", "") if isinstance(ret, dict) else ""
    return {"status_code": r.status_code, "documentId": doc_id,
            "fileName": generated_name}


# ── Parent Info ───────────────────────────────────────────────────────────────

def get_parent_info(client: requests.Session, session: dict,
                    patient_id: str) -> dict:
    url = _make_url(
        "/mobiledoc/jsp/webemr/toppanel/patientInfo/getSetParentInfo.jsp",
        session)
    r = client.post(url, data={"accessParam": "load", "patientId": patient_id},
                    headers=_get_headers(session))
    r.raise_for_status()
    return r.json()


def save_parent_info(client: requests.Session, session: dict,
                     patient_id: str, parent_data: dict) -> dict:
    url = _make_url(
        "/mobiledoc/jsp/webemr/toppanel/patientInfo/getSetParentInfo.jsp",
        session)
    r = client.post(url, data={
        "accessParam": "save",
        "patientId": patient_id,
        "FormData": json.dumps(parent_data),
    }, headers=_get_headers(session))
    r.raise_for_status()
    return {"status_code": r.status_code, "saved": r.text.strip() == "true"}


# ── SOGI ──────────────────────────────────────────────────────────────────────

def get_sogi(client: requests.Session, session: dict,
             patient_id: str) -> dict:
    url = _make_url(
        f"/mobiledoc/jsp/catalog/xml/getSOGIdetails.jsp"
        f"?trigger=getSOGI&patientId={patient_id}",
        session)
    r = client.post(url, headers=_get_headers(session))
    r.raise_for_status()
    data = r.json()
    result = {}
    po = data.get("patient_options", {})
    result["birthsex"] = po.get("birthsex", "")
    result["transgender"] = po.get("transgender", "")
    result["pronouns"] = po.get("pp_details", [])
    result["sexual_orientation"] = po.get("so_details", {})
    result["gender_identity"] = po.get("gi_details", [])
    result["pp_list"] = data.get("pp_list", [])
    result["so_list"] = data.get("so_list", [])
    result["gi_list"] = data.get("gi_list", [])
    return result


def save_sogi(client: requests.Session, session: dict,
              patient_id: str, data: dict) -> dict:
    params = {
        "trigger": "saveSOGI",
        "patientId": patient_id,
        "trUserId": session["tr_user_id"],
        "transgender": data.get("transgender", ""),
        "so_id": data.get("so_id", ""),
        "gi_ids": data.get("gi_ids", ""),
        "pp_ids": data.get("pp_ids", ""),
        "so_reason": data.get("so_reason", ""),
        "gi_reason": data.get("gi_reason", ""),
        "pp_reason": data.get("pp_reason", ""),
        "so_date": data.get("so_date", ""),
        "gi_date": data.get("gi_date", ""),
        "so_changed": str(data.get("so_changed", "true")).lower(),
        "gi_changed": str(data.get("gi_changed", "true")).lower(),
        "pp_changed": str(data.get("pp_changed", "true")).lower(),
        "birthsex": data.get("birthsex", ""),
        "transgender_changed": str(data.get("transgender_changed", "false")).lower(),
        "birthsex_changed": str(data.get("birthsex_changed", "false")).lower(),
        "modality": "WEB",
    }
    query = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    url = _make_url(
        f"/mobiledoc/jsp/catalog/xml/getSOGIdetails.jsp?{query}",
        session)
    r = client.post(url, headers=_get_headers(session))
    r.raise_for_status()
    return {"status_code": r.status_code, "body": r.text[:500]}


# ── Guarantor Search / Info ───────────────────────────────────────────────────

def search_patients(client: requests.Session, session: dict,
                    lastname: str, firstname: str = "") -> list:
    url = _make_url(
        f"/mobiledoc/jsp/catalog/xml/getPatients.jsp"
        f"?SearchBy=Name&lastName={urllib.parse.quote(lastname)}"
        f"&firstName={urllib.parse.quote(firstname)}"
        f"&counter=1&MAXCOUNT=20",
        session)
    r = client.get(url, headers=_get_headers(session))
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    ret = parsed.get("return", parsed)
    if isinstance(ret, dict):
        patients = ret.get("patient", [])
        if isinstance(patients, dict):
            return [patients]
        return patients if isinstance(patients, list) else []
    return []


def search_guarantors(client: requests.Session, session: dict,
                      lastname: str, firstname: str = "") -> list:
    url = _make_url(
        f"/mobiledoc/jsp/uadmin/getGrList.jsp"
        f"?counter=1&option=0&MAXCOUNT=20"
        f"&firstName={urllib.parse.quote(firstname)}"
        f"&lastName={urllib.parse.quote(lastname)}",
        session)
    r = client.get(url, headers=_get_headers(session))
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    ret = parsed.get("return", parsed)
    if isinstance(ret, dict):
        grs = ret.get("Guarantor", [])
        if isinstance(grs, dict):
            return [grs]
        return grs if isinstance(grs, list) else []
    return []


def get_guarantor_info(client: requests.Session, session: dict,
                       gr_id: str) -> dict:
    hdrs = _get_headers(session)
    hdrs["Content-Type"] = "application/json"
    url = _make_url(f"/mobiledoc/emr/guarantor/getGuarantorInfo?grId={gr_id}",
                    session)
    r = client.post(url, headers=hdrs)
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    ret = parsed.get("return", parsed)
    if isinstance(ret, dict) and "patient" in ret:
        return ret["patient"]
    return ret
