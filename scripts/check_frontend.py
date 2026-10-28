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
scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", html, flags=re.S | re.I)
assert len(scripts) == 1, f"Scripts intégrés inattendus : {len(scripts)}"
assert "const SEED=" in scripts[0], "Référentiel initial manquant dans le script"
assert "render();" in scripts[0], "Appel du rendu initial manquant"
with tempfile.TemporaryDirectory() as tmp:
    js = Path(tmp) / "observatoire.js"
    js.write_text(scripts[0], encoding="utf-8")
    subprocess.run(["node", "--check", str(js)], check=True)
print(f"Interface JavaScript valide ; {len(records)} SCPI présentes.")
