# Arterial — Kvantum Theme

Qt widget styling via Kvantum: red selection, red-edged inputs and lists, dark-grey
buttons. The widget map descends from KvArcDark (by Tsu Jan, Kvantum project), recoloured
for Arterial; upstream GPL notices are kept in `Arterial/`.

![kvantum preview](preview.png)

## Install

    mkdir -p ~/.config/Kvantum/Arterial
    cp -r Arterial/* ~/.config/Kvantum/Arterial/
    printf '[General]\ntheme=Arterial\n' > ~/.config/Kvantum/kvantum.kvconfig
    kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle kvantum

Or pick **Arterial** in `kvantummanager`. Running Qt apps need a restart.

## KDE Store

Category: **Plasma 6 › Kvantum Themes**. Zip the `Arterial/` folder, upload with a preview.

By splicer scorn (voidrane). GPL-3.0-or-later. Based on KvArcDark (GPL-3.0-or-later).
