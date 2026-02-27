"""
eClinicalWorks SFDP (Sliding Fee Discount Program) Integration (Endgame)
Platform: caoshae8e528d1yp90app.ecwcloud.com

Actions: sliding-history, sliding-detail, other-income-reasons, find-members,
         get-insurance, search-carriers, delete-insurance, save-insurance-detail,
         add-insurance, update-insurance,
         scenario-1, scenario-2, scenario-5, scenario-6, scenario-7

Converted from sfdp_handler.py for Lambda execution:
  - httpx â†’ requests
  - All shared helpers from action_handler.py inlined
  - run(auth_headers, input_data) entry point
  - session_did from auth_headers["X-Session-DID"] or fallback 297477
"""

import hashlib
import json
import re
import time
import urllib.parse
from datetime import datetime, timedelta
from html import escape as html_escape
from xml.etree import ElementTree as ET

import requests

# Prefer runtime-injected BASE_URL from generic executor, fallback to hardcoded
BASE_URL = globals().get("BASE_URL") or "https://caoshae8e528d1yp90app.ecwcloud.com"
DEFAULT_SESSION_DID = "297477"


# â”€â”€ XML Helpers (inlined from action_handler) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


def _parse_soap_rows(text: str, row_tag: str) -> list:
    text = text.strip()
    if not text:
        return []
    cleaned = re.sub(
        r'<(/?)(?:SOAP-ENV|S|soapenv):',
        lambda m: f'<{m.group(1)}',
        text,
    )
    cleaned = re.sub(r'xmlns:[^=]+="[^"]*"', '', cleaned)
    try:
        root = ET.fromstring(cleaned)
    except ET.ParseError:
        return []
    rows = root.findall(f'.//{row_tag}')
    result = []
    for row in rows:
        d = {}
        for child in row:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if len(child) > 0:
                sub = {}
                for sc in child:
                    stag = sc.tag.split("}")[-1] if "}" in sc.tag else sc.tag
                    sub[stag] = (sc.text or "").strip()
                d[tag] = sub
            else:
                d[tag] = (child.text or "").strip()
        result.append(d)
    return result


# â”€â”€ Session (inlined from action_handler) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


# â”€â”€ Shared reads (inlined from action_handler) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


def save_sliding_fee_schedule(client: requests.Session, session: dict,
                              patient_id: str, fields: dict,
                              expire: bool = False) -> dict:
    expired_status = "1" if expire else "0"

    income_info = fields.get("IncomeInfo", {})
    income_elements = []
    income_elements.append(_add_element_raw("IncomeDetailId",
                                            income_info.get("Id", "")))
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
    info_elements.append(_add_element_raw("PatientId",
                                          fields.get("_patient_id", "")))
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


def edit_income(client: requests.Session, session: dict,
                patient_id: str, income_data: dict) -> dict:
    income = income_data.get("Income", "0")
    dependants = income_data.get("Dependants", "1")
    unit = income_data.get("Unit", "Monthly")

    calc = calculate_sliding_fee(client, session, income, dependants, unit)

    fields = {**income_data}
    fields["_patient_id"] = patient_id
    fields["AssignedType"] = calc.get("Type", "")
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
    if isinstance(current, dict) and current.get("status") == "success":
        fields.setdefault("ItemId", current.get("Id", "-1"))
        if "IncomeInfo" not in fields and "IncomeInfo" in current:
            fields["IncomeInfo"] = current["IncomeInfo"]
    else:
        fields.setdefault("ItemId", "-1")

    fields.setdefault("IncomeInfo", {})
    fields.setdefault("MemberInfo", [])

    result = save_sliding_fee_schedule(
        client, session, patient_id, fields, expire=False)
    result["calculated"] = {
        "Type": calc.get("Type", ""),
        "PovertyLevel": calc.get("PovertyLevel", ""),
        "FeeSchId": calc.get("FeeSchId", ""),
    }
    return result


