import React, { useState, useEffect } from 'react';
import { DollarSign, Trash2, Plus, Calendar, Filter } from 'lucide-react';
import { useResponsive } from '../hooks/useResponsive';

import { apiFetch, API_BASE } from '../lib/apiClient';

export default function Expenses() {
  const { isMobile } = useResponsive();
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Form State
  const [title, setTitle] = useState('');
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('Gıda Malzemesi');
  const [showAddForm, setShowAddForm] = useState(false);
  const [filterCategory, setFilterCategory] = useState('All');

  useEffect(() => {
    fetchExpenses();
  }, []);

  const fetchExpenses = async () => {
    try {
      setLoading(true);
      const res = await apiFetch(`/expenses/`);
      const data = await res.json();
      setExpenses(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddExpense = async (e) => {
    e.preventDefault();
    if (!title || !amount) return;

    try {
      const res = await apiFetch(`/expenses/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          amount: parseFloat(amount),
          category
        })
      });
      if (res.ok) {
        setTitle('');
        setAmount('');
        setShowAddForm(false);
        fetchExpenses();
        alert('Gider başarıyla kaydedildi.');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteExpense = async (id) => {
    if (!confirm('Bu gider kaydını silmek istediğinize emin misiniz?')) return;
    try {
      const res = await apiFetch(`/expenses/${id}/`, { method: 'DELETE' });
      if (res.ok) {
        fetchExpenses();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const filteredExpenses = filterCategory === 'All' 
    ? expenses 
    : expenses.filter(exp => exp.category === filterCategory);

  const totalExpense = filteredExpenses.reduce((sum, exp) => sum + parseFloat(exp.amount), 0);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '2fr 1fr', gap: isMobile ? '16px' : '24px' }}>
      
      {/* Expenses Log */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600' }}>Gider Kayıtları</h3>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <div className="date-badge" style={{ padding: '6px 12px', display: 'flex', gap: '8px', alignItems: 'center' }}>
              <Filter size={14} />
              <select 
                style={{ background: 'transparent', border: 'none', color: 'var(--text-main)', outline: 'none', cursor: 'pointer' }}
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
              >
                <option value="All" style={{ background: 'var(--bg-dark)' }}>Tüm Kategoriler</option>
                <option value="Gıda Malzemesi" style={{ background: 'var(--bg-dark)' }}>Gıda Malzemesi</option>
                <option value="Kira" style={{ background: 'var(--bg-dark)' }}>Kira</option>
                <option value="Fatura" style={{ background: 'var(--bg-dark)' }}>Fatura</option>
                <option value="İnsan Kaynakları" style={{ background: 'var(--bg-dark)' }}>İnsan Kaynakları</option>
                <option value="Diğer" style={{ background: 'var(--bg-dark)' }}>Diğer</option>
              </select>
            </div>
            <button className="btn btn-primary" onClick={() => setShowAddForm(!showAddForm)} style={{ display: 'flex', gap: '6px', alignItems: 'center', fontSize: '13px', padding: '8px 16px' }}>
              <Plus size={16} /> Gider Ekle
            </button>
          </div>
        </div>

        {loading ? (
          <div className="spinner"></div>
        ) : filteredExpenses.length === 0 ? (
          <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-muted)' }}>
            Seçili filtreye ait gider kaydı bulunmuyor.
          </div>
        ) : (
          <div className="table-container">
            <table className="mgmt-table">
              <thead>
                <tr>
                  <th>Açıklama</th>
                  <th>Kategori</th>
                  <th>Tarih</th>
                  <th>Tutar</th>
                  <th>İşlem</th>
                </tr>
              </thead>
              <tbody>
                {filteredExpenses.map(exp => (
                  <tr key={exp.id}>
                    <td style={{ fontWeight: '500' }}>{exp.title}</td>
                    <td>
                      <span className="badge badge-secondary" style={{ background: 'rgba(0,0,0,0.05)' }}>
                        {exp.category}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-muted)' }}>
                      {new Date(exp.date).toLocaleDateString('tr-TR')}
                    </td>
                    <td style={{ fontWeight: '700', color: 'var(--danger)' }}>
                      {parseFloat(exp.amount).toLocaleString('tr-TR')} ₺
                    </td>
                    <td>
                      <button className="action-icon-btn delete" onClick={() => handleDeleteExpense(exp.id)}>
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Stats Summary & Add Form */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Total Expense Card */}
        <div className="card" style={{ background: 'linear-gradient(135deg, rgba(244, 63, 94, 0.06) 0%, rgba(244, 63, 94, 0.01) 100%)' }}>
          <h4 style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '8px' }}>Toplam Harcama</h4>
          <h2 style={{ fontSize: '32px', fontWeight: '800', color: 'var(--danger)' }}>
            {totalExpense.toLocaleString('tr-TR')} ₺
          </h2>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Listelenen verilere göre hesaplanmıştır</span>
        </div>

        {/* Add Form */}
        {showAddForm && (
          <div className="card">
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>Yeni Gider Gir</h3>
            <form onSubmit={handleAddExpense}>
              <div className="form-group">
                <label>Açıklama / Başlık *</label>
                <input type="text" className="form-control" placeholder="örn: Sebze Tedarikçisi" value={title} onChange={(e) => setTitle(e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Tutar (TL) *</label>
                <input type="number" step="0.01" className="form-control" placeholder="0.00" value={amount} onChange={(e) => setAmount(e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Kategori</label>
                <select className="form-control form-select" value={category} onChange={(e) => setCategory(e.target.value)}>
                  <option value="Gıda Malzemesi">Gıda Malzemesi</option>
                  <option value="Kira">Kira</option>
                  <option value="Fatura">Fatura</option>
                  <option value="İnsan Kaynakları">İnsan Kaynakları</option>
                  <option value="Diğer">Diğer</option>
                </select>
              </div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '12px' }}>
                Gideri Kaydet
              </button>
            </form>
          </div>
        )}
      </div>

    </div>
  );
}
