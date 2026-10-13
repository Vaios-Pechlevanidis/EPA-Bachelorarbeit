#!/usr/bin/env python3
"""DZ1-Regelprüfer (Lauf 2): reine Rechenarbeit auf einer Serien-CSV, nur Standardbibliothek.

Liest backend/data/series/<id>_<slug>_employee.csv und prüft Kandidaten gegen das
Annotationsprotokoll (Regeln 2 bis 5) und die Setzungen des Agenten (Fassung Lauf 2).
Importiert nichts aus services oder models und kennt keine Erkennungsergebnisse.

Aufruf:
  python3 dz1_rechner.py tabelle CSV
  python3 dz1_rechner.py pruefe  CSV VON BIS [--json]
  python3 dz1_rechner.py scan    CSV [--json]          alle regelkonformen Zeiträume und Zweifelsfälle
  python3 dz1_rechner.py satz    CSV VON:BIS [VON:BIS ...]   Regel 5 für eine Auswahl
"""
import csv
import json
import sys

MIN_N = 5            # bewerteter Monat (E4, Regel 3)
DUENN_MAX = 9        # 5..9 Bewertungen: braucht Stützung (Regel 3)
VOR_MAX = 6          # Vorniveau: bis zu sechs bewertete Monate (Regel 4)
VOR_MIN = 3          # Setzung: mindestens drei bewertete Monate Vorniveau
NACH_MAX = 3         # Setzung: Folgeniveau aus bis zu drei bewerteten Monaten
LAENGE_MAX = 6       # Regel 2
INNEN_MAX = 1        # Regel 3: höchstens ein nicht bewerteter Monat innerhalb
RICHTWERT = 0.5      # Regel 4
ZWEIFEL_MIN = 0.3    # Zweifelsfall 0,30..0,49
RUECKKEHR = 0.25     # Setzung (b): erster Folgemonat mindestens 0,25 vom Vorniveau entfernt
ABSTAND_MIN = 3      # Regel 5: mindestens drei bewertete Monate zwischen zwei Zeiträumen
ANZAHL_MAX = 3       # Regel 5


