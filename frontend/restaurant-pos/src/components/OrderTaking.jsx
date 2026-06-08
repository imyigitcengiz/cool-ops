import React, { useState, useEffect } from 'react';
import { Plus, Minus, Send, CreditCard, DollarSign, X, Check, Clock, Utensils, Tag, Percent, ChevronDown, AlertCircle } from 'lucide-react';

import { apiFetch, API_BASE } from '../lib/apiClient';

export default function OrderTaking({ table, activeOrder, onBack }) {
  const [categories, setCategories] = useState([]);
  const [menuItems, setMenuItems] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [cart, setCart] = useState([]);
  const [existingOrder, setExistingOrder] = useState(activeOrder);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [showDiscountModal, setShowDiscountModal] = useState(false);
  const [showModifierModal, setShowModifierModal] = useState(false);
  const [pendingItem, setPendingItem] = useState(null);
  const [selectedModifiers, setSelectedModifiers] = useState([]);
  const [paymentMethod, setPaymentMethod] = useState('card');
  const [loading, setLoading] = useState(false);

  // Discount state
  const [discountType, setDiscountType] = useState('none');
  const [discountValue, setDiscountValue] = useState('');
  const [discountReason, setDiscountReason] = useState('');
  const [appliedDiscount, setAppliedDiscount] = useState(null); // { type, value, reason }

  useEffect(() => {
    fetchCategories();
    fetchMenuItems();
    if (activeOrder) {
      fetchLatestOrderDetails(activeOrder.id);
    }
  }, [table, activeOrder]);

  const fetchCategories = async () => {
    try {
      const res = await apiFetch(`/categories/`);
      const data = await res.json();
      setCategories(data);
      if (data.length > 0) setSelectedCategory(data[0].id);
    } catch (err) { console.error(err); }
  };

  const fetchMenuItems = async () => {
    try {
      const res = await apiFetch(`/menu-items/`);
      const data = await res.json();
      setMenuItems(data);
    } catch (err) { console.error(err); }
  };

  const fetchLatestOrderDetails = async (orderId) => {
    const id = orderId || (existingOrder?.id) || (activeOrder?.id);
    if (!id) return;
    try {
      const res = await apiFetch(`/orders/${id}/`);
      const data = await res.json();
      setExistingOrder(data);
      // Restore discount state from server
      if (data.discount_type && data.discount_type !== 'none') {
        setAppliedDiscount({ type: data.discount_type, value: data.discount_value, reason: data.discount_reason });
      }
    } catch (err) { console.error(err); }
  };

  // Open modifier modal if item has modifiers, else add directly
  const handleMenuItemClick = (item) => {
    if (item.modifiers && item.modifiers.length > 0) {
      setPendingItem(item);
      setSelectedModifiers([]);
      setShowModifierModal(true);
    } else {
      addToCart(item, [], 0);
    }
  };

  const toggleModifier = (modifier) => {
    setSelectedModifiers(prev => {
      const exists = prev.find(m => m.id === modifier.id);
      if (exists) return prev.filter(m => m.id !== modifier.id);
      return [...prev, modifier];
    });
  };

  const confirmModifiers = () => {
    if (!pendingItem) return;
    const extraTotal = selectedModifiers.reduce((s, m) => s + parseFloat(m.price_extra), 0);
    const modText = selectedModifiers.map(m => m.name).join(', ');
    addToCart(pendingItem, selectedModifiers, extraTotal, modText);
    setShowModifierModal(false);
    setPendingItem(null);
    setSelectedModifiers([]);
  };

  const addToCart = (item, modifiers = [], modifierExtra = 0, modifierText = '') => {
    const cartKey = `${item.id}_${modifierText}`;
    const existing = cart.find(ci => ci.cartKey === cartKey);
    if (existing && modifierText === '') {
      setCart(cart.map(ci => ci.cartKey === cartKey ? { ...ci, quantity: ci.quantity + 1 } : ci));
    } else {
      setCart([...cart, {
        ...item,
        cartKey,
        quantity: 1,
        note: '',
        modifierExtra,
        modifierText,
        effectivePrice: parseFloat(item.price) + modifierExtra
      }]);
    }
  };

  const updateQuantity = (cartKey, change) => {
    const item = cart.find(ci => ci.cartKey === cartKey);
    if (!item) return;
    const newQty = item.quantity + change;
    if (newQty <= 0) {
      setCart(cart.filter(ci => ci.cartKey !== cartKey));
    } else {
      setCart(cart.map(ci => ci.cartKey === cartKey ? { ...ci, quantity: newQty } : ci));
    }
  };

  const updateItemNote = (cartKey, note) => {
    setCart(cart.map(ci => ci.cartKey === cartKey ? { ...ci, note } : ci));
  };

  const getCartTotal = () => cart.reduce((sum, item) => sum + (item.effectivePrice * item.quantity), 0);

  const getRawTotal = () => {
    const existingTotal = existingOrder ? parseFloat(existingOrder.total_amount) : 0;
    return existingTotal + getCartTotal();
  };

  const getDiscountAmount = () => {
    const raw = getRawTotal();
    const d = appliedDiscount || (existingOrder && existingOrder.discount_type !== 'none' ? { type: existingOrder.discount_type, value: existingOrder.discount_value } : null);
    if (!d) return 0;
    if (d.type === 'percent') return raw * (parseFloat(d.value) / 100);
    if (d.type === 'fixed') return Math.min(parseFloat(d.value), raw);
    return 0;
  };

  const getGrandTotal = () => Math.max(0, getRawTotal() - getDiscountAmount());

  const handleSendToKitchen = async () => {
    if (cart.length === 0) return;
    setLoading(true);
    try {
      const itemsPayload = cart.map(item => ({
        menu_item: item.id,
        quantity: item.quantity,
        note: item.note,
        modifier_text: item.modifierText || '',
        modifier_extra: item.modifierExtra || 0
      }));

      const res = await apiFetch(`/orders/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ table: table.id, items: itemsPayload })
      });

      if (res.ok) {
        const orderData = await res.json();
        setExistingOrder(orderData);
        setCart([]);
        fetchLatestOrderDetails(orderData.id);
      } else {
        alert('Sipariş gönderilirken bir hata oluştu.');
      }
    } catch (err) { console.error(err); alert('Sistem hatası.'); }
    finally { setLoading(false); }
  };

  const handleApplyDiscount = async () => {
    if (!existingOrder) {
      // Store locally if no order yet (will apply after first send)
      setAppliedDiscount({ type: discountType, value: parseFloat(discountValue) || 0, reason: discountReason });
      setShowDiscountModal(false);
      return;
    }
    try {
      const res = await apiFetch(`/orders/${existingOrder.id}/apply_discount/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          discount_type: discountType,
          discount_value: parseFloat(discountValue) || 0,
          discount_reason: discountReason
        })
      });
      if (res.ok) {
        const data = await res.json();
        setExistingOrder(data);
        setAppliedDiscount({ type: discountType, value: parseFloat(discountValue) || 0, reason: discountReason });
        setShowDiscountModal(false);
      }
    } catch (err) { console.error(err); }
  };

  const removeDiscount = async () => {
    setAppliedDiscount(null);
    if (existingOrder) {
      await apiFetch(`/orders/${existingOrder.id}/apply_discount/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ discount_type: 'none', discount_value: 0, discount_reason: '' })
      });
    }
  };

  const handleRequestBill = async () => {
    try {
      const res = await apiFetch(`/tables/${table.id}/change_status/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'bill_requested' })
      });
      if (res.ok) { alert('Hesap istendi olarak işaretlendi.'); onBack(); }
    } catch (err) { console.error(err); }
  };

  const handleCheckout = async () => {
    if (!existingOrder) return;
    setLoading(true);
    try {
      const finalAmount = getGrandTotal();
      const res = await apiFetch(`/orders/${existingOrder.id}/pay_and_close/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payment_method: paymentMethod, amount: finalAmount })
      });
      if (res.ok) {
        const data = await res.json();
        let successMsg = 'Ödeme başarıyla kaydedildi, masa kapatıldı.';
        if (data.whatsapp_simulated) {
          successMsg += `\n\n[WhatsApp] Mesaj gönderildi: ${data.whatsapp_simulated.to}`;
        }
        alert(successMsg);
        setShowPaymentModal(false);
        onBack();
      } else {
        const errorData = await res.json();
        alert(`Hata: ${errorData.error || 'Ödeme tamamlanamadı'}`);
      }
    } catch (err) { console.error(err); alert('Ödeme hatası.'); }
    finally { setLoading(false); }
  };

  const filteredMenuItems = menuItems.filter(item => item.category === selectedCategory && item.is_available);
  const discountAmount = getDiscountAmount();
  const hasDiscount = discountAmount > 0;

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <button onClick={onBack} className="btn btn-secondary" style={{ padding: '8px 16px', fontSize: '13px' }}>
          ← Masalara Dön
        </button>
        <h2 style={{ fontSize: '22px', fontWeight: '700' }}>{table.name} — Sipariş & Ödeme</h2>
      </div>

      <div className="order-screen-container">
        {/* Left: Menu */}
        <div>
          <div className="menu-categories-bar">
            {categories.map(cat => (
              <div
                key={cat.id}
                className={`category-tab ${selectedCategory === cat.id ? 'active' : ''}`}
                onClick={() => setSelectedCategory(cat.id)}
              >
                <span>{cat.name}</span>
              </div>
            ))}
          </div>

          <div className="menu-items-grid">
            {filteredMenuItems.map(item => (
              <div className="menu-item-card" key={item.id} onClick={() => handleMenuItemClick(item)}>
                {item.image && (
                  <img
                    src={item.image.startsWith('http') ? item.image : `${(import.meta.env.VITE_API_URL || '')}${item.image}`}
                    alt={item.name}
                    style={{ width: '100%', height: '120px', borderRadius: '10px', objectFit: 'cover', marginBottom: '4px' }}
                  />
                )}
                <div>
                  <div className="menu-item-name">{item.name}</div>
                  <div className="menu-item-desc">{item.description}</div>
                  {item.modifiers && item.modifiers.length > 0 && (
                    <div style={{ fontSize: '10px', color: 'var(--primary)', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '3px' }}>
                      <ChevronDown size={10} /> {item.modifiers.length} seçenek
                    </div>
                  )}
                </div>
                <div className="menu-item-bottom">
                  <span className="menu-item-price">{parseFloat(item.price).toLocaleString('tr-TR')} ₺</span>
                  <button className="add-item-btn"><Plus size={16} /></button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Cart */}
        <div>
          <div className="card order-cart-card">
            <div className="order-cart-header">
              <span style={{ fontWeight: '750', fontSize: '16px' }}>Sipariş Detayı</span>
              <span className="badge badge-primary">{table.name}</span>
            </div>

            <div className="order-cart-items">
              {/* Existing order items */}
              {existingOrder?.items?.length > 0 && (
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '600', marginBottom: '8px', textTransform: 'uppercase' }}>
                    Gönderilmiş Siparişler
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {existingOrder.items.map((item, idx) => (
                      <div key={idx} className="cart-item" style={{ borderLeft: '3px solid var(--primary)', background: 'rgba(99,102,241,0.03)' }}>
                        <div className="cart-item-details">
                          <div className="cart-item-name">
                            <span style={{ fontWeight: '700', marginRight: '6px' }}>{item.quantity}x</span>
                            {item.menu_item_name}
                          </div>
                          {item.modifier_text && (
                            <div style={{ fontSize: '10px', color: 'var(--primary)', marginTop: '2px' }}>+ {item.modifier_text}</div>
                          )}
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                            <span className="cart-item-price">
                              {(parseFloat(item.price) * item.quantity).toLocaleString('tr-TR')} ₺
                            </span>
                            <span className={`badge ${item.status === 'served' ? 'badge-success' : 'badge-warning'}`} style={{ fontSize: '10px', padding: '1px 6px' }}>
                              {item.status === 'served' ? <><Check size={10} /> Servis Edildi</>
                                : item.status === 'ready' ? <><Utensils size={10} /> Hazır</>
                                : <><Clock size={10} /> Hazırlanıyor</>}
                            </span>
                          </div>
                          {item.note && <div className="cart-item-note">{item.note}</div>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* New cart items */}
              <div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '600', marginBottom: '8px', textTransform: 'uppercase' }}>
                  Yeni Eklenecekler
                </div>
                {cart.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {cart.map((item) => (
                      <div key={item.cartKey} className="cart-item">
                        <div className="cart-item-details">
                          <div className="cart-item-name">{item.name}</div>
                          {item.modifierText && (
                            <div style={{ fontSize: '10px', color: 'var(--primary)', marginTop: '2px' }}>+ {item.modifierText}</div>
                          )}
                          <div className="cart-item-price" style={{ margin: '4px 0' }}>
                            {item.effectivePrice.toLocaleString('tr-TR')} ₺
                            {item.modifierExtra > 0 && (
                              <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: '4px' }}>
                                (+{parseFloat(item.modifierExtra).toLocaleString('tr-TR')} ₺ ekstra)
                              </span>
                            )}
                          </div>
                          <input
                            type="text"
                            placeholder="Mutfak notu..."
                            value={item.note}
                            onChange={(e) => updateItemNote(item.cartKey, e.target.value)}
                            className="form-control"
                            style={{ padding: '6px 10px', fontSize: '11px', height: '28px', marginTop: '6px' }}
                          />
                        </div>
                        <div className="cart-item-actions">
                          <button className="qty-btn" onClick={() => updateQuantity(item.cartKey, -1)}><Minus size={12} /></button>
                          <span className="qty-val">{item.quantity}</span>
                          <button className="qty-btn" onClick={() => updateQuantity(item.cartKey, 1)}><Plus size={12} /></button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '16px', color: 'var(--text-muted)', fontSize: '13px' }}>
                    Eklenecek ürün seçilmedi
                  </div>
                )}
              </div>
            </div>

            {/* Totals */}
            <div className="cart-totals">
              {existingOrder && (
                <div className="totals-row">
                  <span>Mevcut Tutar:</span>
                  <span>{parseFloat(existingOrder.total_amount).toLocaleString('tr-TR')} ₺</span>
                </div>
              )}
              {cart.length > 0 && (
                <div className="totals-row">
                  <span>Yeni Tutar:</span>
                  <span>{getCartTotal().toLocaleString('tr-TR')} ₺</span>
                </div>
              )}
              {hasDiscount && (
                <div className="totals-row" style={{ color: '#22c55e' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Tag size={12} />
                    İndirim {appliedDiscount?.type === 'percent' ? `(%${appliedDiscount.value})` : `(${appliedDiscount?.value} ₺)`}:
                  </span>
                  <span>-{discountAmount.toLocaleString('tr-TR')} ₺</span>
                </div>
              )}
              <div className="totals-row grand">
                <span>Ödenecek Tutar:</span>
                <span>{getGrandTotal().toLocaleString('tr-TR')} ₺</span>
              </div>
            </div>

            {/* Actions */}
            <div className="cart-actions" style={{ flexWrap: 'wrap', gap: '8px' }}>
              {cart.length > 0 ? (
                <button
                  className="btn btn-primary"
                  onClick={handleSendToKitchen}
                  disabled={loading}
                  style={{ flex: 2 }}
                >
                  <Send size={16} /> Mutfağa Gönder
                </button>
              ) : existingOrder ? (
                <>
                  {/* Discount button */}
                  <button
                    className="btn btn-secondary"
                    onClick={() => { setDiscountType(appliedDiscount?.type || 'percent'); setDiscountValue(appliedDiscount?.value || ''); setDiscountReason(appliedDiscount?.reason || ''); setShowDiscountModal(true); }}
                    style={{ fontSize: '12px', padding: '8px 12px', display: 'flex', alignItems: 'center', gap: '5px' }}
                  >
                    <Tag size={14} /> İndirim
                  </button>
                  <button className="btn btn-secondary" onClick={handleRequestBill} style={{ fontSize: '12px' }}>
                    Hesap İste
                  </button>
                  <button className="btn btn-success" onClick={() => setShowPaymentModal(true)} style={{ fontSize: '12px' }}>
                    Ödeme Al
                  </button>
                </>
              ) : (
                <div style={{ width: '100%', textAlign: 'center', fontSize: '12px', color: 'var(--text-muted)' }}>
                  Sipariş göndermek için soldan ürün ekleyin.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Modifier Selection Modal ── */}
      {showModifierModal && pendingItem && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '420px' }}>
            <div className="modal-header">
              <h3 className="modal-title">Seçenekler — {pendingItem.name}</h3>
              <button className="close-btn" onClick={() => setShowModifierModal(false)}><X size={20} /></button>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Ürüne eklemek istediğiniz seçenekleri işaretleyin.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
              {pendingItem.modifiers.map(mod => {
                const isSelected = selectedModifiers.find(m => m.id === mod.id);
                return (
                  <div
                    key={mod.id}
                    onClick={() => mod.is_available && toggleModifier(mod)}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '12px 14px',
                      borderRadius: '10px',
                      border: `1px solid ${isSelected ? 'var(--primary)' : 'var(--panel-border)'}`,
                      background: isSelected ? 'rgba(99,102,241,0.08)' : 'rgba(255,255,255,0.02)',
                      cursor: mod.is_available ? 'pointer' : 'not-allowed',
                      opacity: mod.is_available ? 1 : 0.4,
                      transition: 'all 0.15s'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{
                        width: '18px', height: '18px', borderRadius: '4px',
                        border: `2px solid ${isSelected ? 'var(--primary)' : 'var(--panel-border)'}`,
                        background: isSelected ? 'var(--primary)' : 'transparent',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        flexShrink: 0
                      }}>
                        {isSelected && <Check size={11} color="#fff" />}
                      </div>
                      <span style={{ fontSize: '13px', fontWeight: '600' }}>{mod.name}</span>
                    </div>
                    <span style={{ fontSize: '13px', color: parseFloat(mod.price_extra) > 0 ? 'var(--success)' : 'var(--text-muted)', fontWeight: '700' }}>
                      {parseFloat(mod.price_extra) > 0 ? `+${parseFloat(mod.price_extra).toLocaleString('tr-TR')} ₺` : 'Ücretsiz'}
                    </span>
                  </div>
                );
              })}
            </div>
            {selectedModifiers.length > 0 && (
              <div style={{ background: 'rgba(99,102,241,0.06)', padding: '10px 14px', borderRadius: '8px', marginBottom: '16px', fontSize: '12px', color: 'var(--text-muted)' }}>
                Toplam ekstra: <strong style={{ color: 'var(--text-main)' }}>
                  +{selectedModifiers.reduce((s, m) => s + parseFloat(m.price_extra), 0).toLocaleString('tr-TR')} ₺
                </strong>
              </div>
            )}
            <button className="btn btn-primary" onClick={confirmModifiers} style={{ width: '100%' }}>
              <Check size={16} /> Seçenekleri Onayla ve Ekle
            </button>
          </div>
        </div>
      )}

      {/* ── Discount Modal ── */}
      {showDiscountModal && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '400px' }}>
            <div className="modal-header">
              <h3 className="modal-title"><Tag size={18} style={{ marginRight: '8px' }} />İndirim Uygula</h3>
              <button className="close-btn" onClick={() => setShowDiscountModal(false)}><X size={20} /></button>
            </div>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
              <button
                type="button"
                onClick={() => setDiscountType('percent')}
                style={{
                  flex: 1, padding: '10px', borderRadius: '10px', border: 'none', cursor: 'pointer',
                  background: discountType === 'percent' ? 'var(--primary)' : 'rgba(255,255,255,0.04)',
                  color: discountType === 'percent' ? '#fff' : 'var(--text-muted)',
                  fontWeight: '600', fontSize: '13px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px'
                }}
              >
                <Percent size={14} /> Yüzde (%)
              </button>
              <button
                type="button"
                onClick={() => setDiscountType('fixed')}
                style={{
                  flex: 1, padding: '10px', borderRadius: '10px', border: 'none', cursor: 'pointer',
                  background: discountType === 'fixed' ? 'var(--primary)' : 'rgba(255,255,255,0.04)',
                  color: discountType === 'fixed' ? '#fff' : 'var(--text-muted)',
                  fontWeight: '600', fontSize: '13px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px'
                }}
              >
                <DollarSign size={14} /> Sabit (₺)
              </button>
            </div>
            <div className="form-group" style={{ marginBottom: '12px' }}>
              <label>{discountType === 'percent' ? 'İndirim Yüzdesi (%)' : 'İndirim Tutarı (₺)'}</label>
              <input
                type="number"
                className="form-control"
                value={discountValue}
                onChange={(e) => setDiscountValue(e.target.value)}
                placeholder={discountType === 'percent' ? 'Örn: 10' : 'Örn: 50'}
                min="0"
                max={discountType === 'percent' ? '100' : undefined}
              />
            </div>
            <div className="form-group" style={{ marginBottom: '20px' }}>
              <label>Gerekçe (Opsiyonel)</label>
              <input
                type="text"
                className="form-control"
                value={discountReason}
                onChange={(e) => setDiscountReason(e.target.value)}
                placeholder="Örn: Sadık müşteri, doğum günü, şikâyet..."
              />
            </div>
            {discountValue && (
              <div style={{ background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '10px', padding: '10px 14px', marginBottom: '16px', fontSize: '13px' }}>
                <strong style={{ color: '#22c55e' }}>
                  {discountType === 'percent'
                    ? `${discountValue}% indirim → -${(getRawTotal() * parseFloat(discountValue) / 100).toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺`
                    : `-${parseFloat(discountValue).toLocaleString('tr-TR')} ₺ indirim`}
                </strong>
                <br />
                <span style={{ color: 'var(--text-muted)' }}>
                  Ödenecek: {Math.max(0, getRawTotal() - (discountType === 'percent' ? getRawTotal() * parseFloat(discountValue) / 100 : parseFloat(discountValue))).toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺
                </span>
              </div>
            )}
            <div style={{ display: 'flex', gap: '10px' }}>
              {appliedDiscount && (
                <button className="btn btn-secondary" onClick={() => { removeDiscount(); setShowDiscountModal(false); }} style={{ flex: 1 }}>
                  <X size={14} /> Kaldır
                </button>
              )}
              <button className="btn btn-primary" onClick={handleApplyDiscount} disabled={!discountValue} style={{ flex: 2 }}>
                <Check size={16} /> Uygula
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Payment Modal ── */}
      {showPaymentModal && existingOrder && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3 className="modal-title">Hesap Kapatma</h3>
              <button className="close-btn" onClick={() => setShowPaymentModal(false)}><X size={20} /></button>
            </div>

            <div className="bill-summary">
              {existingOrder.items.map((item, idx) => (
                <div className="bill-item" key={idx}>
                  <span>{item.quantity}x {item.menu_item_name}{item.modifier_text ? ` (${item.modifier_text})` : ''}</span>
                  <span>{(parseFloat(item.price) * item.quantity).toLocaleString('tr-TR')} ₺</span>
                </div>
              ))}
              {hasDiscount && (
                <div className="bill-item" style={{ color: '#22c55e' }}>
                  <span>🏷️ İndirim {appliedDiscount?.type === 'percent' ? `(%${appliedDiscount.value})` : ''}</span>
                  <span>-{discountAmount.toLocaleString('tr-TR')} ₺</span>
                </div>
              )}
              <div className="bill-total">
                <span>Ödenecek Tutar:</span>
                <span>{getGrandTotal().toLocaleString('tr-TR', { minimumFractionDigits: 2 })} ₺</span>
              </div>
            </div>

            <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px', color: 'var(--text-muted)' }}>Ödeme Yöntemi</h4>
            <div className="payment-methods-grid">
              <div className={`pay-method-card ${paymentMethod === 'card' ? 'active' : ''}`} onClick={() => setPaymentMethod('card')}>
                <CreditCard />
                <span style={{ fontSize: '14px', fontWeight: '600' }}>Kredi Kartı</span>
              </div>
              <div className={`pay-method-card ${paymentMethod === 'cash' ? 'active' : ''}`} onClick={() => setPaymentMethod('cash')}>
                <DollarSign />
                <span style={{ fontSize: '14px', fontWeight: '600' }}>Nakit</span>
              </div>
            </div>

            <button
              className="btn btn-success"
              onClick={handleCheckout}
              disabled={loading}
              style={{ width: '100%', padding: '16px', marginTop: '8px' }}
            >
              Ödemeyi Tamamla ve Masayı Boşalt
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
