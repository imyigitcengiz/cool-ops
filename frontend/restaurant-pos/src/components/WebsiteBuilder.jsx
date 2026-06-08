import React, { useState, useEffect } from 'react';
import { Globe, Copy, Check, Download, ToggleLeft, ToggleRight } from 'lucide-react';
import { useResponsive } from '../hooks/useResponsive';

import { apiFetch, API_BASE } from '../lib/apiClient';

export default function WebsiteBuilder() {
  const { isMobile } = useResponsive();
  const [profileId, setProfileId] = useState(null);
  const [slug, setSlug] = useState('bidolu-restoran');
  const [themeColor, setThemeColor] = useState('#6366f1');
  const [bannerText, setBannerText] = useState('Hoş Geldiniz!');
  const [enableTable, setEnableTable] = useState(true);
  const [enableDelivery, setEnableDelivery] = useState(true);
  const [enableTakeaway, setEnableTakeaway] = useState(true);
  
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const res = await apiFetch(`${API_BASE}/restaurant-profile/`);
      const data = await res.json();
      if (data && data.length > 0) {
        const prof = data[0];
        setProfileId(prof.id);
        setSlug(prof.website_slug || 'bidolu-restoran');
        setThemeColor(prof.website_theme_color || '#6366f1');
        setBannerText(prof.website_banner_text || 'Hoş Geldiniz!');
        setEnableTable(prof.website_enable_table_orders !== false);
        setEnableDelivery(prof.website_enable_delivery !== false);
        setEnableTakeaway(prof.website_enable_takeaway !== false);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    const payload = {
      website_slug: slug,
      website_theme_color: themeColor,
      website_banner_text: bannerText,
      website_enable_table_orders: enableTable,
      website_enable_delivery: enableDelivery,
      website_enable_takeaway: enableTakeaway
    };

    try {
      if (profileId) {
        const res = await apiFetch(`${API_BASE}/restaurant-profile/${profileId}/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          alert('Websitesi ayarlarınız başarıyla kaydedildi!');
          fetchProfile();
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCopyLink = () => {
    const link = `https://bidolupos.com/m/${slug}`;
    navigator.clipboard.writeText(link);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1.2fr 1fr', gap: isMobile ? '16px' : '24px' }}>
      
      {/* Settings Form Card */}
      <div className="card">
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Globe size={20} /> Web Sipariş & QR Menü Ayarları
        </h3>

        {loading ? (
          <div className="spinner"></div>
        ) : (
          <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            
            {/* Slug URL */}
            <div className="form-group">
              <label>Websitesi Linki (Adres / Slug)</label>
              <div style={{ display: 'flex', gap: '8px' }}>
                <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--panel-border)', borderRadius: '10px', display: 'flex', alignItems: 'center', padding: '0 12px', color: 'var(--text-muted)', fontSize: '13px' }}>
                  bidolupos.com/m/
                </div>
                <input 
                  type="text" 
                  className="form-control" 
                  value={slug} 
                  onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''))}
                  placeholder="restoran-adi" 
                  required 
                  style={{ flex: 1 }}
                />
                <button type="button" className="btn btn-secondary" onClick={handleCopyLink} style={{ padding: '10px 14px' }}>
                  {copied ? <Check size={16} style={{ color: 'var(--success)' }} /> : <Copy size={16} />}
                </button>
              </div>
            </div>

            {/* Banner message */}
            <div className="form-group">
              <label>Müşteri Karşılama Mesajı (Banner)</label>
              <input 
                type="text" 
                className="form-control" 
                value={bannerText} 
                onChange={(e) => setBannerText(e.target.value)} 
                placeholder="örn: En Leziz Kebaplar Bidolu'da!" 
              />
            </div>

            {/* Color picker */}
            <div className="form-group">
              <label>Sitenizin Ana Renk Teması</label>
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <input 
                  type="color" 
                  value={themeColor} 
                  onChange={(e) => setThemeColor(e.target.value)}
                  style={{ border: 'none', background: 'transparent', width: '50px', height: '40px', cursor: 'pointer' }}
                />
                <input 
                  type="text" 
                  className="form-control" 
                  value={themeColor} 
                  onChange={(e) => setThemeColor(e.target.value)}
                  style={{ maxWidth: '120px' }}
                />
              </div>
            </div>

            <hr style={{ borderColor: 'var(--panel-border)', margin: '8px 0' }} />

            {/* Order methods toggles */}
            <div>
              <label style={{ fontSize: '13px', color: 'var(--text-muted)', display: 'block', marginBottom: '12px' }}>Aktif Sipariş Yöntemleri</label>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '10px', border: '1px solid var(--panel-border)' }}>
                  <div>
                    <strong style={{ fontSize: '14px', display: 'block' }}>Masadan QR Sipariş</strong>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Müşteriler masadaki QR kodu okutarak sipariş verebilir.</span>
                  </div>
                  <button type="button" onClick={() => setEnableTable(!enableTable)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: enableTable ? 'var(--primary)' : 'var(--text-muted)' }}>
                    {enableTable ? <ToggleRight size={36} /> : <ToggleLeft size={36} />}
                  </button>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '10px', border: '1px solid var(--panel-border)' }}>
                  <div>
                    <strong style={{ fontSize: '14px', display: 'block' }}>Adrese Paket Siparişi</strong>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Müşteriler sitenizden adreslerine teslimat siparişi oluşturabilir.</span>
                  </div>
                  <button type="button" onClick={() => setEnableDelivery(!enableDelivery)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: enableDelivery ? 'var(--primary)' : 'var(--text-muted)' }}>
                    {enableDelivery ? <ToggleRight size={36} /> : <ToggleLeft size={36} />}
                  </button>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '10px', border: '1px solid var(--panel-border)' }}>
                  <div>
                    <strong style={{ fontSize: '14px', display: 'block' }}>Gel-Al Sipariş</strong>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Müşteriler gelip almak üzere ön sipariş oluşturabilir.</span>
                  </div>
                  <button type="button" onClick={() => setEnableTakeaway(!enableTakeaway)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: enableTakeaway ? 'var(--primary)' : 'var(--text-muted)' }}>
                    {enableTakeaway ? <ToggleRight size={36} /> : <ToggleLeft size={36} />}
                  </button>
                </div>
              </div>
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '8px' }}>
              Değişiklikleri Canlıya Al
            </button>

          </form>
        )}
      </div>

      {/* QR Code and Live Mobile Mockup */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        {/* QR Code Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '16px' }}>
          <h4 style={{ fontSize: '15px', fontWeight: '700', alignSelf: 'flex-start' }}>Masalar İçin QR Kodu</h4>
          
          <div style={{ background: 'white', padding: '16px', borderRadius: '12px', display: 'inline-block' }}>
            <svg viewBox="0 0 100 100" style={{ width: '130px', height: '130px' }}>
              {/* Outer borders */}
              <rect x="10" y="10" width="25" height="25" fill="black" />
              <rect x="15" y="15" width="15" height="15" fill="white" />
              <rect x="18" y="18" width="9" height="9" fill="black" />

              <rect x="65" y="10" width="25" height="25" fill="black" />
              <rect x="70" y="15" width="15" height="15" fill="white" />
              <rect x="73" y="18" width="9" height="9" fill="black" />

              <rect x="10" y="65" width="25" height="25" fill="black" />
              <rect x="15" y="70" width="15" height="15" fill="white" />
              <rect x="18" y="73" width="9" height="9" fill="black" />

              {/* Dotted fillers for mock QR code */}
              <rect x="42" y="12" width="6" height="6" fill="black" />
              <rect x="52" y="18" width="6" height="6" fill="black" />
              <rect x="45" y="30" width="8" height="6" fill="black" />

              <rect x="12" y="45" width="6" height="8" fill="black" />
              <rect x="25" y="42" width="6" height="6" fill="black" />
              
              <rect x="45" y="45" width="12" height="12" fill="black" />
              <rect x="70" y="45" width="6" height="8" fill="black" />
              <rect x="80" y="52" width="8" height="6" fill="black" />

              <rect x="42" y="70" width="6" height="6" fill="black" />
              <rect x="52" y="78" width="8" height="6" fill="black" />
              <rect x="75" y="70" width="12" height="12" fill="black" />
            </svg>
          </div>

          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Müşteriler bu kodu okutarak restoranınızın online menüsüne ulaşır.</p>
          <button className="btn btn-secondary" style={{ width: '100%', display: 'flex', gap: '8px', justifyContent: 'center', alignItems: 'center' }}>
            <Download size={16} /> QR Kodu İndir
          </button>
        </div>

        {/* Live Mobile Mockup */}
        <div className="card" style={{ padding: '0', overflow: 'hidden', border: '1px solid var(--panel-border)', borderRadius: '24px', position: 'relative' }}>
          <div style={{ background: 'var(--bg-darker)', padding: '12px', textAlign: 'center', borderBottom: '1px solid var(--panel-border)', fontSize: '11px', color: 'var(--text-muted)' }}>
            📱 Canlı Menü Önizlemesi
          </div>
          
          <div style={{ padding: '20px', minHeight: '300px', display: 'flex', flexDirection: 'column', gap: '16px', background: '#0c0d12' }}>
            {/* Header banner */}
            <div style={{ background: themeColor, color: 'white', padding: '16px', borderRadius: '12px', textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '4px', boxShadow: `0 8px 24px ${themeColor}20` }}>
              <span style={{ fontSize: '16px', fontWeight: '800' }}>Bidolu Kebap</span>
              <span style={{ fontSize: '11px', opacity: 0.9 }}>{bannerText}</span>
            </div>

            {/* Methods options list */}
            <div style={{ display: 'flex', gap: '6px' }}>
              {enableTable && (
                <div style={{ flex: 1, padding: '6px', fontSize: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--panel-border)', borderRadius: '6px', textAlign: 'center', color: 'white' }}>
                  🛎️ Masadan Sipariş
                </div>
              )}
              {enableDelivery && (
                <div style={{ flex: 1, padding: '6px', fontSize: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--panel-border)', borderRadius: '6px', textAlign: 'center', color: 'white' }}>
                  🛵 Paket Servis
                </div>
              )}
              {enableTakeaway && (
                <div style={{ flex: 1, padding: '6px', fontSize: '10px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--panel-border)', borderRadius: '6px', textAlign: 'center', color: 'white' }}>
                  🛍️ Gel-Al
                </div>
              )}
            </div>

            {/* Mock menu items */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.02)' }}>
                <div>
                  <div style={{ fontSize: '12px', fontWeight: '600' }}>Adana Kebap</div>
                  <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>Lavaş ve garnitür ile</div>
                </div>
                <button style={{ border: 'none', background: themeColor, color: 'white', padding: '4px 10px', fontSize: '11px', borderRadius: '6px', fontWeight: '700' }}>
                  280 ₺
                </button>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.02)' }}>
                <div>
                  <div style={{ fontSize: '12px', fontWeight: '600' }}>Künefe</div>
                  <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>Antep fıstığı ile</div>
                </div>
                <button style={{ border: 'none', background: themeColor, color: 'white', padding: '4px 10px', fontSize: '11px', borderRadius: '6px', fontWeight: '700' }}>
                  150 ₺
                </button>
              </div>
            </div>

          </div>
        </div>

      </div>

    </div>
  );
}
