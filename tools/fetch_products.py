"""Amazon SP-API'den aktif listingleri ceker -> data/products.json
Kullanim: python3 tools/fetch_products.py
Satis fiyati/stok/SKU siteye KONMAZ; sadece baslik, marka, gorsel, kategori, ASIN.
"""
import gzip, json, sys, time, csv, io
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path.home() / "scripts/urun_arastirici"))
import sp_api  # noqa: E402
from config import SP_API_MARKETPLACE_ID as MP  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/products.json"


def create_report():
    r = sp_api._api_post("/reports/2021-06-30/reports", {
        "reportType": "GET_MERCHANT_LISTINGS_DATA",
        "marketplaceIds": [MP],
    })
    if not r or "reportId" not in r:
        sys.exit(f"Rapor olusturulamadi: {r}")
    rid = r["reportId"]
    print("Rapor istendi:", rid)
    while True:
        s = sp_api._api_get(f"/reports/2021-06-30/reports/{rid}")
        st = s.get("processingStatus")
        print("  durum:", st)
        if st == "DONE":
            return s["reportDocumentId"]
        if st in ("CANCELLED", "FATAL"):
            sys.exit(f"Rapor basarisiz: {s}")
        time.sleep(15)


def download(doc_id):
    d = sp_api._api_get(f"/reports/2021-06-30/documents/{doc_id}")
    raw = urlopen(Request(d["url"]), timeout=60).read()
    if d.get("compressionAlgorithm") == "GZIP":
        raw = gzip.decompress(raw)
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass


def catalog(asins):
    out = {}
    for i in range(0, len(asins), 20):
        chunk = asins[i:i + 20]
        for attempt in range(5):
            r = sp_api._api_get("/catalog/2022-04-01/items", {
                "identifiers": ",".join(chunk), "identifiersType": "ASIN",
                "marketplaceIds": MP, "includedData": "summaries,images,classifications",
                "pageSize": 20,
            })
            if r and "error" not in r:
                break
            time.sleep(3 * (attempt + 1))
        for it in (r or {}).get("items", []):
            summ = next(iter(it.get("summaries", [])), {})
            imgs = next(iter(it.get("images", [])), {}).get("images", [])
            main = [x for x in imgs if x.get("variant") == "MAIN"] or imgs
            main.sort(key=lambda x: -x.get("height", 0))
            # 500px civari gorsel yeterli
            pick = next((x for x in sorted(main, key=lambda x: x.get("height", 0)) if x.get("height", 0) >= 500), main[0] if main else None)
            out[it["asin"]] = {
                "asin": it["asin"],
                "title": summ.get("itemName", ""),
                "brand": summ.get("brand") or summ.get("brandName", ""),
                "category": (summ.get("websiteDisplayGroupName") or "").strip(),
                "image": pick["link"] if pick else "",
            }
        print(f"  katalog {min(i + 20, len(asins))}/{len(asins)}")
        time.sleep(0.6)
    return out


def main():
    text = download(create_report())
    rows = list(csv.DictReader(io.StringIO(text), delimiter="\t"))
    active = [r for r in rows if (r.get("status", "Active") or "Active").lower() == "active"
              and int(r.get("quantity") or 0) >= 0]
    asins = sorted({(r.get("asin1") or "").strip() for r in active} - {""})
    print(f"{len(rows)} satir, {len(asins)} benzersiz aktif ASIN")
    items = [v for v in catalog(asins).values() if v["title"] and v["image"]]
    items.sort(key=lambda x: (x["brand"].lower(), x["title"].lower()))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"updated": time.strftime("%Y-%m-%d"), "products": items},
                              ensure_ascii=False, indent=1))
    print(f"{len(items)} urun yazildi -> {OUT}")


if __name__ == "__main__":
    main()
