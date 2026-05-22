(function () {
    const panel = document.getElementById('customerOpenServicesPanel');
    const customerSelect = document.querySelector('select[name="customer"]');
    const isCreateForm = !document.querySelector('input[name="customer"][type="hidden"]') && customerSelect;
    if (!panel || !customerSelect) return;

    const base = window.SD_BASE || '/services-dashboard';

    function escapeHtml(s) {
        return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function csrf() {
        const value = `; ${document.cookie}`;
        const parts = value.split('; csrftoken=');
        if (parts.length === 2) return parts.pop().split(';').shift();
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    function renderPanel(data) {
        const open = data.open_services || [];
        const timeline = data.timeline || [];
        if (!open.length && !timeline.length) {
            panel.classList.add('hidden');
            panel.innerHTML = '';
            return;
        }

        let html = '<div class="rounded-2xl border border-amber-200 bg-amber-50/80 p-4 space-y-3">';
        if (open.length && isCreateForm) {
            html += '<p class="text-sm font-bold text-amber-900">Bu müşterinin açık servis kaydı var</p>';
            html += '<p class="text-xs text-amber-800">Yeni dosya açmadan önce mevcut kayda devam etmek genelde daha doğrudur.</p>';
            html += '<div class="space-y-2">';
            open.forEach((s) => {
                html += `<div class="flex flex-wrap items-center gap-2 p-2 rounded-xl bg-white border border-amber-100">
                    <span class="text-xs font-bold text-slate-700">#${s.id}</span>
                    <span class="text-xs font-semibold text-slate-600">${escapeHtml(s.status_name)} · ${escapeHtml(s.created_date)}</span>
                    <span class="text-[11px] text-slate-500 truncate max-w-[200px]">${escapeHtml(s.service_types)}</span>
                    <a href="${escapeHtml(s.edit_url)}" class="ml-auto px-3 py-1.5 rounded-lg text-xs font-bold bg-brand-600 text-white hover:bg-brand-700">Bu kayda devam et</a>
                </div>`;
            });
            html += '<p class="text-[11px] text-amber-700">Farklı bir arıza / yeni ziyaret ise aşağıdaki formu doldurup yeni kayıt oluşturabilirsiniz.</p>';
        } else if (open.length) {
            html += '<p class="text-sm font-bold text-slate-800">Diğer açık kayıtlar</p>';
            open.forEach((s) => {
                html += `<a href="${escapeHtml(s.edit_url)}" class="block text-xs font-semibold text-brand-600 hover:underline">#${s.id} ${escapeHtml(s.status_name)} · ${escapeHtml(s.created_date)}</a>`;
            });
        }

        if (timeline.length > 1) {
            html += `<details class="text-xs"><summary class="cursor-pointer font-bold text-slate-600 py-1">Tüm servis geçmişi (${data.counts?.total || timeline.length})</summary>`;
            html += '<ul class="mt-2 space-y-1 max-h-40 overflow-y-auto">';
            timeline.forEach((s) => {
                const tone = s.is_open ? 'text-brand-700 font-bold' : 'text-slate-600';
                html += `<li class="${tone}"><a href="${escapeHtml(s.edit_url)}" class="hover:underline">#${s.id} ${escapeHtml(s.status_name)} · ${escapeHtml(s.created_date)} — ${escapeHtml(s.service_types)}</a></li>`;
            });
            html += '</ul></details>';
        }
        html += '</div>';
        panel.innerHTML = html;
        panel.classList.remove('hidden');
        if (window.lucide) window.lucide.createIcons();
    }

    async function loadHints(customerId) {
        if (!customerId) {
            panel.classList.add('hidden');
            return;
        }
        try {
            const res = await fetch(`${base}/services/musteri/${customerId}/ozet/`);
            const data = await res.json();
            if (!data.ok) return;
            renderPanel(data);
        } catch (e) {
            console.error('customer service hints', e);
        }
    }

    customerSelect.addEventListener('change', () => loadHints(customerSelect.value));
    if (customerSelect.value) loadHints(customerSelect.value);

    window.reopenServiceRecord = async function (serviceId) {
        if (!serviceId || !confirm('Bu kayıt yeniden aktif yapılsın mı?')) return;
        try {
            const res = await fetch(`${base}/services/${serviceId}/yeniden-ac/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrf() },
            });
            const data = await res.json();
            if (!data.ok) {
                alert(data.error || 'İşlem başarısız.');
                if (data.edit_url) window.location.href = data.edit_url;
                return;
            }
            window.location.href = data.edit_url || window.location.href;
        } catch (e) {
            alert('Yeniden açma sırasında hata oluştu.');
        }
    };
})();