# â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _add_business_days(start_date, days: int):
    if isinstance(start_date, str):
        if re.match(r'\d{4}-\d{2}-\d{2}', start_date):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            start_date = datetime.strptime(start_date, "%m/%d/%Y").date()
    current = start_date
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


def _parse_date(date_str: str) -> datetime:
    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        return datetime.strptime(date_str, "%Y-%m-%d")
    return datetime.strptime(date_str, "%m/%d/%Y")


# â”€â”€ Sliding Fee Read Functions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_sliding_scale_history(client: requests.Session, session: dict,
                              patient_id: str) -> dict:
    url = _make_url(
        f"/mobiledoc/jsp/catalog/xml/edi/getPtSlidingScaleHistory.jsp"
        f"?PtId={patient_id}",
        session)
    r = client.post(url, headers=_get_headers(session))
    r.raise_for_status()
    rows = _parse_soap_rows(r.text, "row")
    parsed = _parse_soap_xml(r.text)
    status = {}
    if isinstance(parsed, dict):
        ret = parsed.get("return", parsed)
        if isinstance(ret, dict):
            status = ret.get("status", {})
    return {"status": status, "rows": rows}


def get_sliding_scale_detail(client: requests.Session, session: dict,
                             assignment_id: str) -> dict:
    url = _make_url(
        f"/mobiledoc/jsp/catalog/xml/edi/getSlidingScaleDetailForPatient.jsp"
        f"?Id={assignment_id}",
        session)
    r = client.post(url, headers=_get_headers(session))
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    if isinstance(parsed, dict) and "return" in parsed:
        return parsed["return"]
    return parsed


def load_other_income_reasons(client: requests.Session, session: dict) -> list:
    url = _make_url(
        "/mobiledoc/jsp/catalog/xml/edi/loadSlidingOtherIncomeReason.jsp",
        session)
    r = client.post(url, headers=_get_headers(session))
    r.raise_for_status()
    rows = _parse_soap_rows(r.text, "row")
    return [row.get("OtherIncomeReason", "") for row in rows]


def find_sliding_members(client: requests.Session, session: dict,
                         patient_id: str) -> list:
    r = _post(client, session,
              "/mobiledoc/jsp/catalog/xml/edi/findSlidingMembers.jsp",
              {"PtId": patient_id})
    r.raise_for_status()
    rows = _parse_soap_rows(r.text, "row")
    if not rows:
        rows = _parse_soap_rows(r.text, "MemberDetailInfo")
    if not rows:
        parsed = _parse_soap_xml(r.text)
        if isinstance(parsed, dict):
            ret = parsed.get("return", parsed)
            if isinstance(ret, dict):
                data = ret.get("data", "")
                if isinstance(data, dict) and data:
                    return [data]
    return rows


# â”€â”€ Insurance Read Functions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_insurance_info(client: requests.Session, session: dict,
                       patient_id: str) -> dict:
    url = _make_url(
        f"/mobiledoc/jsp/catalog/xml/getInsuranceInfo.jsp"
        f"?patientId={patient_id}&isPtDemo=true",
        session)
    r = client.post(url, headers=_get_headers(session))
    r.raise_for_status()
    insurances = _parse_soap_rows(r.text, "insurance")
    parsed = _parse_soap_xml(r.text)
    rp = {}
    if isinstance(parsed, dict):
        ret = parsed.get("return", parsed)
        if isinstance(ret, dict):
            rp = ret.get("ResponsibleParty", {})
    return {"insurances": insurances, "responsible_party": rp}


def search_insurance_carriers(client: requests.Session, session: dict,
                              name: str, ins_type: str = "") -> list:
    params = urllib.parse.urlencode({
        "counter": "",
        "ShowAll": "0",
        "InsType": ins_type,
        "name": name,
        "searchBy": "Name",
        "Inactive": "",
        "MAXCOUNT": "15",
        "SelectedPracticeID": "",
    })
    path = f"/mobiledoc/jsp/uadmin/getInsuranceList.jsp?{params}"
    url = _make_url(path, session)
    r = client.get(url, headers=_get_headers(session))
    r.raise_for_status()
    return _parse_soap_rows(r.text, "insurance")


