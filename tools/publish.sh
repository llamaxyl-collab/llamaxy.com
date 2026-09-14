#!/bin/zsh
# Urunleri Amazon'dan cek, siteyi uret, GitHub Pages'e yukle
# Kullanim: tools/publish.sh            (urunleri de gunceller)
#           tools/publish.sh --no-fetch (sadece site degisikligi)
set -e
cd "$(dirname "$0")/.."
export PATH=~/.local/bin:$PATH
[[ "$1" == "--no-fetch" ]] || python3 tools/fetch_products.py
python3 tools/build.py
git add -A
git commit -qm "Update site $(date +%F)" || true
git push -q origin main
# site/ agacini gh-pages'in ustune yeni commit olarak ekle (force push yok)
git fetch -q origin gh-pages
tree=$(git rev-parse HEAD:site)
if [[ "$tree" != "$(git rev-parse origin/gh-pages^{tree})" ]]; then
  c=$(git commit-tree "$tree" -p origin/gh-pages -m "Publish $(date +%F)")
  git push -q origin "$c":refs/heads/gh-pages
fi
echo "Yayinlandi: https://llamaxy.com"
