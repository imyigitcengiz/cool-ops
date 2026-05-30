/** Uygulama geneli toast bildirimleri (alert yerine). */
(function (global) {
  const ICONS = {
    success: 'check-circle',
    error: 'alert-circle',
    warning: 'alert-triangle',
    info: 'info',
  };

  const STYLES = {
    success: 'bg-emerald-50 border-emerald-200 text-emerald-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-amber-50 border-amber-200 text-amber-900',
    info: 'bg-slate-50 border-slate-200 text-slate-800',
  };

  function ensureRoot() {
    let root = document.getElementById('gyToastRoot');
    if (!root) {
      root = document.createElement('div');
      root.id = 'gyToastRoot';
      root.className = 'fixed top-4 right-4 z-[300] flex flex-col gap-2 max-w-sm pointer-events-none';
      root.setAttribute('aria-live', 'polite');
      document.body.appendChild(root);
    }
    return root;
  }

  function show(message, type = 'info', duration = 4200) {
    if (!message) return;
    const root = ensureRoot();
    const toast = document.createElement('div');
    toast.className = `pointer-events-auto px-4 py-3 rounded-2xl border shadow-lg flex items-start gap-3 text-sm font-medium transition-all ${STYLES[type] || STYLES.info}`;
    const icon = ICONS[type] || ICONS.info;
    toast.innerHTML = `<i data-lucide="${icon}" class="w-5 h-5 shrink-0 mt-0.5"></i><span class="flex-1 leading-snug"></span>`;
    toast.querySelector('span').textContent = message;
    root.appendChild(toast);
    if (global.lucide) global.lucide.createIcons({ nodes: [toast] });
    requestAnimationFrame(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateX(0)';
    });
    window.setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(12px)';
      window.setTimeout(() => toast.remove(), 220);
    }, duration);
  }

  global.GyToast = {
    show,
    success: (msg, d) => show(msg, 'success', d),
    error: (msg, d) => show(msg, 'error', d),
    warning: (msg, d) => show(msg, 'warning', d),
    info: (msg, d) => show(msg, 'info', d),
  };
})(window);
