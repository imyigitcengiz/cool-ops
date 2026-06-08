import React, { useState, useEffect } from 'react';
import { Truck, Plus, Check, RefreshCw, DollarSign, Activity, MapPin, Map, Navigation, Compass } from 'lucide-react';
import { useResponsive } from '../hooks/useResponsive';

import { apiFetch, API_BASE } from '../lib/apiClient';

export default function Couriers({ restaurantProfile }) {
  const { isMobile } = useResponsive();
  const [couriers, setCouriers] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  // Form states
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [cashAdvance, setCashAdvance] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);

  // Adjust Cash advance
  const [selectedCourier, setSelectedCourier] = useState(null);
  const [adjustAmount, setAdjustAmount] = useState('');
  const [adjustType, setAdjustType] = useState('add'); // 'add' or 'subtract'

  // Live map states
  const [courierLocations, setCourierLocations] = useState({});
  const [activeCourierId, setActiveCourierId] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (couriers.length === 0) return;
    setCourierLocations(prev => {
      const updated = { ...prev };
      couriers.forEach(c => {
        if (!updated[c.id]) {
          const isOnDelivery = c.status === 'on_delivery';
          updated[c.id] = {
            id: c.id,
            name: c.name,
            x: isOnDelivery ? Math.floor(Math.random() * 300) + 100 : 250,
            y: isOnDelivery ? Math.floor(Math.random() * 150) + 75 : 175,
            destX: isOnDelivery ? Math.floor(Math.random() * 300) + 100 : 250,
            destY: isOnDelivery ? Math.floor(Math.random() * 150) + 75 : 175,
            isMoving: isOnDelivery,
            angle: Math.floor(Math.random() * 360),
            speed: isOnDelivery ? Math.floor(Math.random() * 20) + 40 : 0,
            eta: isOnDelivery ? `${Math.floor(Math.random() * 10) + 2} dk` : '-',
            address: isOnDelivery ? `Atatürk Mah. Rota Sk. No:${Math.floor(Math.random() * 50) + 1}` : 'Restoranda Bekliyor'
          };
        } else {
          const isOnDelivery = c.status === 'on_delivery';
          updated[c.id].isMoving = isOnDelivery;
          if (!isOnDelivery) {
            updated[c.id].x = 250;
            updated[c.id].y = 175;
            updated[c.id].destX = 250;
            updated[c.id].destY = 175;
            updated[c.id].speed = 0;
            updated[c.id].eta = '-';
            updated[c.id].address = 'Restoranda Bekliyor';
          } else if (!prev[c.id]?.isMoving) {
            updated[c.id].destX = Math.floor(Math.random() * 300) + 100;
            updated[c.id].destY = Math.floor(Math.random() * 150) + 75;
            updated[c.id].speed = Math.floor(Math.random() * 20) + 40;
            updated[c.id].eta = `${Math.floor(Math.random() * 10) + 4} dk`;
            updated[c.id].address = `İnönü Cad. Sokak ${Math.floor(Math.random() * 80) + 1} No:${Math.floor(Math.random() * 15) + 1}`;
          }
        }
      });
      return updated;
    });
  }, [couriers]);

  useEffect(() => {
    if (!restaurantProfile?.ext_live_courier_enabled) return;

    const interval = setInterval(() => {
      setCourierLocations(prev => {
        const next = { ...prev };
        let updated = false;
        Object.keys(next).forEach(id => {
          const loc = next[id];
          if (loc.isMoving) {
            let dx = loc.destX - loc.x;
            let dy = loc.destY - loc.y;
            let distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < 5) {
              if (loc.destX === 250 && loc.destY === 175) {
                loc.destX = Math.floor(Math.random() * 300) + 100;
                loc.destY = Math.floor(Math.random() * 150) + 75;
                loc.address = `Mithatpaşa Cad. Sokak ${Math.floor(Math.random()*100)+1} No:${Math.floor(Math.random()*20)+1}`;
                loc.eta = `${Math.floor(Math.random() * 10) + 3} dk`;
                loc.speed = Math.floor(Math.random() * 20) + 40;
              } else {
                loc.destX = 250;
                loc.destY = 175;
                loc.address = 'Restorana Dönüyor';
                loc.eta = '2 dk';
                loc.speed = Math.floor(Math.random() * 15) + 30;
              }
            } else {
              const speedFactor = 2.5;
              loc.x += (dx / distance) * speedFactor;
              loc.y += (dy / distance) * speedFactor;
              loc.x += (Math.random() - 0.5) * 1.0;
              loc.y += (Math.random() - 0.5) * 1.0;
              loc.angle = Math.atan2(dy, dx) * (180 / Math.PI);
            }
            updated = true;
          }
        });
        return updated ? next : prev;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [restaurantProfile?.ext_live_courier_enabled]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [courRes, logsRes] = await Promise.all([
        apiFetch('/couriers/'),
        apiFetch('/courier-logs/'),
      ]);
      const cours = await courRes.json();
      const lgs = await logsRes.json();
      setCouriers(cours);
      setLogs(lgs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCourier = async (e) => {
    e.preventDefault();
    if (!name) return;

    try {
      const res = await apiFetch(`/couriers/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          phone,
          cash_advance_amount: parseFloat(cashAdvance || 0),
          status: 'available'
        })
      });

      if (res.ok) {
        setName('');
        setPhone('');
        setCashAdvance('');
        setShowAddForm(false);
        fetchData();
        alert('Kurye başarıyla tanımlandı.');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdateStatus = async (id, currentStatus) => {
    const newStatus = currentStatus === 'available' ? 'on_delivery' : 'available';
    try {
      const res = await apiFetch(`/couriers/${id}/`, {
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

  const handleAdjustAdvance = async (e) => {
    e.preventDefault();
    if (!selectedCourier || !adjustAmount) return;

    const amount = parseFloat(adjustAmount);
    let newAmount = parseFloat(selectedCourier.cash_advance_amount);

    if (adjustType === 'add') {
      newAmount += amount;
    } else {
      newAmount -= amount;
    }

    try {
      const res = await apiFetch(`/couriers/${selectedCourier.id}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cash_advance_amount: newAmount })
      });

      if (res.ok) {
        setSelectedCourier(null);
        setAdjustAmount('');
        fetchData();
        alert('Kurye kasası / avansı güncellendi.');
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '2fr 1.2fr', gap: isMobile ? '16px' : '24px' }}>
      
      {/* Couriers List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        {restaurantProfile?.ext_live_courier_enabled && (
          <div className="card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <MapPin size={20} style={{ color: '#f59e0b' }} />
                <h3 style={{ fontSize: '18px', fontWeight: '600', margin: 0 }}>Canlı Kurye Lokasyon Takibi</h3>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-muted)' }}>
                <span className="pulse-dot" style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b', marginRight: '4px' }}></span>
                Anlık Canlı Rota Takip Sistemi
              </div>
            </div>

            {/* Map Container */}
            <div style={{ 
              position: 'relative', 
              width: '100%', 
              height: '300px', 
              background: '#0b0f19', 
              borderRadius: '12px', 
              border: '1px solid var(--panel-border)',
              overflow: 'hidden'
            }}>
              {/* Grid road layout representation (SVG overlay) */}
              <svg style={{ position: 'absolute', width: '100%', height: '100%', pointerEvents: 'none', opacity: 0.2 }}>
                {/* Horizontal major streets */}
                <line x1="0" y1="90" x2="100%" y2="90" stroke="#fff" strokeWidth="6" strokeDasharray="3 3" />
                <line x1="0" y1="175" x2="100%" y2="175" stroke="#fff" strokeWidth="12" />
                <line x1="0" y1="260" x2="100%" y2="260" stroke="#fff" strokeWidth="6" strokeDasharray="3 3" />
                
                {/* Vertical major streets */}
                <line x1="90" y1="0" x2="90" y2="100%" stroke="#fff" strokeWidth="6" strokeDasharray="3 3" />
                <line x1="250" y1="0" x2="250" y2="100%" stroke="#fff" strokeWidth="12" />
                <line x1="410" y1="0" x2="410" y2="100%" stroke="#fff" strokeWidth="6" strokeDasharray="3 3" />

                {/* Rotunda / Alsancak Square */}
                <circle cx="250" cy="175" r="50" fill="none" stroke="#fff" strokeWidth="12" />

                {/* Secondary diagonal street */}
                <line x1="0" y1="0" x2="100%" y2="100%" stroke="#fff" strokeWidth="4" strokeOpacity="0.5" />
                <line x1="100%" y1="0" x2="0" y2="100%" stroke="#fff" strokeWidth="4" strokeOpacity="0.5" />
              </svg>

              {/* Styled Buildings */}
              <div style={{ position: 'absolute', top: '25px', left: '25px', width: '45px', height: '45px', background: 'rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.06)', borderRadius: '6px' }}></div>
              <div style={{ position: 'absolute', top: '25px', left: '120px', width: '90px', height: '45px', background: 'rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.06)', borderRadius: '6px' }}></div>
              <div style={{ position: 'absolute', top: '25px', left: '280px', width: '90px', height: '45px', background: 'rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.06)', borderRadius: '6px' }}></div>
              <div style={{ position: 'absolute', top: '115px', left: '120px', width: '90px', height: '35px', background: 'rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.06)', borderRadius: '6px' }}></div>
              <div style={{ position: 'absolute', top: '115px', left: '280px', width: '90px', height: '35px', background: 'rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.06)', borderRadius: '6px' }}></div>
              <div style={{ position: 'absolute', top: '205px', left: '120px', width: '90px', height: '35px', background: 'rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.06)', borderRadius: '6px' }}></div>
              <div style={{ position: 'absolute', top: '205px', left: '280px', width: '90px', height: '35px', background: 'rgba(0,0,0,0.04)', border: '1px solid rgba(0,0,0,0.06)', borderRadius: '6px' }}></div>

              {/* Restaurant Center Point */}
              <div style={{ 
                position: 'absolute', 
                left: '250px', 
                top: '175px', 
                transform: 'translate(-50%, -50%)',
                zIndex: 10
              }}>
                <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <div style={{ position: 'absolute', width: '30px', height: '30px', borderRadius: '50%', background: 'rgba(99, 102, 241, 0.2)', border: '1px solid rgba(99, 102, 241, 0.4)', animation: 'ping 2s infinite' }}></div>
                  <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#6366f1', border: '2px solid #fff', zIndex: 2 }}></div>
                </div>
                <div style={{ position: 'absolute', top: '16px', left: '50%', transform: 'translateX(-50%)', background: 'rgba(11, 15, 25, 0.85)', padding: '2px 8px', borderRadius: '4px', border: '1px solid var(--panel-border)', fontSize: '10px', color: '#fff', whiteSpace: 'nowrap', fontWeight: '700' }}>
                  Kobi Kebap (Merkez)
                </div>
              </div>

              {/* Courier target routes and destination pins */}
              {Object.values(courierLocations).map(loc => {
                if (!loc.isMoving) return null;
                const isActive = activeCourierId === loc.id;
                return (
                  <React.Fragment key={`route-${loc.id}`}>
                    {/* Route Line */}
                    <svg style={{ position: 'absolute', width: '100%', height: '100%', pointerEvents: 'none', zIndex: 1 }}>
                      <line 
                        x1="250" 
                        y1="175" 
                        x2={loc.x} // Rota çizgisi kuryeye kadar çekilsin
                        y2={loc.y} 
                        stroke={isActive ? '#f59e0b' : 'rgba(245, 158, 11, 0.25)'} 
                        strokeWidth={isActive ? '2' : '1'} 
                        strokeDasharray="4 4"
                      />
                      <line 
                        x1={loc.x} 
                        y1={loc.y} 
                        x2={loc.destX} 
                        y2={loc.destY} 
                        stroke="rgba(239, 68, 68, 0.3)" 
                        strokeWidth="1" 
                        strokeDasharray="2 2"
                      />
                    </svg>
                    
                    {/* Destination Pin */}
                    <div style={{ 
                      position: 'absolute', 
                      left: `${loc.destX}px`, 
                      top: `${loc.destY}px`, 
                      transform: 'translate(-50%, -100%)',
                      zIndex: 3,
                      cursor: 'pointer'
                    }} onClick={() => setActiveCourierId(loc.id)}>
                      <MapPin size={isActive ? 22 : 16} style={{ color: isActive ? '#f59e0b' : '#ef4444', filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.5))' }} />
                    </div>
                  </React.Fragment>
                );
              })}

              {/* Moving Courier Avatars */}
              {Object.values(courierLocations).map(loc => {
                const isActive = activeCourierId === loc.id;
                return (
                  <div 
                    key={`courier-${loc.id}`}
                    style={{ 
                      position: 'absolute', 
                      left: `${loc.x}px`, 
                      top: `${loc.y}px`, 
                      transform: 'translate(-50%, -50%)',
                      zIndex: 5,
                      cursor: 'pointer',
                      transition: 'left 1s linear, top 1s linear'
                    }}
                    onClick={() => setActiveCourierId(loc.id)}
                  >
                    <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {loc.isMoving && (
                        <div style={{ 
                          position: 'absolute', 
                          width: '24px', 
                          height: '24px', 
                          borderRadius: '50%', 
                          background: isActive ? 'rgba(245, 158, 11, 0.25)' : 'rgba(16, 185, 129, 0.2)',
                          animation: 'pulse 1.5s infinite' 
                        }}></div>
                      )}
                      <div style={{ 
                        width: '20px', 
                        height: '20px', 
                        borderRadius: '50%', 
                        background: loc.isMoving ? (isActive ? '#f59e0b' : '#10b981') : 'var(--text-muted)', 
                        border: '2px solid #fff', 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center',
                        color: '#fff',
                        boxShadow: '0 2px 6px rgba(0,0,0,0.4)'
                      }}>
                        <Truck size={10} />
                      </div>
                      
                      {/* Name Label */}
                      <span style={{ 
                        position: 'absolute', 
                        bottom: '22px', 
                        background: isActive ? '#f59e0b' : 'rgba(0,0,0,0.75)', 
                        color: '#fff', 
                        padding: '1px 5px', 
                        borderRadius: '4px', 
                        fontSize: '9.5px', 
                        fontWeight: '700',
                        whiteSpace: 'nowrap',
                        border: isActive ? '1px solid #fff' : '1px solid rgba(255,255,255,0.1)',
                        pointerEvents: 'none'
                      }}>
                        {loc.name.split(' ')[0]}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Courier Info Popovers / Quick Panel */}
            {activeCourierId && courierLocations[activeCourierId] && (
              <div style={{ 
                padding: '14px', 
                borderRadius: '10px', 
                background: 'rgba(245, 158, 11, 0.04)', 
                border: '1px solid rgba(245, 158, 11, 0.2)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <strong style={{ fontSize: '14px' }}>{courierLocations[activeCourierId].name}</strong>
                    <span className={`badge ${courierLocations[activeCourierId].isMoving ? 'badge-danger' : 'badge-success'}`} style={{ fontSize: '10px', padding: '2px 6px' }}>
                      {courierLocations[activeCourierId].isMoving ? 'Teslimatta' : 'Müsait'}
                    </span>
                  </div>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    📍 {courierLocations[activeCourierId].address}
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '16px', textAlign: 'right' }}>
                  {courierLocations[activeCourierId].isMoving && (
                    <>
                      <div>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block' }}>Hız</span>
                        <strong style={{ fontSize: '13px', color: '#f59e0b' }}>{courierLocations[activeCourierId].speed} km/s</strong>
                      </div>
                      <div>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block' }}>ETA (Tahmini)</span>
                        <strong style={{ fontSize: '13px', color: '#10b981' }}>{courierLocations[activeCourierId].eta}</strong>
                      </div>
                    </>
                  )}
                  <button 
                    onClick={() => setActiveCourierId(null)} 
                    className="btn btn-secondary" 
                    style={{ padding: '4px 8px', fontSize: '11px', height: 'fit-content', alignSelf: 'center' }}
                  >
                    Kapat
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600' }}>Kurye Durum ve Paraüstü Takibi</h3>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button className="btn btn-secondary" onClick={fetchData} style={{ padding: '8px' }}>
                <RefreshCw size={16} />
              </button>
              <button className="btn btn-primary" onClick={() => setShowAddForm(!showAddForm)} style={{ display: 'flex', gap: '6px', alignItems: 'center', fontSize: '13px', padding: '8px 16px' }}>
                <Plus size={16} /> Kurye Ekle
              </button>
            </div>
          </div>

          {loading ? (
            <div className="spinner"></div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
              {couriers.map(c => (
                <div key={c.id} style={{ padding: '16px', border: '1px solid var(--panel-border)', borderRadius: '12px', background: 'rgba(0,0,0,0.02)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: '600', fontSize: '16px' }}>{c.name}</span>
                    <span 
                      onClick={() => handleUpdateStatus(c.id, c.status)}
                      className={`badge ${c.status === 'available' ? 'badge-success' : 'badge-danger'}`}
                      style={{ cursor: 'pointer' }}
                    >
                      {c.status === 'available' ? 'Müsait' : 'Teslimatta'}
                    </span>
                  </div>

                  <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                    <div>Telefon: {c.phone || 'Girilmedi'}</div>
                    <div style={{ marginTop: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span>Taşınan Paraüstü Avansı:</span>
                      <strong style={{ color: 'var(--success)', fontSize: '15px' }}>{parseFloat(c.cash_advance_amount).toLocaleString('tr-TR')} ₺</strong>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                    <button 
                      className="btn btn-secondary" 
                      onClick={() => setSelectedCourier(c)}
                      style={{ flex: 1, padding: '6px 12px', fontSize: '12px' }}
                    >
                      Paraüstü Düzenle
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Courier Logs */}
        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>Son Kurye Teslimatları</h3>
          <div className="table-container">
            <table className="mgmt-table">
              <thead>
                <tr>
                  <th>Kurye</th>
                  <th>Sipariş</th>
                  <th>Zaman</th>
                  <th>Durum</th>
                </tr>
              </thead>
              <tbody>
                {logs.slice(0, 8).map(log => (
                  <tr key={log.id}>
                    <td style={{ fontWeight: '600' }}>
                      {couriers.find(c => c.id === log.courier)?.name || 'Kurye'}
                    </td>
                    <td>Sipariş #{log.order}</td>
                    <td style={{ color: 'var(--text-muted)' }}>
                      {new Date(log.timestamp).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td>
                      <span className="badge badge-success">Teslim Edildi</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Forms Sidebar */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Adjust Advance Form */}
        {selectedCourier && (
          <div className="card" style={{ border: '1px solid var(--primary)' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>
              Paraüstü Avansını Düzenle: <br /> <span style={{ color: 'var(--primary)' }}>{selectedCourier.name}</span>
            </h3>
            <form onSubmit={handleAdjustAdvance}>
              <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                <button 
                  type="button" 
                  className={`btn ${adjustType === 'add' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ flex: 1, fontSize: '12px', padding: '6px' }}
                  onClick={() => setAdjustType('add')}
                >
                  Ekle
                </button>
                <button 
                  type="button" 
                  className={`btn ${adjustType === 'subtract' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ flex: 1, fontSize: '12px', padding: '6px' }}
                  onClick={() => setAdjustType('subtract')}
                >
                  Geri Al
                </button>
              </div>
              <div className="form-group">
                <label>Tutar (TL)</label>
                <input type="number" step="0.01" className="form-control" placeholder="0.00" value={adjustAmount} onChange={(e) => setAdjustAmount(e.target.value)} required />
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>Kaydet</button>
                <button type="button" className="btn btn-secondary" onClick={() => setSelectedCourier(null)}>Vazgeç</button>
              </div>
            </form>
          </div>
        )}

        {/* Add Courier Form */}
        {showAddForm && (
          <div className="card">
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>Kurye Kaydı</h3>
            <form onSubmit={handleCreateCourier}>
              <div className="form-group">
                <label>Kurye Adı *</label>
                <input type="text" className="form-control" placeholder="örn: Murat Can" value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Telefon</label>
                <input type="text" className="form-control" placeholder="05XX XXX XX XX" value={phone} onChange={(e) => setPhone(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Açılış Paraüstü Avansı</label>
                <input type="number" step="0.01" className="form-control" placeholder="100.00" value={cashAdvance} onChange={(e) => setCashAdvance(e.target.value)} />
              </div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '12px' }}>
                Kuryeyi Kaydet
              </button>
            </form>
          </div>
        )}
      </div>

    </div>
  );
}
