#!/usr/bin/env bash
# Publish the website to GitHub Pages (https://mtaimourz.github.io/pale-blue-flame/).
# Builds the static version (no backend, no API key) and pushes it to the gh-pages branch, which Pages serves.
# Uses your normal git credentials for the repo. Run from anywhere:  webapp/scripts/deploy-pages.sh
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"            # webapp/
remote="$(git -C "$here" remote get-url origin)"
cd "$here"
VITE_STATIC=1 npm run build
touch dist/.nojekyll                                # serve files as they are
tmp="$(mktemp -d)"
cp -R dist/. "$tmp/"
cd "$tmp"
git init -q -b gh-pages
git add -A
git commit -q -m "site build $(date -u +%Y-%m-%dT%H:%MZ)"
git push -f "$remote" gh-pages
rm -rf "$tmp"
echo "published: https://mtaimourz.github.io/pale-blue-flame/ (Pages takes a minute or two to update)"
