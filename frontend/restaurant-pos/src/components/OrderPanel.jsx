import React, { useState, useEffect } from 'react';
import { ShoppingBag, Check, Clock, Truck, RefreshCw, Plus } from 'lucide-react';

import { apiFetch, API_BASE } from '../lib/apiClient';

const PLATFORM_COLORS = {
  'Yemeksepeti': { bg: 'rgba(225, 27, 34, 0.15)', text: '#e11b22', border: 'rgba(225, 27, 34, 0.3)' },
  'Getir': { bg: 'rgba(93, 56, 198, 0.15)', text: '#a855f7', border: 'rgba(93, 56, 198, 0.3)' },
  'Trendyol Yemek': { bg: 'rgba(242, 122, 26, 0.15)', text: '#f27a1a', border: 'rgba(242, 122, 26, 0.3)' },
  'Migros Yemek': { bg: 'rgba(255, 106, 0, 0.15)', text: '#ff8a00', border: 'rgba(255, 106, 0, 0.3)' },
  'WebSitesi': { bg: 'rgba(37, 99, 235, 0.15)', text: '#3b82f6', border: 'rgba(37, 99, 235, 0.3)' }
};

const renderPlatformLogo = (platformName) => {
  switch (platformName) {
    case 'Yemeksepeti':
      return (
        <svg viewBox="0 0 100 100" style={{ width: '20px', height: '20px', marginRight: '8px', borderRadius: '5px' }}>
          <rect width="100" height="100" rx="22" fill="#e11b22" />
          <path d="M50 20 C35 20, 25 35, 25 50 C25 65, 35 80, 50 80 C65 80, 75 65, 75 50 C75 40, 70 30, 60 25 C62 32, 60 40, 55 45 C50 50, 42 48, 42 40 C42 32, 48 27, 50 20 Z" fill="white" />
        </svg>
      );
    case 'Getir':
      return (
        <svg viewBox="0 0 100 100" style={{ width: '20px', height: '20px', marginRight: '8px', borderRadius: '5px' }}>
          <rect width="100" height="100" rx="22" fill="#5d38c6" />
          <circle cx="50" cy="50" r="28" fill="#ffd200" />
          <text x="50" y="58" fontSize="24" fontWeight="900" fill="#5d38c6" textAnchor="middle" fontFamily="sans-serif">g</text>
        </svg>
      );
    case 'Trendyol Yemek':
      return (
        <svg viewBox="0 0 100 100" style={{ width: '20px', height: '20px', marginRight: '8px', borderRadius: '5px' }}>
          <rect width="100" height="100" rx="22" fill="#f27a1a" />
          <text x="50" y="66" fontSize="50" fontWeight="950" fill="white" textAnchor="middle" fontFamily="sans-serif">ty</text>
        </svg>
      );
    case 'Migros Yemek':
      return (
        <svg viewBox="0 0 100 100" style={{ width: '20px', height: '20px', marginRight: '8px', borderRadius: '5px' }}>
          <rect width="100" height="100" rx="22" fill="#ff6a00" />
          <path d="M25 75 L38 25 L50 50 L62 25 L75 75" stroke="white" strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" fill="none" />
          <circle cx="50" cy="20" r="6" fill="#8bc53f" />
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 100 100" style={{ width: '20px', height: '20px', marginRight: '8px', borderRadius: '5px' }}>
          <rect width="100" height="100" rx="22" fill="#2563eb" />
          <circle cx="50" cy="50" r="25" stroke="white" strokeWidth="5" fill="none" />
          <line x1="50" y1="25" x2="50" y2="75" stroke="white" strokeWidth="5" />
          <line x1="25" y1="50" x2="75" y2="50" stroke="white" strokeWidth="5" />
        </svg>
      );
  }
};

