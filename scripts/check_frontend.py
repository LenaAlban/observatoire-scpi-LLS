#!/usr/bin/env python3
"""Validation du JS embarqué et des données SCPI avant publication GitHub Pages."""
import json
from pathlib import Path
import re
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
html = (root / "index.html").read_text(encoding="utf-8")
records = json.loads((root / "data/scpi.json").read_text(encoding="utf-8"))
assert len(records) >= 31, f"Nombre de SCPI inattendu : {len(records)}"
assert len({r["id"] for r in records}) == len(records), "Identifiants SCPI dupliqués"
assert all(r.get("name") for r in records), "Nom SCPI manquant"
# Validate all published allocations and their documented provenance.
for scpi in records:
    for field in ("geo", "types"):
        allocation = scpi.get(field) or []
        if not allocation:
            continue
        assert 99 <= sum(float(value) for _, value in allocation) <= 101, (
            f"Répartition {field} non cohérente pour {scpi['name']}"
        )
        assert scpi.get(field + "Date"), f"Répartition {field} non datée : {scpi['name']}"
        assert (scpi.get("fieldSources") or {}).get(field, {}).get("url"), (
            f"Source manquante pour {field} : {scpi['name']}"
        )
# Prevent silently losing the verified geographic chart from CORUM T3 2026.
origin = next(r for r in records if r["id"] == "corum-origin")
assert origin.get("geoDate") >= "2026-09-30", "CORUM Origin : ventilation datée du T3 perdue"
assert origin.get("geo"), "CORUM Origin : ventilation géographique perdue"
assert origin.get("types"), "CORUM Origin : ventilation sectorielle perdue"
assert origin.get("tof") is not None, "CORUM Origin : TOF manquant"
scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, flags=re.S | re.I)
assert len(scripts) == 1, f"Scripts intégrés inattendus : {len(scripts)}"
assert "const SEED=" in scripts[0], "Référentiel initial manquant dans le script"
assert "render();" in scripts[0], "Appel du rendu initial manquant"
with tempfile.TemporaryDirectory() as tmp:
    js = Path(tmp) / "observatoire.js"
    js.write_text(scripts[0], encoding="utf-8")
    subprocess.run(["node", "--check", str(js)], check=True)
print(f"Interface JavaScript valide ; {len(records)} SCPI présentes.")
