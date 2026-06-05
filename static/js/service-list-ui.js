/** Servis listesi — görünüm modu. */
(function (global) {
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
    initViewModeButtons();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  global.GyServiceListUi = { init };
})(window);
