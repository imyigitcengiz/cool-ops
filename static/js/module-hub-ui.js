/** Modül merkezi — durum filtresi ve grup sayaçları */
(function () {
  function countVisibleCards(root) {
    return root.querySelectorAll('[data-module-card]:not(.is-hub-hidden)').length;
  }

  function updateGroupCounts() {
    document.querySelectorAll('[data-hub-group]').forEach(function (section) {
      const countEl = section.querySelector('[data-group-count]');
      if (!countEl) return;
      const n = countVisibleCards(section);
      countEl.textContent = n ? n + ' modül' : '';
      section.classList.toggle('is-hub-group-empty', n === 0);
    });
  }

  function applyFilter(mode) {
    document.querySelectorAll('[data-module-card]').forEach(function (card) {
      const on = card.dataset.moduleInstalled === '1';
      let show = true;
      if (mode === 'open') show = on;
      if (mode === 'closed') show = !on;
      card.classList.toggle('is-hub-hidden', !show);
    });

    document.querySelectorAll('[data-hub-filter]').forEach(function (btn) {
      btn.classList.toggle('is-active', btn.dataset.hubFilter === mode);
    });

    const empty = document.getElementById('moduleHubFilterEmpty');
    const body = document.getElementById('moduleHubBody');
    const visible = body ? body.querySelectorAll('[data-module-card]:not(.is-hub-hidden)').length : 0;
    if (empty) {
      empty.classList.toggle('hidden', visible > 0);
    }
    updateGroupCounts();
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-hub-filter]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        applyFilter(btn.dataset.hubFilter || 'all');
      });
    });

    const reset = document.querySelector('[data-hub-filter-reset]');
    if (reset) {
      reset.addEventListener('click', function () {
        applyFilter('all');
      });
    }

    updateGroupCounts();
  });
})();
