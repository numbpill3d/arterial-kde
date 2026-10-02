// SPDX-FileCopyrightText: splicer scorn
// SPDX-License-Identifier: GPL-3.0-or-later

'use strict';

function readRGBA(key, fallback) {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})?([a-f\d]{2})?$/i.exec(
    String(effect.readConfig(key, fallback)));
  if (!m) {
    return [0.7, 0.0, 0.0, 1.0];
  }
  const c = m.slice(1).filter(x => x !== undefined).map(x => parseInt(x, 16) / 255);
  return c.length == 3 ? [c[0], c[1], c[2], 1.0] : [c[1], c[2], c[3], c[0]];
}

const blacklist = [
  'ksmserver ksmserver', 'ksmserver-logout-greeter ksmserver-logout-greeter',
  'ksplashqml ksplashqml'
];

// Window filter adapted from Burn-My-Windows (Simon Schneegans, Vlad Zahorodnii,
// Martin Flöser), GPL-3.0-or-later.
function shouldAnimate(window) {
  if (window.windowClass == 'plasmashell plasmashell' ||
      window.windowClass == 'plasmashell org.kde.plasmashell') {
    return window.hasDecoration;
  }
  if (!window.hasDecoration && window.onAllDesktops) {
    return false;
  }
  if (blacklist.indexOf(window.windowClass) != -1) {
    return false;
  }
  if (window.hasDecoration) {
    return true;
  }
  if (window.popupWindow || window.lockScreen || window.outline || !window.managed) {
    return false;
  }
  return window.normalWindow || window.dialog;
}

function forceRoles(window, on) {
  window.setData(Effect.WindowForceBackgroundContrastRole, on ? true : null);
  window.setData(Effect.WindowForceBlurRole, on ? true : null);
}

class ArterialPulse {
  constructor() {
    effect.configChanged.connect(this.loadConfig.bind(this));
    effect.animationEnded.connect(this.onEnded.bind(this));
    effects.windowAdded.connect(window => { window.arterialBorn = Date.now(); });
    effects.windowActivated.connect(this.onActivated.bind(this));
    this.shader = effect.addFragmentShader(Effect.MapTexture, 'arterial-pulse.frag');
    this.loadConfig();
  }

  loadConfig() {
    this.duration = animationTime(effect.readConfig('Duration', 600));
    effect.setUniform(this.shader, 'uEdgeWidth', effect.readConfig('EdgeWidth', 2.0));
    effect.setUniform(this.shader, 'uColor', readRGBA('Color', '#e01b1b'));
  }

  onActivated(window) {
    if (!window || effects.hasActiveFullScreenEffect || !shouldAnimate(window)) {
      return;
    }
    if (!window.visible || window.minimized || window.fullScreen) {
      return;
    }
    // A freshly opened window is already being cut open by the incision effect.
    if (window.arterialBorn && Date.now() - window.arterialBorn < 1200) {
      return;
    }
    if (window.arterialPulse) {
      cancel(window.arterialPulse);
      delete window.arterialPulse;
    }
    forceRoles(window, true);
    effect.setUniform(this.shader, 'uForOpening', 1.0);
    effect.setUniform(this.shader, 'uIsFullscreen', 0.0);
    window.arterialPulse = animate({
      window: window,
      curve: QEasingCurve.OutQuad,
      duration: this.duration,
      animations: [{
        type: Effect.ShaderUniform,
        fragmentShader: this.shader,
        uniform: 'uProgress',
        from: 0.0,
        to: 1.0
      }]
    });
  }

  onEnded(window) {
    forceRoles(window, false);
    delete window.arterialPulse;
  }
}

new ArterialPulse();
