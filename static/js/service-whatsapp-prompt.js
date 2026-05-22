(function () {
    const modal = document.getElementById('serviceWhatsappStatusModal');
    if (!modal) return;

    const titleEl = document.getElementById('waStatusModalTitle');
    const subtitleEl = document.getElementById('waStatusModalSubtitle');
    const hintEl = document.getElementById('waStatusModalHint');
    const bodyEl = document.getElementById('waStatusModalBody');
    const listEl = document.getElementById('waStatusTemplateList');
    const deferredActions = document.getElementById('waStatusModalActionsDeferred');
    const legacyActions = document.getElementById('waStatusModalActionsLegacy');
    const sendBtn = modal.querySelector('[data-wa-status-send]');
    const skipBtn = modal.querySelector('[data-wa-status-skip]');
    const cancelBtn = modal.querySelector('[data-wa-status-cancel]');
    const saveBtn = modal.querySelector('[data-wa-status-save]');
    const saveSendBtn = modal.querySelector('[data-wa-status-save-send]');

    const confirmUrl = window.SERVICE_WA_STATUS_CONFIRM_URL || '/services-dashboard/services/whatsapp/durum-onay/';
    const applyUrl = window.SERVICE_WA_STATUS_APPLY_URL || '/services-dashboard/services/whatsapp/durum-uygula/';

    const PROMPT_COPY = {
        service_created: {
            title: 'WhatsApp mesajı gönderilsin mi?',
            body: 'Yeni servis kaydı için tanımlı senaryo kuralları eşleşti. Müşteriye otomatik mesaj göndermeden önce onaylayın.',
            send: 'Evet, gönder',
            skip: 'Hayır, gönderme',
        },
        customer_created: {
            title: 'WhatsApp mesajı gönderilsin mi?',
            body: 'Yeni müşteri kaydı için tanımlı mesaj şablonları var. Göndermek istiyor musunuz?',
            send: 'Evet, gönder',
            skip: 'Hayır, gönderme',
        },
        sales_created: {
            title: 'WhatsApp mesajı gönderilsin mi?',
            body: 'Yeni satış / proje kaydı için tanımlı mesaj şablonları var. Göndermek istiyor musunuz?',
            send: 'Evet, gönder',
            skip: 'Hayır, gönderme',
        },
        sales_status: {
            title: 'WhatsApp mesajı gönderilsin mi?',
            body: 'Satış durumu değişimi için tanımlı senaryo kuralları eşleşti. Müşteriye mesaj göndermek istiyor musunuz?',
            send: 'Evet, gönder',
            skip: 'Hayır, gönderme',
        },
        status_change: {
            title: 'WhatsApp mesajı gönderilsin mi?',
            body: 'Durum değişimi için tanımlı senaryo kuralları eşleşti. Müşteriye mesaj göndermek istiyor musunuz?',
            send: 'Evet, gönder',
            skip: 'Hayır, gönderme',
        },
    };

    let queue = [];
    let currentPrompt = null;
    let onComplete = null;
    let onApplied = null;
    let onCancel = null;

    function csrf() {
        const value = `; ${document.cookie}`;
        const parts = value.split('; csrftoken=');
        if (parts.length === 2) return parts.pop().split(';').shift();
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    function escapeHtml(s) {
        return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    function promptType(prompt) {
        return (prompt && prompt.prompt_type) || 'status_change';
    }

    function isDeferredPrompt(prompt) {
        return Boolean(prompt && prompt.deferred);
    }

    function renderTemplates(templates) {
        if (!listEl) return;
        if (!templates || !templates.length) {
            listEl.innerHTML = '<p class="text-xs text-slate-400">Eşleşen mesaj şablonu yok.</p>';
            return;
        }
        listEl.innerHTML = templates.map((t) => `
            <div class="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p class="text-xs font-bold text-violet-700">${escapeHtml(t.title)}</p>
                <p class="text-xs text-slate-600 mt-2 whitespace-pre-wrap">${escapeHtml(t.message)}</p>
            </div>
        `).join('');
    }

    function setModalMode(deferred, ptype) {
        const copy = PROMPT_COPY[ptype] || PROMPT_COPY.status_change;
        deferredActions?.classList.toggle('hidden', !deferred);
        legacyActions?.classList.toggle('hidden', deferred);
        hintEl?.classList.toggle('hidden', !deferred);
        if (titleEl) titleEl.textContent = deferred ? 'Durum değişikliğini onaylayın' : copy.title;
        if (bodyEl) {
            bodyEl.textContent = deferred
                ? 'Durum değişimi için tanımlı senaryo kuralları eşleşti. Durum henüz kaydedilmedi — nasıl devam etmek istersiniz?'
                : copy.body;
        }
        if (sendBtn) sendBtn.textContent = copy.send;
        if (skipBtn) skipBtn.textContent = copy.skip;
    }

    function openModal(prompt) {
        currentPrompt = prompt;
        const deferred = isDeferredPrompt(prompt);
        const ptype = promptType(prompt);
        setModalMode(deferred, ptype);
        if (subtitleEl) {
            subtitleEl.textContent = prompt.subtitle
                || `#${prompt.service_id || prompt.customer_id || prompt.sales_lead_id || ''} · ${prompt.customer_name || '-'}`;
        }
        renderTemplates(prompt.templates || []);
        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    function closeModal() {
        modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
        currentPrompt = null;
        onApplied = null;
        onCancel = null;
    }

    function finishCurrent(nextAction) {
        const cb = onComplete;
        closeModal();
        if (queue.length) {
            showNext();
            return;
        }
        onComplete = null;
        if (typeof nextAction === 'function') {
            nextAction();
        } else if (typeof cb === 'function') {
            cb();
        }
    }

    function showNext() {
        if (!queue.length) {
            closeModal();
            if (typeof onComplete === 'function') {
                const cb = onComplete;
                onComplete = null;
                cb();
            }
            return;
        }
        const next = queue.shift();
        onApplied = next.onApplied || null;
        onCancel = next.onCancel || null;
        openModal(next.prompt);
    }

    function setBusy(busy) {
        [sendBtn, skipBtn, cancelBtn, saveBtn, saveSendBtn].forEach((btn) => {
            if (btn) btn.disabled = busy;
        });
    }

    function buildConfirmPayload(prompt) {
        const ptype = promptType(prompt);
        const payload = {
            prompt_type: ptype,
            template_ids: (prompt.templates || []).map((t) => t.id),
        };
        if (ptype === 'service_created' || ptype === 'status_change') {
            payload.service_id = prompt.service_id;
        }
        if (ptype === 'status_change') {
            payload.prev_status_id = prompt.prev_status_id;
            payload.prev_status_name = prompt.prev_status_name || '';
        }
        if (ptype === 'customer_created') {
            payload.customer_id = prompt.customer_id;
        }
        if (ptype === 'sales_created' || ptype === 'sales_status') {
            payload.sales_lead_id = prompt.sales_lead_id;
        }
        if (ptype === 'sales_status') {
            payload.prev_status = prompt.prev_status || '';
        }
        return payload;
    }

    async function confirmLegacySend() {
        if (!currentPrompt) return;
        setBusy(true);
        try {
            const res = await fetch(confirmUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf(),
                },
                body: JSON.stringify(buildConfirmPayload(currentPrompt)),
            });
            const data = await res.json();
            if (!data.ok) {
                alert(data.error || 'Mesaj gönderilemedi.');
                return;
            }
            if (data.sent > 0) {
                finishCurrent();
            } else {
                alert(data.error || 'Mesaj gönderilemedi.');
            }
        } catch (err) {
            alert('Mesaj gönderimi sırasında hata oluştu.');
        } finally {
            setBusy(false);
        }
    }

    async function confirmDeferredApply(sendWhatsapp) {
        if (!currentPrompt) return;
        setBusy(true);
        try {
            const res = await fetch(applyUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf(),
                },
                body: JSON.stringify({
                    service_id: currentPrompt.service_id,
                    new_status_id: currentPrompt.new_status_id,
                    prev_status_id: currentPrompt.prev_status_id,
                    prev_status_name: currentPrompt.prev_status_name || '',
                    send_whatsapp: sendWhatsapp,
                    template_ids: sendWhatsapp ? (currentPrompt.templates || []).map((t) => t.id) : [],
                }),
            });
            const data = await res.json();
            if (!data.ok) {
                alert(data.error || 'Durum kaydedilemedi.');
                return;
            }
            if (sendWhatsapp && !data.sent) {
                alert(data.error || 'Durum kaydedildi ancak mesaj gönderilemedi.');
            }
            const appliedCb = onApplied;
            const completeCb = onComplete;
            closeModal();
            onApplied = null;
            onCancel = null;
            if (typeof appliedCb === 'function') {
                await appliedCb(data);
            }
            if (queue.length) {
                showNext();
                return;
            }
            onComplete = null;
            if (typeof completeCb === 'function') {
                completeCb();
            }
        } catch (err) {
            alert('Durum kaydı sırasında hata oluştu.');
        } finally {
            setBusy(false);
        }
    }

    sendBtn?.addEventListener('click', confirmLegacySend);
    skipBtn?.addEventListener('click', () => finishCurrent());
    saveBtn?.addEventListener('click', () => confirmDeferredApply(false));
    saveSendBtn?.addEventListener('click', () => confirmDeferredApply(true));
    cancelBtn?.addEventListener('click', () => {
        const cancelCb = onCancel;
        finishCurrent(() => {
            if (typeof cancelCb === 'function') cancelCb();
        });
    });
    modal.querySelector('[data-wa-status-dismiss]')?.addEventListener('click', () => {
        if (isDeferredPrompt(currentPrompt)) {
            const cancelCb = onCancel;
            finishCurrent(() => {
                if (typeof cancelCb === 'function') cancelCb();
            });
            return;
        }
        finishCurrent();
    });

    function enqueuePrompts(items, completeCallback) {
        if (!items.length) {
            if (typeof completeCallback === 'function') completeCallback();
            return;
        }
        queue = queue.concat(items);
        onComplete = completeCallback || onComplete;
        if (!currentPrompt) {
            showNext();
        }
    }

    window.enqueueServiceWhatsappStatusPrompts = function (prompts, completeCallback) {
        const raw = Array.isArray(prompts) ? prompts.filter(Boolean) : (prompts ? [prompts] : []);
        const items = raw.map((prompt) => ({ prompt, onApplied: null, onCancel: null }));
        enqueuePrompts(items, completeCallback);
    };

    window.showDeferredServiceStatusChange = function (prompt, callbacks) {
        if (!prompt) {
            if (typeof callbacks?.onApplied === 'function') callbacks.onApplied();
            return;
        }
        enqueuePrompts([{
            prompt,
            onApplied: callbacks?.onApplied || null,
            onCancel: callbacks?.onCancel || null,
        }], callbacks?.onComplete || null);
    };

    window.handleServiceWhatsappStatusResponse = function (data, completeCallback) {
        if (data && data.deferred && data.whatsapp_prompt) {
            window.showDeferredServiceStatusChange(data.whatsapp_prompt, {
                onApplied: () => {
                    if (typeof completeCallback === 'function') completeCallback();
                },
                onCancel: () => {},
            });
            return true;
        }
        if (data && data.whatsapp_prompt) {
            window.enqueueServiceWhatsappStatusPrompts(data.whatsapp_prompt, completeCallback);
            return true;
        }
        return false;
    };

    document.addEventListener('DOMContentLoaded', () => {
        const el = document.getElementById('whatsappPromptQueueData');
        if (!el) return;
        try {
            const initial = JSON.parse(el.textContent || '[]');
            if (initial.length) {
                window.enqueueServiceWhatsappStatusPrompts(initial);
            }
        } catch (e) {}
    });
})();
