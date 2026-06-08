import React, { useState, useEffect } from 'react';
import { useResponsive } from '../hooks/useResponsive';
import { Layers, QrCode, Globe, Users, MessageSquare, Plus, Trash2, Send, Save, ArrowLeft, RefreshCw, CheckCircle2, Play, MapPin, Lock } from 'lucide-react';

import { apiFetch, API_BASE } from '../lib/apiClient';

const planLevels = {
  'Starter': 1,
  'Growth': 2,
  'Enterprise': 3
};

const hasRequiredPlan = (currentPlan, requiredPlan) => {
  const current = planLevels[currentPlan] || 1;
  const required = planLevels[requiredPlan] || 1;
  return current >= required;
};



export default function Extensions({ setCurrentTab, activeSubView, setActiveSubView, restaurantProfile, fetchRestaurantProfile }) {
  const { isMobile } = useResponsive();
  const handleToggleExtension = async (field, value) => {
    if (!restaurantProfile || !restaurantProfile.id) return;
    try {
      const res = await apiFetch(`${API_BASE}/restaurant-profile/${restaurantProfile.id}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [field]: value })
      });
      if (res.ok) {
        fetchRestaurantProfile();
      }
    } catch (err) {
      console.error(err);
    }
  };

  // CRM State
  const [customers, setCustomers] = useState([]);
  const [loadingCrm, setLoadingCrm] = useState(false);
  const [newCustName, setNewCustName] = useState('');
  const [newCustPhone, setNewCustPhone] = useState('');
  const [newCustEmail, setNewCustEmail] = useState('');

  // WhatsApp Config State
  const [waConfig, setWaConfig] = useState({
    id: null,
    api_key: '',
    phone_number_id: '',
    is_auto_message_enabled: true,
    message_template: '',
    is_live_chat_enabled: false,
    ask_admin_before_sending: true
  });
  const [loadingWa, setLoadingWa] = useState(false);

  // WhatsApp Campaign State
  const [campaignSegment, setCampaignSegment] = useState('all'); // 'all', 'passive'
  const [campaignMessage, setCampaignMessage] = useState('Merhaba {customer_name}, size özel sürpriz indirimler ve yeni lezzetlerimiz KobiPOS kalitesiyle kapınızda! Hızlı sipariş için sitemizi ziyaret edin.');
  const [campaignLogs, setCampaignLogs] = useState([]);
  const [campaignRunning, setCampaignRunning] = useState(false);
  const [campaignProgress, setCampaignProgress] = useState(0);
  const [waSubTab, setWaSubTab] = useState('contacts'); // 'contacts', 'campaign', 'logs'

  useEffect(() => {
    fetchCustomers();
    fetchWhatsAppConfig();
  }, []);

  const fetchCustomers = async () => {
    try {
      setLoadingCrm(true);
      const res = await apiFetch(`${API_BASE}/customers/`);
      const data = await res.json();
      setCustomers(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingCrm(false);
    }
  };

  const fetchWhatsAppConfig = async () => {
    try {
      setLoadingWa(true);
      const res = await apiFetch(`${API_BASE}/whatsapp-configs/`);
      const data = await res.json();
      if (data && data.length > 0) {
        setWaConfig(data[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingWa(false);
    }
  };

  const handleAddCustomer = async (e) => {
    e.preventDefault();
    if (!newCustName || !newCustPhone) return;

    try {
      const res = await apiFetch(`${API_BASE}/customers/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newCustName,
          phone: newCustPhone,
          email: newCustEmail,
          total_orders: 0
        })
      });

      if (res.ok) {
        setNewCustName('');
        setNewCustPhone('');
        setNewCustEmail('');
        fetchCustomers();
        alert('Müşteri başarıyla CRM listesine eklendi.');
      } else {
        const errData = await res.json();
        alert(`Hata: ${errData.phone ? 'Bu telefon numarası zaten kayıtlı.' : 'Kayıt başarısız.'}`);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteCustomer = async (id) => {
    if (!window.confirm('Bu müşteriyi silmek istediğinizden emin misiniz?')) return;
    try {
      const res = await apiFetch(`${API_BASE}/customers/${id}/`, { method: 'DELETE' });
      if (res.ok) {
        fetchCustomers();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleToggleSubscription = async (id, currentStatus) => {
    const newStatus = currentStatus === 'cancelled' ? 'active' : 'cancelled';
    try {
      const res = await apiFetch(`${API_BASE}/customers/${id}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subscription_status: newStatus })
      });
      if (res.ok) {
        fetchCustomers();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleExportCSV = () => {
    if (customers.length === 0) {
      alert('Dışa aktarılacak müşteri kaydı bulunamadı.');
      return;
    }
    const headers = ['İsim', 'Telefon', 'E-posta', 'Sipariş Sayısı', 'Abonelik Durumu'];
    const rows = customers.map(c => [
      c.name,
      c.phone,
      c.email || '',
      c.total_orders || 0,
      c.subscription_status === 'cancelled' ? 'cancelled' : 'active'
    ]);
    
    const csvContent = "data:text/csv;charset=utf-8,\uFEFF" 
      + [headers.join(','), ...rows.map(e => e.map(val => `"${val.toString().replace(/"/g, '""')}"`).join(','))].join('\n');
      
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `bidolu_crm_musteriler_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const parseCSVRow = (line) => {
    const result = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        result.push(current.trim().replace(/^["']|["']$/g, ''));
        current = '';
      } else {
        current += char;
      }
    }
    result.push(current.trim().replace(/^["']|["']$/g, ''));
    return result;
  };

  const handleImportCSV = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (evt) => {
      const text = evt.target.result;
      const lines = text.split(/\r?\n/);
      if (lines.length <= 1) {
        alert('CSV dosyası boş veya başlık satırı eksik.');
        return;
      }

      // Parse headers
      const headers = lines[0].split(',').map(h => h.replace(/^["']|["']$/g, '').trim().toLowerCase());
      
      // Map columns
      const nameIndex = headers.findIndex(h => h.includes('isim') || h.includes('name') || h.includes('ad'));
      const phoneIndex = headers.findIndex(h => h.includes('telefon') || h.includes('phone') || h.includes('tel'));
      const emailIndex = headers.findIndex(h => h.includes('posta') || h.includes('email') || h.includes('mail'));
      const statusIndex = headers.findIndex(h => h.includes('durum') || h.includes('status') || h.includes('abonelik'));

      if (nameIndex === -1 || phoneIndex === -1) {
        alert('CSV dosyasında "İsim" ve "Telefon" sütunları bulunamadı. Lütfen kontrol edin.');
        return;
      }

      const importedCustomers = [];
      for (let i = 1; i < lines.length; i++) {
        if (!lines[i].trim()) continue;
        
        const row = parseCSVRow(lines[i]);
        if (row.length < Math.max(nameIndex, phoneIndex) + 1) continue;

        const name = row[nameIndex];
        const phone = row[phoneIndex];
        const email = emailIndex !== -1 ? row[emailIndex] : '';
        const status = statusIndex !== -1 ? (row[statusIndex].toLowerCase().includes('iptal') || row[statusIndex].toLowerCase().includes('cancel') ? 'cancelled' : 'active') : 'active';

        if (name && phone) {
          importedCustomers.push({ name, phone, email, subscription_status: status });
        }
      }

      if (importedCustomers.length === 0) {
        alert('CSV dosyasında geçerli müşteri kaydı bulunamadı.');
        return;
      }

      if (!confirm(`${importedCustomers.length} adet müşteri CRM rehberine eklenecektir. Onaylıyor musunuz?`)) {
        return;
      }

      let successCount = 0;
      let failCount = 0;

      for (const cust of importedCustomers) {
        try {
          const res = await apiFetch(`${API_BASE}/customers/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: cust.name,
              phone: cust.phone,
              email: cust.email,
              subscription_status: cust.subscription_status,
              total_orders: 0
            })
          });
          if (res.ok) {
            successCount++;
          } else {
            failCount++;
          }
        } catch (err) {
          failCount++;
        }
      }

      fetchCustomers();
      alert(`Toplu yükleme tamamlandı!\nBaşarılı: ${successCount}\nHatalı (Örn: Mükerrer Numara): ${failCount}`);
      e.target.value = '';
    };
    reader.readAsText(file, 'UTF-8');
  };

  const handleSaveWhatsAppConfig = async (e) => {
    e.preventDefault();
    try {
      let res;
      if (waConfig.id) {
        res = await apiFetch(`${API_BASE}/whatsapp-configs/${waConfig.id}/`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(waConfig)
        });
      } else {
        res = await apiFetch(`${API_BASE}/whatsapp-configs/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(waConfig)
        });
      }

      if (res.ok) {
        const data = await res.json();
        setWaConfig(data);
        alert('WhatsApp API ayarları başarıyla kaydedildi.');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleStartCampaign = async () => {
    if (customers.length === 0) {
      alert('Kampanya başlatmak için önce en az bir müşteri bulunmalıdır.');
      return;
    }

    // Filter recipients based on segment
    let recipients = [];
    if (campaignSegment === 'all') {
      recipients = customers;
    } else if (campaignSegment === 'active') {
      recipients = customers.filter(c => c.subscription_status !== 'cancelled');
    } else if (campaignSegment === 'cancelled') {
      recipients = customers.filter(c => c.subscription_status === 'cancelled');
    }

    if (recipients.length === 0) {
      alert('Seçilen segmentte alıcı bulunamadı.');
      return;
    }

    if (waConfig.ask_admin_before_sending !== false) {
      const confirmed = window.confirm(`${recipients.length} müşteriye kampanya bildirimi gönderilecektir. Onaylıyor musunuz?`);
      if (!confirmed) return;
    }

    setCampaignRunning(true);
    setCampaignProgress(0);
    setCampaignLogs([]);
    setWaSubTab('logs');

    try {
      const res = await apiFetch(`${API_BASE}/whatsapp-configs/send_campaign/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: campaignMessage,
          recipients: recipients
        })
      });

      if (res.ok) {
        const data = await res.json();
        // Simulate progress bar and feed logging
        let count = 0;
        const interval = setInterval(() => {
          count++;
          setCampaignProgress(Math.floor((count / data.logs.length) * 100));
          setCampaignLogs(data.logs.slice(0, count));

          if (count >= data.logs.length) {
            clearInterval(interval);
            setCampaignRunning(false);
            alert('WhatsApp Kampanyası başarıyla tamamlandı!');
          }
        }, 1200);
      } else {
        const errData = await res.json();
        alert(errData.error || 'Kampanya başlatılamadı.');
        setCampaignRunning(false);
      }
    } catch (err) {
      console.error(err);
      setCampaignRunning(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {activeSubView === null ? (
        <>
          {/* Main Extensions Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px' }}>
            
            {/* QR Menu Card */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '240px', background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(0,0,0,0) 100%)', border: '1px solid var(--panel-border)' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <div style={{ background: 'rgba(99, 102, 241, 0.1)', color: '#6366f1', width: '40px', height: '40px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <QrCode size={22} />
                  </div>
                  {hasRequiredPlan(restaurantProfile.active_plan, 'Growth') ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontSize: '11px', color: restaurantProfile.ext_qr_menu_enabled ? 'var(--success)' : 'var(--text-muted)' }}>
                        {restaurantProfile.ext_qr_menu_enabled ? 'Açık' : 'Kapalı'}
                      </span>
                      <input 
                        type="checkbox"
                        checked={restaurantProfile.ext_qr_menu_enabled}
                        onChange={(e) => handleToggleExtension('ext_qr_menu_enabled', e.target.checked)}
                        style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                      />
                    </div>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', padding: '4px 8px', borderRadius: '6px', fontSize: '10px', fontWeight: '700' }}>
                      <Lock size={12} /> Büyüyen Plan
                    </div>
                  )}
                </div>
                <h4 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '6px' }}>QR Menü</h4>
                <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', lineHeight: '1.5' }}>Masalardan veya adresten QR kod okutarak sipariş alın, menü temalarını yönetin.</p>
              </div>
              {hasRequiredPlan(restaurantProfile.active_plan, 'Growth') ? (
                <button 
                  onClick={() => setCurrentTab('qr-menu')} 
                  disabled={!restaurantProfile.ext_qr_menu_enabled}
                  className="btn btn-secondary" 
                  style={{ width: '100%', padding: '8px', opacity: restaurantProfile.ext_qr_menu_enabled ? 1 : 0.5 }}
                >
                  {restaurantProfile.ext_qr_menu_enabled ? 'Yönetime Git' : 'Aktif Etmek İçin Açın'}
                </button>
              ) : (
                <button 
                  onClick={() => {
                    localStorage.setItem('settingsSubTab', 'plans');
                    setCurrentTab('settings');
                  }}
                  className="btn btn-primary" 
                  style={{ width: '100%', padding: '8px', display: 'flex', gap: '6px', justifyContent: 'center', alignItems: 'center' }}
                >
                  Planı Yükselt
                </button>
              )}
            </div>

            {/* Official Website Card */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '240px', background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(0,0,0,0) 100%)', border: '1px solid var(--panel-border)' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <div style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', width: '40px', height: '40px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Globe size={22} />
                  </div>
                  {hasRequiredPlan(restaurantProfile.active_plan, 'Growth') ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontSize: '11px', color: restaurantProfile.ext_official_website_enabled ? 'var(--success)' : 'var(--text-muted)' }}>
                        {restaurantProfile.ext_official_website_enabled ? 'Açık' : 'Kapalı'}
                      </span>
                      <input 
                        type="checkbox"
                        checked={restaurantProfile.ext_official_website_enabled}
                        onChange={(e) => handleToggleExtension('ext_official_website_enabled', e.target.checked)}
                        style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                      />
                    </div>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', padding: '4px 8px', borderRadius: '6px', fontSize: '10px', fontWeight: '700' }}>
                      <Lock size={12} /> Büyüyen Plan
                    </div>
                  )}
                </div>
                <h4 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '6px' }}>Tanıtım Web Sitesi</h4>
                <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', lineHeight: '1.5' }}>Kendi özel alan adınız, tasarımlarınız, rezervasyon formu ve hikayenizle web sitenizi oluşturun.</p>
              </div>
              {hasRequiredPlan(restaurantProfile.active_plan, 'Growth') ? (
                <button 
                  onClick={() => setCurrentTab('official-website')} 
                  disabled={!restaurantProfile.ext_official_website_enabled}
                  className="btn btn-secondary" 
                  style={{ width: '100%', padding: '8px', opacity: restaurantProfile.ext_official_website_enabled ? 1 : 0.5 }}
                >
                  {restaurantProfile.ext_official_website_enabled ? 'Yönetime Git' : 'Aktif Etmek İçin Açın'}
                </button>
              ) : (
                <button 
                  onClick={() => {
                    localStorage.setItem('settingsSubTab', 'plans');
                    setCurrentTab('settings');
                  }}
                  className="btn btn-primary" 
                  style={{ width: '100%', padding: '8px', display: 'flex', gap: '6px', justifyContent: 'center', alignItems: 'center' }}
                >
                  Planı Yükselt
                </button>
              )}
            </div>

            {/* WhatsApp API Card */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '240px', background: 'linear-gradient(135deg, rgba(37, 211, 102, 0.05) 0%, rgba(0,0,0,0) 100%)', border: '1px solid var(--panel-border)' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <div style={{ background: 'rgba(37, 211, 102, 0.1)', color: '#25d366', width: '40px', height: '40px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <MessageSquare size={22} />
                  </div>
                  {hasRequiredPlan(restaurantProfile.active_plan, 'Enterprise') ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontSize: '11px', color: restaurantProfile.ext_whatsapp_enabled ? 'var(--success)' : 'var(--text-muted)' }}>
                        {restaurantProfile.ext_whatsapp_enabled ? 'Açık' : 'Kapalı'}
                      </span>
                      <input 
                        type="checkbox"
                        checked={restaurantProfile.ext_whatsapp_enabled}
                        onChange={(e) => handleToggleExtension('ext_whatsapp_enabled', e.target.checked)}
                        style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                      />
                    </div>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', padding: '4px 8px', borderRadius: '6px', fontSize: '10px', fontWeight: '700' }}>
                      <Lock size={12} /> Kurumsal Plan
                    </div>
                  )}
                </div>
                <h4 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '6px' }}>WhatsApp Kampanyaları</h4>
                <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', lineHeight: '1.5' }}>Müşteri gruplarına ve abonelere özel WhatsApp mesaj şablonları ile toplu kampanya bildirimleri gönderin.</p>
              </div>
              {hasRequiredPlan(restaurantProfile.active_plan, 'Enterprise') ? (
                <button 
                  onClick={() => setActiveSubView('whatsapp')} 
                  disabled={!restaurantProfile.ext_whatsapp_enabled}
                  className="btn btn-primary" 
                  style={{ width: '100%', padding: '8px', background: restaurantProfile.ext_whatsapp_enabled ? '#25d366' : 'var(--bg-darker)', borderColor: restaurantProfile.ext_whatsapp_enabled ? '#25d366' : 'var(--panel-border)', opacity: restaurantProfile.ext_whatsapp_enabled ? 1 : 0.5 }}
                >
                  {restaurantProfile.ext_whatsapp_enabled ? 'WhatsApp Kampanyalarını Yönet' : 'Aktif Etmek İçin Açın'}
                </button>
              ) : (
                <button 
                  onClick={() => {
                    localStorage.setItem('settingsSubTab', 'plans');
                    setCurrentTab('settings');
                  }}
                  className="btn btn-primary" 
                  style={{ width: '100%', padding: '8px', display: 'flex', gap: '6px', justifyContent: 'center', alignItems: 'center' }}
                >
                  Planı Yükselt
                </button>
              )}
            </div>

            {/* Live Courier Tracking Card */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '240px', background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.05) 0%, rgba(0,0,0,0) 100%)', border: '1px solid var(--panel-border)' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <div style={{ background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b', width: '40px', height: '40px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <MapPin size={22} />
                  </div>
                  {hasRequiredPlan(restaurantProfile.active_plan, 'Enterprise') ? (
                    <span style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', padding: '4px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: '700', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
                      YAKINDA
                    </span>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', padding: '4px 8px', borderRadius: '6px', fontSize: '10px', fontWeight: '700' }}>
                      <Lock size={12} /> Kurumsal Plan
                    </div>
                  )}
                </div>
                <h4 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '6px' }}>Live Kurye Lokasyon Takibi</h4>
                <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', lineHeight: '1.5' }}>Teslimattaki kuryelerin canlı konumlarını, sipariş rotalarını ve durumlarını anlık haritadan izleyin.</p>
              </div>
              {hasRequiredPlan(restaurantProfile.active_plan, 'Enterprise') ? (
                <button 
                  disabled={true}
                  className="btn btn-secondary" 
                  style={{ width: '100%', padding: '8px', cursor: 'not-allowed', opacity: 0.6 }}
                >
                  Yakında Hizmete Girecektir
                </button>
              ) : (
                <button 
                  onClick={() => {
                    localStorage.setItem('settingsSubTab', 'plans');
                    setCurrentTab('settings');
                  }}
                  className="btn btn-primary" 
                  style={{ width: '100%', padding: '8px', display: 'flex', gap: '6px', justifyContent: 'center', alignItems: 'center' }}
                >
                  Planı Yükselt
                </button>
              )}
            </div>

          </div>
        </>
      ) : activeSubView === 'crm' ? (
        <>
          {/* Customer CRM Manager View */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <button onClick={() => setActiveSubView(null)} className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', fontSize: '12px' }}>
              <ArrowLeft size={14} /> Eklentilere Dön
            </button>
            <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>/ Müşteri CRM</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '2fr 1fr', gap: isMobile ? '16px' : '24px' }}>
            {/* Customer CRM List */}
            <div className="card">
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Müşteri Rehberi ({customers.length})</span>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <button onClick={handleExportCSV} className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                    📥 Dışa Aktar (CSV)
                  </button>
                  <label className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', margin: 0 }}>
                    📤 İçe Aktar (CSV)
                    <input type="file" accept=".csv" onChange={handleImportCSV} style={{ display: 'none' }} />
                  </label>
                  <button onClick={fetchCustomers} className="action-icon-btn"><RefreshCw size={14} /></button>
                </div>
              </h3>

              {loadingCrm ? (
                <div className="spinner"></div>
              ) : customers.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>Müşteri kaydı bulunamadı.</div>
              ) : (
                <div className="table-container">
                  <table className="mgmt-table">
                    <thead>
                      <tr>
                        <th>Müşteri Adı</th>
                        <th>Telefon</th>
                        <th>E-posta</th>
                        <th style={{ textAlign: 'center' }}>Sipariş Sayısı</th>
                        <th>Son Sipariş Tarihi</th>
                        <th>İşlem</th>
                      </tr>
                    </thead>
                    <tbody>
                      {customers.map(c => (
                        <tr key={c.id}>
                          <td style={{ fontWeight: '600' }}>{c.name}</td>
                          <td>{c.phone}</td>
                          <td style={{ color: 'var(--text-muted)' }}>{c.email || '-'}</td>
                          <td style={{ textAlign: 'center', fontWeight: '700' }}>{c.total_orders}</td>
                          <td style={{ color: 'var(--text-muted)' }}>{c.last_order_date || 'Hiç Sipariş Yok'}</td>
                          <td>
                            <button onClick={() => handleDeleteCustomer(c.id)} className="action-icon-btn delete"><Trash2 size={15} /></button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Customer Add Form */}
            <div className="card" style={{ height: 'fit-content' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>Yeni Müşteri Ekle</h3>
              <form onSubmit={handleAddCustomer} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div className="form-group">
                  <label>Müşteri Ad Soyad *</label>
                  <input type="text" className="form-control" placeholder="örn: Canan Dağdeviren" value={newCustName} onChange={(e) => setNewCustName(e.target.value)} required />
                </div>
                <div className="form-group">
                  <label>Telefon Numarası *</label>
                  <input type="text" className="form-control" placeholder="örn: 0555 444 33 22" value={newCustPhone} onChange={(e) => setNewCustPhone(e.target.value)} required />
                </div>
                <div className="form-group">
                  <label>E-posta Adresi</label>
                  <input type="email" className="form-control" placeholder="örn: canan@mail.com" value={newCustEmail} onChange={(e) => setNewCustEmail(e.target.value)} />
                </div>
                <button type="submit" className="btn btn-primary" style={{ width: '100%', display: 'flex', gap: '8px', justifyContent: 'center', alignItems: 'center' }}>
                  <Plus size={16} /> Müşteriyi CRM'e Kaydet
                </button>
              </form>
            </div>
          </div>
        </>
      ) : (
        <>
          {/* WhatsApp API View */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <button onClick={() => setActiveSubView(null)} className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', fontSize: '12px' }}>
              <ArrowLeft size={14} /> Eklentilere Dön
            </button>
            <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>/ WhatsApp Kampanyaları</span>
          </div>

          {/* Subtab Navigation inside WhatsApp View */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', marginBottom: '24px', borderBottom: '1px solid var(--panel-border)', paddingBottom: '12px' }}>
            <button 
              onClick={() => setWaSubTab('contacts')} 
              className={`btn ${waSubTab === 'contacts' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '8px 16px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
            >
              <Users size={16} /> Abonelik & Kişiler
            </button>
            <button 
              onClick={() => setWaSubTab('campaign')} 
              className={`btn ${waSubTab === 'campaign' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '8px 16px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
            >
              <Send size={16} /> Kampanya Gönderimi
            </button>
            <button 
              onClick={() => setWaSubTab('logs')} 
              className={`btn ${waSubTab === 'logs' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '8px 16px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
            >
              <RefreshCw size={16} /> Gönderim Kayıtları {(campaignRunning || campaignLogs.length > 0) && `(${campaignLogs.length})`}
            </button>
          </div>

          {/* Tab 1: Contacts & Subscription Management */}
          {waSubTab === 'contacts' && (
            <div>
              {/* Summary Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '20px' }}>
                <div className="card" style={{ padding: '16px', background: 'rgba(37, 211, 102, 0.05)', border: '1px solid rgba(37, 211, 102, 0.15)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Devam Eden Abonelikler</span>
                  <strong style={{ fontSize: '24px', color: '#25d366' }}>
                    {customers.filter(c => c.subscription_status !== 'cancelled').length}
                  </strong>
                </div>
                <div className="card" style={{ padding: '16px', background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.15)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>İptal Olan Abonelikler</span>
                  <strong style={{ fontSize: '24px', color: '#ef4444' }}>
                    {customers.filter(c => c.subscription_status === 'cancelled').length}
                  </strong>
                </div>
              </div>

              {/* CRM Table */}
              <div className="card">
                <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Kişiler ve Abonelik Durumları ({customers.length})</span>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <button onClick={handleExportCSV} className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                      📥 Dışa Aktar
                    </button>
                    <label className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer', margin: 0 }}>
                      📤 İçe Aktar
                      <input type="file" accept=".csv" onChange={handleImportCSV} style={{ display: 'none' }} />
                    </label>
                    <button onClick={fetchCustomers} className="action-icon-btn"><RefreshCw size={14} /></button>
                  </div>
                </h3>

                {loadingCrm ? (
                  <div className="spinner"></div>
                ) : customers.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>CRM rehberinde henüz kayıtlı müşteri yok.</div>
                ) : (
                  <div className="table-container">
                    <table className="mgmt-table">
                      <thead>
                        <tr>
                          <th>Müşteri Adı</th>
                          <th>Telefon</th>
                          <th style={{ textAlign: 'center' }}>Sipariş Sayısı</th>
                          <th>Abonelik Durumu</th>
                          <th style={{ textAlign: 'right' }}>İşlemler</th>
                        </tr>
                      </thead>
                      <tbody>
                        {customers.map(c => {
                          const isActive = c.subscription_status !== 'cancelled';
                          return (
                            <tr key={c.id}>
                              <td style={{ fontWeight: '600' }}>{c.name}</td>
                              <td>{c.phone}</td>
                              <td style={{ textAlign: 'center', fontWeight: '700' }}>{c.total_orders}</td>
                              <td>
                                <span 
                                  className={`badge ${isActive ? 'badge-success' : 'badge-danger'}`}
                                  style={{ 
                                    background: isActive ? 'rgba(37, 211, 102, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                                    color: isActive ? '#25d366' : '#ef4444',
                                    border: `1px solid ${isActive ? 'rgba(37, 211, 102, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`,
                                    padding: '4px 8px',
                                    borderRadius: '4px',
                                    fontSize: '11px',
                                    fontWeight: '600'
                                  }}
                                >
                                  {isActive ? 'Devam Ediyor' : 'İptal Edildi'}
                                </span>
                              </td>
                              <td style={{ textAlign: 'right' }}>
                                <button 
                                  onClick={() => handleToggleSubscription(c.id, c.subscription_status)}
                                  className="btn"
                                  style={{ 
                                    padding: '4px 10px', 
                                    fontSize: '11px', 
                                    background: isActive ? 'rgba(239, 68, 68, 0.1)' : 'rgba(37, 211, 102, 0.1)',
                                    border: `1px solid ${isActive ? 'rgba(239, 68, 68, 0.2)' : 'rgba(37, 211, 102, 0.2)'}`,
                                    color: isActive ? '#ef4444' : '#25d366',
                                    cursor: 'pointer',
                                    borderRadius: '4px'
                                  }}
                                >
                                  {isActive ? 'Aboneliği İptal Et' : 'Aboneliği Başlat'}
                                </button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Tab 2: Campaign Send Planner */}
          {waSubTab === 'campaign' && (
            <div className="card" style={{ maxWidth: isMobile ? '100%' : '600px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Send size={18} /> Yeni WhatsApp Kampanyası Oluştur
              </h3>
              
              <div className="form-group" style={{ marginBottom: '16px' }}>
                <label>Hedef Müşteri Segmenti</label>
                <select 
                  className="form-control form-select" 
                  value={campaignSegment} 
                  onChange={(e) => setCampaignSegment(e.target.value)}
                >
                  <option value="all">Tüm CRM Müşterileri ({customers.length})</option>
                  <option value="active">Devam Eden Aboneler (Aktif) ({customers.filter(c => c.subscription_status !== 'cancelled').length})</option>
                  <option value="cancelled">Aboneliği İptal Olanlar ({customers.filter(c => c.subscription_status === 'cancelled').length})</option>
                </select>
              </div>

              <div className="form-group" style={{ marginBottom: '20px' }}>
                <label>Kampanya Mesajı İçeriği</label>
                <textarea 
                  className="form-control" 
                  rows="5" 
                  value={campaignMessage} 
                  onChange={(e) => setCampaignMessage(e.target.value)}
                  placeholder="Müşterilere gidecek kampanya yazısı..."
                />
                <small style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginTop: '6px' }}>
                  İpucu: Kişiselleştirmek için <strong>{'{customer_name}'}</strong> etiketini kullanabilirsiniz.
                </small>
              </div>

              <button 
                className="btn btn-primary" 
                disabled={campaignRunning} 
                onClick={handleStartCampaign}
                style={{ width: '100%', display: 'flex', gap: '8px', justifyContent: 'center', alignItems: 'center', background: '#0284c7', borderColor: '#0284c7' }}
              >
                <Play size={16} /> {campaignRunning ? 'Kampanya Gönderiliyor...' : 'Kampanyayı Başlat (WhatsApp API)'}
              </button>
            </div>
          )}

          {/* Tab 3: Delivery Logs & Report */}
          {waSubTab === 'logs' && (
            <div className="card">
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>Kampanya Gönderim Raporları & Kayıtları</h3>
              
              {campaignRunning && (
                <div style={{ marginBottom: '24px', padding: '16px', background: 'rgba(0,0,0,0.02)', borderRadius: '12px', border: '1px solid var(--panel-border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '8px' }}>
                    <span>Gönderim İlerlemesi</span>
                    <strong>%{campaignProgress}</strong>
                  </div>
                  <div style={{ height: '8px', background: 'rgba(0,0,0,0.06)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${campaignProgress}%`, height: '100%', background: '#25d366', transition: 'width 0.3s ease' }}></div>
                  </div>
                </div>
              )}

              {campaignLogs.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  Henüz tamamlanmış veya aktif bir kampanya gönderim kaydı bulunamadı.
                </div>
              ) : (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Toplam {campaignLogs.length} Gönderim Kaydı</span>
                    {!campaignRunning && (
                      <button onClick={() => setCampaignLogs([])} className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '11px', cursor: 'pointer' }}>
                        Kayıtları Temizle
                      </button>
                    )}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '400px', overflowY: 'auto' }}>
                    {campaignLogs.map(log => (
                      <div 
                        key={log.id} 
                        style={{ 
                          padding: '12px', 
                          borderRadius: '8px', 
                          border: '1px solid var(--panel-border)', 
                          background: 'rgba(0,0,0,0.01)',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}
                      >
                        <div>
                          <strong style={{ fontSize: '13px', display: 'block' }}>{log.customer}</strong>
                          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{log.phone} ➜ "{log.message_preview}"</span>
                        </div>
                        <span style={{ fontSize: '11px', color: '#25d366', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '4px', shrink: 0 }}>
                          <CheckCircle2 size={13} /> {log.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

    </div>
  );
}
