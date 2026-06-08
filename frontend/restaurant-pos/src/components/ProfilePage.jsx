import React, { useState } from 'react';
import { User, Mail, Phone, Lock, Save, Check, Camera, Shield } from 'lucide-react';
import { useResponsive } from '../hooks/useResponsive';

import { apiFetch, API_BASE } from '../lib/apiClient';

const ROLE_LABELS = {
  super_admin: { label: 'Süper Yönetici', color: '#dc2626', bg: '#fef2f2' },
  store_owner: { label: 'Kurum Yöneticisi', color: '#7c3aed', bg: '#f5f3ff' },
  manager: { label: 'Operasyon Müdürü', color: '#2563eb', bg: '#eff6ff' },
  cashier: { label: 'Finans Sorumlusu', color: '#0891b2', bg: '#ecfeff' },
  kitchen: { label: 'Üretim Sorumlusu', color: '#059669', bg: '#ecfdf5' },
  waiter: { label: 'Servis Sorumlusu', color: '#d97706', bg: '#fffbeb' },
  staff: { label: 'Ekip Üyesi', color: '#059669', bg: '#ecfdf5' },
  admin: { label: 'Yönetici', color: '#7c3aed', bg: '#f5f3ff' },
};

export default function ProfilePage({ authToken, currentUser, onProfileUpdate }) {
  const { isMobile } = useResponsive();
  const [form, setForm] = useState({
    first_name: currentUser?.first_name || '',
    last_name: currentUser?.last_name || '',
    email: currentUser?.email || '',
    phone: currentUser?.phone || '',
  });
  const [passwordForm, setPasswordForm] = useState({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [showPasswordSection, setShowPasswordSection] = useState(false);

  const handleSave = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await apiFetch(`${API_BASE}/auth/me/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.error || 'Güncelleme başarısız.'); return; }
      setSuccess('Profil başarıyla güncellendi.');
      if (onProfileUpdate) onProfileUpdate(data.user);
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Sunucu hatası.');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setError('');
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setError('Yeni şifreler eşleşmiyor.');
      return;
    }
    if (passwordForm.new_password.length < 6) {
      setError('Şifre en az 6 karakter olmalıdır.');
      return;
    }
    setLoading(true);
    try {
      const res = await apiFetch(`${API_BASE}/auth/me/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
        body: JSON.stringify({
          old_password: passwordForm.old_password,
          new_password: passwordForm.new_password,
        }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.error || 'Şifre değiştirilemiyor.'); return; }
      setSuccess('Şifre başarıyla değiştirildi.');
      setPasswordForm({ old_password: '', new_password: '', confirm_password: '' });
      setShowPasswordSection(false);
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Sunucu hatası.');
    } finally {
      setLoading(false);
    }
  };

  const roleCfg = ROLE_LABELS[currentUser?.role] || ROLE_LABELS.staff;

  return (
    <div style={{ maxWidth: '700px' }}>
      {/* Profile Header Card */}
      <div className="card" style={{ marginBottom: '20px', position: 'relative', overflow: 'hidden' }}>
        {/* Accent gradient top */}
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '80px', background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)', borderRadius: '14px 14px 0 0' }} />

        <div style={{ position: 'relative', paddingTop: '40px', display: 'flex', alignItems: isMobile ? 'center' : 'flex-end', gap: '16px', flexDirection: isMobile ? 'column' : 'row' }}>
          {/* Avatar */}
          <div style={{
            width: '80px', height: '80px', borderRadius: '20px',
            background: 'linear-gradient(135deg, #e0e7ff, #c7d2fe)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: '800', fontSize: '32px', color: '#4f46e5',
            border: '4px solid var(--bg-card)', flexShrink: 0,
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          }}>
            {(currentUser?.first_name?.[0] || currentUser?.username?.[0] || 'U').toUpperCase()}
          </div>

          <div style={{ flex: 1, textAlign: isMobile ? 'center' : 'left' }}>
            <h2 style={{ fontSize: '20px', fontWeight: '700', margin: '0 0 4px 0' }}>
              {currentUser?.first_name} {currentUser?.last_name}
            </h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: isMobile ? 'center' : 'flex-start', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>@{currentUser?.username}</span>
              <span style={{
                display: 'inline-flex', alignItems: 'center', gap: '4px',
                background: roleCfg.bg, color: roleCfg.color,
                padding: '3px 10px', borderRadius: '8px', fontSize: '11px', fontWeight: '600',
              }}>
                <Shield size={11} /> {roleCfg.label}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Success / Error */}
      {success && (
        <div style={{ background: '#ecfdf5', border: '1px solid #10b981', borderRadius: '10px', padding: '12px 16px', marginBottom: '16px', fontSize: '13px', color: '#065f46', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Check size={16} /> {success}
        </div>
      )}
      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '10px', padding: '12px 16px', marginBottom: '16px', fontSize: '13px', color: '#991b1b' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Profile Form */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <User size={16} style={{ color: 'var(--primary)' }} /> Kişisel Bilgiler
        </h3>

        <form onSubmit={handleSave}>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
            <div className="form-group">
              <label>Ad</label>
              <input className="form-control" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} placeholder="Adınız" />
            </div>
            <div className="form-group">
              <label>Soyad</label>
              <input className="form-control" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} placeholder="Soyadınız" />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '14px', marginBottom: '20px' }}>
            <div className="form-group">
              <label><Mail size={13} style={{ verticalAlign: 'middle', marginRight: '4px' }} />E-posta</label>
              <input className="form-control" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="email@ornek.com" />
            </div>
            <div className="form-group">
              <label><Phone size={13} style={{ verticalAlign: 'middle', marginRight: '4px' }} />Telefon</label>
              <input className="form-control" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="+90 5XX XXX XX XX" />
            </div>
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}
            style={{ width: isMobile ? '100%' : 'auto', display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'center' }}>
            <Save size={16} /> {loading ? 'Kaydediliyor...' : 'Değişiklikleri Kaydet'}
          </button>
        </form>
      </div>

      {/* Password Change */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: showPasswordSection ? '16px' : '0' }}>
          <h3 style={{ fontSize: '15px', fontWeight: '700', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Lock size={16} style={{ color: 'var(--primary)' }} /> Şifre Değiştir
          </h3>
          <button type="button" onClick={() => setShowPasswordSection(!showPasswordSection)}
            style={{ background: 'none', border: 'none', color: 'var(--primary)', fontSize: '13px', cursor: 'pointer', fontWeight: '600' }}>
            {showPasswordSection ? 'Kapat' : 'Aç'}
          </button>
        </div>

        {showPasswordSection && (
          <form onSubmit={handlePasswordChange}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '16px' }}>
              <div className="form-group">
                <label>Mevcut Şifre</label>
                <input className="form-control" type="password" value={passwordForm.old_password} onChange={(e) => setPasswordForm({ ...passwordForm, old_password: e.target.value })} required />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '12px' }}>
                <div className="form-group">
                  <label>Yeni Şifre</label>
                  <input className="form-control" type="password" value={passwordForm.new_password} onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })} required minLength={6} />
                </div>
                <div className="form-group">
                  <label>Yeni Şifre (Tekrar)</label>
                  <input className="form-control" type="password" value={passwordForm.confirm_password} onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })} required minLength={6} />
                </div>
              </div>
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading}
              style={{ width: isMobile ? '100%' : 'auto', display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'center' }}>
              <Lock size={16} /> {loading ? 'Değiştiriliyor...' : 'Şifreyi Değiştir'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
