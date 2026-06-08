import React, { useState, useEffect } from 'react';
import { useResponsive } from '../hooks/useResponsive';
import { 
  TrendingUp, Users, ShoppingBag, PieChart, DollarSign, 
  Building2,
  CreditCard, FileText, CheckCircle, Clock, ChevronRight, Star, Zap, Crown,
  GitBranch
} from 'lucide-react';

import { apiFetch, API_BASE } from '../lib/apiClient';

const PLAN_CONFIG = {
  starter: {
    label: 'Starter',
    price: 499,
    color: '#6366f1',
    bg: 'rgba(99,102,241,0.08)',
    border: 'rgba(99,102,241,0.25)',
    icon: Zap,
    features: ['1 Şube', '5 Ekip Üyesi', 'Temel Raporlar', '14 Gün Deneme'],
  },
  growth: {
    label: 'Growth',
    price: 999,
    color: '#10b981',
    bg: 'rgba(16,185,129,0.08)',
    border: 'rgba(16,185,129,0.25)',
    icon: Star,
    features: ['3 Şube', '15 Ekip Üyesi', 'Franchise Paneli', 'Web Sitesi', 'QR Menü'],
  },
  enterprise: {
    label: 'Enterprise',
    price: 1999,
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.08)',
    border: 'rgba(245,158,11,0.25)',
    icon: Crown,
    features: ['Sınırsız Şube', 'Sınırsız Ekip', 'WhatsApp', 'CRM', 'Öncelikli Destek'],
  },
};

