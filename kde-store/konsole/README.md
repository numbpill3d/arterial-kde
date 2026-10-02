# Arterial — Konsole Color Scheme

Black background, ghost-grey text, blood-red ANSI palette.

![konsole](preview.png)

## Install

    mkdir -p ~/.local/share/konsole
    cp Arterial.colorscheme ~/.local/share/konsole/

Then set it in your Konsole profile (Settings → Edit Profile → Appearance → **Arterial**),
or on the command line:

    kwriteconfig6 --file ~/.local/share/konsole/<Profile>.profile \
      --group Appearance --key ColorScheme Arterial

By splicer scorn (voidrane). GPL-3.0-or-later.
