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
      search-facility       - Search facilities by name
      search-resource       - Search scheduling resources
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
      read-advance-directive         - Read patient Advance Directive entries
      list-advance-directive-options - List Advance Directive dictionary
      save-advance-directive         - Append an Advance Directive entry
      create-guarantor      - Create a new guarantor record
      update-guarantor      - Update an existing guarantor record
      delete-guarantor      - Delete a guarantor (fails if linked to insurances)
      search-patient        - Search patients by name and optionally DOB
      search-guarantor      - Search guarantors by name
      search-diagnosis      - Search ICD-10 diagnosis codes (IMO engine)
      search-procedure     - Search CPT/HCPCS procedure codes
      list-referrals        - List incoming/outgoing referrals for a patient
      create-referral       - Create a new incoming/outgoing referral
      delete-referral       - Delete a referral by ID
      get-appointments       - Get last and next appointments
      update-appointment    - Update appointment fields and/or add payment
      list-document-folders - List available document folders
      upload-document       - Upload document to any folder
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
            changes = _flatten_edit_input(changes)
            result = edit_demographics(client, session, patient_id, changes)
            appt_changes = changes.get("appointment")
            if appt_changes and isinstance(appt_changes, dict):
                enc_id = appt_changes.pop("enc_id", "")
                if not enc_id:
                    if isinstance(result, dict):
                        result["appointment_update"] = {"error": "enc_id is required in appointment"}
                else:
                    appt_result = update_appointment(
                        client, session, patient_id, enc_id, appt_changes)
                    if isinstance(result, dict):
                        result["appointment_update"] = appt_result.get("body", {})
            return result

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

        elif action == "search-resource":
            name = input_data.get("name", "")
            max_count = int(input_data.get("max_count", 50))
            return {"resources": search_resources(
                client, session, name=name, max_count=max_count)}

        elif action == "search-diagnosis":
            search = input_data.get("search", "")
            if not search:
                return {"status_code": 400,
                        "body": {"error": "search is required"}}
            search_by = input_data.get("search_by", "code")
            max_count = int(input_data.get("max_count", 10))
            return {"status_code": 200,
                    "body": {"results": search_diagnosis(
                        client, session, search, search_by, max_count)}}

        elif action == "search-procedure":
            search = input_data.get("search", "")
            if not search:
                return {"status_code": 400,
                        "body": {"error": "search is required"}}
            search_by = input_data.get("search_by", "code")
            max_count = int(input_data.get("max_count", 20))
            return {"status_code": 200,
                    "body": {"results": search_procedure(
                        client, session, search, search_by, max_count)}}

        elif action == "list-referrals":
            ref_type = input_data.get("referral_type", "Incoming")
            offset = int(input_data.get("offset", 0))
            rows = int(input_data.get("rows_per_page", 50))
            return list_referrals(client, session, patient_id,
                                  ref_type, offset, rows)

        elif action == "create-referral":
            return create_referral(client, session, patient_id, input_data)

        elif action == "delete-referral":
            ref_id = input_data.get("referral_id", "")
            if not ref_id:
                return {"status_code": 400,
                        "body": {"error": "referral_id is required"}}
            ref_type = input_data.get("referral_type", "Incoming")
            return delete_referral(client, session, ref_id, ref_type)

        elif action == "search-facility":
            return {"facilities": search_facilities(
                client, session,
                name=input_data.get("name", ""),
                facility_type=input_data.get("facility_type", "0"),
                max_count=int(input_data.get("max_count", 50)))}

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
                        "body": {"error": "lrte_type is required (race/language/ethnicity/tribe)"}}
            return save_lrte(client, session, patient_id, lrte_type,
                             entries, decline_to_specify=decline,
                             translator=translator)

        elif action == "read-advance-directive":
            return get_advance_directive(client, session, patient_id)

        elif action == "list-advance-directive-options":
            return {"options": get_advance_directive_dictionary(
                client, session)}

        elif action == "save-advance-directive":
            code = input_data.get("code") or input_data.get("Code") or ""
            name = input_data.get("name") or input_data.get("Name") or ""
            if not (code or name):
                return {"status_code": 400,
                        "body": {"error": "code and/or name is required "
                                          "(use list-advance-directive-options "
                                          "to get valid values)"}}
            return save_advance_directive(
                client, session, patient_id, code, name)

        elif action == "read-structured-data":
            return get_structured_data(client, session, patient_id)

        elif action == "save-structured-data":
            fields = input_data.get("structured_data", {})
            if not fields:
                return {"status_code": 400,
                        "body": {"error": "structured_data dict is required"}}
            return save_structured_data(client, session, patient_id, fields)

        elif action == "list-document-folders":
            return {"folders": list_document_folders(client, session, patient_id)}

        elif action == "upload-document":
            image_b64 = input_data.get("document_base64", "")
            folder = input_data.get("folder", "")
            if not image_b64:
                return {"status_code": 400,
                        "body": {"error": "document_base64 is required"}}
            if not folder:
                return {"status_code": 400,
                        "body": {"error": "folder is required (use list-document-folders to see options)"}}
            import base64 as _b64
            doc_bytes = _b64.b64decode(image_b64)
            fname = input_data.get("filename", "document.pdf")
            desc = input_data.get("description", "")
            reviewed = input_data.get("reviewed", True)
            if isinstance(reviewed, str):
                reviewed = reviewed.lower() not in ("0", "false", "no")
            return upload_document(
                client, session, patient_id, doc_bytes, folder, fname, desc, reviewed)

        elif action == "upload-insurance-card":
            image_b64 = input_data.get("image_base64", input_data.get("document_base64", ""))
            if not image_b64:
                return {"status_code": 400,
                        "body": {"error": "image_base64 is required"}}
            import base64 as _b64
            image_bytes = _b64.b64decode(image_b64)
            fname = input_data.get("filename", "insurance_card.png")
            desc = input_data.get("description", "")
            return upload_document(
                client, session, patient_id, image_bytes, "Insurance", fname, desc)

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

        elif action == "get-appointments":
            return get_appointments(client, session, patient_id)

        elif action == "update-appointment":
            enc_id = input_data.get("enc_id", "")
            if not enc_id:
                return {"status_code": 400,
                        "body": {"error": "enc_id is required (from get-appointments)"}}
            changes = input_data.get("changes", {})
            if not changes:
                return {"status_code": 400,
                        "body": {"error": "changes dict is required"}}
            return update_appointment(client, session, patient_id, enc_id, changes)

        elif action == "create-guarantor":
            guarantor_data = input_data.get("guarantor", {})
            if not guarantor_data:
                return {"status_code": 400,
                        "body": {"error": "guarantor dict is required"}}
            return create_guarantor(client, session, guarantor_data)

        elif action == "update-guarantor":
            gr_id = input_data.get("gr_id", "")
            guarantor_data = input_data.get("guarantor", {})
            if not gr_id or not guarantor_data:
                return {"status_code": 400,
                        "body": {"error": "gr_id and guarantor dict are required"}}
            return update_guarantor(client, session, gr_id, guarantor_data)

        elif action == "delete-guarantor":
            gr_id = input_data.get("gr_id", "")
            if not gr_id:
                return {"status_code": 400,
                        "body": {"error": "gr_id is required"}}
            return delete_guarantor(client, session, gr_id)

        elif action == "search-patient":
            lastname = input_data.get("lastname", "")
            firstname = input_data.get("firstname", "")
            dob = input_data.get("dob", "")
            status_filter = input_data.get("status", "Active")
            max_count = int(input_data.get("max_count", 15))
            if not lastname:
                return {"status_code": 400,
                        "body": {"error": "lastname is required"}}
            return {"patients": search_patients(
                client, session, lastname, firstname, dob, status_filter, max_count)}

        elif action == "search-guarantor":
            search = input_data.get("search", "")
            dob = input_data.get("dob", "")
            status_filter = input_data.get("status", "All")
            max_count = int(input_data.get("max_count", 15))
            if not search:
                return {"status_code": 400,
                        "body": {"error": "search is required (LastName or LastName, FirstName)"}}
            return {"guarantors": search_guarantors(
                client, session, search, dob, status_filter, max_count)}

        else:
            return {"status_code": 400,
                    "body": {"error": f"Unknown action: {action}",
                             "valid_actions": [
                                 "read", "edit-demographics", "read-combos",
                                 "read-sliding-fee", "calculate",
                                 "search-provider", "search-facility",
                                 "search-resource", "get-contacts",
                                 "add-contact", "update-contact",
                                 "set-responsible-party", "edit-income",
                                 "read-sogi", "save-sogi",
                                 "read-lrte", "lrte-lookup", "save-lrte",
                                 "read-parent-info", "save-parent-info",
                                 "read-advance-directive",
                                 "list-advance-directive-options",
                                 "save-advance-directive",
                                 "read-structured-data", "save-structured-data",
                                 "list-document-folders", "upload-document",
                                 "upload-insurance-card", "upload-profile-picture",
                                 "save-communication-notes", "save-communication-settings",
                                 "send-sms",
                                 "create-telephone-encounter",
                                 "get-appointments", "update-appointment",
                                 "create-guarantor", "update-guarantor",
                                 "delete-guarantor", "search-patient",
                                 "search-guarantor",
                                 "search-diagnosis", "search-procedure",
                                 "list-referrals", "create-referral",
                                 "delete-referral",
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


def _parse_soap_list(text: str, item_tag: str) -> list:
    """Parse SOAP XML that contains repeated sibling elements (e.g. <facility>).
    _xml_to_dict collapses these; this function preserves all items."""
    text = text.strip()
    if not text:
        return []
    try:
        cleaned = re.sub(r'<(/?)(?:SOAP-ENV|S|soapenv):', lambda m: f'<{m.group(1)}', text)
        cleaned = re.sub(r'xmlns:[^=]+="[^"]*"', '', cleaned)
        root = ET.fromstring(cleaned)
        items = root.findall(f'.//{item_tag}')
        return [_xml_to_dict(item) for item in items]
    except ET.ParseError:
        return []


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

def _get_patient_info_core(client: requests.Session, session: dict,
                           patient_id: str) -> dict:
    """Raw flat patient record from getPatientInfo.jsp (no nesting, no side enrichments).
    Used internally by edit_demographics to read current field values for merging."""
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
    return parsed if isinstance(parsed, dict) else {}


def get_patient_info(client: requests.Session, session: dict,
                     patient_id: str) -> dict:
    parsed = _get_patient_info_core(client, session, patient_id)
    if not parsed:
        return parsed

    # Enrich with phone list data (cell, home, work with database IDs)
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

    # Enrich with most recent last/next appointment (full detail matching get-appointments)
    try:
        appts = get_appointments(client, session, patient_id)
        parsed["lastAppt"] = appts.get("lastAppt", "")
        parsed["nextAppt"] = appts.get("nextAppt", "")
        last_list = appts.get("lastAppointments", [])
        next_list = appts.get("nextAppointments", [])
        if last_list:
            parsed["lastAppointment"] = last_list[0]
            parsed["lastEncId"] = last_list[0].get("encId", "")
        if next_list:
            parsed["nextAppointment"] = next_list[0]
    except Exception:
        pass

    # Tribe (LRTE) — not returned by getPatientInfo, fetch separately
    try:
        lrte = get_patient_lrte(client, session, patient_id)
        tribe_data = lrte.get("Tribe", {}) if isinstance(lrte, dict) else {}
        selected = tribe_data.get("SelectedTribe", []) if isinstance(tribe_data, dict) else []
        if selected and isinstance(selected, list):
            parsed["tribe"] = ",".join(t.get("name", "") for t in selected if isinstance(t, dict))
        else:
            parsed["tribe"] = ""
    except Exception:
        parsed["tribe"] = ""

    # Enrich with sogi_data, parent_data, income_data, structured_data, contacts, insurance
    try:
        parsed["sogi_data"] = get_sogi_details(client, session, patient_id)
    except Exception:
        parsed["sogi_data"] = {}
    try:
        parsed["parent_data"] = get_parent_info(client, session, patient_id)
    except Exception:
        parsed["parent_data"] = {}
    try:
        parsed["income_data"] = get_sliding_fee_schedule(client, session, patient_id)
    except Exception:
        parsed["income_data"] = {}
    try:
        parsed["structured_data"] = get_structured_data(client, session, patient_id)
    except Exception:
        parsed["structured_data"] = {}
    try:
        parsed["contacts"] = get_contacts(client, session, patient_id)
    except Exception:
        parsed["contacts"] = []
    try:
        parsed["insurance"] = get_insurance_info(client, session, patient_id)
    except Exception:
        parsed["insurance"] = {}
    try:
        parsed["advance_directive"] = get_advance_directive(
            client, session, patient_id)
    except Exception:
        parsed["advance_directive"] = {"AdvDir": [], "AdvDirDiscussionDate": ""}

    return _nest_read(parsed)


_NESTED_SECTIONS = {
    "personal_info", "contact", "address", "demographics",
    "employment", "student", "providers", "responsible_party",
    "consent",
    "other",  # bucket for fields that don't belong to a documented section;
              # flattened on write so round-trips preserve writable values
}
# Read-only read keys that aren't real write fields (drop when flattening).
# Only include fields that are purely display/derived — do NOT drop fields that
# exist on the save payload, or round-trips will wipe them.
_READ_ONLY_KEYS = {
    # Display/derived names
    "namewithsuffix", "EthnicityName", "doctorName", "RefPcpName", "RendName",
    "refHygienistName", "priDentistName",
    "formatedPrefName", "Insurancename", "relation",
    # Enrichment helpers
    "phoneList",
    # Derived codes
    "languageISOCode1", "languageISOCode2", "languageISOName",
    # System-managed metadata
    "regdate", "patientId", "ControlNo", "uname", "UserType",
    "webenabled", "textenabled", "optout", "default_growthchart",
    "empStatusCode", "empStatusDesc",
    # Consent-section read-only (exposed in read but no known save endpoint)
    "ReceivedConsent", "DateConsentSigned",
    # Composite read-only sub-sections — caller writes these via dedicated actions
    "appointments",       # use update-appointment or appointment sub-object
    "contacts",           # use add-contact / update-contact
    "insurance",          # use ecw_sfdp actions
    "structured_data",    # use save-structured-data
    "advance_directive",  # use save-advance-directive or advance_directive sub-object
    # Appointment / admin read-only display fields (kept out of the save merge)
    "lastAppt", "nextAppt", "lastEncId", "lastAppointment", "nextAppointment",
}
# Read-key → write-key remaps (flattener applies these when unwrapping nested
# sections OR when a flat legacy caller passes a read-side key).
_READ_TO_WRITE_KEY = {
    "upreferredname": "PreferredName",
    "upreviousname": "PreviousName",
    "address": "address1",
    "maritalStatus": "maritalstatus",
    "mobile": "mobile",  # already write-form in contact section
    "umobileno": "mobile",
    # Student address: read uses stAddress1/stAddress2, write uses StAddress/StAddress2
    "stAddress1": "StAddress",
    "stAddress2": "StAddress2",
    # Case mismatches between read and write payloads
    "hl7id": "hl7Id",
    "SsnReason": "ssnReason",
    "SsnReasonNotes": "ssnReasonNotes",
}


def _flatten_edit_input(changes: dict) -> dict:
    """Accept either nested (new) or flat (legacy) changes dict.
    Returns a flat dict with write-side keys for edit_demographics().

    Sub-objects (sogi_data, parent_data, income_data, contact (single new),
    appointment) are preserved as-is on the flat output. Nested section
    wrappers (personal_info, address, etc.) are unwrapped."""
    if not isinstance(changes, dict):
        return changes

    out = {}
    for key, value in changes.items():
        if key in _NESTED_SECTIONS and isinstance(value, dict):
            for inner_k, inner_v in value.items():
                if inner_k in _READ_ONLY_KEYS:
                    continue
                mapped = _READ_TO_WRITE_KEY.get(inner_k, inner_k)
                out[mapped] = inner_v
        else:
            # Pass-through: sub-objects (sogi_data/parent_data/income_data/
            # appointment/contact) and any legacy flat fields
            if key in _READ_ONLY_KEYS:
                continue
            mapped = _READ_TO_WRITE_KEY.get(key, key)
            out[mapped] = value
    return out


def _nest_read(flat: dict) -> dict:
    """Reorganize flat read output into category sections matching edit-demographics.
    Read-side field keys are mapped to write-side keys so a caller can round-trip
    the output back into `edit-demographics` → `changes`."""
    def _pluck(keys):
        """Pop keys from flat, return dict with write-side names.
        Keeps read-only display fields (namewithsuffix, doctorName, etc.) under
        their original names so the caller can see them but they're also safe
        to round-trip back via edit-demographics (flattener drops them)."""
        out = {}
        for k in keys:
            if k in flat:
                v = flat.pop(k)
                mapped = _READ_TO_WRITE_KEY.get(k, k)
                out[mapped] = v
        return out

    nested = {"patient_id": flat.get("patientId", "")}

    nested["personal_info"] = _pluck([
        "fname", "lname", "mname", "namewithsuffix", "upreferredname", "upreviousname",
        "prefix", "suffix", "dob", "tob", "sex", "ssn", "status",
        "TransGender", "gestationalAge",
        "BirthOrder", "VFC", "SsnReason", "SsnReasonNotes",
        "deceased", "deceasedDate", "deceasedNotes",
    ])

    nested["contact"] = _pluck([
        "phone", "umobileno", "empPhone", "email", "emailReason",
        "phoneList", "HomeMsgType", "CellMsgType", "WorkMsgType",
        "CellMflag", "empMflag",
    ])
    # Rename umobileno to mobile for parity with write keys
    if "umobileno" in nested["contact"]:
        nested["contact"]["mobile"] = nested["contact"].pop("umobileno")

    nested["address"] = _pluck([
        "address", "address2", "city", "state", "zip", "Country",
        "CountyName", "CountyCode", "MailCountyName", "MailCountyCode",
    ])

    nested["demographics"] = _pluck([
        "maritalStatus", "race", "language", "Ethnicity", "EthnicityName",
        "tribe", "Translator", "mflag",
        "characterestic",  # ECW-spelled "Characteristic" dropdown
        "notes",           # free-text demographics notes
    ])

    nested["consent"] = _pluck([
        "RelInfo",           # Release of Info (Y/N/U)
        "RelInfoDate",       # Signature Date
        "RxConsent",         # Rx History Consent (Y/N/U)
        "Consent",           # General Consent flag
        "ReceivedConsent",   # Consent received flag
        "DateConsentSigned", # Date consent signed
    ])

    nested["employment"] = _pluck([
        "empId", "empName", "empAddress", "empAddress2",
        "empCity", "empState", "empZip", "EmpStatus",
    ])

    nested["student"] = _pluck([
        "StudentStatus", "stAddress1", "stAddress2",
        "stCity", "stState", "stZip", "stCountry", "stCountryCode",
    ])

    nested["providers"] = _pluck([
        "doctorId", "doctorName",
        "refPrId", "RefPcpName",
        "rendPrId", "RendName",
        "refHygienistId", "refHygienistName",
        "primaryDentistId", "priDentistName",
        "MailOrderPharmacyId", "MOMemberId",
        "primaryServiceLocation",  # aka Default Facility
    ])

    nested["responsible_party"] = _pluck(["GrId", "GrRel", "IsGrPt"])

    # Structured / composite sub-sections — keep as-is
    for key in ["sogi_data", "parent_data", "income_data",
                "structured_data", "contacts", "insurance",
                "advance_directive"]:
        if key in flat:
            nested[key] = flat.pop(key)

    # Appointments — group under single section
    appt_section = {}
    for key in ["lastAppt", "nextAppt", "lastEncId",
                "lastAppointment", "nextAppointment"]:
        if key in flat:
            appt_section[key] = flat.pop(key)
    if appt_section:
        nested["appointments"] = appt_section

    # Anything left over (read-only metadata, billing flags, alerts, etc.) → `other`
    if flat:
        nested["other"] = flat

    return nested


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
        ret = parsed["return"]
    else:
        ret = parsed
    # "failed" means no active sliding fee schedule — not an error
    if isinstance(ret, dict) and ret.get("status") == "failed":
        return {"status": "no_sliding_fee_schedule",
                "message": "No active sliding fee schedule assigned to this patient"}
    return ret


def get_insurance_info(client: requests.Session, session: dict,
                       patient_id: str) -> dict:
    """Read patient insurance records + responsible party."""
    url = _make_url(
        f"/mobiledoc/jsp/catalog/xml/getInsuranceInfo.jsp"
        f"?patientId={patient_id}&isPtDemo=true",
        session)
    r = client.post(url, headers=_get_headers(session))
    r.raise_for_status()
    insurances = _parse_soap_list(r.text, "insurance")
    parsed = _parse_soap_xml(r.text)
    rp = {}
    if isinstance(parsed, dict):
        ret = parsed.get("return", parsed)
        if isinstance(ret, dict):
            rp = ret.get("ResponsibleParty", {})
    return {"insurances": insurances, "responsible_party": rp}


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
    return _parse_soap_list(r.text, "Provider")


def search_facilities(client: requests.Session, session: dict,
                      name: str = "", facility_type: str = "0",
                      max_count: int = 50) -> list:
    hdrs = _get_headers(session)
    url = _make_url(
        f"/mobiledoc/jsp/catalog/xml/edi/getFacilityList.jsp"
        f"?counter=0&MAXCOUNT={max_count}&callingForm=&name={urllib.parse.quote(name)}"
        f"&searchby=0&FacilityType={facility_type}",
        session)
    r = client.get(url, headers=hdrs)
    r.raise_for_status()
    return _parse_soap_list(r.text, "facility")


def search_resources(client: requests.Session, session: dict,
                     name: str = "", max_count: int = 500) -> list:
    """Search scheduling resources (providers, rooms, equipment).
    Paginates through all pages since provider-type resources appear on later pages."""
    all_resources = []
    page_size = 200
    for pg in range(1, 10):  # safety cap
        data = {
            "action": "getResourcesWithPagination",
            "page": str(pg),
            "recordsPerPage": str(page_size),
            "isWithId": "false",
        }
        r = _post(client, session,
                  "/mobiledoc/jsp/webemr/scheduling/Controller.jsp", data)
        r.raise_for_status()
        resp = r.json() if r.text.strip() else {}
        batch = resp.get("result", [])
        all_resources.extend(batch)
        if len(batch) < page_size or len(all_resources) >= max_count:
            break

    if name:
        name_lower = name.lower()
        all_resources = [res for res in all_resources
                         if name_lower in res.get("resourceName", "").lower()]
    return all_resources[:max_count]


def get_patient_lrte(client: requests.Session, session: dict,
                     patient_id: str) -> dict:
    r = _post(client, session,
              "/mobiledoc/emr/patient/demographics/lrte/get-patient-lrte",
              {"patientId": patient_id})
    r.raise_for_status()
    return r.json()


def get_lrte_lookup(client: requests.Session, session: dict,
                    lrte_type: str, search: str = "") -> list:
    """Lookup LRTE values. lrte_type: 'race', 'language', 'ethnicity', or 'tribe'."""
    type_to_path = {
        "language": "/mobiledoc/emr/patient/demographics/lrte/get-language-list",
        "race": "/mobiledoc/emr/patient/demographics/lrte/get-race-list",
        "ethnicity": "/mobiledoc/emr/patient/demographics/lrte/get-ethnicity-list",
        "tribe": "/mobiledoc/emr/patient/demographics/lrte/get-tribe-list",
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
        "tribe": "TribeList",
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
    raw = r.json()
    # Extract only the patient's actual values, not the option lists
    opts = raw.get("patient_options", {})
    so = opts.get("so_details", {})
    gi_list = opts.get("gi_details", [])
    pp_list = opts.get("pp_details", [])
    so_list_ref = raw.get("so_list", [])
    return {
        "sexual_orientation": next(
            (o["Name"] for o in so_list_ref if o.get("id") == so.get("id")), ""),
        "sexual_orientation_snomed": so.get("snomed", ""),
        "sexual_orientation_reason": so.get("reason", ""),
        "gender_identity": [{"name": g.get("name", ""),
                             "snomed": g.get("snomed", ""),
                             "reason": g.get("reason", "")} for g in gi_list],
        "pronouns": [p.get("name", "") for p in pp_list],
        "birthsex": opts.get("birthsex", ""),
        "transgender": opts.get("transgender", "N"),
    }


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

    lrte_type: 'race', 'language', 'ethnicity', or 'tribe'
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


# ── Advance Directive ──────────────────────────────────────────────────────

def get_advance_directive_dictionary(client: requests.Session,
                                     session: dict) -> list:
    """List available Advance Directive options (dictionary).

    Returns list of {Id, Code, Name, ...} entries used as codes/descriptions
    when saving.
    """
    url = _make_url(
        "/mobiledoc/emr/patient/advanceDirective/get-advDirective-dictionary-list",
        session)
    r = client.get(url, headers=_get_headers(session))
    r.raise_for_status()
    data = r.json() if r.text.strip() else {}
    if isinstance(data, dict):
        return data.get("result", data.get("advDirDictionary", []))
    if isinstance(data, list):
        return data
    return []


def get_advance_directive(client: requests.Session, session: dict,
                          patient_id: str) -> dict:
    """Read patient's Advance Directive entries.

    Returns {"AdvDir": [...], "AdvDirDiscussionDate": "..."} where each AdvDir
    entry is {Id, Code, Name, MDate, PtId, delflag}.
    """
    url = _make_url(
        f"/mobiledoc/jsp/webemr/rightpanel/getAdvanceDirective.jsp"
        f"?patientId={patient_id}",
        session)
    r = client.get(url, headers=_get_headers(session))
    r.raise_for_status()
    text = r.text.strip()
    if not text:
        return {"AdvDir": [], "AdvDirDiscussionDate": ""}
    try:
        data = json.loads(text)
    except ValueError:
        return {"AdvDir": [], "AdvDirDiscussionDate": "", "_raw": text[:500]}
    if isinstance(data, dict):
        adv = data.get("AdvDir", [])
        if isinstance(adv, dict):
            adv = [adv]
        data["AdvDir"] = adv if isinstance(adv, list) else []
    return data


def save_advance_directive(client: requests.Session, session: dict,
                           patient_id: str, code: str, name: str) -> dict:
    """Append an Advance Directive entry for the patient.

    Uses the same JSP with `hdMode=save`. `code` and `name` come from
    get_advance_directive_dictionary (Code/Name fields).
    """
    url = _make_url(
        f"/mobiledoc/jsp/webemr/rightpanel/getAdvanceDirective.jsp"
        f"?patientId={patient_id}"
        f"&hdCode={urllib.parse.quote(str(code))}"
        f"&hdDesc={urllib.parse.quote(str(name))}"
        f"&hdMode=save",
        session)
    r = client.get(url, headers=_get_headers(session))
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

    current = _get_patient_info_core(client, session, patient_id)
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
    advance_directive_data = changes.pop("advance_directive", None)

    rp_keys = {"GrId", "GrRel", "IsGrPt"}
    rp_changes = {k: changes.pop(k) for k in rp_keys if k in changes}

    current = _get_patient_info_core(client, session, patient_id)
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
        "refHygienistId", "primaryDentistId",
        "MailOrderPharmacyId", "MOMemberId",
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

    lrte_fields = {"race", "language", "Ethnicity", "tribe"}
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

    if advance_directive_data and isinstance(advance_directive_data, dict):
        # Accept two shapes:
        #   1. {"code": "...", "name": "..."} — add a new entry
        #   2. {"add": [{"code":..,"name":..}, ...]} — batch add
        # A raw read echo ({"AdvDir": [...], "AdvDirDiscussionDate": ...}) is
        # ignored as a no-op (no add/name fields present).
        adv_adds = []
        if "add" in advance_directive_data:
            extra = advance_directive_data.get("add") or []
            if isinstance(extra, list):
                adv_adds.extend(extra)
        if ("code" in advance_directive_data
                or "name" in advance_directive_data):
            adv_adds.append(advance_directive_data)
        if adv_adds:
            adv_results = []
            for entry in adv_adds:
                if not isinstance(entry, dict):
                    continue
                code = entry.get("code") or entry.get("Code") or ""
                name = entry.get("name") or entry.get("Name") or ""
                if not (code or name):
                    continue
                adv_results.append(save_advance_directive(
                    client, session, patient_id, code, name))
            results["advance_directive"] = adv_results

    return results


def edit_income(client: requests.Session, session: dict,
                patient_id: str, income_data: dict) -> dict:
    income = income_data.get("Income", "0")
    dependants = income_data.get("Dependants", "1")
    unit = income_data.get("Unit", "Monthly")

    calc = calculate_sliding_fee(client, session, income, dependants, unit)

    # When NonProofOfIncome=1, ECW browser recalculates with Income=0/Dependants=0
    # to get type F (no-proof sliding scale), but preserves the real PovertyLevel.
    if income_data.get("NonProofOfIncome") == "1":
        real_poverty = calc.get("PovertyLevel", "")
        calc = calculate_sliding_fee(client, session, "0", "0", unit)
        calc["PovertyLevel"] = real_poverty

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


# ── Appointments ──────────────────────────────────────────────────────────────

def get_appointments(client: requests.Session, session: dict,
                     patient_id: str) -> dict:
    """Get last and next appointments from Patient Hub."""
    data = {"pid": patient_id, "encounterId": "0"}
    r = _post(client, session,
              "/mobiledoc/jsp/webemr/toppanel/patientHub/fetchPatientHub.jsp", data)
    r.raise_for_status()
    resp = r.json() if r.text.strip() else {}
    pi = resp.get("patientinfo", {})

    last_raw = pi.get("lastAppointments", "[]")
    next_raw = pi.get("nextAppointments", "[]")
    last = json.loads(last_raw) if isinstance(last_raw, str) else last_raw
    nxt = json.loads(next_raw) if isinstance(next_raw, str) else next_raw

    hdrs = _get_headers(session)

    # Fetch sub-type mapping once (vtname -> {subTypeId -> {code, name}})
    subtype_index = {}
    try:
        st_url = _make_url(
            "/mobiledoc/jsp/webemr/uadmin/visitsubtype/subTypeOperationController.jsp"
            "?action=getVisitSubTypesMapping&rowPerpage=0&currentPage=1",
            session)
        st_r = client.get(st_url, headers=hdrs)
        if st_r.status_code == 200:
            st_data = st_r.json() if st_r.text.strip() else {}
            for vt in st_data.get("subTypeMapping", []):
                vtname = vt.get("vtname", "")
                subtype_index[vtname] = {
                    str(st.get("id", "")): {
                        "code": st.get("code", ""),
                        "name": st.get("name", ""),
                    }
                    for st in vt.get("subTypes", [])
                }
    except Exception:
        pass

    def _enrich(appt):
        """Enrich appointment with concurrency check + copay data."""
        enc_id = appt.get("encId", "")
        base = {
            "encId": enc_id,
            "date": appt.get("appDateOnly", ""),
            "dateTime": appt.get("apptDateTime", ""),
            "timeZone": appt.get("apptTimeZone", ""),
            "facility": appt.get("facility", ""),
            "facilityId": appt.get("facilityId", ""),
            "provider": appt.get("providerName", ""),
            "providerId": appt.get("providerId", ""),
            "visitType": appt.get("visitType", ""),
            "reason": appt.get("encReason", ""),
            "encType": appt.get("encType", ""),
            "nonBillable": appt.get("nonBillable", "0"),
            # Defaults — overwritten by enrichment calls
            "status": "",
            "visitSubTypeId": "",
            "visitSubTypeCode": "",
            "visitSubTypeName": "",
            "newPt": False,
            "resourceId": appt.get("providerId", ""),
            "billingNotes": "",
            "generalNotes": "",
            "copay": "0.00",
        }
        if not enc_id:
            return base
        # Visit sub-type + newPt flag — parse encdata XML from newAppointment.jsp
        # Note: encdata is JSON-escaped JS string, so XML close tags appear as `<\/tag>`.
        # Match only up to the first `<` to handle both raw and escaped forms.
        try:
            na_url = _make_url(
                f"/mobiledoc/jsp/webemr/scheduling/newAppointment.jsp"
                f"?encounterId={enc_id}&parentScreen=patientHub",
                session)
            nr = client.get(na_url, headers=hdrs)
            if nr.status_code == 200:
                na_text = nr.text
                # Only match inside the encdata block to avoid picking up the init var
                enc_start = na_text.find("encdata")
                enc_chunk = na_text[enc_start:enc_start + 5000] if enc_start > 0 else ""
                vsti_m = re.search(r'visitSubTypeId>(\d+)<', enc_chunk)
                if vsti_m:
                    base["visitSubTypeId"] = vsti_m.group(1)
                newpt_m = re.search(r'newPt>(\w*)<', enc_chunk)
                if newpt_m:
                    base["newPt"] = newpt_m.group(1) == "1"
        except Exception:
            pass
        # Resolve sub-type code/name from the visit type mapping
        vtname = base.get("visitType", "")
        vsti = base.get("visitSubTypeId", "")
        if vtname and vsti and vtname in subtype_index:
            sub = subtype_index[vtname].get(vsti)
            if sub:
                base["visitSubTypeCode"] = sub["code"]
                base["visitSubTypeName"] = sub["name"]
        # Concurrency check — gives status, resourceId, notes
        try:
            conc_url = _make_url(
                f"/mobiledoc/emr/concurrency/checkApptFieldLevelConcurrency/{enc_id}",
                session)
            cr = client.get(conc_url, headers=hdrs)
            if cr.status_code == 200:
                cd = cr.json()
                base["status"] = cd.get("visitStatusCode", "")
                base["resourceId"] = str(cd.get("resourceId", base["resourceId"]))
                base["billingNotes"] = cd.get("billingNotes", "")
                base["generalNotes"] = cd.get("generalNotes", "")
        except Exception:
            pass
        # CoPay
        try:
            copay_url = _make_url(
                f"/mobiledoc/jsp/catalog/xml/edi/getApptCoPay.jsp"
                f"?patientId={patient_id}&encounterId={enc_id}",
                session)
            cpr = client.get(copay_url, headers=hdrs)
            if cpr.status_code == 200:
                cp_parsed = _parse_soap_xml(cpr.text)
                cp_ret = cp_parsed.get("return", {})
                enc_data = cp_ret.get("Encounter", {}) if isinstance(cp_ret, dict) else {}
                base["copay"] = enc_data.get("Copays", "0.00") if isinstance(enc_data, dict) else "0.00"
        except Exception:
            pass
        return base

    return {
        "lastAppointments": [_enrich(a) for a in (last or [])],
        "nextAppointments": [_enrich(a) for a in (nxt or [])],
        "lastAppt": pi.get("lastAppt", ""),
        "nextAppt": pi.get("nextAppt", ""),
    }


def update_appointment(client: requests.Session, session: dict,
                       patient_id: str, enc_id: str, changes: dict) -> dict:
    """Update an appointment/encounter. Supports visit fields and optional payment.

    changes can include:
      Appointment fields:
        visitType, visitSubTypeId, status, reason, providerId (doctorid),
        resourceId, facilityId, time, endTime, date, notes, infoForProvider,
        billing, billingNotes, generalNotes, cancellationReason
      Payment (nested under 'payment'):
        amount, method (Cash/Credit Card/Check/etc), memo, facilityId
    """
    hdrs = _get_headers(session)

    # Step 1: Get current appointment state via concurrency check
    conc_url = _make_url(
        f"/mobiledoc/emr/concurrency/checkApptFieldLevelConcurrency/{enc_id}",
        session)
    r = client.get(conc_url, headers=hdrs)
    r.raise_for_status()
    current = r.json() if r.text.strip() else {}
    if current.get("status") != "success":
        return {"status_code": 400, "body": {"error": "Failed to read appointment", "detail": current}}

    # Step 2: Build encounter update XML
    from datetime import datetime as _dt
    now = _dt.now()

    provider_id = changes.get("providerId", str(current.get("doctorId", "0")))
    resource_id = changes.get("resourceId", str(current.get("resourceId", provider_id)))
    status_code = changes.get("status", current.get("visitStatusCode", "PEN"))
    visit_type = changes.get("visitType", "MED")
    visit_sub_type_id = changes.get("visitSubTypeId", "0")
    reason = changes.get("reason", "")
    facility_id = changes.get("facilityId", "0")
    pos = changes.get("POS", str(current.get("pos", "50")))
    appt_date = changes.get("date", now.strftime("%Y-%m-%d"))
    appt_time = changes.get("time", "")
    end_time = changes.get("endTime", "")
    notes = changes.get("notes", current.get("generalNotes", ""))
    billing_notes = changes.get("billingNotes", current.get("billingNotes", ""))
    info_for_provider = changes.get("infoForProvider", "")
    cancellation_reason = changes.get("cancellationReason", "")

    enc_xml = (
        f'<encounter xsi:type="xsd:string">'
        f'<id xsi:type="xsd:int">{patient_id}</id>'
        f'<date xsi:type="xsd:string">{appt_date}</date>'
        f'<time xsi:type="xsd:string">{appt_time}</time>'
        f'<endTime xsi:type="xsd:string">{end_time}</endTime>'
        f'<visitType xsi:type="xsd:string">{_escape_xml(visit_type)}</visitType>'
        f'<visitSubTypeId xsi:type="xsd:int">{visit_sub_type_id}</visitSubTypeId>'
        f'<reason xsi:type="xsd:string">{_escape_xml(reason)}</reason>'
        f'<doctorid xsi:type="xsd:int">{provider_id}</doctorid>'
        f'<status xsi:type="xsd:string">{_escape_xml(status_code)}</status>'
        f'<billing xsi:type="xsd:string">{_escape_xml(billing_notes)}</billing>'
        f'<encType xsi:type="xsd:string">1</encType>'
        f'<notes xsi:type="xsd:string">{_escape_xml(notes)}</notes>'
        f'<infoForProvider xsi:type="xsd:string">{_escape_xml(info_for_provider)}</infoForProvider>'
        f'<visitSubType xsi:type="xsd:string"></visitSubType>'
        f'<facilityId xsi:type="xsd:int">{facility_id}</facilityId>'
        f'<POS xsi:type="xsd:int">{pos}</POS>'
        f'<arrTime xsi:type="xsd:string">00:00:00</arrTime>'
        f'<depTime xsi:type="xsd:string">00:00:00</depTime>'
        f'<ptFlag xsi:type="xsd:string">0</ptFlag>'
        f'<Dx xsi:type="xsd:string"></Dx>'
        f'<visitTypeOverriden xsi:type="xsd:string"></visitTypeOverriden>'
        f'<refPrName xsi:type="xsd:string"></refPrName>'
        f'<refPrId xsi:type="xsd:string">0</refPrId>'
        f'<DeptId xsi:type="xsd:int">0</DeptId>'
        f'<UserInfo xsi:type="xsd:string"></UserInfo>'
        f'<resourceId xsi:type="xsd:string">{resource_id}</resourceId>'
        f'<resFacFilterId xsi:type="xsd:int">0</resFacFilterId>'
        f'<practiceId xsi:type="xsd:int">0</practiceId>'
        f'<transitionofcare xsi:type="xsd:int">0</transitionofcare>'
        f'<ptEmail xsi:type="xsd:string"></ptEmail>'
        f'<cancellationReason xsi:type="xsd:string">{_escape_xml(cancellation_reason)}</cancellationReason>'
        f'<userId xsi:type="xsd:string">{session["tr_user_id"]}</userId>'
        f'<webEnabled xsi:type="xsd:string">false</webEnabled>'
        f'<hasBookConflict xsi:type="xsd:string">false</hasBookConflict>'
        f'<hasOverbookAppt xsi:type="xsd:string">false</hasOverbookAppt>'
        f'<stsAfterArr xsi:type="xsd:string"></stsAfterArr>'
        f'<stsCheckInCheckOutTime xsi:type="xsd:string"></stsCheckInCheckOutTime>'
        f'<stsCheckInCheckOutTimeInUTC xsi:type="xsd:string"></stsCheckInCheckOutTimeInUTC>'
        f'<currDate xsi:type="xsd:string">{now.strftime("%Y-%m-%d")}</currDate>'
        f'<currTime xsi:type="xsd:string">{now.strftime("%H:%M:%S")}</currTime>'
        f'<webEmr xsi:type="xsd:string">true</webEmr>'
        f'<isResourceScheduleAppt xsi:type="xsd:string">true</isResourceScheduleAppt>'
        f'</encounter>')
    full_xml = _soap_envelope(enc_xml)

    r = _post(client, session,
              f"/mobiledoc/jsp/catalog/xml/updateEncounter.jsp?EncounterId={enc_id}",
              {"FormData": full_xml})
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    ret = parsed.get("return", parsed)
    enc_status = ret.get("status", "") if isinstance(ret, dict) else ""

    result = {"status_code": 200 if enc_status == "success" else 400,
              "body": {"encounter_update": enc_status}}

    # Step 3: Save dental/resource details (browser always does this)
    res_data = json.dumps({
        "encId": str(enc_id),
        "providerTime": "[]", "resourceTime": "[]",
        "chairTime": "[]", "isDental": "0",
    })
    res_hdrs = _get_headers(session)
    res_hdrs["Content-Type"] = "application/json"
    res_url = _make_url(
        "/mobiledoc/dental/dentalApptResourceDetail/saveApptDetails/", session)
    client.post(res_url, headers=res_hdrs, data=res_data)

    # Step 4: Payment (optional)
    payment = changes.get("payment")
    if payment:
        amount = str(payment.get("amount", "0.00"))
        method = payment.get("method", "Cash")
        memo = payment.get("memo", "")
        pmt_facility = payment.get("facilityId", facility_id)
        check_no = payment.get("checkNo", "")
        deposit_date = payment.get("depositDate", "")

        pmt_xml = (
            f'<PaymentData xsi:type="xsd:string">'
            f'<paymentId xsi:type="xsd:string">0</paymentId>'
            f'<payerId xsi:type="xsd:string">{patient_id}</payerId>'
            f'<payerType xsi:type="xsd:string">2</payerType>'
            f'<date xsi:type="xsd:string">{appt_date}</date>'
            f'<depositDate xsi:type="xsd:string">{deposit_date}</depositDate>'
            f'<amount xsi:type="xsd:double">{amount}</amount>'
            f'<type xsi:type="xsd:string">{_escape_xml(method)}</type>'
            f'<checkNo  xsi:type="xsd:string">{_escape_xml(check_no)}</checkNo >'
            f'<checkDate xsi:type="xsd:string">0000-00-00</checkDate>'
            f'<memo xsi:type="xsd:string">{_escape_xml(memo)}</memo>'
            f'<providerId xsi:type="xsd:string">0</providerId>'
            f'<facilityId xsi:type="xsd:string">{pmt_facility}</facilityId>'
            f'<PracticeId xsi:type="xsd:string">0</PracticeId>'
            f'<userId xsi:type="xsd:string">{session["tr_user_id"]}</userId>'
            f'<PaymentCode  xsi:type="xsd:string"></PaymentCode >'
            f'<ePaymentIdVal xsi:type="xsd:string"></ePaymentIdVal>'
            f'<creditType xsi:type="xsd:int">0</creditType>'
            f'<BatchId xsi:type="xsd:int">0</BatchId>'
            f'<PostedById xsi:type="xsd:int">{session["tr_user_id"]}</PostedById>'
            f'<createdFromAppt xsi:type="xsd:int">1</createdFromAppt>'
            f'</PaymentData>')
        pmt_full_xml = _soap_envelope(pmt_xml)
        r = _post(client, session,
                  "/mobiledoc/jsp/catalog/xml/setInsPayment.jsp",
                  {"FormData": pmt_full_xml})
        pmt_parsed = _parse_soap_xml(r.text)
        pmt_ret = pmt_parsed.get("return", pmt_parsed)
        pmt_id = pmt_ret.get("paymentId", "") if isinstance(pmt_ret, dict) else ""
        pmt_status = pmt_ret.get("status", "") if isinstance(pmt_ret, dict) else ""
        result["body"]["payment"] = {"status": pmt_status, "paymentId": pmt_id}

        # Link payment to encounter
        if pmt_id:
            det_xml = (
                f'<UpdatedPmtDetails xsi:type="xsd:string">'
                f'<PmtDetail xsi:type="xsd:string">'
                f'<PmtDetailId  xsi:type="xsd:int">0</PmtDetailId >'
                f'<invoiceId xsi:type="xsd:int">0</invoiceId>'
                f'<encounterId  xsi:type="xsd:int">{enc_id}</encounterId >'
                f'<adjustment xsi:type="xsd:string">0.00</adjustment>'
                f'<allowed xsi:type="xsd:string">0.00</allowed>'
                f'<deduct xsi:type="xsd:string">0.00</deduct>'
                f'<coins xsi:type="xsd:string">0.00</coins>'
                f'<copay xsi:type="xsd:string">0.00</copay>'
                f'<paid  xsi:type="xsd:string">0.00</paid >'
                f'<withheld xsi:type="xsd:string">0.00</withheld>'
                f'<MsgCode xsi:type="xsd:string"></MsgCode>'
                f'</PmtDetail>'
                f'</UpdatedPmtDetails>'
                f'<DeletedPmtDetails xsi:type="xsd:string" />')
            det_full_xml = _soap_envelope(det_xml)
            r = _post(client, session,
                      "/mobiledoc/jsp/catalog/xml/setPaymentDetails.jsp",
                      {"FormData": det_full_xml})
            det_text = (r.text or "").strip()
            if det_text == "null" or not det_text:
                result["body"]["payment_detail"] = "success"
            else:
                det_parsed = _parse_soap_xml(det_text)
                det_ret = det_parsed.get("return", det_parsed)
                result["body"]["payment_detail"] = det_ret.get("status", "success") if isinstance(det_ret, dict) else det_text[:200]

    return result


# ── Diagnosis & Procedure Search ───────────────────────────────────────────────

def search_diagnosis(client: requests.Session, session: dict,
                     search: str, search_by: str = "code",
                     max_count: int = 10) -> list:
    """Search ICD-10 diagnosis codes via IMO SmartICD engine.

    search_by: "code" (ICD-10 code like "I10") or "name" (description like "hypertension")
    Returns list of {dgId, code, icd10, name, snomed_code, snomed_desc}.
    The dgId can be passed directly to create-referral's diagnosis field.
    """
    uid = session.get("tr_user_id", session.get("session_did", ""))
    sb = "code" if search_by.lower().startswith("c") else "name"
    url = _make_url(
        f"/mobiledoc/jsp/catalog/xml/IMO/DoSmartICDSearch.jsp"
        f"?vendorcode=IMO&searchby={sb}&search={urllib.parse.quote(search)}"
        f"&ncounter=1&maxcount={max_count}&useEnhancedPagination=true"
        f"&parentId=0&useicd10=1&encounterId=0&frm=asmt&userId={uid}",
        session)
    r = client.post(url, headers=_get_headers(session))
    r.raise_for_status()
    # Parse <icd> elements (non-standard XML, not <row>)
    results = []
    try:
        import xml.etree.ElementTree as _ET
        root = _ET.fromstring(r.text)
        for icd in root.iter("icd"):
            item_id = icd.findtext("itemId", "")
            icd_data = icd.findtext("ICDData", "")
            icd10 = icd.findtext("ICD10", "")
            name = icd.findtext("name", "")
            snomed = icd.findtext("snowMedCode", "")
            snomed_desc = icd.findtext("snowMedDesc", "")
            # dgId candidate from ICDData blob (parts[0])
            dg_id = ""
            if icd_data:
                parts = icd_data.split("*")
                if parts and parts[0].isdigit():
                    dg_id = parts[0]
            if not icd10:
                continue
            results.append({
                "dgId": dg_id or item_id,
                "code": icd.findtext("code", ""),
                "icd10": icd10,
                "name": name,
                "snomed_code": snomed,
                "snomed_desc": snomed_desc,
            })
    except Exception:
        return [{"warning": "Diagnosis search encountered an error — session may have expired"}]
    return results


def search_procedure(client: requests.Session, session: dict,
                     search: str, search_by: str = "code",
                     max_count: int = 20) -> list:
    """Search CPT/HCPCS procedure codes.

    search_by: "code" (CPT code like "99213") or "name" (description)
    Returns list of {itemId, code, name, keyname, fee}.
    The itemId can be passed to create-referral's procedures field (pipe-delimited).
    """
    sb = "code" if search_by.lower().startswith("c") else "name"
    condition = "Starts With" if sb == "code" else "Contains"
    lookup_xml = (
        '<lookup xsi:type="xsd:string">'
        f'<searchBy xsi:type="xsd:string">{sb}</searchBy>'
        f'<code xsi:type="xsd:string">{search}</code>'
        '<keyName xsi:type="xsd:string">CPTCodes</keyName>'
        '<keyName xsi:type="xsd:string">HCPCS</keyName>'
        f'<counter xsi:type="xsd:string">1</counter>'
        f'<maxcount xsi:type="xsd:string">{max_count}</maxcount>'
        '<bActive xsi:type="xsd:string">Active</bActive>'
        '<ShowInvalid xsi:type="xsd:string">0</ShowInvalid>'
        '<Fee xsi:type="xsd:string"></Fee>'
        '<Amount xsi:type="xsd:string">0.00</Amount>'
        '<FeeSchId xsi:type="xsd:string">0</FeeSchId>'
        '<ValidDate xsi:type="xsd:string"></ValidDate>'
        f'<Condition xsi:type="xsd:string">{condition}</Condition>'
        '</lookup>')
    form_data = _soap_envelope(lookup_xml)
    r = _post(client, session,
              "/mobiledoc/jsp/catalog/xml/edi/LookupCPTCodes.jsp?parentId=0&encId=0",
              {"FormData": form_data})
    r.raise_for_status()
    results = []
    try:
        import xml.etree.ElementTree as _ET
        root = _ET.fromstring(r.text)
        for proc in root.iter("procedure"):
            item_id = proc.findtext("itemId", "")
            code = proc.findtext("code", "")
            name = proc.findtext("name", "")
            keyname = proc.findtext("keyname", "")
            fee = proc.findtext("fee", "0.0")
            if not item_id or not code:
                continue
            results.append({
                "itemId": item_id,
                "code": code,
                "name": name,
                "keyname": keyname,
                "fee": fee,
            })
    except Exception:
        return [{"warning": "Procedure search encountered an error — session may have expired"}]
    return results


# ── Referrals ──────────────────────────────────────────────────────────────────

def list_referrals(client: requests.Session, session: dict,
                   patient_id: str, referral_type: str = "Incoming",
                   offset: int = 0, rows_per_page: int = 50) -> dict:
    ref_code = "I" if referral_type.lower().startswith("i") else "O"
    data = {
        "PatientId": str(patient_id),
        "referralType": ref_code,
        "offset": str(offset),
        "rowsPerPage": str(rows_per_page),
        "isTotalCountRequired": "true",
    }
    r = _post(client, session,
              "/mobiledoc/jsp/catalog/xml/getPtReferrals.jsp", data)
    r.raise_for_status()
    referrals = _parse_soap_list(r.text, "row")
    # Extract total count
    parsed = _parse_soap_xml(r.text)
    count = 0
    try:
        ret = parsed.get("return", {})
        rs = ret.get("resultset", ret)
        d = rs.get("data", rs)
        count = int(d.get("count", len(referrals)))
    except (AttributeError, ValueError, TypeError):
        count = len(referrals)
    # Clean up each referral
    cleaned = []
    for ref in referrals:
        # Build display names from first/last (refFromName may be just ",")
        from_name = ref.get("refFromName", "")
        if not from_name or from_name.strip(",").strip() == "":
            fl = ref.get("refFromLastName", "")
            ff = ref.get("refFromFirstName", "")
            from_name = f"{fl}, {ff}".strip(", ") if fl or ff else ""
        to_name = ref.get("refToName", "")
        if not to_name or to_name.strip(",").strip() == "":
            tl = ref.get("refToLastName", "")
            tf = ref.get("refToFirstName", "")
            to_name = f"{tl}, {tf}".strip(", ") if tl or tf else ""
        cleaned.append({
            "referralId": ref.get("referralId", ""),
            "date": ref.get("date", ""),
            "reason": ref.get("reason", ""),
            "startDate": ref.get("refStDate", ""),
            "endDate": ref.get("refEnddate", ""),
            "visitsAllowed": ref.get("visitsAllowed", ""),
            "visitsUsed": ref.get("visitsUsed", ""),
            "referralFrom": from_name,
            "referralTo": to_name,
            "specialty": ref.get("refToSpeciality", ""),
            "insurance": ref.get("insName", ""),
            "insuranceId": ref.get("insId", ""),
            "status": ref.get("status", ""),
            "referralSubType": ref.get("referralsubType", ""),
            "authNo": ref.get("authNo", ""),
            "cptUnitsAllowed": ref.get("cptunitsallowed", ""),
            "cptUnitsUsed": ref.get("cptunitsused", ""),
        })
    return {
        "status_code": 200,
        "body": {
            "referral_type": referral_type,
            "referrals": cleaned,
            "total_count": count,
            "offset": offset,
        },
    }


def create_referral(client: requests.Session, session: dict,
                    patient_id: str, data: dict) -> dict:
    """Create a new referral (incoming or outgoing).

    Required fields:
        ref_from_id        - Provider ID for Referral From
        ref_to_id          - Provider ID for Referral To
        specialty          - Specialty name (e.g. "Internal Medicine")
        reason             - Referral reason text (pipe-delimited for multiple)
        diagnosis          - Comma-separated diagnosis IDs, or list of
                             {"code": "ICD-10", "name": "desc"} dicts

    Optional fields:
        referral_type      - "Incoming" (default) or "Outgoing"
        ref_from_name      - Display name (auto-resolved if omitted)
        ref_to_name        - Display name (auto-resolved if omitted)
        from_facility_id   - Facility ID for From provider (default 0)
        to_facility_id     - Facility ID for To provider (default 0)
        insurance_id       - Insurance ID (default: patient's current primary)
        auth_type          - Authorization type name (e.g. "PENDING I")
        auth_code          - Authorization code string
        start_date         - YYYY-MM-DD (default: today)
        end_date           - YYYY-MM-DD (default: start + 90 days)
        referral_date      - YYYY-MM-DD (default: today)
        received_date      - YYYY-MM-DD (default: 0000-00-00)
        appt_date          - YYYY-MM-DD (default: 0000-00-00)
        appt_time          - HH:MM:SS A (default: 00:00:00 A)
        visits_allowed     - Number of visits allowed (default "6")
        unit_type          - e.g. "V (VISIT)", "VM (VISIT/MONTH)" (default "V (VISIT)")
        priority           - "0"=Routine, "1"=Urgent, "2"=Stat (default "0")
        status             - "Open", "Pending", etc. (default "Open")
        sub_status_id      - Sub-status numeric ID (default "0")
        pos                - Place of Service code (default "11")
        assigned_to_id     - Staff ID for Assigned To (default "0")
        assigned_to_name   - Staff display name
        case_id            - Open Cases ID (default "0")
        encounter_id       - Link to an encounter (default "0")
        notes              - General notes text
        clinical_notes     - Clinical notes text
        procedures         - Comma-separated procedure IDs
        ref_sub_type       - "Visit" (default) or "Procedure"
    """
    ref_type_str = data.get("referral_type", "Incoming")
    ref_type_code = "I" if ref_type_str.lower().startswith("i") else "O"
    uid = session.get("tr_user_id", session.get("session_did", ""))
    uname = session.get("user_name", "WEDGE,AI")

    # --- Required fields ---
    ref_from_id = str(data.get("ref_from_id", "0"))
    ref_to_id = str(data.get("ref_to_id", "0"))
    specialty_name = data.get("specialty", "")
    reason_text = data.get("reason", "")

    if ref_from_id == "0" or ref_to_id == "0":
        return {"status_code": 400,
                "body": {"error": "ref_from_id and ref_to_id are required"}}
    if not reason_text:
        return {"status_code": 400,
                "body": {"error": "reason is required"}}

    _warnings = []

    # --- Resolve provider names if not provided ---
    ref_from_name = data.get("ref_from_name", "")
    ref_to_name = data.get("ref_to_name", "")
    if not ref_from_name or not ref_to_name:
        for pid, is_from in [(ref_from_id, True), (ref_to_id, False)]:
            if (is_from and ref_from_name) or (not is_from and ref_to_name):
                continue
            try:
                pr = _post(client, session,
                           "/mobiledoc/jsp/catalog/xml/getProviderData.jsp",
                           {"nd": str(int(time.time() * 1000)),
                            "providerId": pid})
                pp = _parse_soap_xml(pr.text)
                ret = pp.get("return", pp) if isinstance(pp, dict) else pp
                prov = ret.get("provider", ret) if isinstance(ret, dict) else ret
                if isinstance(prov, dict):
                    name = f"{prov.get('lastName','')}, {prov.get('firstName','')}"
                    if is_from:
                        ref_from_name = name
                    else:
                        ref_to_name = name
            except Exception:
                label = "ref_from" if is_from else "ref_to"
                _warnings.append(f"Could not resolve provider name for {label}_id={pid}")

    # --- Resolve specialty ID ---
    specialty_id = data.get("specialty_id", "")
    if not specialty_id and specialty_name:
        try:
            sr = _post(client, session,
                       "/mobiledoc/jsp/uadmin/GetSpecialities.jsp", {})
            specs = _parse_soap_list(sr.text, "row")
            for s in specs:
                sname = s.get("Speciality", s.get("speciality", ""))
                if sname and sname.lower() == specialty_name.lower():
                    specialty_id = s.get("Id", s.get("id", "0"))
                    break
            if not specialty_id:
                for s in specs:
                    sname = s.get("Speciality", s.get("speciality", ""))
                    if sname and sname.lower().startswith(specialty_name.lower()):
                        specialty_id = s.get("Id", s.get("id", "0"))
                        break
        except Exception:
            _warnings.append(f"Could not resolve specialty '{specialty_name}'")
    if not specialty_id:
        specialty_id = "0"
        if specialty_name:
            _warnings.append(f"Specialty '{specialty_name}' not found — saved without specialty")

    # --- Resolve insurance ---
    ins_id = data.get("insurance_id", "")
    if not ins_id:
        try:
            ir = client.get(
                _make_url(f"/mobiledoc/jsp/catalog/xml/getCurrentIns.jsp"
                          f"?PatientId={patient_id}&encounterId=0", session),
                headers=_get_headers(session))
            ip = _parse_soap_xml(ir.text)
            ret = ip.get("return", ip) if isinstance(ip, dict) else ip
            rs = ret.get("resultset", ret) if isinstance(ret, dict) else ret
            d = rs.get("data", rs) if isinstance(rs, dict) else rs
            row = d.get("row", d) if isinstance(d, dict) else d
            if isinstance(row, dict):
                ins_id = row.get("insid", "0")
            elif isinstance(row, list) and row:
                ins_id = row[0].get("insid", "0")
        except Exception:
            _warnings.append("Could not resolve patient's current insurance")
    if not ins_id:
        ins_id = "0"

    # --- Resolve facility IDs ---
    def _resolve_fac(provider_id):
        """Get provider's primary service location. Try ProviderType 1, fallback to 5."""
        for ptype in ["1", "5"]:
            try:
                fr = _post(client, session,
                           "/mobiledoc/jsp/uadmin/GetProviderFacId.jsp",
                           {"ProviderId": provider_id, "ProviderType": ptype,
                            "specialtyName": "undefined"})
                fp = _parse_soap_xml(fr.text)
                ret = fp.get("return", fp) if isinstance(fp, dict) else fp
                if isinstance(ret, dict):
                    rs = ret.get("resultset", ret)
                    d = rs.get("data", rs) if isinstance(rs, dict) else rs
                    row = d.get("row", d) if isinstance(d, dict) else d
                    if isinstance(row, dict):
                        fid = row.get("primaryservicelocation",
                                      row.get("FacId", row.get("facId", "")))
                        if fid and str(fid) != "0":
                            return str(fid)
            except Exception:
                pass
        return "0"

    from_fac_id = str(data.get("from_facility_id", "0"))
    to_fac_id = str(data.get("to_facility_id", "0"))
    if from_fac_id == "0":
        from_fac_id = _resolve_fac(ref_from_id)
        if from_fac_id == "0":
            _warnings.append(f"No default facility found for from provider {ref_from_id} — pass from_facility_id explicitly")
    if to_fac_id == "0":
        to_fac_id = _resolve_fac(ref_to_id)
        if to_fac_id == "0":
            _warnings.append(f"No default facility found for to provider {ref_to_id} — pass to_facility_id explicitly")

    # --- Dates ---
    today = time.strftime("%Y-%m-%d")
    start_date = data.get("start_date", today)
    referral_date = data.get("referral_date", today)
    # Default end = start + 90 days
    end_date = data.get("end_date", "")
    if not end_date:
        from datetime import datetime as _dt, timedelta as _td
        try:
            sd = _dt.strptime(start_date, "%Y-%m-%d")
            end_date = (sd + _td(days=90)).strftime("%Y-%m-%d")
        except ValueError:
            end_date = start_date
    received_date = data.get("received_date", "0000-00-00")
    appt_date = data.get("appt_date", "0000-00-00")
    appt_time = data.get("appt_time", "00:00:00 A")

    # --- Optional fields with defaults ---
    visits_allowed = str(data.get("visits_allowed", "6"))
    unit_type = data.get("unit_type", "V (VISIT)")
    priority = str(data.get("priority", "0"))
    status = data.get("status", "open")
    sub_status_id = str(data.get("sub_status_id", "0"))
    pos = str(data.get("pos", "11"))
    assigned_to_id = str(data.get("assigned_to_id", "0"))
    assigned_to_name = data.get("assigned_to_name", "")
    case_id = str(data.get("case_id", "0"))
    encounter_id = str(data.get("encounter_id", "0"))
    notes = data.get("notes", "")
    clinical_notes = data.get("clinical_notes", "")
    auth_type = data.get("auth_type", "")
    auth_code = data.get("auth_code", "")
    ref_sub_type = data.get("ref_sub_type", "Visit")

    # --- Diagnosis: accept IDs string or list of {code, name} ---
    diagnosis_raw = data.get("diagnosis", "")
    diagnosis_ids = ""
    if isinstance(diagnosis_raw, list):
        ids = []
        for d in diagnosis_raw:
            if isinstance(d, dict) and d.get("id"):
                ids.append(str(d["id"]))
            elif isinstance(d, dict) and d.get("code"):
                # Use IMO SmartICD search to resolve ICD code to dgId
                try:
                    dr = _post(client, session,
                               "/mobiledoc/jsp/catalog/xml/IMO/DoSmartICDSearch.jsp"
                               f"?vendorcode=IMO&searchby=code"
                               f"&search={d['code']}&ncounter=1&maxcount=5"
                               f"&useEnhancedPagination=true&parentId=0"
                               f"&useicd10=1&encounterId=0&frm=asmt"
                               f"&userId={uid}",
                               {})
                    dp = _parse_soap_list(dr.text, "row")
                    if dp:
                        ids.append(str(dp[0].get("dgId",
                                       dp[0].get("itemId",
                                       dp[0].get("Id", "")))))
                    else:
                        _warnings.append(f"Diagnosis code '{d['code']}' not found — use search-diagnosis to find valid codes")
                except Exception:
                    _warnings.append(f"Could not look up diagnosis code '{d['code']}'")
        diagnosis_ids = ",".join(ids)
    elif isinstance(diagnosis_raw, str):
        diagnosis_ids = diagnosis_raw

    # --- Procedures: pipe-delimited internal IDs ---
    procedures = data.get("procedures", "")
    if isinstance(procedures, list):
        procedures = "|".join(str(p) for p in procedures)

    # --- Build SOAP XML ---
    def _cdata(v):
        return f"<![CDATA[{v}]]>"

    def _el(tag, val, xtype="xsd:string"):
        return f'<{tag} xsi:type="{xtype}">{val}</{tag}>'

    xml_fields = "".join([
        _el("patientId", patient_id, "xsd:int"),
        _el("insId", ins_id, "xsd:int"),
        _el("refFrom", ref_from_id),
        _el("refFromName", _cdata(ref_from_name)),
        _el("refFromP2pNPI", "0", "xsd:int"),
        _el("authNo", _cdata(auth_code)),
        _el("ReferralNumber", ""),
        _el("date", referral_date),
        _el("reason", _cdata(reason_text)),
        _el("diagnosis", diagnosis_ids),
        _el("Procedures", procedures),
        _el("EmCodes", ""),
        _el("subStatus", sub_status_id, "xsd:int"),
        _el("refStDate", start_date),
        _el("refEndDate", end_date),
        _el("visitsAllowed", visits_allowed),
        _el("cptunitsallowed", str(data.get("cpt_units_allowed", "0"))),
        _el("cptunitsused", str(data.get("cpt_units_used", "0"))),
        _el("refTo", ref_to_id),
        _el("refToName", _cdata(ref_to_name)),
        _el("refToP2pNPI", "0", "xsd:int"),
        _el("fromDirectAddress", ""),
        _el("toDirectAddress", ""),
        _el("nppes", "0"),
        _el("notes", _cdata(notes)),
        _el("referralType", ref_type_code),
        _el("refSubType", ref_sub_type),
        _el("priority", priority),
        _el("assignedToId", assigned_to_id),
        _el("assignedTo", _cdata(assigned_to_name)),
        _el("status", status),
        _el("FromFacId", from_fac_id, "xsd:int"),
        _el("ToFacId", to_fac_id, "xsd:int"),
        _el("AuthType", _cdata(auth_type)),
        _el("FrontOfficeAuth", "0", "xsd:int"),
        _el("extNHXApptBlockId", "0"),
        _el("Attachments", ""),
        _el("extNHXRefTxId", "0"),
        _el("AppointmentDate", appt_date),
        _el("PrevAppointmentDate", "0000-00-00"),
        _el("ApptTime", appt_time),
        _el("ReceivedDate", received_date),
        _el("ClinicalNotes", _cdata(clinical_notes)),
        _el("encounterid", encounter_id, "xsd:int"),
        _el("Speciality", specialty_id, "xsd:int"),
        _el("caseid", case_id),
        _el("UserName", _cdata(uname)),
        _el("UID", uid),
        _el("POS", pos),
        _el("UnitType", unit_type),
        _el("nhxReqId", ""),
        _el("SAStatus", ""),
        _el("ProcedureUnits", ""),
        _el("isHealowAppt", "0"),
        _el("healowApptGUID", "undefined"),
        _el("Attachdefaults", "1"),
        _el("RefSupportingData",
            '{"isHISPTxCapable":false,"isReceiverFTPEnabled":false}'),
        _el("isReferralReopened", "false"),
        _el("referral360id", ""),
        _el("cloneReferralId", "0", "xsd:int"),
    ])

    referral_xml = (
        '<referral xsi:type="xsd:string">'
        + xml_fields
        + '</referral>')
    form_data = _soap_envelope(referral_xml)

    # --- Duplicate check ---
    try:
        dup_resp = client.post(
            _make_url("/mobiledoc/referral/checkDuplicateReferral", session),
            json={
                "patientId": str(patient_id),
                "referralStartDate": start_date,
                "refTo": ref_to_id,
                "toFacId": to_fac_id,
                "specialty": specialty_id,
                "referralType": ref_type_str,
                "trUserId": uid,
            },
            headers={**_get_headers(session),
                     "Content-Type": "application/json"})
        dup_data = dup_resp.json()
        dups = (dup_data.get("responseData", {}) or {}).get(
            "duplicateReferrals", [])
    except Exception:
        dups = []

    # --- Save referral ---
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    save_params = {
        "referralId": "0",
        "referral360id": "",
        "cancelReferral": "",
        "nhxMsgTxId": "0",
        "validateTransitStatus": "false",
        "uploadptdocs": "false",
        "scannedBy": uname,
        "doNotSaveSA": "0",
        "referralType": ref_type_str,
        "timeZone": "Atlantic/Reykjavik",
        "timeZoneName": "GMT",
        "browserTime": now,
        "uid": uid,
        "uName": uname,
        "context": "webemr",
        "FormData": form_data,
    }
    r = _post(client, session,
              "/mobiledoc/jsp/catalog/xml/setReferral.jsp", save_params)
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    ret = parsed.get("return", parsed) if isinstance(parsed, dict) else parsed

    if not isinstance(ret, dict) or ret.get("status") != "success":
        err = ret.get("errormsg", r.text[:200]) if isinstance(ret, dict) else r.text[:200]
        return {"status_code": 400, "body": {"error": err, "raw": str(ret)[:300]}}

    referral_id = ret.get("referralId", "0")

    # --- Save referral visit (links referral to encounter) ---
    if encounter_id and encounter_id != "0":
        visit_note = (f"Referral Auth No:{auth_code} "
                      f"Start date:{start_date.replace('-','/')} "
                      f"End date:{end_date.replace('-','/')}"
                      if auth_code else
                      f"Start date:{start_date} End date:{end_date}")
        visit_xml = (
            '<visit xsi:type="xsd:string">'
            + _el("referralId", referral_id, "xsd:int")
            + _el("encounterId", encounter_id, "xsd:int")
            + _el("notes", visit_note)
            + _el("visitNo", "1")
            + _el("refType", ref_sub_type)
            + _el("invoiceId", "0")
            + _el("unitsUsed", "0")
            + '</visit>')
        visit_form = _soap_envelope(visit_xml)
        try:
            _post(client, session,
                  "/mobiledoc/p2pmodule/referral/visits/referralvisits",
                  {"referralId": referral_id, "referral360id": "",
                   "FormData": visit_form})
        except Exception:
            pass

    result = {
        "status_code": 200,
        "body": {
            "status": "success",
            "referralId": referral_id,
            "referral_type": ref_type_str,
        },
    }
    if dups:
        result["body"]["duplicate_warning"] = [
            {"referralId": d.get("referralId"),
             "status": d.get("referralStatus"),
             "reason": d.get("reason"),
             "startDate": d.get("referralStartDate"),
             "referralTo": d.get("referralTo")}
            for d in dups]
    if _warnings:
        result["body"]["warnings"] = _warnings
    return result


def delete_referral(client: requests.Session, session: dict,
                    referral_id: str, referral_type: str = "Incoming") -> dict:
    log_type = "I" if referral_type.lower().startswith("i") else "O"
    data = {
        "referralId": str(referral_id),
        "recType": "REF",
        "logType": log_type,
        "uid": session.get("tr_user_id", session.get("session_did", "")),
        "uName": session.get("user_name", "WEDGE,AI"),
        "context": "webemr",
    }
    r = _post(client, session,
              "/mobiledoc/jsp/catalog/xml/deleteReferral.jsp", data)
    r.raise_for_status()
    text = r.text.strip()
    if text == "null" or "success" in text.lower():
        return {"status_code": 200, "body": {"status": "success",
                "referralId": referral_id}}
    parsed = _parse_soap_xml(text)
    ret = parsed.get("return", parsed) if isinstance(parsed, dict) else parsed
    return {"status_code": 400, "body": ret}


# ── Patient Search ─────────────────────────────────────────────────────────────

def search_patients(client: requests.Session, session: dict,
                    lastname: str, firstname: str = "",
                    dob: str = "", status: str = "Active",
                    max_count: int = 15) -> list:
    """Search patients by lastname (required), firstname (optional), and optionally DOB."""

    # DOB: accept YYYY-MM-DD or MM/DD/YYYY, send as MM/DD/YYYY
    dob_formatted = ""
    if dob:
        if "-" in dob and len(dob) == 10:
            parts = dob.split("-")
            dob_formatted = f"{parts[1]}/{parts[2]}/{parts[0]}"
        else:
            dob_formatted = dob

    data = {
        "counter": "1",
        "firstName": firstname,
        "lastName": lastname,
        "DOB": "",
        "SSN": "",
        "AccountNo": "",
        "PhoneNo": "",
        "PreviousName": "",
        "PreferredName": "",
        "Email": "",
        "MedicalRecNo": "",
        "StatusSearch": status,
        "enc": "0",
        "limitstart": "0",
        "limitrange": str(max_count),
        "SubscriberNo": "",
        "AddlSearchBy": "DateOfBirth",
        "AddlSearchVal": dob_formatted,
        "MAXCOUNT": str(max_count),
        "column1": "AllPhones",
        "column2": "GrName",
        "column3": "LastAppt",
        "primarySearchValue": lastname,
        "device": "webemr",
        "callFromScreen": "PatientSearch",
        "userType": "",
        "action": "Patient",
        "donorProfileStatus": "2",
        "ptid": "0",
        "srcContext": "JELLY_BEAN_PANEL",
        "SearchBy": "Name",
        "orderBy": "",
    }
    r = _post(client, session, "/mobiledoc/jsp/catalog/xml/getPatients.jsp", data)
    r.raise_for_status()
    return _parse_soap_list(r.text, "patient")


# ── Guarantor CRUD ────────────────────────────────────────────────────────────

def delete_guarantor(client: requests.Session, session: dict,
                     gr_id: str) -> dict:
    """Delete a guarantor. Checks encounter count first. Returns insurance pairs if blocked."""
    hdrs = _get_headers(session)

    # Step 1: Check encounter count
    enc_url = _make_url(
        f"/mobiledoc/jsp/catalog/xml/getEncCount.jsp?patientId={gr_id}", session)
    r = client.get(enc_url, headers=hdrs)
    r.raise_for_status()
    enc_text = r.text.strip()
    # Extract count from SOAP response
    import re as _re
    enc_match = _re.search(r'>(\d+)<', enc_text)
    enc_count = int(enc_match.group(1)) if enc_match else 0
    if enc_count > 0:
        return {"status_code": 400,
                "body": {"error": f"Guarantor has {enc_count} encounters and cannot be deleted"}}

    # Step 2: Delete
    del_url = _make_url(
        f"/mobiledoc/jsp/uadmin/deleteGuarantor.jsp?uid={gr_id}", session)
    r = client.post(del_url, headers=hdrs)
    r.raise_for_status()

    resp_text = (r.text or "").strip()
    if resp_text == "null" or not resp_text:
        return {"status_code": 200, "body": "deleted"}

    # Non-null response = error (e.g. insurance blocking)
    parsed = _parse_soap_xml(resp_text) if resp_text.startswith("<?xml") else {}
    if parsed:
        ret = parsed.get("return", parsed)
        status_msg = ret.get("status", "") if isinstance(ret, dict) else resp_text
    else:
        status_msg = resp_text

    if "cannot be deleted" in status_msg.lower() or "insurance" in status_msg.lower():
        # Look up which patients have this guarantor linked
        linked = _find_patients_by_guarantor(client, session, gr_id)
        result = {"status_code": 409,
                  "body": {"error": status_msg, "gr_id": gr_id}}
        if linked:
            result["body"]["linked_patients"] = linked
        return result

    return {"status_code": 400, "body": {"error": status_msg}}


def _find_patients_by_guarantor(client: requests.Session, session: dict,
                                gr_id: str) -> list:
    """Find patients linked to a guarantor by searching patients via GrName."""
    try:
        # Get guarantor's name
        hdrs = _get_headers(session)
        r = client.get(
            _make_url(f"/mobiledoc/jsp/uadmin/getGrGenData.jsp?uid={gr_id}", session),
            headers=hdrs)
        parsed = _parse_soap_xml(r.text)
        ret = parsed.get("return", parsed)
        # Data is nested: return.resultset.data.row
        row = ret
        if isinstance(ret, dict) and "resultset" in ret:
            row = ret.get("resultset", {}).get("data", {}).get("row", {})
        gr_lname = row.get("ulname", "") if isinstance(row, dict) else ""
        gr_fname = row.get("ufname", "") if isinstance(row, dict) else ""
        if not gr_lname:
            return []
        gr_name = f"{gr_lname}, {gr_fname}".strip(", ") if gr_fname else gr_lname

        # Search patients by guarantor name
        data = {
            "counter": "1", "firstName": "", "lastName": "",
            "DOB": "", "SSN": "", "AccountNo": "", "PhoneNo": "",
            "PreviousName": "", "PreferredName": "", "Email": "",
            "MedicalRecNo": "", "StatusSearch": "All", "enc": "0",
            "limitstart": "0", "limitrange": "50", "SubscriberNo": "",
            "AddlSearchBy": "GrName", "AddlSearchVal": gr_lname,
            "MAXCOUNT": "50", "column1": "AllPhones", "column2": "GrName",
            "column3": "LastAppt", "primarySearchValue": gr_lname,
            "device": "webemr", "callFromScreen": "PatientSearch",
            "userType": "", "action": "Patient", "donorProfileStatus": "2",
            "ptid": "0", "srcContext": "JELLY_BEAN_PANEL",
            "SearchBy": "GrName", "orderBy": "",
        }
        r = _post(client, session, "/mobiledoc/jsp/catalog/xml/getPatients.jsp", data)
        patients = _parse_soap_list(r.text, "patient")
        return [{"patient_id": p.get("id", ""),
                 "name": f"{p.get('lname', '')}, {p.get('fname', '')}",
                 "insurance": p.get("InsuranceName", "")}
                for p in patients]
    except Exception:
        return []


def search_guarantors(client: requests.Session, session: dict,
                      search: str, dob: str = "", status: str = "All",
                      max_count: int = 15) -> list:
    """Search guarantors by name (LastName or LastName, FirstName)."""
    lastname, firstname = "", ""
    if "," in search:
        parts = search.split(",", 1)
        lastname, firstname = parts[0].strip(), parts[1].strip()
    else:
        lastname = search.strip()

    dob_formatted = ""
    if dob:
        if "-" in dob and len(dob) == 10:
            parts = dob.split("-")
            dob_formatted = f"{parts[1]}/{parts[2]}/{parts[0]}"
        else:
            dob_formatted = dob

    data = {
        "counter": "1", "firstName": firstname, "lastName": lastname,
        "DOB": "", "SSN": "", "AccountNo": "", "PhoneNo": "",
        "PreviousName": "", "PreferredName": "", "Email": "",
        "MedicalRecNo": "", "StatusSearch": status, "enc": "",
        "limitstart": "0", "limitrange": str(max_count), "SubscriberNo": "",
        "AddlSearchBy": "DateOfBirth", "AddlSearchVal": dob_formatted,
        "MAXCOUNT": str(max_count),
        "column1": "UserType", "column2": "LastUpdated", "column3": "MailingAddress",
        "primarySearchValue": f"{lastname}, {firstname}".strip(", ") if firstname else lastname,
        "device": "webemr", "callFromScreen": "PatientSearch",
        "userType": "Both", "action": "Guarantor", "donorProfileStatus": "2",
        "ptid": "0", "srcContext": "JELLY_BEAN_PANEL",
        "SearchBy": "Name", "orderBy": "",
    }
    r = _post(client, session, "/mobiledoc/jsp/catalog/xml/getPatients.jsp", data)
    r.raise_for_status()
    return _parse_soap_list(r.text, "patient")


def create_guarantor(client: requests.Session, session: dict,
                     data: dict) -> dict:
    return _save_guarantor(client, session, "0", data)


def update_guarantor(client: requests.Session, session: dict,
                     gr_id: str, data: dict) -> dict:
    return _save_guarantor(client, session, gr_id, data)


def _save_guarantor(client: requests.Session, session: dict,
                    uid: str, data: dict) -> dict:
    # Phase 1: General tab
    gen_elements = []
    gen_elements.append(f'<uid xsi:type="xsd:string">{uid}</uid>')
    gen_elements.append(f'<GrType xsi:type="xsd:string">{data.get("GrType", "1")}</GrType>')
    gen_elements.append(_add_element("ulname", data.get("lname", ""), cdata=True))
    gen_elements.append(_add_element("ufname", data.get("fname", ""), cdata=True))
    gen_elements.append(_add_element("uminitial", data.get("mi", ""), cdata=True))
    gen_elements.append(_add_element("dob", data.get("dob", "")))
    gen_elements.append(_add_element("ssn", data.get("ssn", "")))
    gen_elements.append(_add_element("tel", data.get("cellPhone", "")))
    gen_elements.append(_add_element("homephone", data.get("homePhone", "")))
    gen_elements.append(_add_element("sex", data.get("sex", "").lower()))
    gen_elements.append(_add_element("email", data.get("email", "")))
    gen_elements.append(_add_element("accountNo", data.get("accountNo", "")))

    gen_xml = f'<guarantor xsi:type="xsd:string">{"".join(gen_elements)}</guarantor>'
    full_xml = _soap_envelope(gen_xml)

    r = _post(client, session,
              "/mobiledoc/jsp/uadmin/SaveGrGenData.jsp",
              {"FormData": full_xml, "oldFormData": ""})
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    ret = parsed.get("return", parsed)
    new_uid = ret.get("uid", "") if isinstance(ret, dict) else ""
    status = ret.get("status", "") if isinstance(ret, dict) else ""

    if status != "success" or not new_uid:
        return _soap_result(r)

    results = {"uid": new_uid, "general": "success"}

    # Phase 2: Address + Employment + Other via individual POSTs
    addr = data.get("address", {})
    street = data.get("streetAddress", {})
    emp = data.get("employment", {})
    notes = data.get("notes", "")

    def _addr_xml(a, tag):
        return (f'<{tag}>'
                f'{_add_element("AddressLine1", a.get("address1", ""), cdata=True)}'
                f'{_add_element("AddressLine2", a.get("address2", ""), cdata=True)}'
                f'{_add_element("city", a.get("city", ""), cdata=True)}'
                f'{_add_element("state", a.get("state", ""), cdata=True)}'
                f'{_add_element("zip", a.get("zip", ""), cdata=True)}'
                f'{_add_element("Country", a.get("country", ""), cdata=True)}'
                f'</{tag}>')

    # Address
    addr_xml = _soap_envelope(
        f'<guarantor xsi:type="xsd:string">'
        f'<uid xsi:type="xsd:string">{new_uid}</uid>'
        f'{_addr_xml(addr, "MailingAddress")}'
        f'{_addr_xml(street, "StreetAddress")}'
        f'</guarantor>')
    r = _post(client, session, "/mobiledoc/jsp/uadmin/setGrAddresses.jsp",
              {"FormData": addr_xml})
    results["address"] = "success" if "success" in r.text.lower() else r.text[:200]

    # Employment
    emp_addr = emp.get("address", {})
    emp_xml = _soap_envelope(
        f'<guarantor xsi:type="xsd:string">'
        f'<uid xsi:type="xsd:string">{new_uid}</uid>'
        f'<Employment>'
        f'{_add_element("name", emp.get("name", ""))}'
        f'{_add_element("tel", emp.get("phone", ""), cdata=True)}'
        f'{_add_element("MsgFlag", emp.get("msgFlag", "off"))}'
        f'{_add_element("empId", emp.get("empId", ""))}'
        f'<Address>'
        f'{_add_element("AddressLine1", emp_addr.get("address1", ""), cdata=True)}'
        f'{_add_element("AddressLine2", emp_addr.get("address2", ""), cdata=True)}'
        f'{_add_element("city", emp_addr.get("city", ""), cdata=True)}'
        f'{_add_element("state", emp_addr.get("state", ""), cdata=True)}'
        f'{_add_element("zip", emp_addr.get("zip", ""), cdata=True)}'
        f'{_add_element("workPhone", emp_addr.get("workPhone", ""), cdata=True)}'
        f'{_add_element("workPhoneExt", emp_addr.get("workPhoneExt", ""), cdata=True)}'
        f'{_add_element("Country", emp_addr.get("country", ""))}'
        f'</Address>'
        f'</Employment>'
        f'</guarantor>')
    r = _post(client, session, "/mobiledoc/jsp/uadmin/setGrEmpAddress.jsp",
              {"FormData": emp_xml})
    results["employment"] = "success" if "success" in r.text.lower() else r.text[:200]

    # Other (notes)
    misc_xml = _soap_envelope(
        f'<guarantor xsi:type="xsd:string">'
        f'<uid xsi:type="xsd:string">{new_uid}</uid>'
        f'{_add_element("notes", notes, cdata=True)}'
        f'</guarantor>')
    r = _post(client, session, "/mobiledoc/jsp/uadmin/setGrMiscData.jsp",
              {"FormData": misc_xml})
    results["other"] = "success" if "success" in r.text.lower() else r.text[:200]

    return {"status_code": 200, "body": results}


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


# ── Document Upload ───────────────────────────────────────────────────────────

def list_document_folders(client: requests.Session, session: dict,
                          patient_id: str) -> list:
    """Return the patient document folder tree."""
    data = {
        "requestSource": "patientDocuments",
        "TrUserId": session["tr_user_id"],
        "PatientId": patient_id,
        "itemVal": "true",
        "sortOrder": "desc",
        "sortDateOrder": "desc",
        "templateId": "",
        "tagIds": "",
        "showMigratedOnly": "false",
    }
    r = _post(client, session,
              "/mobiledoc/jsp/webemr/toppanel/patientdocs/getPatientDocs.jsp", data)
    r.raise_for_status()
    raw = r.json() if r.text.strip() else []
    tree = raw[0] if isinstance(raw, list) and len(raw) > 0 and isinstance(raw[0], list) else raw

    def _flatten(node, parent_name=""):
        name = (node.get("customname") or "").strip()
        entry = {"id": node.get("id", ""), "name": name, "catId": node.get("catId", "")}
        if parent_name:
            entry["qualified_name"] = f"{parent_name} > {name}"
            entry["parent"] = parent_name
        results = [entry]
        for child in node.get("children", []):
            results.extend(_flatten(child, parent_name=name))
        return results

    folders = []
    for node in tree:
        folders.extend(_flatten(node))
    return folders


def _resolve_folder(client: requests.Session, session: dict,
                    patient_id: str, folder_name: str) -> dict:
    """Resolve a folder name to its id and catId. Supports 'Parent > Child' syntax."""
    folders = list_document_folders(client, session, patient_id)

    target = folder_name.strip()

    # Exact match on qualified_name first
    if " > " in target:
        for f in folders:
            if f.get("qualified_name", "").lower() == target.lower():
                return f

    # Exact match on name (case-insensitive)
    matches = [f for f in folders if f["name"].lower() == target.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        # Ambiguous — require qualified name
        options = [f.get("qualified_name") or f["name"] + " (root)" for f in matches]
        raise ValueError(
            f"Ambiguous folder '{target}' - matches {len(matches)} folders. "
            f"Use qualified name from the following options: {options}")

    # Partial / substring match as fallback
    partial = [f for f in folders if target.lower() in f["name"].lower()]
    if len(partial) == 1:
        return partial[0]

    raise ValueError(f"Folder '{target}' not found")


def upload_document(client: requests.Session, session: dict,
                    patient_id: str, doc_bytes: bytes, folder: str,
                    filename: str = "document.pdf",
                    description: str = "",
                    reviewed: bool = True) -> dict:
    """Upload a document to any patient docs folder by name."""
    resolved = _resolve_folder(client, session, patient_id, folder)
    catid = resolved["id"]
    return _upload_doc(client, session, patient_id, doc_bytes, catid, filename, description, reviewed)


def _upload_doc(client: requests.Session, session: dict,
                patient_id: str, image_bytes: bytes, catid: str,
                filename: str = "document.pdf",
                description: str = "",
                reviewed: bool = True) -> dict:
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
        f'<catid xsi:type="xsd:string">{catid}</catid>'
        f'<CustomName xsi:type="xsd:string">{_escape_xml(custom_name)}</CustomName>'
        f'<ScannedDate xsi:type="xsd:string">{scanned_date}</ScannedDate>'
        f'<ScannedBy xsi:type="xsd:string"></ScannedBy>'
        f'<Description xsi:type="xsd:string">{_escape_xml(description)}</Description>'
        f'<Review xsi:type="xsd:string">{"1" if reviewed else "0"}</Review>'
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
    # ECW requires JPEG — validates magic bytes against extension.
    # The browser converts all formats to JPEG via canvas.toBlob before upload.
    # Reject non-JPEG input since the Lambda doesn't have Pillow for conversion.
    if image_bytes[:3] != b'\xff\xd8\xff':
        return {"status_code": 400,
                "body": {"error": "Image must be JPEG format. ECW requires JPEG for profile pictures. "
                                  "Convert to JPEG before base64-encoding."}}
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
    if not ok:
        return {"status_code": 400, "body": r.text.strip(), "fileName": filename}

    # Sync patient image (mirrors browser post-upload call)
    sync_url = _make_url(
        "/mobiledoc/emr/schedule/appt-check-in-assistant/sync-patient-image",
        session)
    client.post(sync_url, data={"patientId": str(patient_id)}, headers=_get_headers(session))

    return {"status_code": 200, "body": "success", "fileName": filename}


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

