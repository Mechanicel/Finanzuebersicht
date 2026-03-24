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


def _handle_service_error(exc: Exception, isin: str, endpoint_name: str):
    if isinstance(exc, InvalidRequestError):
        logger.warning("Ungültige Anfrage in %s für ISIN=%s: %s", endpoint_name, isin, exc)
        return _error_response(400, str(exc), "invalid_request")
    if isinstance(exc, (InstrumentNotFoundError, PriceNotFoundError)):
        logger.info("Daten nicht gefunden in %s für ISIN=%s: %s", endpoint_name, isin, exc)
        return _error_response(404, str(exc), "not_found")

    logger.exception("Interner Fehler in %s für ISIN=%s", endpoint_name, isin)
    return _error_response(500, f"Internal server error: {exc}", "internal_error")


@stock_bp.route("/stock/<isin>", methods=["GET"])
def get_stock(isin: str):
    """
    Legacy-Endpoint (beibehalten für bestehende Aufrufer).

    Hinweis: Neue Clients sollten /analysis/company/<isin>/snapshot oder
    /analysis/company/<isin>/full verwenden.
    """
    etf = request.args.get("etf")
    try:
        if etf:
            model = service.build(isin, etf_key=etf)
            key = etf.lower()
            etf_data = model.etf.get(key)

            if hasattr(etf_data, "to_dict") and callable(etf_data.to_dict):
                payload = etf_data.to_dict()
            elif isinstance(etf_data, dict):
                payload = etf_data
            else:
                payload = {"entries": getattr(etf_data, "entries", [])}

            response = {
                "instrument": model.basic if isinstance(model.basic, dict) else {},
                "etf": {key: payload},
                "entries": payload.get("entries", []),
                "meta": {
                    "deprecated": True,
                    "preferred_endpoint": f"/analysis/company/{isin}/full",
                    "coverage": f"etf:{key}",
                },
            }
            return jsonify(response)

        model = service.build(isin)
        response = model.to_dict()
        response.setdefault("meta", {})
        response["meta"].update(
            {
                "deprecated": True,
                "preferred_endpoint": f"/analysis/company/{isin}/full",
                "coverage": "legacy_stock",
            }
        )
        return jsonify(response)
    except Exception as exc:
        return _handle_service_error(exc, isin, "/stock")


@stock_bp.route("/analysis/company/<isin>/snapshot", methods=["GET"])
def get_company_snapshot(isin: str):
    try:
        return jsonify(service.get_analysis_snapshot(isin))
    except Exception as exc:
        return _handle_service_error(exc, isin, "/analysis/company/<isin>/snapshot")


@stock_bp.route("/analysis/company/<isin>/full", methods=["GET"])
def get_company_full(isin: str):
    try:
        return jsonify(service.get_analysis_full(isin))
    except Exception as exc:
        return _handle_service_error(exc, isin, "/analysis/company/<isin>/full")


@stock_bp.route("/volatility", methods=["GET"])
def get_volatility():
    isin = request.args.get("isin", "")
    try:
        return jsonify(service.get_volatility(isin))
    except Exception as exc:
        return _handle_service_error(exc, isin, "/volatility")


@stock_bp.route("/sharpe", methods=["GET"])
def get_sharpe():
    isin = request.args.get("isin", "")
    try:
        return jsonify(service.get_sharpe_ratio(isin))
    except Exception as exc:
        return _handle_service_error(exc, isin, "/sharpe")


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
    except Exception as exc:
        return _handle_service_error(exc, isin, "/price")


@stock_bp.route("/company/<isin>", methods=["GET"])
def get_company(isin: str):
    """Gibt den Firmennamen für eine ISIN zurück."""
    try:
        name = service.get_company(isin)
        return jsonify({"company_name": name})
    except Exception as exc:
        return _handle_service_error(exc, isin, "/company")
