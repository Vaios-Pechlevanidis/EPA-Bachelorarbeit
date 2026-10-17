"""
Stabilität der erkannten auffälligen Veränderungen über das Parameterraster
(Prüfung 2026-10-17, docs/feature-doku/16-report-qualitaet.md, B9).

Für jedes Unternehmen außer Demo 1/2/3 (E2), Mitarbeitende, Gesamtbewertung, ohne
Statusfilter (der geprüfte Umfang, E27): die Veränderungen der Standardparameter mit
``stability`` aus ``services.anomaly_service.company_anomalies`` (Raster
``STABILITY_GRID``: Strafterm-Faktor 1–4, Mindestlänge 2–6, Mindestdichte 3/5/8;
Toleranz 3 Kalendermonate). Die Datenbank wird nur gelesen.

Ausgabe:
- JSON ``backend/data/calibration/anomaly_stability_<Datum>.json``,
- Tabelle auf der Konsole.

Aufruf:
    cd backend
    uv run python scripts/report_stability.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from database.supabase_client import get_supabase_client  # noqa: E402
from services.anomaly_service import STABILITY_GRID, STABILITY_TOLERANCE_MONTHS, company_anomalies  # noqa: E402

DEMO_IDS = {10, 17, 18}


def main() -> int:
    sb = get_supabase_client()
    companies = sb.table("companies").select("id,name").order("id").execute().data or []
    out = []
    shares = []
    print(f"{'Unternehmen':32} {'Monat':>8} {'Richtung':>8} {'Delta':>7} {'Varianten':>9} {'Treffer':>7} {'Anteil':>6}")
    for c in companies:
        cid = int(c["id"])
        if cid in DEMO_IDS:
            continue
        name = str(c.get("name", "")).strip()
        res = company_anomalies(cid, "employee")
        if not res["eligibility"]["eligible"]:
            out.append({"company_id": cid, "name": name, "eligible": False, "anomalies": []})
            continue
        items = []
        for a in res["anomalies"]:
            st = a.get("stability") or {}
            items.append({
                "date": a["date"], "direction": a["direction"], "delta": a["delta"], "severity": a["severity"],
                "variants": st.get("variants"), "matches": st.get("matches"), "share": st.get("share"),
            })
            if st.get("share") is not None:
                shares.append(st["share"])
            print(f"{name[:32]:32} {a['date']:>8} {a['direction']:>8} {a['delta']:7.3f} {st.get('variants', 0):9d} {st.get('matches', 0):7d} {st.get('share') if st.get('share') is not None else float('nan'):6.2f}")
        if not items:
            print(f"{name[:32]:32}        – keine Veränderung")
        out.append({"company_id": cid, "name": name, "eligible": True, "anomalies": items})
    summary = {
        "n_anomalies": len(shares),
        "share_mean": round(sum(shares) / len(shares), 3) if shares else None,
        "share_min": min(shares) if shares else None,
        "n_share_at_least_0_75": sum(1 for s in shares if s >= 0.75),
        "n_share_below_0_5": sum(1 for s in shares if s < 0.5),
    }
    print("\nZusammenfassung:", json.dumps(summary, ensure_ascii=False))
    target = Path(__file__).resolve().parents[1] / "data" / "calibration" / f"anomaly_stability_{datetime.now().date().isoformat()}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "employee, durchschnittsbewertung, ohne Statusfilter; Standardparameter gegen das Raster",
        "grid": {k: list(v) for k, v in STABILITY_GRID.items()}, "tolerance_months": STABILITY_TOLERANCE_MONTHS,
        "summary": summary, "companies": out,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Ergebnis: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