export default function Dashboard({ currentUser, authToken, setCurrentTab, onUserUpdate }) {
  const { isMobile } = useResponsive();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  // Plan & Invoice states
  const [invoices, setInvoices] = useState([]);
  const [loadingInvoices, setLoadingInvoices] = useState(false);
  const [planSection, setPlanSection] = useState('overview'); // 'overview' | 'change' | 'invoices'
  const [selectedPlan, setSelectedPlan] = useState('');
  const [changingPlan, setChangingPlan] = useState(false);
  const [planMessage, setPlanMessage] = useState('');
  const [planError, setPlanError] = useState('');
  const [paymentProvider, setPaymentProvider] = useState('mock');

  const isStoreOwner = currentUser?.role === 'store_owner';
  const canManagePlan = isStoreOwner;

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Token ${authToken}`
  };

  useEffect(() => {
    fetchStats();
    if (canManagePlan) {
      fetchInvoices();
      fetchPaymentProviders();
    }
  }, [authToken]);

  const fetchPaymentProviders = async () => {
    try {
      const res = await apiFetch(`${API_BASE}/auth/payment-providers/`, { headers });
      if (res.ok) {
        const data = await res.json();
        setPaymentProvider(data.active_provider || 'mock');
      }
    } catch (err) {
      console.error('Payment providers:', err);
    }
  };

  const fetchStats = async () => {
    try {
      setLoading(true);
      const res = await apiFetch(`${API_BASE}/dashboard-stats/`, { headers });
      const data = await res.json();
      setStats(data);
    } catch (err) {
      console.error('Dashboard stats error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchInvoices = async () => {
    try {
      setLoadingInvoices(true);
      const res = await apiFetch(`${API_BASE}/auth/invoices/`, { headers });
      if (res.ok) {
        const data = await res.json();
        setInvoices(data);
      }
    } catch (err) {
      console.error('Invoice error:', err);
    } finally {
      setLoadingInvoices(false);
    }
  };

  const handleChangePlan = async () => {
    if (!selectedPlan) return;
    const brandId = currentUser?.brand?.id;
    if (!brandId) { setPlanError('Marka bilgisi bulunamadı.'); return; }

    setChangingPlan(true);
    setPlanMessage('');
    setPlanError('');
    try {
      const res = await apiFetch(`${API_BASE}/auth/brands/${brandId}/checkout/`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ plan: selectedPlan }),
      });
      const data = await res.json();
      if (!res.ok) {
        setPlanError(data.error || 'Ödeme başlatılamadı.');
        return;
      }

      if (data.checkout_url) {
        window.location.href = data.checkout_url;
        return;
      }

      setPlanMessage(`✅ Plan başarıyla "${PLAN_CONFIG[selectedPlan]?.label}" olarak güncellendi!`);
      const meRes = await apiFetch(`${API_BASE}/auth/me/`, { headers });
      if (meRes.ok) {
        const meData = await meRes.json();
        if (onUserUpdate) onUserUpdate(meData.user);
      }
      fetchInvoices();
      setPlanSection('invoices');
    } catch (err) {
      setPlanError('Sunucu bağlantı hatası.');
    } finally {
      setChangingPlan(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
        <div className="spinner"></div>
      </div>
    );
  }

  if (!stats) {
    return <div className="card">Veriler yüklenemedi. Sunucu bağlantısını veya oturum durumunu kontrol edin.</div>;
  }

  // Chart calculations
  const sales = stats.daily_sales || [];
  const maxRevenue = Math.max(...sales.map(s => s.revenue), 100) * 1.1;
  const svgWidth = 600, svgHeight = 220, paddingX = 40, paddingY = 30;
  const points = sales.map((s, idx) => ({
    x: paddingX + (idx / Math.max(sales.length - 1, 1)) * (svgWidth - paddingX * 2),
    y: svgHeight - paddingY - (s.revenue / maxRevenue) * (svgHeight - paddingY * 2),
    ...s
  }));
  const pathD = points.length > 0 ? `M ${points[0].x} ${points[0].y} ` + points.slice(1).map(p => `L ${p.x} ${p.y}`).join(' ') : '';
  const areaD = points.length > 0 ? `${pathD} L ${points[points.length - 1].x} ${svgHeight - paddingY} L ${points[0].x} ${svgHeight - paddingY} Z` : '';

  const currentPlan = currentUser?.brand?.plan || 'starter';
  const currentPlanCfg = PLAN_CONFIG[currentPlan] || PLAN_CONFIG.starter;
  const CurrentPlanIcon = currentPlanCfg.icon;
  const planStatus = currentUser?.brand?.plan_status;
  const brandUsage = currentUser?.brand?.usage;
  const brandLimits = currentUser?.brand?.limits;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

      {/* Welcome + Brand Card */}
      <div className="card" style={{
        padding: '24px', display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        justifyContent: 'space-between', alignItems: isMobile ? 'flex-start' : 'center',
        gap: '20px',
        background: 'linear-gradient(135deg, var(--bg-card) 0%, rgba(99,102,241,0.04) 100%)',
        border: '1px solid var(--panel-border)', boxShadow: '0 4px 30px rgba(0,0,0,0.15)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '18px' }}>
          <div style={{ position: 'relative', flexShrink: 0 }}>
            {currentUser?.avatar ? (
              <img src={currentUser.avatar} alt="Profile"
                style={{ width: '64px', height: '64px', borderRadius: '50%', objectFit: 'cover', border: '3px solid var(--primary)' }} />
            ) : (
              <div style={{
                width: '64px', height: '64px', borderRadius: '50%',
                background: 'rgba(99,102,241,0.15)', color: 'var(--primary)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: '800', fontSize: '22px', border: '2.5px solid var(--primary)'
              }}>
                {currentUser?.first_name ? currentUser.first_name[0].toUpperCase() : (currentUser?.username || 'U')[0].toUpperCase()}
              </div>
            )}
            <span style={{ position: 'absolute', bottom: '2px', right: '2px', width: '14px', height: '14px', background: '#10b981', border: '2.5px solid var(--bg-card)', borderRadius: '50%' }} />
          </div>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: '800', margin: 0, color: 'var(--text-main)' }}>
              Hoş Geldiniz, {currentUser?.first_name || currentUser?.username} 👋
            </h2>
            <div style={{ display: 'flex', gap: '6px', alignItems: 'center', marginTop: '6px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '11px', color: 'var(--primary)', fontWeight: '700', background: 'rgba(99,102,241,0.08)', padding: '2px 8px', borderRadius: '20px' }}>
                {currentUser?.role_display || 'Kullanıcı'}
              </span>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>• {currentUser?.email}</span>
            </div>
          </div>
        </div>

        <div style={{
          display: 'flex', alignItems: 'center', gap: '16px',
          background: 'rgba(255,255,255,0.02)', border: '1px solid var(--panel-border)',
          padding: '12px 20px', borderRadius: '14px',
          width: isMobile ? '100%' : 'auto', justifyContent: 'space-between'
        }}>
          <div>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'block', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: '700' }}>Aktif Marka</span>
            <span style={{ fontSize: '14px', fontWeight: '800', color: 'var(--text-main)' }}>
              🏢 {currentUser?.brand?.name || 'KobiPOS Restoran'}
            </span>
          </div>
          <span style={{
            padding: '4px 12px', borderRadius: '8px',
            background: currentPlanCfg.bg, color: currentPlanCfg.color,
            fontSize: '11px', fontWeight: '700', textTransform: 'uppercase',
            border: `1px solid ${currentPlanCfg.border}`
          }}>
            <CurrentPlanIcon size={12} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
            {currentPlanCfg.label}
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-header">
            <span>Bugün Toplam Ciro</span>
            <div className="stat-icon-wrapper revenue"><DollarSign size={20} /></div>
          </div>
          <div className="stat-value">{stats.today_revenue.toLocaleString('tr-TR')} ₺</div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Anlık gerçekleşen ödemeler</span>
        </div>
        <div className="stat-card">
          <div className="stat-header">
            <span>Aktif Masa Doluluğu</span>
            <div className="stat-icon-wrapper tables"><Users size={20} /></div>
          </div>
          <div className="stat-value">{stats.active_tables} / {stats.active_tables + stats.empty_tables}</div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Boş masa sayısı: {stats.empty_tables}</span>
        </div>
        <div className="stat-card">
          <div className="stat-header">
            <span>Hazırlanan Siparişler</span>
            <div className="stat-icon-wrapper orders"><ShoppingBag size={20} /></div>
          </div>
          <div className="stat-value">{stats.active_orders}</div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Mutfaktaki aktif siparişler</span>
        </div>
        <div className="stat-card">
          <div className="stat-header">
            <span>Nakit / Kart Dağılımı</span>
            <div className="stat-icon-wrapper empty"><PieChart size={20} /></div>
          </div>
          <div className="stat-value">
            <span style={{ fontSize: '16px', color: 'var(--success)' }}>{stats.payment_methods.cash.toLocaleString('tr-TR')} ₺</span>
            <span style={{ fontSize: '16px', color: 'var(--text-muted)', margin: '0 8px' }}>/</span>
            <span style={{ fontSize: '16px', color: 'var(--accent)' }}>{stats.payment_methods.card.toLocaleString('tr-TR')} ₺</span>
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Nakit / Kredi Kartı cirosu</span>
        </div>
      </div>

      {/* ── Plan & Billing Section (store_owner only) ── */}
      {canManagePlan && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          {/* Section Header */}
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '20px 24px', borderBottom: '1px solid var(--panel-border)',
            background: 'linear-gradient(135deg, rgba(99,102,241,0.04) 0%, rgba(168,85,247,0.04) 100%)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'linear-gradient(135deg, #6366f1, #a855f7)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <CreditCard size={18} color="#fff" />
              </div>
              <div>
                <h3 style={{ fontSize: '15px', fontWeight: '800', margin: 0 }}>Plan & Fatura İşlemleri</h3>
                <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: 0 }}>Abonelik planınızı ve faturalarınızı yönetin</p>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '6px' }}>
              {['overview', 'change', 'invoices'].map(tab => (
                <button key={tab} onClick={() => { setPlanSection(tab); setPlanMessage(''); setPlanError(''); }}
                  style={{
                    padding: '6px 14px', borderRadius: '8px', border: 'none', cursor: 'pointer',
                    fontSize: '12px', fontWeight: '600',
                    background: planSection === tab ? 'var(--primary)' : 'rgba(255,255,255,0.04)',
                    color: planSection === tab ? '#fff' : 'var(--text-muted)',
                    transition: 'all 0.15s'
                  }}>
                  {tab === 'overview' ? '📊 Özet' : tab === 'change' ? '🔄 Plan Değiştir' : '🧾 Faturalar'}
                </button>
              ))}
            </div>
          </div>

          <div style={{ padding: '24px' }}>
            {/* Overview Tab */}
            {planSection === 'overview' && (
              <div>
                {planStatus && planStatus.status !== 'unlimited' && (
                  <div style={{
                    marginBottom: '20px', padding: '14px 18px', borderRadius: '12px',
                    background: planStatus.status === 'expired' || planStatus.status === 'grace' ? 'rgba(239,68,68,0.08)' : 'rgba(245,158,11,0.08)',
                    border: `1px solid ${planStatus.status === 'expired' || planStatus.status === 'grace' ? 'rgba(239,68,68,0.25)' : 'rgba(245,158,11,0.25)'}`,
                    fontSize: '13px', color: 'var(--text-main)',
                  }}>
                    <div style={{ fontWeight: '700', marginBottom: '6px' }}>
                      {planStatus.is_trial ? '🎁 Deneme Süresi' : '📅 Abonelik Durumu'}
                    </div>
                    <div style={{ color: 'var(--text-muted)', lineHeight: 1.5 }}>
                      {planStatus.message || 'Planınız aktif.'}
                      {planStatus.plan_expiry && (
                        <span> Bitiş tarihi: <strong>{planStatus.plan_expiry}</strong></span>
                      )}
                    </div>
                    {brandUsage && brandLimits && (
                      <div style={{ marginTop: '10px', display: 'flex', gap: '16px', fontSize: '12px', flexWrap: 'wrap' }}>
                        <span>Şube: <strong>{brandUsage.branches}/{brandLimits.branches}</strong></span>
                        <span>Ekip: <strong>{brandUsage.staff}/{brandLimits.staff}</strong></span>
                      </div>
                    )}
                  </div>
                )}
                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: '16px' }}>
                  {Object.entries(PLAN_CONFIG).map(([key, cfg]) => {
                    const Icon = cfg.icon;
                    const isActive = currentPlan === key;
                    return (
                      <div key={key} style={{
                        border: `2px solid ${isActive ? cfg.color : 'var(--panel-border)'}`,
                        borderRadius: '14px', padding: '20px',
                        background: isActive ? cfg.bg : 'transparent',
                        position: 'relative', transition: 'all 0.2s'
                      }}>
                        {isActive && (
                          <span style={{
                            position: 'absolute', top: '12px', right: '12px',
                            background: cfg.color, color: '#fff', fontSize: '10px',
                            fontWeight: '700', padding: '2px 8px', borderRadius: '20px'
                          }}>AKTİF</span>
                        )}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                          <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: cfg.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <Icon size={18} color={cfg.color} />
                          </div>
                          <div>
                            <div style={{ fontSize: '14px', fontWeight: '800', color: 'var(--text-main)' }}>{cfg.label}</div>
                            <div style={{ fontSize: '18px', fontWeight: '900', color: cfg.color }}>{cfg.price.toLocaleString('tr-TR')} ₺<span style={{ fontSize: '11px', fontWeight: '500', color: 'var(--text-muted)' }}>/ay</span></div>
                          </div>
                        </div>
                        <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {cfg.features.map(f => (
                            <li key={f} style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <CheckCircle size={12} color={cfg.color} /> {f}
                            </li>
                          ))}
                        </ul>
                        {!isActive && isStoreOwner && (
                          <button onClick={() => { setSelectedPlan(key); setPlanSection('change'); }}
                            className="btn btn-secondary"
                            style={{ width: '100%', marginTop: '16px', fontSize: '12px', padding: '8px' }}>
                            Bu Plana Geç
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Change Plan Tab */}
            {planSection === 'change' && isStoreOwner && (
              <div style={{ maxWidth: '520px', margin: '0 auto' }}>
                <h4 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '6px' }}>Plan Değiştir</h4>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '20px' }}>Mevcut planınız: <strong style={{ color: currentPlanCfg.color }}>{currentPlanCfg.label}</strong>. Yeni plan seçerek aboneliğinizi güncelleyebilirsiniz.</p>

                {planMessage && (
                  <div style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '10px', padding: '12px 16px', marginBottom: '16px', fontSize: '13px', color: '#10b981' }}>
                    {planMessage}
                  </div>
                )}
                {planError && (
                  <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '10px', padding: '12px 16px', marginBottom: '16px', fontSize: '13px', color: '#ef4444' }}>
                    ⚠️ {planError}
                  </div>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
                  {Object.entries(PLAN_CONFIG).map(([key, cfg]) => {
                    const Icon = cfg.icon;
                    const isActive = currentPlan === key;
                    return (
                      <label key={key} style={{
                        display: 'flex', alignItems: 'center', gap: '14px',
                        padding: '14px 16px', borderRadius: '12px', cursor: isActive ? 'not-allowed' : 'pointer',
                        border: `2px solid ${selectedPlan === key ? cfg.color : isActive ? cfg.color : 'var(--panel-border)'}`,
                        background: selectedPlan === key ? cfg.bg : isActive ? `${cfg.bg}80` : 'transparent',
                        opacity: isActive ? 0.65 : 1, transition: 'all 0.15s'
                      }}>
                        <input type="radio" name="plan" value={key}
                          checked={selectedPlan === key}
                          disabled={isActive}
                          onChange={() => setSelectedPlan(key)}
                          style={{ accentColor: cfg.color }} />
                        <Icon size={18} color={cfg.color} />
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-main)' }}>{cfg.label} {isActive && <span style={{ fontSize: '10px', color: cfg.color }}>(Mevcut Plan)</span>}</div>
                          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{cfg.features.join(' · ')}</div>
                        </div>
                        <div style={{ fontSize: '16px', fontWeight: '900', color: cfg.color, whiteSpace: 'nowrap' }}>{cfg.price.toLocaleString('tr-TR')} ₺/ay</div>
                      </label>
                    );
                  })}
                </div>

                <button onClick={handleChangePlan} disabled={!selectedPlan || changingPlan}
                  className="btn btn-primary"
                  style={{ width: '100%', padding: '12px', fontSize: '14px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', opacity: !selectedPlan || changingPlan ? 0.6 : 1 }}>
                  {changingPlan ? <><div className="spinner" style={{ width: '16px', height: '16px', margin: 0 }} /> İşleniyor...</> : <><CreditCard size={16} /> {paymentProvider === 'mock' ? 'Planı Aktifleştir (Test)' : 'Ödemeye Geç'}</>}
                </button>
                <p style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center', marginTop: '8px' }}>
                  {paymentProvider === 'mock'
                    ? 'Geliştirme modu: gerçek ödeme alınmaz, plan anında aktifleşir.'
                    : paymentProvider === 'stripe'
                      ? 'Stripe güvenli ödeme sayfasına yönlendirileceksiniz.'
                      : 'iyzico güvenli ödeme sayfasına yönlendirileceksiniz.'}
                </p>
              </div>
            )}

            {/* Invoices Tab */}
            {planSection === 'invoices' && (
              <div>
                {planMessage && (
                  <div style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '10px', padding: '12px 16px', marginBottom: '16px', fontSize: '13px', color: '#10b981' }}>
                    {planMessage}
                  </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '700', margin: 0 }}>Fatura Geçmişi</h4>
                  <button onClick={fetchInvoices} className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <RefreshCw size={13} /> Yenile
                  </button>
                </div>
                {loadingInvoices ? (
                  <div style={{ display: 'flex', justifyContent: 'center', padding: '30px' }}><div className="spinner" /></div>
                ) : invoices.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)', fontSize: '13px' }}>
                    <FileText size={36} style={{ opacity: 0.3, marginBottom: '12px', display: 'block', margin: '0 auto 12px' }} />
                    Henüz fatura kaydı bulunmuyor.
                  </div>
                ) : (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                      <thead>
                        <tr style={{ background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--panel-border)' }}>
                          {['Fatura No', 'Plan', 'Tutar', 'Tarih', 'Durum'].map(h => (
                            <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontWeight: '600', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {invoices.map(inv => {
                          const planCfg = PLAN_CONFIG[inv.plan] || PLAN_CONFIG.starter;
                          return (
                            <tr key={inv.id} style={{ borderBottom: '1px solid var(--panel-border)' }}
                              onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
                              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                              <td style={{ padding: '12px 14px', fontWeight: '600', fontFamily: 'monospace', fontSize: '12px' }}>{inv.invoice_number}</td>
                              <td style={{ padding: '12px 14px' }}>
                                <span style={{ background: planCfg.bg, color: planCfg.color, padding: '3px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: '700' }}>
                                  {planCfg.label}
                                </span>
                              </td>
                              <td style={{ padding: '12px 14px', fontWeight: '700', color: 'var(--text-main)' }}>{inv.amount.toLocaleString('tr-TR')} ₺</td>
                              <td style={{ padding: '12px 14px', color: 'var(--text-muted)', fontSize: '12px' }}>
                                {new Date(inv.created_at).toLocaleDateString('tr-TR')}
                              </td>
                              <td style={{ padding: '12px 14px' }}>
                                <span style={{
                                  display: 'inline-flex', alignItems: 'center', gap: '4px',
                                  background: inv.paid ? 'rgba(16,185,129,0.08)' : 'rgba(245,158,11,0.08)',
                                  color: inv.paid ? '#10b981' : '#f59e0b',
                                  padding: '3px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: '700'
                                }}>
                                  {inv.paid ? <CheckCircle size={11} /> : <Clock size={11} />}
                                  {inv.paid ? 'Ödendi' : 'Bekliyor'}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {isStoreOwner && (
        <div className="card" style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', justifyContent: 'space-between', alignItems: isMobile ? 'flex-start' : 'center', gap: '12px', background: 'linear-gradient(135deg, rgba(16,185,129,0.06) 0%, transparent 100%)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <GitBranch size={22} style={{ color: '#059669' }} />
            <div>
              <strong style={{ fontSize: '14px' }}>Franchise (Şube) Merkezi</strong>
              <p style={{ margin: '4px 0 0', fontSize: '12px', color: 'var(--text-muted)' }}>
                Harici franchise paneli ve şube şifreleri ayrı modülde yönetilir.
              </p>
            </div>
          </div>
          <button onClick={() => setCurrentTab('franchise-mgmt')} className="btn btn-primary" style={{ padding: '8px 16px', fontSize: '12px', whiteSpace: 'nowrap' }}>
            Franchise Merkezine Git →
          </button>
        </div>
      )}

      {/* Weekly Sales Chart + Popular Items */}
      <div className="dashboard-grid">
        <div className="card">
          <div className="card-title">
            <span>Haftalık Satış Grafiği</span>
            <span style={{ fontSize: '12px', color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <TrendingUp size={14} /> Son 7 Gün Satış Analizi
            </span>
          </div>
          <div className="chart-container">
            <svg className="chart-svg" viewBox={`0 0 ${svgWidth} ${svgHeight}`}>
              <defs>
                <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="var(--primary)" stopOpacity="0.0" />
                </linearGradient>
              </defs>
              {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
                const y = paddingY + ratio * (svgHeight - paddingY * 2);
                return <line key={i} x1={paddingX} y1={y} x2={svgWidth - paddingX} y2={y} stroke="rgba(255,255,255,0.06)" strokeWidth="1" />;
              })}
              {areaD && <path d={areaD} fill="url(#chartGradient)" />}
              {pathD && <path d={pathD} fill="none" stroke="var(--primary)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />}
              {points.map((p, idx) => (
                <g key={idx}>
                  <circle cx={p.x} cy={p.y} r="4" fill="var(--bg-dark)" stroke="var(--primary)" strokeWidth="2.5" />
                  <text x={p.x} y={p.y - 12} fill="white" fontSize="10" fontWeight="bold" textAnchor="middle">
                    {p.revenue > 0 ? `${Math.round(p.revenue)}₺` : ''}
                  </text>
                  <text x={p.x} y={svgHeight - 8} fill="var(--text-muted)" fontSize="11" textAnchor="middle">{p.date}</text>
                </g>
              ))}
            </svg>
          </div>
        </div>

        <div className="card">
          <div className="card-title">En Popüler Ürünler</div>
          <div className="popular-item-list">
            {stats.popular_items && stats.popular_items.length > 0 ? (
              stats.popular_items.map((item, idx) => (
                <div className="popular-item" key={idx}>
                  <div className="popular-item-info">
                    <div className="popular-item-rank">{idx + 1}</div>
                    <span className="popular-item-name">{item.name}</span>
                  </div>
                  <span className="popular-item-count">{item.count} adet</span>
                </div>
              ))
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '14px', textAlign: 'center', padding: '20px 0' }}>
                Henüz tamamlanmış satış bulunmuyor.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
