#!/usr/bin/env bash
# Assemble ready-to-upload KDE Store packages from dist/. Run build.py first.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
[ -d "$HERE/dist" ] || python3 "$HERE/build.py"
D="$HERE/dist"; K="$HERE/kde-store"

sync() { rm -rf "$2"; mkdir -p "$(dirname "$2")"; cp -a "$1" "$2"; }

sync "$D/share/color-schemes/Arterial.colors"       "$K/color-scheme/Arterial.colors"
sync "$D/share/aurorae/themes/Arterial"             "$K/aurorae/Arterial"
sync "$D/share/plasma/desktoptheme/Arterial"        "$K/plasma-style/Arterial"
sync "$D/config/Kvantum/Arterial"                   "$K/kvantum/Arterial"
sync "$D/share/kwin/effects/arterial_incision"      "$K/kwin-effects/arterial_incision"
sync "$D/share/kwin/effects/arterial_pulse"         "$K/kwin-effects/arterial_pulse"
sync "$D/share/konsole/Arterial.colorscheme"        "$K/konsole/Arterial.colorscheme"
sync "$D/config/kitty/arterial.conf"                "$K/terminal-extras/kitty/arterial.conf"
sync "$D/config/mako/config"                        "$K/terminal-extras/mako/config"
echo "packaged into $K"
