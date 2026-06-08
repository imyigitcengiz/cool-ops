import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useResponsive } from '../hooks/useResponsive';
import { TrendingUp, TrendingDown, DollarSign, ShoppingBag, CreditCard, Banknote, Clock, Award, BarChart3, CalendarDays, ChevronDown, RefreshCw } from 'lucide-react';

import { apiFetch, API_BASE } from '../lib/apiClient';

// ─── Mini Bar Chart (Canvas) ─────────────────────────
function BarChart({ data, labelKey, valueKey, height = 220, color = '#6366f1' }) {
  const canvasRef = useRef(null);
  const { isMobile } = useResponsive();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data.length) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.parentElement.clientWidth;
    const h = height;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    ctx.scale(dpr, dpr);

    const maxVal = Math.max(...data.map(d => d[valueKey]), 1);
    const padding = { top: 20, right: 10, bottom: 36, left: 50 };
    const chartW = w - padding.left - padding.right;
    const chartH = h - padding.top - padding.bottom;
    const barWidth = Math.min(40, (chartW / data.length) * 0.6);
    const gap = chartW / data.length;

    ctx.clearRect(0, 0, w, h);

    // Grid lines
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.12)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (chartH / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(w - padding.right, y);
      ctx.stroke();

      // Y-axis labels
      const val = maxVal - (maxVal / 4) * i;
      ctx.fillStyle = 'rgba(148, 163, 184, 0.7)';
      ctx.font = '10px Inter, system-ui';
      ctx.textAlign = 'right';
      ctx.fillText(val >= 1000 ? (val / 1000).toFixed(1) + 'K' : Math.round(val).toString(), padding.left - 8, y + 4);
    }

    // Bars
    data.forEach((d, i) => {
      const barH = (d[valueKey] / maxVal) * chartH;
      const x = padding.left + gap * i + (gap - barWidth) / 2;
      const y = padding.top + chartH - barH;

      // Bar gradient
      const grad = ctx.createLinearGradient(x, y, x, y + barH);
      grad.addColorStop(0, color);
      grad.addColorStop(1, color + '60');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.roundRect(x, y, barWidth, barH, [4, 4, 0, 0]);
      ctx.fill();

      // X-axis label
      ctx.fillStyle = 'rgba(148, 163, 184, 0.7)';
      ctx.font = '10px Inter, system-ui';
      ctx.textAlign = 'center';
      ctx.fillText(d[labelKey], x + barWidth / 2, h - padding.bottom + 16);
    });
  }, [data, labelKey, valueKey, height, color, isMobile]);

  return <canvas ref={canvasRef} style={{ display: 'block', width: '100%' }} />;
}

// ─── Hourly Heatmap ──────────────────────────────────
function HourlyHeatmap({ data }) {
  if (!data || data.length === 0) return null;
  const max = Math.max(...data, 1);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '4px' }}>
      {data.map((count, h) => {
        const intensity = count / max;
        return (
          <div key={h} title={`${h}:00 — ${count} sipariş`} style={{
            aspectRatio: '1', borderRadius: '6px', display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: '600',
            cursor: 'default', transition: 'transform 0.15s',
            background: count === 0 ? 'rgba(148,163,184,0.06)' : `rgba(99,102,241,${0.1 + intensity * 0.6})`,
            color: intensity > 0.5 ? '#fff' : 'var(--text-muted)',
          }}>
            <span style={{ fontSize: '8px', opacity: 0.7 }}>{String(h).padStart(2, '0')}</span>
            <span>{count}</span>
          </div>
        );
      })}
    </div>
  );
}

