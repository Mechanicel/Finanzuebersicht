from fastapi import FastAPI

app = FastAPI(title="portfolio-service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "portfolio-service"}
