import React, { useState, useEffect } from 'react';
import { CreditCard, ArrowUpRight, ArrowDownLeft, Plus, DollarSign } from 'lucide-react';
import { useResponsive } from '../hooks/useResponsive';

import { apiFetch, API_BASE } from '../lib/apiClient';

export default function CashRegister() {
  const { isMobile } = useResponsive();
  const [registers, setRegisters] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Register Actions
  const [selectedRegister, setSelectedRegister] = useState(null);
  const [transType, setTransType] = useState('in'); // 'in' or 'out'
  const [transAmount, setTransAmount] = useState('');
  const [transDesc, setTransDesc] = useState('');
  
  // Register creation
  const [showAddRegister, setShowAddRegister] = useState(false);
  const [newRegName, setNewRegName] = useState('');
  const [newRegBal, setNewRegBal] = useState('');
  const [newRegLoc, setNewRegLoc] = useState('');

  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    fetchRegisters();
  }, []);

  useEffect(() => {
    if (selectedRegister) {
      fetchTransactions(selectedRegister.id);
    }
  }, [selectedRegister]);

  const fetchRegisters = async () => {
    try {
      setLoading(true);
      const res = await apiFetch(`/cash-registers/`);
      const data = await res.json();
      setRegisters(data);
      if (data.length > 0) {
        if (selectedRegister) {
          const updated = data.find(r => r.id === selectedRegister.id);
          setSelectedRegister(updated || data[0]);
        } else {
          setSelectedRegister(data[0]);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTransactions = async (registerId) => {
    if (!registerId) return;
    try {
      const res = await apiFetch(`/cash-transactions/?register=${registerId}`);
      const data = await res.json();
      setTransactions(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleTransaction = async (e) => {
    e.preventDefault();
    if (!transAmount || !selectedRegister) return;

    const amount = parseFloat(transAmount);

    try {
      const res = await apiFetch(`/cash-transactions/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          register: selectedRegister.id,
          transaction_type: transType,
          amount,
          description: transDesc || (transType === 'in' ? 'Para Girişi' : 'Para Çıkışı')
        })
      });

      if (res.ok) {
        await fetchRegisters();
        await fetchTransactions(selectedRegister.id);
        setTransAmount('');
        setTransDesc('');
        alert('İşlem başarıyla gerçekleştirildi.');
      } else {
        alert('İşlem kaydedilemedi.');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateRegister = async (e) => {
    e.preventDefault();
    if (!newRegName || !newRegBal) return;

    try {
      const res = await apiFetch(`/cash-registers/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newRegName,
          balance: parseFloat(newRegBal),
          location: newRegLoc
        })
      });

      if (res.ok) {
        setNewRegName('');
        setNewRegBal('');
        setNewRegLoc('');
        setShowAddRegister(false);
        fetchRegisters();
        alert('Yeni Kasa başarıyla oluşturuldu!');
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 2fr', gap: isMobile ? '16px' : '24px' }}>
      
      {/* Registers List Sidebar */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600' }}>Kasa Listesi</h3>
            <button className="action-icon-btn" onClick={() => setShowAddRegister(!showAddRegister)}>
              <Plus size={18} />
            </button>
          </div>

          {showAddRegister && (
            <form onSubmit={handleCreateRegister} style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px', padding: '12px', border: '1px solid var(--panel-border)', borderRadius: '10px' }}>
              <input type="text" className="form-control" placeholder="Kasa Adı" value={newRegName} onChange={(e) => setNewRegName(e.target.value)} required />
              <input type="number" step="0.01" className="form-control" placeholder="Açılış Bakiyesi (TL)" value={newRegBal} onChange={(e) => setNewRegBal(e.target.value)} required />
              <input type="text" className="form-control" placeholder="Konum / Detay" value={newRegLoc} onChange={(e) => setNewRegLoc(e.target.value)} />
              <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '8px' }}>Oluştur</button>
            </form>
          )}

          {loading ? (
            <div className="spinner"></div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {registers.map(reg => (
                <div 
                  key={reg.id} 
                  onClick={() => setSelectedRegister(reg)}
                  style={{ 
                    padding: '16px', 
                    borderRadius: '12px', 
                    border: '1px solid', 
                    borderColor: selectedRegister?.id === reg.id ? 'var(--primary)' : 'var(--panel-border)',
                    background: selectedRegister?.id === reg.id ? 'rgba(99, 102, 241, 0.1)' : 'rgba(0,0,0,0.02)',
                    cursor: 'pointer',
                    transition: 'var(--transition)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: '600' }}>{reg.name}</span>
                    <CreditCard size={16} style={{ color: selectedRegister?.id === reg.id ? 'var(--primary)' : 'var(--text-muted)' }} />
                  </div>
                  <div style={{ fontSize: '18px', fontWeight: '700', marginTop: '8px', color: 'var(--success)' }}>
                    {parseFloat(reg.balance).toLocaleString('tr-TR')} ₺
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{reg.location || 'Konum belirtilmedi'}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Selected Register Actions & Details */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {selectedRegister ? (
          <>
            {/* Action Form */}
            <div className="card">
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>{selectedRegister.name} - Nakit / Kasa İşlemi</h3>
              <form onSubmit={handleTransaction}>
                <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                  <button 
                    type="button" 
                    className={`btn ${transType === 'in' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ flex: 1, display: 'flex', justifyContent: 'center', gap: '8px', alignItems: 'center' }}
                    onClick={() => setTransType('in')}
                  >
                    <ArrowDownLeft size={16} /> Para Girişi (Tahsilat)
                  </button>
                  <button 
                    type="button" 
                    className={`btn ${transType === 'out' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ flex: 1, display: 'flex', justifyContent: 'center', gap: '8px', alignItems: 'center', background: transType === 'out' ? 'var(--danger)' : '' }}
                    onClick={() => setTransType('out')}
                  >
                    <ArrowUpRight size={16} /> Para Çıkışı (Ödeme)
                  </button>
                </div>

                <div className="form-group">
                  <label>Tutar (TL) *</label>
                  <input type="number" step="0.01" className="form-control" placeholder="0.00" value={transAmount} onChange={(e) => setTransAmount(e.target.value)} required />
                </div>

                <div className="form-group">
                  <label>İşlem Açıklaması</label>
                  <input type="text" className="form-control" placeholder="örn: Sebze toptancısı ödemesi" value={transDesc} onChange={(e) => setTransDesc(e.target.value)} />
                </div>

                <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '12px' }}>
                  İşlemi Kaydet
                </button>
              </form>
            </div>

            {/* Transactions Log */}
            <div className="card">
              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>Son Kasa Hareketleri</h3>
              <div className="table-container">
                <table className="mgmt-table">
                  <thead>
                    <tr>
                      <th>Tür</th>
                      <th>Açıklama</th>
                      <th>Saat</th>
                      <th>Tutar</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map(t => (
                      <tr key={t.id}>
                        <td>
                          {t.transaction_type === 'in' ? (
                            <span style={{ color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', fontWeight: '700' }}>
                              <ArrowDownLeft size={14} /> GİRİŞ
                            </span>
                          ) : (
                            <span style={{ color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', fontWeight: '700' }}>
                              <ArrowUpRight size={14} /> ÇIKIŞ
                            </span>
                          )}
                        </td>
                        <td style={{ fontWeight: '500' }}>{t.description}</td>
                        <td style={{ color: 'var(--text-muted)' }}>
                          {new Date(t.created_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                        </td>
                        <td style={{ fontWeight: '700', color: t.transaction_type === 'in' ? 'var(--success)' : 'var(--danger)' }}>
                          {t.transaction_type === 'in' ? '+' : '-'}{parseFloat(t.amount).toLocaleString('tr-TR')} ₺
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : (
          <div className="card" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: isMobile ? '24px' : '60px', color: 'var(--text-muted)' }}>
            Lütfen sol menüden bir Kasa seçin veya yeni bir Kasa oluşturun.
          </div>
        )}
      </div>

    </div>
  );
}
