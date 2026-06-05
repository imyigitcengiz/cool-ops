(function () {
    const API_BASE = window.CUSTOMER_API_BASE || '/contact';
    let activeModal = null;

    function escapeHtml(s) {
        return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    // Initialize custom selector on a given select element
    function initSearchSelector(select) {
        if (select.dataset.customerSearchSelectorInitialized) return;
        select.dataset.customerSearchSelectorInitialized = 'true';

        // Hide original select
        select.style.display = 'none';

        // Create container and selector UI
        const container = document.createElement('div');
        container.className = 'custom-customer-selector relative w-full';

        const wrapper = document.createElement('div');
        wrapper.className = 'w-full flex items-center justify-between p-3 bg-slate-50 border border-slate-200 rounded-xl hover:border-brand-500 hover:bg-white focus-within:ring-2 focus-within:ring-brand-500/20 transition-all text-left group';

        wrapper.innerHTML = `
            <!-- Clickable Search Area -->
            <div class="search-trigger-area flex-1 flex items-center gap-3 min-w-0 cursor-pointer">
                <div class="w-9 h-9 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center shrink-0 group-hover:bg-brand-100 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-user"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                </div>
                <div class="min-w-0 flex-1">
                    <span class="text-sm font-bold text-slate-700 block select-display-name">Müşteri Seçin / Arayın...</span>
                    <span class="text-xs text-slate-500 font-medium select-display-detail hidden"></span>
                </div>
            </div>
            
            <!-- Action Area -->
            <div class="flex items-center gap-2 shrink-0 pl-2 border-l border-slate-200/60 ml-2">
                <button type="button" class="clear-cust-btn hidden p-1.5 hover:bg-slate-200 text-slate-400 hover:text-slate-600 rounded-lg transition-colors" title="Temizle">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-x"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>
                </button>
                <div class="search-trigger-area cursor-pointer text-slate-400 hover:text-slate-600">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevrons-up-down"><path d="m7 15 5 5 5-5"></path><path d="m7 9 5-5 5 5"></path></svg>
                </div>
            </div>
        `;

        select.parentNode.insertBefore(container, select.nextSibling);
        container.appendChild(wrapper);

        const displayNameSpan = wrapper.querySelector('.select-display-name');
        const detailSpan = wrapper.querySelector('.select-display-detail');
        const clearBtn = wrapper.querySelector('.clear-cust-btn');

        // Fetch and display full details of selected customer
        function updateUI() {
            const val = select.value;
            if (val) {
                // Try to find currently loaded option text as a fallback first
                const fallbackText = select.options[select.selectedIndex]?.text || 'Yükleniyor...';
                displayNameSpan.textContent = fallbackText;
                detailSpan.classList.add('hidden');

                fetch(`${API_BASE}/musteriler/api/${val}/`)
                    .then(res => res.json())
                    .then(data => {
                        if (data && !data.error) {
                            displayNameSpan.textContent = data.name;
                            detailSpan.textContent = `${data.phone || '-'} • ${data.region || 'Bölge yok'}`;
                            detailSpan.classList.remove('hidden');
                            clearBtn.classList.remove('hidden');
                        }
                    })
                    .catch(err => console.error('Error fetching customer details:', err));
            } else {
                displayNameSpan.textContent = 'Müşteri Seçin / Arayın...';
                detailSpan.textContent = '';
                detailSpan.classList.add('hidden');
                clearBtn.classList.add('hidden');
            }
        }

        // Intercept programmatic value changes
        const originalValueDescriptor = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value');
        Object.defineProperty(select, 'value', {
            get: function () {
                return originalValueDescriptor.get.call(this);
            },
            set: function (val) {
                originalValueDescriptor.set.call(this, val);
                updateUI();
            }
        });

        // Also update UI when change event occurs
        select.addEventListener('change', updateUI);

        // Also detect DOM changes in select (like new options added)
        const observer = new MutationObserver(updateUI);
        observer.observe(select, { childList: true });

        // Trigger initial load UI
        updateUI();

        // Bind events
        container.querySelectorAll('.search-trigger-area').forEach(el => {
            el.addEventListener('click', () => {
                openSearchModal(select, (selectedId) => {
                    select.value = selectedId;
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                });
            });
        });

        clearBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            select.value = '';
            select.dispatchEvent(new Event('change', { bubbles: true }));
        });
    }

    // Modal creation and open
    function openSearchModal(selectEl, onSelect) {
        if (activeModal) return;

        const modal = document.createElement('div');
        modal.className = 'custom-customer-search-modal fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-[200] flex items-center justify-center p-4 animate-in fade-in duration-200';
        modal.innerHTML = `
            <div class="bg-white rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col max-h-[85vh] animate-in zoom-in-95 duration-200">
                <!-- Header -->
                <div class="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50 shrink-0">
                    <div class="flex items-center gap-2">
                        <div class="w-8 h-8 rounded-lg bg-brand-100 text-brand-700 flex items-center justify-center">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-search"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg>
                        </div>
                        <h3 class="font-bold text-slate-900 text-base">Müşteri Seçin</h3>
                    </div>
                    <button type="button" class="close-search-modal-btn p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-x"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>
                    </button>
                </div>
                
                <!-- Search Input -->
                <div class="p-4 border-b border-slate-100 bg-white shrink-0">
                    <div class="relative">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-search absolute left-3.5 top-3.5 text-slate-400"><circle cx="11" cy="11" r="8"></circle><path d="m21 21-4.3-4.3"></path></svg>
                        <input type="text" class="customer-search-input w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500 text-sm" placeholder="Müşteri adı, telefon numarası veya bölge yazın..." autocomplete="off">
                    </div>
                </div>
                
                <!-- Results List -->
                <div class="customer-results-list overflow-y-auto divide-y divide-slate-100 flex-1 min-h-[300px] p-2 bg-slate-50 space-y-1">
                    <!-- Loaded dynamically -->
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        activeModal = modal;

        const searchInput = modal.querySelector('.customer-search-input');
        const resultsList = modal.querySelector('.customer-results-list');
        const closeBtn = modal.querySelector('.close-search-modal-btn');

        searchInput.focus();

        let searchTimer = null;

        function closeModal() {
            if (!activeModal) return;
            modal.classList.add('fade-out');
            modal.querySelector('div').classList.add('zoom-out-95');
            setTimeout(() => {
                modal.remove();
                if (activeModal === modal) activeModal = null;
            }, 150);
        }

        async function loadResults(q) {
            resultsList.innerHTML = '<div class="p-8 text-center text-slate-400 text-sm flex flex-col items-center justify-center gap-2"><svg class="animate-spin h-5 w-5 text-brand-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Aranıyor...</div>';
            
            const params = new URLSearchParams({ all: '1' });
            if (q) params.set('q', q);

            try {
                const res = await fetch(`${API_BASE}/musteriler/secim/?${params}`);
                const data = await res.json();
                if (!data.ok) throw new Error(data.error || 'Liste alınamadı');

                const rows = data.results || [];
                if (!rows.length) {
                    resultsList.innerHTML = '<div class="p-8 text-center text-slate-400 text-sm">Müşteri bulunamadı.</div>';
                    return;
                }

                const currentVal = selectEl.value;

                resultsList.innerHTML = rows.map(c => {
                    const isSelected = String(c.id) === String(currentVal);
                    return `
                        <div class="select-result-item flex items-center justify-between p-3 hover:bg-brand-50/50 rounded-xl cursor-pointer transition-colors border ${isSelected ? 'bg-brand-50 border-brand-200' : 'border-transparent hover:border-brand-100'}" data-id="${c.id}">
                            <div class="min-w-0 flex-1">
                                <div class="flex items-center gap-2 flex-wrap">
                                    <span class="font-bold text-slate-900 text-sm truncate">${escapeHtml(c.name)}</span>
                                    ${c.region ? `<span class="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-slate-100 text-slate-600 border border-slate-200">${escapeHtml(c.region)}</span>` : ''}
                                </div>
                                <div class="flex items-center gap-1.5 text-xs text-slate-500 mt-1">
                                    <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 font-semibold text-[11px] border border-emerald-100 shrink-0">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-phone"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
                                        ${escapeHtml(c.phone || '-')}
                                    </span>
                                    ${c.product_names && c.product_names.length ? `
                                        <span class="text-slate-300">|</span>
                                        <span class="truncate text-slate-400 max-w-[220px]" title="${escapeHtml(c.product_names.join(', '))}">${escapeHtml(c.product_names.join(', '))}</span>
                                    ` : ''}
                                </div>
                            </div>
                            <div class="shrink-0 w-8 h-8 rounded-lg ${isSelected ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-400'} flex items-center justify-center transition-colors">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-check"><path d="M20 6 9 17l-5-5"></path></svg>
                            </div>
                        </div>
                    `;
                }).join('');

            } catch (err) {
                resultsList.innerHTML = `<div class="p-8 text-center text-red-600 text-sm">${escapeHtml(err.message)}</div>`;
            }
        }

        // Initial load
        loadResults('');

        // Event listeners
        closeBtn.addEventListener('click', closeModal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });

        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                loadResults(e.target.value.trim());
            }, 250);
        });

        resultsList.addEventListener('click', (e) => {
            const item = e.target.closest('.select-result-item');
            if (item) {
                const id = item.dataset.id;
                onSelect(id);
                closeModal();
            }
        });

        // Keyboard support
        document.addEventListener('keydown', function onKey(e) {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', onKey);
            }
        });
    }

    // Initialize on page load and dynamically
    function initAll() {
        const selects = document.querySelectorAll('select[name="customer"], select[name="existing_customer"]');
        selects.forEach(select => {
            // Only convert if it's not a hidden field
            if (select.type !== 'hidden' && select.style.display !== 'none') {
                initSearchSelector(select);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
    } else {
        initAll();
    }

    // Expose initialization function for dynamic forms
    window.initializeCustomerSearchSelectors = initAll;
})();
