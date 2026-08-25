import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://tecnidesk-backend.onrender.com/_test_crash"

req = urllib.request.Request(url, headers={"Origin": "https://www.tecnidesk.lat"})

try:
    with urllib.request.urlopen(req, context=ctx) as f:
        print("Status:", f.status)
        print("Headers:", dict(f.headers))
        print("Body:", f.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print("Headers:", dict(e.headers))
    print("Body:", e.read().decode())
except Exception as e:
    print("Error:", e)
