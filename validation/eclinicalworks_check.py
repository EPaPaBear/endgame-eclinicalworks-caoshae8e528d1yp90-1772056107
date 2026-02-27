"""
eClinicalWorks validation script.
Contract: check(headers) -> bool
Hits a lightweight authenticated endpoint to verify session is still valid.
"""

import urllib.request


BASE_URL = "https://caoshae8e528d1yp90app.ecwcloud.com"


def check(headers: dict) -> bool:
    url = f"{BASE_URL}/mobiledoc/jsp/webemr/lookup/facilityGroup-lookup.jsp"
    req = urllib.request.Request(url)
    for k, v in headers.items():
        req.add_header(k, v)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    req.add_header("Referer", f"{BASE_URL}/mobiledoc/jsp/webemr/index.jsp")
    req.add_header("isAjaxRequest", "true")
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.status == 200
    except Exception:
        return False
