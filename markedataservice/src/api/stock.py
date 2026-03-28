import logging
import time
from datetime import date, datetime as dt
from typing import Optional

from flask import Blueprint, jsonify, request
from finanzuebersicht_shared import get_settings

from src.services.stock_service import (
    InstrumentNotFoundError,
    InvalidRequestError,
    PriceNotFoundError,
    StockService,
)

stock_bp = Blueprint("stock", __name__)
service = StockService()
logger = logging.getLogger(__name__)
settings = get_settings()


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


def _log_endpoint_timing(endpoint_name: str, started_at: float):
    if not settings.performance_logging:
        return
    duration_ms = (time.perf_counter() - started_at) * 1000
    logger.info("GET %s took %.0fms", endpoint_name, duration_ms)


def _parse_isins_query_param(raw_isins: str | None) -> list[str]:
    if raw_isins is None:
        raise InvalidRequestError("Missing required query parameter: isins")
    return [token.strip() for token in raw_isins.split(",")]


@stock_bp.route("/stock/<isin>", methods=["GET"])
def get_stock(isin: str):
    etf = request.args.get("etf")
    try:
        if etf:
            model = service.build(isin, etf_key=etf)
            key = etf.lower()
            payload = model.etf.get(key) if isinstance(model.etf.get(key), dict) else {"entries": []}
            return jsonify(
                {
                    "instrument": model.basic if isinstance(model.basic, dict) else {},
                    "etf": {key: payload},
                    "entries": payload.get("entries", []),
                    "meta": {"deprecated": True, "preferred_endpoint": f"/analysis/company/{isin}/full", "coverage": f"etf:{key}"},
                }
            )

        model = service.build(isin)
        response = model.to_dict()
        response.setdefault("meta", {})
        response["meta"].update({"deprecated": True, "preferred_endpoint": f"/analysis/company/{isin}/full", "coverage": "legacy_stock"})
        return jsonify(response)
    except Exception as exc:
        return _handle_service_error(exc, isin, "/stock")


@stock_bp.route("/analysis/company/<isin>/snapshot", methods=["GET"])
def get_company_snapshot(isin: str):
    started_at = time.perf_counter()
    try:
        return jsonify(service.get_analysis_snapshot(isin))
    except Exception as exc:
        return _handle_service_error(exc, isin, "/analysis/company/<isin>/snapshot")
    finally:
        _log_endpoint_timing("/analysis/company/<isin>/snapshot", started_at)


@stock_bp.route("/analysis/company/<isin>/financials", methods=["GET"])
def get_company_financials(isin: str):
    period = (request.args.get("period") or "annual").lower()
    if period not in {"annual", "quarterly"}:
        return _error_response(400, "Invalid period, expected annual|quarterly", "invalid_period")
    try:
        return jsonify(service.get_analysis_financials(isin, period=period))
    except Exception as exc:
        return _handle_service_error(exc, isin, "/analysis/company/<isin>/financials")


@stock_bp.route("/analysis/company/<isin>/fundamentals", methods=["GET"])
def get_company_fundamentals(isin: str):
    try:
        return jsonify(service.get_analysis_fundamentals(isin))
    except Exception as exc:
        return _handle_service_error(exc, isin, "/analysis/company/<isin>/fundamentals")


@stock_bp.route("/analysis/company/<isin>/analysts", methods=["GET"])
def get_company_analysts(isin: str):
    try:
        return jsonify(service.get_analysis_analysts(isin))
    except Exception as exc:
        return _handle_service_error(exc, isin, "/analysis/company/<isin>/analysts")


@stock_bp.route("/analysis/company/<isin>/fund", methods=["GET"])
def get_company_fund(isin: str):
    try:
        return jsonify(service.get_analysis_fund(isin))
    except Exception as exc:
        return _handle_service_error(exc, isin, "/analysis/company/<isin>/fund")


@stock_bp.route("/analysis/company/<isin>/full", methods=["GET"])
def get_company_full(isin: str):
    started_at = time.perf_counter()
    try:
        return jsonify(service.get_analysis_full(isin))
    except Exception as exc:
        return _handle_service_error(exc, isin, "/analysis/company/<isin>/full")
    finally:
        _log_endpoint_timing("/analysis/company/<isin>/full", started_at)


