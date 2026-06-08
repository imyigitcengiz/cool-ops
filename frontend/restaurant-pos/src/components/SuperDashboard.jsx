import React, { useState, useEffect, useMemo } from 'react';
import {
  Building2, Users, Crown, BarChart3, Search, Edit3, Trash2, LogIn,
  X, Save, Check, AlertTriangle, Clock, UserPlus, Store, ChevronDown,
  ToggleLeft, ToggleRight, Filter, Activity, Star, Zap, Gem, Server, Shield,
} from 'lucide-react';
import { useResponsive } from '../hooks/useResponsive';

import { apiFetch, API_BASE } from '../lib/apiClient';

const PLAN_COLORS = {
  starter:    { color: '#94a3b8', bg: '#f1f5f9', label: 'Starter',    icon: Star },
  growth:     { color: '#6366f1', bg: '#eef2ff', label: 'Growth',     icon: Zap },
  enterprise: { color: '#f59e0b', bg: '#fffbeb', label: 'Enterprise', icon: Gem },
};

const ROLE_CONFIG = {
  store_owner: { label: 'Mağaza Sahibi', color: '#7c3aed', bg: '#f5f3ff' },
  super_admin: { label: 'Süper Yönetici', color: '#dc2626', bg: '#fef2f2' },
};

// ─── Shared Styles ───────────────────────────────────────────────────
const s = {
  card: {
    background: 'var(--bg-card, #fff)',
    borderRadius: '16px',
    border: '1px solid var(--panel-border, #e2e8f0)',
    padding: '20px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
  },
  th: {
    padding: '12px 16px',
    textAlign: 'left',
    fontWeight: '600',
    color: '#64748b',
    whiteSpace: 'nowrap',
    fontSize: '12px',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  },
  td: {
    padding: '14px 16px',
    fontSize: '13px',
    color: 'var(--text-main, #1e293b)',
  },
  badge: (color, bg) => ({
    display: 'inline-flex',
    alignItems: 'center',
    gap: '5px',
    background: bg,
    color: color,
    padding: '4px 10px',
    borderRadius: '8px',
    fontSize: '11px',
    fontWeight: '600',
    whiteSpace: 'nowrap',
  }),
  iconBtn: (color, bg) => ({
    background: bg,
    border: 'none',
    borderRadius: '8px',
    padding: '7px 9px',
    cursor: 'pointer',
    color: color,
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.15s',
  }),
  overlay: {
    position: 'fixed',
    top: 0, left: 0, right: 0, bottom: 0,
    background: 'rgba(0,0,0,0.5)',
    backdropFilter: 'blur(4px)',
    zIndex: 9999,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '20px',
  },
};

