from fastapi import FastAPI

app = FastAPI(title="person-service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "person-service"}
