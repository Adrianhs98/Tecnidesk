import urllib.request
import json
import ssl
import sys

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://tecnidesk-backend.onrender.com/tickets/00000000-0000-0000-0000-000000000000/status"

req = urllib.request.Request(url, 
    method="PATCH",
    headers={"Origin": "https://www.tecnidesk.lat", "Content-Type": "application/json"},
    data=json.dumps({"status": "EN_REPARACION"}).encode("utf-8")
)

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
