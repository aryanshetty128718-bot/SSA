import urllib.request
import urllib.error
import json

BASE_URL = "http://127.0.0.1:8000/api/v1/products/barcode"

def test_endpoint(barcode, description):
    url = f"{BASE_URL}/{barcode}"
    print(f"\n--- Scenario: {description} ---")
    print(f"Request: GET {url}")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as res:
            status = res.status
            body = json.loads(res.read().decode('utf-8'))
            print(f"Response Status: {status} OK")
            print(f"Product Name:    {body.get('name')}")
            print(f"Barcode:         {body.get('barcode')}")
            print(f"Source:          {body.get('source')}")
            print(f"Data Source:     {body.get('data_source')}")
            return status, body
    except urllib.error.HTTPError as err:
        status = err.code
        body = err.read().decode('utf-8')
        try:
            body_json = json.loads(body)
            detail = body_json.get('detail')
        except Exception:
            detail = body
        print(f"Response Status: {status} {err.reason}")
        print(f"Detail:          {detail}")
        return status, detail
    except Exception as ex:
        print(f"Network Error:   {ex}")
        return None, str(ex)

def main():
    print("=" * 80)
    print("OFFLINE BEHAVIOR & BARCODE VALIDATION LIVE DEMO")
    print("=" * 80)

    # 1. Local Cache Hit (Nutella) -> Expect 200 OK
    test_endpoint("3017620422003", "Local Cache Hit (Nutella - in DB)")

    # 2. Genuinely Invalid Barcode (Bad GS1 Check Digit) -> Expect 422
    # 4006381333932 has invalid check digit (correct is 1)
    test_endpoint("4006381333932", "Genuinely Invalid Barcode Check Digit (4006381333932)")

    # 3. Valid Barcode Format not in DB (8909999999994)
    # Check digit is valid: 8*1 + 9*3 + 0*1 + 9*3 + 9*1 + 9*3 + 9*1 + 9*3 + 9*1 + 9*3 + 9*1 + 9*3 = 206 -> (210-206) = 4
    test_endpoint("8909999999994", "Valid GS1 EAN-13 Check Digit, Unknown to OFF / DB (8909999999994)")

if __name__ == "__main__":
    main()