def lese(pfad):
    rows = []
    with open(pfad, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            m = (r.get("mean_durchschnittsbewertung") or "").strip()
            c = (r.get("count") or "").strip()
            mean = float(m) if m else None
            n = int(c) if c else 0
            rows.append({"period": r["period"].strip(), "mean": mean, "n": n,
                         "bewertet": mean is not None and n >= MIN_N})
    rows.sort(key=lambda x: x["period"])
    return rows


def midx(p):
    return int(p[:4]) * 12 + int(p[5:7]) - 1


def laenge(a, b):
    return midx(b) - midx(a) + 1


def de(x, nk):
    s = f"{x:+.{nk}f}" if nk == 2 else f"{x:.{nk}f}"
    return s.replace(".", ",")


def nspanne(ms):
    ns = [m["n"] for m in ms]
    return f"n={min(ns)}" if min(ns) == max(ns) else f"n={min(ns)}-{max(ns)}"


def pruefe(rows, von, bis):
    """Alle Regelprüfungen für einen Kandidaten; entscheidet nur mechanisch prüfbare Regeln."""
    res = {"von": von, "bis": bis, "regeln": {}, "hinweise": []}
    perioden = [r["period"] for r in rows]
    if von not in perioden or bis not in perioden or von > bis:
        res["fehler"] = "Monat außerhalb der Reihe oder VON > BIS"
        res["ergebnis"] = "verworfen"
        return res
    bew = [r for r in rows if r["bewertet"]]
    im = [r for r in rows if von <= r["period"] <= bis]
    im_bew = [r for r in im if r["bewertet"]]
    innen = [r for r in im if not r["bewertet"]]
    vor = [r for r in bew if r["period"] < von][-VOR_MAX:]
    nach = [r for r in bew if r["period"] > bis][:NACH_MAX]
    L = laenge(von, bis)
    res.update({
        "laenge": L,
        "monate_im_zeitraum": [{"period": r["period"], "mean": r["mean"], "n": r["n"], "bewertet": r["bewertet"]} for r in im],
        "vorniveau_monate": [{"period": r["period"], "mean": r["mean"], "n": r["n"]} for r in vor],
        "folgemonate": [{"period": r["period"], "mean": r["mean"], "n": r["n"]} for r in nach],
    })
    R = res["regeln"]
    # Regel 2
    R["R2_laenge"] = {"ok": L <= LAENGE_MAX, "wert": L}
    # Regel 3
    rand_ok = bool(im) and im[0]["bewertet"] and im[-1]["bewertet"]
    R["R3_raender"] = {"ok": rand_ok, "von_n": im[0]["n"], "bis_n": im[-1]["n"]}
    R["R3_innen_nicht_bewertet"] = {"ok": len(innen) <= INNEN_MAX, "monate": [f"{r['period']} (n={r['n']})" for r in innen]}
    # Vorniveau
    if len(vor) < VOR_MIN:
        R["S_vorniveau_min3"] = {"ok": False, "wert": len(vor)}
        res["ergebnis"] = "verworfen"
        return res
    R["S_vorniveau_min3"] = {"ok": True, "wert": len(vor)}
    pre = sum(r["mean"] for r in vor) / len(vor)
    lvl = sum(r["mean"] for r in im_bew) / len(im_bew) if im_bew else None
    if lvl is None:
        res["ergebnis"] = "verworfen"
        return res
    d = lvl - pre
    sgn = 1 if d > 0 else -1
    res.update({"vorniveau": pre, "niveau": lvl, "delta": d, "richtung": "rise" if d > 0 else "fall"})
    # Regel 4
    if abs(d) >= RICHTWERT:
        R["R4_groesse"] = {"ok": True, "wert": round(d, 4)}
    elif abs(d) >= ZWEIFEL_MIN:
        R["R4_groesse"] = {"ok": False, "zweifel": True, "wert": round(d, 4)}
    else:
        R["R4_groesse"] = {"ok": False, "wert": round(d, 4)}
    # Setzung (c): Folgeniveau prüfbar
    if not nach:
        R["S_folgeniveau"] = {"ok": False, "grund": "kein bewerteter Monat nach period_to; Bleiben nicht prüfbar"}
    else:
        post = sum(r["mean"] for r in nach) / len(nach)
        a_ok = (post - pre) * sgn >= abs(d) / 2
        first_dev = (nach[0]["mean"] - pre) * sgn
        b_ok = first_dev >= RUECKKEHR
        R["S_folgeniveau"] = {
            "ok": a_ok and b_ok,
            "folgemittel": round(post, 4), "folgemittel_abstand": round((post - pre) * sgn, 4),
            "verlangt_mindestens": round(abs(d) / 2, 4), "a_haelfte_bleibt": a_ok,
            "erster_folgemonat": f"{nach[0]['period']}={nach[0]['mean']:.3f} (n={nach[0]['n']})",
            "erster_folgemonat_abstand": round(first_dev, 4), "b_keine_rueckkehr": b_ok,
        }
    # Regel 3, Stützung dünner Monate (5..9)
    duenn = [r for r in im_bew if r["n"] <= DUENN_MAX]
    stuetz_ok = True
    stuetz_info = []
    kandidaten = im_bew + nach[:1]
    for t in duenn:
        stuetzen = [k for k in kandidaten if k["period"] != t["period"] and (k["mean"] - pre) * sgn >= RICHTWERT]
        stuetz_info.append(f"{t['period']} (n={t['n']}): " + (", ".join(f"{k['period']} ({k['mean']:.2f}, n={k['n']})" for k in stuetzen) or "keine Stützung"))
        if not stuetzen:
            stuetz_ok = False
    R["R3_stuetzung_duenn"] = {"ok": stuetz_ok, "details": stuetz_info}
    # Hinweis Vortrend (Regel 2, Trend): Lage der Vormonate
    if len(vor) >= 6:
        erst = sum(r["mean"] for r in vor[:3]) / 3
        letzt = sum(r["mean"] for r in vor[-3:]) / 3
        res["vortrend"] = round(letzt - erst, 4)
        if (letzt - erst) * sgn >= 0.25:
            res["hinweise"].append(f"Vorniveau bewegt sich bereits in Richtung des Sprungs ({de(letzt - erst, 2)}); Trend prüfen (Regel 2)")
    if (midx(vor[-1]["period"]) - midx(vor[0]["period"]) + 1) > 12:
        res["hinweise"].append(f"Vorniveau über {midx(vor[-1]['period']) - midx(vor[0]['period']) + 1} Kalendermonate verteilt (lückige Reihe)")
    alle_ok = all(v.get("ok") for v in R.values())
    if alle_ok:
        res["ergebnis"] = "regelkonform"
    elif all(v.get("ok") for k, v in R.items() if k != "R4_groesse") and R["R4_groesse"].get("zweifel"):
        res["ergebnis"] = "zweifelsfall_0_3_bis_0_49"
    else:
        res["ergebnis"] = "verworfen"
        res["gescheitert_an"] = [k for k, v in R.items() if not v.get("ok")]
    # note-Gerüst (Regel 11)
    teile = [
        f"Vorniveau {de(pre, 1)} ({vor[0]['period']} bis {vor[-1]['period']}, {nspanne(vor)})",
        f"Zeitraum {de(lvl, 1)} (n={', '.join(str(r['n']) for r in im_bew)})",
        f"Δ {de(d, 2)}",
        res["richtung"],
    ]
    grau = [f"{r['period']} nicht bewertet (n={r['n']})" for r in innen]
    if grau:
        teile.append("; ".join(grau))
    res["note_geruest"] = "; ".join(teile) + "; <Streuungshinweis optional>; Anker: keiner; Reihe allein."
    return res


def scan(rows):
    bew = [r for r in rows if r["bewertet"]]
    gut, zweifel = [], []
    for i, a in enumerate(bew):
        for b in bew[i:]:
            if laenge(a["period"], b["period"]) > LAENGE_MAX:
                break
            p = pruefe(rows, a["period"], b["period"])
            if p["ergebnis"] == "regelkonform":
                gut.append(p)
            elif p["ergebnis"] == "zweifelsfall_0_3_bis_0_49":
                zweifel.append(p)
    return gut, zweifel


def cluster(liste):
    liste = sorted(liste, key=lambda p: (p["von"], p["bis"]))
    gruppen = []
    for p in liste:
        if gruppen and p["von"] <= gruppen[-1]["bis_max"]:
            g = gruppen[-1]
            g["varianten"].append(p)
            g["bis_max"] = max(g["bis_max"], p["bis"])
        else:
            gruppen.append({"varianten": [p], "bis_max": p["bis"]})
    return gruppen


def kurz(p):
    return (f"{p['von']}..{p['bis']} ({p['laenge']} Mon.) {p.get('richtung', '?')} Δ {p.get('delta', 0):+.3f} "
            f"Vor {p.get('vorniveau', 0):.3f} Niv {p.get('niveau', 0):.3f} "
            f"Folge {p['regeln'].get('S_folgeniveau', {}).get('folgemittel', '-')}")


def satz(rows, paare):
    bew = [r["period"] for r in rows if r["bewertet"]]
    paare = sorted(paare)
    out = {"anzahl": len(paare), "anzahl_ok": len(paare) <= ANZAHL_MAX, "abstaende": []}
    for (a1, b1), (a2, b2) in zip(paare, paare[1:]):
        zwischen = [p for p in bew if b1 < p < a2]
        out["abstaende"].append({"zwischen": f"{b1}..{a2}", "bewertete_monate_dazwischen": len(zwischen),
                                 "ok": len(zwischen) >= ABSTAND_MIN and a2 > b1})
    out["ok"] = out["anzahl_ok"] and all(x["ok"] for x in out["abstaende"])
    out["bewertete_monate_reihe"] = len(bew)
    return out


def tabelle(rows):
    bew_vor = []
    print(f"{'Monat':8} {'Mittel':>7} {'n':>4} {'Status':9} {'Vor6':>6} {'Diff':>6}")
    for r in rows:
        vor, diff = "", ""
        if r["bewertet"] and bew_vor:
            w = bew_vor[-VOR_MAX:]
            v = sum(w) / len(w)
            vor, diff = f"{v:.2f}", f"{r['mean'] - v:+.2f}"
        status = "bewertet" if r["bewertet"] else ("grau" if r["n"] > 0 else "leer")
        mean = f"{r['mean']:.3f}" if r["mean"] is not None else "-"
        print(f"{r['period']:8} {mean:>7} {r['n']:>4} {status:9} {vor:>6} {diff:>6}")
        if r["bewertet"]:
            bew_vor.append(r["mean"])
    print(f"bewertete Monate: {sum(1 for r in rows if r['bewertet'])}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    cmd, pfad = sys.argv[1], sys.argv[2]
    rows = lese(pfad)
    js = "--json" in sys.argv
    if cmd == "tabelle":
        tabelle(rows)
    elif cmd == "pruefe":
        p = pruefe(rows, sys.argv[3], sys.argv[4])
        print(json.dumps(p, ensure_ascii=False, indent=1))
    elif cmd == "scan":
        gut, zweifel = scan(rows)
        if js:
            print(json.dumps({"regelkonform": gut, "zweifel": zweifel}, ensure_ascii=False))
        else:
            print(f"Regelkonforme Zeiträume (alle Regeln und Setzungen erfüllt): {len(gut)} in {len(cluster(gut))} Gruppen")
            for g in cluster(gut):
                print("  Gruppe:")
                for p in g["varianten"]:
                    print("    " + kurz(p))
            print(f"Zweifelsfälle 0,30..0,49 (sonst regelkonform): {len(zweifel)} in {len(cluster(zweifel))} Gruppen")
            for g in cluster(zweifel):
                print("  Gruppe:")
                for p in g["varianten"]:
                    print("    " + kurz(p))
    elif cmd == "satz":
        paare = [tuple(x.split(":")) for x in sys.argv[3:] if ":" in x]
        print(json.dumps(satz(rows, paare), ensure_ascii=False, indent=1))
    else:
        print(__doc__); sys.exit(1)
