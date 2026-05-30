/** Servis listesi — sekme, filtre paneli, görünüm modu. */
(function (global) {
  function initFilterDrawer() {
    const toggle = document.getElementById('serviceFilterToggle');
    const drawer = document.getElementById('serviceFilterDrawer');
    if (!toggle || !drawer) return;

    const open = () => {
      drawer.classList.remove('hidden');
      toggle.setAttribute('aria-expanded', 'true');
    };
    const close = () => {
      drawer.classList.add('hidden');
      toggle.setAttribute('aria-expanded', 'false');
    };

    toggle.addEventListener('click', () => {
      if (drawer.classList.contains('hidden')) open();
      else close();
    });

    if (drawer.dataset.openDefault === '1') open();
  }

  function initViewModeButtons() {
    const form = document.getElementById('serviceFilterForm');
    const input = document.getElementById('listViewModeInput');
    if (!form || !input) return;

    document.querySelectorAll('[data-set-view]').forEach((btn) => {
      btn.addEventListener('click', () => {
        input.value = btn.dataset.setView || 'customer';
        form.submit();
      });
    });
  }

  function init() {
    initFilterDrawer();
    initViewModeButtons();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  global.GyServiceListUi = { init };
})(window);
