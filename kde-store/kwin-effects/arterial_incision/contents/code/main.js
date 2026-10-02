// SPDX-FileCopyrightText: splicer scorn; harness after Burn-My-Windows by Simon Schneegans,
// Vlad Zahorodnii and Martin Flöser
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

class ArterialIncision {
  constructor() {
    effect.configChanged.connect(this.loadConfig.bind(this));
    effect.animationEnded.connect(window => forceRoles(window, false));
    effects.windowAdded.connect(this.onAdded.bind(this));
    effects.windowClosed.connect(this.onClosed.bind(this));
    effects.windowDataChanged.connect(this.onDataChanged.bind(this));
    this.shader = effect.addFragmentShader(Effect.MapTexture, 'arterial-incision.frag');
    this.loadConfig();
  }

  loadConfig() {
    this.duration = animationTime(effect.readConfig('Duration', 900));
    effect.setUniform(this.shader, 'uDuration', this.duration * 0.001);
    effect.setUniform(this.shader, 'uEdgeWidth', effect.readConfig('EdgeWidth', 2.0));
    effect.setUniform(this.shader, 'uTear', effect.readConfig('Tear', 1.0));
    effect.setUniform(this.shader, 'uColor', readRGBA('Color', '#e01b1b'));
  }

  run(window, opening) {
    forceRoles(window, true);
    effect.setUniform(this.shader, 'uForOpening', opening ? 1.0 : 0.0);
    effect.setUniform(this.shader, 'uIsFullscreen', window.fullScreen ? 1.0 : 0.0);
    effect.setUniform(this.shader, 'uSeed', Math.random());
    return animate({
      window: window,
      curve: QEasingCurve.Linear,
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

  onAdded(window) {
    window.arterialBorn = Date.now();
    if (effects.hasActiveFullScreenEffect || !shouldAnimate(window) || !window.visible) {
      return;
    }
    if (effect.isGrabbed(window, Effect.WindowAddedGrabRole)) {
      return;
    }
    window.arterialIn = this.run(window, true);
  }

  onClosed(window) {
    if (effects.hasActiveFullScreenEffect || !shouldAnimate(window)) {
      return;
    }
    if (!window.visible || window.skipsCloseAnimation) {
      return;
    }
    if (effect.isGrabbed(window, Effect.WindowClosedGrabRole)) {
      return;
    }
    if (window.arterialIn) {
      cancel(window.arterialIn);
      delete window.arterialIn;
    }
    window.arterialOut = this.run(window, false);
  }

  onDataChanged(window, role) {
    const key = role == Effect.WindowAddedGrabRole ? 'arterialIn' :
                role == Effect.WindowClosedGrabRole ? 'arterialOut' : null;
    if (key && window[key] && effect.isGrabbed(window, role)) {
      cancel(window[key]);
      delete window[key];
      forceRoles(window, false);
    }
  }
}

new ArterialIncision();
