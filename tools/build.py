"""data/products.json + sirket bilgileri -> site/ (statik HTML)
Kullanim: python3 tools/build.py
"""
import html, json, shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DATA = json.loads((ROOT / "data/products.json").read_text())

CO = {
    "name": "Llamaxy Limited",
    "email": "info@llamaxy.com",
    "trade": "trade@llamaxy.com",
    "address": "122 Hawkins Road, Cambridge, CB4 2RD, United Kingdom",
    "crn": "13143085",
    "vat": "GB435877456",
    "eori": "GB078550584000",
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
products = DATA["products"]
for p in products:
    p["cat"] = CAT.get(p["category"], "Other")
cats = Counter(p["cat"] for p in products)
cat_rank = {c: i for i, (c, _) in enumerate(cats.most_common())}
products.sort(key=lambda p: (p["cat"] == "Other", cat_rank[p["cat"]], p["brand"].lower(), p["title"].lower()))
brands = Counter(p["brand"] for p in products if p["brand"])
# Ana sayfada sadece tanınan oyuncak/koleksiyon markaları (rastgele ev/giyim markaları güven vermiyor)
SHOW_BRANDS = ["Squishmallows", "Schleich", "Funko", "Mattel", "Hasbro", "Hot Wheels", "Barbie", "Nerf",
               "Transformers", "Star Wars", "Masters of the Universe", "Miraculous", "Jazwares", "Jurassic World",
               "Polly Pocket", "Disney", "Marvel", "Playmobil", "Ravensburger", "Simba", "Bizak", "Geomag",
               "Yu-Gi-Oh!", "BANDAI", "Mini Brands", "My Little Pony", "Weta Workshop", "Just Play"]
toy_brands = Counter(p["brand"] for p in products if p["cat"] == "Toys & Games" and p["brand"])
top_brands = [b for b in SHOW_BRANDS if toy_brands.get(b)]

CSS = """
:root{--ink:#14213d;--muted:#5b6475;--line:#e3e6ec;--bg:#f7f8fa;--card:#fff;--accent:#e07a1f;--accent-d:#b8600f}
*{box-sizing:border-box}
body{margin:0;display:flex;flex-direction:column;min-height:100vh;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}
a{color:inherit}
.wrap{max-width:1160px;margin:0 auto;padding-inline:20px}
header{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:10}
header .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;min-height:64px;flex-wrap:wrap}
.logo{font-weight:800;font-size:22px;letter-spacing:-.02em;text-decoration:none}
.logo span{color:var(--accent)}
nav{display:flex;gap:22px;flex-wrap:wrap}
nav a{text-decoration:none;color:var(--muted);font-weight:500;font-size:15px}
nav a:hover,nav a.on{color:var(--ink)}
.hero{background:linear-gradient(135deg,#14213d 0%,#23365f 100%);color:#fff;padding-block:72px}
.hero h1{font-size:clamp(30px,5vw,48px);line-height:1.15;margin:0 0 16px;letter-spacing:-.02em;max-width:760px}
.hero p{font-size:18px;color:#c9d1e3;max-width:680px;margin:0 0 28px}
.btn{display:inline-block;background:var(--accent);color:#fff;text-decoration:none;padding:12px 22px;border-radius:8px;font-weight:600}
.btn:hover{background:var(--accent-d)}
.btn.ghost{background:transparent;border:1px solid #6d7a99;margin-left:8px}
section{padding-block:56px}
h2{font-size:28px;margin:0 0 8px;letter-spacing:-.01em}
.sub{color:var(--muted);margin:0 0 28px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-top:-36px}
.stat{background:#fff;border:1px solid var(--line);border-radius:12px;padding:20px}
.stat b{display:block;font-size:28px}
.stat span{color:var(--muted);font-size:14px}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px}
.box{background:#fff;border:1px solid var(--line);border-radius:12px;padding:24px}
.box h3{margin:0 0 6px;font-size:18px}
.box p{margin:0;color:var(--muted)}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{background:#fff;border:1px solid var(--line);border-radius:999px;padding:6px 14px;font-size:14px}
dl.facts{display:grid;grid-template-columns:max-content 1fr;gap:10px 24px;margin:0}
dl.facts dt{color:var(--muted)}
dl.facts dd{margin:0;font-weight:500;overflow-wrap:anywhere}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden;display:flex;flex-direction:column}
.card .img{aspect-ratio:1;display:flex;align-items:center;justify-content:center;padding:14px;background:#fff}
.card img{max-width:100%;max-height:100%;object-fit:contain}
.card .t{padding:10px 14px 14px;border-top:1px solid var(--line);font-size:13px;flex:1;display:flex;flex-direction:column;gap:4px}
.card .b{font-size:12px;color:var(--accent-d);font-weight:600;text-transform:uppercase;letter-spacing:.03em}
.card .n{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.card .a{font-size:11px;color:var(--muted);margin-top:auto}
.filters{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px}
.filters input,.filters select{font:inherit;padding:10px 12px;border:1px solid var(--line);border-radius:8px;background:#fff;min-width:0;flex:1 1 200px}
.note{background:#fff7ec;border:1px solid #f3d6b3;border-radius:10px;padding:12px 16px;font-size:14px;color:#6b4a1f;margin-bottom:20px}
.count{color:var(--muted);font-size:14px;margin-bottom:12px}
footer{margin-top:auto;background:#0f1a30;color:#aab3c7;padding-block:40px;font-size:14px}
footer .wrap{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:24px}
footer b{color:#fff}
footer a{color:#fff}
"""


def page(title, active, body, desc):
    links = [("index.html", "Home"), ("products.html", "Products"), ("suppliers.html", "For suppliers"), ("about.html", "Company"), ("contact.html", "Contact")]
    nav = "".join(f'<a href="{h}"{" class=on" if h == active else ""}>{t}</a>' for h, t in links)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='%2314213d'/><text x='50' y='70' font-size='62' text-anchor='middle' fill='%23e07a1f' font-family='Arial' font-weight='bold'>L</text></svg>">
<link rel="stylesheet" href="style.css"></head><body>
<header><div class="wrap"><a class="logo" href="index.html">Llamaxy<span>.</span></a><nav>{nav}</nav></div></header>
{body}
<footer><div class="wrap">
<div><b>{CO['name']}</b><br>Registered in England &amp; Wales<br>Company No. {CO['crn']}<br>VAT No. {CO['vat']}</div>
<div><b>Office address</b><br>{esc(CO['address'])}</div>
<div><b>Contact</b><br>Trade: <a href="mailto:{CO['trade']}">{CO['trade']}</a><br><a href="mailto:{CO['email']}">{CO['email']}</a></div>
</div><div class="wrap" style="display:block;margin-top:24px">© {DATA['updated'][:4]} {CO['name']}. · <a href="privacy.html">Privacy</a></div></footer>
</body></html>"""


def card(p):
    return (f'<div class="card" data-c="{esc(p["cat"])}" data-b="{esc(p["brand"])}" data-s="{esc((p["title"] + " " + p["brand"]).lower())}">'
            f'<div class="img"><img loading="lazy" src="{esc(p["image"])}" alt="{esc(p["title"][:90])}"></div>'
            f'<div class="t"><div class="b">{esc(p["brand"])}</div><div class="n">{esc(p["title"])}</div>'
            '</div></div>')


def build():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    (SITE / "style.css").write_text(CSS)
    (SITE / "CNAME").write_text("llamaxy.com\n")
    (SITE / ".nojekyll").write_text("")

    n = len(products)
    featured = [p for p in products if p["cat"] == "Toys & Games"][::max(1, cats["Toys & Games"] // 10)][:10]
    home = f"""
<div class="hero"><div class="wrap">
<h1>UK importer and retailer of branded toys, games and collectibles</h1>
<p>{CO['name']} is a VAT-registered company in Cambridge. We buy genuine branded stock from authorised distributors across Europe, import it into the United Kingdom under our own EORI number and sell it to consumers in the UK.</p>
<a class="btn" href="suppliers.html">For suppliers</a><a class="btn ghost" href="products.html">View our range</a>
</div></div>
<div class="wrap"><div class="stats">
<div class="stat"><b>{n}+</b><span>Products currently listed</span></div>
<div class="stat"><b>{len(brands)}</b><span>Brands in our catalogue</span></div>
<div class="stat"><b>UK only</b><span>We sell to UK end consumers</span></div>
<div class="stat"><b>Since 2021</b><span>UK limited company</span></div>
</div></div>
<section><div class="wrap">
<h2>What we do</h2><p class="sub">We buy from authorised sources and sell to end consumers in the UK.</p>
<div class="cols">
<div class="box"><h3>Import &amp; purchasing</h3><p>We buy brand-new stock from authorised distributors in the EU and UK in carton and pallet quantities, pay by bank transfer and arrange collection, freight and UK customs clearance ourselves.</p></div>
<div class="box"><h3>UK retail</h3><p>We sell to consumers across the United Kingdom through established online retail channels, led by Amazon.co.uk with stock held in UK fulfilment centres for fast delivery and full customer service.</p></div>
<div class="box"><h3>Brand-safe selling</h3><p>Only new, original products with correct EAN barcodes. We follow manufacturer pricing and brand guidelines, never resell to other traders and comply with UK product safety rules.</p></div>
</div></div></section>
<section style="background:#fff;border-block:1px solid var(--line)"><div class="wrap">
<h2>Brands we carry</h2><p class="sub">A selection of brands currently in our catalogue.</p>
<div class="chips">{''.join(f'<span class="chip">{esc(b)}</span>' for b in top_brands)}</div>
</div></section>
<section><div class="wrap">
<h2>Categories</h2><p class="sub">Our main focus is toys &amp; games.</p>
<div class="chips">{''.join(f'<a class="chip" style="text-decoration:none" href="products.html#{esc(c)}">{esc(c)} · {k}</a>' for c, k in cats.most_common() if c != "Other")}</div>
<h2 style="margin-top:48px">Selected products</h2><p class="sub"><a href="products.html">See all {n} products →</a></p>
<div class="grid">{''.join(card(p) for p in featured)}</div>
</div></section>"""
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

    (SITE / "index.html").write_text(page(f"{CO['name']} — UK Importer & Retailer of Toys", "index.html", home,
                                          "Llamaxy Limited is a UK importer and retailer of branded toys, games and collectibles."))

    opts_c = "".join(f'<option>{esc(c)}</option>' for c, _ in cats.most_common())
    opts_b = "".join(f'<option>{esc(b)}</option>' for b in sorted(brands, key=str.lower))
    prod = f"""<section><div class="wrap">
<h2>Our product range</h2><p class="sub">Products currently listed for sale on Amazon.co.uk. Updated {DATA['updated']}.</p>
<div class="filters"><input id="q" type="search" placeholder="Search product or brand">
<select id="c"><option value="">All categories</option>{opts_c}</select>
<select id="b"><option value="">All brands</option>{opts_b}</select></div>
<div class="count" id="cnt"></div>
<div class="grid" id="g">{''.join(card(p) for p in products)}</div>
</div></section>
<script>
const q=document.getElementById('q'),c=document.getElementById('c'),b=document.getElementById('b'),cards=[...document.querySelectorAll('#g .card')],cnt=document.getElementById('cnt');
function f(){{const s=q.value.trim().toLowerCase();let n=0;for(const e of cards){{const ok=(!s||e.dataset.s.includes(s))&&(!c.value||e.dataset.c===c.value)&&(!b.value||e.dataset.b===b.value);e.hidden=!ok;if(ok)n++}}cnt.textContent=n+' products'}}
[q,c,b].forEach(x=>x.addEventListener('input',f));
const h=decodeURIComponent(location.hash.slice(1));if(h&&[...c.options].some(o=>o.value===h))c.value=h;f();
</script>"""
    (SITE / "products.html").write_text(page(f"Products — {CO['name']}", "products.html", prod,
                                              "Product catalogue of Llamaxy Limited."))

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
<p style="margin-top:12px">We sell to consumers across the United Kingdom, mainly through Amazon.co.uk with stock held in UK fulfilment centres. We are VAT registered and hold an EORI number for importing goods from the European Union. See <a href="suppliers.html">For suppliers</a> for how we work with distributors.</p>
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
<div class="box"><h3>Consumers</h3><p>For orders placed on Amazon, please contact us through your Amazon account (Your Orders → Contact seller).</p></div>
</div></div></section>"""
    (SITE / "contact.html").write_text(page(f"Contact — {CO['name']}", "contact.html", contact,
                                             "Contact Llamaxy Limited for trade enquiries."))
    privacy = f"""<section><div class="wrap">
<h2>Privacy policy</h2><p class="sub">Last updated: 9 October 2026</p>
<div class="box">
<h3>Who we are</h3><p>{CO['name']}, {esc(CO['address'])}. Contact: <a href="mailto:{CO['email']}">{CO['email']}</a>.</p>
<h3 style="margin-top:16px">This website</h3><p>This website does not use cookies, analytics or contact forms and does not collect personal data from visitors.</p>
<h3 style="margin-top:16px">Our internal tools and Google data</h3><p>We run a private, internal business tool used only by our own staff. With the account owner's consent it reads our own company Gmail mailboxes (Google OAuth) to find supplier invoices, delivery updates and replies to our business emails. This data is used only for running our own business, is stored on our own secured server, is never sold or shared with third parties, and is not used for advertising or to train AI models. Access can be revoked at any time at <a href="https://myaccount.google.com/permissions">myaccount.google.com/permissions</a>.</p>
<p style="margin-top:12px">Our use of information received from Google APIs adheres to the <a href="https://developers.google.com/terms/api-services-user-data-policy">Google API Services User Data Policy</a>, including the Limited Use requirements.</p>
<h3 style="margin-top:16px">Customers</h3><p>Orders placed on Amazon are handled under Amazon's privacy notice. We only use order details to fulfil and support those orders.</p>
<h3 style="margin-top:16px">Your rights</h3><p>Under UK GDPR you can ask what data we hold about you, ask us to correct or delete it, or complain to the ICO (ico.org.uk). Email us at {CO['email']}.</p>
</div></div></section>"""
    (SITE / "privacy.html").write_text(page(f"Privacy — {CO['name']}", "privacy.html", privacy,
                                             "Privacy policy of Llamaxy Limited."))
    print(f"site/ olusturuldu: {n} urun, {len(brands)} marka")


build()
