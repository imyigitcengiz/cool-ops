(function () {
  const catalogEl = document.getElementById('optionsCatalogData');
  if (!catalogEl) return;

  const catalog = JSON.parse(catalogEl.textContent);
  const initialProducts = JSON.parse(document.getElementById('initialProductIds')?.textContent || '[]');
  const initialServiceTypes = JSON.parse(document.getElementById('initialServiceTypeIds')?.textContent || '[]');

  const productContainer = document.getElementById('productCheckboxesContainer');
  const serviceTypeContainer = document.getElementById('serviceTypeCheckboxesContainer');
  const serviceTypeHint = document.getElementById('serviceTypeFilterHint');
  const statusSelect = document.querySelector('select[name="status"]');
  const prioritySelect = document.querySelector('select[name="priority"]');

  let selectedServiceTypeIds = new Set(initialServiceTypes.map(Number));

  function getSelectedProductIds() {
    return Array.from(document.querySelectorAll('input[name="products"]:checked')).map((cb) =>
      parseInt(cb.value, 10)
    );
  }

  function resolveAllowedServiceTypeIds(productIds) {
    if (!productIds.length) {
      return { ids: null, mode: 'none', message: 'Önce en az bir ürün seçin.' };
    }
    const union = new Set();
    let anyMapping = false;
    productIds.forEach((pid) => {
      const product = catalog.products.find((p) => p.id === pid);
      if (product?.service_type_ids?.length) {
        anyMapping = true;
        product.service_type_ids.forEach((id) => union.add(id));
      }
    });
    if (!anyMapping) {
      return {
        ids: null,
        mode: 'all_fallback',
        message: 'Seçili ürünlerde tanımlı arıza tipi yok; tüm tipler gösteriliyor.',
      };
    }
    return {
      ids: union,
      mode: 'filtered',
      message: `${union.size} arıza tipi bu ürün(ler) için tanımlı.`,
    };
  }

  function getServiceTypeColor(serviceTypeId, selectedProductIds) {
    const selectedFirst = selectedProductIds.length
      ? catalog.products.find((p) => p.id === selectedProductIds[0])
      : null;
    for (const pid of selectedProductIds) {
      const product = catalog.products.find((p) => p.id === pid);
      if (product?.service_type_ids?.includes(serviceTypeId)) return product.color;
    }
    if (selectedFirst) return selectedFirst.color;
    const fallbackProduct = catalog.products.find((p) => p.service_type_ids?.includes(serviceTypeId));
    if (fallbackProduct) return fallbackProduct.color;
    return catalog.service_types.find((st) => st.id === serviceTypeId)?.color || '#3b82f6';
  }

  function renderServiceTypes() {
    if (!serviceTypeContainer) return;
    const productIds = getSelectedProductIds();
    const { ids, mode, message } = resolveAllowedServiceTypeIds(productIds);

    let list = catalog.service_types;
    if (ids && mode === 'filtered') {
      list = catalog.service_types.filter((st) => ids.has(st.id));
    }

    const validIds = new Set(list.map((st) => st.id));
    selectedServiceTypeIds = new Set(
      [...selectedServiceTypeIds].filter((id) => validIds.has(id))
    );

    serviceTypeContainer.innerHTML = '';
    if (!productIds.length) {
      serviceTypeContainer.innerHTML =
        '<p class="col-span-full text-sm text-amber-600 font-medium py-2">Servis tipleri için önce ürün seçin.</p>';
    } else if (!list.length) {
      serviceTypeContainer.innerHTML =
        '<p class="col-span-full text-sm text-slate-500 py-2">Gösterilecek servis tipi yok. Sistem ayarlarından tanımlayın.</p>';
    } else {
      list.forEach((st) => {
        const label = document.createElement('label');
        label.className =
          'flex items-center gap-2 p-2 hover:bg-white rounded-lg transition-colors cursor-pointer group border border-transparent hover:border-slate-200';
        const checked = selectedServiceTypeIds.has(st.id);
        const dotColor = getServiceTypeColor(st.id, productIds);
        label.innerHTML = `
          <input type="checkbox" name="service_types" value="${st.id}" ${checked ? 'checked' : ''}
            class="rounded border-slate-300 text-brand-600 service-type-cb">
          <span class="w-2.5 h-2.5 rounded-full shrink-0" style="background-color:${dotColor}"></span>
          <span class="text-sm text-slate-600 group-hover:text-brand-600">${st.name}</span>`;
        serviceTypeContainer.appendChild(label);
      });
    }

    if (serviceTypeHint) {
      serviceTypeHint.textContent = message;
      serviceTypeHint.className =
        'text-xs font-medium ' + (mode === 'none' ? 'text-amber-600' : 'text-slate-500');
    }
  }

  function bindServiceTypeContainer() {
    serviceTypeContainer?.addEventListener('change', (e) => {
      if (e.target.classList.contains('service-type-cb')) {
        const id = parseInt(e.target.value, 10);
        if (e.target.checked) selectedServiceTypeIds.add(id);
        else selectedServiceTypeIds.delete(id);
      }
    });
  }

  function refreshSelectOptions(selectEl, items, currentValue) {
    if (!selectEl) return;
    const val = currentValue || selectEl.value;
    selectEl.innerHTML = '';
    items.forEach((item) => {
      const opt = document.createElement('option');
      opt.value = item.id;
      opt.textContent = item.name;
      if (String(item.id) === String(val)) opt.selected = true;
      selectEl.appendChild(opt);
    });
  }

  const quickLabels = {
    status: 'durum',
    priority: 'öncelik',
    product: 'ürün',
    service_type: 'arıza / servis tipi',
  };

  function setQuickModalColor(hex) {
    const hidden = document.querySelector('#quickOptionModal .color-picker-value');
    if (hidden) hidden.value = hex || '#3b82f6';
    const hexInput = document.querySelector('#quickOptionModal .cp-hex');
    const native = document.querySelector('#quickOptionModal .cp-native');
    if (hexInput) hexInput.value = (hex || '#3b82f6').toUpperCase();
    if (native) native.value = hex || '#3b82f6';
    const preview = document.querySelector('#quickOptionModal .cp-preview');
    if (preview) preview.style.backgroundColor = hex || '#3b82f6';
  }

  function openQuickModal(kind, item = null) {
    const modal = document.getElementById('quickOptionModal');
    const title = document.getElementById('quickOptionModalTitle');
    const colorWrap = document.getElementById('quickOptionColorWrap');
    const productStWrap = document.getElementById('quickOptionProductTypesWrap');
    document.getElementById('quickOptionType').value = kind;
    document.getElementById('quickOptionId').value = item ? String(item.id) : '';
    document.getElementById('quickOptionName').value = item ? item.name : '';

    const label = quickLabels[kind] || 'seçenek';
    title.textContent = item ? `${label} düzenle` : `Yeni ${label}`;
    colorWrap.classList.toggle('hidden', kind === 'whatsapp' || kind === 'service_type');
    productStWrap.classList.toggle('hidden', kind !== 'product');

    if (kind === 'product') {
      const box = document.getElementById('quickProductServiceTypes');
      const selectedSt = item?.service_type_ids || [];
      box.innerHTML = catalog.service_types
        .map(
          (st) => `<label class="flex items-center gap-2 text-sm py-1">
        <input type="checkbox" class="quick-product-st-cb rounded" value="${st.id}" ${selectedSt.includes(st.id) ? 'checked' : ''}>
        <span class="w-2 h-2 rounded-full" style="background-color:${st.color}"></span>${st.name}</label>`
        )
        .join('');
    }

    setQuickModalColor(item?.color || '#3b82f6');
    if (window.initColorPickers) window.initColorPickers(modal);
    modal.classList.remove('hidden');
    if (window.lucide) lucide.createIcons();
  }

  function openQuickEdit(kind) {
    let item = null;
    if (kind === 'status') {
      const id = parseInt(statusSelect?.value, 10);
      item = catalog.statuses.find((s) => s.id === id);
      if (!item) return alert('Önce düzenlemek istediğiniz durumu seçin.');
    } else if (kind === 'priority') {
      const id = parseInt(prioritySelect?.value, 10);
      item = catalog.priorities.find((p) => p.id === id);
      if (!item) return alert('Önce düzenlemek istediğiniz önceliği seçin.');
    } else if (kind === 'product') {
      const checked = document.querySelectorAll('input[name="products"]:checked');
      if (checked.length !== 1) {
        return alert('Ürün düzenlemek için tam olarak bir ürün işaretleyin.');
      }
      const id = parseInt(checked[0].value, 10);
      item = catalog.products.find((p) => p.id === id);
    } else if (kind === 'service_type') {
      const ids = [...selectedServiceTypeIds];
      if (ids.length !== 1) {
        return alert('Arıza tipi düzenlemek için tam olarak bir tip işaretleyin.');
      }
      item = catalog.service_types.find((s) => s.id === ids[0]);
    }
    if (!item) return alert('Kayıt bulunamadı.');
    openQuickModal(kind, item);
  }

  async function saveQuickOption() {
    const kind = document.getElementById('quickOptionType').value;
    const id = document.getElementById('quickOptionId').value;
    const name = document.getElementById('quickOptionName').value.trim();
    const color =
      document.querySelector('#quickOptionModal .color-picker-value')?.value || '#3b82f6';
    if (!name) return alert('İsim girin');

    const body = { type: kind, name };
    if (kind !== 'service_type') {
      body.color = color;
    }
    if (kind === 'product') {
      body.service_type_ids = Array.from(
        document.querySelectorAll('.quick-product-st-cb:checked')
      ).map((cb) => parseInt(cb.value, 10));
    }

    const base = window.SD_BASE || '/services-dashboard';
    const url = id ? `${base}/api/options/quick-update/` : `${base}/api/options/quick-create/`;
    if (id) {
      body.id = parseInt(id, 10);
    }

    const csrf = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!data.ok) {
      alert(data.error || 'Kayıt başarısız');
      return;
    }

    const item = data.item;
    const catalogKey = {
      status: 'statuses',
      priority: 'priorities',
      product: 'products',
      service_type: 'service_types',
    }[kind];

    if (id && catalogKey) {
      const list = catalog[catalogKey];
      const idx = list.findIndex((x) => x.id === item.id);
      if (idx >= 0) list[idx] = { ...list[idx], ...item };
      else list.push(item);
    } else if (kind === 'status') {
      catalog.statuses.push(item);
    } else if (kind === 'priority') {
      catalog.priorities.push(item);
    } else if (kind === 'product') {
      catalog.products.push(item);
      appendProductCheckbox(item);
    } else if (kind === 'service_type') {
      catalog.service_types.push(item);
    }

    if (kind === 'status') {
      refreshSelectOptions(statusSelect, catalog.statuses, item.id);
    } else if (kind === 'priority') {
      refreshSelectOptions(prioritySelect, catalog.priorities, item.id);
    } else if (kind === 'product') {
      updateProductCheckboxLabel(item);
      renderServiceTypes();
    } else if (kind === 'service_type') {
      renderServiceTypes();
    }

    document.getElementById('quickOptionModal').classList.add('hidden');
    if (typeof updateProductStyling === 'function') updateProductStyling();
    if (window.lucide) lucide.createIcons();
  }

  function updateProductCheckboxLabel(product) {
    const cb = document.querySelector(`input[name="products"][value="${product.id}"]`);
    if (!cb) return;
    const label = cb.closest('label');
    const nameSpan = label?.querySelector('span.text-sm, span:last-child');
    const dot = label?.querySelector('.product-color-dot');
    if (dot) dot.style.backgroundColor = product.color;
    if (nameSpan) nameSpan.textContent = product.name;
  }

  function enrichProductCheckboxes() {
    document.querySelectorAll('#productCheckboxesContainer input[name="products"]').forEach((cb) => {
      const product = catalog.products.find((p) => p.id === parseInt(cb.value, 10));
      if (!product) return;
      const label = cb.closest('label');
      if (!label || label.querySelector('.product-color-dot')) return;
      const dot = document.createElement('span');
      dot.className = 'w-2.5 h-2.5 rounded-full shrink-0 product-color-dot';
      dot.style.backgroundColor = product.color;
      const textSpan = label.querySelector('span.text-sm') || label.querySelector('span');
      if (textSpan) label.insertBefore(dot, textSpan);
      else label.appendChild(dot);
    });
  }

  function appendProductCheckbox(product) {
    const label = document.createElement('label');
    label.className =
      'flex items-center gap-2 p-2 hover:bg-white rounded-lg transition-colors cursor-pointer group';
    label.innerHTML = `
      <input type="checkbox" name="products" value="${product.id}" class="rounded border-slate-300 text-brand-600">
      <span class="w-2.5 h-2.5 rounded-full shrink-0" style="background-color:${product.color}"></span>
      <span class="text-sm text-slate-600 group-hover:text-brand-600">${product.name}</span>`;
    productContainer.appendChild(label);
  }

  productContainer?.addEventListener('change', (e) => {
    if (e.target.name === 'products') {
      renderServiceTypes();
      if (typeof updateProductStyling === 'function') updateProductStyling();
    }
  });

  bindServiceTypeContainer();
  enrichProductCheckboxes();
  renderServiceTypes();

  document.querySelectorAll('[data-quick-add]').forEach((btn) => {
    btn.addEventListener('click', () => openQuickModal(btn.dataset.quickAdd));
  });
  document.querySelectorAll('[data-quick-edit]').forEach((btn) => {
    btn.addEventListener('click', () => openQuickEdit(btn.dataset.quickEdit));
  });
  document.getElementById('quickOptionSaveBtn')?.addEventListener('click', saveQuickOption);
  document.getElementById('quickOptionCancelBtn')?.addEventListener('click', () => {
    document.getElementById('quickOptionModal').classList.add('hidden');
  });

  window.serviceFormCatalog = catalog;
  window.refreshServiceTypesForProducts = renderServiceTypes;
})();
