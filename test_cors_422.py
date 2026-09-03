from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.patch("/test")
def test_route(body: dict):
    return {"ok": True}

@app.patch("/test_401")
def test_route_401():
    raise HTTPException(status_code=401, detail="Unauthorized")

client = TestClient(app, raise_server_exceptions=False)
print("422 Error:")
r = client.patch("/test", headers={"Origin": "http://localhost"})
print(r.headers)

print("\n401 Error:")
r2 = client.patch("/test_401", headers={"Origin": "http://localhost"})
print(r2.headers)
