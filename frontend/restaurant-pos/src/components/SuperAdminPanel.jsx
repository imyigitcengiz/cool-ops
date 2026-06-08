import React, { useState, useEffect } from 'react';
import { Users, Plus, Edit3, Trash2, Shield, ShieldCheck, ShieldAlert, X, Save, Eye, EyeOff, UserCog, Check, AlertTriangle } from 'lucide-react';
import { useResponsive } from '../hooks/useResponsive';

import { apiFetch, API_BASE } from '../lib/apiClient';

const ROLE_CONFIG = {
  super_admin: { label: 'Süper Yönetici', color: '#dc2626', bg: '#fef2f2', icon: ShieldAlert },
  store_owner: { label: 'Kurum Yöneticisi', color: '#7c3aed', bg: '#f5f3ff', icon: ShieldCheck },
  manager: { label: 'Operasyon Müdürü', color: '#2563eb', bg: '#eff6ff', icon: Shield },
  waiter: { label: 'Servis Sorumlusu', color: '#d97706', bg: '#fffbeb', icon: Users },
  cashier: { label: 'Finans Sorumlusu', color: '#059669', bg: '#ecfdf5', icon: UserCog },
  kitchen: { label: 'Üretim Sorumlusu', color: '#0891b2', bg: '#ecfeff', icon: UserCog },
};

