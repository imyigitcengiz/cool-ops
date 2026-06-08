import React, { useState, useEffect, useCallback } from 'react';
import {
  Store, Lock, LogOut, GitBranch, Building2, TrendingUp, ShoppingBag,
  LayoutGrid, Clock, Coffee, Plus, Minus, Send, CreditCard, ArrowLeft, RefreshCw,
} from 'lucide-react';
import { franchiseFetch } from '../lib/franchiseClient';

const STATUS_LABELS = {
  empty: 'Boş',
  occupied: 'Dolu',
  bill_requested: 'Hesap İstendi',
};

const ORDER_STATUS = {
  preparing: 'Hazırlanıyor',
  ready: 'Hazır',
  completed: 'Tamamlandı',
  cancelled: 'İptal',
};

export default function FranchisePortal() {
  const params = new URLSearchParams(window.location.search);
  const [accessCode, setAccessCode] = useState(params.get('code') || '');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState(() => localStorage.getItem('franchise_token') || '');
  const [branch, setBranch] = useState(() => {
    try { return JSON.parse(localStorage.getItem('franchise_branch')); } catch { return null; }
  });
  const [dashboard, setDashboard] = useState(null);
  const [tables, setTables] = useState([]);
  const [orders, setOrders] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedTable, setSelectedTable] = useState(null);
  const [activeOrder, setActiveOrder] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Order screen state
  const [categories, setCategories] = useState([]);
  const [menuItems, setMenuItems] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [cart, setCart] = useState([]);
  const [orderLoading, setOrderLoading] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('card');
  const [showPayment, setShowPayment] = useState(false);

  const fetchAll = useCallback(async () => {
    if (!token) return;
    try {
      const [dashRes, tablesRes, ordersRes] = await Promise.all([
        franchiseFetch('/dashboard/'),
        franchiseFetch('/tables/'),
        franchiseFetch('/orders/?active=true'),
      ]);
      if (!dashRes.ok) {
        handleLogout();
        return;
      }
      const dashData = await dashRes.json();
      setDashboard(dashData);
      setBranch(dashData.branch);
      localStorage.setItem('franchise_branch', JSON.stringify(dashData.branch));
      if (tablesRes.ok) setTables(await tablesRes.json());
      if (ordersRes.ok) setOrders(await ordersRes.json());
    } catch {
      setError('Sunucuya bağlanılamadı.');
    }
  }, [token]);

  useEffect(() => {
    if (token) fetchAll();
  }, [token, fetchAll]);

  useEffect(() => {
    if (!token) return;
    const interval = setInterval(fetchAll, 15000);
    return () => clearInterval(interval);
  }, [token, fetchAll, activeTab]);

  useEffect(() => {
    const onExpired = () => handleLogout();
    window.addEventListener('franchise-session-expired', onExpired);
    return () => window.removeEventListener('franchise-session-expired', onExpired);
  }, []);

  const fetchMenu = async () => {
    const res = await franchiseFetch('/menu/');
    if (res.ok) {
      const data = await res.json();
      setCategories(data.categories || []);
      setMenuItems(data.menu_items || []);
      if (data.categories?.length > 0) setSelectedCategory(data.categories[0].id);
    }
  };

  const openTableOrder = async (table, order) => {
    setSelectedTable(table);
    setActiveOrder(order || null);
    setCart([]);
    setActiveTab('order');
    await fetchMenu();
    if (order?.id) {
      const res = await franchiseFetch(`/orders/${order.id}/`);
      if (res.ok) setActiveOrder(await res.json());
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await franchiseFetch('/login/', {
        method: 'POST',
        body: JSON.stringify({ access_code: accessCode.trim().toLowerCase(), password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Giriş başarısız.');
        return;
      }
      setToken(data.token);
      setBranch(data.branch);
      localStorage.setItem('franchise_token', data.token);
      localStorage.setItem('franchise_branch', JSON.stringify(data.branch));
      setPassword('');
    } catch {
      setError('Sunucuya bağlanılamadı.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    if (token) {
      franchiseFetch('/logout/', { method: 'POST' }).catch(() => {});
    }
    setToken('');
    setBranch(null);
    setDashboard(null);
    setTables([]);
    setOrders([]);
    setSelectedTable(null);
    setActiveOrder(null);
    setActiveTab('overview');
    localStorage.removeItem('franchise_token');
    localStorage.removeItem('franchise_branch');
  };

  const addToCart = (item) => {
    const existing = cart.find((c) => c.id === item.id);
    if (existing) {
      setCart(cart.map((c) => (c.id === item.id ? { ...c, quantity: c.quantity + 1 } : c)));
    } else {
      setCart([...cart, { ...item, quantity: 1, note: '' }]);
    }
  };

  const updateCartQty = (id, delta) => {
    setCart(cart.map((c) => {
      if (c.id !== id) return c;
      const q = c.quantity + delta;
      return q > 0 ? { ...c, quantity: q } : c;
    }).filter((c) => c.quantity > 0));
  };

  const cartTotal = cart.reduce((s, c) => s + parseFloat(c.price) * c.quantity, 0);
  const existingTotal = activeOrder ? parseFloat(activeOrder.total_amount) : 0;
  const grandTotal = existingTotal + cartTotal;

  const handleSendOrder = async () => {
    if (!selectedTable || cart.length === 0) return;
    setOrderLoading(true);
    try {
      const res = await franchiseFetch('/orders/', {
        method: 'POST',
        body: JSON.stringify({
          table: selectedTable.id,
          items: cart.map((c) => ({
            menu_item: c.id,
            quantity: c.quantity,
            note: c.note,
          })),
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setActiveOrder(data);
        setCart([]);
        await fetchAll();
      } else {
        const err = await res.json();
        alert(err.error || 'Sipariş gönderilemedi.');
      }
    } catch {
      alert('Sistem hatası.');
    } finally {
      setOrderLoading(false);
    }
  };

  const handleRequestBill = async () => {
    if (!selectedTable) return;
    const res = await franchiseFetch(`/tables/${selectedTable.id}/change_status/`, {
      method: 'POST',
      body: JSON.stringify({ status: 'bill_requested' }),
    });
    if (res.ok) {
      alert('Hesap istendi olarak işaretlendi.');
      setActiveTab('tables');
      setSelectedTable(null);
      fetchAll();
    }
  };

  const handlePayAndClose = async () => {
    if (!activeOrder) return;
    setOrderLoading(true);
    try {
      const res = await franchiseFetch(`/orders/${activeOrder.id}/pay_and_close/`, {
        method: 'POST',
        body: JSON.stringify({ payment_method: paymentMethod, amount: grandTotal }),
      });
      if (res.ok) {
        setShowPayment(false);
        setActiveOrder(null);
        setSelectedTable(null);
        setCart([]);
        setActiveTab('tables');
        await fetchAll();
        alert('Ödeme alındı, masa kapatıldı.');
      } else {
        const err = await res.json();
        alert(err.error || 'Ödeme tamamlanamadı.');
      }
    } catch {
      alert('Ödeme hatası.');
    } finally {
      setOrderLoading(false);
    }
  };

  const ordersByTable = {};
  orders.forEach((o) => { ordersByTable[o.table] = o; });

  if (!token) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', padding: '24px' }}>
        <div style={{ width: '100%', maxWidth: '420px', background: '#fff', borderRadius: '20px', padding: '32px', boxShadow: '0 25px 60px rgba(0,0,0,0.35)' }}>
          <div style={{ textAlign: 'center', marginBottom: '28px' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '16px', background: 'linear-gradient(135deg, #10b981, #059669)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
              <GitBranch size={28} color="#fff" />
            </div>
            <h1 style={{ margin: '0 0 8px', fontSize: '22px', fontWeight: '800', color: '#0f172a' }}>Franchise Paneli</h1>
            <p style={{ margin: 0, fontSize: '13px', color: '#64748b', lineHeight: 1.5 }}>
              Şube operasyonları: masa yönetimi ve sipariş alma.
            </p>
          </div>
          {error && (
            <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '10px', padding: '12px', marginBottom: '16px', fontSize: '13px', color: '#991b1b' }}>
              {error}
            </div>
          )}
          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '6px' }}>Erişim Kodu</label>
              <input className="form-control" value={accessCode} onChange={(e) => setAccessCode(e.target.value)} placeholder="örn: bidolu-alsancak" required style={{ width: '100%', boxSizing: 'border-box' }} />
            </div>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '6px' }}>Panel Şifresi</label>
              <input className="form-control" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required style={{ width: '100%', boxSizing: 'border-box' }} />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%', padding: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
              <Lock size={16} /> {loading ? 'Giriş yapılıyor...' : 'Panele Giriş Yap'}
            </button>
          </form>
          <p style={{ textAlign: 'center', marginTop: '20px', fontSize: '12px', color: '#94a3b8' }}>
            <a href="/" style={{ color: '#6366f1' }}>Ana platforma dön</a>
          </p>
        </div>
      </div>
    );
  }

  const stats = dashboard?.stats || {};
  const parent = dashboard?.parent_company || {};
  const filteredMenu = menuItems.filter((m) => m.category === selectedCategory);

  const tabBtn = (id, label, Icon) => (
    <button
      key={id}
      onClick={() => { setActiveTab(id); if (id !== 'order') { setSelectedTable(null); setActiveOrder(null); } }}
      style={{
        padding: '8px 14px', fontSize: '13px', fontWeight: '600', borderRadius: '8px', border: 'none',
        cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px',
        background: activeTab === id ? '#10b981' : '#f1f5f9',
        color: activeTab === id ? '#fff' : '#475569',
      }}
    >
      <Icon size={16} /> {label}
    </button>
  );

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-main, #f8fafc)' }}>
      <header style={{ background: '#fff', borderBottom: '1px solid #e2e8f0', padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'linear-gradient(135deg, #10b981, #059669)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Store size={20} color="#fff" />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '16px', fontWeight: '800' }}>{branch?.name || 'Franchise Paneli'}</h1>
            <p style={{ margin: 0, fontSize: '11px', color: '#64748b' }}>{parent.name} — {parent.plan_display}</p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
          <button onClick={fetchAll} className="btn btn-secondary" style={{ padding: '8px 12px', fontSize: '12px' }} title="Yenile">
            <RefreshCw size={14} />
          </button>
          <button onClick={handleLogout} className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
            <LogOut size={14} /> Çıkış
          </button>
        </div>
      </header>

      <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '16px 24px 0', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {tabBtn('overview', 'Özet', LayoutGrid)}
        {tabBtn('tables', 'Masalar & Sipariş', Coffee)}
      </div>

      <main style={{ maxWidth: '1100px', margin: '0 auto', padding: '24px' }}>
        {activeTab === 'overview' && (
          <>
            <div style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '12px', padding: '14px 18px', marginBottom: '24px', fontSize: '13px', color: '#065f46' }}>
              <Building2 size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '8px' }} />
              Operasyon paneli — yalnızca <strong>{branch?.name}</strong> şubesi.
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', marginBottom: '24px' }}>
              <div className="card" style={{ padding: '20px' }}>
                <ShoppingBag size={20} style={{ color: '#6366f1', marginBottom: '8px' }} />
                <div style={{ fontSize: '24px', fontWeight: '800' }}>{stats.today_orders ?? '—'}</div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Bugünkü Sipariş</div>
              </div>
              <div className="card" style={{ padding: '20px' }}>
                <TrendingUp size={20} style={{ color: '#10b981', marginBottom: '8px' }} />
                <div style={{ fontSize: '24px', fontWeight: '800' }}>{stats.today_revenue != null ? `${Number(stats.today_revenue).toLocaleString('tr-TR')} ₺` : '—'}</div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Bugünkü Ciro</div>
              </div>
              <div className="card" style={{ padding: '20px' }}>
                <Clock size={20} style={{ color: '#f59e0b', marginBottom: '8px' }} />
                <div style={{ fontSize: '24px', fontWeight: '800' }}>{stats.active_orders ?? '—'}</div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Aktif Sipariş</div>
              </div>
              <div className="card" style={{ padding: '20px' }}>
                <LayoutGrid size={20} style={{ color: '#8b5cf6', marginBottom: '8px' }} />
                <div style={{ fontSize: '24px', fontWeight: '800' }}>{stats.occupied_tables ?? '—'}/{stats.table_count ?? '—'}</div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>Dolu / Toplam Masa</div>
              </div>
            </div>
            <div className="card">
              <h3 style={{ margin: '0 0 12px', fontSize: '15px', fontWeight: '700' }}>Aktif Siparişler</h3>
              {orders.length === 0 ? (
                <p style={{ margin: 0, fontSize: '13px', color: '#94a3b8' }}>Aktif sipariş yok.</p>
              ) : (
                <div style={{ display: 'grid', gap: '8px' }}>
                  {orders.map((o) => (
                    <div key={o.id} style={{ padding: '10px 12px', background: '#f8fafc', borderRadius: '8px', fontSize: '13px', display: 'flex', justifyContent: 'space-between' }}>
                      <span><strong>#{o.id}</strong> — {o.table_name}</span>
                      <span>{Number(o.total_amount).toLocaleString('tr-TR')} ₺ · {ORDER_STATUS[o.status]}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}

        {activeTab === 'tables' && (
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px' }}>Masalar — sipariş almak için tıklayın</h2>
            {tables.length === 0 ? (
              <p style={{ color: '#94a3b8' }}>Henüz masa tanımlanmamış.</p>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '12px' }}>
                {tables.map((t) => {
                  const order = ordersByTable[t.id];
                  return (
                    <button
                      key={t.id}
                      onClick={() => openTableOrder(t, order)}
                      style={{
                        padding: '16px', borderRadius: '12px', border: '2px solid',
                        borderColor: t.status === 'occupied' ? '#fbbf24' : t.status === 'bill_requested' ? '#f87171' : '#86efac',
                        background: '#fff', cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit',
                      }}
                    >
                      <Coffee size={20} style={{ marginBottom: '8px', color: '#64748b' }} />
                      <div style={{ fontWeight: '800', fontSize: '15px' }}>{t.name}</div>
                      <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>{STATUS_LABELS[t.status] || t.status}</div>
                      {order && (
                        <div style={{ fontSize: '12px', fontWeight: '600', color: '#6366f1', marginTop: '6px' }}>
                          {Number(order.total_amount).toLocaleString('tr-TR')} ₺
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {activeTab === 'order' && selectedTable && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
              <button onClick={() => { setActiveTab('tables'); setSelectedTable(null); setActiveOrder(null); setCart([]); }} className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ArrowLeft size={16} /> Masalar
              </button>
              <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '800' }}>{selectedTable.name} — Sipariş</h2>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(280px, 340px)', gap: '20px' }}>
              <div className="card" style={{ padding: '16px' }}>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '16px' }}>
                  {categories.map((cat) => (
                    <button
                      key={cat.id}
                      onClick={() => setSelectedCategory(cat.id)}
                      className="btn"
                      style={{
                        padding: '6px 12px', fontSize: '12px',
                        background: selectedCategory === cat.id ? '#10b981' : '#f1f5f9',
                        color: selectedCategory === cat.id ? '#fff' : '#475569',
                        border: 'none',
                      }}
                    >
                      {cat.name}
                    </button>
                  ))}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '10px' }}>
                  {filteredMenu.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => addToCart(item)}
                      style={{
                        padding: '12px', borderRadius: '10px', border: '1px solid #e2e8f0',
                        background: '#fff', cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit',
                      }}
                    >
                      <div style={{ fontWeight: '700', fontSize: '13px' }}>{item.name}</div>
                      <div style={{ fontSize: '12px', color: '#10b981', marginTop: '4px' }}>{parseFloat(item.price).toLocaleString('tr-TR')} ₺</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="card" style={{ padding: '16px' }}>
                <h3 style={{ margin: '0 0 12px', fontSize: '15px' }}>Sepet & Ödeme</h3>
                {activeOrder?.items?.length > 0 && (
                  <div style={{ marginBottom: '12px', paddingBottom: '12px', borderBottom: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '6px' }}>Mevcut sipariş</div>
                    {activeOrder.items.map((it) => (
                      <div key={it.id} style={{ fontSize: '12px', display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span>{it.quantity}x {it.menu_item_name}</span>
                        <span>{(parseFloat(it.price) * it.quantity).toLocaleString('tr-TR')} ₺</span>
                      </div>
                    ))}
                  </div>
                )}
                {cart.length === 0 && !activeOrder ? (
                  <p style={{ fontSize: '13px', color: '#94a3b8' }}>Menüden ürün seçin.</p>
                ) : (
                  <>
                    {cart.map((c) => (
                      <div key={c.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', fontSize: '13px' }}>
                        <span>{c.name}</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <button onClick={() => updateCartQty(c.id, -1)} style={{ border: 'none', background: '#f1f5f9', borderRadius: '6px', padding: '2px 6px', cursor: 'pointer' }}><Minus size={14} /></button>
                          <span>{c.quantity}</span>
                          <button onClick={() => updateCartQty(c.id, 1)} style={{ border: 'none', background: '#f1f5f9', borderRadius: '6px', padding: '2px 6px', cursor: 'pointer' }}><Plus size={14} /></button>
                        </div>
                      </div>
                    ))}
                    <div style={{ fontWeight: '800', fontSize: '18px', margin: '16px 0', color: '#0f172a' }}>
                      Toplam: {grandTotal.toLocaleString('tr-TR')} ₺
                    </div>
                    {cart.length > 0 && (
                      <button onClick={handleSendOrder} disabled={orderLoading} className="btn btn-primary" style={{ width: '100%', marginBottom: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                        <Send size={16} /> {orderLoading ? 'Gönderiliyor...' : 'Mutfağa Gönder'}
                      </button>
                    )}
                    {activeOrder && (
                      <>
                        <button onClick={handleRequestBill} className="btn btn-secondary" style={{ width: '100%', marginBottom: '8px' }}>
                          Hesap İste
                        </button>
                        <button onClick={() => setShowPayment(true)} className="btn btn-primary" style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', background: '#6366f1' }}>
                          <CreditCard size={16} /> Ödeme Al & Kapat
                        </button>
                      </>
                    )}
                  </>
                )}
              </div>
            </div>

            {showPayment && (
              <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999, padding: '20px' }}>
                <div className="card" style={{ maxWidth: '400px', width: '100%', padding: '24px' }}>
                  <h3 style={{ margin: '0 0 16px' }}>Ödeme — {grandTotal.toLocaleString('tr-TR')} ₺</h3>
                  <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                    {['card', 'cash'].map((m) => (
                      <button key={m} onClick={() => setPaymentMethod(m)} className="btn" style={{ flex: 1, background: paymentMethod === m ? '#10b981' : '#f1f5f9', color: paymentMethod === m ? '#fff' : '#475569', border: 'none' }}>
                        {m === 'card' ? 'Kart' : 'Nakit'}
                      </button>
                    ))}
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button onClick={() => setShowPayment(false)} className="btn btn-secondary" style={{ flex: 1 }}>İptal</button>
                    <button onClick={handlePayAndClose} disabled={orderLoading} className="btn btn-primary" style={{ flex: 1 }}>Onayla</button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
