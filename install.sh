#!/usr/bin/env bash
# Arterial — install + apply. Re-runnable. Undo with ./revert.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
[ -d "$HERE/dist" ] || python3 "$HERE/build.py"

echo "· copying assets"
cp -a "$HERE/dist/share/." "$HOME/.local/share/"
mkdir -p "$HOME/.config/Kvantum" "$HOME/.config/kitty"
cp -a "$HERE/dist/config/Kvantum/Arterial" "$HOME/.config/Kvantum/"
cp -a "$HERE/dist/config/kitty/arterial.conf" "$HOME/.config/kitty/"

# The apply tools skip a name that is already active, so a rebuilt Arterial has to be
# bounced through another theme to be re-read.
echo "· colour scheme"
[ "$(kreadconfig6 --file kdeglobals --group General --key ColorScheme)" = Arterial ] \
  && plasma-apply-colorscheme BreezeDark >/dev/null || true
plasma-apply-colorscheme Arterial >/dev/null || true

echo "· window decoration"
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.kwin.aurorae.v2
if [ "$(kreadconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme)" = __aurorae__svg__Arterial ]; then
  kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme __aurorae__svg__ObsidianSigil
  qdbus6 org.kde.KWin /KWin reconfigure >/dev/null; sleep 1
fi
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme __aurorae__svg__Arterial
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key BorderSize Normal
kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key BorderSizeAuto false

echo "· widget style (Kvantum)"
printf '[General]\ntheme=Arterial\n' > "$HOME/.config/Kvantum/kvantum.kvconfig"
kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle kvantum

echo "· plasma style"
rm -rf "$HOME"/.cache/plasma_theme_Arterial* "$HOME"/.cache/plasma-svgelements* "$HOME"/.cache/ksvg-elements* 2>/dev/null || true
[ "$(kreadconfig6 --file plasmarc --group Theme --key name)" = Arterial ] \
  && plasma-apply-desktoptheme default >/dev/null || true
plasma-apply-desktoptheme Arterial >/dev/null || true

echo "· kwin effects (installed but OFF by default — opt in below)"
# The effects are installed, not auto-enabled: shader effects are GPU-heavy on
# integrated graphics and own the exclusive window open/close slot. Enable them
# yourself in System Settings > Desktop Effects, or:
#   kwriteconfig6 --file kwinrc --group Plugins --key kwin6_effect_doomEnabled false
#   kwriteconfig6 --file kwinrc --group Plugins --key arterial_incisionEnabled true
#   kwriteconfig6 --file kwinrc --group Plugins --key arterial_pulseEnabled true
#   qdbus6 org.kde.KWin /KWin reconfigure
kwriteconfig6 --file kwinrc --group Plugins --key arterial_incisionEnabled false
kwriteconfig6 --file kwinrc --group Plugins --key arterial_pulseEnabled false
qdbus6 org.kde.KWin /KWin reconfigure >/dev/null

echo "· terminals"
grep -qx 'include arterial.conf' "$HOME/.config/kitty/kitty.conf" 2>/dev/null \
  || printf '\n# ── arterial palette (remove this line to go back) ──\ninclude arterial.conf\n' >> "$HOME/.config/kitty/kitty.conf"
PROFILE="$(kreadconfig6 --file konsolerc --group 'Desktop Entry' --key DefaultProfile)"
[ -n "$PROFILE" ] && [ -f "$HOME/.local/share/konsole/$PROFILE" ] \
  && kwriteconfig6 --file "$HOME/.local/share/konsole/$PROFILE" --group Appearance --key ColorScheme Arterial

if command -v makoctl >/dev/null; then
  echo "· notifications (mako)"
  if [ ! -e "$HOME/.config/mako/config" ] || grep -q '^# Arterial' "$HOME/.config/mako/config"; then
    mkdir -p "$HOME/.config/mako" && cp -a "$HERE/dist/config/mako/config" "$HOME/.config/mako/config"
    makoctl reload >/dev/null 2>&1 || true
  else
    echo "  existing mako config left alone; see dist/config/mako/config"
  fi
fi

echo "done — restart Qt apps to pick up Kvantum; new Konsole/kitty windows get the palette."