# â”€â”€ Insurance Write Functions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def delete_insurance(client: requests.Session, session: dict,
                     patient_id: str, pt_ins_id: str,
                     skip_claim_check: bool = False) -> dict:
    results = {}

    url = _make_url(
        f"/mobiledoc/jsp/catalog/xml/edi/checkCaseExistsforInsurance.jsp"
        f"?InsuranceDetailId={pt_ins_id}",
        session)
    r = client.post(url, headers=_get_headers(session))
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    ret = parsed.get("return", parsed) if isinstance(parsed, dict) else parsed
    if isinstance(ret, dict):
        case_man = ret.get("CaseMan", {})
        if isinstance(case_man, dict):
            total = case_man.get("TotalCount", "0")
            if str(total) != "0":
                return {"error": f"Cannot delete: {total} case(s) associated"}
    results["case_check"] = "passed"

    if not skip_claim_check:
        url = _make_url(
            f"/mobiledoc/jsp/catalog/xml/edi/checkClaimExistsForInsurance.jsp"
            f"?InsuranceDetailId={pt_ins_id}&PatientId={patient_id}",
            session)
        r = client.post(url, headers=_get_headers(session))
        r.raise_for_status()
        parsed = _parse_soap_xml(r.text)
        ret = parsed.get("return", parsed) if isinstance(parsed, dict) else parsed
        if isinstance(ret, dict):
            inv_det = ret.get("InvDet", {})
            claim_count = "0"
            if isinstance(inv_det, dict):
                claim_count = inv_det.get("TotalCount", "0")
            if ret.get("status") == "success" and str(claim_count) != "0":
                return {"error": f"Cannot delete: {claim_count} claim(s) associated"}
        results["claim_check"] = "passed"
    else:
        results["claim_check"] = "skipped"

    r = _post(client, session,
              "/mobiledoc/jsp/uadmin/deletePtInsurance.jsp",
              {"PtInsId": pt_ins_id})
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    ret = parsed.get("return", parsed) if isinstance(parsed, dict) else parsed
    status = "success"
    if isinstance(ret, dict):
        status = ret.get("status", "unknown")
    results["delete"] = status

    return results


def save_insurance_detail(client: requests.Session, session: dict,
                          patient_id: str, insurances: list,
                          gr_id: str = None, gr_rel: str = "0",
                          is_gr_pt: str = "1", prim_ins: str = "",
                          record_number: str = "") -> dict:
    gr_id = gr_id or patient_id

    ins_elements = []
    count = len(insurances)
    for i, ins in enumerate(insurances):
        order = count - i
        ins_elements.append(
            f'<insurance>'
            f'{_add_element("id", ins["PtInsId"])}'
            f'{_add_element("order", str(order))}'
            f'</insurance>'
        )
    ins_xml = f'<insurances>{"".join(ins_elements)}</insurances>'

    rp_parts = [
        _add_element("GrId", gr_id),
        _add_element("GrRel", gr_rel),
        _add_element("IsGrPt", is_gr_pt),
    ]
    if record_number:
        rp_parts.append(_add_element("RecordNumber", record_number))
    rp_xml = f'<ResponsibleParty>{"".join(rp_parts)}</ResponsibleParty>'

    prim_xml = _add_element("PrimIns", prim_ins)

    body_xml = f'{ins_xml}{prim_xml}{rp_xml}'
    full_xml = _soap_envelope(body_xml)

    r = _post(client, session,
              f"/mobiledoc/jsp/catalog/xml/setInsDetail.jsp"
              f"?patientId={patient_id}",
              {"FormData": full_xml})
    r.raise_for_status()
    return {"status_code": r.status_code, "body": r.text[:500]}


