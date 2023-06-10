import hashlib
import requests
import pdf2image
import numpy as np
from pyzbar.pyzbar import decode, ZBarSymbol, Decoded
import re
import json


def spm_slip_url(angka_giliran: str, nokp: str) -> str:
    """derived from the script from https://myresultspm.moe.gov.my/"""

    angka_giliran, nokp = angka_giliran.upper(), nokp.upper()

    # ic format: YYMMDD-PB-###G
    # Source: https://en.wikipedia.org/wiki/Malaysian_identity_card#:~:text=Structure%20of%20the%20National%20Registration%20Identity%20Card%20Number%20(NRIC)
    if len(nokp) == 12:
        place_birth = nokp[6:8]
        last_4_digit = nokp[8:]

        encrypt_str = angka_giliran + place_birth + last_4_digit
        hashed = hashlib.sha1(encrypt_str.encode("utf-8"))

        url = "/result/SPM-2022/" + place_birth + "/" + hashed.hexdigest() + ".pdf"
    else:
        # different ic format
        encrypt_str = angka_giliran + nokp
        hashed = hashlib.sha1(encrypt_str.encode("utf-8"))

        url = "/result/SPM-2022/99/" + hashed.hexdigest() + ".pdf"

    return "https://myresultspm.moe.gov.my" + url


def get_qrs_from_pdf(pdf_bytes: bytes) -> list[Decoded, ...]:
    img = pdf2image.convert_from_bytes(pdf_bytes)[0]

    arr = np.asarray(img)
    return decode(arr, symbols=[ZBarSymbol.QRCODE])


def get_semakan_url_from_pdf(pdf_bytes: bytes):
    """Get the url embedded in the qr code at the bottom of the results slip pdf"""

    qr = get_qrs_from_pdf(pdf_bytes)[0]  # get the first and the only one qr code
    return "https://" + qr.data.decode()


def get_slip_html(semakan_url: str, angka_giliran: str) -> str:
    """Send a POST requests to the qr code url in the results slip.
    Returns html, which contains info about the results slip"""

    data = {
        "__VIEWSTATE": "/wEPDwULLTE3MzcyMTAzODRkZHZIE9/MKCuQm+PFbpMBTPnqpU6c7V0dS+cQ6ac6Q68W",
        "__VIEWSTATEGENERATOR": "4AC78990",
        "__EVENTVALIDATION": "/wEdAAIykBk5lXqClnlg7OvNHCTea8vGXYAkndFA0LOnlZMzdgzz2RLpasWIUmH6cJoAo5edJu5CgYztJQ1vWE22pFPY",
        "ag": angka_giliran
    }
    ret = requests.post(semakan_url, data=data, verify=False)
    ret.raise_for_status()
    return ret.text


def get_student_json_from_html(html: str) -> dict:
    """Get student data as json dict from the results slip html"""

    # get "var rec = {"idx": ..., "ic": ..., ...}" inside <script></script>
    var_str = re.search(r"var rec = ({.+})", html)[1]
    return json.loads(var_str)


def get_student_data(angka_giliran: str, nokp: str) -> dict:
    """Get student and results data in a dict.

    Keys & values reference, all values' type is string.
    {
        "idx": <angka_giliran | str>,
        "ic": <nokp, format ######-##-#### | str>,
        "cdd": <full name based on ic | str>,
        "sch": <school name | str>,
        "exam": <spm year, e.g. 2022 | int-like>,
        "regTyp": < | int-like>,
        "prvExam": < | int-like>,
        "overallRem": <overall remark?>,
        "certNo": <certificate number | int-like>,
        "certStt": <>,
        "certRem": <cert remark, usually denote passing or failing | "LAYAK MENDAPAT SIJIL" & "SIJIL ATAU PERNYATAAN TIDAK DIKELUARKAN" & "LAYAK MENDAPAT PERNYATAAN">,
        "islamRem": <>,
        "gceoRem": <>,
        "lcciRem": <>,
        "sumRem": <summary remarks, ujian lisan bm, cefr english, akaun lcci, and pengecualian acca all goes here | str>,
        "subjCntDesc": <subject counts in malay (all caps), e.g. SEMBILAN | str>,
        "docTyp": <>,
        "subj": [
            {
                "c1": <subject code | int-like>,
                "s1": <subject name | str>,
                "g1": <grade | str>,
                "d1": <grade description | str>,
                "c2": <>,
                "s2": <>,
                "g2": <>,
                "d2": <>
            },
            {
                // example
                "c1": "1103",
                "s1": "BAHASA MELAYU",
                "g1": "B+",
                "d1": "KEPUJIAN TERTINGGI",
                "c2": "",
                "s2": "",
                "g2": "",
                "d2": ""
            }
        ]
    }
    """

    slip_pdf_url = spm_slip_url(angka_giliran, nokp)

    pdf_ret = requests.get(slip_pdf_url, verify=False)
    pdf_ret.raise_for_status()
    semakan_url = get_semakan_url_from_pdf(pdf_ret.content)

    slip_html = get_slip_html(semakan_url, angka_giliran)

    return get_student_json_from_html(slip_html)


if __name__ == "__main__":
    print(json.dumps(get_student_data("angka_giliran", "ic"), indent=4))