// ─── Payment Donut ───────────────────────────────────
function PaymentDonut({ cash, card }) {
  const canvasRef = useRef(null);
  const total = cash + card;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || total === 0) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const size = 140;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    canvas.style.width = size + 'px';
    canvas.style.height = size + 'px';
    ctx.scale(dpr, dpr);

    const cx = size / 2, cy = size / 2, r = 56, lw = 18;
    const cashPct = cash / total;
    const cashAngle = cashPct * Math.PI * 2;

    ctx.clearRect(0, 0, size, size);

    // Card arc
    ctx.beginPath();
    ctx.arc(cx, cy, r, -Math.PI / 2 + cashAngle, -Math.PI / 2 + Math.PI * 2);
    ctx.strokeStyle = '#8b5cf6';
    ctx.lineWidth = lw;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Cash arc
    ctx.beginPath();
    ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + cashAngle);
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = lw;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Center text
    ctx.fillStyle = 'var(--text-main, #0f172a)';
    ctx.font = 'bold 16px Inter, system-ui';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${Math.round(cashPct * 100)}%`, cx, cy - 6);
    ctx.font = '10px Inter, system-ui';
    ctx.fillStyle = 'rgba(148,163,184,0.7)';
    ctx.fillText('Nakit', cx, cy + 10);
  }, [cash, card, total]);

  if (total === 0) return <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px', fontSize: '13px' }}>Veri yok</div>;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '20px', justifyContent: 'center' }}>
      <canvas ref={canvasRef} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '3px', background: '#10b981' }} />
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Nakit</div>
            <div style={{ fontSize: '14px', fontWeight: '700' }}>{cash.toLocaleString('tr-TR')} ₺</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '3px', background: '#8b5cf6' }} />
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Kart</div>
            <div style={{ fontSize: '14px', fontWeight: '700' }}>{card.toLocaleString('tr-TR')} ₺</div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── KPI Card ────────────────────────────────────────
function KpiCard({ title, value, subtitle, change, icon: Icon, color = '#6366f1', isMobile }) {
  const isPositive = change >= 0;
  return (
    <div className="card" style={{ padding: isMobile ? '16px' : '20px', position: 'relative', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', top: '-10px', right: '-10px', width: '60px', height: '60px', borderRadius: '50%', background: `${color}08` }} />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
        <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '600' }}>{title}</span>
        <div style={{ width: '32px', height: '32px', borderRadius: '10px', background: `${color}12`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Icon size={16} color={color} />
        </div>
      </div>
      <div style={{ fontSize: isMobile ? '22px' : '26px', fontWeight: '800', color: 'var(--text-main)', letterSpacing: '-0.5px' }}>{value}</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px' }}>
        {change !== undefined && change !== null && (
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: '2px',
            fontSize: '11px', fontWeight: '700', padding: '2px 6px', borderRadius: '6px',
            background: isPositive ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
            color: isPositive ? '#10b981' : '#ef4444',
          }}>
            {isPositive ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
            {isPositive ? '+' : ''}{change}%
          </span>
        )}
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{subtitle}</span>
      </div>
    </div>
  );
}

// ─── Main Reports Component ──────────────────────────
export default function Reports() {
  const { isMobile } = useResponsive();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('week'); // today, week, month, year, custom
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [activeTab, setActiveTab] = useState('overview'); // overview, products, orders

  const getDateRange = useCallback(() => {
    const today = new Date();
    const fmt = (d) => d.toISOString().split('T')[0];

    switch (period) {
      case 'today':
        return { start: fmt(today), end: fmt(today) };
      case 'week': {
        const s = new Date(today);
        s.setDate(s.getDate() - 6);
        return { start: fmt(s), end: fmt(today) };
      }
      case 'month': {
        const s = new Date(today.getFullYear(), today.getMonth(), 1);
        return { start: fmt(s), end: fmt(today) };
      }
      case 'year': {
        const s = new Date(today.getFullYear(), 0, 1);
        return { start: fmt(s), end: fmt(today) };
      }
      case 'custom':
        return { start: customStart || fmt(today), end: customEnd || fmt(today) };
      default:
        return { start: fmt(today), end: fmt(today) };
    }
  }, [period, customStart, customEnd]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const { start, end } = getDateRange();
      const res = await apiFetch(`/report-stats/?start=${start}&end=${end}`);
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [getDateRange]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const periods = [
    { key: 'today', label: 'Bugün' },
    { key: 'week', label: 'Son 7 Gün' },
    { key: 'month', label: 'Bu Ay' },
    { key: 'year', label: 'Bu Yıl' },
    { key: 'custom', label: 'Özel' },
  ];

  const tabs = [
    { key: 'overview', label: '📊 Genel Bakış' },
    { key: 'products', label: '🏆 Ürünler' },
    { key: 'orders', label: '📋 Siparişler' },
  ];

  const s = data?.summary || {};
  const c = data?.comparison || {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

      {/* Period Filter Bar */}
      <div className="card" style={{ padding: '14px 18px', display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
        <CalendarDays size={16} style={{ color: 'var(--primary)', flexShrink: 0 }} />
        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', flex: 1 }}>
          {periods.map(p => (
            <button key={p.key} onClick={() => setPeriod(p.key)} style={{
              padding: '6px 14px', borderRadius: '8px', border: 'none', cursor: 'pointer',
              fontSize: '12px', fontWeight: '600', transition: 'all 0.15s',
              background: period === p.key ? 'var(--primary)' : 'rgba(148,163,184,0.08)',
              color: period === p.key ? '#fff' : 'var(--text-muted)',
            }}>{p.label}</button>
          ))}
        </div>
        {period === 'custom' && (
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <input type="date" value={customStart} onChange={e => setCustomStart(e.target.value)} className="form-control" style={{ padding: '5px 8px', fontSize: '12px', width: '130px' }} />
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>–</span>
            <input type="date" value={customEnd} onChange={e => setCustomEnd(e.target.value)} className="form-control" style={{ padding: '5px 8px', fontSize: '12px', width: '130px' }} />
          </div>
        )}
        <button onClick={fetchData} style={{
          background: 'none', border: '1px solid var(--panel-border)', borderRadius: '8px',
          padding: '6px 8px', cursor: 'pointer', color: 'var(--text-muted)', flexShrink: 0,
        }} title="Yenile">
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
        </button>
      </div>

      {/* Sub-tabs */}
      <div style={{ display: 'flex', gap: '4px', borderBottom: '1px solid var(--panel-border)', paddingBottom: '0' }}>
        {tabs.map(t => (
          <button key={t.key} onClick={() => setActiveTab(t.key)} style={{
            padding: '10px 18px', border: 'none', cursor: 'pointer', fontSize: '13px', fontWeight: '600',
            background: 'transparent', borderBottom: activeTab === t.key ? '2px solid var(--primary)' : '2px solid transparent',
            color: activeTab === t.key ? 'var(--primary)' : 'var(--text-muted)',
            transition: 'all 0.15s', marginBottom: '-1px',
          }}>{t.label}</button>
        ))}
      </div>

      {loading ? (
        <div className="spinner" style={{ margin: '60px auto' }} />
      ) : !data ? (
        <div className="card" style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>Veri yüklenemedi.</div>
      ) : (
        <>
          {/* ═══ OVERVIEW TAB ═══ */}
          {activeTab === 'overview' && (
            <>
              {/* KPI Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(3, 1fr)', gap: isMobile ? '10px' : '16px' }}>
                <KpiCard title="Brüt Ciro" value={`${s.total_revenue?.toLocaleString('tr-TR')} ₺`} subtitle="önceki döneme göre" change={c.revenue_change} icon={DollarSign} color="#10b981" isMobile={isMobile} />
                <KpiCard title="Toplam Gider" value={`${s.total_expense?.toLocaleString('tr-TR')} ₺`} subtitle="önceki döneme göre" change={c.expense_change} icon={CreditCard} color="#ef4444" isMobile={isMobile} />
                <KpiCard title="Net Kâr" value={`${s.net_profit?.toLocaleString('tr-TR')} ₺`} subtitle="önceki döneme göre" change={c.profit_change} icon={TrendingUp} color={s.net_profit >= 0 ? '#10b981' : '#ef4444'} isMobile={isMobile} />
                <KpiCard title="Sipariş Sayısı" value={s.order_count} subtitle="önceki döneme göre" change={c.order_change} icon={ShoppingBag} color="#6366f1" isMobile={isMobile} />
                <KpiCard title="Ort. Sipariş" value={`${s.avg_order?.toLocaleString('tr-TR')} ₺`} subtitle="sipariş başına" change={null} icon={BarChart3} color="#f59e0b" isMobile={isMobile} />
                <KpiCard title="Nakit / Kart" value={`${Math.round(s.total_revenue > 0 ? (s.cash_total / s.total_revenue) * 100 : 0)}% / ${Math.round(s.total_revenue > 0 ? (s.card_total / s.total_revenue) * 100 : 0)}%`} subtitle="ödeme dağılımı" change={null} icon={Banknote} color="#8b5cf6" isMobile={isMobile} />
              </div>

              {/* Charts Row */}
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '2fr 1fr', gap: '16px' }}>
                {/* Daily Sales Bar Chart */}
                <div className="card">
                  <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <BarChart3 size={16} style={{ color: 'var(--primary)' }} /> Günlük Satış Trendi
                  </h3>
                  {data.daily_sales?.length > 0 ? (
                    <BarChart data={data.daily_sales} labelKey="date" valueKey="revenue" color="#6366f1" height={200} />
                  ) : (
                    <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>Bu dönemde satış verisi yok</div>
                  )}
                </div>

                {/* Payment Distribution */}
                <div className="card">
                  <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <CreditCard size={16} style={{ color: '#8b5cf6' }} /> Ödeme Dağılımı
                  </h3>
                  <PaymentDonut cash={s.cash_total || 0} card={s.card_total || 0} />
                </div>
              </div>

              {/* Hourly + Channel Row */}
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '16px' }}>
                {/* Hourly Heatmap */}
                <div className="card">
                  <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Clock size={16} style={{ color: '#f59e0b' }} /> Saatlik Yoğunluk
                  </h3>
                  <HourlyHeatmap data={data.hourly_distribution} />
                </div>

                {/* Channel Breakdown */}
                <div className="card">
                  <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '16px' }}>Kanal Ciro Dağılımı</h3>
                  {Object.keys(data.channel_breakdown || {}).length === 0 ? (
                    <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>Veri yok</div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {Object.entries(data.channel_breakdown).sort((a, b) => b[1] - a[1]).map(([ch, amt]) => {
                        const pct = s.total_revenue > 0 ? (amt / s.total_revenue) * 100 : 0;
                        const colors = { 'Yemeksepeti': '#fa0050', 'Getir': '#5d3ebc', 'Trendyol': '#f27a1a', 'Migros': '#ff6600', 'WebSitesi': '#10b981', 'Masa Satışları': '#6366f1' };
                        return (
                          <div key={ch}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                              <span style={{ fontWeight: '600' }}>{ch}</span>
                              <span style={{ color: 'var(--text-muted)' }}>{amt.toLocaleString('tr-TR')} ₺ ({pct.toFixed(1)}%)</span>
                            </div>
                            <div style={{ height: '6px', background: 'rgba(0,0,0,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                              <div style={{ height: '100%', background: colors[ch] || '#94a3b8', width: `${pct}%`, borderRadius: '3px', transition: 'width 0.5s' }} />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>

              {/* Expense Breakdown */}
              {Object.keys(data.expense_breakdown || {}).length > 0 && (
                <div className="card">
                  <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '16px' }}>Gider Kategori Dağılımı</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '12px' }}>
                    {Object.entries(data.expense_breakdown).sort((a, b) => b[1] - a[1]).map(([cat, amt]) => {
                      const pct = s.total_expense > 0 ? (amt / s.total_expense) * 100 : 0;
                      return (
                        <div key={cat}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                            <span style={{ fontWeight: '600' }}>{cat}</span>
                            <span style={{ color: 'var(--text-muted)' }}>{amt.toLocaleString('tr-TR')} ₺ ({pct.toFixed(1)}%)</span>
                          </div>
                          <div style={{ height: '6px', background: 'rgba(0,0,0,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ height: '100%', background: '#ef4444', width: `${pct}%`, borderRadius: '3px', transition: 'width 0.5s' }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          )}

          {/* ═══ PRODUCTS TAB ═══ */}
          {activeTab === 'products' && (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: '18px 20px', borderBottom: '1px solid var(--panel-border)' }}>
                <h3 style={{ margin: 0, fontSize: '15px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Award size={16} style={{ color: '#f59e0b' }} /> En Çok Satan Ürünler (Top 10)
                </h3>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ background: '#f8fafc', borderBottom: '1px solid var(--panel-border)' }}>
                      <th style={{ padding: '10px 16px', textAlign: 'left', fontWeight: '600', color: '#64748b' }}>#</th>
                      <th style={{ padding: '10px 16px', textAlign: 'left', fontWeight: '600', color: '#64748b' }}>Ürün</th>
                      <th style={{ padding: '10px 16px', textAlign: 'right', fontWeight: '600', color: '#64748b' }}>Adet</th>
                      <th style={{ padding: '10px 16px', textAlign: 'right', fontWeight: '600', color: '#64748b' }}>Ciro</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(data.top_products || []).length === 0 ? (
                      <tr><td colSpan={4} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Bu dönemde satış verisi yok</td></tr>
                    ) : data.top_products.map((p, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid var(--panel-border)' }}>
                        <td style={{ padding: '10px 16px' }}>
                          <span style={{
                            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                            width: '24px', height: '24px', borderRadius: '7px', fontSize: '11px', fontWeight: '800',
                            background: i < 3 ? ['#fef3c7', '#f1f5f9', '#fef2f2'][i] : 'transparent',
                            color: i < 3 ? ['#d97706', '#475569', '#dc2626'][i] : 'var(--text-muted)',
                          }}>{i + 1}</span>
                        </td>
                        <td style={{ padding: '10px 16px', fontWeight: '600' }}>{p.name}</td>
                        <td style={{ padding: '10px 16px', textAlign: 'right' }}>{p.total_qty} adet</td>
                        <td style={{ padding: '10px 16px', textAlign: 'right', fontWeight: '700', color: 'var(--primary)' }}>
                          {parseFloat(p.total_revenue).toLocaleString('tr-TR')} ₺
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ═══ ORDERS TAB ═══ */}
          {activeTab === 'orders' && (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: '18px 20px', borderBottom: '1px solid var(--panel-border)' }}>
                <h3 style={{ margin: 0, fontSize: '15px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShoppingBag size={16} style={{ color: '#6366f1' }} /> Son Siparişler
                </h3>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ background: '#f8fafc', borderBottom: '1px solid var(--panel-border)' }}>
                      <th style={{ padding: '10px 16px', textAlign: 'left', fontWeight: '600', color: '#64748b', whiteSpace: 'nowrap' }}>Sipariş #</th>
                      <th style={{ padding: '10px 16px', textAlign: 'left', fontWeight: '600', color: '#64748b' }}>Masa</th>
                      <th style={{ padding: '10px 16px', textAlign: 'right', fontWeight: '600', color: '#64748b' }}>Tutar</th>
                      <th style={{ padding: '10px 16px', textAlign: 'center', fontWeight: '600', color: '#64748b' }}>Durum</th>
                      <th style={{ padding: '10px 16px', textAlign: 'center', fontWeight: '600', color: '#64748b' }}>Ödeme</th>
                      {!isMobile && <th style={{ padding: '10px 16px', textAlign: 'right', fontWeight: '600', color: '#64748b' }}>Tarih</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {(data.recent_orders || []).length === 0 ? (
                      <tr><td colSpan={6} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Bu dönemde sipariş yok</td></tr>
                    ) : data.recent_orders.map((o) => {
                      const statusColors = {
                        'completed': { bg: '#ecfdf5', color: '#059669' },
                        'preparing': { bg: '#fef3c7', color: '#d97706' },
                        'ready': { bg: '#eff6ff', color: '#2563eb' },
                        'cancelled': { bg: '#fef2f2', color: '#dc2626' },
                      };
                      const sc = statusColors[o.status_key] || statusColors.preparing;
                      return (
                        <tr key={o.id} style={{ borderBottom: '1px solid var(--panel-border)' }}>
                          <td style={{ padding: '10px 16px', fontWeight: '600' }}>#{o.id}</td>
                          <td style={{ padding: '10px 16px' }}>{o.table}</td>
                          <td style={{ padding: '10px 16px', textAlign: 'right', fontWeight: '700' }}>{o.total.toLocaleString('tr-TR')} ₺</td>
                          <td style={{ padding: '10px 16px', textAlign: 'center' }}>
                            <span style={{ background: sc.bg, color: sc.color, padding: '3px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: '600' }}>{o.status}</span>
                          </td>
                          <td style={{ padding: '10px 16px', textAlign: 'center', fontSize: '12px', color: 'var(--text-muted)' }}>{o.payment_method}</td>
                          {!isMobile && <td style={{ padding: '10px 16px', textAlign: 'right', fontSize: '12px', color: 'var(--text-muted)' }}>{o.date}</td>}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
