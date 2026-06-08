import React from 'react';
import { Shield, Cloud, Zap, Check, ChevronRight, Layers, CreditCard, Award, ArrowRight, X } from 'lucide-react';

export default function LandingPage({ onLaunchApp }) {
  return (
    <div className="landing-container">
      {/* Navigation Header */}
      <header className="landing-header">
        <div className="landing-logo">
          <div className="logo-icon">B</div>
          <span className="logo-text">Bidolu POS</span>
        </div>
        <nav className="landing-nav">
          <a href="#features">Özellikler</a>
          <a href="#pricing">Fiyatlandırma</a>
          <a href="#testimonials">Referanslar</a>
        </nav>
        <div>
          <button onClick={onLaunchApp} className="btn btn-primary" style={{ padding: '10px 20px', fontSize: '13px' }}>
            Yönetim Paneli <ArrowRight size={14} style={{ marginLeft: '4px' }} />
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <span className="hero-badge">🚀 Yeni Nesil Restoran SaaS Çözümü</span>
          <h1 className="hero-title">
            Restoranınızı Buluttan Yönetin, <br />
            <span>Hızla Büyütün.</span>
          </h1>
          <p className="hero-subtitle">
            Bidolu POS ile masa siparişleri, mutfak akışı, hızlı ödemeler ve detaylı ciro analizleri tek platformda. Yeni başlayan ve büyüyen restoranlar için optimize edilmiş en esnek SaaS altyapısı.
          </p>
          <div className="hero-buttons">
            <button onClick={onLaunchApp} className="btn btn-primary" style={{ padding: '16px 28px', fontSize: '15px' }}>
              Hemen Ücretsiz Deneyin <ChevronRight size={16} />
            </button>
            <a href="#features" className="btn btn-secondary" style={{ padding: '16px 28px', fontSize: '15px' }}>
              Özellikleri Keşfet
            </a>
          </div>
        </div>
        
        {/* Visual Mockup Dashboard preview */}
        <div className="hero-mockup-wrapper">
          <div className="hero-mockup-frame">
            <div className="mockup-header">
              <span className="mockup-dot red"></span>
              <span className="mockup-dot yellow"></span>
              <span className="mockup-dot green"></span>
              <span className="mockup-title">Bidolu POS - Yönetim Paneli</span>
            </div>
            <div className="mockup-body">
              <div className="mockup-sidebar"></div>
              <div className="mockup-content">
                <div className="mockup-widgets">
                  <div className="mockup-widget"></div>
                  <div className="mockup-widget"></div>
                  <div className="mockup-widget"></div>
                </div>
                <div className="mockup-chart"></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features-section">
        <div className="section-header">
          <h2>Akıllı Özellikler ile İşinizi Kolaylaştırın</h2>
          <p>Manuel süreçleri geride bırakın, otomasyon ile zamandan ve maliyetten tasarruf edin.</p>
        </div>

        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon"><Cloud size={24} /></div>
            <h3>Bulut Tabanlı Altyapı</h3>
            <p>Sunucu kurulum derdi yok. Tüm verileriniz bulutta güvende, restoranınızı istediğiniz yerden, mobilden veya tabletten yönetin.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon"><Zap size={24} /></div>
            <h3>Masa & Sipariş Yönetimi</h3>
            <p>Masalarınızın durumunu renkli durum göstergeleriyle anlık izleyin. Garsonlar saniyeler içinde sipariş girsin.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon"><Layers size={24} /></div>
            <h3>Mutfak Ekranı (KDS)</h3>
            <p>Kağıt biletleri unutun. Siparişler mutfak ekranına anında düşer, hazırlık süreleri otomatik ölçülür ve takip edilir.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon"><CreditCard size={24} /></div>
            <h3>Hızlı Ödeme & Hesap Kapatma</h3>
            <p>Nakit ve kredi kartı ödemelerini saniyeler içinde alın, masaları hızlıca kapatın. Parçalı ödeme altyapısına hazır.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon"><Shield size={24} /></div>
            <h3>Kolay Menü Yönetimi</h3>
            <p>Yeni ürünler ekleyin, fiyatları güncelleyin, kategoriler tasarlayın. Menü değişiklikleriniz anında tüm cihazlarda aktif olur.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon"><Award size={24} /></div>
            <h3>Gelişmiş Raporlama</h3>
            <p>Bugünün cirosu, haftalık satış grafikleri, en çok satan ürünler. İşletmenizin durumunu gösteren grafikler tek ekranda.</p>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="pricing-section">
        <div className="section-header">
          <h2>Restoranınızla Birlikte Büyüyen Esnek Fiyatlandırma</h2>
          <p>Gizli ücretler yok, kurulum ücreti yok. İhtiyacınıza uygun paketi seçin.</p>
        </div>

        <div className="pricing-grid">
          {/* Plan 1 */}
          <div className="price-card">
            <div className="plan-name">Başlangıç (Starter)</div>
            <div className="plan-price">499 ₺ <span>/ Ay</span></div>
            <p className="plan-desc">Yeni açılan, küçük ölçekli kafe ve büfeler için ideal temel paket.</p>
            <ul className="plan-features">
              <li><Check size={16} /> 10 Masaya Kadar Destek</li>
              <li><Check size={16} /> Temel Sipariş ve Masa Takibi</li>
              <li><Check size={16} /> 1 Mutfak Ekranı</li>
              <li><Check size={16} /> Günlük Satış Raporu</li>
              <li className="disabled"><X size={16} /> Detaylı Haftalık Analizler</li>
              <li className="disabled"><X size={16} /> Öncelikli 7/24 Destek</li>
            </ul>
            <button onClick={onLaunchApp} className="btn btn-secondary" style={{ width: '100%', marginTop: 'auto' }}>
              Hemen Başla
            </button>
          </div>

          {/* Plan 2 */}
          <div className="price-card popular">
            <div className="popular-badge">En Çok Tercih Edilen</div>
            <div className="plan-name">Büyüyen (Growth)</div>
            <div className="plan-price">999 ₺ <span>/ Ay</span></div>
            <p className="plan-desc">İşlerini büyüten ve profesyonel kontrol isteyen restoranlar için.</p>
            <ul className="plan-features">
              <li><Check size={16} /> Sınırsız Masa Yönetimi</li>
              <li><Check size={16} /> Gelişmiş Sipariş ve Masa Takibi</li>
              <li><Check size={16} /> 3 Mutfak Ekranı</li>
              <li><Check size={16} /> Detaylı Satış ve Ürün Analizleri</li>
              <li><Check size={16} /> Haftalık/Aylık Kar-Zarar Raporu</li>
              <li><Check size={16} /> Öncelikli Destek Hattı</li>
            </ul>
            <button onClick={onLaunchApp} className="btn btn-primary" style={{ width: '100%', marginTop: 'auto' }}>
              14 Gün Ücretsiz Dene
            </button>
          </div>

          {/* Plan 3 */}
          <div className="price-card">
            <div className="plan-name">Kurumsal (Enterprise)</div>
            <div className="plan-price">1999 ₺ <span>/ Ay</span></div>
            <p className="plan-desc">Çok şubeli büyük restoran zincirleri ve franchise işletmeler için.</p>
            <ul className="plan-features">
              <li><Check size={16} /> Sınırsız Masa & Çoklu Şube</li>
              <li><Check size={16} /> Tüm Gelişmiş Özellikler Dahil</li>
              <li><Check size={16} /> Sınırsız Mutfak Ekranı</li>
              <li><Check size={16} /> API ve Entegrasyon Desteği</li>
              <li><Check size={16} /> Özel Bulut Sunucusu</li>
              <li><Check size={16} /> 7/24 Özel Müşteri Temsilcisi</li>
            </ul>
            <button onClick={onLaunchApp} className="btn btn-secondary" style={{ width: '100%', marginTop: 'auto' }}>
              İletişime Geç
            </button>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="testimonials-section">
        <div className="section-header">
          <h2>Restoran Sahipleri Ne Diyor?</h2>
          <p>Yüzlerce büyüyen restoranın tercihi olan Bidolu POS ile işinizi şansa bırakmayın.</p>
        </div>

        <div className="testimonials-grid">
          <div className="testimonial-card">
            <p className="testimonial-text">
              "Bidolu POS'a geçtikten sonra sipariş hatalarımız sıfıra indi. Mutfak ekranı sayesinde garsonlarımız ve aşçılarımız kusursuz bir uyum yakaladı. Kesinlikle tavsiye ederim."
            </p>
            <div className="testimonial-user">
              <div className="user-avatar">MK</div>
              <div>
                <div className="user-name">Mustafa Koç</div>
                <div className="user-title">Gusto Bistro - İşletme Sahibi</div>
              </div>
            </div>
          </div>

          <div className="testimonial-card">
            <p className="testimonial-text">
              "SaaS modeli olması harika, hiçbir lisanslama ve güncelleme masrafı yok. Evden bile restoranın anlık cirosunu ve masa durumunu takip edebiliyorum. Kurulumu da 5 dakikada yaptık!"
            </p>
            <div className="testimonial-user">
              <div className="user-avatar">AY</div>
              <div>
                <div className="user-name">Aylin Yılmaz</div>
                <div className="user-title">Mola Kahvesi - Kurucu</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <div className="landing-logo">
              <div className="logo-icon">B</div>
              <span className="logo-text">Bidolu POS</span>
            </div>
            <p style={{ marginTop: '12px', fontSize: '13px', color: 'var(--text-muted)' }}>
              Bulut tabanlı modern restoran otomasyonu ve yönetim sistemi.
            </p>
          </div>
          <div className="footer-links">
            <div>
              <h4>Ürün</h4>
              <a href="#features">Özellikler</a>
              <a href="#pricing">Fiyatlandırma</a>
            </div>
            <div>
              <h4>Şirket</h4>
              <a href="#">Hakkımızda</a>
              <a href="#">Destek</a>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          &copy; {new Date().getFullYear()} Bidolu POS. Tüm hakları saklıdır.
        </div>
      </footer>
    </div>
  );
}
