from fastapi import FastAPI

app = FastAPI(title="api-gateway")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api-gateway"}
