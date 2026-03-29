from fastapi import FastAPI

app = FastAPI(title="account-service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "account-service"}
