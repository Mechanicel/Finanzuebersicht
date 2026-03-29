from fastapi import FastAPI

app = FastAPI(title="analytics-service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "analytics-service"}
