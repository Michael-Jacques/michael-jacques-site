#!/usr/bin/env bash
# Rebuild the site and push it live.
#
#   ./publish.sh                  rebuild, commit, push
#   ./publish.sh "raised prices"  same, with your own commit message
#   ./publish.sh --images         also reprocess photos in assets/src first
#
# GitHub Pages redeploys on its own once the push lands, usually within a minute.
set -euo pipefail
cd "$(dirname "$0")"

MSG=""
DO_IMAGES=0
for arg in "$@"; do
  case "$arg" in
    --images) DO_IMAGES=1 ;;
    *) MSG="$arg" ;;
  esac
done

if [ "$DO_IMAGES" = "1" ]; then
  echo "→ processing photos"
  python3 tools/process_images.py
fi

echo "→ building"
python3 build.py

if [ -z "$(git status --porcelain)" ]; then
  echo "✓ nothing changed — site is already up to date"
  exit 0
fi

echo
git status --short | sed 's/^/   /'
echo

git add -A
git commit -q -m "${MSG:-Update site}"

echo "→ pushing"
git pull -q --rebase origin main
git push -q origin main

echo "✓ pushed. live in about a minute at https://www.michael-jacques.com"
echo "  build status: gh api repos/Michael-Jacques/michael-jacques-site/pages --jq .status"
