/**
 * Modern renk seçici: doygunluk/parlaklık alanı + ton kaydırıcısı + hex.
 */
(function () {
  function clamp(n, min, max) {
    return Math.min(max, Math.max(min, n));
  }

  function hslToHex(h, s, l) {
    s /= 100;
    l /= 100;
    const a = s * Math.min(l, 1 - l);
    const f = (n) => {
      const k = (n + h / 30) % 12;
      const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
      return Math.round(255 * color)
        .toString(16)
        .padStart(2, '0');
    };
    return `#${f(0)}${f(8)}${f(4)}`;
  }

  function hexToHsl(hex) {
    const r = parseInt(hex.slice(1, 3), 16) / 255;
    const g = parseInt(hex.slice(3, 5), 16) / 255;
    const b = parseInt(hex.slice(5, 7), 16) / 255;
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h = 0;
    let s = 0;
    const l = (max + min) / 2;
    if (max !== min) {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r:
          h = ((g - b) / d + (g < b ? 6 : 0)) * 60;
          break;
        case g:
          h = ((b - r) / d + 2) * 60;
          break;
        default:
          h = ((r - g) / d + 4) * 60;
      }
    }
    return { h, s: s * 100, l: l * 100 };
  }

  function normalizeHex(value) {
    if (!value) return '#3b82f6';
    let v = String(value).trim();
    if (!v.startsWith('#')) v = `#${v}`;
    if (v.length === 4) {
      v = `#${v[1]}${v[1]}${v[2]}${v[2]}${v[3]}${v[3]}`;
    }
    return /^#[0-9a-f]{6}$/i.test(v) ? v.toLowerCase() : '#3b82f6';
  }

  function bindPicker(root) {
    const hidden = root.querySelector('.color-picker-value');
    const sv = root.querySelector('.cp-sv');
    const svThumb = root.querySelector('.cp-sv-thumb');
    const hue = root.querySelector('.cp-hue');
    const hexInput = root.querySelector('.cp-hex');
    const preview = root.querySelector('.cp-preview');
    if (!hidden || !sv || !hue) return;

    let state = hexToHsl(normalizeHex(hidden.value));

    function paintSvBackground() {
      sv.style.backgroundColor = `hsl(${state.h}, 100%, 50%)`;
    }

    function commit() {
      const hex = hslToHex(state.h, state.s, state.l);
      hidden.value = hex;
      if (hexInput) hexInput.value = hex;
      if (preview) preview.style.backgroundColor = hex;
      svThumb.style.left = `${state.s}%`;
      svThumb.style.top = `${100 - state.l}%`;
      hue.value = String(Math.round(state.h));
      root.dispatchEvent(new CustomEvent('colorchange', { detail: { hex } }));
    }

    function setFromHex(hex) {
      state = hexToHsl(normalizeHex(hex));
      paintSvBackground();
      commit();
    }

    hue.addEventListener('input', () => {
      state.h = Number(hue.value);
      paintSvBackground();
      commit();
    });

    function pointerOnSv(clientX, clientY) {
      const rect = sv.getBoundingClientRect();
      state.s = clamp(((clientX - rect.left) / rect.width) * 100, 0, 100);
      state.l = clamp(100 - ((clientY - rect.top) / rect.height) * 100, 0, 100);
      commit();
    }

    sv.addEventListener('mousedown', (e) => {
      e.preventDefault();
      pointerOnSv(e.clientX, e.clientY);
      const move = (ev) => pointerOnSv(ev.clientX, ev.clientY);
      const up = () => {
        window.removeEventListener('mousemove', move);
        window.removeEventListener('mouseup', up);
      };
      window.addEventListener('mousemove', move);
      window.addEventListener('mouseup', up);
    });

    if (hexInput) {
      hexInput.addEventListener('change', () => setFromHex(hexInput.value));
      hexInput.addEventListener('blur', () => setFromHex(hexInput.value));
    }

    const native = root.querySelector('.cp-native');
    if (native) {
      native.addEventListener('input', () => setFromHex(native.value));
    }

    paintSvBackground();
    commit();
    root.setFromHex = setFromHex;
  }

  window.initColorPickers = function (scope) {
    (scope || document).querySelectorAll('[data-color-picker]').forEach(bindPicker);
  };

  document.addEventListener('DOMContentLoaded', () => initColorPickers());
})();
