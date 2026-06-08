import React, { useState, useEffect } from 'react';
import { Clock, Check, RefreshCw } from 'lucide-react';

import { apiFetch, API_BASE } from '../lib/apiClient';

export default function Kitchen() {
  const [activeOrders, setActiveOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchActiveOrders();
    // Poll the kitchen screen every 10 seconds to get new orders automatically
    const interval = setInterval(fetchActiveOrders, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchActiveOrders = async () => {
    try {
      // Fetch all active orders (excluding completed and cancelled)
      const res = await apiFetch(`/orders/?active=true`);
      const data = await res.json();
      
      // Sort orders: oldest first so we prioritize first-come-first-served
      const sorted = data.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
      setActiveOrders(sorted);
    } catch (err) {
      console.error('Error fetching kitchen orders:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleItemStatusChange = async (itemId, newStatus) => {
    try {
      const res = await apiFetch(`/order-items/${itemId}/change_status/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) {
        // Refresh local state
        fetchActiveOrders();
      }
    } catch (err) {
      console.error('Error changing item status:', err);
    }
  };

  const getElapsedTime = (createdAt) => {
    const created = new Date(createdAt);
    const diff = Math.floor((new Date() - created) / 60000); // Difference in minutes
    if (diff < 1) return 'Yeni';
    return `${diff} dk önce`;
  };

  if (loading) {
    return <div className="spinner"></div>;
  }

  // Filter orders that have at least one item still preparing or ready (not served)
  const kitchenOrders = activeOrders.filter(order => 
    order.items && order.items.some(item => item.status !== 'served' && item.status !== 'cancelled')
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: '600' }}>Mutfak Sipariş Paneli</h2>
        <button onClick={fetchActiveOrders} className="btn btn-secondary" style={{ padding: '8px 14px', fontSize: '13px', display: 'flex', gap: '6px' }}>
          <RefreshCw size={14} /> Yenile
        </button>
      </div>

      {kitchenOrders.length === 0 ? (
        <div style={{ 
          background: 'var(--panel-bg)', 
          border: '1px solid var(--panel-border)', 
          borderRadius: '16px', 
          padding: '40px', 
          textAlign: 'center', 
          color: 'var(--text-muted)' 
        }}>
          Aktif hazırlanacak sipariş bulunmuyor.
        </div>
      ) : (
        <div className="kitchen-container">
          {kitchenOrders.map(order => {
            // Count items in preparing vs total
            const itemsToPrepare = order.items.filter(item => item.status !== 'served' && item.status !== 'cancelled');
            const allReady = itemsToPrepare.every(item => item.status === 'ready');
            
            return (
              <div key={order.id} className={`kitchen-card ${allReady ? 'ready' : ''}`}>
                <div className="kitchen-card-header">
                  <div>
                    <span className="kitchen-table-name">{order.table_name}</span>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>Sipariş #{order.id}</div>
                  </div>
                  <span className="kitchen-time" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} /> {getElapsedTime(order.created_at)}
                  </span>
                </div>

                <div className="kitchen-items-list">
                  {itemsToPrepare.map((item, idx) => (
                    <div 
                      key={idx} 
                      className={`kitchen-item ${item.status}`}
                    >
                      <div style={{ flex: 1 }}>
                        <div className="kitchen-item-text">
                          <span className="kitchen-item-qty">{item.quantity}x</span>
                          {item.menu_item_name}
                        </div>
                        {item.note && <div className="kitchen-item-note">Not: {item.note}</div>}
                      </div>
                      
                      <div>
                        {item.status === 'preparing' ? (
                          <button 
                            className="btn btn-success" 
                            style={{ padding: '4px 8px', fontSize: '11px', borderRadius: '6px' }}
                            onClick={() => handleItemStatusChange(item.id, 'ready')}
                          >
                            ✓ Hazır
                          </button>
                        ) : (
                          <button 
                            className="btn btn-secondary" 
                            style={{ padding: '4px 8px', fontSize: '11px', borderRadius: '6px', color: 'var(--success)' }}
                            onClick={() => handleItemStatusChange(item.id, 'served')}
                          >
                            Servis Et
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                
                {allReady && (
                  <div style={{ 
                    fontSize: '12px', 
                    fontWeight: '600', 
                    color: 'var(--success)', 
                    textAlign: 'center',
                    background: 'var(--success-glow)',
                    padding: '8px',
                    borderRadius: '8px',
                    marginTop: '8px'
                  }}>
                    Tüm ürünler hazırlandı! Garson servisi bekliyor.
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
