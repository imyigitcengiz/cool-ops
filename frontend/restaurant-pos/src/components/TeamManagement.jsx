import React, { useState, useEffect } from 'react';
import { Users, Shield, Plus, Building2 } from 'lucide-react';
import { useResponsive } from '../hooks/useResponsive';

import { apiFetch, API_BASE } from '../lib/apiClient';

const ROLE_LABELS = {
  store_owner: 'Kurum Yöneticisi',
  manager: 'Operasyon Müdürü',
  cashier: 'Finans Sorumlusu',
  kitchen: 'Üretim Sorumlusu',
  waiter: 'Servis Sorumlusu',
};

const ROLE_BADGE = {
  store_owner: 'badge-danger',
  manager: 'badge-warning',
  cashier: 'badge-info',
  kitchen: 'badge-secondary',
  waiter: 'badge-success',
};

export default function TeamManagement() {
  const { isMobile } = useResponsive();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('manager');
  const [hireDate, setHireDate] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);

  useEffect(() => {
    fetchMembers();
  }, []);

  const fetchMembers = async () => {
    try {
      setLoading(true);
      const res = await apiFetch(`${API_BASE}/staff-members/`);
      const data = await res.json();
      setMembers(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddMember = async (e) => {
    e.preventDefault();
    if (!username || !email) return;

    try {
      const newMember = {
        id: members.length + 1,
        user_name: username,
        email,
        role,
        hire_date: hireDate || new Date().toISOString().split('T')[0],
      };

      setMembers([...members, newMember]);
      setUsername('');
      setEmail('');
      setRole('manager');
      setHireDate('');
      setShowAddForm(false);
      alert('Ekip üyesi organizasyona eklendi.');
    } catch (err) {
      console.error(err);
    }
  };

  const displayList = members.length > 0 ? members : [
    { id: 1, user_name: 'im.yigit', email: 'yigit@bidolupos.com', role: 'store_owner', hire_date: '2026-05-01' },
    { id: 2, user_name: 'garson1', email: 'garson1@bidolupos.com', role: 'waiter', hire_date: '2026-05-15' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="card" style={{
        padding: '18px 20px',
        background: 'linear-gradient(135deg, rgba(99,102,241,0.06) 0%, rgba(168,85,247,0.04) 100%)',
        border: '1px solid rgba(99,102,241,0.15)',
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <Building2 size={22} style={{ color: 'var(--primary)', marginTop: '2px' }} />
          <div>
            <h3 style={{ margin: '0 0 6px', fontSize: '16px', fontWeight: '700' }}>Organizasyon Yönetimi</h3>
            <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-muted)', lineHeight: 1.5 }}>
              Şube ekibinizi, yetki seviyelerini ve erişim rollerini kurumsal yapınıza uygun şekilde yönetin.
              Koordinatör ve yönetici hesapları bu panel üzerinden yapılandırılır.
            </p>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '2fr 1fr', gap: isMobile ? '16px' : '24px' }}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '10px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', margin: 0 }}>Ekip Kadrosu</h3>
            <button
              className="btn btn-primary"
              onClick={() => setShowAddForm(!showAddForm)}
              style={{ display: 'flex', gap: '6px', alignItems: 'center', fontSize: '13px', padding: '8px 16px' }}
            >
              <Plus size={16} /> Ekip Üyesi Ekle
            </button>
          </div>

          {loading ? (
            <div className="spinner" />
          ) : (
            <div className="table-container">
              <table className="mgmt-table">
                <thead>
                  <tr>
                    <th>Kullanıcı</th>
                    <th>Organizasyon Rolü</th>
                    <th>Katılım Tarihi</th>
                    <th>Durum</th>
                  </tr>
                </thead>
                <tbody>
                  {displayList.map((member) => (
                    <tr key={member.id}>
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          <span style={{ fontWeight: '600' }}>
                            {member.user_name || member.username || `Üye #${member.id}`}
                          </span>
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{member.email || '—'}</span>
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${ROLE_BADGE[member.role] || 'badge-success'}`}>
                          {ROLE_LABELS[member.role] || member.role}
                        </span>
                      </td>
                      <td>
                        <span style={{ color: 'var(--text-muted)' }}>{member.hire_date || '—'}</span>
                      </td>
                      <td>
                        <span className="badge badge-success">Aktif</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {showAddForm && (
            <div className="card">
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>Yeni Ekip Üyesi</h3>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '20px' }}>
                Organizasyona yeni bir kullanıcı tanımlayın ve yetki rolünü belirleyin.
              </p>
              <form onSubmit={handleAddMember}>
                <div className="form-group">
                  <label>Kullanıcı Adı</label>
                  <input type="text" className="form-control" placeholder="örn: koordinator.izmir" value={username} onChange={(e) => setUsername(e.target.value)} required />
                </div>
                <div className="form-group">
                  <label>Kurumsal E-posta</label>
                  <input type="email" className="form-control" placeholder="ad.soyad@sirket.com" value={email} onChange={(e) => setEmail(e.target.value)} required />
                </div>
                <div className="form-group">
                  <label>Yetki Rolü</label>
                  <select className="form-control form-select" value={role} onChange={(e) => setRole(e.target.value)}>
                    <option value="manager">Operasyon Müdürü</option>
                    <option value="cashier">Finans Sorumlusu</option>
                    <option value="kitchen">Üretim Sorumlusu</option>
                    <option value="waiter">Servis Sorumlusu</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Katılım Tarihi</label>
                  <input type="date" className="form-control" value={hireDate} onChange={(e) => setHireDate(e.target.value)} />
                </div>
                <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '12px' }}>
                  Organizasyona Ekle
                </button>
              </form>
            </div>
          )}

          <div className="card" style={{ background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.06) 0%, rgba(168, 85, 247, 0.01) 100%)' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Shield size={18} style={{ color: 'var(--accent)' }} /> Yetki Matrisi
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px', color: 'var(--text-muted)' }}>
              <p><strong>Operasyon Müdürü:</strong> Operasyon akışı, masa ve sipariş yönetimi, kasa görünürlüğü.</p>
              <p><strong>Finans Sorumlusu:</strong> Tahsilat, kasa hareketleri ve ödeme süreçleri.</p>
              <p><strong>Üretim Sorumlusu:</strong> Mutfak operasyonları ve sipariş durum güncellemeleri.</p>
              <p><strong>Servis Sorumlusu:</strong> Sipariş girişi ve servis süreçleri.</p>
            </div>
          </div>

          <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Users size={20} style={{ color: 'var(--primary)' }} />
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.5 }}>
              <strong style={{ color: 'var(--text-main)' }}>{displayList.length}</strong> aktif ekip üyesi tanımlı.
              Kurum koordinatörleri için önerilen rol: <strong>Operasyon Müdürü</strong>.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
