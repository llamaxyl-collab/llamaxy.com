"""data/products.json + sirket bilgileri -> site/ (statik HTML)
Kullanim: python3 tools/build.py
"""
import html, json, math, re, shutil, sqlite3
from urllib.request import Request, urlopen
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
PREVIEW = (ROOT / "data/preview-dir").read_text().strip()  # gizli test vitrini, ör. preview-3f9a… (4 Kas 2026)
DATA = json.loads((ROOT / "data/products.json").read_text())

CO = {
    "name": "Llamaxy Limited",
    "email": "info@llamaxy.com",
    "trade": "trade@llamaxy.com",
    "address": "122 Hawkins Road, Cambridge, CB4 2RD, United Kingdom",
    "crn": "13143085",
    "vat": "GB435877456",
    "eori": "GB435877456000",
    "director": "Abdullah Dönmez",
}

CAT = {
    "Toy": "Toys & Games", "Kitchen": "Home & Kitchen", "Home": "Home & Kitchen",
    "Sports": "Sports & Outdoors", "Apparel": "Clothing", "Shoes": "Clothing",
    "CE": "Electronics", "Personal Computer": "Electronics", "Wireless": "Electronics",
    "Office Product": "Office & Stationery", "Musical Instruments": "Musical Instruments",
    "Health and Beauty": "Health & Beauty", "Beauty": "Health & Beauty",
    "Baby Product": "Baby", "Lawn & Patio": "Garden", "Video Games": "Video Games",
    "Book": "Books", "Pet Products": "Pet Supplies", "Home Improvement": "DIY & Tools",
}

esc = html.escape
# Oyuncak turleri (basliktan); renkler dukkan paleti
TYPES = [("Plush & soft toys", "#ff5d73", r"plush|squishmallow|soft toy|cuddl|teddy"),
         ("Collectibles", "#8b5cf6", r"blind|mystery|capsule|surprise|collectible|series \d|funko|pop!"),
         ("Action figures", "#2b6cff", r"figure|transformers|marvel|star wars|wwe|masters of"),
         ("Animals & dinos", "#1fb978", r"schleich|dinosaur|dino|animal|horse"),
         ("Cars & vehicles", "#ff8a00", r"hot wheels|car\b|cars\b|vehicle|truck|matchbox|train"),
         ("Dolls & playsets", "#ff4fb4", r"doll|barbie|polly|playset|house"),
         ("Games & creative", "#00b3c7", r"game|puzzle|cards|jigsaw|yu-gi|lego|build|magnetic|geomag|craft|slime|kit"),
         ("More toys", "#ffb400", r"$^")]
products = DATA["products"]
for p in products:
    p["cat"] = CAT.get(p["category"], "Other")
# Sitede sadece oyuncaklar (Apo 10 Eki 2026)
products = [p for p in products if p["cat"] == "Toys & Games"]
# Site fiyati = Amazon FBA fiyatimizin %15 ustu, .99'a yuvarli; FBA stogu yoksa "Out of stock" (Apo 4 Kas 2026)
_db = sqlite3.connect("file:" + str(Path.home() / "src/data/app.db") + "?mode=ro", uri=True)
QTY = dict(_db.execute("select asin, sum(quantity) from listings where fulfillment_channel like 'AMAZON%' and status = 'Active' group by asin"))
AMZ = dict(_db.execute("select asin, max(price) from listings where fulfillment_channel like 'AMAZON%' "
                       "and quantity > 0 and status = 'Active' group by asin"))
