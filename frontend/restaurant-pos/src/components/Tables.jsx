import React, { useState, useEffect } from 'react';
import { Coffee, Users, AlertCircle } from 'lucide-react';

import { apiFetch, API_BASE } from '../lib/apiClient';

export default function Tables({ onSelectTable }) {
  const [tables, setTables] = useState([]);
  const [activeOrders, setActiveOrders] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTablesAndOrders();
    // Refresh table statuses every 15 seconds to stay updated
    const interval = setInterval(fetchTablesAndOrders, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchTablesAndOrders = async () => {
    try {
      // Fetch all tables
      const tablesRes = await apiFetch(`/tables/`);
      const tablesData = await tablesRes.json();
      
      // Fetch all active orders
      const ordersRes = await apiFetch(`/orders/?active=true`);
      const ordersData = await ordersRes.json();
      
      // Map table ID to active order
      const ordersMap = {};
      ordersData.forEach(order => {
        ordersMap[order.table] = order;
      });
      
      setTables(tablesData);
      setActiveOrders(ordersMap);
    } catch (err) {
      console.error('Error fetching tables and orders:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'occupied':
        return 'Dolu';
      case 'bill_requested':
        return 'Hesap İstendi';
      default:
        return 'Boş';
    }
  };

  if (loading) {
    return <div className="spinner"></div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: '600' }}>Masa Durumları</h2>
        <div style={{ display: 'flex', gap: '16px', fontSize: '13px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--success)' }}></span> Boş
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--warning)' }}></span> Dolu
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--danger)' }}></span> Hesap İstendi
          </span>
        </div>
      </div>

      <div className="tables-grid">
        {tables.map(table => {
          const activeOrder = activeOrders[table.id];
          const hasOrder = !!activeOrder;
          
          return (
            <div 
              key={table.id} 
              className={`table-box ${table.status}`}
              onClick={() => onSelectTable(table, activeOrder)}
            >
              <div className="table-icon">
                <Coffee size={24} />
              </div>
              
              <div className="table-box-name">{table.name}</div>
              {table.branch_name && (
                <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>{table.branch_name}</div>
              )}

              <div className="table-box-capacity">
                <Users size={12} /> {table.capacity} Kişilik
              </div>
              
              {hasOrder && (
                <div className="table-box-amount">
                  {parseFloat(activeOrder.total_amount).toLocaleString('tr-TR')} ₺
                </div>
              )}
              
              <div style={{ 
                fontSize: '11px', 
                fontWeight: '600',
                marginTop: '4px',
                color: table.status === 'occupied' ? 'var(--warning)' : table.status === 'bill_requested' ? 'var(--danger)' : 'var(--success)'
              }}>
                {getStatusLabel(table.status)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
