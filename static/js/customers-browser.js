(function () {
    const PICKER_URL = (window.CUSTOMER_API_BASE || '/contact') + '/musteriler/secim/?all=1';
    let searchTimer = null;

    function escapeHtml(s) {
        return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function apiBase() {
        return window.CUSTOMER_API_BASE || '/contact';
    }

    function getModal() {
        return document.getElementById('customersBrowserModal');
    }

    function getDetailModal() {
        return document.getElementById('customersBrowserDetailModal');
    }

    async function loadCustomers(q) {
        const list = document.getElementById('customersBrowserList');
        if (!list) return;
        list.innerHTML = '<div class="p-8 text-center text-slate-400 text-sm">Yükleniyor…</div>';
        const params = new URLSearchParams({ all: '1' });
        if (q) params.set('q', q);
        try {
            const res = await fetch(`${PICKER_URL.split('?')[0]}?${params}`);
            const data = await res.json();
            if (!data.ok) throw new Error(data.error || 'Liste alınamadı');
            const rows = data.results || [];
            if (!rows.length) {
                list.innerHTML = '<div class="p-8 text-center text-slate-400 text-sm">Müşteri bulunamadı.</div>';
                return;
            }
            list.innerHTML = rows.map(c => `
                <button type="button" class="w-full text-left p-4 hover:bg-slate-50 flex items-start gap-3 customer-browser-row" data-customer-id="${c.id}">
                    <span class="w-10 h-10 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center shrink-0 font-bold text-sm">${escapeHtml((c.name || '?').charAt(0).toUpperCase())}</span>
                    <div class="min-w-0 flex-1">
                        <p class="font-bold text-slate-900 truncate">${escapeHtml(c.name)}</p>
                        <p class="text-xs text-slate-500 mt-0.5">${escapeHtml(c.phone || '-')} · ${escapeHtml(c.region || 'Bölge yok')}</p>
                        ${(c.product_names && c.product_names.length) ? `<p class="text-[10px] text-slate-400 mt-1 truncate">${escapeHtml(c.product_names.join(', '))}</p>` : ''}
                    </div>
                    <i data-lucide="chevron-right" class="w-4 h-4 text-slate-300 shrink-0 mt-2"></i>
                </button>
            `).join('');
            if (window.lucide) lucide.createIcons();
        } catch (err) {
            list.innerHTML = `<div class="p-8 text-center text-red-600 text-sm">${escapeHtml(err.message)}</div>`;
        }
    }

    function renderServiceTimeline(timeline, counts) {
        const box = document.getElementById('cbServices');
        const countsEl = document.getElementById('cbServiceCounts');
        if (!box) return;
        if (countsEl && counts) {
            countsEl.textContent = `${counts.open || 0} açık · ${counts.total || 0} toplam`;
        }
        if (!timeline || !timeline.length) {
            box.innerHTML = '<p class="text-sm text-slate-400">Servis kaydı yok.</p>';
            return;
        }
        const sdBase = window.SD_BASE || '/services-dashboard';
        box.innerHTML = timeline.map((item) => {
            const editUrl = item.edit_url || `${sdBase}/services/${item.id}/edit/`;
            const openCls = item.is_open ? 'border-brand-200 bg-brand-50/50' : 'border-slate-100 bg-slate-50/50';
            return `<a href="${editUrl}" class="block p-3 rounded-xl border ${openCls} hover:border-brand-300">
                <div class="flex flex-wrap items-center gap-2">
                    <span class="text-xs font-mono font-bold text-slate-500">#${item.id}</span>
                    <span class="text-xs font-bold text-brand-700">${escapeHtml(item.status_name)}</span>
                    <span class="text-[11px] text-slate-400">${escapeHtml(item.created_at)}</span>
                </div>
                <p class="text-xs text-slate-600 mt-1">${escapeHtml(item.service_types)}</p>
            </a>`;
        }).join('');
    }

    async function openCustomerDetail(customerId) {
        try {
            const sdBase = window.SD_BASE || '/services-dashboard';
            const [res, svcRes] = await Promise.all([
                fetch(`${apiBase()}/musteriler/api/${customerId}/`),
                fetch(`${sdBase}/services/musteri/${customerId}/ozet/`),
            ]);
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Müşteri bilgisi alınamadı');
            let svcData = { timeline: [], counts: {} };
            try {
                svcData = await svcRes.json();
            } catch (e) { /* ignore */ }

            document.getElementById('cbName').textContent = data.name || '-';
            document.getElementById('cbPhone').textContent = data.phone || '-';
            document.getElementById('cbRegion').textContent = data.region || '-';
            document.getElementById('cbContract').textContent = `${data.contract_date || '-'} ${data.contract_age || ''}`.trim();

            const loc = document.getElementById('cbLocation');
            const locEmpty = document.getElementById('cbLocationEmpty');
            if (loc && locEmpty) {
                if (data.location_link) {
                    loc.href = data.location_link;
                    loc.classList.remove('hidden');
                    locEmpty.classList.add('hidden');
                } else {
                    loc.classList.add('hidden');
                    locEmpty.classList.remove('hidden');
                }
            }

            const productsBox = document.getElementById('cbProducts');
            if (productsBox) {
                productsBox.innerHTML = '';
                if (data.product_names && data.product_names.length) {
                    data.product_names.forEach(name => {
                        const chip = document.createElement('span');
                        chip.className = 'px-2 py-0.5 rounded-lg text-[11px] font-bold bg-brand-100 text-brand-700';
                        chip.textContent = name;
                        productsBox.appendChild(chip);
                    });
                } else {
                    productsBox.innerHTML = '<span class="text-sm text-slate-400">Tanımlı ürün yok</span>';
                }
            }

            renderServiceTimeline(svcData.timeline, svcData.counts);

            const editLink = document.getElementById('cbEditLink');
            const serviceLink = document.getElementById('cbServiceLink');
            if (editLink) editLink.href = `${apiBase()}/musteriler/${customerId}/duzenle/`;
            if (serviceLink) serviceLink.href = `${sdBase}/services/new/?customer=${customerId}`;

            getDetailModal()?.classList.remove('hidden');
            if (window.lucide) lucide.createIcons();
        } catch (err) {
            alert(err.message);
        }
    }

    function openCustomersBrowser() {
        const modal = getModal();
        if (!modal) return;
        modal.classList.remove('hidden');
        const search = document.getElementById('customersBrowserSearch');
        if (search) search.value = '';
        loadCustomers('');
        if (window.lucide) lucide.createIcons();
    }

    function closeCustomersBrowser() {
        getModal()?.classList.add('hidden');
        getDetailModal()?.classList.add('hidden');
    }

    document.addEventListener('click', (e) => {
        if (e.target.closest('#openCustomersBrowserBtn')) {
            e.preventDefault();
            openCustomersBrowser();
        }
        if (e.target.closest('#closeCustomersBrowserBtn')) {
            closeCustomersBrowser();
        }
        if (e.target.closest('#closeCustomersBrowserDetailBtn')) {
            getDetailModal()?.classList.add('hidden');
        }
        const row = e.target.closest('.customer-browser-row');
        if (row) {
            openCustomerDetail(row.dataset.customerId);
        }
        const modal = getModal();
        if (modal && e.target === modal) closeCustomersBrowser();
        const detail = getDetailModal();
        if (detail && e.target === detail) detail.classList.add('hidden');
    });

    document.addEventListener('input', (e) => {
        if (e.target.id !== 'customersBrowserSearch') return;
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => loadCustomers(e.target.value.trim()), 280);
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeCustomersBrowser();
    });

    window.openCustomersBrowser = openCustomersBrowser;
})();
