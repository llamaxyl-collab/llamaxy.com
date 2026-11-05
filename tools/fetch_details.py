"""Urun detay sayfalari icin katalog bilgisi (Apo 5 Kas 2026: "urunlerin icine girip ozelliklerine bakilmiyor mu")
data/products.json'daki ASIN'ler -> data/details.json (madde imleri, aciklama, 6'ya kadar gorsel, yas, olcu, agirlik, parca).
Sadece eksik ya da 30 gunden eski olanlari ceker; publish.sh her calismada cagirir.
Kullanim: python3 tools/fetch_details.py [--all]
"""
import json, os, subprocess, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path

MP = "A1F83G8C2ARO7P"
SRC = Path.home() / "src"


def catalog(asins):
    """SP-API through APZ (scripts/catalog-raw.ts); the Python sp_api module lived on the Mac"""
    r = subprocess.run(["npx", "tsx", "--conditions=react-server", "--tsconfig", "scripts/tsconfig.json", "scripts/catalog-raw.ts", ",".join(asins)],
                       cwd=SRC, capture_output=True, text=True, timeout=120,
                       env={**os.environ, "APP_DB_PATH": str(Path.home() / "apozon/data/app.db")})
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.startswith("{") else None

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/details.json"
NOW = datetime.now(timezone.utc)


def val(attrs, key):
    """first value of an SP-API attribute for the UK marketplace / English"""
    for x in attrs.get(key, []):
        if x.get("marketplace_id", MP) == MP and x.get("language_tag", "en_GB").startswith("en"):
            return x.get("value", x)
    return None


def first(attrs, key):
    return next(iter(attrs.get(key, [])), None)


def vals(attrs, key):
    return [x["value"] for x in attrs.get(key, []) if "value" in x and x.get("language_tag", "en_GB").startswith("en")]


def size(d):
    if not isinstance(d, dict):
        return None
    parts = [d.get(k) for k in ("length", "width", "height")]
    if not all(isinstance(p, dict) and p.get("value") for p in parts):
        return None
    u = {"centimeters": "cm", "millimeters": "mm", "inches": "in"}.get(parts[0].get("unit"), parts[0].get("unit", ""))
    return " × ".join(f"{p['value']:g}" for p in parts) + f" {u}"


def weight(d):
    if not isinstance(d, dict) or not d.get("value"):
        return None
    u = {"kilograms": "kg", "grams": "g", "pounds": "lb", "ounces": "oz"}.get(d.get("unit"), d.get("unit", ""))
    return f"{d['value']:g} {u}"


def age(attrs):
    m = attrs.get("manufacturer_minimum_age") or []
    if m and isinstance(m[0], dict) and m[0].get("value"):
        v, u = m[0]["value"], m[0].get("unit", "months")
        return f"{v / 12:g}+ years" if u == "months" and v >= 24 else f"{v:g}+ {u}"
    return val(attrs, "age_range_description")


def images(it):
    best = {}
    for x in next(iter(it.get("images", [])), {}).get("images", []):
        v, h = x.get("variant", ""), x.get("height", 0)
        if h <= 1600 and h > best.get(v, {}).get("height", 0):
            best[v] = x
    order = sorted(best, key=lambda v: (v != "MAIN", v))
    return [best[v]["link"] for v in order][:6]


def parse(it):
    a = it.get("attributes", {})
    yn = lambda k: {True: "Yes", False: "No"}.get(val(a, k))
    spec = {
        "Age": age(a),
        "Pieces": val(a, "number_of_pieces"),
        "Colour": val(a, "color"),
        "Material": val(a, "material"),
        "Size": size(first(a, "item_dimensions")) or size(first(a, "item_package_dimensions")),
        "Weight": weight(first(a, "item_weight")) or weight(first(a, "item_package_weight")),
        "Batteries required": yn("batteries_required"),
        "Assembly required": yn("is_assembly_required"),
        "Model number": val(a, "model_number") or val(a, "part_number"),
    }
    return {
        "bullets": [b.strip() for b in vals(a, "bullet_point") if b.strip()][:7],
        "description": (val(a, "product_description") or "").strip(),
        "images": images(it),
        "spec": {k: str(v) for k, v in spec.items() if v not in (None, "", 0)},
        "at": NOW.isoformat(timespec="seconds"),
    }


def main():
    cache = json.loads(OUT.read_text()) if OUT.exists() else {}
    asins = [p["asin"] for p in json.loads((ROOT / "data/products.json").read_text())["products"]]
    old = (NOW - timedelta(days=30)).isoformat()
    todo = [a for a in asins if "--all" in sys.argv or a not in cache or cache[a].get("at", "") < old]
    for i in range(0, len(todo), 20):
        chunk = todo[i:i + 20]
        r = None
        for attempt in range(5):
            r = catalog(chunk)
            if r:
                break
            time.sleep(3 * (attempt + 1))
        for it in (r or {}).get("items", []):
            cache[it["asin"]] = parse(it)
        OUT.write_text(json.dumps(cache, ensure_ascii=False))
        print(f"  detay {min(i + 20, len(todo))}/{len(todo)}")
    print(f"details.json: {len(cache)} urun ({len(todo)} cekildi)")


if __name__ == "__main__":
    main()
