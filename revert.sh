#!/usr/bin/env bash
# Arterial — restore the configs saved before the first install.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
B="${1:-$(cat "$HERE/.last-backup")}"
[ -d "$B/config" ] || { echo "no backup at $B"; exit 1; }
echo "· restoring from $B"
# Apply the old scheme and style first: the tools do nothing once the config already names them.
plasma-apply-colorscheme "$(kreadconfig6 --file "$B/config/kdeglobals" --group General --key ColorScheme)" >/dev/null || true
plasma-apply-desktoptheme "$(kreadconfig6 --file "$B/config/plasmarc" --group Theme --key name)" >/dev/null || true
for f in kdeglobals kwinrc plasmarc kcminputrc kitty/kitty.conf; do
  [ -e "$B/config/$f" ] && cp -a "$B/config/$f" "$HOME/.config/$f"
done
rm -f "$HOME/.config/Kvantum/kvantum.kvconfig"
[ -e "$B/config/Kvantum/kvantum.kvconfig" ] && cp -a "$B/config/Kvantum/kvantum.kvconfig" "$HOME/.config/Kvantum/"
cp -a "$B"/konsole/*.profile "$HOME/.local/share/konsole/" 2>/dev/null || true
if grep -q '^# Arterial' "$HOME/.config/mako/config" 2>/dev/null; then rm -f "$HOME/.config/mako/config"; makoctl reload >/dev/null 2>&1 || true; fi
qdbus6 org.kde.KWin /KWin reconfigure >/dev/null
for e in arterial_incision arterial_pulse; do
  qdbus6 org.kde.KWin /Effects org.kde.kwin.Effects.unloadEffect "$e" >/dev/null || true
done
qdbus6 org.kde.KWin /Effects org.kde.kwin.Effects.loadEffect kwin6_effect_doom >/dev/null || true
echo "reverted. Arterial's files stay installed; pick it again from System Settings or ./install.sh"
