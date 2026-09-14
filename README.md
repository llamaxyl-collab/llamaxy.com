# llamaxy.com

Statik şirket/katalog sitesi (satış yok, form yok, cookie yok).

Güncelleme:
    python3 tools/fetch_products.py   # Amazon SP-API'den aktif ürünler -> data/products.json
    python3 tools/build.py            # site/ klasörünü üretir
