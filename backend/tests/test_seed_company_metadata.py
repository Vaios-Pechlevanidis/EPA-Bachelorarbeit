"""Scratch-Tests (Reviewer): Fehlerpfade von seed_company_metadata.py und
fix_company_names.py gegen Fake-Clients, ohne gehostete DB."""
import json, os, sys, copy
import pytest

BACKEND = "/Users/vaios/EPA-Bachelorarbeit/EPA-Bachelorarbeit/backend"
sys.path.insert(0, BACKEND)
sys.path.insert(0, os.path.join(BACKEND, "scripts"))

import seed_company_metadata as seed  # noqa: E402
import fix_company_names as fix  # noqa: E402

DATA = os.path.join(BACKEND, "data", "company_metadata.json")


class _Err(Exception):
    def __init__(self):
        super().__init__("column companies.ticker does not exist")
        self.code = "42703"


class _QB:
    def __init__(self, client, rows, with_meta):
        self.c, self.rows, self.with_meta = client, rows, with_meta
        self.cols = ""
        self.upd = None
    def select(self, cols):
        self.cols = cols
        if not self.with_meta and any(m in cols for m in seed.META_COLUMNS):
            raise _Err()
        return self
    def limit(self, n): return self
    def order(self, *a, **k): return self
    def range(self, a, b): self._r = (a, b); return self
    def eq(self, col, val):
        self.rows = [r for r in self.rows if r.get(col) == val]; return self
    def update(self, data):
        self.upd = data; return self
    def execute(self):
        if self.upd is not None:
            self.c.writes.append((self.rows[0]["id"] if self.rows else None, self.upd))
            return type("R", (), {"data": self.rows})()
        if hasattr(self, "_r"):
            a, b = self._r
            return type("R", (), {"data": self.rows[a:b + 1]})()
        return type("R", (), {"data": self.rows})()


class _Client:
    def __init__(self, rows, with_meta):
        self.rows, self.with_meta, self.writes = rows, with_meta, []
    def table(self, name):
        assert name == "companies"
        return _QB(self, copy.deepcopy(self.rows), self.with_meta)


def _entries():
    with open(DATA, encoding="utf-8") as fh:
        return json.load(fh)


def _db_rows(with_meta):
    rows = []
    for e in _entries():
        r = {"id": e["company_id"], "name": e["name"]}
        if with_meta:
            r.update({c: None for c in seed.META_COLUMNS})
        rows.append(r)
    return rows


def test_apply_without_columns_exits_2_and_writes_nothing(monkeypatch, capsys):
    client = _Client(_db_rows(False), with_meta=False)
    monkeypatch.setattr(seed, "get_supabase_client", lambda: client)
    assert seed.main(["--apply"]) == 2
    assert client.writes == []
    assert "006_add_company_metadata" in capsys.readouterr().out


def test_dry_run_with_columns_reports_changes_and_writes_nothing(monkeypatch, capsys):
    client = _Client(_db_rows(True), with_meta=True)
    monkeypatch.setattr(seed, "get_supabase_client", lambda: client)
    assert seed.main([]) == 0
    assert client.writes == []
    out = capsys.readouterr().out
    assert "26 Einträge geprüft" in out


def test_name_mismatch_aborts_before_any_write_even_with_apply(monkeypatch, tmp_path, capsys):
    rows = _db_rows(True)
    rows[0]["name"] = "Jemand anderes"  # id 3 heißt in der DB anders
    client = _Client(rows, with_meta=True)
    monkeypatch.setattr(seed, "get_supabase_client", lambda: client)
    assert seed.main(["--apply"]) == 1
    assert client.writes == [], "Kein UPDATE bei Validierungsfehler"
    assert "passt nicht" in capsys.readouterr().out


def test_unknown_id_aborts(monkeypatch, tmp_path):
    rows = [r for r in _db_rows(True) if r["id"] != 33]
    client = _Client(rows, with_meta=True)
    monkeypatch.setattr(seed, "get_supabase_client", lambda: client)
    assert seed.main(["--apply"]) == 1
    assert client.writes == []


def test_invalid_peer_group_in_json_exits_3(monkeypatch, tmp_path):
    entries = _entries()
    entries[0]["peer_group"] = "DAX"
    p = tmp_path / "m.json"
    p.write_text(json.dumps(entries), encoding="utf-8")
    monkeypatch.setattr(seed, "get_supabase_client", lambda: (_ for _ in ()).throw(AssertionError("DB darf nicht angefasst werden")))
    assert seed.main(["--json", str(p)]) == 3


def test_duplicate_id_in_json_exits_3(tmp_path):
    entries = _entries()
    entries[1]["company_id"] = entries[0]["company_id"]
    p = tmp_path / "m.json"
    p.write_text(json.dumps(entries), encoding="utf-8")
    assert seed.main(["--json", str(p)]) == 3


def test_apply_with_columns_writes_only_changed(monkeypatch):
    rows = _db_rows(True)
    # id 8 (RWE) bereits korrekt gesetzt -> kein Update erwartet
    for r in rows:
        if r["id"] == 8:
            r.update({"ticker": "RWE.DE", "isin": None, "sector": "Energie", "peer_group": "Börsennotiert DE"})
    client = _Client(rows, with_meta=True)
    monkeypatch.setattr(seed, "get_supabase_client", lambda: client)
    assert seed.main(["--apply"]) == 0
    ids = [w[0] for w in client.writes]
    assert 8 not in ids and len(ids) == 25


def test_fix_names_dry_run_lists_defects_and_conflicts(monkeypatch, capsys):
    rows = [{"id": 1, "name": "E.ON\n"}, {"id": 2, "name": "e.on"}, {"id": 3, "name": "NTT  DATA SE"}, {"id": 4, "name": "ok"}]
    client = _Client(rows, with_meta=False)
    monkeypatch.setattr(fix, "get_supabase_client", lambda: client)
    assert fix.main([]) == 0
    out = capsys.readouterr().out
    assert "KONFLIKT mit id 2" in out and "'NTT DATA SE'" in out
    assert client.writes == []


def test_fix_names_apply_skips_conflicts(monkeypatch):
    rows = [{"id": 1, "name": "E.ON\n"}, {"id": 2, "name": "e.on"}, {"id": 3, "name": "NTT  DATA SE"}]
    client = _Client(rows, with_meta=False)
    monkeypatch.setattr(fix, "get_supabase_client", lambda: client)
    assert fix.main(["--apply"]) == 1
    assert client.writes == [(3, {"name": "NTT DATA SE"})]


def test_fix_names_empty_db(monkeypatch, capsys):
    client = _Client([], with_meta=False)
    monkeypatch.setattr(fix, "get_supabase_client", lambda: client)
    assert fix.main([]) == 0
    assert "Nichts zu tun" in capsys.readouterr().out