def _set_pt_insurance(client: requests.Session, session: dict,
                      patient_id: str, insurance_data: dict,
                      pt_ins_id: str = "0") -> dict:
    e = _add_element
    d = insurance_data

    elements = []
    elements.append(f'<Id xsi:type="xsd:int">{pt_ins_id}</Id>')
    elements.append(
        f'<InsuranceId xsi:type="xsd:int">'
        f'{d.get("InsuranceId", "0")}</InsuranceId>')
    elements.append(
        f'<PatientId xsi:type="xsd:int">{patient_id}</PatientId>')
    elements.append(e("SubscriberNo", d.get("SubscriberNo", ""), cdata=True))
    elements.append(e("GroupNo", d.get("GroupNo", ""), cdata=True))
    elements.append(e("CoPay", d.get("CoPay", "")))
    elements.append(e("CopayMethod", d.get("CopayMethod", "")))
    elements.append(e("StartDate", d.get("StartDate", "")))
    elements.append(e("EndDate", d.get("EndDate", "")))
    elements.append(
        f'<GrId xsi:type="xsd:int">'
        f'{d.get("GrId", patient_id)}</GrId>')
    elements.append(
        f'<IsGrPt xsi:type="xsd:int">'
        f'{d.get("IsGrPt", "1")}</IsGrPt>')
    elements.append(e("AssignBenefits", d.get("AssignBenefits", "")))
    elements.append(e("GrRel", d.get("GrRel", "")))
    elements.append(e("PaymentSource", d.get("PaymentSource", "")))
    elements.append(e("InsuranceClass", d.get("InsuranceClass", "")))
    elements.append(e("InsType", d.get("InsType", "")))
    elements.append(e("SubscriberIdentificationQualifier",
                      d.get("SubscriberIdentificationQualifier", "")))
    elements.append(e("SubscriberSecondaryIdentifier",
                      d.get("SubscriberSecondaryIdentifier", ""), cdata=True))
    elements.append(e("SubscriberSecondaryInvRefQualifier",
                      d.get("SubscriberSecondaryInvRefQualifier", "")))
    elements.append(e("SubscriberSecondaryInvRef",
                      d.get("SubscriberSecondaryInvRef", ""), cdata=True))
    elements.append(e("GroupName", d.get("GroupName", ""), cdata=True))
    elements.append(
        f'<SeqNo xsi:type="xsd:int">'
        f'{d.get("SeqNo", "1")}</SeqNo>')
    elements.append(e("SuppInsInd", d.get("SuppInsInd", "")))
    elements.append(e("MedicaidId", d.get("MedicaidId", "")))
    elements.append(e("MedicaidSeqNo", d.get("MedicaidSeqNo", "")))
    elements.append(
        f'<DentalIns xsi:type="xsd:int">'
        f'{d.get("DentalIns", "0")}</DentalIns>')
    elements.append(
        f'<visionIns xsi:type="xsd:int">'
        f'{d.get("visionIns", "0")}</visionIns>')
    elements.append(
        f'<behavioralHealthIns xsi:type="xsd:int">'
        f'{d.get("behavioralHealthIns", "0")}</behavioralHealthIns>')
    elements.append(e("PtSigSource", d.get("PtSigSource", "")))
    elements.append(e("PPOIndex", d.get("PPOIndex", "")))
    elements.append(e("PPOId", d.get("PPOId", ""), cdata=True))
    elements.append(e("PayerClaimOfficeNo",
                      d.get("PayerClaimOfficeNo", ""), cdata=True))
    elements.append(
        f'<KenPAC xsi:type="xsd:int">'
        f'{d.get("KenPAC", "0")}</KenPAC>')
    elements.append(e("InsuredAltLName",
                      d.get("InsuredAltLName", ""), cdata=True))
    elements.append(e("InsuredAltFName",
                      d.get("InsuredAltFName", ""), cdata=True))
    elements.append(e("InsuredAltMiddleInitial",
                      d.get("InsuredAltMiddleInitial", ""), cdata=True))
    elements.append(e("notes", d.get("notes", "")))
    elements.append(e("PatientAltLName",
                      d.get("PatientAltLName", ""), cdata=True))
    elements.append(e("PatientAltFName",
                      d.get("PatientAltFName", ""), cdata=True))
    elements.append(e("PatientAltMiddleInitial",
                      d.get("PatientAltMiddleInitial", ""), cdata=True))
    elements.append(e("MedicaidSubId",
                      d.get("MedicaidSubId", ""), cdata=True))
    if d.get("MedicareSubId"):
        elements.append(e("MedicareSubId", d["MedicareSubId"]))
    elements.append(e("MultipleCoPay", d.get("MultipleCoPay", "0")))
    elements.append(e("PCPCoPay", d.get("PCPCoPay", "")))
    elements.append(e("SpecialityCoPay", d.get("SpecialityCoPay", "")))
    elements.append(e("OtherCoPay", d.get("OtherCoPay", "")))
    elements.append(e("CoInsurance", d.get("CoInsurance", "")))
    elements.append(e("InsuranceImgName", d.get("InsuranceImgName", "")))
    elements.append(e("FtpDirPath", d.get("FtpDirPath", "")))

    body_xml = (f'<PtIns xsi:type="xsd:string">'
                f'{"".join(elements)}</PtIns>')
    full_xml = _soap_envelope(body_xml)

    r = _post(client, session,
              "/mobiledoc/jsp/uadmin/setPtInsurance.jsp",
              {"FormData": full_xml})
    r.raise_for_status()
    parsed = _parse_soap_xml(r.text)
    ret = parsed.get("return", parsed) if isinstance(parsed, dict) else parsed
    result = {"status": "unknown", "pt_ins_id": ""}
    if isinstance(ret, dict):
        result["status"] = ret.get("status", "unknown")
        result["pt_ins_id"] = ret.get("Id", "")
        if ret.get("type"):
            result["error_type"] = ret["type"]
    return result


