#!/bin/zsh
# Urunleri Amazon'dan cek, siteyi uret, GitHub Pages'e yukle
set -e
cd "$(dirname "$0")/.."
export PATH=~/.local/bin:$PATH
python3 tools/fetch_products.py
python3 tools/build.py
git add -A
git commit -qm "Update products $(date +%F)" || true
git push -q origin main
git push -q -f origin "$(git subtree split --prefix site main)":refs/heads/gh-pages
echo "Yayinlandi: https://llamaxy.com"
