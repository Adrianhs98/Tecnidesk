from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def my_dep():
    raise HTTPException(status_code=403, detail="Forbidden")

@app.patch("/test")
def test_route(d = Depends(my_dep)):
    return {"ok": True}

client = TestClient(app, raise_server_exceptions=False)
r = client.patch("/test", headers={"Origin": "http://localhost"})
print("Status:", r.status_code)
print("Headers:", r.headers)