def add_insurance(client: requests.Session, session: dict,
                  patient_id: str, insurance_data: dict) -> dict:
    return _set_pt_insurance(
        client, session, patient_id, insurance_data, pt_ins_id="0")


def update_insurance(client: requests.Session, session: dict,
                     patient_id: str, pt_ins_id: str,
                     insurance_data: dict) -> dict:
    return _set_pt_insurance(
        client, session, patient_id, insurance_data, pt_ins_id=pt_ins_id)


# â”€â”€ SFDP Scenario Orchestrators â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def scenario_1_poi_on_visit(client: requests.Session, session: dict,
                            patient_id: str, income_data: dict,
                            old_pt_ins_id: str = None,
                            new_ins_data: dict = None) -> dict:
    """Scenario 1: PENDING -> FINAL WITH POI."""
    income_data = dict(income_data)
    results = {}

    income_data["DocProof"] = "1"
    income_data["NonProofOfIncome"] = "0"
    income_data["ItemId"] = "-1"

    assigned = income_data.get("AssignedDate")
    if assigned and not income_data.get("ExpiryDate"):
        dt = _parse_date(assigned)
        expiry = dt.replace(year=dt.year + 1)
        income_data["ExpiryDate"] = expiry.strftime("%Y-%m-%d")

    results["assign"] = edit_income(client, session, patient_id, income_data)

    if old_pt_ins_id:
        results["delete_old_ins"] = delete_insurance(
            client, session, patient_id, old_pt_ins_id)

    if new_ins_data:
        results["add_new_ins"] = add_insurance(
            client, session, patient_id, new_ins_data)

    return results


