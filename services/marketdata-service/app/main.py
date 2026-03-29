from fastapi import FastAPI

app = FastAPI(title="marketdata-service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "marketdata-service"}