export default function OrderPanel() {
  const [orders, setOrders] = useState([]);
  const [couriers, setCouriers] = useState([]);
  const [channels, setChannels] = useState([]);
  const [activeTab, setActiveTab] = useState('All'); // 'All', 'Yemeksepeti', etc.
  const [loading, setLoading] = useState(true);
  
  // Simulating/Adding orders dialog
  const [showSimulateForm, setShowSimulateForm] = useState(false);
  const [simChannel, setSimChannel] = useState('');
  const [simName, setSimName] = useState('');
  const [simTotal, setSimTotal] = useState('');
  
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [ordRes, courRes, chanRes] = await Promise.all([
        apiFetch('/orders/'),
        apiFetch('/couriers/'),
        apiFetch('/order-channels/'),
      ]);
      const ords = await ordRes.json();
      const cours = await courRes.json();
      const chans = await chanRes.json();
      
      setOrders(ords);
      setCouriers(cours);
      setChannels(chans);
      if (chans.length > 0) {
        setSimChannel(chans[0].name);
      }
    } catch (err) {
      console.error('Veriler çekilirken hata oluştu:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (orderId, newStatus) => {
    try {
      const res = await apiFetch(`/orders/${orderId}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) {
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAssignCourier = async (orderId, courierId) => {
    try {
      // Create courier log
      const res = await apiFetch(`/courier-logs/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order: orderId,
          courier: courierId,
          status: 'assigned'
        })
      });
      if (res.ok) {
        // Update order status to ready/preparing or keep track
        await handleUpdateStatus(orderId, 'ready');
        alert('Kurye başarıyla atandı!');
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSimulateOrder = async (e) => {
    e.preventDefault();
    if (!simName || !simTotal) return;

    try {
      // Find the virtual table matching channel
      const tableName = `${simChannel} Paket`;
      // Fetch tables to get the ID
      const tRes = await apiFetch(`/tables/`);
      const tables = await tRes.json();
      let table = tables.find(t => t.name === tableName);
      if (!table) {
        // Create table if not exist
        const tCreate = await apiFetch(`/tables/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: tableName, status: 'occupied', capacity: 1 })
        });
        table = await tCreate.json();
      }

      // Create Order
      const oRes = await apiFetch(`/orders/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          table: table.id,
          status: 'preparing',
          total_amount: parseFloat(simTotal),
          items: [] // simulated empty/external items
        })
      });

      if (oRes.ok) {
        alert('Simüle Sipariş başarıyla oluşturuldu!');
        setSimName('');
        setSimTotal('');
        setShowSimulateForm(false);
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Filter orders that belong to delivery tables
  const deliveryOrders = orders.filter(o => o.table_name && o.table_name.includes('Paket'));

  // Get matching platform branding
  const getPlatformBranding = (tableName) => {
    const cleanName = tableName.replace(' Paket', '');
    return PLATFORM_COLORS[cleanName] || { bg: 'rgba(0,0,0,0.03)', text: '#334155', border: 'rgba(0,0,0,0.08)' };
  };

  const filteredOrders = activeTab === 'All' 
    ? deliveryOrders 
    : deliveryOrders.filter(o => o.table_name.startsWith(activeTab));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button 
            className={`btn ${activeTab === 'All' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('All')}
            style={{ padding: '8px 16px', fontSize: '13px' }}
          >
            Tümü ({deliveryOrders.length})
          </button>
          {channels.map(ch => {
            const count = deliveryOrders.filter(o => o.table_name.startsWith(ch.name)).length;
            return (
              <button 
                key={ch.id}
                className={`btn ${activeTab === ch.name ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setActiveTab(ch.name)}
                style={{ padding: '8px 16px', fontSize: '13px' }}
              >
                {ch.name} ({count})
              </button>
            );
          })}
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn btn-secondary" onClick={fetchData} style={{ padding: '10px' }}>
            <RefreshCw size={16} />
          </button>
          <button className="btn btn-primary" onClick={() => setShowSimulateForm(true)} style={{ display: 'flex', gap: '8px', alignItems: 'center', padding: '10px 16px' }}>
            <Plus size={16} /> Sipariş Simüle Et
          </button>
        </div>
      </div>

      {/* Simulation Modal */}
      {showSimulateForm && (
        <div className="card" style={{ maxWidth: '450px', border: '1px solid var(--primary)', padding: '24px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>Sipariş Simüle Edin</h3>
          <form onSubmit={handleSimulateOrder}>
            <div className="form-group">
              <label>Kanal Seçin</label>
              <select className="form-control form-select" value={simChannel} onChange={(e) => setSimChannel(e.target.value)}>
                {channels.map(ch => (
                  <option key={ch.id} value={ch.name}>{ch.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Müşteri Adı / Sipariş No</label>
              <input type="text" className="form-control" placeholder="örn: Ahmet Y. #9901" value={simName} onChange={(e) => setSimName(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Tutar (TL)</label>
              <input type="number" step="0.01" className="form-control" placeholder="örn: 340.00" value={simTotal} onChange={(e) => setSimTotal(e.target.value)} required />
            </div>
            <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
              <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>Sipariş Gönder</button>
              <button type="button" className="btn btn-secondary" onClick={() => setShowSimulateForm(false)}>Vazgeç</button>
            </div>
          </form>
        </div>
      )}

      {/* Orders List */}
      {loading ? (
        <div className="spinner"></div>
      ) : filteredOrders.length === 0 ? (
        <div className="card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <ShoppingBag size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
          <p>Aktif teslimat / paket siparişi bulunmamaktadır.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
          {filteredOrders.map(order => {
            const branding = getPlatformBranding(order.table_name);
            return (
              <div 
                className="card" 
                key={order.id} 
                style={{ 
                  borderColor: branding.border, 
                  background: `linear-gradient(135deg, ${branding.bg}, rgba(248, 250, 252, 0.8))`,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '16px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    {renderPlatformLogo(order.table_name.replace(' Paket', ''))}
                    <span 
                      style={{ 
                        fontSize: '11px', 
                        fontWeight: '700', 
                        textTransform: 'uppercase', 
                        color: branding.text,
                        padding: '4px 8px',
                        borderRadius: '6px',
                        background: 'rgba(0,0,0,0.04)',
                        border: `1px solid ${branding.border}`
                      }}
                    >
                      {order.table_name.replace(' Paket', '')}
                    </span>
                  </div>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    #{order.id} | {new Date(order.created_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                <div>
                  <h4 style={{ fontSize: '16px', fontWeight: '600' }}>Tutar: {parseFloat(order.total_amount).toLocaleString('tr-TR')} ₺</h4>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Durum: <span style={{ color: order.status === 'completed' ? 'var(--success)' : 'var(--warning)', fontWeight: '600' }}>
                      {order.status === 'preparing' ? 'Mutfakta / Hazırlanıyor' : order.status === 'ready' ? 'Kuryede / Yolda' : order.status === 'completed' ? 'Teslim Edildi' : 'İptal'}
                    </span>
                  </p>
                </div>

                {/* Courier Assignment Section */}
                {order.status === 'preparing' && (
                  <div style={{ borderTop: '1px solid var(--panel-border)', paddingTop: '12px' }}>
                    <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '8px' }}>Kurye Ata</label>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <select 
                        className="form-control form-select" 
                        style={{ padding: '6px 12px', fontSize: '12px' }}
                        onChange={(e) => {
                          if (e.target.value) {
                            handleAssignCourier(order.id, e.target.value);
                          }
                        }}
                        defaultValue=""
                      >
                        <option value="" disabled>Kurye Seçin...</option>
                        {couriers.map(c => (
                          <option key={c.id} value={c.id}>{c.name} ({c.status === 'available' ? 'Müsait' : 'Meşgul'})</option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}

                {/* Action Controls */}
                <div style={{ display: 'flex', gap: '8px', marginTop: 'auto' }}>
                  {order.status === 'preparing' && (
                    <button 
                      className="btn btn-secondary" 
                      onClick={() => handleUpdateStatus(order.id, 'ready')}
                      style={{ flex: 1, display: 'flex', gap: '6px', alignItems: 'center', justifyContent: 'center', fontSize: '12px', padding: '8px' }}
                    >
                      <Clock size={14} /> Yola Çıkar
                    </button>
                  )}
                  {order.status === 'ready' && (
                    <button 
                      className="btn btn-primary" 
                      onClick={() => handleUpdateStatus(order.id, 'completed')}
                      style={{ flex: 1, display: 'flex', gap: '6px', alignItems: 'center', justifyContent: 'center', fontSize: '12px', padding: '8px' }}
                    >
                      <Check size={14} /> Teslim Edildi
                    </button>
                  )}
                  <button 
                    className="btn btn-secondary" 
                    onClick={() => handleUpdateStatus(order.id, 'cancelled')}
                    style={{ color: 'var(--danger)', fontSize: '12px', padding: '8px' }}
                  >
                    İptal
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