def scenario_2_no_poi(client: requests.Session, session: dict,
                      patient_id: str, income_data: dict,
                      old_pt_ins_id: str = None,
                      new_ins_data: dict = None) -> dict:
    """Scenario 2: PENDING -> PROVISIONAL."""
    income_data = dict(income_data)
    results = {}

    income_data["DocProof"] = "0"
    income_data["NonProofOfIncome"] = "1"
    income_data["ItemId"] = "-1"
    income_data.setdefault("NoProofReason", "Unknown")

    assigned = income_data.get("AssignedDate")
    if assigned and not income_data.get("ExpiryDate"):
        start = _parse_date(assigned).date()
        expiry = _add_business_days(start, 10)
        income_data["ExpiryDate"] = expiry.strftime("%Y-%m-%d")

    results["assign"] = edit_income(client, session, patient_id, income_data)

    if old_pt_ins_id:
        results["delete_old_ins"] = delete_insurance(
            client, session, patient_id, old_pt_ins_id)

    if new_ins_data:
        results["add_new_ins"] = add_insurance(
            client, session, patient_id, new_ins_data)

    return results


def scenario_5_no_poi_after_10d(client: requests.Session, session: dict,
                                patient_id: str, income_data: dict,
                                old_pt_ins_id: str = None,
                                new_ins_data: dict = None) -> dict:
    """Scenario 5: PROVISIONAL -> FINAL NO POI."""
    income_data = dict(income_data)
    results = {}

    current = get_sliding_fee_schedule(client, session, patient_id)
    if isinstance(current, dict) and current.get("status") == "success":
        expire_fields = dict(current)
        expire_fields["_patient_id"] = patient_id
        expire_fields.setdefault("IncomeInfo", current.get("IncomeInfo", {}))
        expire_fields.setdefault("MemberInfo", [])
        results["expire"] = save_sliding_fee_schedule(
            client, session, patient_id, expire_fields, expire=True)
    else:
        results["expire"] = {"error": "No active sliding fee to expire"}

    income_data["DocProof"] = "0"
    income_data["NonProofOfIncome"] = "1"
    income_data["ItemId"] = "-1"
    income_data.setdefault("NoProofReason", "Unknown")

    results["reassign"] = edit_income(client, session, patient_id, income_data)

    if old_pt_ins_id:
        results["delete_old_ins"] = delete_insurance(
            client, session, patient_id, old_pt_ins_id)

    if new_ins_data:
        results["add_new_ins"] = add_insurance(
            client, session, patient_id, new_ins_data)

    return results


def scenario_6_poi_arrives(client: requests.Session, session: dict,
                           patient_id: str, income_data: dict,
                           old_pt_ins_id: str = None,
                           new_ins_data: dict = None) -> dict:
    """Scenario 6: PROVISIONAL -> FINAL WITH POI."""
    income_data = dict(income_data)
    results = {}

    current = get_sliding_fee_schedule(client, session, patient_id)
    if isinstance(current, dict) and current.get("status") == "success":
        expire_fields = dict(current)
        expire_fields["_patient_id"] = patient_id
        expire_fields.setdefault("IncomeInfo", current.get("IncomeInfo", {}))
        expire_fields.setdefault("MemberInfo", [])
        results["expire"] = save_sliding_fee_schedule(
            client, session, patient_id, expire_fields, expire=True)
    else:
        results["expire"] = {"error": "No active sliding fee to expire"}

    income_data["DocProof"] = "1"
    income_data["NonProofOfIncome"] = "0"
    income_data["ItemId"] = "-1"

    assigned = income_data.get("AssignedDate")
    if assigned and not income_data.get("ExpiryDate"):
        dt = _parse_date(assigned)
        expiry = dt.replace(year=dt.year + 1)
        income_data["ExpiryDate"] = expiry.strftime("%Y-%m-%d")

    results["reassign"] = edit_income(client, session, patient_id, income_data)

    if old_pt_ins_id:
        results["delete_old_ins"] = delete_insurance(
            client, session, patient_id, old_pt_ins_id)

    if new_ins_data:
        results["add_new_ins"] = add_insurance(
            client, session, patient_id, new_ins_data)

    return results


