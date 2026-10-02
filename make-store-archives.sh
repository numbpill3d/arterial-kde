#!/usr/bin/env bash
# Build ready-to-upload KDE Store archives (one .tar.gz per part) + screenshots.
# Usage: ./make-store-archives.sh [OUTPUT_DIR]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$HOME/Documents/Arterial KDE Store}"
[ -d "$HERE/kde-store/aurorae/Arterial" ] || "$HERE/package.sh"
K="$HERE/kde-store"
rm -rf "$OUT"; mkdir -p "$OUT"

# deterministic, clean archives (no uid/gid/mtime noise)
pack() { # pack <srcdir> <item-to-include> <out.tar.gz>
  tar --sort=name --owner=0 --group=0 --numeric-owner --mtime='2026-01-01 00:00:00' \
      -czf "$3" -C "$1" "$2"
}

part() { # part <name> <store-category>
  mkdir -p "$OUT/$1"
  cp "$K/$1"/README.md "$OUT/$1/description.md" 2>/dev/null || true
  cp "$K/$1"/preview*.png "$OUT/$1/" 2>/dev/null || true
  printf '%s\n' "$2" > "$OUT/$1/KDE-STORE-CATEGORY.txt"
}

part color-scheme "Plasma 6 › Plasma Color Schemes"
pack "$K/color-scheme" Arterial.colors            "$OUT/color-scheme/Arterial-color-scheme.tar.gz"

part aurorae "Plasma 6 › Window Decorations (Aurorae)"
pack "$K/aurorae" Arterial                         "$OUT/aurorae/Arterial-aurorae.tar.gz"

part plasma-style "Plasma 6 › Plasma Styles"
pack "$K/plasma-style" Arterial                     "$OUT/plasma-style/Arterial-plasma-style.tar.gz"

part kvantum "Plasma 6 › Kvantum Themes"
pack "$K/kvantum" Arterial                          "$OUT/kvantum/Arterial-kvantum.tar.gz"

part kwin-effects "Plasma 6 › KWin Effects"
pack "$K/kwin-effects" arterial_incision            "$OUT/kwin-effects/arterial_incision.tar.gz"
pack "$K/kwin-effects" arterial_pulse               "$OUT/kwin-effects/arterial_pulse.tar.gz"

part konsole "(not a KDE Store category — Konsole color scheme)"
pack "$K/konsole" Arterial.colorscheme              "$OUT/konsole/Arterial-konsole.tar.gz"

part terminal-extras "(not a KDE Store category — kitty + mako)"
tar --sort=name --owner=0 --group=0 --numeric-owner --mtime='2026-01-01 00:00:00' \
    -czf "$OUT/terminal-extras/Arterial-terminal-extras.tar.gz" \
    -C "$K/terminal-extras" kitty mako

cp "$HERE/screenshots/overview.png" "$OUT/overview.png"
cat > "$OUT/README.txt" <<'TXT'
Arterial — KDE Store upload kit
By splicer scorn (voidrane). GPL-3.0-or-later.

One folder per part. In each:
  *.tar.gz                 the exact archive to upload
  preview*.png             screenshot(s) for the listing
  description.md           text for the store description box
  KDE-STORE-CATEGORY.txt   which category to post it under

Upload at https://store.kde.org (Add Product). Pick the category named in
KDE-STORE-CATEGORY.txt, attach the .tar.gz, and add the preview image(s).

To verify an archive's contents:  tar tzf <file>.tar.gz
TXT
echo "built upload kit in: $OUT"
