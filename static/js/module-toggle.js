/** Modül / entegrasyon aç-kapa — sayfa yenilemeden, scroll korunur. */
(function (global) {
  function csrfToken() {
    const inp = document.querySelector(
      'input[name="csrfmiddlewaretoken"]'
    );
    if (inp && inp.value) return inp.value;
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function toast(message, level) {
    if (global.GyToast) {
      const fn = global.GyToast[level] || global.GyToast.info;
      fn(message);
      return;
    }
    const el = document.createElement('div');
    el.className = 'fixed bottom-4 right-4 z-[300] px-4 py-2 rounded-xl bg-slate-900 text-white text-sm shadow-lg';
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(function () { el.remove(); }, 3500);
  }

  function findCard(btn) {
    return btn.closest('[data-module-card]');
  }

  function applyCardState(card, data) {
    const installed = !!data.installed;
    const kind = card.dataset.moduleKind || data.kind || 'app';
    const isIntegration = kind === 'integration';

    card.dataset.moduleInstalled = installed ? '1' : '0';
    card.classList.toggle('erp-hub-card--on', installed);

    const badge = card.querySelector('[data-module-badge]');
    if (badge) {
      badge.textContent = installed ? 'Açık' : 'Kapalı';
      badge.classList.toggle('erp-hub-card__badge--on', installed);
    }

    const toggle = card.querySelector('[data-module-toggle]');
    if (toggle && data.can_toggle !== false) {
      if (toggle.type === 'checkbox') {
        toggle.checked = installed;
      } else {
        toggle.textContent = installed ? 'Kapat' : 'Aç';
        toggle.classList.toggle('text-red-600', installed);
        toggle.classList.toggle('text-emerald-700', !installed);
      }
      toggle.disabled = false;
      toggle.removeAttribute('aria-busy');
    }

    const particles = card.querySelector('[data-particles-block]');
    if (particles) {
      particles.classList.toggle('is-disabled', !installed);
    }

    const actions = card.querySelector('[data-module-actions]');
    if (!actions) return;

    let openLink = actions.querySelector('[data-module-open]');
    let permHint = actions.querySelector('[data-module-perm-hint]');

    if (installed && data.can_open && data.open_url) {
      if (permHint) permHint.remove();
      if (!openLink) {
        openLink = document.createElement('a');
        openLink.dataset.moduleOpen = '1';
        openLink.className = 'erp-hub-card__cta';
        openLink.textContent = isIntegration ? 'Kullan' : 'Modüle git';
        actions.insertBefore(openLink, actions.firstChild);
      }
      openLink.href = data.open_url;
      openLink.classList.remove('hidden');
    } else if (openLink) {
      openLink.remove();
    }

    if (installed && !data.can_open) {
      if (!permHint) {
        permHint = document.createElement('span');
        permHint.dataset.modulePermHint = '1';
        permHint.className = 'erp-hub-card__hint';
        permHint.textContent = 'Rol izni gerekir';
        actions.insertBefore(permHint, actions.firstChild);
      }
    } else if (permHint) {
      permHint.remove();
    }

    card.querySelectorAll('[data-particle-row]').forEach(function (row) {
      const ptoggle = row.querySelector('[data-particle-toggle]');
      const wrap = row.closest('form[data-particle-toggle-form]');
      if (wrap) wrap.classList.toggle('is-disabled', !installed);
      if (!installed) {
        applyParticleRow(row, { enabled: false });
      }
      if (ptoggle) ptoggle.disabled = !installed;
    });
  }

  function updateCounters(data) {
    const hubCount = document.querySelector('[data-module-installed-count]');
    if (hubCount && data.installed_count != null) {
      hubCount.textContent = String(data.installed_count);
    }
    const capCount = document.querySelector('[data-capabilities-enabled-count]');
    if (capCount && data.capabilities_enabled != null) {
      capCount.textContent = String(data.capabilities_enabled);
    }
  }

  async function toggleModule(btn) {
    const slug = btn.dataset.moduleSlug;
    if (!slug || btn.disabled) return;

    const card = findCard(btn);
    const isCheckbox = btn.type === 'checkbox';
    const prevChecked = isCheckbox ? !btn.checked : null;
    const prevLabel = isCheckbox ? null : btn.textContent;
    btn.disabled = true;
    btn.setAttribute('aria-busy', 'true');
    if (!isCheckbox) {
      btn.textContent = '…';
    }

    try {
      const body = new URLSearchParams();
      body.set('module_slug', slug);

      const res = await fetch(global.MODULE_TOGGLE_URL || '/panel/moduller/toggle/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': csrfToken(),
          'Accept': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: body.toString(),
      });

      const data = await res.json().catch(function () { return { ok: false, error: 'Yanıt okunamadı.' }; });

      if (!res.ok || !data.ok) {
        toast(data.error || 'İşlem başarısız.', 'error');
        if (isCheckbox && prevChecked != null) btn.checked = prevChecked;
        else if (!isCheckbox && prevLabel != null) btn.textContent = prevLabel;
        btn.disabled = false;
        btn.removeAttribute('aria-busy');
        return;
      }

      if (card) applyCardState(card, data);
      document.querySelectorAll('[data-module-card][data-module-slug="' + slug + '"]').forEach(function (c) {
        if (c !== card) applyCardState(c, data);
      });
      updateCounters(data);
      toast(data.message, data.level || 'success');
    } catch (err) {
      toast('Bağlantı hatası — tekrar deneyin.', 'error');
      if (isCheckbox && prevChecked != null) btn.checked = prevChecked;
      else if (!isCheckbox && prevLabel != null) btn.textContent = prevLabel;
      btn.disabled = false;
      btn.removeAttribute('aria-busy');
    }
  }

  function applyParticleRow(row, data) {
    const enabled = !!data.enabled;
    row.dataset.particleEnabled = enabled ? '1' : '0';
    const dot = row.querySelector('[data-particle-dot]');
    if (dot) {
      dot.classList.toggle('is-on', enabled);
    }
    const btn = row.querySelector('[data-particle-toggle]');
    if (btn) {
      if (btn.type === 'checkbox') {
        btn.checked = enabled;
      } else {
        btn.textContent = enabled ? 'Kapat' : 'Aç';
        btn.classList.toggle('text-red-600', enabled);
        btn.classList.toggle('text-emerald-700', !enabled);
      }
      btn.disabled = false;
      btn.removeAttribute('aria-busy');
    }
  }

  function syncParticleRows(slug, data) {
    document.querySelectorAll('[data-particle-row][data-particle-slug="' + slug + '"]').forEach(function (row) {
      applyParticleRow(row, data);
    });
  }

  function applyParticlesList(particles) {
    if (!particles || !particles.length) return;
    particles.forEach(function (p) {
      document.querySelectorAll('[data-particle-row][data-particle-slug="' + p.slug + '"]').forEach(function (row) {
        applyParticleRow(row, { enabled: !!p.enabled });
      });
    });
  }

  async function toggleParticle(btn) {
    const slug = btn.dataset.particleSlug;
    if (!slug || btn.disabled) return;

    const row = btn.closest('[data-particle-row]');
    const form = btn.closest('form[data-particle-toggle-form]');
    const isCheckbox = btn.type === 'checkbox';
    const prevChecked = isCheckbox ? !btn.checked : null;
    btn.disabled = true;
    btn.setAttribute('aria-busy', 'true');

    try {
      const body = new URLSearchParams();
      body.set('particle_slug', slug);
      if (form) {
        const csrfInp = form.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInp && csrfInp.value) body.set('csrfmiddlewaretoken', csrfInp.value);
      }

      const res = await fetch(global.MODULE_TOGGLE_URL || '/panel/moduller/toggle/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': csrfToken(),
          'Accept': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: body.toString(),
      });

      const data = await res.json().catch(function () { return { ok: false, error: 'Yanıt okunamadı.' }; });

      if (!res.ok || !data.ok) {
        toast(data.error || 'İşlem başarısız.', 'error');
        if (isCheckbox) btn.checked = prevChecked;
        btn.disabled = false;
        btn.removeAttribute('aria-busy');
        return;
      }

      if (row) applyParticleRow(row, data);
      syncParticleRows(slug, data);
      if (data.particles) applyParticlesList(data.particles);
      updateCounters(data);
      toast(data.message, data.level || 'success');
    } catch (err) {
      toast('Bağlantı hatası — tekrar deneyin.', 'error');
      if (isCheckbox) btn.checked = prevChecked;
      btn.disabled = false;
      btn.removeAttribute('aria-busy');
    }
  }

  function bindParticleForms(root) {
    (root || document).querySelectorAll('form[data-particle-toggle-form]').forEach(function (form) {
      if (form.dataset.particleFormBound) return;
      form.dataset.particleFormBound = '1';
      form.addEventListener('submit', function (e) {
        const btn = form.querySelector('[data-particle-toggle]');
        if (!btn || btn.disabled) return;
        e.preventDefault();
        toggleParticle(btn);
      });
    });
  }

  function bind(root) {
    (root || document).querySelectorAll('[data-module-toggle]').forEach(function (btn) {
      if (btn.dataset.moduleToggleBound) return;
      btn.dataset.moduleToggleBound = '1';
      const evt = btn.type === 'checkbox' ? 'change' : 'click';
      btn.addEventListener(evt, function (e) {
        e.preventDefault();
        toggleModule(btn);
      });
    });
    (root || document).querySelectorAll('[data-particle-toggle]').forEach(function (btn) {
      if (btn.dataset.particleToggleBound) return;
      btn.dataset.particleToggleBound = '1';
      const evt = btn.type === 'checkbox' ? 'change' : 'click';
      btn.addEventListener(evt, function (e) {
        e.preventDefault();
        toggleParticle(btn);
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    bind(document);
    bindParticleForms(document);
    document.querySelectorAll('form[data-preserve-scroll]').forEach(function (form) {
      form.addEventListener('submit', function () {
        try { sessionStorage.setItem('moduleHubScrollY', String(window.scrollY)); } catch (e) { /* ignore */ }
      });
    });
    try {
      const y = sessionStorage.getItem('moduleHubScrollY');
      if (y != null) {
        sessionStorage.removeItem('moduleHubScrollY');
        requestAnimationFrame(function () { window.scrollTo(0, parseInt(y, 10) || 0); });
      }
    } catch (e) { /* ignore */ }
  });

  global.ModuleToggle = { bind: bind, toggle: toggleModule, toggleParticle: toggleParticle };
})(window);