def scenario_7_returns_with_poi(client: requests.Session, session: dict,
                                patient_id: str, income_data: dict,
                                old_pt_ins_id: str = None,
                                new_ins_data: dict = None) -> dict:
    """Scenario 7: FINAL NO POI -> FINAL WITH POI."""
    income_data = dict(income_data)
    results = {}

    current = get_sliding_fee_schedule(client, session, patient_id)
    if isinstance(current, dict) and current.get("status") == "success":
        expire_fields = dict(current)
        expire_fields["_patient_id"] = patient_id
        expire_fields.setdefault("IncomeInfo", current.get("IncomeInfo", {}))
        expire_fields.setdefault("MemberInfo", [])
        results["expire"] = save_sliding_fee_schedule(
            client, session, patient_id, expire_fields, expire=True)
    else:
        results["expire"] = {"error": "No active sliding fee to expire"}

    income_data["DocProof"] = "1"
    income_data["NonProofOfIncome"] = "0"
    income_data["ItemId"] = "-1"

    assigned = income_data.get("AssignedDate")
    if assigned and not income_data.get("ExpiryDate"):
        dt = _parse_date(assigned)
        expiry = dt.replace(year=dt.year + 1)
        income_data["ExpiryDate"] = expiry.strftime("%Y-%m-%d")

    results["reassign"] = edit_income(client, session, patient_id, income_data)

    if old_pt_ins_id:
        results["delete_old_ins"] = delete_insurance(
            client, session, patient_id, old_pt_ins_id)

    if new_ins_data:
        results["add_new_ins"] = add_insurance(
            client, session, patient_id, new_ins_data)

    return results


