(function () {
    const DEFAULT_SEND = '/tools/whatsapp/gonder/';
    const DEFAULT_READY = '/tools/whatsapp/baglantilar/hazir/';
    const DEFAULT_CONNECT = '/tools/whatsapp-baglan/';
    const WA_CONN_PREF_KEY = 'gy_wa_connection_id';

    function cfg(key, fallback) {
        return (window.WA_API && window.WA_API[key]) || fallback;
    }

    function csrf() {
        const fromInput = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (fromInput) return fromInput;
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    }

    let cachedConnections = null;

    function getPreferredConnectionId() {
        try {
            return localStorage.getItem(WA_CONN_PREF_KEY);
        } catch (e) {
            return null;
        }
    }

    function savePreferredWhatsAppConnectionId(id) {
        try {
            if (id) localStorage.setItem(WA_CONN_PREF_KEY, String(id));
        } catch (e) {}
    }

    function connectionStatusLabel(status, ready) {
        if (ready) return 'Bağlı';
        const map = {
            connecting: 'Bağlanıyor',
            qr: 'QR bekliyor',
            disconnected: 'Bağlı değil',
        };
        return map[status] || 'Bağlı değil';
    }

    function formatConnectionLabel(c) {
        const name = c.pushname || c.name || ('Hat #' + c.id);
        const phone = c.phone ? ' · ' + c.phone : '';
        const status = connectionStatusLabel(c.status, c.ready);
        return name + phone + ' (' + status + ')';
    }

    function populateWhatsAppConnectionSelect(selectEl, data) {
        if (!selectEl) {
            return { readyCount: 0, hasConnections: false, bridgeOffline: false };
        }

        const connections = data.connections || [];
        const preferred = getPreferredConnectionId();
        selectEl.innerHTML = '';

        if (!connections.length) {
            const opt = document.createElement('option');
            opt.value = '';
            opt.textContent = data.bridge_offline ? 'Köprü kapalı — hat listesi alınamadı' : 'Kayıtlı hat yok';
            selectEl.appendChild(opt);
            selectEl.disabled = true;
            return {
                readyCount: 0,
                hasConnections: false,
                bridgeOffline: !!data.bridge_offline,
            };
        }

        selectEl.disabled = false;
        connections.forEach(function (c) {
            const opt = document.createElement('option');
            opt.value = String(c.id);
            opt.textContent = formatConnectionLabel(c);
            opt.disabled = !c.ready;
            selectEl.appendChild(opt);
        });

        const ready = connections.filter(function (c) { return c.ready; });
        let selected = null;
        if (preferred && ready.some(function (c) { return String(c.id) === String(preferred); })) {
            selected = String(preferred);
        } else if (data.default_connection_id && ready.some(function (c) { return c.id === data.default_connection_id; })) {
            selected = String(data.default_connection_id);
        } else if (ready.length) {
            selected = String(ready[0].id);
        } else {
            selected = String(connections[0].id);
        }
        if (selected) selectEl.value = selected;

        return {
            readyCount: ready.length,
            hasConnections: true,
            bridgeOffline: !!data.bridge_offline,
        };
    }

    function getSelectedWhatsAppConnectionId(selectEl) {
        if (!selectEl || selectEl.disabled) return null;
        const opt = selectEl.options[selectEl.selectedIndex];
        if (!opt || !opt.value || opt.disabled) return null;
        return opt.value;
    }

    async function loadWhatsAppConnections(force) {
        if (cachedConnections && !force) return cachedConnections;
        const res = await fetch(cfg('ready', DEFAULT_READY));
        let data = {};
        try {
            data = await res.json();
        } catch (e) {
            throw new Error('WhatsApp bağlantı listesi alınamadı.');
        }
        if (!res.ok && data.offline) {
            const err = new Error(data.error || 'WhatsApp köprüsü kapalı.');
            err.offline = true;
            throw err;
        }
        cachedConnections = data;
        return data;
    }

    async function sendWhatsAppViaBridge(opts) {
        const body = {
            phone: opts.phone,
            message: opts.message || '',
            allow_empty: !!opts.allowEmpty,
            connection_id: opts.connectionId || null,
            recipient_name: opts.recipientName || '',
            customer_id: opts.customerId || null,
            firm_id: opts.firmId || null,
            source: opts.source || 'manual',
        };
        const res = await fetch(cfg('send', DEFAULT_SEND), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf(),
            },
            body: JSON.stringify(body),
        });
        let data = {};
        try {
            data = await res.json();
        } catch (e) {
            throw new Error('Sunucu yanıtı okunamadı.');
        }
        if (!res.ok || !data.ok) {
            const err = new Error(data.error || 'Gönderim başarısız.');
            err.offline = !!data.offline;
            err.raw = data;
            throw err;
        }
        if (opts.connectionId) {
            savePreferredWhatsAppConnectionId(opts.connectionId);
        }
        return data;
    }

    window.loadWhatsAppConnections = loadWhatsAppConnections;
    window.sendWhatsAppViaBridge = sendWhatsAppViaBridge;
    window.populateWhatsAppConnectionSelect = populateWhatsAppConnectionSelect;
    window.getSelectedWhatsAppConnectionId = getSelectedWhatsAppConnectionId;
    window.savePreferredWhatsAppConnectionId = savePreferredWhatsAppConnectionId;
    window.getWhatsAppCsrf = csrf;
    window.WA_CONNECT_URL = cfg('connect', DEFAULT_CONNECT);
})();