// ─── Helper: format relative time in Turkish ─────────────────────────
function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = (Date.now() - new Date(dateStr).getTime()) / 1000;
  if (diff < 60) return 'Az önce';
  if (diff < 3600) return `${Math.floor(diff / 60)} dk önce`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} saat önce`;
  if (diff < 604800) return `${Math.floor(diff / 86400)} gün önce`;
  return new Date(dateStr).toLocaleDateString('tr-TR');
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('tr-TR', {
    day: '2-digit', month: 'short', year: 'numeric',
  });
}

// ═════════════════════════════════════════════════════════════════════
// ─── SUPER DASHBOARD ─────────────────────────────────────────────────
// ═════════════════════════════════════════════════════════════════════
export default function SuperDashboard({ authToken, onImpersonate }) {
  const { isMobile } = useResponsive();

  const [activeTab, setActiveTab] = useState('brands');
  const [stats, setStats] = useState(null);
  const [brands, setBrands] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tabLoading, setTabLoading] = useState(false);

  // Search / filter
  const [brandSearch, setBrandSearch] = useState('');
  const [userSearch, setUserSearch] = useState('');
  const [userBrandFilter, setUserBrandFilter] = useState('');

  // Modal
  const [editModal, setEditModal] = useState(null);
  const [storeOwners, setStoreOwners] = useState([]);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Token ${authToken}`,
  };

  // ── Fetch Stats ──────────────────────────────────────────────────
  const fetchStats = async () => {
    try {
      const res = await apiFetch(`${API_BASE}/auth/super-stats/`, { headers });
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Stats fetch error:', err);
    }
  };

  // ── Fetch Brands ─────────────────────────────────────────────────
  const fetchBrands = async () => {
    try {
      setTabLoading(true);
      const res = await apiFetch(`${API_BASE}/auth/brands/`, { headers });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) setBrands(data);
      }
    } catch (err) {
      console.error('Brands fetch error:', err);
    } finally {
      setTabLoading(false);
    }
  };

  // ── Fetch Store Owners (super admin MVP view) ────────────────────
  const fetchUsers = async () => {
    try {
      setTabLoading(true);
      const res = await apiFetch(`${API_BASE}/auth/users/`, { headers });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setUsers(data);
          setStoreOwners(data);
        }
      }
    } catch (err) {
      console.error('Users fetch error:', err);
    } finally {
      setTabLoading(false);
    }
  };

  // ── Initial load ─────────────────────────────────────────────────
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await fetchStats();
      await fetchBrands();
      setLoading(false);
    };
    load();
  }, []);

  // ── Tab change data fetching ─────────────────────────────────────
  useEffect(() => {
    if (activeTab === 'brands') fetchBrands();
    else if (activeTab === 'users') fetchUsers();
    else if (activeTab === 'activity') fetchStats();
  }, [activeTab]);

  // ── Brand actions ────────────────────────────────────────────────
  const handleToggleBrandActive = async (brand) => {
    try {
      await apiFetch(`${API_BASE}/auth/brands/${brand.id}/`, {
        method: 'PATCH', headers,
        body: JSON.stringify({ is_active: !brand.is_active }),
      });
      fetchBrands();
      fetchStats();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteBrand = async (brand) => {
    if (!confirm(`"${brand.name}" markasını silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.`)) return;
    try {
      const res = await apiFetch(`${API_BASE}/auth/brands/${brand.id}/`, { method: 'DELETE', headers });
      if (res.ok) {
        showSuccess('Marka başarıyla silindi.');
        fetchBrands();
        fetchStats();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveEdit = async () => {
    if (!editModal) return;
    setError('');
    try {
      const body = {};
      if (editModal.plan !== editModal.brand.plan) body.plan = editModal.plan;
      if (editModal.name !== editModal.brand.name) body.name = editModal.name;
      if (editModal.is_active !== editModal.brand.is_active) body.is_active = editModal.is_active;
      if (editModal.plan_expiry !== (editModal.brand.plan_expiry || '')) body.plan_expiry = editModal.plan_expiry || null;

      if (editModal.ownerMode === 'assign' && editModal.ownerId) {
        body.owner_id = Number(editModal.ownerId);
      }
      if (editModal.ownerMode === 'create') {
        if (!editModal.newOwnerUsername?.trim() || !editModal.newOwnerPassword) {
          setError('Yeni sahip için kullanıcı adı ve şifre zorunludur.');
          return;
        }
        body.new_owner = {
          username: editModal.newOwnerUsername.trim(),
          password: editModal.newOwnerPassword,
          email: editModal.newOwnerEmail?.trim() || '',
          first_name: editModal.newOwnerFirstName?.trim() || '',
          last_name: editModal.newOwnerLastName?.trim() || '',
        };
      }

      if (Object.keys(body).length === 0) {
        setEditModal(null);
        return;
      }

      const res = await apiFetch(`${API_BASE}/auth/brands/${editModal.brand.id}/`, {
        method: 'PATCH', headers, body: JSON.stringify(body),
      });
      if (!res.ok) {
        const data = await res.json();
        setError(data.error || data.detail || 'Güncelleme başarısız.');
        return;
      }
      setEditModal(null);
      showSuccess('Marka bilgileri güncellendi.');
      fetchBrands();
      fetchStats();
    } catch (err) {
      setError('Sunucu hatası.');
    }
  };

  // ── Enter store as brand owner ───────────────────────────────────
  const handleEnterStore = async (brand) => {
    if (!brand.owner) {
      alert('Bu markanın sahibi tanımlı değil. Önce mağaza sahibi atayın.');
      return;
    }
    if (!confirm(`"${brand.name}" mağazasına sahip olarak giriş yapmak istiyor musunuz?`)) return;
    try {
      const res = await apiFetch(`${API_BASE}/auth/brands/${brand.id}/enter/`, {
        method: 'POST', headers,
      });
      if (res.ok) {
        const data = await res.json();
        onImpersonate(data.token, data.user);
      } else {
        const data = await res.json();
        alert(data.error || data.detail || 'Mağazaya giriş başarısız.');
      }
    } catch {
      alert('Sunucu hatası.');
    }
  };

  const handleImpersonateOwner = async (userId, userName) => {
    if (!confirm(`"${userName}" mağaza sahibi olarak giriş yapmak istiyor musunuz?`)) return;
    try {
      const res = await apiFetch(`${API_BASE}/auth/users/${userId}/impersonate/`, {
        method: 'POST', headers,
      });
      if (res.ok) {
        const data = await res.json();
        onImpersonate(data.token, data.user);
      } else {
        const data = await res.json();
        alert(data.error || data.detail || 'Giriş başarısız.');
      }
    } catch {
      alert('Sunucu hatası.');
    }
  };

  const openEditModal = async (brand) => {
    if (storeOwners.length === 0) await fetchUsers();
    setEditModal({
      brand,
      name: brand.name,
      plan: brand.plan,
      is_active: brand.is_active,
      plan_expiry: brand.plan_expiry || '',
      ownerMode: brand.owner ? 'keep' : 'create',
      ownerId: brand.owner?.id ? String(brand.owner.id) : '',
      newOwnerUsername: '',
      newOwnerPassword: '',
      newOwnerEmail: '',
      newOwnerFirstName: '',
      newOwnerLastName: '',
    });
  };

  // ── Helpers ──────────────────────────────────────────────────────
  const showSuccess = (msg) => {
    setSuccess(msg);
    setTimeout(() => setSuccess(''), 3000);
  };

  // ── Filtered data ────────────────────────────────────────────────
  const filteredBrands = useMemo(() => {
    if (!brandSearch) return brands;
    const q = brandSearch.toLowerCase();
    return brands.filter(b =>
      b.name.toLowerCase().includes(q) ||
      b.slug?.toLowerCase().includes(q) ||
      b.owner?.username?.toLowerCase().includes(q) ||
      b.owner?.email?.toLowerCase().includes(q)
    );
  }, [brands, brandSearch]);

  const filteredUsers = useMemo(() => {
    let list = users;
    if (userBrandFilter) {
      list = list.filter(u => u.brand && String(u.brand.id) === userBrandFilter);
    }
    if (userSearch) {
      const q = userSearch.toLowerCase();
      list = list.filter(u =>
        u.username.toLowerCase().includes(q) ||
        u.email?.toLowerCase().includes(q) ||
        `${u.first_name} ${u.last_name}`.toLowerCase().includes(q)
      );
    }
    return list;
  }, [users, userSearch, userBrandFilter]);

  const uniqueBrandsForFilter = useMemo(() => {
    const map = new Map();
    users.forEach(u => {
      if (u.brand && !map.has(u.brand.id)) map.set(u.brand.id, u.brand.name);
    });
    return Array.from(map.entries());
  }, [users]);

  // ── Loading state ────────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
        <div className="spinner" />
      </div>
    );
  }

  // ══════════════════════════════════════════════════════════════════
  // ── PLAN DISTRIBUTION MINI BAR ────────────────────────────────────
  // ══════════════════════════════════════════════════════════════════
  const planDist = stats?.plan_distribution || { starter: 0, growth: 0, enterprise: 0 };
  const totalPlans = (planDist.starter || 0) + (planDist.growth || 0) + (planDist.enterprise || 0);

  const TABS = [
    { key: 'brands',   label: 'Markalar',         icon: Building2 },
    { key: 'users',    label: 'Mağaza Sahipleri', icon: Users },
    { key: 'platform', label: 'Platform (KVKK)',  icon: Server },
    { key: 'activity', label: 'Son Aktiviteler',  icon: Activity },
  ];

  const platformMetrics = stats?.platform_metrics;

  return (
    <div>
      {/* ── Success Banner ──────────────────────────────────────── */}
      {success && (
        <div style={{
          background: '#ecfdf5', border: '1px solid #10b981', borderRadius: '12px',
          padding: '12px 18px', marginBottom: '20px', fontSize: '13px', color: '#065f46',
          display: 'flex', alignItems: 'center', gap: '8px',
        }}>
          <Check size={16} /> {success}
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════ */}
      {/* ── KPI CARDS ─────────────────────────────────────────────── */}
      {/* ════════════════════════════════════════════════════════════ */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(4, 1fr)',
        gap: '16px',
        marginBottom: '28px',
      }}>
        {/* Toplam Marka */}
        <div style={s.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted, #64748b)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Toplam Marka
            </span>
            <div style={{
              width: '36px', height: '36px', borderRadius: '10px',
              background: 'linear-gradient(135deg, #6366f1, #818cf8)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Building2 size={18} color="#fff" />
            </div>
          </div>
          <div style={{ fontSize: '28px', fontWeight: '800', color: 'var(--text-main, #1e293b)', lineHeight: 1 }}>
            {stats?.total_brands ?? 0}
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted, #64748b)', marginTop: '4px', display: 'block' }}>
            Kayıtlı tüm markalar
          </span>
        </div>

        {/* Aktif Marka */}
        <div style={s.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted, #64748b)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Aktif Marka
            </span>
            <div style={{
              width: '36px', height: '36px', borderRadius: '10px',
              background: 'linear-gradient(135deg, #10b981, #34d399)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Store size={18} color="#fff" />
            </div>
          </div>
          <div style={{ fontSize: '28px', fontWeight: '800', color: 'var(--text-main, #1e293b)', lineHeight: 1 }}>
            {stats?.active_brands ?? 0}
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted, #64748b)', marginTop: '4px', display: 'block' }}>
            Aktif abonelikler
          </span>
        </div>

        {/* Toplam Kullanıcı */}
        <div style={s.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted, #64748b)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Mağaza Sahibi
            </span>
            <div style={{
              width: '36px', height: '36px', borderRadius: '10px',
              background: 'linear-gradient(135deg, #f59e0b, #fbbf24)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Users size={18} color="#fff" />
            </div>
          </div>
          <div style={{ fontSize: '28px', fontWeight: '800', color: 'var(--text-main, #1e293b)', lineHeight: 1 }}>
            {stats?.total_users ?? 0}
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted, #64748b)', marginTop: '4px', display: 'block' }}>
            Kayıtlı mağaza sahipleri
          </span>
        </div>

        {/* Plan Dağılımı */}
        <div style={s.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted, #64748b)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Plan Dağılımı
            </span>
            <div style={{
              width: '36px', height: '36px', borderRadius: '10px',
              background: 'linear-gradient(135deg, #8b5cf6, #a78bfa)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <BarChart3 size={18} color="#fff" />
            </div>
          </div>
          {/* Mini stacked bar */}
          <div style={{
            display: 'flex', height: '8px', borderRadius: '4px', overflow: 'hidden',
            background: '#f1f5f9', marginBottom: '10px',
          }}>
            {totalPlans > 0 && (
              <>
                <div style={{ width: `${(planDist.starter / totalPlans) * 100}%`, background: PLAN_COLORS.starter.color, transition: 'width 0.3s' }} />
                <div style={{ width: `${(planDist.growth / totalPlans) * 100}%`, background: PLAN_COLORS.growth.color, transition: 'width 0.3s' }} />
                <div style={{ width: `${(planDist.enterprise / totalPlans) * 100}%`, background: PLAN_COLORS.enterprise.color, transition: 'width 0.3s' }} />
              </>
            )}
          </div>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {Object.entries(PLAN_COLORS).map(([key, cfg]) => (
              <div key={key} style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--text-muted, #64748b)' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: cfg.color, flexShrink: 0 }} />
                <span>{cfg.label}</span>
                <span style={{ fontWeight: '700', color: 'var(--text-main, #1e293b)' }}>{planDist[key] || 0}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ════════════════════════════════════════════════════════════ */}
      {/* ── TAB NAV ───────────────────────────────────────────────── */}
      {/* ════════════════════════════════════════════════════════════ */}
      <div style={{
        display: 'flex', gap: '4px', marginBottom: '20px',
        background: '#f1f5f9', borderRadius: '12px', padding: '4px',
        overflowX: 'auto',
      }}>
        {TABS.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                flex: isMobile ? 1 : 'none',
                padding: isMobile ? '10px 12px' : '10px 20px',
                borderRadius: '10px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: isActive ? '600' : '500',
                color: isActive ? 'var(--primary, #6366f1)' : 'var(--text-muted, #64748b)',
                background: isActive ? '#fff' : 'transparent',
                boxShadow: isActive ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                transition: 'all 0.2s',
                whiteSpace: 'nowrap',
              }}
            >
              <Icon size={15} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* ════════════════════════════════════════════════════════════ */}
      {/* ── TAB CONTENT ───────────────────────────────────────────── */}
      {/* ════════════════════════════════════════════════════════════ */}
      {tabLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
          <div className="spinner" />
        </div>
      ) : (
        <>
          {activeTab === 'brands' && <BrandsTab
            brands={filteredBrands}
            search={brandSearch}
            setSearch={setBrandSearch}
            isMobile={isMobile}
            onToggle={handleToggleBrandActive}
            onDelete={handleDeleteBrand}
            onEdit={openEditModal}
            onEnterStore={handleEnterStore}
          />}

          {activeTab === 'users' && <UsersTab
            users={filteredUsers}
            search={userSearch}
            setSearch={setUserSearch}
            brandFilter={userBrandFilter}
            setBrandFilter={setUserBrandFilter}
            brandsForFilter={uniqueBrandsForFilter}
            isMobile={isMobile}
            onImpersonate={handleImpersonateOwner}
          />}

          {activeTab === 'platform' && (
            <div className="card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                <Shield size={20} style={{ color: '#6366f1' }} />
                <h3 style={{ margin: 0, fontSize: '15px', fontWeight: '700' }}>KVKK Uyumlu Platform Metrikleri</h3>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '20px', lineHeight: 1.6 }}>
                {platformMetrics?.kvkk_notice || 'Toplam hesap sayıları yalnızca sunucu kapasite planlaması içindir.'}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
                {[
                  ['Toplam Hesap', platformMetrics?.total_user_accounts ?? stats?.total_users ?? 0],
                  ['Aktif Hesap', platformMetrics?.active_user_accounts ?? 0],
                  ['Toplam Şube', platformMetrics?.total_branches ?? 0],
                  ['Aktif Franchise Paneli', platformMetrics?.active_franchise_panels ?? 0],
                ].map(([label, val]) => (
                  <div key={label} style={{ background: '#f8fafc', borderRadius: '12px', padding: '16px', textAlign: 'center' }}>
                    <div style={{ fontSize: '22px', fontWeight: '800', color: '#1e293b' }}>{val}</div>
                    <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>{label}</div>
                  </div>
                ))}
              </div>
              {platformMetrics?.accounts_by_role && (
                <div>
                  <h4 style={{ fontSize: '13px', fontWeight: '700', marginBottom: '10px' }}>Rol Bazlı Hesap Dağılımı (anonim)</h4>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {Object.entries(platformMetrics.accounts_by_role).map(([role, count]) => (
                      <span key={role} style={{ background: '#eef2ff', color: '#4f46e5', padding: '6px 12px', borderRadius: '8px', fontSize: '12px', fontWeight: '600' }}>
                        {role}: {count}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'activity' && <ActivityTab stats={stats} isMobile={isMobile} />}
        </>
      )}

      {/* ════════════════════════════════════════════════════════════ */}
      {/* ── EDIT MODAL ────────────────────────────────────────────── */}
      {/* ════════════════════════════════════════════════════════════ */}
      {editModal && (
        <div
          style={s.overlay}
          onClick={(e) => { if (e.target === e.currentTarget) setEditModal(null); }}
        >
          <div style={{
            background: '#fff',
            borderRadius: '20px',
            width: '100%',
            maxWidth: isMobile ? '95vw' : '480px',
            maxHeight: '90vh',
            overflowY: 'auto',
            boxShadow: '0 25px 60px rgba(0,0,0,0.3)',
          }}>
            {/* Header */}
            <div style={{
              padding: '20px 24px',
              borderBottom: '1px solid #e2e8f0',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Edit3 size={18} color="var(--primary, #6366f1)" />
                Marka Düzenle
              </h3>
              <button
                onClick={() => { setEditModal(null); setError(''); }}
                style={{ background: '#f1f5f9', border: 'none', borderRadius: '8px', padding: '6px', cursor: 'pointer' }}
              >
                <X size={18} color="#64748b" />
              </button>
            </div>

            {/* Body */}
            <div style={{ padding: '24px' }}>
              {error && (
                <div style={{
                  background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '10px',
                  padding: '10px 14px', marginBottom: '16px', fontSize: '13px', color: '#991b1b',
                  display: 'flex', alignItems: 'center', gap: '6px',
                }}>
                  <AlertTriangle size={14} /> {error}
                </div>
              )}

              {/* Brand Name */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '6px' }}>
                  Marka Adı
                </label>
                <input
                  value={editModal.name}
                  onChange={(e) => setEditModal({ ...editModal, name: e.target.value })}
                  className="form-control"
                  style={{ width: '100%', boxSizing: 'border-box' }}
                />
              </div>

              {/* Plan Selection */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '8px' }}>
                  Plan
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                  {Object.entries(PLAN_COLORS).map(([key, cfg]) => {
                    const PIcon = cfg.icon;
                    const selected = editModal.plan === key;
                    return (
                      <button
                        key={key}
                        type="button"
                        onClick={() => setEditModal({ ...editModal, plan: key })}
                        style={{
                          padding: '12px 8px',
                          borderRadius: '12px',
                          border: `2px solid ${selected ? cfg.color : '#e2e8f0'}`,
                          background: selected ? cfg.bg : '#fff',
                          cursor: 'pointer',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '6px',
                          transition: 'all 0.15s',
                        }}
                      >
                        <PIcon size={20} color={cfg.color} />
                        <span style={{ fontSize: '12px', fontWeight: '600', color: selected ? cfg.color : '#64748b' }}>
                          {cfg.label}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Owner Management */}
              <div style={{ marginBottom: '16px', padding: '14px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', color: '#334155', marginBottom: '10px' }}>
                  Mağaza Sahibi
                </label>
                {editModal.brand.owner && (
                  <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '10px' }}>
                    Mevcut: <strong>{editModal.brand.owner.first_name} {editModal.brand.owner.last_name}</strong> (@{editModal.brand.owner.username})
                  </div>
                )}
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '12px' }}>
                  {[
                    { key: 'keep', label: 'Değiştirme' },
                    { key: 'assign', label: 'Mevcut Sahip Ata' },
                    { key: 'create', label: 'Yeni Sahip Oluştur' },
                  ].map(opt => (
                    <button
                      key={opt.key}
                      type="button"
                      onClick={() => setEditModal({ ...editModal, ownerMode: opt.key })}
                      style={{
                        padding: '6px 10px', borderRadius: '8px', fontSize: '11px', fontWeight: '600', cursor: 'pointer',
                        border: `1.5px solid ${editModal.ownerMode === opt.key ? '#6366f1' : '#e2e8f0'}`,
                        background: editModal.ownerMode === opt.key ? '#eef2ff' : '#fff',
                        color: editModal.ownerMode === opt.key ? '#4f46e5' : '#64748b',
                      }}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
                {editModal.ownerMode === 'assign' && (
                  <select
                    value={editModal.ownerId}
                    onChange={(e) => setEditModal({ ...editModal, ownerId: e.target.value })}
                    className="form-control"
                    style={{ width: '100%', boxSizing: 'border-box' }}
                  >
                    <option value="">Mağaza sahibi seçin...</option>
                    {storeOwners.map(o => (
                      <option key={o.id} value={String(o.id)}>
                        {o.first_name || o.last_name ? `${o.first_name} ${o.last_name}`.trim() : o.username} (@{o.username})
                      </option>
                    ))}
                  </select>
                )}
                {editModal.ownerMode === 'create' && (
                  <div style={{ display: 'grid', gap: '10px' }}>
                    <input className="form-control" placeholder="Kullanıcı adı *" value={editModal.newOwnerUsername}
                      onChange={(e) => setEditModal({ ...editModal, newOwnerUsername: e.target.value })} />
                    <input className="form-control" type="password" placeholder="Şifre *" value={editModal.newOwnerPassword}
                      onChange={(e) => setEditModal({ ...editModal, newOwnerPassword: e.target.value })} />
                    <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '10px' }}>
                      <input className="form-control" placeholder="Ad" value={editModal.newOwnerFirstName}
                        onChange={(e) => setEditModal({ ...editModal, newOwnerFirstName: e.target.value })} />
                      <input className="form-control" placeholder="Soyad" value={editModal.newOwnerLastName}
                        onChange={(e) => setEditModal({ ...editModal, newOwnerLastName: e.target.value })} />
                    </div>
                    <input className="form-control" type="email" placeholder="E-posta" value={editModal.newOwnerEmail}
                      onChange={(e) => setEditModal({ ...editModal, newOwnerEmail: e.target.value })} />
                  </div>
                )}
              </div>

              {/* Plan Expiry */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '6px' }}>
                  Plan Bitiş Tarihi
                </label>
                <input
                  type="date"
                  value={editModal.plan_expiry ? editModal.plan_expiry.split('T')[0] : ''}
                  onChange={(e) => setEditModal({ ...editModal, plan_expiry: e.target.value })}
                  className="form-control"
                  style={{ width: '100%', boxSizing: 'border-box' }}
                />
              </div>

              {/* Status */}
              <div style={{ marginBottom: '24px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '8px' }}>
                  Durum
                </label>
                <button
                  type="button"
                  onClick={() => setEditModal({ ...editModal, is_active: !editModal.is_active })}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '10px',
                    padding: '10px 16px', borderRadius: '10px',
                    border: `1.5px solid ${editModal.is_active ? '#10b981' : '#ef4444'}`,
                    background: editModal.is_active ? '#ecfdf5' : '#fef2f2',
                    cursor: 'pointer', width: '100%', boxSizing: 'border-box',
                  }}
                >
                  {editModal.is_active
                    ? <ToggleRight size={22} color="#10b981" />
                    : <ToggleLeft size={22} color="#ef4444" />
                  }
                  <span style={{
                    fontSize: '13px', fontWeight: '600',
                    color: editModal.is_active ? '#065f46' : '#991b1b',
                  }}>
                    {editModal.is_active ? 'Aktif' : 'Pasif'}
                  </span>
                </button>
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  onClick={() => { setEditModal(null); setError(''); }}
                  className="btn btn-secondary"
                  style={{ flex: 1 }}
                >
                  İptal
                </button>
                <button
                  onClick={handleSaveEdit}
                  className="btn btn-primary"
                  style={{ flex: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
                >
                  <Save size={16} /> Kaydet
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════
// ── BRANDS TAB ─────────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════
function BrandsTab({ brands, search, setSearch, isMobile, onToggle, onDelete, onEdit, onEnterStore }) {
  return (
    <div>
      {/* Search bar */}
      <div style={{ marginBottom: '16px' }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          background: '#f8fafc', borderRadius: '10px', padding: '8px 14px',
          border: '1px solid var(--panel-border, #e2e8f0)',
        }}>
          <Search size={16} color="#94a3b8" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Marka veya sahip ara..."
            style={{
              border: 'none', background: 'transparent', outline: 'none',
              fontSize: '13px', color: 'var(--text-main, #1e293b)', width: '100%',
            }}
          />
          {search && (
            <button onClick={() => setSearch('')} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
              <X size={14} color="#94a3b8" />
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div style={{ ...s.card, padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid var(--panel-border, #e2e8f0)' }}>
                <th style={s.th}>Marka</th>
                {!isMobile && <th style={s.th}>Sahip</th>}
                <th style={s.th}>Plan</th>
                {!isMobile && <th style={{ ...s.th, textAlign: 'center' }}>Üye</th>}
                <th style={{ ...s.th, textAlign: 'center' }}>Durum</th>
                <th style={{ ...s.th, textAlign: 'right' }}>İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {brands.length === 0 ? (
                <tr>
                  <td colSpan={isMobile ? 4 : 6} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted, #64748b)', fontSize: '13px' }}>
                    Marka bulunamadı.
                  </td>
                </tr>
              ) : brands.map(brand => {
                const planCfg = PLAN_COLORS[brand.plan] || PLAN_COLORS.starter;
                const PlanIcon = planCfg.icon;
                return (
                  <tr
                    key={brand.id}
                    style={{ borderBottom: '1px solid var(--panel-border, #e2e8f0)', transition: 'background 0.15s' }}
                    onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    {/* Brand Name */}
                    <td style={s.td}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{
                          width: '38px', height: '38px', borderRadius: '10px',
                          background: `linear-gradient(135deg, ${planCfg.color}22, ${planCfg.color}44)`,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontWeight: '700', fontSize: '15px', color: planCfg.color, flexShrink: 0,
                        }}>
                          {brand.name[0]?.toUpperCase()}
                        </div>
                        <div>
                          <div style={{ fontWeight: '600', fontSize: '13px' }}>{brand.name}</div>
                          <div style={{ fontSize: '11px', color: '#94a3b8' }}>{brand.slug}</div>
                        </div>
                      </div>
                    </td>

                    {/* Owner */}
                    {!isMobile && (
                      <td style={s.td}>
                        <div style={{ fontSize: '13px', fontWeight: '500' }}>{brand.owner?.username || '—'}</div>
                        <div style={{ fontSize: '11px', color: '#94a3b8' }}>{brand.owner?.email || ''}</div>
                      </td>
                    )}

                    {/* Plan Badge */}
                    <td style={s.td}>
                      <span style={s.badge(planCfg.color, planCfg.bg)}>
                        <PlanIcon size={12} />
                        {brand.plan_display || planCfg.label}
                      </span>
                    </td>

                    {/* Member Count */}
                    {!isMobile && (
                      <td style={{ ...s.td, textAlign: 'center' }}>
                        <span style={{
                          background: '#f1f5f9', padding: '4px 10px', borderRadius: '8px',
                          fontSize: '12px', fontWeight: '600', color: '#475569',
                        }}>
                          {brand.member_count ?? 0}
                        </span>
                      </td>
                    )}

                    {/* Status Toggle */}
                    <td style={{ ...s.td, textAlign: 'center' }}>
                      <button
                        onClick={() => onToggle(brand)}
                        style={{
                          background: brand.is_active ? '#ecfdf5' : '#fef2f2',
                          color: brand.is_active ? '#059669' : '#dc2626',
                          border: 'none', borderRadius: '20px', padding: '5px 12px',
                          fontSize: '11px', fontWeight: '600', cursor: 'pointer',
                          display: 'inline-flex', alignItems: 'center', gap: '4px',
                        }}
                      >
                        {brand.is_active
                          ? <><ToggleRight size={14} /> Aktif</>
                          : <><ToggleLeft size={14} /> Pasif</>
                        }
                      </button>
                    </td>

                    {/* Actions */}
                    <td style={{ ...s.td, textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '5px', justifyContent: 'flex-end' }}>
                        <button onClick={() => onEdit(brand)} title="Düzenle / Sahip Yönet" style={s.iconBtn('#6366f1', '#eef2ff')}>
                          <Edit3 size={14} />
                        </button>
                        <button
                          onClick={() => onEnterStore(brand)}
                          title={brand.owner ? 'Mağazaya Gir' : 'Önce sahip atayın'}
                          disabled={!brand.owner}
                          style={{
                            ...s.iconBtn(brand.owner ? '#059669' : '#94a3b8', brand.owner ? '#ecfdf5' : '#f1f5f9'),
                            opacity: brand.owner ? 1 : 0.5,
                            cursor: brand.owner ? 'pointer' : 'not-allowed',
                          }}
                        >
                          <LogIn size={14} />
                        </button>
                        <button onClick={() => onDelete(brand)} title="Sil" style={s.iconBtn('#ef4444', '#fef2f2')}>
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════
// ── USERS TAB ──────────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════
function UsersTab({ users, search, setSearch, brandFilter, setBrandFilter, brandsForFilter, isMobile, onImpersonate }) {
  return (
    <div>
      {/* Search + Filter bar */}
      <div style={{
        display: 'flex', gap: '10px', marginBottom: '16px',
        flexDirection: isMobile ? 'column' : 'row',
      }}>
        <div style={{
          flex: 1, display: 'flex', alignItems: 'center', gap: '8px',
          background: '#f8fafc', borderRadius: '10px', padding: '8px 14px',
          border: '1px solid var(--panel-border, #e2e8f0)',
        }}>
          <Search size={16} color="#94a3b8" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Mağaza sahibi ara..."
            style={{
              border: 'none', background: 'transparent', outline: 'none',
              fontSize: '13px', color: 'var(--text-main, #1e293b)', width: '100%',
            }}
          />
          {search && (
            <button onClick={() => setSearch('')} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
              <X size={14} color="#94a3b8" />
            </button>
          )}
        </div>

        {/* Brand filter dropdown */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '6px',
          background: '#f8fafc', borderRadius: '10px', padding: '8px 14px',
          border: '1px solid var(--panel-border, #e2e8f0)',
          minWidth: isMobile ? undefined : '200px',
          position: 'relative',
        }}>
          <Filter size={14} color="#94a3b8" />
          <select
            value={brandFilter}
            onChange={(e) => setBrandFilter(e.target.value)}
            style={{
              border: 'none', background: 'transparent', outline: 'none',
              fontSize: '13px', color: 'var(--text-main, #1e293b)',
              cursor: 'pointer', width: '100%',
              appearance: 'none',
            }}
          >
            <option value="">Tüm Markalar</option>
            {brandsForFilter.map(([id, name]) => (
              <option key={id} value={String(id)}>{name}</option>
            ))}
          </select>
          <ChevronDown size={14} color="#94a3b8" style={{ flexShrink: 0 }} />
        </div>
      </div>

      {/* Table */}
      <div style={{ ...s.card, padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid var(--panel-border, #e2e8f0)' }}>
                <th style={s.th}>Kullanıcı</th>
                {!isMobile && <th style={s.th}>E-posta</th>}
                <th style={s.th}>Rol</th>
                {!isMobile && <th style={s.th}>Marka</th>}
                <th style={{ ...s.th, textAlign: 'center' }}>Durum</th>
                <th style={{ ...s.th, textAlign: 'right' }}>İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan={isMobile ? 4 : 6} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted, #64748b)', fontSize: '13px' }}>
                    Mağaza sahibi bulunamadı.
                  </td>
                </tr>
              ) : users.map(user => {
                const roleCfg = ROLE_CONFIG[user.role] || ROLE_CONFIG.staff;
                return (
                  <tr
                    key={user.id}
                    style={{ borderBottom: '1px solid var(--panel-border, #e2e8f0)', transition: 'background 0.15s' }}
                    onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    {/* User */}
                    <td style={s.td}>
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
                          <div style={{ fontWeight: '600', fontSize: '13px' }}>
                            {user.first_name || user.last_name
                              ? `${user.first_name} ${user.last_name}`.trim()
                              : user.username
                            }
                          </div>
                          <div style={{ fontSize: '11px', color: '#94a3b8' }}>@{user.username}</div>
                        </div>
                      </div>
                    </td>

                    {/* Email */}
                    {!isMobile && (
                      <td style={{ ...s.td, color: '#64748b', fontSize: '12px' }}>{user.email || '—'}</td>
                    )}

                    {/* Role */}
                    <td style={s.td}>
                      <span style={s.badge(roleCfg.color, roleCfg.bg)}>
                        {user.role_display || roleCfg.label}
                      </span>
                    </td>

                    {/* Brand */}
                    {!isMobile && (
                      <td style={s.td}>
                        {user.brand ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Building2 size={13} color="#94a3b8" />
                            <span style={{ fontSize: '12px', fontWeight: '500' }}>{user.brand.name}</span>
                          </div>
                        ) : (
                          <span style={{ color: '#94a3b8', fontSize: '12px' }}>—</span>
                        )}
                      </td>
                    )}

                    {/* Status */}
                    <td style={{ ...s.td, textAlign: 'center' }}>
                      <span style={{
                        background: user.is_active ? '#ecfdf5' : '#fef2f2',
                        color: user.is_active ? '#059669' : '#dc2626',
                        padding: '4px 10px', borderRadius: '20px',
                        fontSize: '11px', fontWeight: '600',
                      }}>
                        {user.is_active ? 'Aktif' : 'Pasif'}
                      </span>
                    </td>

                    {/* Actions */}
                    <td style={{ ...s.td, textAlign: 'right' }}>
                      <button
                        onClick={() => onImpersonate(user.id, user.username)}
                        title="Bu kullanıcı olarak giriş yap"
                        style={{
                          ...s.iconBtn('#f59e0b', '#fffbeb'),
                          padding: '6px 12px',
                          gap: '5px',
                          fontSize: '11px',
                          fontWeight: '600',
                        }}
                      >
                        <LogIn size={14} />
                        {!isMobile && 'Giriş Yap'}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════
// ── ACTIVITY TAB ───────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════
function ActivityTab({ stats, isMobile }) {
  const recentBrands = stats?.recent_brands || [];
  const recentUsers = stats?.recent_users || [];

  const timeline = [
    ...recentBrands.map(b => ({
      type: 'brand',
      icon: Building2,
      color: '#6366f1',
      bg: '#eef2ff',
      title: b.name,
      subtitle: `Yeni marka oluşturuldu • ${b.plan_display || b.plan || 'Starter'}`,
      time: b.created_at,
    })),
    ...recentUsers.map(u => ({
      type: 'user',
      icon: UserPlus,
      color: '#10b981',
      bg: '#ecfdf5',
      title: u.username || `${u.first_name} ${u.last_name}`.trim(),
      subtitle: `Yeni mağaza sahibi kayıt oldu${u.brand ? ` • ${u.brand.name || u.brand}` : ''}`,
      time: u.date_joined || u.created_at,
    })),
  ].sort((a, b) => new Date(b.time) - new Date(a.time));

  if (timeline.length === 0) {
    return (
      <div style={{
        ...s.card,
        textAlign: 'center',
        padding: '60px 20px',
        color: 'var(--text-muted, #64748b)',
      }}>
        <Activity size={40} color="#cbd5e1" style={{ marginBottom: '12px' }} />
        <div style={{ fontSize: '14px', fontWeight: '500' }}>Henüz aktivite bulunmuyor</div>
        <div style={{ fontSize: '12px', marginTop: '4px' }}>Yeni markalar ve kullanıcılar burada görünecek.</div>
      </div>
    );
  }

  return (
    <div style={s.card}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: '8px',
        marginBottom: '20px', paddingBottom: '14px',
        borderBottom: '1px solid var(--panel-border, #e2e8f0)',
      }}>
        <Activity size={18} color="var(--primary, #6366f1)" />
        <span style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-main, #1e293b)' }}>
          Son Aktiviteler
        </span>
        <span style={{
          background: '#eef2ff', color: '#6366f1', padding: '2px 8px',
          borderRadius: '8px', fontSize: '11px', fontWeight: '600',
        }}>
          {timeline.length}
        </span>
      </div>

      <div style={{ position: 'relative' }}>
        {/* Vertical line */}
        <div style={{
          position: 'absolute',
          left: '19px',
          top: '0',
          bottom: '0',
          width: '2px',
          background: '#e2e8f0',
          borderRadius: '1px',
        }} />

        {timeline.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div
              key={idx}
              style={{
                display: 'flex',
                gap: '14px',
                padding: '14px 0',
                position: 'relative',
                alignItems: 'flex-start',
              }}
            >
              {/* Icon circle */}
              <div style={{
                width: '40px', height: '40px', borderRadius: '12px',
                background: item.bg,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
                zIndex: 1,
                border: '3px solid #fff',
              }}>
                <Icon size={18} color={item.color} />
              </div>

              {/* Content */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  fontSize: '13px', fontWeight: '600',
                  color: 'var(--text-main, #1e293b)',
                  marginBottom: '2px',
                }}>
                  {item.title}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted, #64748b)' }}>
                  {item.subtitle}
                </div>
              </div>

              {/* Time */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: '4px',
                fontSize: '11px', color: '#94a3b8', whiteSpace: 'nowrap',
                flexShrink: 0,
              }}>
                <Clock size={12} />
                {timeAgo(item.time)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