# â”€â”€ Endgame Entry Point â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def run(auth_headers: dict, input_data: dict = None) -> dict:
    """Endgame integration entry point.

    input_data:
      action (str): One of the supported actions (see below).
      patient_id (str): Required for most actions.
      ... action-specific fields.

    Actions:
      sliding-history       - Read sliding scale history
      sliding-detail        - Read detail for a specific assignment
      other-income-reasons  - Load dropdown options for income reasons
      find-members          - Find household members for sliding fee
      get-insurance         - Read patient insurance info
      search-carriers       - Search insurance carriers by name
      delete-insurance      - Delete a patient insurance record
      save-insurance-detail - Save insurance ordering + responsible party
      add-insurance         - Add an insurance record
      update-insurance      - Update an existing insurance record
      scenario-1            - PENDING -> FINAL WITH POI
      scenario-2            - PENDING -> PROVISIONAL (no POI)
      scenario-5            - PROVISIONAL -> FINAL NO POI (10d expired)
      scenario-6            - PROVISIONAL -> FINAL WITH POI (POI arrives)
      scenario-7            - FINAL NO POI -> FINAL WITH POI (returns with POI)
    """
    input_data = input_data or {}
    action = input_data.get("action")
    patient_id = input_data.get("patient_id")

    if not action:
        return {"status_code": 400, "body": {"error": "action is required"}}

    session = _build_session_from_headers(auth_headers)

    with requests.Session() as client:
        client.cookies.update(session["cookies"])

        # -- Read actions --

        if action == "sliding-history":
            if not patient_id:
                return {"status_code": 400, "body": {"error": "patient_id required"}}
            return get_sliding_scale_history(client, session, patient_id)

        elif action == "sliding-detail":
            assignment_id = input_data.get("assignment_id")
            if not assignment_id:
                return {"status_code": 400,
                        "body": {"error": "assignment_id required"}}
            return get_sliding_scale_detail(client, session, assignment_id)

        elif action == "other-income-reasons":
            return {"reasons": load_other_income_reasons(client, session)}

        elif action == "find-members":
            if not patient_id:
                return {"status_code": 400, "body": {"error": "patient_id required"}}
            return {"members": find_sliding_members(
                client, session, patient_id)}

        elif action == "get-insurance":
            if not patient_id:
                return {"status_code": 400, "body": {"error": "patient_id required"}}
            return get_insurance_info(client, session, patient_id)

        elif action == "search-carriers":
            name = input_data.get("search", "")
            ins_type = input_data.get("ins_type", "")
            if not name:
                return {"status_code": 400, "body": {"error": "search required"}}
            return {"carriers": search_insurance_carriers(
                client, session, name, ins_type)}

        # -- Write actions --

        elif action == "delete-insurance":
            if not patient_id:
                return {"status_code": 400, "body": {"error": "patient_id required"}}
            pt_ins_id = input_data.get("pt_ins_id")
            if not pt_ins_id:
                return {"status_code": 400, "body": {"error": "pt_ins_id required"}}
            skip_claim = input_data.get("skip_claim_check", False)
            return delete_insurance(
                client, session, patient_id, pt_ins_id, skip_claim)

        elif action == "save-insurance-detail":
            if not patient_id:
                return {"status_code": 400, "body": {"error": "patient_id required"}}
            insurances = input_data.get("insurances", [])
            return save_insurance_detail(
                client, session, patient_id, insurances,
                gr_id=input_data.get("gr_id", patient_id),
                gr_rel=input_data.get("gr_rel", "0"),
                is_gr_pt=input_data.get("is_gr_pt", "1"))

        elif action == "add-insurance":
            if not patient_id:
                return {"status_code": 400, "body": {"error": "patient_id required"}}
            insurance_data = input_data.get("insurance_data", {})
            if not insurance_data.get("InsuranceId"):
                return {"status_code": 400,
                        "body": {"error": "insurance_data.InsuranceId required"}}
            return add_insurance(client, session, patient_id, insurance_data)

        elif action == "update-insurance":
            if not patient_id:
                return {"status_code": 400, "body": {"error": "patient_id required"}}
            pt_ins_id = input_data.get("pt_ins_id")
            insurance_data = input_data.get("insurance_data", {})
            if not pt_ins_id:
                return {"status_code": 400, "body": {"error": "pt_ins_id required"}}
            return update_insurance(
                client, session, patient_id, pt_ins_id, insurance_data)

        # -- Scenario orchestrators --

        elif action.startswith("scenario-"):
            if not patient_id:
                return {"status_code": 400, "body": {"error": "patient_id required"}}
            scenario_num = action.split("-", 1)[1]
            income_data = input_data.get("income_data", {})
            old_pt_ins_id = input_data.get("old_pt_ins_id")
            new_ins_data = input_data.get("new_ins_data")

            scenarios = {
                "1": scenario_1_poi_on_visit,
                "2": scenario_2_no_poi,
                "5": scenario_5_no_poi_after_10d,
                "6": scenario_6_poi_arrives,
                "7": scenario_7_returns_with_poi,
            }
            fn = scenarios.get(scenario_num)
            if not fn:
                return {"status_code": 400,
                        "body": {"error": f"Unknown scenario: {scenario_num}",
                                 "valid": ["1", "2", "5", "6", "7"]}}
            return fn(client, session, patient_id,
                      income_data, old_pt_ins_id, new_ins_data)

        else:
            return {"status_code": 400,
                    "body": {"error": f"Unknown action: {action}",
                             "valid_actions": [
                                 "sliding-history", "sliding-detail",
                                 "other-income-reasons", "find-members",
                                 "get-insurance", "search-carriers",
                                 "delete-insurance", "save-insurance-detail",
                                 "add-insurance", "update-insurance",
                                 "scenario-1", "scenario-2", "scenario-5",
                                 "scenario-6", "scenario-7",
                             ]}}
