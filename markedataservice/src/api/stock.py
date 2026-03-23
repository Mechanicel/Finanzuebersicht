import logging
from datetime import date, datetime as dt
from typing import Optional

from flask import Blueprint, jsonify, request

from src.services.stock_service import (
    InstrumentNotFoundError,
    InvalidRequestError,
    PriceNotFoundError,
    StockService,
)

stock_bp = Blueprint("stock", __name__)
service = StockService()
logger = logging.getLogger(__name__)


def _error_response(status_code: int, message: str, code: str):
    return jsonify({"error": {"code": code, "message": message}}), status_code


@stock_bp.route("/stock/<isin>", methods=["GET"])
def get_stock(isin: str):
    """Historischer Modus oder ETF-Modus je nach Query-Parameter."""
    etf = request.args.get("etf")
    if etf:
        model = service.build(isin, etf_key=etf)
        key = etf.lower()
        etf_data = model.etf.get(key)

        if hasattr(etf_data, "to_dict") and callable(etf_data.to_dict):
            payload = etf_data.to_dict().get("entries", [])
        elif isinstance(etf_data, dict):
            payload = etf_data.get("entries", [])
        else:
            payload = getattr(etf_data, "entries", [])

        return jsonify(payload)

    model = service.build(isin)
    return jsonify(model.to_dict())


@stock_bp.route("/price/<isin>", methods=["GET"])
def get_price(isin: str):
    """Liefert den Preis einer ISIN für heute oder ein explizites Datum."""
    date_str = request.args.get("date")
    target_date: Optional[date] = None
    if date_str:
        try:
            target_date = dt.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return _error_response(400, "Invalid date format, expected YYYY-MM-DD", "invalid_date")

    try:
        price = service.get_price(isin, target_date)
        return jsonify({"price": price})
    except InvalidRequestError as exc:
        logger.warning("Ungültige Preisanfrage für ISIN=%s: %s", isin, exc)
        return _error_response(400, str(exc), "invalid_request")
    except (InstrumentNotFoundError, PriceNotFoundError) as exc:
        logger.info("Preis nicht gefunden für ISIN=%s: %s", isin, exc)
        return _error_response(404, str(exc), "not_found")
    except Exception as exc:
        logger.exception("Interner Fehler im /price-Endpoint für ISIN=%s", isin)
        return _error_response(500, f"Internal server error: {exc}", "internal_error")


@stock_bp.route("/company/<isin>", methods=["GET"])
def get_company(isin: str):
    """Gibt den Firmennamen für eine ISIN zurück."""
    try:
        name = service.get_company(isin)
        return jsonify({"company_name": name})
    except InvalidRequestError as exc:
        logger.warning("Ungültige Company-Anfrage für ISIN=%s: %s", isin, exc)
        return _error_response(400, str(exc), "invalid_request")
    except InstrumentNotFoundError as exc:
        logger.info("Firma nicht gefunden für ISIN=%s: %s", isin, exc)
        return _error_response(404, str(exc), "not_found")
    except Exception as exc:
        logger.exception("Interner Fehler im /company-Endpoint für ISIN=%s", isin)
        return _error_response(500, f"Internal server error: {exc}", "internal_error")
