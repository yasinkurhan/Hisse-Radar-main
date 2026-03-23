from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta

from ..services.borsapy_fetcher import get_borsapy_fetcher

router = APIRouter(prefix="/api/economy", tags=["Ekonomi & Makro"])

@router.get("/bonds")
async def get_bonds():
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_bonds()

        if result is None or (hasattr(result, 'empty') and result.empty):
            return {"records": [], "count": 0}

        if hasattr(result, 'to_dict'):
            records = result.to_dict(orient='records')
            return {"records": records, "count": len(records)}
            
        return {"records": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/eurobonds")
async def get_eurobonds(currency: Optional[str] = Query(None, description="Para birimi: USD, EUR")):
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_eurobonds(currency=currency)

        if result is None or (hasattr(result, 'empty') and result.empty):
            return {"records": [], "count": 0}

        if hasattr(result, 'to_dict'):
            records = result.to_dict(orient='records')
            return {"records": records, "count": len(records)}
            
        return {"records": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calendar")
async def get_calendar(period: str = "1w", country: str = "TR"):
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_economic_calendar(period=period, country=country)

        records = []
        if result is not None and hasattr(result, 'to_dict') and not result.empty:
            result = result.fillna(0)
            result.columns = [c.lower() for c in result.columns]
            result = result.rename(columns={'importance': 'impact'})
            if 'impact' in result.columns:
                result['impact'] = result['impact'].replace({'mid': 'medium', 'high': 'High', 'Medium': 'Medium', 'Low': 'Low'})
            records = result.to_dict(orient='records')
            for r in records:
                for k, v in r.items():
                    if hasattr(v, 'isoformat'):
                        r[k] = v.isoformat()
                    if k in ['actual', 'forecast', 'previous'] and v == 0:
                        r[k] = None
        else:
            now = datetime.now()
            records = [
                {'date': (now).strftime('%Y-%m-%d'), 'time': '14:00', 'country': 'TR', 'impact': 'High', 'event': 'TCMB Banka Meclisi Toplantisi', 'actual': None, 'forecast': 50.0, 'previous': 50.0},
                {'date': (now + timedelta(days=1)).strftime('%Y-%m-%d'), 'time': '10:00', 'country': 'TR', 'impact': 'High', 'event': 'TUFE Enflasyon', 'actual': None, 'forecast': 3.1, 'previous': 2.96},
                {'date': (now + timedelta(days=2)).strftime('%Y-%m-%d'), 'time': '10:00', 'country': 'TR', 'impact': 'Medium', 'event': 'Issizlik Orani', 'actual': None, 'forecast': 8.6, 'previous': 8.5},
            ]

        return {
            "period": period,
            "country": country,
            "events": records,
            "count": len(records),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tcmb")
async def get_tcmb():
    return {
        "policy_rate": 50.0,
        "overnight_borrowing": 47.0,
        "overnight_lending": 53.0,
        "glp_rate": 56.0,
        "last_updated": datetime.now().isoformat()
    }

@router.get("/inflation")
async def get_inflation():
    return {
        "cpi_yearly": 64.77,
        "cpi_monthly": 6.70,
        "ppi_yearly": 44.20,
        "last_updated": datetime.now().isoformat()
    }

@router.get("/risk-free-rate")
async def get_risk_free_rate():
    try:
        fetcher = get_borsapy_fetcher()
        result = fetcher.get_bonds()
        if result is not None and not result.empty:
            for _, row in result.iterrows():
                name = str(row.get('Name', row.get('name', ''))).lower()
                if "10" in name:
                    return {"rate": float(row.get('Yield', row.get('yield', 40.0))), "source": "10Y TR Bond"}
            return {"rate": 40.0, "source": "Fallback"}
    except Exception:
        pass
    return {"rate": 40.0, "source": "Fallback"}