IMG = ROOT / "data/img"
IMG.mkdir(parents=True, exist_ok=True)
for p in products:
    f = IMG / (p["asin"] + ".jpg")
    if not f.exists() and p["image"]:
        try:
            f.write_bytes(urlopen(Request(p["image"], headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read())
        except Exception as e:
            print("gorsel inmedi", p["asin"], e)
    p["image"] = "img/" + f.name if f.exists() else ""
    a = AMZ.get(p["asin"])
    p["price"] = math.ceil(a * 1.15) - 0.01 if a else None
    p["qty"] = QTY.get(p["asin"]) or 0
    t = (p["title"] + " " + p["brand"]).lower()
    p["type"] = next((n for n, _, r in TYPES if re.search(r, t)), "More toys")
# Urun sayfalari (Apo 5 Kas 2026: "urunlerin icine girip ozelliklerine bakilmiyor mu") — tools/fetch_details.py
_det = ROOT / "data/details.json"
DET = json.loads(_det.read_text()) if _det.exists() else {}
for p in products:
    p["url"] = "p/" + (re.sub(r"[^a-z0-9]+", "-", p["title"].lower())[:60].strip("-") or "toy") + "-" + p["asin"].lower() + ".html"
cats = Counter(p["cat"] for p in products)
cat_rank = {c: i for i, (c, _) in enumerate(cats.most_common())}
products.sort(key=lambda p: (p["price"] is None, p["cat"] == "Other", cat_rank[p["cat"]], p["brand"].lower(), p["title"].lower()))
brands = Counter(p["brand"] for p in products if p["brand"])
# Ana sayfada sadece tanınan oyuncak/koleksiyon markaları (rastgele ev/giyim markaları güven vermiyor)
SHOW_BRANDS = ["Squishmallows", "Schleich", "Funko", "Mattel", "Hasbro", "Hot Wheels", "Barbie", "Nerf",
               "Transformers", "Star Wars", "Masters of the Universe", "Miraculous", "Jazwares", "Jurassic World",
               "Polly Pocket", "Disney", "Marvel", "Playmobil", "Ravensburger", "Simba", "Bizak", "Geomag",
               "Yu-Gi-Oh!", "BANDAI", "Mini Brands", "My Little Pony", "Weta Workshop", "Just Play"]
toy_brands = Counter(p["brand"] for p in products if p["cat"] == "Toys & Games" and p["brand"])
top_brands = [b for b in SHOW_BRANDS if toy_brands.get(b)]

CSS = """
@font-face{font-family:Fredoka;src:url(fredoka.woff2) format("woff2");font-weight:300 700;font-display:swap}
:root{--ink:#1d2340;--muted:#6a7090;--line:#ebeef5;--bg:#fff;--red:#ff4757;--red-d:#e0303f;--blue:#2b6cff;--yellow:#ffc93c;--green:#1fb978;--purple:#8b5cf6;--soft:#f5f7ff}
*{box-sizing:border-box}
body{margin:0;display:flex;flex-direction:column;min-height:100vh;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}
h1,h2,h3,.logo,.fun,nav.cats a,.btn,.buy,.price,.stat b{font-family:Fredoka,ui-rounded,"Arial Rounded MT Bold",sans-serif}
a{color:inherit}
.wrap{width:100%;max-width:1200px;margin:0 auto;padding-inline:20px}
.promo{background:var(--red);color:#fff;text-align:center;font-weight:600;font-size:14px;padding:8px 12px;letter-spacing:.02em}
.promo b{color:var(--yellow)}
header{background:var(--blue);color:#fff;position:sticky;top:0;z-index:10;box-shadow:0 2px 0 rgba(0,0,0,.06)}
header .wrap{display:flex;align-items:center;gap:24px;min-height:78px}
.logo{font-weight:700;font-size:34px;letter-spacing:-.01em;text-decoration:none;color:#fff;line-height:1;white-space:nowrap}
.logo span{color:var(--yellow)}
.logo small{display:block;font-size:12px;font-weight:500;color:#d6e2ff;letter-spacing:.06em;margin-top:2px}
form.search{flex:1;display:flex;background:#fff;border-radius:999px;overflow:hidden;max-width:560px}
form.search input{flex:1;border:0;font:inherit;padding:12px 20px;outline:0;min-width:0}
form.search button{border:0;background:var(--red);color:#fff;font:600 15px Fredoka,sans-serif;padding:0 22px;cursor:pointer}
.hlinks{display:flex;gap:18px;align-items:center;margin-left:auto}
.hlinks a{text-decoration:none;font-weight:600;font-size:14px;color:#fff;white-space:nowrap}
.bk{background:var(--yellow);color:var(--ink)!important;border-radius:999px;padding:9px 16px}
.bk i{font-style:normal;background:var(--red);color:#fff;border-radius:999px;padding:0 7px;font-size:12px;margin-left:6px}
nav.cats{background:#fff;border-bottom:1px solid var(--line)}
nav.cats .wrap{display:flex;gap:6px;overflow-x:auto;padding-block:8px}
nav.cats a{text-decoration:none;font-weight:600;font-size:15px;padding:8px 14px;border-radius:999px;white-space:nowrap}
nav.cats a:hover{background:var(--soft)}
nav.cats a.hot{color:var(--red)}
.usp{background:var(--soft);font-size:13px;font-weight:600;color:var(--muted)}
.usp .wrap{display:flex;justify-content:space-around;gap:12px;flex-wrap:wrap;padding-block:9px}
.hero{background:radial-gradient(circle at 85% 30%,#ffe27a 0,#ffc93c 30%,#ff9f43 100%);overflow:hidden}
.hero .wrap{display:grid;grid-template-columns:1.05fr 1fr;align-items:center;gap:24px;min-height:400px}
.hero h1{font-size:clamp(34px,5.4vw,60px);line-height:1.02;margin:0 0 14px;color:var(--ink)}
.hero h1 em{font-style:normal;color:var(--red)}
.hero p{font-size:18px;margin:0 0 26px;color:#3c3420;max-width:500px}
.collage{position:relative;height:380px}
.collage img{position:absolute;background:#fff;border-radius:24px;padding:14px;box-shadow:0 14px 30px rgba(120,60,0,.25);object-fit:contain}
.collage img:nth-child(1){width:52%;height:58%;left:4%;top:6%;transform:rotate(-6deg)}
.collage img:nth-child(2){width:44%;height:50%;right:2%;top:0;transform:rotate(5deg)}
.collage img:nth-child(3){width:40%;height:46%;left:22%;bottom:0;transform:rotate(3deg)}
.collage img:nth-child(4){width:36%;height:42%;right:6%;bottom:4%;transform:rotate(-4deg)}
.btn{display:inline-block;background:var(--red);color:#fff;text-decoration:none;padding:14px 30px;border-radius:999px;font-weight:600;font-size:18px;border:0;cursor:pointer;box-shadow:0 4px 0 var(--red-d)}
.btn:hover{transform:translateY(-1px)}
.btn.ghost{background:#fff;color:var(--ink);box-shadow:0 4px 0 #e6d6b0;margin-left:10px}
section{padding-block:48px}
h2{font-size:34px;margin:0 0 6px;text-align:center}
.sub{color:var(--muted);margin:0 0 28px;text-align:center}
.types{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:18px}
.type{text-decoration:none;text-align:center;font:600 16px Fredoka,sans-serif}
.type .c{aspect-ratio:1;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-bottom:8px;border:6px solid #fff;box-shadow:0 6px 16px rgba(0,0,0,.12);transition:transform .15s}
.type:hover .c{transform:scale(1.05) rotate(-3deg)}
.type img{width:66%;height:66%;object-fit:contain;filter:drop-shadow(0 4px 6px rgba(0,0,0,.2));background:#fff;border-radius:18px;padding:6px}
.band{background:var(--soft)}
.prices{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px}
.prices a{text-decoration:none;color:#fff;border-radius:22px;padding:26px;font:700 26px Fredoka,sans-serif;line-height:1.1}
.prices a small{display:block;font-size:15px;font-weight:500;opacity:.9;margin-top:6px}
.chips{display:flex;flex-wrap:wrap;gap:10px;justify-content:center}
.chip{background:#fff;border:2px solid var(--line);border-radius:999px;padding:8px 18px;font:600 15px Fredoka,sans-serif;text-decoration:none}
.chip:hover{border-color:var(--blue);color:var(--blue)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px}
.stat{background:#fff;border-radius:20px;padding:20px;text-align:center;border:2px solid var(--line)}
.stat .e{font-size:34px}
.stat b{display:block;font-size:20px}
.stat span{color:var(--muted);font-size:14px}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px}
.box{background:#fff;border:2px solid var(--line);border-radius:20px;padding:24px}
.box h3{margin:0 0 6px;font-size:20px}
.box p{margin:0;color:var(--muted)}
dl.facts{display:grid;grid-template-columns:max-content 1fr;gap:10px 24px;margin:0}
dl.facts dt{color:var(--muted)}
dl.facts dd{margin:0;font-weight:500;overflow-wrap:anywhere}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:18px}
.card{background:#fff;border:2px solid var(--line);border-radius:20px;overflow:hidden;display:flex;flex-direction:column;position:relative;transition:transform .15s,box-shadow .15s}
.card:hover{transform:translateY(-3px);box-shadow:0 12px 26px rgba(29,35,64,.12);border-color:#dfe4f2}
.card .img{aspect-ratio:1;display:flex;align-items:center;justify-content:center;padding:16px;background:#fff}
.card img{max-width:100%;max-height:100%;object-fit:contain}
.card .t{padding:4px 16px 16px;font-size:14px;flex:1;display:flex;flex-direction:column;gap:4px}
.card .b{font-size:12px;color:var(--blue);font-weight:700;text-transform:uppercase;letter-spacing:.04em}
.card .n{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.9em}
.badge{position:absolute;top:12px;left:12px;background:var(--red);color:#fff;font:600 12px Fredoka,sans-serif;border-radius:999px;padding:3px 10px}
.badge.g{background:var(--green)}
.price{font-size:24px;font-weight:700;color:var(--red);margin-top:auto}
.buy{display:block;margin-top:8px;text-align:center;background:var(--green);color:#fff;text-decoration:none;font-weight:600;border-radius:999px;padding:10px 0;font-size:16px}
.buy:hover{filter:brightness(.95)}
button.buy{width:100%;border:0;cursor:pointer;box-shadow:0 3px 0 #149a62}
.buy.off{background:#d5d9e4;box-shadow:none;cursor:default}
.filters{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px}
.filters input,.filters select{font:inherit;padding:11px 14px;border:2px solid var(--line);border-radius:999px;background:#fff;min-width:0;flex:1 1 180px}
.count{color:var(--muted);font-size:14px;margin-bottom:12px}
.toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:var(--ink);color:#fff;padding:12px 20px;border-radius:999px;font-size:14px;z-index:50}
table.cart{width:100%;border-collapse:collapse;background:#fff}
table.cart td{border-bottom:1px solid var(--line);padding:10px;vertical-align:middle}
table.cart img{width:64px;height:64px;object-fit:contain}
table.cart input{width:56px;font:inherit;padding:4px}
.sum{max-width:360px;margin-left:auto;margin-top:20px}
.sum div{display:flex;justify-content:space-between;padding:4px 0}
.sum .tot{font-weight:700;font-size:20px;border-top:1px solid var(--line);margin-top:6px;padding-top:10px}
form.co{display:grid;grid-template-columns:1fr 1fr;gap:12px}
form.co label{display:flex;flex-direction:column;font-size:14px;color:var(--muted);gap:4px}
form.co label.w{grid-column:1/-1}
form.co input,form.co select{font:inherit;padding:10px 12px;border:2px solid var(--line);border-radius:12px;color:var(--ink)}
.err{background:#fdecec;border:1px solid #f2b8b8;color:#8a1f1f;border-radius:14px;padding:14px 18px;margin-top:16px}
.spin{display:inline-block;width:16px;height:16px;border:2px solid #fff;border-right-color:transparent;border-radius:50%;animation:r .8s linear infinite;vertical-align:-3px;margin-right:8px}
@keyframes r{to{transform:rotate(360deg)}}
.card a.img,.card a.n{text-decoration:none;color:inherit}
.card a.n:hover{color:var(--blue)}
.crumbs{font-size:14px;color:var(--muted);margin:0 0 18px}.crumbs a{text-decoration:none;color:var(--blue)}
.pd{display:grid;grid-template-columns:1fr 1fr;gap:36px;align-items:start}
.gal .main{aspect-ratio:1;background:#fff;border:2px solid var(--line);border-radius:22px;display:flex;align-items:center;justify-content:center;padding:24px}
.gal .main img{max-width:100%;max-height:100%;object-fit:contain}
.thumbs{display:flex;gap:10px;margin-top:12px;overflow-x:auto}
.thumbs img{width:72px;height:72px;object-fit:contain;border:2px solid var(--line);border-radius:12px;padding:4px;background:#fff;cursor:pointer;flex:none}
.thumbs img:hover{border-color:var(--blue)}
.info .b{font-size:13px;color:var(--blue);font-weight:700;text-transform:uppercase;letter-spacing:.04em}
.info h1{font-size:clamp(24px,3vw,32px);line-height:1.15;margin:4px 0 12px}
.info .price{font-size:34px;margin:0 8px 0 0;display:inline-block}
.info .buy{max-width:320px;margin-top:16px;font-size:18px;padding:13px 0}
.perks{list-style:none;padding:0;margin:18px 0;color:var(--muted);font-size:14px;line-height:1.9}
.info h3{margin:22px 0 6px}
.feats{padding-left:20px;margin:0;line-height:1.6}.feats li{margin-bottom:6px}
@media(max-width:800px){.pd{grid-template-columns:1fr;gap:20px}}
footer{margin-top:auto;background:var(--ink);color:#b9bfd6;padding-block:44px 28px;font-size:14px}
footer .wrap{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:24px}
footer b{color:#fff;font:600 17px Fredoka,sans-serif;display:block;margin-bottom:8px}
footer a{color:#dfe4f5;text-decoration:none;display:block;line-height:1.9}
footer a:hover{color:var(--yellow)}
footer .legal{display:block;margin-top:28px;border-top:1px solid #333a5c;padding-top:18px;font-size:12px;color:#8990ad}
@media(max-width:800px){.hero .wrap{grid-template-columns:1fr}.collage{height:260px}header .wrap{flex-wrap:wrap;padding-block:10px}form.search{order:3;flex-basis:100%;max-width:none}.hlinks .hide{display:none}}
"""

def page(title, active, body, desc):
    cats_nav = "".join(f'<a href="products.html#t={esc(n)}">{esc(n)}</a>' for n, _, _ in TYPES if n != "More toys")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='30' fill='%232b6cff'/><text x='50' y='72' font-size='66' text-anchor='middle' fill='%23ffc93c' font-family='Arial' font-weight='bold'>L</text></svg>">
<link rel="preload" href="fredoka.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="style.css"></head><body>
<div class="promo">🎄 Christmas toy shop is open · <b>FREE UK delivery</b> on orders over £40</div>
<header><div class="wrap"><a class="logo" href="index.html">Llamaxy<span>!</span><small>TOYS · GAMES · COLLECTIBLES</small></a>
<form class="search" action="products.html"><input name="q" type="search" placeholder="Search toys, brands, characters…"><button>Search</button></form>
<div class="hlinks"><a class="hide" href="help.html">Help</a><a class="bk" href="basket.html">🛒 Basket<i id="bkn">0</i></a></div></div></header>
<nav class="cats"><div class="wrap"><a href="products.html" class="hot">All toys</a>{cats_nav}<a href="products.html#p=10" class="hot">Under £10</a></div></nav>
<div class="usp"><div class="wrap"><span>🚚 Dispatched in 1–2 working days</span><span>↩️ 14-day returns</span><span>✅ 100% genuine branded toys</span><span>🔒 Secure checkout</span></div></div>
{body}
<footer><div class="wrap">
<div><b>Shop</b><a href="products.html">All toys</a>{"".join(f'<a href="products.html#t={esc(n)}">{esc(n)}</a>' for n, _, _ in TYPES[:4])}</div>
<div><b>Help</b><a href="help.html">Delivery &amp; returns</a><a href="terms.html">Terms of sale</a><a href="contact.html">Contact us</a><a href="basket.html">Your basket</a></div>
<div><b>About Llamaxy</b><a href="about.html">Our company</a><a href="suppliers.html">Trade &amp; suppliers</a><a href="privacy.html">Privacy</a></div>
<div><b>Questions?</b>We're happy to help.<a href="mailto:{CO['email']}">{CO['email']}</a></div>
<span class="legal" style="grid-column:1/-1">© {DATA['updated'][:4]} {CO['name']} · Registered in England &amp; Wales No. {CO['crn']} · VAT {CO['vat']} · {esc(CO['address'])}</span>
</div></footer>
<script src="shop.js"></script></body></html>"""


def card(p):
    badge = ""
    if p["price"] and p["qty"] <= 3:
        badge = f'<span class="badge">Only {p["qty"]} left</span>'
    return (f'<div class="card" data-c="{esc(p["type"])}" data-b="{esc(p["brand"])}" data-p="{p["price"] or 0}" data-s="{esc((p["title"] + " " + p["brand"]).lower())}">{badge}'
            f'<a class="img" href="{p["url"]}"><img loading="lazy" src="{esc(p["image"])}" alt="{esc(p["title"][:90])}"></a>'
            f'<div class="t"><div class="b">{esc(p["brand"])}</div><a class="n" href="{p["url"]}">{esc(p["title"])}</a>'
            + (f'<div class="price">£{p["price"]:.2f}</div><button class="buy" data-a="{esc(p["asin"])}" data-p="{p["price"]:.2f}" '
               f'data-t="{esc(p["title"][:120])}" data-i="{esc(p["image"])}">Add to basket</button>'
               if p["price"] else '<div class="price" style="color:var(--muted);font-size:16px">Out of stock</div><button class="buy off" disabled>Add to basket</button>')
            + '</div></div>')

def buy_button(p):
    return (f'<button class="buy" data-a="{esc(p["asin"])}" data-p="{p["price"]:.2f}" data-t="{esc(p["title"][:120])}" data-i="{esc(p["image"])}">Add to basket</button>'
            if p["price"] else '<button class="buy off" disabled>Out of stock</button>')


def product_page(p, related):
    d = DET.get(p["asin"], {})
    imgs = ([p["image"]] if p["image"] else []) + [u for u in d.get("images", [])[1:]]
    thumbs = "".join(f'<img src="{esc(u)}" alt="" loading="lazy" onclick="document.getElementById(\'pm\').src=this.src">' for u in imgs) if len(imgs) > 1 else ""
    stock = (f'<span class="badge" style="position:static">Only {p["qty"]} left</span>' if p["price"] and p["qty"] <= 3
             else '<span class="badge g" style="position:static">In stock</span>' if p["price"] else "")
    feats = "".join(f"<li>{esc(b)}</li>" for b in d.get("bullets", []))
    spec = {"Brand": p["brand"], **d.get("spec", {})}
    facts = "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in spec.items() if v)
    desc = d.get("description", "")
    ld = {"@context": "https://schema.org", "@type": "Product", "name": p["title"], "brand": {"@type": "Brand", "name": p["brand"]},
          "image": ["https://llamaxy.com/" + u if u.startswith("img/") else u for u in imgs[:3]], "sku": p["asin"],
          "description": (d.get("bullets") or [desc or p["title"]])[0][:300]}
    if p["price"]:
        ld["offers"] = {"@type": "Offer", "priceCurrency": "GBP", "price": f'{p["price"]:.2f}', "availability": "https://schema.org/InStock",
                        "url": "https://llamaxy.com/" + p["url"], "seller": {"@type": "Organization", "name": CO["name"]}}
    body = f"""<section style="padding-top:24px"><div class="wrap">
<p class="crumbs"><a href="index.html">Home</a> › <a href="products.html#t={esc(p['type'])}">{esc(p['type'])}</a> › {esc(p['title'][:60])}</p>
<div class="pd"><div class="gal"><div class="main"><img id="pm" src="{esc(imgs[0] if imgs else '')}" alt="{esc(p['title'][:90])}"></div><div class="thumbs">{thumbs}</div></div>
<div class="info"><div class="b">{esc(p['brand'])}</div><h1>{esc(p['title'])}</h1>
<div class="price">{f"£{p['price']:.2f}" if p['price'] else '<span style="color:var(--muted);font-size:18px">Out of stock</span>'}</div>{stock}
{buy_button(p)}
<ul class="perks"><li>🚚 Dispatched in 1–2 working days · free UK delivery over £40</li><li>↩️ 14-day returns</li><li>✅ Genuine, brand-new and sealed</li></ul>
{f'<h3>Features</h3><ul class="feats">{feats}</ul>' if feats else ''}
</div></div>
{f'<div class="box" style="margin-top:28px"><h3>Description</h3><p style="color:var(--ink);white-space:pre-line">{esc(desc)}</p></div>' if desc else ''}
<div class="box" style="margin-top:20px"><h3>Product details</h3><dl class="facts">{facts}</dl></div>
{f'<h2 style="margin-top:44px">You may also like</h2><div class="grid" style="margin-top:20px">{"".join(card(r) for r in related)}</div>' if related else ''}
</div></section><script type="application/ld+json">{json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")}</script>"""
    h = page(f"{p['title'][:70]} — Llamaxy", "products.html", body, (d.get("bullets") or [p["title"]])[0][:155])
    return h.replace('<meta charset="utf-8">', '<meta charset="utf-8"><base href="../">', 1)


def build():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    (SITE / "style.css").write_text(CSS)
    shutil.copy(ROOT / "tools/shop.js", SITE / "shop.js")
    shutil.copytree(ROOT / "data/img", SITE / "img")
    shutil.copy(ROOT / "tools/font/fredoka.woff2", SITE / "fredoka.woff2")
    (SITE / "CNAME").write_text("llamaxy.com\n")
    (SITE / ".nojekyll").write_text("")

    n = len(products)
    instock = [p for p in products if p["price"]]
    featured = sorted(instock, key=lambda p: -p["qty"])[:15][::-1][:10]
    pick = {}
    for p in sorted(instock, key=lambda p: -p["qty"]):
        pick.setdefault(p["type"], p)
    hero_imgs = "".join(f'<img src="{esc(pick[t]["image"])}" alt="">' for t in ("Plush & soft toys", "Cars & vehicles", "Animals & dinos", "Collectibles") if t in pick)
    types_html = "".join(f'<a class="type" href="products.html#t={esc(n)}"><div class="c" style="background:{c}">'
                         + (f'<img src="{esc(pick[n]["image"])}" alt="">' if n in pick else '') + f'</div>{esc(n)}</a>'
                         for n, c, _ in TYPES if n in pick and n != "More toys")
    home = f"""
<div class="hero"><div class="wrap">
<div><h1>Toys they'll <em>love</em>, prices you'll like</h1>
<p>{n}+ genuine branded toys — Squishmallows, Schleich, Funko, Hot Wheels, Barbie and more. Brand-new, sealed and sent fast from the UK.</p>
<a class="btn" href="products.html">Shop all toys</a><a class="btn ghost" href="products.html#p=10">Under £10</a></div>
<div class="collage">{hero_imgs}</div>
</div></div>
<section><div class="wrap">
<h2>Shop by type</h2><p class="sub">Find the perfect toy in a couple of clicks.</p>
<div class="types">{types_html}</div>
</div></section>
<section class="band"><div class="wrap">
<h2>Popular right now</h2><p class="sub"><a href="products.html">See all toys →</a></p>
<div class="grid">{''.join(card(p) for p in featured)}</div>
</div></section>
<section><div class="wrap">
<h2>Shop by price</h2><p class="sub">Stocking fillers to big presents.</p>
<div class="prices">
<a href="products.html#p=10" style="background:var(--green)">Under £10<small>Pocket-money toys</small></a>
<a href="products.html#p=20" style="background:var(--blue)">Under £20<small>Stocking fillers</small></a>
<a href="products.html#p=40" style="background:var(--purple)">Under £40<small>Birthday presents</small></a>
<a href="products.html#p=9999" style="background:var(--red)">Big presents<small>The wow gifts</small></a>
</div></div></section>
<section class="band"><div class="wrap">
<h2>Top brands</h2><p class="sub">Official, original products from the brands kids ask for.</p>
<div class="chips">{''.join(f'<a class="chip" href="products.html?q={esc(b)}">{esc(b)}</a>' for b in top_brands)}</div>
</div></section>
<section><div class="wrap"><div class="stats">
<div class="stat"><div class="e">🚚</div><b>Free delivery</b><span>On UK orders over £40</span></div>
<div class="stat"><div class="e">⚡</div><b>Fast dispatch</b><span>Within 1–2 working days, tracked</span></div>
<div class="stat"><div class="e">↩️</div><b>14-day returns</b><span>Change of mind? No problem</span></div>
<div class="stat"><div class="e">✅</div><b>100% genuine</b><span>From authorised distributors</span></div>
</div></div></section>"""
    sup = f"""<div class="hero"><div class="wrap">
<h1>Working with {CO['name']}</h1>
<p>Information for distributors, wholesalers and brand owners who are considering opening a trade account for us.</p>
<a class="btn" href="mailto:{CO['trade']}">{CO['trade']}</a>
</div></div>
<section><div class="wrap">
<h2>How we buy</h2><p class="sub">Simple, predictable orders from a UK business customer.</p>
<div class="cols">
<div class="box"><h3>Orders</h3><p>Regular orders in full cartons and pallets. We are happy to meet your minimum order value and to start with a smaller first order.</p></div>
<div class="box"><h3>Payment</h3><p>Pro-forma payment by bank transfer (EUR or GBP) before dispatch. Credit terms only if you offer them later.</p></div>
<div class="box"><h3>Logistics</h3><p>We can collect from your warehouse (EXW/FCA) with our own freight partners, or use your carrier. We handle UK import, customs and VAT under our EORI number.</p></div>
</div></div></section>
<section style="background:#fff;border-block:1px solid var(--line)"><div class="wrap">
<h2>Our commitments to brands and distributors</h2><p class="sub">Why distributors can trust us with their brands.</p>
<div class="cols">
<div class="box"><h3>UK end consumers only</h3><p>Stock bought from you is sold only to consumers in the United Kingdom. We do not resell to other traders and do not ship back into your territory.</p></div>
<div class="box"><h3>Pricing &amp; brand rules</h3><p>We respect recommended and minimum advertised prices and the brand owner's listing and image guidelines.</p></div>
<div class="box"><h3>Compliance</h3><p>UK product safety, labelling and UK importer requirements are met for every product we sell. Documentation is kept for every shipment.</p></div>
</div></div></section>
<section><div class="wrap">
<h2>Company details for your account form</h2><p class="sub">Full details are on our <a href="about.html">company page</a>. Trade references and bank details are available on request.</p>
<div class="cols">
<div class="box"><dl class="facts">
<dt>Legal name</dt><dd>{CO['name']}</dd>
<dt>Company number</dt><dd>{CO['crn']} (England &amp; Wales)</dd>
<dt>VAT number</dt><dd>{CO['vat']}</dd>
<dt>EORI number</dt><dd>{CO['eori']}</dd>
<dt>Purchasing</dt><dd><a href="mailto:{CO['trade']}">{CO['trade']}</a></dd>
</dl></div>
<div class="box"><h3>What we are looking for</h3><p>Licensed and branded toys, games, plush, trading cards and collectibles. If you are an official distributor for brands in our range, or for brands we do not yet carry, we would like to hear from you.</p></div>
</div></div></section>"""
    (SITE / "suppliers.html").write_text(page(f"For suppliers — {CO['name']}", "suppliers.html", sup,
                                               "Trade account information for distributors and wholesalers supplying Llamaxy Limited."))

    (SITE / "index.html").write_text(page(f"{CO['name']} — Genuine Branded Toys, UK Delivery", "index.html", home,
                                          "Llamaxy Limited is a UK importer and retailer of branded toys, games and collectibles."))

    opts_c = "".join(f'<option>{esc(t)}</option>' for t, _, _ in TYPES)
    opts_b = "".join(f'<option>{esc(b)}</option>' for b in sorted(brands, key=str.lower))
    prod = f"""<section><div class="wrap">
<h2 id="h">All toys</h2><p class="sub">Genuine branded toys, games and collectibles. Free UK delivery over £40.</p>
<div class="filters"><input id="q" type="search" placeholder="Search toys or brands">
<select id="c"><option value="">All types</option>{opts_c}</select>
<select id="b"><option value="">All brands</option>{opts_b}</select>
<select id="p"><option value="">Any price</option><option value="10">Under £10</option><option value="20">Under £20</option><option value="40">Under £40</option><option value="9999">£40 and over</option></select>
<select id="o"><option value="">Recommended</option><option value="lo">Price: low to high</option><option value="hi">Price: high to low</option></select></div>
<div class="count" id="cnt"></div>
<div class="grid" id="g">{''.join(card(p) for p in products)}</div>
</div></section>
<script>
const $i=x=>document.getElementById(x),q=$i('q'),c=$i('c'),b=$i('b'),pr=$i('p'),o=$i('o'),g=$i('g'),cards=[...g.children],cnt=$i('cnt');
const inP=v=>{{const x=+v;if(!pr.value)return true;if(!x)return false;return pr.value==='9999'?x>=40:x<+pr.value}};
function f(){{const s=q.value.trim().toLowerCase();let n=0;for(const e of cards){{const ok=(!s||e.dataset.s.includes(s))&&(!c.value||e.dataset.c===c.value)&&(!b.value||e.dataset.b===b.value)&&inP(e.dataset.p);e.hidden=!ok;if(ok)n++}}
 const k=o.value,arr=k?[...cards].sort((x,y)=>{{const a=+x.dataset.p||1e9*(k==='lo'?1:-1),z=+y.dataset.p||1e9*(k==='lo'?1:-1);return k==='lo'?a-z:z-a}}):cards;arr.forEach(e=>g.append(e));
 cnt.textContent=n+' toys';$i('h').textContent=c.value||(pr.selectedIndex?pr.options[pr.selectedIndex].text:'All toys')}}
[q,c,b,pr,o].forEach(x=>x.addEventListener('input',f));
const P=new URLSearchParams(location.search),H=new URLSearchParams(location.hash.slice(1));
if(P.get('q'))q.value=P.get('q');if(H.get('t'))c.value=H.get('t');if(H.get('p'))pr.value=H.get('p');
window.addEventListener('hashchange',()=>{{const h=new URLSearchParams(location.hash.slice(1));c.value=h.get('t')||'';pr.value=h.get('p')||'';f()}});f();
</script>"""
    (SITE / "products.html").write_text(page(f"Shop all toys — Llamaxy", "products.html", prod,
                                              "Shop genuine branded toys, games and collectibles with fast UK delivery."))

    facts = f"""<dl class="facts">
<dt>Legal name</dt><dd>{CO['name']}</dd>
<dt>Company type</dt><dd>Private limited company (Ltd)</dd>
<dt>Registered in</dt><dd>England &amp; Wales</dd>
<dt>Company number</dt><dd><a href="https://find-and-update.company-information.service.gov.uk/company/{CO['crn']}" rel="noopener">{CO['crn']}</a></dd>
<dt>VAT number</dt><dd>{CO['vat']}</dd>
<dt>EORI number</dt><dd>{CO['eori']}</dd>
<dt>Director</dt><dd>{CO['director']}</dd>
<dt>Registered address</dt><dd>{esc(CO['address'])}</dd>
</dl>"""
    about = f"""<section><div class="wrap">
<h2>Company information</h2><p class="sub">Official details of {CO['name']}.</p>
<div class="cols">
<div class="box">{facts}</div>
<div class="box"><h3>About us</h3><p>{CO['name']} is an independent UK importer and retailer based in Cambridge, trading since 2021. We specialise in branded toys, games and collectibles.</p>
<p style="margin-top:12px">We sell online to consumers across the United Kingdom, with stock held in UK fulfilment centres. We are VAT registered and hold an EORI number for importing goods from the European Union. See <a href="suppliers.html">For suppliers</a> for how we work with distributors.</p>
<p style="margin-top:12px">We are always interested in building long-term relationships with authorised distributors, wholesalers and brand owners.</p></div>
</div></div></section>"""
    (SITE / "about.html").write_text(page(f"Company — {CO['name']}", "about.html", about,
                                           "Company registration, VAT and EORI details of Llamaxy Limited."))

    contact = f"""<section><div class="wrap">
<h2>Contact</h2><p class="sub">Wholesalers, distributors and brands — we'd be glad to hear from you.</p>
<div class="cols">
<div class="box"><h3>Trade enquiries</h3><p>Purchasing: <a href="mailto:{CO['trade']}">{CO['trade']}</a></p><p>General: <a href="mailto:{CO['email']}">{CO['email']}</a></p>
<p style="margin-top:12px">Please include your company name, brands/price list and minimum order requirements. We reply within one business day.</p></div>
<div class="box"><h3>Office address</h3><p>{CO['name']}<br>{esc(CO['address']).replace(', ', '<br>')}</p></div>
<div class="box"><h3>Customers</h3><p>Questions about an order or delivery: <a href="mailto:{CO['email']}">{CO['email']}</a>. Please include your order details.</p></div>
</div></div></section>"""
    (SITE / "contact.html").write_text(page(f"Contact — {CO['name']}", "contact.html", contact,
                                             "Contact Llamaxy Limited for trade enquiries."))
    privacy = f"""<section><div class="wrap">
<h2>Privacy policy</h2><p class="sub">Last updated: 9 October 2026</p>
<div class="box">
<h3>Who we are</h3><p>{CO['name']}, {esc(CO['address'])}. Contact: <a href="mailto:{CO['email']}">{CO['email']}</a>.</p>
<h3 style="margin-top:16px">This website</h3><p>This website does not use cookies or analytics. Your basket is kept only in your own browser. Card payments are taken by Stripe on its secure page; we never see your card details.</p>
<h3 style="margin-top:16px">Our internal tools and Google data</h3><p>We run a private, internal business tool used only by our own staff. With the account owner's consent it reads our own company Gmail mailboxes (Google OAuth) to find supplier invoices, delivery updates and replies to our business emails. This data is used only for running our own business, is stored on our own secured server, is never sold or shared with third parties, and is not used for advertising or to train AI models. Access can be revoked at any time at <a href="https://myaccount.google.com/permissions">myaccount.google.com/permissions</a>.</p>
<p style="margin-top:12px">Our use of information received from Google APIs adheres to the <a href="https://developers.google.com/terms/api-services-user-data-policy">Google API Services User Data Policy</a>, including the Limited Use requirements.</p>
<h3 style="margin-top:16px">Customers</h3><p>When you order on this website we receive your name, email, phone number and delivery address from the payment page. We use them only to deliver your order, send you order and tracking emails and handle returns; our UK fulfilment partner receives your name, address and phone number to deliver the parcel. Order records are kept for 6 years for tax purposes.</p>
<h3 style="margin-top:16px">Your rights</h3><p>Under UK GDPR you can ask what data we hold about you, ask us to correct or delete it, or complain to the ICO (ico.org.uk). Email us at {CO['email']}.</p>
</div></div></section>"""
    (SITE / "privacy.html").write_text(page(f"Privacy — {CO['name']}", "privacy.html", privacy,
                                             "Privacy policy of Llamaxy Limited."))
    nostock = '<p class="sub">Maximum 3 of each item per order — for larger quantities please <a href="contact.html">contact us</a>. Delivery to UK addresses only. Standard delivery £3.99, free on orders over £40. Dispatched within 1–2 working days from our UK fulfilment centre.</p>'
    basket = f"""<section><div class="wrap">
<h2>Your basket</h2>{nostock}
<div id="cart"></div></div></section>"""
    (SITE / "basket.html").write_text(page(f"Basket — {CO['name']}", "basket.html", basket, "Your basket."))
    checkout = f"""<section><div class="wrap" style="max-width:760px">
<h2>Checkout</h2>{nostock}
<div class="box"><form class="co" id="co">
<div class="w" style="grid-column:1/-1"><div id="osum"></div></div>
<p class="w" style="grid-column:1/-1;font-size:14px;color:var(--muted)">You will enter your email and delivery address on the next, secure payment page (Stripe). By placing an order you agree to our <a href="terms.html">terms of sale</a>.</p>
<button class="btn" style="grid-column:1/-1;border:0;font:inherit;font-weight:600;cursor:pointer" id="pay">Continue to secure payment</button>
</form><div id="perr"></div></div></div></section>"""
    (SITE / "checkout.html").write_text(page(f"Checkout — {CO['name']}", "checkout.html", checkout, "Checkout."))
    help_ = f"""<section><div class="wrap" style="max-width:860px">
<h2>Delivery &amp; returns</h2><p class="sub">Everything you need to know about your order.</p>
<div class="cols">
<div class="box"><h3>🚚 Delivery</h3><p>We deliver to UK addresses only. Orders are dispatched within 1–2 working days from our UK fulfilment centre and usually arrive 1–3 days later. Standard delivery is £3.99 and free on orders over £40. You'll get an email with tracking when your order ships.</p></div>
<div class="box"><h3>↩️ Returns</h3><p>Changed your mind? You can return unopened items within 14 days of delivery for a full refund. Email <a href="mailto:{CO['email']}">{CO['email']}</a> with your order details and we'll send you the return address. Faulty or damaged items are always refunded or replaced.</p></div>
<div class="box"><h3>🛒 Quantities</h3><p>To keep prices fair for everyone, you can buy up to 3 of each item. Need more for a school, club or shop? <a href="contact.html">Contact us</a>.</p></div>
<div class="box"><h3>🔒 Payment</h3><p>Payments are handled by a secure card payment provider. We never see or store your card details. Prices include VAT.</p></div>
</div></div></section>"""
    (SITE / "help.html").write_text(page(f"Delivery & returns — Llamaxy", "help.html", help_, "Delivery and returns information."))
    terms = f"""<section><div class="wrap" style="max-width:860px">
<h2>Terms of sale</h2><p class="sub">Last updated: 4 November 2026</p>
<div class="box">
<h3>Who you are buying from</h3><p>{CO['name']}, registered in England &amp; Wales No. {CO['crn']}, VAT {CO['vat']}, {esc(CO['address'])}. Email <a href="mailto:{CO['email']}">{CO['email']}</a>.</p>
<h3 style="margin-top:16px">Prices and payment</h3><p>All prices are in pounds sterling and include VAT. Delivery is £3.99, free on orders over £40. Payment is taken by card on Stripe's secure page when you place the order. Up to 3 of each item per order.</p>
<h3 style="margin-top:16px">Your order</h3><p>Our contract is made when we email your order confirmation. If an item sells out before your order is dispatched we will cancel that order, refund you in full straight away and let you know by email.</p>
<h3 style="margin-top:16px">Delivery</h3><p>UK addresses only. Orders are dispatched within 1–2 working days and usually arrive 1–3 working days later. We email your tracking number when the parcel leaves our warehouse.</p>
<h3 style="margin-top:16px">Cancelling and returns (14 days)</h3><p>Under the Consumer Contracts Regulations you can cancel your order for any reason within 14 days of receiving it. Email us within that time, then send the item back within a further 14 days; we refund the item price and the standard delivery cost within 14 days of getting it back. Items must be unused and complete. You pay the cost of returning an item unless it is faulty or not as described.</p>
<h3 style="margin-top:16px">Faulty items</h3><p>Your rights under the Consumer Rights Act 2015 are not affected. If an item is faulty, damaged or not as described, email us and we will refund or replace it, including return postage.</p>
<h3 style="margin-top:16px">Toy safety</h3><p>All toys are genuine branded products carrying the UKCA or CE mark. Please read the age warnings on each pack.</p>
</div></div></section>"""
    (SITE / "terms.html").write_text(page(f"Terms of sale — {CO['name']}", "terms.html", terms, "Terms of sale of Llamaxy Limited."))
    thanks = f"""<section><div class="wrap" style="max-width:760px;text-align:center" id="thanks">
<h2>Thank you for your order! 🎉</h2><p class="sub">Your payment went through. We have emailed your order confirmation, and we will send your tracking number as soon as the parcel leaves our warehouse (within 1–2 working days).</p>
<p><a class="btn" href="products.html">Keep shopping</a></p></div></section>"""
    (SITE / "thanks.html").write_text(page(f"Thank you — {CO['name']}", "thanks.html", thanks, "Order received."))
    (SITE / "p").mkdir()
    for p in products:
        rel = [r for r in instock if r["type"] == p["type"] and r["asin"] != p["asin"]][:4]
        (SITE / p["url"]).write_text(product_page(p, rel))
    # Checkout endpoint reads prices and stock from here, never from the browser (Apo 4 Kas 2026)
    (SITE / "prices.json").write_text(json.dumps({p["asin"]: {"p": p["price"], "t": p["title"][:120], "i": p["image"]} for p in products if p["price"]}))
    # Hidden preview with Stripe TEST payments until Apo approves (noindex, not linked anywhere)
    pv = SITE / PREVIEW
    pv.mkdir()
    (pv / "p").mkdir()
    for f in [*SITE.glob("*.html"), *SITE.glob("p/*.html")]:
        h = f.read_text().replace('<meta charset="utf-8">', '<meta charset="utf-8"><meta name="robots" content="noindex">', 1)
        h = h.replace('src="img/', 'src="../img/').replace('<script src="shop.js">', '<script>window.LLX_TEST=1</script><script src="../shop.js">')
        h = h.replace('href="style.css"', 'href="../style.css"').replace('href="fredoka.woff2"', 'href="../fredoka.woff2"')
        (pv / f.relative_to(SITE)).write_text(h)
    print(f"site/ olusturuldu: {n} urun, {len(brands)} marka")


build()
