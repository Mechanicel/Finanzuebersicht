# markedataservice/src/api/stock.py

import logging
from typing import Any, Optional
from datetime import date, datetime as dt

from flask import Blueprint, jsonify, request
from markedataservice.src.services.stock_service import StockService

# Blueprint für Stock-Endpoints
stock_bp = Blueprint('stock', __name__)
service = StockService()

@stock_bp.route('/stock/<isin>', methods=['GET'])
def get_stock(isin: str):
    """Historischer Modus oder ETF-Modus je nach Query-Parameter"""
    etf = request.args.get('etf')
    if etf:
        # ETF-Modus: baue das vollständige Modell, gebe aber nur die Entries zurück
        model = service.build(isin, etf_key=etf)
        key = etf.lower()
        etf_data = model.etf.get(key)

        # ETFData-Objekt oder Dict in entries-List umwandeln
        if hasattr(etf_data, "to_dict") and callable(etf_data.to_dict):
            payload = etf_data.to_dict().get("entries", [])
        elif isinstance(etf_data, dict):
            payload = etf_data.get("entries", [])
        else:
            payload = getattr(etf_data, "entries", [])

        return jsonify(payload)
    else:
        # Historischer Modus: liefere das komplette Modell zurück
        model = service.build(isin)
        return jsonify(model.to_dict())

@stock_bp.route('/price/<isin>', methods=['GET'])
def get_price(isin: str):
    """Liefer Preis für eine ISIN an einem gegebenen Datum oder heute, falls kein Datum angegeben"""
    date_str = request.args.get('date')
    target_date: Optional[date] = None
    if date_str:
        try:
            target_date = dt.fromisoformat(date_str).date()
        except ValueError:
            return jsonify({'error': 'Invalid date format, expected YYYY-MM-DD'}), 400
    try:
        price = service.get_price(isin, target_date)
    except Exception as e:
        return jsonify({'error': str(e)}), 404
    return jsonify({'price': price})

@stock_bp.route('/company/<isin>', methods=['GET'])
def get_company(isin: str):
    """Gibt den Firmennamen für eine ISIN zurück"""
    try:
        name = service.get_company(isin)
    except Exception as e:
        return jsonify({'error': str(e)}), 404
    return jsonify({'company_name': name})