export default function SuperAdminPanel({ authToken }) {
  const { isMobile } = useResponsive();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form state
  const [formData, setFormData] = useState({
    username: '', password: '', first_name: '', last_name: '',
    email: '', phone: '', role: 'store_owner',
  });

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Token ${authToken}`,
  };

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const res = await apiFetch(`${API_BASE}/auth/users/`, { headers });
      const data = await res.json();
      if (Array.isArray(data)) setUsers(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  const openAddModal = () => {
    setEditUser(null);
    setFormData({ username: '', password: '', first_name: '', last_name: '', email: '', phone: '', role: 'store_owner' });
    setError('');
    setShowModal(true);
  };

  const openEditModal = (user) => {
    setEditUser(user);
    setFormData({
      username: user.username, password: '', first_name: user.first_name,
      last_name: user.last_name, email: user.email, phone: user.phone, role: user.role,
    });
    setError('');
    setShowModal(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setError('');

    try {
      if (editUser) {
        // PATCH existing user
        const payload = { ...formData };
        if (!payload.password) delete payload.password;
        const res = await apiFetch(`${API_BASE}/auth/users/${editUser.id}/`, {
          method: 'PATCH', headers, body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) { setError(data.error || 'Güncelleme başarısız.'); return; }
        setSuccess('Kullanıcı güncellendi.');
      } else {
        // Create new user
        if (!formData.username || !formData.password) {
          setError('Kullanıcı adı ve şifre zorunludur.'); return;
        }
        const res = await apiFetch(`${API_BASE}/auth/register/`, {
          method: 'POST', headers, body: JSON.stringify(formData),
        });
        const data = await res.json();
        if (!res.ok) { setError(data.error || 'Oluşturma başarısız.'); return; }
        setSuccess('Yeni kullanıcı oluşturuldu.');
      }

      setShowModal(false);
      fetchUsers();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Sunucu hatası.');
    }
  };

  const handleDelete = async (userId) => {
    if (!confirm('Bu kullanıcıyı silmek istediğinizden emin misiniz?')) return;
    try {
      const res = await apiFetch(`${API_BASE}/auth/users/${userId}/`, { method: 'DELETE', headers });
      if (res.ok) {
        setSuccess('Kullanıcı silindi.');
        fetchUsers();
        setTimeout(() => setSuccess(''), 3000);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleToggleActive = async (user) => {
    try {
      await apiFetch(`${API_BASE}/auth/users/${user.id}/`, {
        method: 'PATCH', headers,
        body: JSON.stringify({ is_active: !user.is_active }),
      });
      fetchUsers();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '12px', background: 'linear-gradient(135deg, #6366f1, #a855f7)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ShieldAlert size={20} color="#fff" />
            </div>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: '700', margin: 0 }}>Sistem Kullanıcıları</h2>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{users.length} kayıtlı kullanıcı</p>
            </div>
          </div>
        </div>
        <button onClick={openAddModal} className="btn btn-primary" style={{ padding: '10px 20px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Plus size={16} /> Yeni Kullanıcı
        </button>
      </div>

      {/* Success alert */}
      {success && (
        <div style={{ background: '#ecfdf5', border: '1px solid #10b981', borderRadius: '10px', padding: '12px 16px', marginBottom: '16px', fontSize: '13px', color: '#065f46', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Check size={16} /> {success}
        </div>
      )}

      {/* Users Table/Cards */}
      {loading ? (
        <div className="spinner" style={{ margin: '60px auto' }} />
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid var(--panel-border)' }}>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: '600', color: '#64748b', whiteSpace: 'nowrap' }}>Kullanıcı</th>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: '600', color: '#64748b', whiteSpace: 'nowrap' }}>Rol</th>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: '600', color: '#64748b', whiteSpace: 'nowrap' }}>E-posta</th>
                  {!isMobile && <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: '600', color: '#64748b', whiteSpace: 'nowrap' }}>Telefon</th>}
                  <th style={{ padding: '12px 16px', textAlign: 'center', fontWeight: '600', color: '#64748b', whiteSpace: 'nowrap' }}>Durum</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right', fontWeight: '600', color: '#64748b', whiteSpace: 'nowrap' }}>İşlemler</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => {
                  const roleCfg = ROLE_CONFIG[user.role] || ROLE_CONFIG.store_owner;
                  const RoleIcon = roleCfg.icon;
                  return (
                    <tr key={user.id} style={{ borderBottom: '1px solid var(--panel-border)', transition: 'background 0.15s' }}
                        onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'}
                        onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                      <td style={{ padding: '12px 16px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <div style={{
                            width: '36px', height: '36px', borderRadius: '10px',
                            background: 'linear-gradient(135deg, #e0e7ff, #c7d2fe)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontWeight: '700', fontSize: '14px', color: '#4f46e5', flexShrink: 0,
                          }}>
                            {(user.first_name?.[0] || user.username[0]).toUpperCase()}
                          </div>
                          <div>
                            <div style={{ fontWeight: '600' }}>{user.first_name} {user.last_name}</div>
                            <div style={{ fontSize: '11px', color: '#94a3b8' }}>@{user.username}</div>
                          </div>
                        </div>
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span style={{
                          display: 'inline-flex', alignItems: 'center', gap: '5px',
                          background: roleCfg.bg, color: roleCfg.color,
                          padding: '4px 10px', borderRadius: '8px', fontSize: '11px', fontWeight: '600',
                        }}>
                          <RoleIcon size={12} /> {roleCfg.label}
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px', color: '#64748b', fontSize: '12px' }}>{user.email || '—'}</td>
                      {!isMobile && <td style={{ padding: '12px 16px', color: '#64748b', fontSize: '12px' }}>{user.phone || '—'}</td>}
                      <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                        <button
                          onClick={() => handleToggleActive(user)}
                          style={{
                            background: user.is_active ? '#ecfdf5' : '#fef2f2',
                            color: user.is_active ? '#059669' : '#dc2626',
                            border: 'none', borderRadius: '8px', padding: '4px 10px',
                            fontSize: '11px', fontWeight: '600', cursor: 'pointer',
                          }}
                        >
                          {user.is_active ? 'Aktif' : 'Pasif'}
                        </button>
                      </td>
                      <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                        <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end' }}>
                          <button onClick={() => openEditModal(user)} title="Düzenle"
                            style={{ background: '#eff6ff', border: 'none', borderRadius: '8px', padding: '6px 8px', cursor: 'pointer', color: '#2563eb' }}>
                            <Edit3 size={14} />
                          </button>
                          {user.role !== 'super_admin' && (
                            <button onClick={() => handleDelete(user.id)} title="Sil"
                              style={{ background: '#fef2f2', border: 'none', borderRadius: '8px', padding: '6px 8px', cursor: 'pointer', color: '#dc2626' }}>
                              <Trash2 size={14} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add/Edit Modal */}
      {showModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}
          onClick={(e) => { if (e.target === e.currentTarget) setShowModal(false); }}>
          <div style={{
            background: '#fff', borderRadius: '16px', width: '100%',
            maxWidth: isMobile ? '95vw' : '480px', maxHeight: '90vh', overflowY: 'auto',
            boxShadow: '0 25px 60px rgba(0,0,0,0.3)',
          }}>
            {/* Modal header */}
            <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '700' }}>
                {editUser ? '✏️ Kullanıcı Düzenle' : '➕ Yeni Kullanıcı'}
              </h3>
              <button onClick={() => setShowModal(false)} style={{ background: '#f1f5f9', border: 'none', borderRadius: '8px', padding: '6px', cursor: 'pointer' }}>
                <X size={18} color="#64748b" />
              </button>
            </div>

            <form onSubmit={handleSave} style={{ padding: '24px' }}>
              {error && (
                <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '10px', padding: '10px 14px', marginBottom: '16px', fontSize: '13px', color: '#991b1b' }}>
                  ⚠️ {error}
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '4px' }}>Ad</label>
                  <input className="form-control" value={formData.first_name} onChange={(e) => setFormData({ ...formData, first_name: e.target.value })} placeholder="Ad" />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '4px' }}>Soyad</label>
                  <input className="form-control" value={formData.last_name} onChange={(e) => setFormData({ ...formData, last_name: e.target.value })} placeholder="Soyad" />
                </div>
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '4px' }}>Kullanıcı Adı *</label>
                <input className="form-control" value={formData.username} onChange={(e) => setFormData({ ...formData, username: e.target.value })} placeholder="kullanici_adi" required disabled={!!editUser} style={editUser ? { opacity: 0.6 } : {}} />
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '4px' }}>
                  {editUser ? 'Yeni Şifre (boş bırakılırsa değişmez)' : 'Şifre *'}
                </label>
                <input className="form-control" type="password" value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} placeholder="••••••••" required={!editUser} />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '4px' }}>E-posta</label>
                  <input className="form-control" type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} placeholder="ornek@email.com" />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '4px' }}>Telefon</label>
                  <input className="form-control" value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} placeholder="+90 5XX XXX XX XX" />
                </div>
              </div>

              <div style={{ marginBottom: '24px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '8px' }}>Sistem Rolü</label>
                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '8px' }}>
                  {Object.entries(ROLE_CONFIG).map(([key, cfg]) => {
                    const RIcon = cfg.icon;
                    return (
                      <button key={key} type="button" onClick={() => setFormData({ ...formData, role: key })}
                        style={{
                          padding: '10px 12px', borderRadius: '10px', border: `1.5px solid ${formData.role === key ? cfg.color : '#e2e8f0'}`,
                          background: formData.role === key ? cfg.bg : '#fff', cursor: 'pointer',
                          display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', fontWeight: '600',
                          color: formData.role === key ? cfg.color : '#64748b', transition: 'all 0.15s',
                        }}>
                        <RIcon size={14} /> {cfg.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button type="button" onClick={() => setShowModal(false)} className="btn btn-secondary" style={{ flex: 1 }}>İptal</button>
                <button type="submit" className="btn btn-primary" style={{ flex: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
                  <Save size={16} /> {editUser ? 'Güncelle' : 'Oluştur'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
