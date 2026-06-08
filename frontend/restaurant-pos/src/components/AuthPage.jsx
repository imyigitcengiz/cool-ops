import React, { useState } from 'react';
import { User, Lock, Mail, Building2, Crown, Zap, Rocket } from 'lucide-react';
import { useResponsive } from '../hooks/useResponsive';

const API_BASE = (import.meta.env.VITE_API_URL || '') + '/api';

const PLANS = [
  {
    key: 'starter',
    name: 'Starter',
    price: 'Ücretsiz',
    color: '#94a3b8',
    icon: Zap,
    features: ['Temel POS özellikleri', '5 masa', '1 kullanıcı'],
  },
  {
    key: 'growth',
    name: 'Growth',
    price: '₺999/ay',
    color: '#6366f1',
    icon: Rocket,
    recommended: true,
    features: ['QR Menü', 'Web Sitesi', '20 masa', '5 kullanıcı', 'Raporlar'],
  },
  {
    key: 'enterprise',
    name: 'Enterprise',
    price: '₺1999/ay',
    color: '#f59e0b',
    icon: Crown,
    features: ['Sınırsız', 'WhatsApp API', 'Kurye Takibi', 'Özel domain'],
  },
];

export default function AuthPage({ onLogin }) {
  const { isMobile } = useResponsive();

  const [activeTab, setActiveTab] = useState('login');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Login fields
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  // Register fields
  const [regUsername, setRegUsername] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regPasswordConfirm, setRegPasswordConfirm] = useState('');
  const [regBrandName, setRegBrandName] = useState('');
  const [regPlan, setRegPlan] = useState('growth');

  // ── Handlers ──────────────────────────────────────────

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: loginUsername, password: loginPassword }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.error || 'Giriş başarısız.'); return; }
      onLogin(data.token, data.user);
    } catch {
      setError('Sunucuya bağlanılamadı.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');

    if (regPassword.length < 6) { setError('Şifre en az 6 karakter olmalıdır.'); return; }
    if (regPassword !== regPasswordConfirm) { setError('Şifreler eşleşmiyor.'); return; }

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: regUsername,
          password: regPassword,
          email: regEmail,
          brand_name: regBrandName,
          plan: regPlan,
        }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.error || 'Kayıt başarısız.'); return; }
      onLogin(data.token, data.user);
    } catch {
      setError('Sunucuya bağlanılamadı.');
    } finally {
      setLoading(false);
    }
  };

  const handleSeedAdmin = async () => {
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/auth/seed-super-admin/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      if (!res.ok) { setError(data.error || 'Kurulum başarısız.'); return; }
      onLogin(data.token, data.user);
    } catch {
      setError('Sunucuya bağlanılamadı.');
    } finally {
      setLoading(false);
    }
  };

  // ── Shared input builder ──────────────────────────────

  const inputStyle = {
    width: '100%',
    padding: '12px 14px 12px 42px',
    borderRadius: '10px',
    border: '1.5px solid #e2e8f0',
    fontSize: '14px',
    color: '#0f172a',
    background: '#f8fafc',
    outline: 'none',
    transition: 'border-color 0.2s, box-shadow 0.2s',
    boxSizing: 'border-box',
  };

  const focusHandlers = {
    onFocus: (e) => { e.target.style.borderColor = '#6366f1'; e.target.style.boxShadow = '0 0 0 3px rgba(99,102,241,0.12)'; },
    onBlur: (e) => { e.target.style.borderColor = '#e2e8f0'; e.target.style.boxShadow = 'none'; },
  };

  const renderInput = (Icon, label, props) => (
    <div style={{ marginBottom: '14px' }}>
      <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: '#334155', marginBottom: '6px' }}>
        {label}
      </label>
      <div style={{ position: 'relative' }}>
        <Icon size={16} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
        <input style={inputStyle} {...focusHandlers} {...props} />
      </div>
    </div>
  );

  // ── Plan Cards ────────────────────────────────────────

  const renderPlanCards = () => (
    <div style={{ marginBottom: '18px' }}>
      <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: '#334155', marginBottom: '10px' }}>
        Plan Seçimi
      </label>
      <div style={{
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        gap: '10px',
      }}>
        {PLANS.map((plan) => {
          const selected = regPlan === plan.key;
          const PlanIcon = plan.icon;
          return (
            <div
              key={plan.key}
              onClick={() => setRegPlan(plan.key)}
              style={{
                flex: 1,
                border: selected ? `2px solid ${plan.color}` : '2px solid #e2e8f0',
                borderRadius: '14px',
                padding: '16px 14px',
                cursor: 'pointer',
                background: selected ? `${plan.color}0A` : '#fff',
                transition: 'all 0.25s ease',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              {plan.recommended && (
                <div style={{
                  position: 'absolute',
                  top: '8px',
                  right: '-28px',
                  background: plan.color,
                  color: '#fff',
                  fontSize: '9px',
                  fontWeight: '700',
                  padding: '2px 32px',
                  transform: 'rotate(45deg)',
                  letterSpacing: '0.5px',
                }}>
                  ÖNERİLEN
                </div>
              )}

              <div style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: `${plan.color}18`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '10px',
              }}>
                <PlanIcon size={18} style={{ color: plan.color }} />
              </div>

              <div style={{ fontWeight: '700', fontSize: '15px', color: '#0f172a', marginBottom: '2px' }}>
                {plan.name}
              </div>
              <div style={{ fontWeight: '800', fontSize: '14px', color: plan.color, marginBottom: '10px' }}>
                {plan.price}
              </div>

              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {plan.features.map((f, i) => (
                  <li key={i} style={{ fontSize: '11px', color: '#64748b', lineHeight: '1.8', display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <span style={{ color: plan.color, fontSize: '10px' }}>✓</span> {f}
                  </li>
                ))}
              </ul>

              {selected && (
                <div style={{
                  marginTop: '10px',
                  textAlign: 'center',
                  fontSize: '11px',
                  fontWeight: '700',
                  color: plan.color,
                }}>
                  ● Seçili
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );

  // ── Tab Button ────────────────────────────────────────

  const tabBtn = (key, label) => {
    const active = activeTab === key;
    return (
      <button
        type="button"
        onClick={() => { setActiveTab(key); setError(''); }}
        style={{
          flex: 1,
          padding: '10px 0',
          fontSize: '14px',
          fontWeight: '700',
          border: 'none',
          borderRadius: '10px',
          cursor: 'pointer',
          background: active ? '#fff' : 'transparent',
          color: active ? '#6366f1' : '#94a3b8',
          boxShadow: active ? '0 2px 8px rgba(99,102,241,0.12)' : 'none',
          transition: 'all 0.25s ease',
        }}
      >
        {label}
      </button>
    );
  };

  // ── Error block ───────────────────────────────────────

  const renderError = () =>
    error ? (
      <div style={{
        background: '#fef2f2',
        border: '1px solid #fca5a5',
        borderRadius: '10px',
        padding: '10px 14px',
        marginBottom: '14px',
        fontSize: '13px',
        color: '#991b1b',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
      }}>
        ⚠️ {error}
      </div>
    ) : null;

  // ── Submit button ─────────────────────────────────────

  const submitBtn = (label, loadingLabel) => (
    <button
      type="submit"
      disabled={loading}
      style={{
        width: '100%',
        padding: '14px',
        borderRadius: '12px',
        border: 'none',
        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
        color: '#fff',
        fontWeight: '700',
        fontSize: '15px',
        cursor: loading ? 'not-allowed' : 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        boxShadow: '0 4px 14px rgba(99,102,241,0.35)',
        transition: 'opacity 0.2s',
        opacity: loading ? 0.6 : 1,
      }}
    >
      {loading ? loadingLabel : label}
    </button>
  );

  // ── Render ────────────────────────────────────────────

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #6366f1 100%)',
      padding: isMobile ? '16px' : '24px',
      fontFamily: '"Inter", -apple-system, system-ui, sans-serif',
    }}>
      {/* Decorative blobs */}
      <div style={{ position: 'fixed', top: '-120px', right: '-80px', width: '400px', height: '400px', borderRadius: '50%', background: 'rgba(255,255,255,0.06)', pointerEvents: 'none' }} />
      <div style={{ position: 'fixed', bottom: '-160px', left: '-100px', width: '500px', height: '500px', borderRadius: '50%', background: 'rgba(255,255,255,0.04)', pointerEvents: 'none' }} />

      <div style={{
        width: '100%',
        maxWidth: activeTab === 'register' ? '620px' : '440px',
        background: 'rgba(255, 255, 255, 0.92)',
        backdropFilter: 'blur(24px)',
        WebkitBackdropFilter: 'blur(24px)',
        borderRadius: '24px',
        padding: isMobile ? '28px 20px' : '40px 36px',
        boxShadow: '0 25px 60px rgba(0,0,0,0.25), 0 0 0 1px rgba(255,255,255,0.15) inset',
        position: 'relative',
        overflow: 'hidden',
        transition: 'max-width 0.35s ease',
      }}>
        {/* Top accent gradient */}
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '4px', background: 'linear-gradient(90deg, #6366f1, #a855f7, #ec4899)' }} />

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, #6366f1, #a855f7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 14px',
            color: '#fff',
            fontWeight: '800',
            fontSize: '24px',
            boxShadow: '0 8px 24px rgba(99,102,241,0.35)',
          }}>K</div>
          <h1 style={{ fontSize: '22px', fontWeight: '800', color: '#0f172a', margin: 0, letterSpacing: '-0.5px' }}>
            KobiPOS
          </h1>
          <p style={{ fontSize: '13px', color: '#64748b', marginTop: '4px', marginBottom: 0 }}>
            Kobi Hub · Restoran yönetimi
          </p>
        </div>

        {/* Tab switcher */}
        <div style={{
          display: 'flex',
          background: '#f1f5f9',
          borderRadius: '12px',
          padding: '4px',
          marginBottom: '24px',
          gap: '4px',
        }}>
          {tabBtn('login', 'Giriş Yap')}
          {tabBtn('register', 'Kayıt Ol')}
        </div>

        {/* ── LOGIN TAB ── */}
        {activeTab === 'login' && (
          <form onSubmit={handleLogin}>
            {renderError()}

            {renderInput(User, 'Kullanıcı Adı', {
              type: 'text',
              value: loginUsername,
              onChange: (e) => setLoginUsername(e.target.value),
              placeholder: 'Kullanıcı adınız',
              required: true,
              autoComplete: 'username',
            })}

            {renderInput(Lock, 'Şifre', {
              type: 'password',
              value: loginPassword,
              onChange: (e) => setLoginPassword(e.target.value),
              placeholder: 'Şifreniz',
              required: true,
              autoComplete: 'current-password',
            })}

            <div style={{ marginTop: '6px' }}>
              {submitBtn('Giriş Yap', 'Giriş yapılıyor...')}
            </div>

            {/* Seed admin link */}
            <div style={{ textAlign: 'center', marginTop: '18px' }}>
              <button
                type="button"
                onClick={handleSeedAdmin}
                disabled={loading}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#6366f1',
                  fontSize: '12px',
                  cursor: 'pointer',
                  opacity: loading ? 0.5 : 0.8,
                  transition: 'opacity 0.2s',
                }}
                onMouseEnter={(e) => { e.target.style.opacity = '1'; }}
                onMouseLeave={(e) => { e.target.style.opacity = '0.8'; }}
              >
                İlk kurulum? Süper admin oluştur
              </button>
            </div>
          </form>
        )}

        {/* ── REGISTER TAB ── */}
        {activeTab === 'register' && (
          <form onSubmit={handleRegister}>
            {renderError()}

            <div style={{
              display: 'grid',
              gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr',
              gap: '0 14px',
            }}>
              {renderInput(User, 'Kullanıcı Adı', {
                type: 'text',
                value: regUsername,
                onChange: (e) => setRegUsername(e.target.value),
                placeholder: 'Kullanıcı adınız',
                required: true,
                autoComplete: 'username',
              })}

              {renderInput(Mail, 'E-posta', {
                type: 'email',
                value: regEmail,
                onChange: (e) => setRegEmail(e.target.value),
                placeholder: 'ornek@email.com',
                required: true,
                autoComplete: 'email',
              })}

              {renderInput(Lock, 'Şifre', {
                type: 'password',
                value: regPassword,
                onChange: (e) => setRegPassword(e.target.value),
                placeholder: 'En az 6 karakter',
                required: true,
                minLength: 6,
                autoComplete: 'new-password',
              })}

              {renderInput(Lock, 'Şifre Tekrar', {
                type: 'password',
                value: regPasswordConfirm,
                onChange: (e) => setRegPasswordConfirm(e.target.value),
                placeholder: 'Şifrenizi tekrar girin',
                required: true,
                autoComplete: 'new-password',
              })}
            </div>

            {renderInput(Building2, 'Marka Adı', {
              type: 'text',
              value: regBrandName,
              onChange: (e) => setRegBrandName(e.target.value),
              placeholder: 'İşletmenizin adı',
              required: true,
            })}

            {renderPlanCards()}

            {submitBtn('Hesap Oluştur', 'Hesap oluşturuluyor...')}
          </form>
        )}

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: '24px', paddingTop: '18px', borderTop: '1px solid #e2e8f0' }}>
          <p style={{ fontSize: '11px', color: '#94a3b8', margin: 0 }}>
            © 2025 Kobi Hub · KobiPOS • Tüm hakları saklıdır
          </p>
        </div>
      </div>
    </div>
  );
}
