from fastapi import FastAPI

app = FastAPI(title="masterdata-service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "masterdata-service"}
