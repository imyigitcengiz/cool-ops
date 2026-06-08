import React, { useState, useEffect } from 'react';
import { GitBranch, Plus, RefreshCw, MapPin, Phone, Trash2, Store, Lock, Copy, ExternalLink, Shield } from 'lucide-react';
import { useResponsive } from '../hooks/useResponsive';

import { apiFetch, API_BASE } from '../lib/apiClient';

export default function FranchiseManagement({ authToken, currentUser }) {
  const { isMobile } = useResponsive();
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [passwordModal, setPasswordModal] = useState(null);
  const [panelPassword, setPanelPassword] = useState('');
  const [panelEnabled, setPanelEnabled] = useState(true);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const [name, setName] = useState('');
  const [city, setCity] = useState('');
  const [address, setAddress] = useState('');
  const [phone, setPhone] = useState('');

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Token ${authToken}`,
  };

  const brandPlan = currentUser?.brand?.plan || 'starter';
  const planLabel = { starter: 'Starter', growth: 'Growth', enterprise: 'Enterprise' }[brandPlan] || brandPlan;
  const branchUsage = currentUser?.brand?.usage?.branches ?? branches.length;
  const branchLimit = currentUser?.brand?.limits?.branches ?? '—';

  useEffect(() => { fetchBranches(); }, [authToken]);

  const fetchBranches = async () => {
    try {
      setLoading(true);
      const res = await apiFetch(`${API_BASE}/branches/`, { headers });
      if (res.ok) setBranches(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const res = await apiFetch(`${API_BASE}/branches/`, {
        method: 'POST', headers,
        body: JSON.stringify({ name, city, address, phone, is_active: true }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Şube oluşturulamadı.');
        return;
      }
      setName(''); setCity(''); setAddress(''); setPhone('');
      setShowAdd(false);
      setMessage('Franchise/şube oluşturuldu. Panel şifresini belirleyin.');
      fetchBranches();
      setTimeout(() => setMessage(''), 4000);
    } catch {
      setError('Sunucu hatası.');
    }
  };

  const handleSetPassword = async (e) => {
    e.preventDefault();
    if (!passwordModal) return;
    setError('');
    try {
      const res = await apiFetch(`${API_BASE}/branches/${passwordModal.id}/panel-access/`, {
        method: 'POST', headers,
        body: JSON.stringify({ password: panelPassword, panel_enabled: panelEnabled }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Şifre kaydedilemedi.');
        return;
      }
      setPasswordModal(null);
      setPanelPassword('');
      setMessage('Franchise panel şifresi güncellendi.');
      fetchBranches();
      setTimeout(() => setMessage(''), 4000);
    } catch {
      setError('Sunucu hatası.');
    }
  };

  const handleToggle = async (branch) => {
    await apiFetch(`${API_BASE}/branches/${branch.id}/`, {
      method: 'PATCH', headers,
      body: JSON.stringify({ is_active: !branch.is_active }),
    });
    fetchBranches();
  };

  const handleDelete = async (id) => {
    if (!confirm('Bu franchise/şubeyi silmek istediğinize emin misiniz?')) return;
    await apiFetch(`${API_BASE}/branches/${id}/`, { method: 'DELETE', headers });
    fetchBranches();
  };

  const copyPanelLink = (branch) => {
    const url = `${window.location.origin}/franchise?code=${branch.panel_slug}`;
    navigator.clipboard?.writeText(url);
    setMessage('Panel bağlantısı kopyalandı.');
    setTimeout(() => setMessage(''), 2500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="card" style={{ background: 'linear-gradient(135deg, rgba(16,185,129,0.08) 0%, rgba(5,150,105,0.04) 100%)', border: '1px solid rgba(16,185,129,0.2)' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <Shield size={22} style={{ color: '#059669', marginTop: '2px' }} />
          <div>
            <h3 style={{ margin: '0 0 6px', fontSize: '16px', fontWeight: '700' }}>Franchise (Şube) Merkezi</h3>
            <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              Yalnızca <strong>kurum yöneticisi</strong> franchise oluşturabilir. Tüm şubeler ana şirketinizin
              <strong> {planLabel}</strong> planı kapsamında çalışır — ayrı plan tanımlanmaz.
              Her şube için harici panel şifresini siz belirlersiniz.
            </p>
          </div>
        </div>
      </div>

      {message && (
        <div style={{ background: '#ecfdf5', border: '1px solid #10b981', borderRadius: '10px', padding: '12px 16px', fontSize: '13px', color: '#065f46' }}>
          {message}
        </div>
      )}
      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '10px', padding: '12px 16px', fontSize: '13px', color: '#991b1b' }}>
          {error}
        </div>
      )}

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <GitBranch size={20} style={{ color: '#10b981' }} />
            <h3 style={{ margin: 0, fontSize: '15px', fontWeight: '800' }}>
              Şube & Franchise Listesi
              <span style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', marginLeft: '8px' }}>
                ({branchUsage}/{branchLimit})
              </span>
            </h3>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={fetchBranches} className="btn btn-secondary" style={{ padding: '8px 12px' }}>
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
            </button>
            <button onClick={() => setShowAdd(!showAdd)} className="btn btn-primary" style={{ padding: '8px 16px', fontSize: '12px', display: 'flex', gap: '6px', alignItems: 'center' }}>
              <Plus size={14} /> Yeni Franchise
            </button>
          </div>
        </div>

        {showAdd && (
          <form onSubmit={handleAdd} style={{ background: 'rgba(16,185,129,0.04)', border: '1px solid rgba(16,185,129,0.15)', borderRadius: '12px', padding: '16px', marginBottom: '20px', display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '12px' }}>
            <div className="form-group" style={{ gridColumn: isMobile ? 'auto' : 'span 2' }}>
              <label>Şube / Franchise Adı *</label>
              <input className="form-control" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Şehir</label>
              <input className="form-control" value={city} onChange={(e) => setCity(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Telefon</label>
              <input className="form-control" value={phone} onChange={(e) => setPhone(e.target.value)} />
            </div>
            <div className="form-group" style={{ gridColumn: isMobile ? 'auto' : 'span 2' }}>
              <label>Adres</label>
              <textarea className="form-control" rows="2" value={address} onChange={(e) => setAddress(e.target.value)} />
            </div>
            <button type="submit" className="btn btn-primary" style={{ gridColumn: isMobile ? 'auto' : 'span 2' }}>Oluştur</button>
          </form>
        )}

        {loading ? (
          <div className="spinner" style={{ margin: '30px auto' }} />
        ) : branches.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
            <Store size={32} style={{ opacity: 0.3, margin: '0 auto 10px' }} />
            Henüz franchise/şube tanımlanmadı.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
            {branches.map((branch) => (
              <div key={branch.id} style={{ border: '1px solid var(--panel-border)', borderRadius: '12px', padding: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '800' }}>{branch.name}</h4>
                  <span style={{ fontSize: '10px', fontWeight: '700', padding: '2px 8px', borderRadius: '20px', background: branch.is_active ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)', color: branch.is_active ? '#10b981' : '#ef4444' }}>
                    {branch.is_active ? 'Aktif' : 'Pasif'}
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>
                  <div><MapPin size={12} style={{ display: 'inline', marginRight: '4px' }} />{branch.city || '—'}</div>
                  {branch.phone && <div><Phone size={12} style={{ display: 'inline', marginRight: '4px' }} />{branch.phone}</div>}
                  {branch.panel_slug && (
                    <div style={{ marginTop: '6px' }}>
                      <strong>Erişim kodu:</strong> <code>{branch.panel_slug}</code>
                    </div>
                  )}
                  <div style={{ marginTop: '4px' }}>
                    Masa sayısı: <strong>{branch.table_count ?? 0}</strong> (şube oluşturulunca otomatik)
                  </div>
                  <div style={{ marginTop: '4px' }}>
                    Harici panel: {branch.panel_enabled && branch.has_panel_password ? '✅ Aktif' : '⚠️ Şifre bekleniyor'}
                  </div>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  <button onClick={() => { setPasswordModal(branch); setPanelPassword(''); setPanelEnabled(true); setError(''); }} className="btn btn-primary" style={{ flex: 1, padding: '6px 10px', fontSize: '11px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
                    <Lock size={12} /> Panel Şifresi
                  </button>
                  {branch.panel_slug && (
                    <>
                      <button onClick={() => copyPanelLink(branch)} className="btn btn-secondary" style={{ padding: '6px 10px' }} title="Bağlantıyı kopyala">
                        <Copy size={12} />
                      </button>
                      <a href={`/franchise?code=${branch.panel_slug}`} target="_blank" rel="noreferrer" className="btn btn-secondary" style={{ padding: '6px 10px', display: 'flex', alignItems: 'center' }} title="Harici paneli aç">
                        <ExternalLink size={12} />
                      </a>
                    </>
                  )}
                  <button onClick={() => handleToggle(branch)} className="btn btn-secondary" style={{ padding: '6px 10px', fontSize: '11px' }}>{branch.is_active ? 'Pasif' : 'Aktif'}</button>
                  <button onClick={() => handleDelete(branch.id)} className="btn btn-secondary" style={{ padding: '6px 10px', color: '#ef4444' }}>
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {passwordModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}
          onClick={(e) => { if (e.target === e.currentTarget) setPasswordModal(null); }}>
          <div className="card" style={{ width: '100%', maxWidth: '400px', padding: '24px' }}>
            <h3 style={{ margin: '0 0 8px', fontSize: '16px' }}>Panel Şifresi — {passwordModal.name}</h3>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Bu şifreyi franchise operatörleri harici panelde kullanır. Yalnızca siz belirleyebilirsiniz.
            </p>
            <form onSubmit={handleSetPassword}>
              <div className="form-group">
                <label>Yeni Panel Şifresi (min. 6 karakter)</label>
                <input type="password" className="form-control" value={panelPassword} onChange={(e) => setPanelPassword(e.target.value)} required minLength={6} />
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', marginBottom: '16px', cursor: 'pointer' }}>
                <input type="checkbox" checked={panelEnabled} onChange={(e) => setPanelEnabled(e.target.checked)} />
                Harici panel erişimini etkinleştir
              </label>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setPasswordModal(null)}>İptal</button>
                <button type="submit" className="btn btn-primary" style={{ flex: 2 }}>Kaydet</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