@stock_bp.route("/analysis/company/<isin>/metrics", methods=["GET"])
def get_company_metrics(isin: str):
    started_at = time.perf_counter()
    try:
        return jsonify(service.get_analysis_metrics(isin))
    except Exception as exc:
        return _handle_service_error(exc, isin, "/analysis/company/<isin>/metrics")
    finally:
        _log_endpoint_timing("/analysis/company/<isin>/metrics", started_at)


@stock_bp.route("/analysis/company/<isin>/risk", methods=["GET"])
def get_company_risk(isin: str):
    started_at = time.perf_counter()
    benchmark = request.args.get("benchmark")
    try:
        return jsonify(service.get_analysis_risk(isin, benchmark_key=benchmark))
    except Exception as exc:
        return _handle_service_error(exc, isin, "/analysis/company/<isin>/risk")
    finally:
        _log_endpoint_timing("/analysis/company/<isin>/risk", started_at)


@stock_bp.route("/analysis/company/<isin>/benchmark", methods=["GET"])
def get_company_benchmark(isin: str):
    benchmark = request.args.get("benchmark")
    try:
        return jsonify(service.get_analysis_benchmark(isin, benchmark_key=benchmark))
    except Exception as exc:
        return _handle_service_error(exc, isin, "/analysis/company/<isin>/benchmark")


@stock_bp.route("/analysis/company/<isin>/timeseries", methods=["GET"])
def get_company_timeseries(isin: str):
    started_at = time.perf_counter()
    series = request.args.get("series", "price,returns,drawdown")
    benchmark = request.args.get("benchmark")
    try:
        return jsonify(service.get_analysis_timeseries(isin, series=series, benchmark_key=benchmark))
    except Exception as exc:
        return _handle_service_error(exc, isin, "/analysis/company/<isin>/timeseries")
    finally:
        _log_endpoint_timing("/analysis/company/<isin>/timeseries", started_at)


@stock_bp.route("/analysis/benchmark-catalog", methods=["GET"])
@stock_bp.route("/analysis/benchmarks", methods=["GET"])
def get_benchmark_catalog():
    try:
        return jsonify(service.get_analysis_benchmark_catalog())
    except Exception as exc:
        return _handle_service_error(exc, "", "/analysis/benchmarks")


@stock_bp.route("/analysis/depot/holdings-summary", methods=["GET"])
def get_depot_holdings_summary():
    started_at = time.perf_counter()
    try:
        isins = _parse_isins_query_param(request.args.get("isins"))
        return jsonify(service.get_depot_holdings_summary(isins))
    except Exception as exc:
        return _handle_service_error(exc, "", "/analysis/depot/holdings-summary")
    finally:
        _log_endpoint_timing("/analysis/depot/holdings-summary", started_at)


@stock_bp.route("/analysis/benchmark-search", methods=["GET"])
def benchmark_search():
    query = request.args.get("q", "")
    try:
        return jsonify(service.search_benchmark_candidates(query))
    except Exception as exc:
        return _handle_service_error(exc, "", "/analysis/benchmark-search")


@stock_bp.route("/analysis/company/<isin>/comparison-timeseries", methods=["GET"])
def get_company_comparison_timeseries(isin: str):
    symbols = request.args.get("symbols", "")
    try:
        return jsonify(service.get_analysis_comparison_timeseries(isin, symbols=symbols))
    except Exception as exc:
        return _handle_service_error(exc, isin, "/analysis/company/<isin>/comparison-timeseries")


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
    started_at = time.perf_counter()
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
    finally:
        _log_endpoint_timing("/price/<isin>", started_at)


@stock_bp.route("/company/<isin>", methods=["GET"])
def get_company(isin: str):
    started_at = time.perf_counter()
    try:
        name = service.get_company(isin)
        return jsonify({"company_name": name})
    except Exception as exc:
        return _handle_service_error(exc, isin, "/company")
    finally:
        _log_endpoint_timing("/company/<isin>", started_at)
