"""
Backtest der Prognose im Zeitverlauf auf echten Reihen (Prüfung 2026-10-17,
docs/feature-doku/16-report-qualitaet.md, B6).

Für jedes Unternehmen außer Demo 1/2/3 (E2) wird die Reihe des Zeitverlaufs
nachgebildet (Monatsmittel der Gesamtnote der Mitarbeitenden über alle datierten
Bewertungen, Monate ohne Bewertung übersprungen, letzte 10 Jahre wie das Dashboard)
und mit ``services.forecast_service.rolling_origin_backtest`` geprüft: Holt gegen
letzter Wert, Mittel aller Monate, Mittel der letzten 6 Monate und Wert 12 Monate
zuvor; Horizont 6 Monate, 24 Monate Mindestlänge je Ursprung, bis zu 36 jüngste
Ursprünge. Die Datenbank wird nur gelesen.

Ausgabe:
- JSON ``backend/data/calibration/forecast_backtest_<Datum>.json`` je Unternehmen mit
  MAE/RMSE je Verfahren und gepoolt über alle Unternehmen (gewichtet nach Zahl der
  Prognosen),
- Tabelle auf der Konsole.

Aufruf:
    cd backend
    uv run python scripts/backtest_forecast.py
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from database.supabase_client import get_supabase_client  # noqa: E402
from services.forecast_service import HORIZON, METHODS, MIN_TRAIN, rolling_origin_backtest  # noqa: E402
from services.rating_series_service import OVERALL_DIMENSION, fetch_review_rows, month_key  # noqa: E402

DEMO_IDS = {10, 17, 18}
DAYS = 3650


def timeline_values(rows, cutoff: datetime):
    monthly = {}
    for r in rows:
        datum = r.get("datum")
        value = r.get(OVERALL_DIMENSION)
        if not datum or value is None:
            continue
        try:
            dt = datetime.fromisoformat(str(datum).replace("Z", "+00:00"))
        except ValueError:
            continue
        if dt.replace(tzinfo=None) < cutoff:
            continue
        period = month_key(datum)
        monthly.setdefault(period, []).append(float(value))
    periods = sorted(monthly)
    return periods, [round(sum(monthly[p]) / len(monthly[p]), 2) for p in periods], [len(monthly[p]) for p in periods]


def main() -> int:
    sb = get_supabase_client()
    companies = sb.table("companies").select("id,name").order("id").execute().data or []
    cutoff = datetime.now() - timedelta(days=DAYS)
    results = []
    pooled = {name: {"abs": 0.0, "sq": 0.0, "n": 0} for name in METHODS}
    print(f"{'Unternehmen':32} {'Monate':>6} {'Urspr.':>6} " + " ".join(f"{m:>9}" for m in METHODS) + "   bestes")
    for c in companies:
        cid = int(c["id"])
        if cid in DEMO_IDS:
            continue
        rows = fetch_review_rows("employee", cid, OVERALL_DIMENSION)
        periods, values, counts = timeline_values(rows, cutoff)
        bt = rolling_origin_backtest(values, horizon=HORIZON, min_train=MIN_TRAIN)
        entry = {
            "company_id": cid, "name": str(c.get("name", "")).strip(), "months": len(values),
            "first_month": periods[0] if periods else None, "last_month": periods[-1] if periods else None,
            "months_below_5": sum(1 for n in counts if n < 5),
            "backtest": None,
        }
        if bt:
            entry["backtest"] = {k: v for k, v in bt.items() if k != "residuals"}
            for name in METHODS:
                errs = [e for h in bt["residuals"][name].values() for e in h]
                pooled[name]["abs"] += sum(abs(e) for e in errs)
                pooled[name]["sq"] += sum(e * e for e in errs)
                pooled[name]["n"] += len(errs)
            maes = {name: bt["methods"][name]["mae"] for name in METHODS}
            print(f"{entry['name'][:32]:32} {len(values):6d} {bt['origins']:6d} "
                  + " ".join(f"{(maes[m] if maes[m] is not None else float('nan')):9.3f}" for m in METHODS)
                  + f"   {bt['best_method']}")
        else:
            print(f"{entry['name'][:32]:32} {len(values):6d}      – (zu kurz für einen Backtest, mindestens {MIN_TRAIN + 1} Monate)")
        results.append(entry)
    pooled_out = {
        name: {
            "mae": round(v["abs"] / v["n"], 4) if v["n"] else None,
            "rmse": round(math.sqrt(v["sq"] / v["n"]), 4) if v["n"] else None,
            "n": v["n"],
        }
        for name, v in pooled.items()
    }
    best = min((v["mae"], k) for k, v in pooled_out.items() if v["mae"] is not None)[1] if any(v["mae"] for v in pooled_out.values()) else None
    print("\nGepoolt (alle Prognosen gleich gewichtet):")
    for name, v in pooled_out.items():
        print(f"  {name:9} MAE {v['mae']}  RMSE {v['rmse']}  n = {v['n']}")
    print(f"  bestes Verfahren nach MAE: {best}")
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "series": "Monatsmittel der Gesamtnote, Mitarbeitende, letzte 10 Jahre, Monate ohne Bewertung übersprungen (wie GET /analytics/company/{id}/timeline)",
        "horizon": HORIZON, "min_train": MIN_TRAIN,
        "methods": list(METHODS), "pooled": pooled_out, "best_pooled": best,
        "companies": results,
    }
    target = Path(__file__).resolve().parents[1] / "data" / "calibration" / f"forecast_backtest_{datetime.now().date().isoformat()}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nErgebnis: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
