import React, { useState, useEffect, useMemo } from 'react';
import { Globe, Save, Monitor, Tablet, Smartphone, ExternalLink, Calendar, Eye, Edit3, Check, AtSign, Users, Image, ToggleLeft, ToggleRight, Type, Link, ChevronUp, ChevronDown, Trash2, Plus, ArrowLeft, Star, Settings, Trash, Clock, MessageSquare, Lock, Unlock, Layers, Sparkles, BookOpen, UtensilsCrossed, BarChart3, Megaphone, CalendarCheck, Puzzle, Search, Grid3X3, ImagePlus, Quote, MapPin, Mail, Hash, Minus, GripVertical, ChevronRight, Play, Zap, Award, Target, HeartHandshake, Share2, ListOrdered, Columns, SeparatorHorizontal, Code2, HelpCircle, Building2, MousePointerClick } from 'lucide-react';
import { useResponsive } from '../hooks/useResponsive';

import { apiFetch, API_BASE } from '../lib/apiClient';

const TEMPLATES = [
  { id: 'Modern Dark', name: 'Modern Dark', bg: '#0b0c10', text: '#ffffff', accent: '#6366f1', cardBg: '#111218', desc: 'Canlı indigo vurgularıyla şık koyu tema' },
  { id: 'Elegant Gold', name: 'Elegant Gold', bg: '#0f0e0c', text: '#f3e5c8', accent: '#d4af37', cardBg: '#1a1815', desc: 'Altın detaylarla lüks serif başlık stili' },
  { id: 'Cozy Retro', name: 'Cozy Retro', bg: '#f4ede4', text: '#2c221e', accent: '#d96a3b', cardBg: '#ede5dc', desc: 'Sıcak organik krem zemin, vintage mercan dokunuşu' },
  { id: 'Minimal Light', name: 'Minimal Light', bg: '#ffffff', text: '#111827', accent: '#10b981', cardBg: '#f9fafb', desc: 'Sade yüksek kontrastlı ızgara düzeni, zümrüt vurgu' }
];

const DEVICE_CONFIGS = {
  desktop: { width: '100%', label: 'Masaüstü', icon: Monitor },
  tablet: { width: '640px', label: 'Tablet', icon: Tablet },
  mobile: { width: '375px', label: 'Mobil', icon: Smartphone }
};

function WebsitePreview({
  tpl,
  domain,
  aboutText,
  instagram,
  facebook,
  enableReservation,
  bannerText,
  resName,
  device,
  blocks,
  elementorMode = false,
  selectedBlockId = null,
  onSelectBlock = () => {},
  onMoveBlock = () => {},
  onDeleteBlock = () => {},
  onDropBlock = () => {},
  themeColor = '#6366f1',
  typography = 'Sans-serif',
  pages = [],
  activePageId = 'home',
  onSelectPage = () => {}
}) {
  const isLight = tpl.bg === '#ffffff' || tpl.bg === '#f4ede4';
  const accent = themeColor || tpl.accent;

  // Typography font mapping
  let fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
  if (typography === 'Serif') {
    fontFamily = '"Playfair Display", Georgia, serif';
  } else if (typography === 'Monospace') {
    fontFamily = '"Courier New", monospace';
  } else if (typography === 'Outfit') {
    fontFamily = '"Outfit", "Inter", sans-serif';
  }

  const ElementorWrapper = ({ children, id, index, label, active }) => {
    if (!elementorMode) return children;

    return (
      <div
        onClick={(e) => {
          e.stopPropagation();
          onSelectBlock(id);
        }}
        draggable={true}
        onDragStart={(e) => {
          e.stopPropagation();
          e.dataTransfer.setData("text/plain", index.toString());
          e.currentTarget.style.opacity = '0.4';
        }}
        onDragEnd={(e) => {
          e.currentTarget.style.opacity = '1';
        }}
        onDragOver={(e) => {
          e.preventDefault();
          e.stopPropagation();
          e.currentTarget.style.borderTop = '4px dashed #6366f1';
        }}
        onDragLeave={(e) => {
          e.currentTarget.style.borderTop = '1px dashed transparent';
        }}
        onDrop={(e) => {
          e.preventDefault();
          e.stopPropagation();
          e.currentTarget.style.borderTop = '1px dashed transparent';
          const fromIndex = parseInt(e.dataTransfer.getData("text/plain"), 10);
          if (!isNaN(fromIndex) && fromIndex !== index) {
            onDropBlock(fromIndex, index);
          }
        }}
        style={{
          position: 'relative',
          cursor: 'grab',
          border: active ? '2px solid #6366f1' : '1px dashed transparent',
          borderTop: '1px dashed transparent',
          transition: 'all 0.2s',
          margin: '8px 0',
          padding: '4px 0'
        }}
        onMouseOver={(e) => {
          if (!active) e.currentTarget.style.border = '1px dashed rgba(99, 102, 241, 0.6)';
        }}
        onMouseOut={(e) => {
          if (!active) e.currentTarget.style.border = '1px dashed transparent';
        }}
      >
        {/* Outline overlay */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          border: active ? '2px solid #6366f1' : '1px dashed rgba(99, 102, 241, 0.3)',
          pointerEvents: 'none',
          zIndex: 10
        }} />

        {/* Quick Toolbar */}
        <div style={{
          position: 'absolute',
          top: '-12px',
          left: '12px',
          background: active ? '#6366f1' : '#475569',
          color: '#0f172a',
          fontSize: '10px',
          fontWeight: '700',
          padding: '2px 8px',
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          zIndex: 12,
          boxShadow: '0 2px 6px rgba(0,0,0,0.15)'
        }}>
          <span style={{ cursor: 'move' }}>☰ {label}</span>
          <div style={{ display: 'flex', gap: '5px', marginLeft: '6px' }} onClick={e => e.stopPropagation()}>
            <button
              type="button"
              onClick={() => onMoveBlock(index, -1)}
              disabled={index === 0}
              style={{ background: 'none', border: 'none', color: '#0f172a', cursor: 'pointer', padding: 0, opacity: index === 0 ? 0.3 : 1 }}
              title="Yukarı Taşı"
            >
              <ChevronUp size={12} />
            </button>
            <button
              type="button"
              onClick={() => onMoveBlock(index, 1)}
              disabled={index === blocks.length - 1}
              style={{ background: 'none', border: 'none', color: '#0f172a', cursor: 'pointer', padding: 0, opacity: index === blocks.length - 1 ? 0.3 : 1 }}
              title="Aşağı Taşı"
            >
              <ChevronDown size={12} />
            </button>
            <button
              type="button"
              onClick={() => onDeleteBlock(id)}
              style={{ background: 'none', border: 'none', color: '#ff8a8a', cursor: 'pointer', padding: 0, marginLeft: '4px' }}
              title="Sil"
            >
              <Trash2 size={12} />
            </button>
          </div>
        </div>

        {children}
      </div>
    );
  };

  const renderModularBlocks = () => {
    return (blocks || []).map((sec, idx) => {
      const secType = sec.type;
      const title = sec.title || '';
      const content = sec.content || {};
      const active = selectedBlockId === sec.id;

      if (secType === 'hero') {
        const banner = content.banner || 'Eşsiz Lezzetlerin Buluşma Noktası';
        const sub = content.subtitle || 'Taze malzemelerle hazırlanan usta ellerden çıkan eşsiz tabaklar.';
        const btnText = content.button_text || 'Masa Rezervasyonu Yap';
        const layout = content.layout || 'center';
        const image = content.image || 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80';

        const resBtn = enableReservation && btnText && (
          <button style={{
            border: 'none',
            background: accent,
            color: isLight ? '#fff' : '#000',
            padding: '8px 18px',
            fontSize: '11px',
            borderRadius: '20px',
            fontWeight: '700',
            cursor: 'pointer',
            display: 'flex',
            gap: '5px',
            alignItems: 'center',
            marginTop: '6px',
            boxShadow: `0 4px 12px ${accent}30`
          }}>
            <Calendar size={11} /> {btnText}
          </button>
        );

        if (layout === 'split') {
          return (
            <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="Hero Giriş (Split)" active={active}>
              <div style={{
                padding: device === 'mobile' ? '24px 16px' : '40px 24px',
                display: 'flex',
                flexDirection: device === 'mobile' ? 'column' : 'row',
                alignItems: 'center',
                gap: '20px',
                background: `linear-gradient(to bottom, ${accent}10, transparent)`,
                borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.03)'}`
              }}>
                <div style={{ flex: 1.2, textAlign: 'left', display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '8px' }}>
                  <h1 style={{ fontSize: device === 'mobile' ? '18px' : '24px', fontWeight: '800', lineHeight: '1.2', margin: 0 }}>
                    {banner}
                  </h1>
                  <p style={{ fontSize: '11px', opacity: 0.8, lineHeight: '1.6', margin: 0 }}>
                    {sub}
                  </p>
                  {resBtn}
                </div>
                <div style={{ flex: 1, width: '100%' }}>
                  <img src={image} style={{ width: '100%', height: '160px', objectFit: 'cover', borderRadius: '8px', boxShadow: '0 6px 18px rgba(0,0,0,0.15)' }} alt="" />
                </div>
              </div>
            </ElementorWrapper>
          );
        }

        if (layout === 'glass') {
          return (
            <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="Hero Giriş (Glass)" active={active}>
              <div style={{
                padding: device === 'mobile' ? '36px 16px' : '56px 24px',
                backgroundImage: `url(${image})`,
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                position: 'relative',
                borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.03)'}`,
                display: 'flex',
                justifyContent: 'center'
              }}>
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.45)', zIndex: 1 }} />
                <div style={{
                  background: 'rgba(255, 255, 255, 0.08)',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '12px',
                  padding: device === 'mobile' ? '20px 14px' : '28px 20px',
                  maxWidth: '420px',
                  width: '100%',
                  textAlign: 'center',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '8px',
                  position: 'relative',
                  zIndex: 2,
                  boxShadow: '0 15px 30px rgba(0,0,0,0.3)'
                }}>
                  <h1 style={{ fontSize: device === 'mobile' ? '18px' : '22px', fontWeight: '800', lineHeight: '1.25', margin: 0, color: '#0f172a' }}>
                    {banner}
                  </h1>
                  <p style={{ fontSize: '11px', color: 'rgba(255,255,255,0.85)', lineHeight: '1.5', margin: 0 }}>
                    {sub}
                  </p>
                  {resBtn}
                </div>
              </div>
            </ElementorWrapper>
          );
        }

        return (
          <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="Hero Giriş (Center)" active={active}>
            <div style={{
              padding: device === 'mobile' ? '28px 16px' : '36px 28px 28px',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '10px',
              background: `linear-gradient(to bottom, ${accent}10, transparent)`,
              borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.03)'}`
            }}>
              <h1 style={{
                fontSize: device === 'mobile' ? '18px' : '22px',
                fontWeight: '800',
                maxWidth: '320px',
                lineHeight: '1.25',
                margin: 0
              }}>
                {banner}
              </h1>
              <div style={{ width: '36px', height: '2px', background: accent, borderRadius: '2px' }} />
              <p style={{ fontSize: '11px', opacity: 0.75, maxWidth: '300px', lineHeight: '1.6', margin: 0 }}>
                {sub}
              </p>
              {resBtn}
            </div>
          </ElementorWrapper>
        );
      }

      if (secType === 'about') {
        const text = content.text || '';
        const image = content.image || 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=600&q=80';
        const layout = content.layout || 'left';

        if (layout === 'minimal') {
          return (
            <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="Hakkımızda (Minimal)" active={active}>
              <div style={{
                padding: device === 'mobile' ? '20px 16px' : '28px 24px',
                background: `${isLight ? 'rgba(0,0,0,0.02)' : 'rgba(255,255,255,0.02)'}`,
                borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.03)'}`,
                textAlign: 'center',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '8px'
              }}>
                <h3 style={{ fontSize: '13px', fontWeight: '700', color: accent, margin: 0, textTransform: 'uppercase', letterSpacing: '1px' }}>
                  {title}
                </h3>
                <p style={{ fontSize: '11px', lineHeight: '1.65', opacity: 0.8, maxWidth: '480px', margin: 0 }}>
                  {text}
                </p>
              </div>
            </ElementorWrapper>
          );
        }

        return (
          <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="Hakkımızda" active={active}>
            <div style={{
              padding: device === 'mobile' ? '16px' : '20px 28px',
              background: `${isLight ? 'rgba(0,0,0,0.02)' : 'rgba(255,255,255,0.02)'}`,
              borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.03)'}`,
              display: 'flex',
              flexDirection: device === 'mobile' ? 'column' : (layout === 'left' ? 'row' : 'row-reverse'),
              gap: '20px',
              alignItems: 'center'
            }}>
              <div style={{ flex: 1.2, textAlign: 'left' }}>
                <h3 style={{ fontSize: '13px', fontWeight: '700', color: accent, marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '1px' }}>
                  {title}
                </h3>
                <p style={{ fontSize: '11px', lineHeight: '1.65', opacity: 0.8, margin: 0 }}>
                  {text}
                </p>
              </div>
              <div style={{ flex: 1, width: '100%' }}>
                <img src={image} style={{ width: '100%', height: '140px', objectFit: 'cover', borderRadius: '8px' }} alt="" />
              </div>
            </div>
          </ElementorWrapper>
        );
      }

      if (secType === 'menu') {
        const items = content.items || [];
        const layout = content.layout || 'grid';

        let menuGrid;
        if (layout === 'list') {
          menuGrid = (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', textAlign: 'left' }}>
              {items.map((item, i) => (
                <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                    <span style={{ fontSize: '11px', fontWeight: '700' }}>{item.name}</span>
                    <div style={{ flexGrow: 1, borderBottom: `1px dotted ${isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.15)'}`, margin: '0 8px' }} />
                    <span style={{ fontSize: '11px', fontWeight: '800', color: accent }}>{item.price} ₺</span>
                  </div>
                  {item.description && <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>{item.description}</span>}
                </div>
              ))}
            </div>
          );
        } else if (layout === 'minimal') {
          menuGrid = (
            <div style={{ display: 'grid', gridTemplateColumns: device === 'mobile' ? '1fr' : '1fr 1fr 1fr', gap: '10px', textAlign: 'left' }}>
              {items.map((item, i) => (
                <div key={i} style={{
                  background: tpl.cardBg,
                  border: `1px solid ${isLight ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.06)'}`,
                  borderRadius: '8px',
                  padding: '10px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '11px', fontWeight: '700' }}>{item.name}</span>
                    <span style={{ fontSize: '10px', color: accent, fontWeight: '750' }}>{item.price} ₺</span>
                  </div>
                  <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>{item.description}</span>
                </div>
              ))}
            </div>
          );
        } else {
          menuGrid = (
            <div style={{ display: 'grid', gridTemplateColumns: device === 'mobile' ? '1fr' : '1fr 1fr 1fr', gap: '10px', textAlign: 'left' }}>
              {items.map((item, i) => (
                <div key={i} style={{
                  background: tpl.cardBg,
                  border: `1px solid ${isLight ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.06)'}`,
                  borderRadius: '8px',
                  padding: '10px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px'
                }}>
                  {item.image ? (
                    <img src={item.image} style={{ width: '100%', height: '70px', objectFit: 'cover', borderRadius: '4px' }} alt="" />
                  ) : (
                    <div style={{ width: '100%', height: '40px', background: `${accent}20`, borderRadius: '4px' }} />
                  )}
                  <span style={{ fontSize: '11px', fontWeight: '600' }}>{item.name}</span>
                  <span style={{ fontSize: '10px', color: accent, fontWeight: '700' }}>{item.price} ₺</span>
                  <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>{item.description}</span>
                </div>
              ))}
            </div>
          );
        }

        return (
          <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="Öne Çıkan Menü" active={active}>
            <div style={{ padding: device === 'mobile' ? '16px' : '20px 28px', borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.03)'}` }}>
              <h3 style={{ fontSize: '13px', fontWeight: '700', color: accent, marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '1px', textAlign: 'left' }}>
                {title}
              </h3>
              {menuGrid}
            </div>
          </ElementorWrapper>
        );
      }

      if (secType === 'testimonials') {
        const quotes = content.quotes || [];
        const layout = content.layout || 'grid';

        let quotesGrid;
        if (layout === 'spotlight') {
          const q = quotes[0] || { name: 'Misafir', text: 'Harika yemekler, hızlı servis.', rating: 5 };
          quotesGrid = (
            <div style={{
              background: tpl.cardBg,
              padding: '16px 20px',
              borderRadius: '12px',
              border: `1px solid ${isLight ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.06)'}`,
              textAlign: 'center',
              position: 'relative'
            }}>
              <div style={{ fontSize: '11px', color: accent, marginBottom: '6px' }}>{"⭐".repeat(parseInt(q.rating || 5))}</div>
              <p style={{ fontSize: '11px', margin: '0 0 8px 0', fontStyle: 'italic', opacity: 0.9, lineHeight: '1.5' }}>"{q.text}"</p>
              <span style={{ fontSize: '9.5px', fontWeight: '700', opacity: 0.75 }}>- {q.name}</span>
            </div>
          );
        } else {
          quotesGrid = (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', textAlign: 'left' }}>
              {quotes.map((q, i) => (
                <div key={i} style={{ background: tpl.cardBg, padding: '8px 12px', borderRadius: '8px', border: `1px solid ${isLight ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.06)'}` }}>
                  <div style={{ fontSize: '9px', color: accent, marginBottom: '4px' }}>{"⭐".repeat(parseInt(q.rating || 5))}</div>
                  <p style={{ fontSize: '10px', margin: 0, fontStyle: 'italic', opacity: 0.85 }}>"{q.text}"</p>
                  <span style={{ fontSize: '9px', fontWeight: '700', display: 'block', marginTop: '4px', opacity: 0.75 }}>- {q.name}</span>
                </div>
              ))}
            </div>
          );
        }

        return (
          <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="Yorumlar" active={active}>
            <div style={{ padding: device === 'mobile' ? '16px' : '20px 28px', borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.03)'}` }}>
              <h3 style={{ fontSize: '13px', fontWeight: '700', color: accent, marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '1px', textAlign: 'left' }}>
                {title}
              </h3>
              {quotesGrid}
            </div>
          </ElementorWrapper>
        );
      }

      if (secType === 'hours') {
        const address = content.address || '';
        const phone = content.phone || '';
        const times = content.times || [];
        const layout = content.layout || 'split';

        const infoBlock = (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {address && <p style={{ fontSize: '10px', margin: 0 }}>📍 {address}</p>}
            {phone && <p style={{ fontSize: '10px', margin: 0 }}>📞 {phone}</p>}
          </div>
        );

        const hoursBlock = (
          <div style={{ background: tpl.cardBg, padding: '10px', borderRadius: '8px', border: `1px solid ${isLight ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.06)'}`, flex: 1.2, width: '100%' }}>
            <span style={{ fontSize: '10px', fontWeight: '700', color: accent, display: 'block', marginBottom: '6px' }}>Çalışma Saatleri</span>
            {times.map((t, indexRow) => (
              <div key={indexRow} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9.5px', padding: '2px 0', borderBottom: indexRow !== times.length - 1 ? `1px solid ${isLight ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.03)'}` : 'none' }}>
                <span style={{ fontWeight: '600' }}>{t.day}</span>
                <span>{t.hours}</span>
              </div>
            ))}
          </div>
        );

        if (layout === 'center') {
          return (
            <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="Saatler & İletişim (Center)" active={active}>
              <div style={{
                padding: device === 'mobile' ? '16px' : '20px 28px',
                borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.03)'}`,
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                textAlign: 'center',
                alignItems: 'center'
              }}>
                <h3 style={{ fontSize: '13px', fontWeight: '700', color: accent, margin: 0, textTransform: 'uppercase', letterSpacing: '1px' }}>
                  {title}
                </h3>
                {infoBlock}
                {hoursBlock}
              </div>
            </ElementorWrapper>
          );
        }

        return (
          <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="Saatler & İletişim" active={active}>
            <div style={{
              padding: device === 'mobile' ? '16px' : '20px 28px',
              borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.03)'}`,
              display: 'flex',
              flexDirection: device === 'mobile' ? 'column' : 'row',
              gap: '16px',
              textAlign: 'left',
              alignItems: 'center'
            }}>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <h3 style={{ fontSize: '13px', fontWeight: '700', color: accent, margin: 0, textTransform: 'uppercase', letterSpacing: '1px' }}>
                  {title}
                </h3>
                {infoBlock}
              </div>
              {hoursBlock}
            </div>
          </ElementorWrapper>
        );
      }

      if (secType === 'reservation') {
        return (
          <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="Rezervasyon" active={active}>
            <div style={{ padding: device === 'mobile' ? '24px 16px' : '28px 28px', textAlign: 'center', background: `linear-gradient(to top, ${accent}10, transparent)`, borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.03)'}` }}>
              <h3 style={{ fontSize: '13px', fontWeight: '700', color: accent, marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '1px' }}>
                {title}
              </h3>
              <p style={{ fontSize: '10px', opacity: 0.75, marginBottom: '8px' }}>Masa rezervasyonu talebi oluşturabilirsiniz.</p>
              {enableReservation && (
                <button style={{
                  border: 'none',
                  background: accent,
                  color: isLight ? '#fff' : '#000',
                  padding: '6px 14px',
                  fontSize: '10px',
                  borderRadius: '20px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  display: 'inline-flex',
                  gap: '4px',
                  alignItems: 'center'
                }}>
                  <Calendar size={10} /> Rezervasyon Yap
                </button>
              )}
            </div>
          </ElementorWrapper>
        );
      }

      // ─── GALLERY BLOCK ──────────────────────────────
      if (secType === 'gallery') {
        const images = sec.content?.images || [];
        return (
          <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="Galeri" active={active}>
            <div style={{ padding: device === 'mobile' ? '24px 16px' : '40px 28px', borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.03)'}` }}>
              <h3 style={{ fontSize: '16px', fontWeight: '800', textAlign: 'center', marginBottom: '20px', color: accent }}>{title}</h3>
              <div style={{ display: 'grid', gridTemplateColumns: device === 'mobile' ? '1fr 1fr' : '1fr 1fr 1fr', gap: '8px' }}>
                {images.map((img, i) => (
                  <div key={i} style={{ borderRadius: '8px', overflow: 'hidden', position: 'relative', aspectRatio: '4/3', background: isLight ? '#f1f5f9' : '#1e293b' }}>
                    {img.url ? <img src={img.url} alt={img.caption || ''} style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontSize: '10px' }}>📷</div>}
                    {img.caption && <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, background: 'linear-gradient(transparent, rgba(0,0,0,0.7))', padding: '4px 6px', fontSize: '8px', color: '#0f172a' }}>{img.caption}</div>}
                  </div>
                ))}
              </div>
            </div>
          </ElementorWrapper>
        );
      }

      // ─── CTA BLOCK ────────────────────────────────────
      if (secType === 'cta') {
        const ctaBg = sec.content?.bg_color || accent;
        return (
          <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="CTA" active={active}>
            <div style={{ padding: device === 'mobile' ? '24px 16px' : '40px 28px', textAlign: 'center', background: `linear-gradient(135deg, ${ctaBg}15, ${ctaBg}08)`, borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.03)'}` }}>
              <h3 style={{ fontSize: '16px', fontWeight: '800', marginBottom: '8px' }}>{sec.content?.heading || title}</h3>
              <p style={{ fontSize: '11px', opacity: 0.75, marginBottom: '14px', maxWidth: '400px', margin: '0 auto 14px' }}>{sec.content?.text || ''}</p>
              {sec.content?.layout === 'newsletter' ? (
                <div style={{ display: 'flex', gap: '6px', maxWidth: '320px', margin: '0 auto' }}>
                  <input type="email" placeholder={sec.content?.placeholder_text || 'E-posta'} style={{ flex: 1, padding: '8px 12px', border: `1px solid ${isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.15)'}`, borderRadius: '8px', background: isLight ? '#f8fafc' : 'rgba(255,255,255,0.05)', fontSize: '10px', color: 'inherit', outline: 'none' }} />
                  <button style={{ background: ctaBg, color: '#0f172a', border: 'none', padding: '8px 16px', borderRadius: '8px', fontSize: '10px', fontWeight: '700', cursor: 'pointer' }}>{sec.content?.button_text || 'Abone Ol'}</button>
                </div>
              ) : (
                <button style={{ background: ctaBg, color: '#0f172a', border: 'none', padding: '8px 20px', borderRadius: '8px', fontSize: '11px', fontWeight: '700', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                  {sec.content?.button_text || 'Başla'}
                </button>
              )}
            </div>
          </ElementorWrapper>
        );
      }

      // ─── STATS BLOCK ──────────────────────────────────
      if (secType === 'stats') {
        const items = sec.content?.items || [];
        return (
          <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="İstatistik" active={active}>
            <div style={{ padding: device === 'mobile' ? '24px 16px' : '40px 28px', textAlign: 'center', borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.03)'}` }}>
              <h3 style={{ fontSize: '14px', fontWeight: '800', marginBottom: '20px', color: accent }}>{title}</h3>
              <div style={{ display: 'grid', gridTemplateColumns: device === 'mobile' ? '1fr 1fr' : `repeat(${Math.min(items.length, 4)}, 1fr)`, gap: '16px' }}>
                {items.map((item, i) => (
                  <div key={i} style={{ padding: '16px', background: isLight ? 'rgba(0,0,0,0.02)' : 'rgba(255,255,255,0.03)', borderRadius: '10px', border: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.05)'}` }}>
                    <div style={{ fontSize: '16px', marginBottom: '4px' }}>{item.icon}</div>
                    <div style={{ fontSize: '22px', fontWeight: '900', color: accent, lineHeight: '1' }}>{item.number}</div>
                    <div style={{ fontSize: '9px', opacity: 0.7, marginTop: '4px', fontWeight: '600' }}>{item.label}</div>
                  </div>
                ))}
              </div>
            </div>
          </ElementorWrapper>
        );
      }

      // ─── FAQ BLOCK ────────────────────────────────────
      if (secType === 'faq') {
        const faqItems = sec.content?.items || [];
        return (
          <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="SSS" active={active}>
            <div style={{ padding: device === 'mobile' ? '24px 16px' : '40px 28px', borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.03)'}` }}>
              <h3 style={{ fontSize: '16px', fontWeight: '800', textAlign: 'center', marginBottom: '20px', color: accent }}>{title}</h3>
              <div style={{ maxWidth: '500px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {faqItems.map((item, i) => (
                  <div key={i} style={{ background: isLight ? 'rgba(0,0,0,0.02)' : 'rgba(255,255,255,0.03)', border: `1px solid ${isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.05)'}`, borderRadius: '8px', padding: '12px 14px' }}>
                    <div style={{ fontSize: '11px', fontWeight: '700', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ color: accent }}>Q</span> {item.question}
                    </div>
                    <div style={{ fontSize: '10px', opacity: 0.7, lineHeight: '1.5', paddingLeft: '18px' }}>{item.answer}</div>
                  </div>
                ))}
              </div>
            </div>
          </ElementorWrapper>
        );
      }

      // ─── SPACER BLOCK ─────────────────────────────────
      if (secType === 'spacer') {
        const h = sec.content?.height || 60;
        return (
          <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="Boşluk" active={active}>
            <div style={{ height: `${h}px` }} />
          </ElementorWrapper>
        );
      }

      // ─── DIVIDER BLOCK ────────────────────────────────
      if (secType === 'divider') {
        const divStyle = sec.content?.style || 'solid';
        const divThickness = sec.content?.thickness || 1;
        const divColor = sec.content?.color || (isLight ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.08)');
        return (
          <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="Ayırıcı" active={active}>
            <div style={{ padding: '16px 28px' }}>
              <hr style={{ border: 'none', borderTop: `${divThickness}px ${divStyle} ${divColor}`, margin: 0 }} />
            </div>
          </ElementorWrapper>
        );
      }

      // ─── LOGO STRIP BLOCK ─────────────────────────────
      if (secType === 'logo-strip') {
        const logos = sec.content?.logos || [];
        return (
          <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="Logo Şeridi" active={active}>
            <div style={{ padding: device === 'mobile' ? '20px 16px' : '28px', textAlign: 'center', borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.03)'}` }}>
              {sec.content?.heading && <h4 style={{ fontSize: '11px', fontWeight: '700', opacity: 0.5, marginBottom: '14px', textTransform: 'uppercase', letterSpacing: '1px' }}>{sec.content.heading}</h4>}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '24px', flexWrap: 'wrap' }}>
                {logos.map((logo, i) => (
                  <div key={i} style={{ width: '60px', height: '30px', background: isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.05)', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '7px', color: '#94a3b8', fontWeight: '600' }}>
                    {logo.url ? <img src={logo.url} alt={logo.name} style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }} /> : logo.name}
                  </div>
                ))}
              </div>
            </div>
          </ElementorWrapper>
        );
      }

      // ─── SOCIAL LINKS BLOCK ───────────────────────────
      if (secType === 'social-links') {
        const links = sec.content?.links || [];
        const socialIcons = { Instagram: '📸', Facebook: '📘', Twitter: '🐦', YouTube: '▶️', LinkedIn: '💼', TikTok: '🎵' };
        return (
          <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="Sosyal Medya" active={active}>
            <div style={{ padding: '24px', textAlign: 'center', borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.03)'}` }}>
              {sec.content?.heading && <h4 style={{ fontSize: '12px', fontWeight: '700', marginBottom: '12px' }}>{sec.content.heading}</h4>}
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                {links.map((link, i) => (
                  <div key={i} style={{ width: '36px', height: '36px', borderRadius: '50%', background: isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', cursor: 'pointer', transition: 'all 0.2s', border: `1px solid ${isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.08)'}` }} title={link.platform}>
                    {socialIcons[link.platform] || '🔗'}
                  </div>
                ))}
              </div>
            </div>
          </ElementorWrapper>
        );
      }

      // ─── HTML EMBED BLOCK ─────────────────────────────
      if (secType === 'html-embed') {
        return (
          <ElementorWrapper key={sec.id} id={sec.id} index={idx} label="HTML Embed" active={active}>
            <div style={{ padding: '16px', borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.03)'}` }} dangerouslySetInnerHTML={{ __html: sec.content?.code || '' }} />
          </ElementorWrapper>
        );
      }

      return null;
    });
  };

  return (
    <div style={{
      background: tpl.bg,
      color: tpl.text,
      width: '100%',
      minHeight: '420px',
      fontFamily: fontFamily,
      transition: 'all 0.3s ease',
      overflow: 'hidden'
    }}>
      {/* Nav */}
      <header style={{
        padding: device === 'mobile' ? '12px 16px' : '14px 28px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.06)'}`
      }}>
        <span style={{ fontWeight: '800', fontSize: device === 'mobile' ? '13px' : '15px', color: accent }}>
          {resName || 'Restoran Adı'}
        </span>
        <nav style={{ display: 'flex', gap: '12px', fontSize: '11px', opacity: 0.8, alignItems: 'center' }}>
          {pages && pages.length > 0 ? (
            pages.map(p => (
              <span
                key={p.id}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectPage(p.id);
                }}
                style={{
                  cursor: 'pointer',
                  fontWeight: p.id === activePageId ? '700' : '400',
                  color: p.id === activePageId ? accent : 'inherit',
                  borderBottom: p.id === activePageId ? `2px solid ${accent}` : 'none',
                  paddingBottom: '2px',
                  transition: 'all 0.2s'
                }}
              >
                {p.title}
              </span>
            ))
          ) : (
            <>
              <span>Anasayfa</span>
              <span>Hikayemiz</span>
              <span>Menü</span>
              <span>İletişim</span>
            </>
          )}
        </nav>
      </header>

      {blocks && blocks.length > 0 ? (
        renderModularBlocks()
      ) : (
        <>
          {/* Classic fallback view */}
          {/* Hero */}
          <div style={{
            padding: device === 'mobile' ? '28px 16px' : '36px 28px 28px',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '10px',
            background: `linear-gradient(to bottom, ${accent}10, transparent)`
          }}>
            <h1 style={{
              fontSize: device === 'mobile' ? '18px' : '22px',
              fontWeight: '800',
              maxWidth: '320px',
              lineHeight: '1.25',
              margin: 0
            }}>
              {bannerText || 'Eşsiz Lezzetlerin Buluşma Noktası'}
            </h1>
            <div style={{ width: '36px', height: '2px', background: accent, borderRadius: '2px' }} />
            <p style={{ fontSize: '11px', opacity: 0.75, maxWidth: '300px', lineHeight: '1.6', margin: 0 }}>
              Taze malzemelerle hazırlanan usta ellerden çıkan eşsiz tabaklar.
            </p>
            {enableReservation && (
              <button style={{
                border: 'none',
                background: accent,
                color: isLight ? '#fff' : '#000',
                padding: '8px 18px',
                fontSize: '11px',
                borderRadius: '20px',
                fontWeight: '700',
                cursor: 'pointer',
                display: 'flex',
                gap: '5px',
                alignItems: 'center',
                marginTop: '6px'
              }}>
                <Calendar size={11} /> Masa Rezervasyonu Yap
              </button>
            )}
          </div>

          {/* About */}
          <div style={{
            padding: device === 'mobile' ? '16px' : '20px 28px',
            background: `${isLight ? 'rgba(0,0,0,0.03)' : 'rgba(255,255,255,0.03)'}`,
            borderTop: `1px solid ${isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.04)'}`,
            borderBottom: `1px solid ${isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.04)'}`
          }}>
            <h3 style={{ fontSize: '11px', fontWeight: '700', color: accent, marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '1px' }}>
              Hikayemiz
            </h3>
            <p style={{ fontSize: '10.5px', lineHeight: '1.65', opacity: 0.8, margin: 0 }}>
              {aboutText || 'Sol taraftan "Hakkımızda" alanını doldurunca buraya yansıyacaktır...'}
            </p>
          </div>

          {/* Menu snippet cards */}
          <div style={{ padding: device === 'mobile' ? '16px' : '20px 28px' }}>
            <h3 style={{ fontSize: '11px', fontWeight: '700', color: accent, marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '1px' }}>
              Öne Çıkan Lezzetler
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: device === 'mobile' ? '1fr' : '1fr 1fr 1fr', gap: '8px' }}>
              {['Bidolu Kebap', 'Lahmacun', 'Patlıcan Salatası'].map((item, i) => (
                <div key={i} style={{
                  background: tpl.cardBg,
                  border: `1px solid ${isLight ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.06)'}`,
                  borderRadius: '8px',
                  padding: '10px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px'
                }}>
                  <div style={{ width: '100%', height: '36px', background: `${accent}20`, borderRadius: '4px' }} />
                  <span style={{ fontSize: '10px', fontWeight: '600' }}>{item}</span>
                  <span style={{ fontSize: '9px', color: accent, fontWeight: '700' }}>89 ₺</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Footer */}
      <footer style={{
        padding: device === 'mobile' ? '12px 16px' : '14px 28px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '9.5px',
        opacity: 0.5,
        borderTop: `1px solid ${isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.04)'}`
      }}>
        <span>© {new Date().getFullYear()} {resName || 'Restoran'}</span>
        <div style={{ display: 'flex', gap: '8px' }}>
          {instagram && <span>📸 @{instagram}</span>}
          {facebook && <span>👤 /{facebook}</span>}
        </div>
      </footer>
    </div>
  );
}

export default function OfficialWebsite() {
  const { isMobile } = useResponsive();
  const [profileId, setProfileId] = useState(null);
  const [resName, setResName] = useState('');
  const [domain, setDomain] = useState('');
  const [bannerText, setBannerText] = useState('');
  const [aboutText, setAboutText] = useState('');
  const [instagram, setInstagram] = useState('');
  const [facebook, setFacebook] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('Modern Dark');
  const [enableReservation, setEnableReservation] = useState(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [previewDevice, setPreviewDevice] = useState('desktop');
  const [activeSection, setActiveSection] = useState('content'); // 'content' | 'design' | 'settings'

  // Canlı Editör states
  const [showElementorModal, setShowElementorModal] = useState(false);
  const [blocks, setBlocks] = useState([]);
  const [selectedBlockId, setSelectedBlockId] = useState(null);
  const [elementorDevice, setElementorDevice] = useState('desktop');
  
  // Multi-page states
  const [pages, setPages] = useState([{ id: 'home', title: 'Ana Sayfa', slug: 'home', blocks: [], seo: { title: '', description: '', keywords: '' } }]);
  const [activePageId, setActivePageId] = useState('home');
  const [showAddPageDialog, setShowAddPageDialog] = useState(false);
  const [newPageTitle, setNewPageTitle] = useState('');
  const [newPageSlug, setNewPageSlug] = useState('');
  
  // Media Library states
  const [showMediaLibrary, setShowMediaLibrary] = useState(false);
  const [mediaTarget, setMediaTarget] = useState(null); // { blockId, field, index }
  
  // Floating Layers state
  const [showLayersPopup, setShowLayersPopup] = useState(false);
  
  // Custom design states
  const [themeColor, setThemeColor] = useState('#6366f1');
  const [typography, setTypography] = useState('Sans-serif');
  const [elementorTab, setElementorTab] = useState('blocks'); // 'blocks' | 'presets' | 'pages' | 'upgrade'
  const [activePlan, setActivePlan] = useState('Growth');
  const [seoTitle, setSeoTitle] = useState('');
  const [seoDescription, setSeoDescription] = useState('');
  const [seoKeywords, setSeoKeywords] = useState('');
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  
  // Component Library states
  const [componentSearchQuery, setComponentSearchQuery] = useState('');
  const [activeComponentCategory, setActiveComponentCategory] = useState('all');

  useEffect(() => {
    fetchProfile();
    // Dynamically load premium fonts for page previews
    const link = document.createElement('link');
    link.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap';
    link.rel = 'stylesheet';
    document.head.appendChild(link);
    return () => {
      document.head.removeChild(link);
    };
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const res = await apiFetch(`${API_BASE}/restaurant-profile/`);
      const data = await res.json();
      if (data && data.length > 0) {
        const prof = data[0];
        setProfileId(prof.id);
        setResName(prof.name || '');
        setDomain(prof.website_custom_domain || '');
        setBannerText(prof.website_banner_text || '');
        setInstagram(prof.website_instagram || '');
        setFacebook(prof.website_facebook || '');
        setEnableReservation(prof.website_enable_reservation !== false);
        setThemeColor(prof.website_theme_color || '#6366f1');
        setActivePlan(prof.active_plan || 'Growth');
        
        // Parse template & typography
        const templateVal = prof.website_template || 'Modern Dark';
        const parts = templateVal.split('|');
        setSelectedTemplate(parts[0] || 'Modern Dark');
        setTypography(parts[1] || 'Sans-serif');

        // Modular blocks parsing
        const aboutRaw = prof.website_about_text || '';
        let loadedPages = [];
        let loadedBlocks = [];
        let loadedSeo = { title: '', description: '', keywords: '' };
        let activePgId = 'home';
        
        if (aboutRaw.trim().startsWith('{')) {
          try {
            const parsed = JSON.parse(aboutRaw);
            loadedPages = parsed.pages || [];
            if (loadedPages.length > 0) {
              activePgId = parsed.activePageId || loadedPages[0].id || 'home';
              const activePg = loadedPages.find(p => p.id === activePgId) || loadedPages[0];
              loadedBlocks = activePg.blocks || [];
              loadedSeo = activePg.seo || { title: '', description: '', keywords: '' };
            } else {
              loadedBlocks = parsed.blocks || [];
              loadedSeo = parsed.seo || { title: '', description: '', keywords: '' };
            }
          } catch (e) {
            console.error("JSON parse error for website_about_text", e);
          }
        } else if (aboutRaw.trim().startsWith('[')) {
          try {
            loadedBlocks = JSON.parse(aboutRaw);
          } catch (e) {
            console.error("JSON parse error for website_about_text", e);
          }
        }
        
        if (!loadedBlocks || loadedBlocks.length === 0) {
          loadedBlocks = [
            {
              id: 'hero-1',
              type: 'hero',
              title: 'Giriş',
              content: {
                banner: prof.website_banner_text || 'Eşsiz Lezzetlerin Buluşma Noktası',
                subtitle: 'Taze malzemelerle hazırlanan usta ellerden çıkan eşsiz tabaklar.',
                button_text: 'Masa Rezervasyonu Yap',
                button_url: '#reservation',
                layout: 'center'
              }
            },
            {
              id: 'about-1',
              type: 'about',
              title: 'Hikayemiz',
              content: {
                text: aboutRaw || 'Yılların getirdiği tecrübe and mutfak aşkıyla, misafirlerimize en taze ve en lezzetli yemekleri sunmak için her gün aynı heyecanla çalışıyoruz.',
                image: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=600&q=80',
                layout: 'left'
              }
            },
            {
              id: 'menu-1',
              type: 'menu',
              title: 'Öne Çıkan Lezzetler',
              content: {
                layout: 'grid',
                items: [
                  { name: 'Bidolu Kebap', description: 'Özel marine edilmiş kuzu kıyması, lavaş ve közlenmiş garnitür ile', price: '280', image: '' },
                  { name: 'Taş Fırın Lahmacun', description: 'Bol kıymalı harç, taze yeşillik ve limon ile', price: '85', image: '' },
                  { name: 'Ev Yapımı Künefe', description: 'Sıcak şerbet, eritilmiş peynir ve Antep fıstığı ile', price: '150', image: '' }
                ]
              }
            },
            {
              id: 'hours-1',
              type: 'hours',
              title: 'İletişim & Çalışma Saatleri',
              content: {
                layout: 'split',
                address: 'Atatürk Mah. Fatih Cad. No:42, Ataşehir/İstanbul',
                phone: '0216 555 44 33',
                times: [
                  { day: 'Pazartesi - Cuma', hours: '11:00 - 23:00' },
                  { day: 'Cumartesi - Pazar', hours: '11:00 - 00:00' }
                ]
              }
            },
            {
              id: 'reservation-1',
              type: 'reservation',
              title: 'Online Masa Rezervasyonu',
              content: {}
            }
          ];
        }

        if (!loadedPages || loadedPages.length === 0) {
          loadedPages = [{
            id: 'home',
            title: 'Ana Sayfa',
            slug: 'home',
            blocks: loadedBlocks,
            seo: loadedSeo
          }];
        }
        
        setPages(loadedPages);
        setActivePageId(activePgId);
        setBlocks(loadedBlocks);
        setSeoTitle(loadedSeo.title || '');
        setSeoDescription(loadedSeo.description || '');
        setSeoKeywords(loadedSeo.keywords || '');
        
        // Also keep local input for aboutText/bannerText fallback
        const heroBlock = loadedBlocks.find(b => b.type === 'hero');
        const aboutBlock = loadedBlocks.find(b => b.type === 'about');
        setBannerText(heroBlock ? heroBlock.content.banner : (prof.website_banner_text || ''));
        setAboutText(aboutBlock ? aboutBlock.content.text : aboutRaw);
      }
    } catch (err) { console.error(err); } 
    finally { setLoading(false); }
  };

  const handleSave = async (e) => {
    if (e) e.preventDefault();
    try {
      setSaving(true);
      if (profileId) {
        const updatedPages = pages.map(p => p.id === activePageId ? {
          ...p,
          blocks: blocks,
          seo: { title: seoTitle, description: seoDescription, keywords: seoKeywords }
        } : p);

        const savedData = {
          pages: updatedPages,
          activePageId: activePageId
        };
        
        const res = await apiFetch(`${API_BASE}/restaurant-profile/${profileId}/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            website_custom_domain: domain,
            website_banner_text: bannerText,
            website_about_text: JSON.stringify(savedData),
            website_instagram: instagram,
            website_facebook: facebook,
            website_template: `${selectedTemplate}|${typography}`,
            website_theme_color: themeColor,
            website_enable_reservation: enableReservation
          })
        });
        if (res.ok) {
          setSaved(true);
          setTimeout(() => setSaved(false), 2500);
          setPages(updatedPages);
        }
      }
    } catch (err) { console.error(err); } 
    finally { setSaving(false); }
  };

  const handleExportSettings = () => {
    const dataStr = JSON.stringify({
      version: '1.0',
      website_custom_domain: domain,
      website_banner_text: bannerText,
      website_about_text: JSON.stringify({ pages, activePageId }),
      website_instagram: instagram,
      website_facebook: facebook,
      website_template: `${selectedTemplate}|${typography}`,
      website_theme_color: themeColor,
      website_enable_reservation: enableReservation
    }, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `bidolu-pos-site-settings-${resName.toLowerCase().replace(/\s+/g, '-')}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleImportSettings = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const imported = JSON.parse(event.target.result);
        if (imported.website_banner_text !== undefined) setBannerText(imported.website_banner_text);
        if (imported.website_custom_domain !== undefined) setDomain(imported.website_custom_domain);
        if (imported.website_instagram !== undefined) setInstagram(imported.website_instagram);
        if (imported.website_facebook !== undefined) setFacebook(imported.website_facebook);
        if (imported.website_theme_color !== undefined) setThemeColor(imported.website_theme_color);
        if (imported.website_enable_reservation !== undefined) setEnableReservation(imported.website_enable_reservation);
        
        if (imported.website_template) {
          const parts = imported.website_template.split('|');
          setSelectedTemplate(parts[0]);
          if (parts[1]) setTypography(parts[1]);
        }
        
        if (imported.website_about_text) {
          const parsed = JSON.parse(imported.website_about_text);
          if (parsed.pages) {
            setPages(parsed.pages);
            const activePage = parsed.pages.find(p => p.id === parsed.activePageId) || parsed.pages[0];
            if (activePage) {
              setActivePageId(activePage.id);
              setBlocks(activePage.blocks || []);
            }
          }
        }
        alert('Site ayarları başarıyla içe aktarıldı. Kaydetmek için lütfen "Değişiklikleri Kaydet" butonuna basın.');
      } catch (err) {
        alert('Geçersiz dosya formatı.');
        console.error(err);
      }
    };
    reader.readAsText(file);
    e.target.value = ''; // Reset file input
  };

  const handleDeleteSettings = () => {
    if (!window.confirm('Tüm site ayarlarını sıfırlamak ve tasarım bloklarını silmek istediğinize emin misiniz? Bu işlem geri alınamaz.')) return;
    
    setBannerText('');
    setDomain('');
    setInstagram('');
    setFacebook('');
    setThemeColor('#6366f1');
    setEnableReservation(true);
    setSelectedTemplate('Modern Dark');
    setTypography('Sans-serif');
    setBlocks([]);
    setPages([{ id: 'home', title: 'Ana Sayfa', slug: 'home', blocks: [], seo: { title: '', description: '', keywords: '' } }]);
    setActivePageId('home');
    
    alert('Tüm ayarlar sıfırlandı. Değişiklikleri kalıcı yapmak için lütfen "Değişiklikleri Kaydet" butonuna basın.');
  };

  const simulateUpgrade = async () => {
    try {
      setSaving(true);
      if (profileId) {
        const res = await apiFetch(`${API_BASE}/restaurant-profile/${profileId}/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            active_plan: 'Enterprise'
          })
        });
        if (res.ok) {
          setActivePlan('Enterprise');
          setShowUpgradeModal(false);
          alert("Planınız başarıyla 'Profesyonel Web Sitesi' (Kurumsal) planına yükseltildi! Çoklu sayfa ekleme ve gelişmiş SEO ayarları aktif hale getirildi.");
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const simulateDowngrade = async () => {
    try {
      setSaving(true);
      if (profileId) {
        const res = await apiFetch(`${API_BASE}/restaurant-profile/${profileId}/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            active_plan: 'Growth'
          })
        });
        if (res.ok) {
          setActivePlan('Growth');
          alert("Planınız başarıyla 'Growth' (Standart) planına düşürüldü. Çoklu sayfa ve SEO ayarları kısıtlandı.");
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleDropBlock = (fromIndex, toIndex) => {
    if (fromIndex === toIndex) return;
    const updatedBlocks = [...blocks];
    const [dragged] = updatedBlocks.splice(fromIndex, 1);
    updatedBlocks.splice(toIndex, 0, dragged);
    setBlocks(updatedBlocks);
    syncClassicStatesFromBlocks(updatedBlocks);
  };

  const applyPageTemplate = (tplName) => {
    let tplBlocks = [];
    if (tplName === 'gurme') {
      tplBlocks = [
        {
          id: 'hero-gurme',
          type: 'hero',
          title: 'Modern Gurme Giriş',
          content: {
            banner: 'Gurme Lezzetlerin Eşsiz Buluşma Noktası',
            subtitle: 'En taze yerel malzemeler ve usta şeflerimizin elinden çıkan unutulmaz lezzetler.',
            button_text: 'Rezervasyon Yap',
            button_url: '#reservation',
            layout: 'split',
            image: 'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=800&q=80'
          }
        },
        {
          id: 'about-gurme',
          type: 'about',
          title: 'Mutfak Felsefemiz',
          content: {
            text: 'Yemek yapmayı bir sanat, misafir ağırlamayı ise bir tutku olarak görüyoruz. Nesiller boyu aktarılan tariflerimizi modern gastronomi teknikleriyle harmanlayarak sizlere sunuyoruz.',
            image: 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=600&q=80',
            layout: 'right'
          }
        },
        {
          id: 'menu-gurme',
          type: 'menu',
          title: 'Şefin Seçtikleri',
          content: {
            layout: 'grid',
            items: [
              { name: 'Közlenmiş Kuzu İncik', description: '24 saat ağır ateşte pişmiş kuzu incik, kremalı patates püresi ile', price: '420', image: 'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=300&q=80' }
            ]
          }
        },
        {
          id: 'testimonials-gurme',
          type: 'testimonials',
          title: 'Gurme Deneyimleri',
          content: {
            layout: 'grid',
            quotes: [
              { name: 'Murat K.', text: "İstanbul'da yediğim en iyi kuzu incikti. Servis kalitesi ve atmosfer tek kelimeyle mükemmel.", rating: 5 }
            ]
          }
        },
        {
          id: 'hours-gurme',
          type: 'hours',
          title: 'Ulaşım ve Çalışma Saatleri',
          content: {
            layout: 'split',
            address: 'Harbiye Mah. Vali Konağı Cad. No:12, Şişli/İstanbul',
            phone: '0212 234 56 78',
            times: [
              { day: 'Pazartesi - Cuma', hours: '12:00 - 23:30' },
              { day: 'Cumartesi - Pazar', hours: '12:00 - 00:30' }
            ]
          }
        },
        {
          id: 'reservation-gurme',
          type: 'reservation',
          title: 'Masa Rezervasyonu',
          content: {}
        }
      ];
      setSelectedTemplate('Elegant Gold');
      setThemeColor('#d4af37');
      setTypography('Serif');
    } else if (tplName === 'hizli') {
      tplBlocks = [
        {
          id: 'hero-hizli',
          type: 'hero',
          title: 'Hızlı Giriş',
          content: {
            banner: 'Çıtır Lezzetler & Hızlı Servis',
            subtitle: 'Sıcak, hızlı ve taptaze! En sevdiğiniz sokak lezzetleri ve cafe spesiyalleri anında kapınızda veya masanızda.',
            button_text: 'Hemen Sipariş Ver / Rezervasyon',
            button_url: '#reservation',
            layout: 'glass',
            image: 'https://images.unsplash.com/photo-1561758033-d89a9ad46330?auto=format&fit=crop&w=800&q=80'
          }
        },
        {
          id: 'menu-hizli',
          type: 'menu',
          title: 'Sevilen Sokak Lezzetleri',
          content: {
            layout: 'list',
            items: [
              { name: 'Bidolu Double Burger', description: '180gr dana köfte, cheddar peyniri, karamelize soğan ve özel sos', price: '240', image: '' },
              { name: 'Çıtır Patates Sepeti', description: 'Baharatlı çıtır patates, sarımsaklı mayonez ve barbekü sos ile', price: '110', image: '' }
            ]
          }
        },
        {
          id: 'hours-hizli',
          type: 'hours',
          title: 'Çalışma Saatlerimiz',
          content: {
            layout: 'center',
            address: 'Kadıköy Barlar Sokağı No:15, Kadıköy/İstanbul',
            phone: '0216 333 22 11',
            times: [
              { day: 'Hafta İçi', hours: '10:00 - 22:00' },
              { day: 'Hafta Sonu', hours: '10:00 - 00:00' }
            ]
          }
        },
        {
          id: 'reservation-hizli',
          type: 'reservation',
          title: 'Hızlı Rezervasyon',
          content: {}
        }
      ];
      setSelectedTemplate('Cozy Retro');
      setThemeColor('#d96a3b');
      setTypography('Sans-serif');
    } else if (tplName === 'minimal') {
      tplBlocks = [
        {
          id: 'hero-minimal',
          type: 'hero',
          title: 'Minimalist Giriş',
          content: {
            banner: 'Sade ve Doğal Lezzetler',
            subtitle: 'Karmaşadan uzak, sadece lezzete odaklanan yalın mutfak anlayışı.',
            button_text: 'Bize Katılın',
            button_url: '#reservation',
            layout: 'center'
          }
        },
        {
          id: 'about-minimal',
          type: 'about',
          title: 'Yalın Hikayemiz',
          content: {
            text: 'Gereksiz her şeyden arındık. Tabağınıza gelen her bir malzemenin kendi doğal lezzetini ön plana çıkarmayı hedefleyen, doğaya ve malzemeye saygılı minimalist bir restoran deneyimi sunuyoruz.',
            image: '',
            layout: 'minimal'
          }
        },
        {
          id: 'menu-minimal',
          type: 'menu',
          title: 'Yalın Menü',
          content: {
            layout: 'minimal',
            items: [
              { name: 'Fırınlanmış Pancar Salatası', description: 'Keçi peyniri, ceviz ve zeytinyağı sosu ile', price: '165' }
            ]
          }
        },
        {
          id: 'hours-minimal',
          type: 'hours',
          title: 'Ziyaret Saatleri',
          content: {
            layout: 'split',
            address: 'Bebek Mah. Cevdetpaşa Cad. No:80, Beşiktaş/İstanbul',
            phone: '0212 255 66 77',
            times: [
              { day: 'Salı - Pazar', hours: '12:00 - 22:00' },
              { day: 'Pazartesi', hours: 'Kapalı' }
            ]
          }
        }
      ];
      setSelectedTemplate('Minimal Light');
      setThemeColor('#10b981');
      setTypography('Outfit');
    }
    setBlocks(tplBlocks);
    syncClassicStatesFromBlocks(tplBlocks);
  };

  const syncClassicStatesFromBlocks = (updatedBlocks) => {
    const heroBlock = updatedBlocks.find(b => b.type === 'hero');
    if (heroBlock && heroBlock.content && heroBlock.content.banner) {
      setBannerText(heroBlock.content.banner);
    }
    const aboutBlock = updatedBlocks.find(b => b.type === 'about');
    if (aboutBlock && aboutBlock.content && aboutBlock.content.text) {
      setAboutText(aboutBlock.content.text);
    }
  };

  const updateActivePageBlocks = (updatedBlocks) => {
    setBlocks(updatedBlocks);
    setPages(prev => prev.map(p => p.id === activePageId ? { ...p, blocks: updatedBlocks } : p));
  };

  const handleSelectPage = (pageId) => {
    // Sync current editor states to the pages state first
    setPages(prev => prev.map(p => p.id === activePageId ? {
      ...p,
      blocks: blocks,
      seo: { title: seoTitle, description: seoDescription, keywords: seoKeywords }
    } : p));

    setActivePageId(pageId);
    const targetPage = pages.find(p => p.id === pageId);
    if (targetPage) {
      setBlocks(targetPage.blocks || []);
      const pageSeo = targetPage.seo || { title: '', description: '', keywords: '' };
      setSeoTitle(pageSeo.title || '');
      setSeoDescription(pageSeo.description || '');
      setSeoKeywords(pageSeo.keywords || '');
      
      const heroBlock = (targetPage.blocks || []).find(b => b.type === 'hero');
      const aboutBlock = (targetPage.blocks || []).find(b => b.type === 'about');
      setBannerText(heroBlock ? heroBlock.content.banner : '');
      setAboutText(aboutBlock ? aboutBlock.content.text : '');
    }
    setSelectedBlockId(null);
  };

  const handleBannerTextChange = (val) => {
    setBannerText(val);
    const newBlocks = blocks.map(b => b.type === 'hero' ? { ...b, content: { ...b.content, banner: val } } : b);
    updateActivePageBlocks(newBlocks);
  };

  const handleAboutTextChange = (val) => {
    setAboutText(val);
    const newBlocks = blocks.map(b => b.type === 'about' ? { ...b, content: { ...b.content, text: val } } : b);
    updateActivePageBlocks(newBlocks);
  };

  const moveBlock = (index, direction) => {
    const newIndex = index + direction;
    if (newIndex < 0 || newIndex >= blocks.length) return;
    const newBlocks = [...blocks];
    const temp = newBlocks[index];
    newBlocks[index] = newBlocks[newIndex];
    newBlocks[newIndex] = temp;
    updateActivePageBlocks(newBlocks);
    syncClassicStatesFromBlocks(newBlocks);
  };

  const deleteBlock = (id) => {
    const newBlocks = blocks.filter(b => b.id !== id);
    updateActivePageBlocks(newBlocks);
    if (selectedBlockId === id) setSelectedBlockId(null);
    syncClassicStatesFromBlocks(newBlocks);
  };

  const addBlock = (type) => {
    const id = `${type}-${Date.now()}`;
    let title = '';
    let content = {};
    
    if (type === 'hero') {
      title = 'Giriş';
      content = {
        banner: 'Eşsiz Lezzetlerin Buluşma Noktası',
        subtitle: 'Taze malzemelerle hazırlanan usta ellerden çıkan eşsiz tabaklar.',
        button_text: 'Masa Rezervasyonu Yap',
        button_url: '#reservation'
      };
    } else if (type === 'about') {
      title = 'Hikayemiz';
      content = {
        text: 'Yılların getirdiği tecrübe ve mutfak aşkıyla, misafirlerimize en taze ve en lezzetli yemekleri sunmak için her gün aynı heyecanla çalışıyoruz.',
        image: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=600&q=80',
        layout: 'left'
      };
    } else if (type === 'menu') {
      title = 'Öne Çıkan Lezzetler';
      content = {
        items: [
          { name: 'Yeni Yemek', description: 'Yemeğin açıklaması', price: '120', image: '' }
        ]
      };
    } else if (type === 'testimonials') {
      title = 'Misafir Yorumları';
      content = {
        quotes: [
          { name: 'Ahmet Y.', text: 'Harika bir deneyimdi!', rating: 5 }
        ]
      };
    } else if (type === 'hours') {
      title = 'Saatler & İletişim';
      content = {
        address: 'Restoran Adresi',
        phone: '0212 000 00 00',
        times: [
          { day: 'Pazartesi - Pazar', hours: '09:00 - 22:00' }
        ]
      };
    } else if (type === 'reservation') {
      title = 'Masa Rezervasyonu';
      content = {};
    }
    
    const newBlocks = [...blocks, { id, type, title, content }];
    updateActivePageBlocks(newBlocks);
    setSelectedBlockId(id);
    syncClassicStatesFromBlocks(newBlocks);
  };

  const updateBlockContent = (id, newContent) => {
    const newBlocks = blocks.map(b => b.id === id ? { ...b, content: { ...b.content, ...newContent } } : b);
    updateActivePageBlocks(newBlocks);
    syncClassicStatesFromBlocks(newBlocks);
  };

  const updateBlockTitle = (id, newTitle) => {
    const newBlocks = blocks.map(b => b.id === id ? { ...b, title: newTitle } : b);
    updateActivePageBlocks(newBlocks);
  };

  const openMediaLibrary = (blockId, field, index = null) => {
    setMediaTarget({ blockId, field, index });
    setShowMediaLibrary(true);
  };

  const selectImageFromLibrary = (url) => {
    if (!mediaTarget) return;
    const { blockId, field, index } = mediaTarget;
    
    if (field === 'image') {
      updateBlockContent(blockId, { image: url });
    } else if (field === 'menuItemImage' && index !== null) {
      const targetBlock = blocks.find(b => b.id === blockId);
      if (targetBlock && targetBlock.content && targetBlock.content.items) {
        const newItems = [...targetBlock.content.items];
        newItems[index] = { ...newItems[index], image: url };
        updateBlockContent(blockId, { items: newItems });
      }
    }
    setShowMediaLibrary(false);
    setMediaTarget(null);
  };

  const renderMediaLibraryModal = () => {
    if (!showMediaLibrary) return null;
    
    const PRESET_IMAGES = [
      { title: 'Kuzu İncik & Kebap', url: 'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=600&q=80' },
      { title: 'Taş Fırın Pide & Lahmacun', url: 'https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=600&q=80' },
      { title: 'Gurme Burger & Patates', url: 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&q=80' },
      { title: 'Şef Sunum Tabağı', url: 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=600&q=80' },
      { title: 'Lüks Restoran İç Mekan', url: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=600&q=80' },
      { title: 'Geleneksel Serpme Kahvaltı', url: 'https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=600&q=80' },
      { title: 'Izgara Biftek', url: 'https://images.unsplash.com/photo-1546964124-0cce460f38ef?auto=format&fit=crop&w=600&q=80' },
      { title: 'Deniz Ürünleri Tava', url: 'https://images.unsplash.com/photo-1534080391025-09795d197a5b?auto=format&fit=crop&w=600&q=80' },
      { title: 'Taze Domatesli Makarna', url: 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=600&q=80' },
      { title: 'Çikolatalı Sıcak Tatlı', url: 'https://images.unsplash.com/photo-1551024601-bec78aea704b?auto=format&fit=crop&w=600&q=80' }
    ];

    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(15, 23, 42, 0.4)',
        backdropFilter: 'blur(8px)',
        zIndex: 100001,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}>
        <div style={{
          background: '#ffffff',
          border: '1px solid rgba(0, 0, 0, 0.06)',
          borderRadius: '16px',
          width: '100%',
          maxWidth: '800px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.08)'
        }}>
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 24px', borderBottom: '1px solid rgba(0, 0, 0, 0.06)' }}>
            <h3 style={{ fontSize: '15px', fontWeight: '800', color: '#0f172a', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Image size={18} style={{ color: '#4f46e5' }} /> Medya Kütüphanesi
            </h3>
            <button
              type="button"
              onClick={() => setShowMediaLibrary(false)}
              style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '20px', fontWeight: 'bold' }}
            >
              &times;
            </button>
          </div>

          {/* Content */}
          <div style={{ padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px', flex: 1 }}>
            {/* Custom URL input */}
            <div>
              <label style={{ display: 'block', fontSize: '11px', color: '#475569', fontWeight: '600', marginBottom: '8px' }}>Özel Görsel URL'si Girin</label>
              <div style={{ display: 'flex', gap: '10px' }}>
                <input
                  id="custom-media-url"
                  type="text"
                  placeholder="https://images.unsplash.com/..."
                  style={{ flex: 1, background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none' }}
                />
                <button
                  type="button"
                  onClick={() => {
                    const el = document.getElementById('custom-media-url');
                    if (el && el.value.trim()) {
                      selectImageFromLibrary(el.value.trim());
                    } else {
                      alert("Lütfen geçerli bir URL girin.");
                    }
                  }}
                  style={{ background: '#4f46e5', border: 'none', color: '#0f172a', padding: '0 16px', borderRadius: '8px', fontWeight: '750', fontSize: '12px', cursor: 'pointer' }}
                >
                  Görseli Kullan
                </button>
              </div>
            </div>

            {/* Grid of presets */}
            <div>
              <h4 style={{ fontSize: '11px', color: '#475569', fontWeight: '800', textTransform: 'uppercase', marginBottom: '12px', letterSpacing: '0.05em' }}>Hazır Gurme Görseller</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: '12px' }}>
                {PRESET_IMAGES.map((img, idx) => (
                  <div
                    key={idx}
                    onClick={() => selectImageFromLibrary(img.url)}
                    style={{
                      background: '#ffffff',
                      border: '1px solid rgba(0, 0, 0, 0.06)',
                      borderRadius: '10px',
                      overflow: 'hidden',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      position: 'relative'
                    }}
                    onMouseOver={(e) => { e.currentTarget.style.borderColor = '#4f46e5'; }}
                    onMouseOut={(e) => { e.currentTarget.style.borderColor = 'rgba(0, 0, 0, 0.06)'; }}
                  >
                    <div style={{ height: '90px', position: 'relative' }}>
                      <img src={img.url} alt={img.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    </div>
                    <div style={{ padding: '6px 8px', textAlign: 'center' }}>
                      <span style={{ fontSize: '10.5px', fontWeight: '700', color: '#475569', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {img.title}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderLayersPopup = () => {
    if (!showLayersPopup) return null;

    return (
      <div style={{
        position: 'fixed',
        bottom: '30px',
        left: '420px',
        width: '320px',
        maxHeight: '450px',
        background: 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(79, 70, 229, 0.15)',
        borderRadius: '16px',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.08)',
        zIndex: 999,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          background: '#ffffff',
          padding: '12px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid rgba(0, 0, 0, 0.06)',
          cursor: 'move'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={14} style={{ color: '#4f46e5' }} />
            <span style={{ fontSize: '11px', fontWeight: '800', color: '#0f172a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Katmanlar (Popup)</span>
          </div>
          <button
            type="button"
            onClick={() => setShowLayersPopup(false)}
            style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '14px', fontWeight: 'bold' }}
          >
            &times;
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '16px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {blocks.length === 0 ? (
            <p style={{ fontSize: '11px', color: '#64748b', fontStyle: 'italic', textAlign: 'center', margin: 0, padding: '20px' }}>
              Bu sayfada henüz bir katman bulunmuyor.
            </p>
          ) : (
            blocks.map((block, i) => (
              <div
                key={block.id}
                onClick={() => setSelectedBlockId(block.id)}
                style={{
                  background: '#ffffff',
                  border: selectedBlockId === block.id ? '1px solid #4f46e5' : '1px solid rgba(0, 0, 0, 0.06)',
                  padding: '10px',
                  borderRadius: '8px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.01)'
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  <span style={{ fontSize: '12px', fontWeight: '700', color: '#0f172a' }}>{block.title}</span>
                  <span style={{ fontSize: '9px', color: '#4f46e5', textTransform: 'uppercase', fontWeight: '600' }}>{block.type}</span>
                </div>
                <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }} onClick={e => e.stopPropagation()}>
                  <button
                    type="button"
                    onClick={() => moveBlock(i, -1)}
                    disabled={i === 0}
                    style={{ background: 'rgba(0,0,0,0.03)', border: 'none', color: '#475569', cursor: 'pointer', padding: '3px', borderRadius: '4px', opacity: i === 0 ? 0.3 : 1 }}
                  >
                    <ChevronUp size={12} />
                  </button>
                  <button
                    type="button"
                    onClick={() => moveBlock(i, 1)}
                    disabled={i === blocks.length - 1}
                    style={{ background: 'rgba(0,0,0,0.03)', border: 'none', color: '#475569', cursor: 'pointer', padding: '3px', borderRadius: '4px', opacity: i === blocks.length - 1 ? 0.3 : 1 }}
                  >
                    <ChevronDown size={12} />
                  </button>
                  <button
                    type="button"
                    onClick={() => deleteBlock(block.id)}
                    style={{ background: 'rgba(239, 68, 68, 0.1)', border: 'none', color: '#f87171', cursor: 'pointer', padding: '3px', borderRadius: '4px' }}
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    );
  };

  const renderElementorModal = () => {
    if (!showElementorModal) return null;

    const selectedBlock = blocks.find(b => b.id === selectedBlockId);

    // ══════════════════════════════════════════════════════════
    // COMPONENT CATEGORIES — Navigation grid
    // ══════════════════════════════════════════════════════════
    const COMPONENT_CATEGORIES = [
      { id: 'all', label: 'Tümü', icon: Grid3X3, color: '#6366f1' },
      { id: 'hero', label: 'Hero / Giriş', icon: Sparkles, color: '#818cf8' },
      { id: 'about', label: 'Hakkımızda', icon: BookOpen, color: '#fb923c' },
      { id: 'menu', label: 'Menü', icon: UtensilsCrossed, color: '#f59e0b' },
      { id: 'testimonials', label: 'Yorumlar', icon: Quote, color: '#4ade80' },
      { id: 'contact', label: 'İletişim', icon: MapPin, color: '#60a5fa' },
      { id: 'reservation', label: 'Rezervasyon', icon: CalendarCheck, color: '#a78bfa' },
      { id: 'gallery', label: 'Galeri', icon: ImagePlus, color: '#f472b6' },
      { id: 'cta', label: 'CTA', icon: MousePointerClick, color: '#fb7185' },
      { id: 'stats', label: 'İstatistik', icon: BarChart3, color: '#2dd4bf' },
      { id: 'extras', label: 'Özel Bloklar', icon: Puzzle, color: '#94a3b8' }
    ];

    // ══════════════════════════════════════════════════════════
    // COMPONENT LIBRARY — 60+ pre-built components
    // ══════════════════════════════════════════════════════════
    const COMPONENT_LIBRARY = [
      // ─── HERO / GİRİŞ ────────────────────────────────
      { id: 'hero-center', type: 'hero', layout: 'center', category: 'hero', label: 'Ortalanmış Giriş', desc: 'Klasik sade banner yerleşimi', previewBg: '#312e81', previewAccent: '#818cf8', tags: ['klasik', 'basit'], isPremium: false },
      { id: 'hero-split', type: 'hero', layout: 'split', category: 'hero', label: 'Bölünmüş Giriş', desc: 'Görselli iki sütunlu modern giriş', previewBg: '#064e3b', previewAccent: '#34d399', tags: ['modern', 'görsel'], isPremium: false },
      { id: 'hero-glass', type: 'hero', layout: 'glass', category: 'hero', label: 'Cam Efektli Giriş', desc: 'Bulanık cam tasarımlı premium giriş', previewBg: '#1e1b4b', previewAccent: '#a78bfa', tags: ['premium', 'cam'], isPremium: false },
      { id: 'hero-video', type: 'hero', layout: 'video', category: 'hero', label: 'Video Arkaplan', desc: 'Arka planda dönen video ile büyüleyici giriş', previewBg: '#0c0a09', previewAccent: '#ef4444', tags: ['video', 'premium', 'animasyon'], isPremium: false },
      { id: 'hero-parallax', type: 'hero', layout: 'parallax', category: 'hero', label: 'Parallax Giriş', desc: 'Derinlik efektli kaydırmalı giriş alanı', previewBg: '#1a2e05', previewAccent: '#84cc16', tags: ['parallax', 'modern'], isPremium: false },
      { id: 'hero-gradient', type: 'hero', layout: 'gradient', category: 'hero', label: 'Gradient Giriş', desc: 'Canlı renk geçişli etkileyici giriş', previewBg: '#4c1d95', previewAccent: '#c084fc', tags: ['gradient', 'renkli'], isPremium: false },
      { id: 'hero-minimal', type: 'hero', layout: 'minimal-hero', category: 'hero', label: 'Minimalist Giriş', desc: 'Fazlalıklardan arınmış sade giriş', previewBg: '#f5f5f4', previewAccent: '#78716c', tags: ['minimal', 'sade'], isPremium: false },
      { id: 'hero-animated', type: 'hero', layout: 'animated-text', category: 'hero', label: 'Animasyonlu Metin', desc: 'Kelime kelime beliren etkileyici başlık', previewBg: '#0f172a', previewAccent: '#38bdf8', tags: ['animasyon', 'text', 'premium'], isPremium: true },

      // ─── HAKKIMIZDA ───────────────────────────────────
      { id: 'about-left', type: 'about', layout: 'left', category: 'about', label: 'Sol Görselli Hikaye', desc: 'Görsel ve restoran hikayesi yan yana', previewBg: '#451a03', previewAccent: '#fb923c', tags: ['görsel', 'hikaye'], isPremium: false },
      { id: 'about-right', type: 'about', layout: 'right', category: 'about', label: 'Sağ Görselli Hikaye', desc: 'Metin solda, görsel sağda', previewBg: '#3b0764', previewAccent: '#d946ef', tags: ['görsel', 'hikaye'], isPremium: false },
      { id: 'about-minimal', type: 'about', layout: 'minimal', category: 'about', label: 'Sade Hakkımızda', desc: 'Görselsiz tipografik hikaye', previewBg: '#111827', previewAccent: '#94a3b8', tags: ['minimal', 'text'], isPremium: false },
      { id: 'about-timeline', type: 'about', layout: 'timeline', category: 'about', label: 'Zaman Çizelgesi', desc: 'Yıllara göre restoran geçmişi', previewBg: '#0c4a6e', previewAccent: '#7dd3fc', tags: ['tarih', 'timeline'], isPremium: false },
      { id: 'about-team', type: 'about', layout: 'team-grid', category: 'about', label: 'Ekibimiz', desc: 'Şef ve çalışan tanıtım kartları', previewBg: '#1e3a5f', previewAccent: '#93c5fd', tags: ['ekip', 'takım'], isPremium: false },
      { id: 'about-story', type: 'about', layout: 'story-cards', category: 'about', label: 'Hikaye Kartları', desc: 'Kartlarla anlatılan restoran hikayesi', previewBg: '#365314', previewAccent: '#bef264', tags: ['hikaye', 'kart'], isPremium: true },

      // ─── MENÜ / YEMEKLER ──────────────────────────────
      { id: 'menu-grid', type: 'menu', layout: 'grid', category: 'menu', label: 'Yemek Izgarası', desc: 'Resimli 3\'lü yemek kartları', previewBg: '#3f1a01', previewAccent: '#f59e0b', tags: ['grid', 'kart', 'resim'], isPremium: false },
      { id: 'menu-list', type: 'menu', layout: 'list', category: 'menu', label: 'Yemek Listesi', desc: 'Şık restoran fiyat listesi', previewBg: '#1c1917', previewAccent: '#a8a29e', tags: ['liste', 'fiyat'], isPremium: false },
      { id: 'menu-minimal', type: 'menu', layout: 'minimal', category: 'menu', label: 'Minimal Menü', desc: 'Görselsiz sade menü düzeni', previewBg: '#18181b', previewAccent: '#71717a', tags: ['minimal', 'sade'], isPremium: false },
      { id: 'menu-tabbed', type: 'menu', layout: 'tabbed', category: 'menu', label: 'Sekmeli Menü', desc: 'Kategorilerle ayrılan tab menü', previewBg: '#422006', previewAccent: '#fbbf24', tags: ['tab', 'kategori'], isPremium: false },
      { id: 'menu-showcase', type: 'menu', layout: 'image-showcase', category: 'menu', label: 'Görsel Vitrin', desc: 'Büyük fotoğraflarla yemek vitrini', previewBg: '#1e1b4b', previewAccent: '#c4b5fd', tags: ['görsel', 'büyük', 'vitrin'], isPremium: false },
      { id: 'menu-featured', type: 'menu', layout: 'featured-dish', category: 'menu', label: 'Öne Çıkan Yemek', desc: 'Tek yemek hero-style tanıtım', previewBg: '#7c2d12', previewAccent: '#fb923c', tags: ['featured', 'tek', 'özel'], isPremium: true },
      { id: 'menu-price-table', type: 'menu', layout: 'price-table', category: 'menu', label: 'Fiyat Tablosu', desc: 'Düzenli tablo formatında menü', previewBg: '#064e3b', previewAccent: '#6ee7b7', tags: ['tablo', 'fiyat'], isPremium: false },

      // ─── YORUMLAR ─────────────────────────────────────
      { id: 'testimonials-grid', type: 'testimonials', layout: 'grid', category: 'testimonials', label: 'Yorum Kartları', desc: 'Izgara düzeninde yorum kartları', previewBg: '#14532d', previewAccent: '#4ade80', tags: ['grid', 'kart'], isPremium: false },
      { id: 'testimonials-carousel', type: 'testimonials', layout: 'carousel', category: 'testimonials', label: 'Yorum Slaytı', desc: 'Kaydırmalı yorum slider\'ı', previewBg: '#1e3a5f', previewAccent: '#38bdf8', tags: ['slider', 'carousel'], isPremium: false },
      { id: 'testimonials-highlight', type: 'testimonials', layout: 'single-highlight', category: 'testimonials', label: 'Öne Çıkan Yorum', desc: 'Tek büyük öne çıkan yorum', previewBg: '#4a1d96', previewAccent: '#c084fc', tags: ['tek', 'highlight'], isPremium: false },
      { id: 'testimonials-rating', type: 'testimonials', layout: 'rating-bars', category: 'testimonials', label: 'Puan Çubukları', desc: 'Yıldız puanlı değerlendirme barları', previewBg: '#78350f', previewAccent: '#fbbf24', tags: ['puan', 'bar'], isPremium: false },
      { id: 'testimonials-social', type: 'testimonials', layout: 'social-proof', category: 'testimonials', label: 'Sosyal Kanıt', desc: 'Platform puanları ve sayılar', previewBg: '#0f172a', previewAccent: '#f43f5e', tags: ['sosyal', 'sayı'], isPremium: true },

      // ─── İLETİŞİM & SAATLER ──────────────────────────
      { id: 'hours-split', type: 'hours', layout: 'split', category: 'contact', label: 'İletişim & Saatler', desc: 'Detaylı adres ve çalışma saatleri', previewBg: '#172554', previewAccent: '#60a5fa', tags: ['adres', 'saat'], isPremium: false },
      { id: 'hours-compact', type: 'hours', layout: 'compact', category: 'contact', label: 'Kompakt İletişim', desc: 'Tek satırda özet iletişim bilgisi', previewBg: '#1e293b', previewAccent: '#94a3b8', tags: ['kompakt', 'sade'], isPremium: false },
      { id: 'hours-centered', type: 'hours', layout: 'centered', category: 'contact', label: 'Ortalanmış İletişim', desc: 'Ortalanmış büyük iletişim kartı', previewBg: '#0e7490', previewAccent: '#67e8f9', tags: ['ortala', 'kart'], isPremium: false },
      { id: 'hours-card', type: 'hours', layout: 'card-style', category: 'contact', label: 'İletişim Kartları', desc: 'Ayrı kartlarda adres, telefon, saat', previewBg: '#374151', previewAccent: '#d1d5db', tags: ['kart', 'ayrı'], isPremium: false },
      { id: 'hours-banner', type: 'hours', layout: 'full-width-banner', category: 'contact', label: 'Tam Genişlik Banner', desc: 'Tam ekran iletişim şeridi', previewBg: '#7c3aed', previewAccent: '#c4b5fd', tags: ['banner', 'tam'], isPremium: false },

      // ─── REZERVASYON ──────────────────────────────────
      { id: 'reservation-simple', type: 'reservation', layout: 'simple', category: 'reservation', label: 'Basit Form', desc: 'Ad, telefon ve tarih formu', previewBg: '#4c1d95', previewAccent: '#a78bfa', tags: ['basit', 'form'], isPremium: false },
      { id: 'reservation-time-slots', type: 'reservation', layout: 'time-slots', category: 'reservation', label: 'Saat Seçimli', desc: 'Saat dilimi grid\'i ile rezervasyon', previewBg: '#065f46', previewAccent: '#6ee7b7', tags: ['saat', 'grid'], isPremium: false },
      { id: 'reservation-party', type: 'reservation', layout: 'party-size', category: 'reservation', label: 'Kişi Sayılı', desc: 'Kişi sayısı ve masa tercihi', previewBg: '#1e3a5f', previewAccent: '#7dd3fc', tags: ['kişi', 'masa'], isPremium: false },
      { id: 'reservation-premium', type: 'reservation', layout: 'premium-booking', category: 'reservation', label: 'Premium Rezervasyon', desc: 'Çok adımlı profesyonel form', previewBg: '#312e81', previewAccent: '#818cf8', tags: ['premium', 'adım'], isPremium: true },

      // ─── GALERİ ───────────────────────────────────────
      { id: 'gallery-masonry', type: 'gallery', layout: 'masonry', category: 'gallery', label: 'Masonry Galeri', desc: 'Pinterest tarzı galeri ızgarası', previewBg: '#831843', previewAccent: '#f9a8d4', tags: ['masonry', 'pinterest'], isPremium: false },
      { id: 'gallery-grid', type: 'gallery', layout: 'lightbox-grid', category: 'gallery', label: 'Lightbox Galeri', desc: 'Tıklanabilir ızgara fotoğraf galerisi', previewBg: '#3f3f46', previewAccent: '#a1a1aa', tags: ['grid', 'lightbox'], isPremium: false },
      { id: 'gallery-slider', type: 'gallery', layout: 'fullwidth-slider', category: 'gallery', label: 'Tam Genişlik Slayt', desc: 'Tam ekran fotoğraf slaytı', previewBg: '#0a0a0a', previewAccent: '#fafafa', tags: ['slider', 'fullscreen'], isPremium: false },
      { id: 'gallery-before-after', type: 'gallery', layout: 'before-after', category: 'gallery', label: 'Önce-Sonra', desc: 'Kaydırarak karşılaştırma görseli', previewBg: '#1c1917', previewAccent: '#f59e0b', tags: ['karşılaştırma', 'slide'], isPremium: true },
      { id: 'gallery-instagram', type: 'gallery', layout: 'instagram-feed', category: 'gallery', label: 'Instagram Akışı', desc: 'Instagram tarzı kare galeri', previewBg: '#7c2d12', previewAccent: '#e11d48', tags: ['instagram', 'sosyal'], isPremium: false },
      { id: 'gallery-polaroid', type: 'gallery', layout: 'polaroid', category: 'gallery', label: 'Polaroid Galeri', desc: 'Eğimli polaroid tarzı kartlar', previewBg: '#f5f5f4', previewAccent: '#78716c', tags: ['polaroid', 'retro'], isPremium: false },

      // ─── CTA / AKSİYONLAR ────────────────────────────
      { id: 'cta-centered', type: 'cta', layout: 'centered-banner', category: 'cta', label: 'Ortalanmış CTA', desc: 'Dikkat çekici aksiyon çağrısı banner\'ı', previewBg: '#7c2d12', previewAccent: '#fb923c', tags: ['banner', 'buton'], isPremium: false },
      { id: 'cta-split', type: 'cta', layout: 'split-cta', category: 'cta', label: 'Bölünmüş CTA', desc: 'Metin ve butonlu iki sütunlu CTA', previewBg: '#1e3a5f', previewAccent: '#38bdf8', tags: ['split', 'iki'], isPremium: false },
      { id: 'cta-newsletter', type: 'cta', layout: 'newsletter', category: 'cta', label: 'Bülten Abonelik', desc: 'E-posta abonelik formu', previewBg: '#4c1d95', previewAccent: '#a78bfa', tags: ['eposta', 'bülten'], isPremium: false },
      { id: 'cta-countdown', type: 'cta', layout: 'countdown', category: 'cta', label: 'Geri Sayım', desc: 'Kampanya geri sayım sayacı', previewBg: '#be123c', previewAccent: '#fecdd3', tags: ['sayaç', 'kampanya'], isPremium: true },
      { id: 'cta-floating', type: 'cta', layout: 'floating-bar', category: 'cta', label: 'Haber Şeridi', desc: 'Dar tam genişlik haber/duyuru şeridi', previewBg: '#0f172a', previewAccent: '#fbbf24', tags: ['bar', 'haber', 'duyuru'], isPremium: false },

      // ─── İSTATİSTİK & SAYAÇLAR ────────────────────────
      { id: 'stats-counter', type: 'stats', layout: 'counter-row', category: 'stats', label: 'Sayaç Satırı', desc: 'Yatay sayı sayaçları', previewBg: '#0e7490', previewAccent: '#22d3ee', tags: ['sayaç', 'numara'], isPremium: false },
      { id: 'stats-cards', type: 'stats', layout: 'achievement-cards', category: 'stats', label: 'Başarı Kartları', desc: 'İkonlu başarı istatistik kartları', previewBg: '#14532d', previewAccent: '#4ade80', tags: ['kart', 'başarı'], isPremium: false },
      { id: 'stats-progress', type: 'stats', layout: 'progress-bars', category: 'stats', label: 'İlerleme Çubukları', desc: 'Animasyonlu dolum barları', previewBg: '#4c1d95', previewAccent: '#c084fc', tags: ['bar', 'animasyon'], isPremium: false },
      { id: 'stats-numbers', type: 'stats', layout: 'animated-numbers', category: 'stats', label: 'Animasyonlu Sayılar', desc: 'Sayarak artan büyük rakamlar', previewBg: '#312e81', previewAccent: '#818cf8', tags: ['animasyon', 'sayı'], isPremium: true },
      { id: 'stats-milestone', type: 'stats', layout: 'milestone-timeline', category: 'stats', label: 'Kilometre Taşları', desc: 'Dikey zaman çizgisi başarılar', previewBg: '#1e3a5f', previewAccent: '#93c5fd', tags: ['timeline', 'tarih'], isPremium: false },

      // ─── ÖZEL BLOKLAR ─────────────────────────────────
      { id: 'extras-spacer', type: 'spacer', layout: 'spacer', category: 'extras', label: 'Boşluk', desc: 'Ayarlanabilir dikey boşluk', previewBg: '#e5e7eb', previewAccent: '#9ca3af', tags: ['boşluk', 'padding'], isPremium: false },
      { id: 'extras-divider', type: 'divider', layout: 'divider', category: 'extras', label: 'Ayırıcı Çizgi', desc: 'Dekoratif bölüm ayırıcı', previewBg: '#d1d5db', previewAccent: '#6b7280', tags: ['çizgi', 'ayırıcı'], isPremium: false },
      { id: 'extras-faq', type: 'faq', layout: 'accordion', category: 'extras', label: 'SSS / FAQ', desc: 'Açılır-kapanır soru cevap', previewBg: '#1e293b', previewAccent: '#94a3b8', tags: ['sss', 'soru', 'cevap'], isPremium: false },
      { id: 'extras-logo-strip', type: 'logo-strip', layout: 'logo-strip', category: 'extras', label: 'Logo Şeridi', desc: 'Partner/Marka logoları sırası', previewBg: '#f5f5f4', previewAccent: '#a8a29e', tags: ['logo', 'partner', 'marka'], isPremium: false },
      { id: 'extras-social', type: 'social-links', layout: 'social-links', category: 'extras', label: 'Sosyal Medya', desc: 'Sosyal medya ikon linkleri', previewBg: '#0f172a', previewAccent: '#38bdf8', tags: ['sosyal', 'medya', 'link'], isPremium: false },
      { id: 'extras-html', type: 'html-embed', layout: 'html-embed', category: 'extras', label: 'HTML Gömme', desc: 'Özel HTML/Embed kodu', previewBg: '#1e293b', previewAccent: '#6ee7b7', tags: ['html', 'embed', 'kod'], isPremium: true }
    ];

    const addBlockWithLayout = (type, layout) => {
      const id = `${type}-${Date.now()}`;
      let title = '';
      let content = { layout };
      
      if (type === 'hero') {
        title = 'Giriş';
        content = {
          layout,
          banner: 'Eşsiz Lezzetlerin Buluşma Noktası',
          subtitle: 'Taze malzemelerle hazırlanan usta ellerden çıkan eşsiz tabaklar.',
          button_text: 'Masa Rezervasyonu Yap',
          button_url: '#reservation',
          image: 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80'
        };
      } else if (type === 'about') {
        title = layout === 'timeline' ? 'Tarihçemiz' : layout === 'team-grid' ? 'Ekibimiz' : layout === 'story-cards' ? 'Hikayemiz' : 'Hikayemiz';
        content = {
          layout,
          text: 'Yılların getirdiği tecrübe ve mutfak aşkıyla, misafirlerimize en taze ve en lezzetli yemekleri sunmak için her gün aynı heyecanla çalışıyoruz.',
          image: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=600&q=80',
          milestones: layout === 'timeline' ? [
            { year: '2015', text: 'İlk şubemiz İstanbul Kadıköy\'de açıldı' },
            { year: '2018', text: 'İkinci şube Beşiktaş\'ta hizmete girdi' },
            { year: '2022', text: 'Online sipariş platformumuz yayına alındı' },
            { year: '2024', text: '100.000+ mutlu müşteriye ulaştık' }
          ] : undefined,
          team: layout === 'team-grid' ? [
            { name: 'Ahmet Yılmaz', role: 'Baş Şef', image: 'https://images.unsplash.com/photo-1577219491135-ce391730fb2c?auto=format&fit=crop&w=200&q=80' },
            { name: 'Elif Kaya', role: 'Pasta Şefi', image: 'https://images.unsplash.com/photo-1581299894007-aaa50297cf16?auto=format&fit=crop&w=200&q=80' },
            { name: 'Murat Demir', role: 'Restoran Müdürü', image: 'https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=200&q=80' }
          ] : undefined,
          stories: layout === 'story-cards' ? [
            { title: 'İlk Adım', text: 'Küçük bir mutfakta başlayan büyük bir hayal...', icon: '🌱' },
            { title: 'Büyüme', text: 'Sadık müşterilerimizle birlikte büyüdük.', icon: '🚀' },
            { title: 'Bugün', text: 'Artık binlerce kişiye hizmet veriyoruz.', icon: '⭐' }
          ] : undefined
        };
      } else if (type === 'menu') {
        title = 'Öne Çıkan Lezzetler';
        content = {
          layout,
          items: [
            { name: 'Izgara Levrek', description: 'Taze sebzeler ve limonlu tereyağı sosu ile', price: '320', image: 'https://images.unsplash.com/photo-1467003909585-2f8a72700288?auto=format&fit=crop&w=300&q=80' },
            { name: 'Kuzu Tandır', description: 'Fırında 6 saat pişirilmiş kuzu eti, pilav ile', price: '380', image: 'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=300&q=80' },
            { name: 'Karışık Meze', description: 'Humus, babagannuş, atom, acılı ezme', price: '180', image: 'https://images.unsplash.com/photo-1529006557810-274b9b2fc783?auto=format&fit=crop&w=300&q=80' }
          ],
          categories: layout === 'tabbed' ? ['Ana Yemekler', 'Başlangıçlar', 'Tatlılar'] : undefined
        };
      } else if (type === 'testimonials') {
        title = 'Misafir Yorumları';
        content = {
          layout,
          quotes: [
            { name: 'Ayşe K.', text: 'Harika bir deneyimdi! Servisten lezzete her şey mükemmeldi.', rating: 5 },
            { name: 'Mehmet D.', text: 'İstanbul\'da yediğim en iyi restoran. Atmosfer olağanüstü.', rating: 5 },
            { name: 'Zeynep A.', text: 'Ailece gittiğimiz en güzel mekan. Çocuk menüsü de harika.', rating: 4 }
          ],
          platforms: layout === 'social-proof' ? [
            { platform: 'Google', rating: 4.8, count: 1240 },
            { platform: 'TripAdvisor', rating: 4.7, count: 890 },
            { platform: 'Yemeksepeti', rating: 4.9, count: 3200 }
          ] : undefined
        };
      } else if (type === 'hours') {
        title = 'Saatler & İletişim';
        content = {
          layout,
          address: 'Restoran Adresi',
          phone: '0212 000 00 00',
          email: 'info@restoran.com',
          times: [
            { day: 'Pazartesi - Cuma', hours: '11:00 - 23:00' },
            { day: 'Cumartesi - Pazar', hours: '10:00 - 00:00' }
          ]
        };
      } else if (type === 'reservation') {
        title = 'Masa Rezervasyonu';
        content = { layout };
      } else if (type === 'gallery') {
        title = 'Fotoğraf Galerisi';
        content = {
          layout,
          images: [
            { url: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=600&q=80', caption: 'Restoran İç Mekan' },
            { url: 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=600&q=80', caption: 'Özel Tabak' },
            { url: 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=600&q=80', caption: 'Bar Alanı' },
            { url: 'https://images.unsplash.com/photo-1559339352-11d035aa65de?auto=format&fit=crop&w=600&q=80', caption: 'Bahçe Alanı' },
            { url: 'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=600&q=80', caption: 'Mutfak' },
            { url: 'https://images.unsplash.com/photo-1467003909585-2f8a72700288?auto=format&fit=crop&w=600&q=80', caption: 'Deniz Ürünleri' }
          ]
        };
      } else if (type === 'cta') {
        title = layout === 'newsletter' ? 'Bülten Abonelik' : layout === 'countdown' ? 'Geri Sayım' : layout === 'floating-bar' ? 'Duyuru Şeridi' : 'Aksiyona Geç';
        content = {
          layout,
          heading: 'Özel fırsatları kaçırmayın!',
          text: 'Hemen rezervasyon yapın ve %20 indirim kazanın.',
          button_text: 'Hemen Başla',
          button_url: '#reservation',
          bg_color: '#6366f1',
          countdown_date: layout === 'countdown' ? '2025-12-31T23:59:59' : undefined,
          placeholder_text: layout === 'newsletter' ? 'E-posta adresinizi girin' : undefined
        };
      } else if (type === 'stats') {
        title = 'Rakamlarımız';
        content = {
          layout,
          items: [
            { number: '10+', label: 'Yıllık Deneyim', icon: '⏰' },
            { number: '50K+', label: 'Mutlu Müşteri', icon: '😊' },
            { number: '200+', label: 'Menü Çeşidi', icon: '🍽️' },
            { number: '4.8', label: 'Müşteri Puanı', icon: '⭐' }
          ],
          milestones: layout === 'milestone-timeline' ? [
            { year: '2015', text: 'Kuruluş' },
            { year: '2018', text: '10.000 müşteri' },
            { year: '2021', text: 'İkinci şube' },
            { year: '2024', text: 'Dijitalleşme' }
          ] : undefined
        };
      } else if (type === 'faq') {
        title = 'Sıkça Sorulan Sorular';
        content = {
          layout,
          items: [
            { question: 'Rezervasyon nasıl yapabilirim?', answer: 'Web sitemizden veya telefonla rezervasyon yapabilirsiniz.' },
            { question: 'Otopark var mı?', answer: 'Evet, restoranımıza 50 metre mesafede ücretsiz vale parkımız bulunmaktadır.' },
            { question: 'Çocuk menüsü mevcut mu?', answer: 'Evet, 12 yaş altı misafirlerimiz için özel çocuk menümüz mevcuttur.' },
            { question: 'Dış mekan alanınız var mı?', answer: 'Evet, 40 kişilik bahçe alanımız mevcuttur.' }
          ]
        };
      } else if (type === 'spacer') {
        title = 'Boşluk';
        content = { layout, height: 60 };
      } else if (type === 'divider') {
        title = 'Ayırıcı';
        content = { layout, style: 'solid', thickness: 1, color: '' };
      } else if (type === 'logo-strip') {
        title = 'Partner Logoları';
        content = {
          layout,
          heading: 'İş Ortaklarımız',
          logos: [
            { name: 'Partner 1', url: '' },
            { name: 'Partner 2', url: '' },
            { name: 'Partner 3', url: '' },
            { name: 'Partner 4', url: '' }
          ]
        };
      } else if (type === 'social-links') {
        title = 'Sosyal Medya';
        content = {
          layout,
          heading: 'Bizi Takip Edin',
          links: [
            { platform: 'Instagram', url: '' },
            { platform: 'Facebook', url: '' },
            { platform: 'Twitter', url: '' },
            { platform: 'YouTube', url: '' }
          ]
        };
      } else if (type === 'html-embed') {
        title = 'HTML Gömme';
        content = { layout, code: '<div style="padding:20px;text-align:center;color:#64748b;">Buraya özel HTML kodunuzu yazın</div>' };
      }
      
      const newBlocks = [...blocks, { id, type, title, content }];
      updateActivePageBlocks(newBlocks);
      setSelectedBlockId(id);
      syncClassicStatesFromBlocks(newBlocks);
    };

    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: '#f8fafc',
        color: '#0f172a',
        zIndex: 9999,
        display: 'grid',
        gridTemplateColumns: '60px 340px 1fr',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}>
        {/* Wix-Style Vertical Icon Dock */}
        <div style={{
          background: '#ffffff',
          borderRight: '1px solid rgba(0,0,0,0.06)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '24px 0',
          gap: '20px',
          height: '100vh',
          zIndex: 10,
          boxShadow: '2px 0 10px rgba(0,0,0,0.01)'
        }}>
          {/* Logo */}
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #4f46e5 0%, #8b5cf6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: '900',
            fontSize: '16px',
            color: '#0f172a',
            marginBottom: '10px',
            boxShadow: '0 4px 12px rgba(79,70,229,0.2)'
          }}>
            B
          </div>

          {/* Dock Buttons */}
          {[
            { tab: 'blocks', label: 'Bileşenler', icon: Plus },
            { tab: 'presets', label: 'Tasarım', icon: Image },
            { tab: 'pages', label: 'Sayfalar & SEO', icon: Globe },
            { tab: 'upgrade', label: 'Profesyonel Plan', icon: Star, highlight: activePlan !== 'Enterprise' },
            { tab: 'layers', label: 'Katmanlar', icon: Layers, isAction: true }
          ].map(btn => {
            const Icon = btn.icon;
            const isActive = btn.isAction ? showLayersPopup : elementorTab === btn.tab;
            return (
              <button
                key={btn.tab}
                onClick={() => {
                  if (btn.isAction) {
                    setShowLayersPopup(v => !v);
                  } else {
                    setElementorTab(btn.tab);
                    setSelectedBlockId(null);
                  }
                }}
                title={btn.label}
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '10px',
                  border: 'none',
                  background: isActive ? 'rgba(79, 70, 229, 0.08)' : 'transparent',
                  color: isActive ? '#4f46e5' : btn.highlight ? '#fbbf24' : '#64748b',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'all 0.2s',
                  position: 'relative',
                  outline: 'none'
                }}
                onMouseOver={e => {
                  if (!isActive) e.currentTarget.style.color = '#0f172a';
                }}
                onMouseOut={e => {
                  if (!isActive) e.currentTarget.style.color = btn.highlight ? '#fbbf24' : '#64748b';
                }}
              >
                <Icon size={20} />
                {btn.highlight && (
                  <span style={{
                    position: 'absolute',
                    top: '4px',
                    right: '4px',
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    background: '#fbbf24',
                    border: '1px solid #ffffff'
                  }} />
                )}
              </button>
            );
          })}
        </div>

        {/* Wix-Style Properties / Widgets Panel */}
        <div style={{
          background: '#ffffff',
          borderRight: '1px solid rgba(0,0,0,0.06)',
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          overflowY: 'auto'
        }}>
          {/* Header */}
          <div style={{
            padding: '20px',
            borderBottom: '1px solid rgba(0,0,0,0.06)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: '800', margin: 0, display: 'flex', alignItems: 'center', gap: '8px', color: '#4f46e5' }}>
                <Settings size={18} /> Canlı Editör
              </h2>
              <span style={{ fontSize: '11px', color: '#64748b' }}>Sürükle-bırak tadında modüler sayfa tasarımı</span>
            </div>
            <button
              onClick={() => {
                setShowElementorModal(false);
                setSelectedBlockId(null);
              }}
              style={{
                background: 'rgba(0,0,0,0.03)',
                border: 'none',
                color: '#64748b',
                padding: '6px 12px',
                borderRadius: '8px',
                fontSize: '12px',
                cursor: 'pointer',
                fontWeight: '600',
                transition: 'all 0.2s'
              }}
              onMouseOver={e => e.currentTarget.style.background = 'rgba(0,0,0,0.05)'}
              onMouseOut={e => e.currentTarget.style.background = 'rgba(0,0,0,0.03)'}
            >
              Kapat
            </button>
          </div>

          {/* Action buttons */}
          <div style={{ padding: '16px', borderBottom: '1px solid rgba(0,0,0,0.06)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <button
              onClick={() => handleSave()}
              disabled={saving}
              style={{
                width: '100%',
                padding: '10px',
                background: saved ? '#10b981' : '#6366f1',
                color: '#ffffff',
                border: 'none',
                borderRadius: '8px',
                fontWeight: '700',
                fontSize: '13px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                transition: 'all 0.2s'
              }}
            >
              {saved ? <><Check size={14} /> Kaydedildi!</> : saving ? 'Kaydediliyor...' : <><Save size={14} /> Yayınla / Kaydet</>}
            </button>
            
            <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
              <button
                type="button"
                onClick={handleExportSettings}
                style={{
                  flex: 1,
                  padding: '8px',
                  background: 'rgba(99, 102, 241, 0.08)',
                  color: '#4f46e5',
                  border: '1px solid rgba(99, 102, 241, 0.15)',
                  borderRadius: '6px',
                  fontWeight: '600',
                  fontSize: '11px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px'
                }}
              >
                📥 Dışa Aktar
              </button>
              <label
                style={{
                  flex: 1,
                  padding: '8px',
                  background: 'rgba(16, 185, 129, 0.08)',
                  color: '#10b981',
                  border: '1px solid rgba(16, 185, 129, 0.15)',
                  borderRadius: '6px',
                  fontWeight: '600',
                  fontSize: '11px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px',
                  textAlign: 'center'
                }}
              >
                📤 İçe Aktar
                <input
                  type="file"
                  accept=".json"
                  onChange={handleImportSettings}
                  style={{ display: 'none' }}
                />
              </label>
            </div>
            <button
              type="button"
              onClick={handleDeleteSettings}
              style={{
                width: '100%',
                padding: '8px',
                background: 'rgba(239, 68, 68, 0.08)',
                color: '#ef4444',
                border: '1px solid rgba(239, 68, 68, 0.15)',
                borderRadius: '6px',
                fontWeight: '600',
                fontSize: '11px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '4px'
              }}
            >
              🗑️ Tüm Site Ayarlarını Sıfırla
            </button>
          </div>

          {/* Editing Area */}
          <div style={{ padding: '20px', flex: 1 }}>
            {selectedBlock ? (
              // EDIT BLOCK FORM
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <button
                  onClick={() => setSelectedBlockId(null)}
                  style={{
                    alignSelf: 'flex-start',
                    background: 'none',
                    border: 'none',
                    color: '#818cf8',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: '600',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: 0
                  }}
                >
                  <ArrowLeft size={14} /> Bölüm Listesine Dön
                </button>

                <div>
                  <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px', textTransform: 'uppercase' }}>Bölüm Başlığı</label>
                  <input
                    type="text"
                    value={selectedBlock.title}
                    onChange={(e) => updateBlockTitle(selectedBlock.id, e.target.value)}
                    style={{
                      width: '100%',
                      background: '#0f172a',
                      border: '1px solid #475569',
                      borderRadius: '8px',
                      padding: '10px',
                      color: '#0f172a',
                      fontSize: '13.5px',
                      outline: 'none'
                    }}
                  />
                </div>

                {/* Specific field editors per type */}
                {selectedBlock.type === 'hero' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>Tasarım Düzeni</label>
                      <select
                        value={selectedBlock.content.layout || 'center'}
                        onChange={(e) => updateBlockContent(selectedBlock.id, { layout: e.target.value })}
                        style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none' }}
                      >
                        <option value="center">Ortalanmış Klasik</option>
                        <option value="split">Sol Metin, Sağ Görsel</option>
                        <option value="glass">Cam Efekti (Glassmorphism)</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>Banner Büyük Başlığı</label>
                      <input
                        type="text"
                        value={selectedBlock.content.banner || ''}
                        onChange={(e) => updateBlockContent(selectedBlock.id, { banner: e.target.value })}
                        style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none' }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>Alt Başlık / Açıklama</label>
                      <textarea
                        rows="3"
                        value={selectedBlock.content.subtitle || ''}
                        onChange={(e) => updateBlockContent(selectedBlock.id, { subtitle: e.target.value })}
                        style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none', resize: 'vertical' }}
                      />
                    </div>
                    {(selectedBlock.content.layout === 'split' || selectedBlock.content.layout === 'glass') && (
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                          <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', margin: 0 }}>Görsel URL</label>
                          <button
                            type="button"
                            onClick={() => openMediaLibrary(selectedBlock.id, 'image')}
                            style={{ background: 'none', border: 'none', color: '#4f46e5', fontSize: '11px', fontWeight: '700', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', padding: 0 }}
                          >
                            🖼️ Kütüphaneden Seç
                          </button>
                        </div>
                        <input
                          type="text"
                          value={selectedBlock.content.image || ''}
                          onChange={(e) => updateBlockContent(selectedBlock.id, { image: e.target.value })}
                          placeholder="https://images.unsplash.com/photo-..."
                          style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none' }}
                        />
                        <small style={{ fontSize: '11px', color: '#64748b', marginTop: '4px', display: 'block' }}>Arka plan veya yan tarafta görünecek görsel adresi.</small>
                      </div>
                    )}
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>Buton Metni</label>
                      <input
                        type="text"
                        value={selectedBlock.content.button_text || ''}
                        onChange={(e) => updateBlockContent(selectedBlock.id, { button_text: e.target.value })}
                        placeholder="Örn: Masa Rezervasyonu Yap"
                        style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none' }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>Buton Bağlantısı (URL)</label>
                      <input
                        type="text"
                        value={selectedBlock.content.button_url || ''}
                        onChange={(e) => updateBlockContent(selectedBlock.id, { button_url: e.target.value })}
                        placeholder="Örn: #reservation"
                        style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none' }}
                      />
                    </div>
                  </div>
                )}

                {selectedBlock.type === 'about' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>Yerleşim Düzeni</label>
                      <select
                        value={selectedBlock.content.layout || 'left'}
                        onChange={(e) => updateBlockContent(selectedBlock.id, { layout: e.target.value })}
                        style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none' }}
                      >
                        <option value="left">Metin Solda, Resim Sağda</option>
                        <option value="right">Resim Solda, Metin Sağda</option>
                        <option value="minimal">Minimalist (Görselsiz)</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>Hikaye / Açıklama Metni</label>
                      <textarea
                        rows="5"
                        value={selectedBlock.content.text || ''}
                        onChange={(e) => updateBlockContent(selectedBlock.id, { text: e.target.value })}
                        style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none', resize: 'vertical' }}
                      />
                    </div>
                    {selectedBlock.content.layout !== 'minimal' && (
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                          <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', margin: 0 }}>Resim Adresi (URL)</label>
                          <button
                            type="button"
                            onClick={() => openMediaLibrary(selectedBlock.id, 'image')}
                            style={{ background: 'none', border: 'none', color: '#4f46e5', fontSize: '11px', fontWeight: '700', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', padding: 0 }}
                          >
                            🖼️ Kütüphaneden Seç
                          </button>
                        </div>
                        <input
                          type="text"
                          value={selectedBlock.content.image || ''}
                          onChange={(e) => updateBlockContent(selectedBlock.id, { image: e.target.value })}
                          style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none' }}
                        />
                        <small style={{ fontSize: '11px', color: '#64748b', marginTop: '4px', display: 'block' }}>Unsplash veya başka bir görsel linki girebilirsiniz.</small>
                      </div>
                    )}
                  </div>
                )}

                {selectedBlock.type === 'menu' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>Tasarım Düzeni</label>
                      <select
                        value={selectedBlock.content.layout || 'grid'}
                        onChange={(e) => updateBlockContent(selectedBlock.id, { layout: e.target.value })}
                        style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none' }}
                      >
                        <option value="grid">3'lü Kart Izgarası (Görselli)</option>
                        <option value="list">Fiyat Çizgili Menü Listesi</option>
                        <option value="minimal">Minimal Görselsiz Kartlar</option>
                      </select>
                    </div>
                    <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '-10px' }}>Menü Elemanları</label>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '350px', overflowY: 'auto', paddingRight: '4px' }}>
                      {(selectedBlock.content.items || []).map((item, i) => (
                        <div key={i} style={{ background: '#1e293b', border: '1px solid #475569', padding: '12px', borderRadius: '8px', position: 'relative', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          <button
                            type="button"
                            onClick={() => {
                              const newItems = (selectedBlock.content.items || []).filter((_, idx) => idx !== i);
                              updateBlockContent(selectedBlock.id, { items: newItems });
                            }}
                            style={{ position: 'absolute', top: '8px', right: '8px', background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}
                          >
                            <Trash size={14} />
                          </button>
                          
                          <div>
                            <input
                              type="text"
                              placeholder="Yemek Adı"
                              value={item.name || ''}
                              onChange={(e) => {
                                const newItems = [...(selectedBlock.content.items || [])];
                                newItems[i] = { ...newItems[i], name: e.target.value };
                                updateBlockContent(selectedBlock.id, { items: newItems });
                              }}
                              style={{ width: '90%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '6px', color: '#0f172a', fontSize: '12px', outline: 'none' }}
                            />
                          </div>
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                            <input
                              type="text"
                              placeholder="Fiyat (TL)"
                              value={item.price || ''}
                              onChange={(e) => {
                                const newItems = [...(selectedBlock.content.items || [])];
                                newItems[i] = { ...newItems[i], price: e.target.value };
                                updateBlockContent(selectedBlock.id, { items: newItems });
                              }}
                              style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '6px', color: '#0f172a', fontSize: '12px', outline: 'none' }}
                            />
                            {selectedBlock.content.layout === 'grid' && (
                              <div style={{ display: 'flex', gap: '4px' }}>
                                <input
                                  type="text"
                                  placeholder="Resim URL"
                                  value={item.image || ''}
                                  onChange={(e) => {
                                    const newItems = [...(selectedBlock.content.items || [])];
                                    newItems[i] = { ...newItems[i], image: e.target.value };
                                    updateBlockContent(selectedBlock.id, { items: newItems });
                                  }}
                                  style={{ flex: 1, background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '6px', color: '#0f172a', fontSize: '12px', outline: 'none' }}
                                />
                                <button
                                  type="button"
                                  onClick={() => openMediaLibrary(selectedBlock.id, 'menuItemImage', i)}
                                  style={{ background: 'rgba(0,0,0,0.03)', border: '1px solid #cbd5e1', color: '#4f46e5', cursor: 'pointer', padding: '0 6px', borderRadius: '6px', fontSize: '11px', display: 'flex', alignItems: 'center' }}
                                  title="Görsel Seç"
                                >
                                  🖼️
                                </button>
                              </div>
                            )}
                          </div>
                          <input
                            type="text"
                            placeholder="Kısa Açıklama"
                            value={item.description || ''}
                            onChange={(e) => {
                              const newItems = [...(selectedBlock.content.items || [])];
                              newItems[i] = { ...newItems[i], description: e.target.value };
                              updateBlockContent(selectedBlock.id, { items: newItems });
                            }}
                            style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '6px', color: '#0f172a', fontSize: '12px', outline: 'none' }}
                          />
                        </div>
                      ))}
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        const newItems = [...(selectedBlock.content.items || []), { name: 'Yeni Yemek', price: '100', description: '', image: '' }];
                        updateBlockContent(selectedBlock.id, { items: newItems });
                      }}
                      style={{
                        padding: '8px',
                        background: 'rgba(0,0,0,0.04)',
                        color: '#a5b4fc',
                        border: '1px dashed #475569',
                        borderRadius: '8px',
                        fontSize: '12px',
                        fontWeight: '600',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px'
                      }}
                    >
                      <Plus size={14} /> Yeni Yemek Ekle
                    </button>
                  </div>
                )}

                {selectedBlock.type === 'testimonials' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>Tasarım Düzeni</label>
                      <select
                        value={selectedBlock.content.layout || 'grid'}
                        onChange={(e) => updateBlockContent(selectedBlock.id, { layout: e.target.value })}
                        style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none' }}
                      >
                        <option value="grid">Kart Izgarası</option>
                        <option value="spotlight">Öne Çıkan Tek Yorum (Spotlight)</option>
                      </select>
                    </div>
                    <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '-10px' }}>Yorumlar</label>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '350px', overflowY: 'auto', paddingRight: '4px' }}>
                      {(selectedBlock.content.quotes || []).map((quote, i) => (
                        <div key={i} style={{ background: '#1e293b', border: '1px solid #475569', padding: '12px', borderRadius: '8px', position: 'relative', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          <button
                            type="button"
                            onClick={() => {
                              const newQuotes = (selectedBlock.content.quotes || []).filter((_, idx) => idx !== i);
                              updateBlockContent(selectedBlock.id, { quotes: newQuotes });
                            }}
                            style={{ position: 'absolute', top: '8px', right: '8px', background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}
                          >
                            <Trash size={14} />
                          </button>
                          
                          <div>
                            <input
                              type="text"
                              placeholder="Müşteri Adı"
                              value={quote.name || ''}
                              onChange={(e) => {
                                const newQuotes = [...(selectedBlock.content.quotes || [])];
                                newQuotes[i] = { ...newQuotes[i], name: e.target.value };
                                updateBlockContent(selectedBlock.id, { quotes: newQuotes });
                              }}
                              style={{ width: '90%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '6px', color: '#0f172a', fontSize: '12px', outline: 'none' }}
                            />
                          </div>
                          <div>
                            <select
                              value={quote.rating || 5}
                              onChange={(e) => {
                                const newQuotes = [...(selectedBlock.content.quotes || [])];
                                newQuotes[i] = { ...newQuotes[i], rating: parseInt(e.target.value) };
                                updateBlockContent(selectedBlock.id, { quotes: newQuotes });
                              }}
                              style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '6px', color: '#0f172a', fontSize: '12px', outline: 'none' }}
                            >
                              <option value="5">⭐⭐⭐⭐⭐ (5 Yıldız)</option>
                              <option value="4">⭐⭐⭐⭐ (4 Yıldız)</option>
                              <option value="3">⭐⭐⭐ (3 Yıldız)</option>
                              <option value="2">⭐⭐ (2 Yıldız)</option>
                              <option value="1">⭐ (1 Yıldız)</option>
                            </select>
                          </div>
                          <textarea
                            rows="2"
                            placeholder="Yorum metni"
                            value={quote.text || ''}
                            onChange={(e) => {
                              const newQuotes = [...(selectedBlock.content.quotes || [])];
                              newQuotes[i] = { ...newQuotes[i], text: e.target.value };
                              updateBlockContent(selectedBlock.id, { quotes: newQuotes });
                            }}
                            style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '6px', color: '#0f172a', fontSize: '12px', outline: 'none', resize: 'vertical' }}
                          />
                        </div>
                      ))}
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        const newQuotes = [...(selectedBlock.content.quotes || []), { name: 'Yeni Misafir', text: 'Çok lezzetliydi, teşekkürler.', rating: 5 }];
                        updateBlockContent(selectedBlock.id, { quotes: newQuotes });
                      }}
                      style={{
                        padding: '8px',
                        background: 'rgba(0,0,0,0.04)',
                        color: '#a5b4fc',
                        border: '1px dashed #475569',
                        borderRadius: '8px',
                        fontSize: '12px',
                        fontWeight: '600',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px'
                      }}
                    >
                      <Plus size={14} /> Yeni Yorum Ekle
                    </button>
                  </div>
                )}

                {selectedBlock.type === 'hours' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>Tasarım Düzeni</label>
                      <select
                        value={selectedBlock.content.layout || 'split'}
                        onChange={(e) => updateBlockContent(selectedBlock.id, { layout: e.target.value })}
                        style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none' }}
                      >
                        <option value="split">İki Sütunlu (İletişim & Saatler Yan Yana)</option>
                        <option value="center">Tek Sütunlu Ortalanmış</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>Restoran Adresi</label>
                      <textarea
                        rows="2"
                        value={selectedBlock.content.address || ''}
                        onChange={(e) => updateBlockContent(selectedBlock.id, { address: e.target.value })}
                        style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none', resize: 'vertical' }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>Telefon Numarası</label>
                      <input
                        type="text"
                        value={selectedBlock.content.phone || ''}
                        onChange={(e) => updateBlockContent(selectedBlock.id, { phone: e.target.value })}
                        style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none' }}
                      />
                    </div>
                    
                    <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '-10px' }}>Çalışma Saatleri Satırları</label>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '200px', overflowY: 'auto', paddingRight: '4px' }}>
                      {(selectedBlock.content.times || []).map((t, i) => (
                        <div key={i} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                          <input
                            type="text"
                            placeholder="Gün(ler) (Örn: Hafta içi)"
                            value={t.day || ''}
                            onChange={(e) => {
                              const newTimes = [...(selectedBlock.content.times || [])];
                              newTimes[i] = { ...newTimes[i], day: e.target.value };
                              updateBlockContent(selectedBlock.id, { times: newTimes });
                            }}
                            style={{ flex: 1, background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '6px', color: '#0f172a', fontSize: '12px', outline: 'none' }}
                          />
                          <input
                            type="text"
                            placeholder="Saat Aralığı (Örn: 09:00 - 22:00)"
                            value={t.hours || ''}
                            onChange={(e) => {
                              const newTimes = [...(selectedBlock.content.times || [])];
                              newTimes[i] = { ...newTimes[i], hours: e.target.value };
                              updateBlockContent(selectedBlock.id, { times: newTimes });
                            }}
                            style={{ flex: 1, background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '6px', color: '#0f172a', fontSize: '12px', outline: 'none' }}
                          />
                          <button
                            type="button"
                            onClick={() => {
                              const newTimes = (selectedBlock.content.times || []).filter((_, idx) => idx !== i);
                              updateBlockContent(selectedBlock.id, { times: newTimes });
                            }}
                            style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}
                          >
                            <Trash size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        const newTimes = [...(selectedBlock.content.times || []), { day: 'Pazartesi', hours: '09:00 - 22:00' }];
                        updateBlockContent(selectedBlock.id, { times: newTimes });
                      }}
                      style={{
                        padding: '8px',
                        background: 'rgba(0,0,0,0.04)',
                        color: '#a5b4fc',
                        border: '1px dashed #475569',
                        borderRadius: '8px',
                        fontSize: '12px',
                        fontWeight: '600',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px'
                      }}
                    >
                      <Plus size={14} /> Yeni Satır Ekle
                    </button>
                  </div>
                )}

                {selectedBlock.type === 'reservation' && (
                  <div style={{ background: 'rgba(0,0,0,0.02)', border: '1px dashed #94a3b8', padding: '16px', borderRadius: '8px', fontSize: '12.5px', color: '#94a3b8', lineHeight: '1.6' }}>
                    <span style={{ fontWeight: '700', color: '#0f172a', display: 'block', marginBottom: '6px' }}>📅 Rezervasyon Modülü</span>
                    Bu modül müşterilerinizin web sitesinden masa rezervasyonu yapabilmelerini sağlar. Rezervasyon durumunu "Ayarlar" sekmesindeki aktiflik butonundan yönetebilirsiniz.
                  </div>
                )}

                {/* ── Gallery Editor ── */}
                {selectedBlock.type === 'gallery' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <label style={{ fontSize: '11px', color: '#64748b', fontWeight: '700', textTransform: 'uppercase' }}>Galeri Görselleri</label>
                    {(selectedBlock.content.images || []).map((img, i) => (
                      <div key={i} style={{ background: 'rgba(0,0,0,0.02)', border: '1px solid rgba(0,0,0,0.06)', borderRadius: '8px', padding: '10px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        <input type="text" placeholder="Görsel URL" value={img.url || ''} onChange={(e) => { const imgs = [...(selectedBlock.content.images || [])]; imgs[i] = { ...imgs[i], url: e.target.value }; updateBlockContent(selectedBlock.id, { images: imgs }); }} style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '8px', fontSize: '11px', color: '#0f172a', outline: 'none' }} />
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <input type="text" placeholder="Açıklama" value={img.caption || ''} onChange={(e) => { const imgs = [...(selectedBlock.content.images || [])]; imgs[i] = { ...imgs[i], caption: e.target.value }; updateBlockContent(selectedBlock.id, { images: imgs }); }} style={{ flex: 1, background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '8px', fontSize: '11px', color: '#0f172a', outline: 'none' }} />
                          <button onClick={() => { const imgs = [...(selectedBlock.content.images || [])]; imgs.splice(i, 1); updateBlockContent(selectedBlock.id, { images: imgs }); }} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}><Trash size={14} /></button>
                        </div>
                      </div>
                    ))}
                    <button onClick={() => { const imgs = [...(selectedBlock.content.images || []), { url: '', caption: '' }]; updateBlockContent(selectedBlock.id, { images: imgs }); }} style={{ padding: '8px', background: 'rgba(0,0,0,0.03)', color: '#6366f1', border: '1px dashed rgba(0,0,0,0.12)', borderRadius: '8px', fontSize: '12px', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}><Plus size={14} /> Görsel Ekle</button>
                  </div>
                )}

                {/* ── CTA Editor ── */}
                {selectedBlock.type === 'cta' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#64748b', fontWeight: '700', marginBottom: '6px' }}>Başlık</label>
                      <input type="text" value={selectedBlock.content.heading || ''} onChange={(e) => updateBlockContent(selectedBlock.id, { heading: e.target.value })} style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', fontSize: '12px', color: '#0f172a', outline: 'none' }} />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#64748b', fontWeight: '700', marginBottom: '6px' }}>Açıklama</label>
                      <textarea value={selectedBlock.content.text || ''} onChange={(e) => updateBlockContent(selectedBlock.id, { text: e.target.value })} rows={2} style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', fontSize: '12px', color: '#0f172a', outline: 'none', resize: 'vertical' }} />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#64748b', fontWeight: '700', marginBottom: '6px' }}>Buton Metni</label>
                      <input type="text" value={selectedBlock.content.button_text || ''} onChange={(e) => updateBlockContent(selectedBlock.id, { button_text: e.target.value })} style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', fontSize: '12px', color: '#0f172a', outline: 'none' }} />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#64748b', fontWeight: '700', marginBottom: '6px' }}>Buton URL</label>
                      <input type="text" value={selectedBlock.content.button_url || ''} onChange={(e) => updateBlockContent(selectedBlock.id, { button_url: e.target.value })} style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', fontSize: '12px', color: '#0f172a', outline: 'none' }} />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#64748b', fontWeight: '700', marginBottom: '6px' }}>Arka Plan Rengi</label>
                      <input type="color" value={selectedBlock.content.bg_color || '#6366f1'} onChange={(e) => updateBlockContent(selectedBlock.id, { bg_color: e.target.value })} style={{ width: '40px', height: '40px', border: 'none', borderRadius: '8px', cursor: 'pointer', padding: 0 }} />
                    </div>
                  </div>
                )}

                {/* ── Stats Editor ── */}
                {selectedBlock.type === 'stats' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <label style={{ fontSize: '11px', color: '#64748b', fontWeight: '700', textTransform: 'uppercase' }}>İstatistik Öğeleri</label>
                    {(selectedBlock.content.items || []).map((item, i) => (
                      <div key={i} style={{ background: 'rgba(0,0,0,0.02)', border: '1px solid rgba(0,0,0,0.06)', borderRadius: '8px', padding: '10px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <input type="text" placeholder="İkon" value={item.icon || ''} onChange={(e) => { const items = [...(selectedBlock.content.items || [])]; items[i] = { ...items[i], icon: e.target.value }; updateBlockContent(selectedBlock.id, { items }); }} style={{ width: '50px', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '8px', fontSize: '14px', textAlign: 'center', outline: 'none' }} />
                          <input type="text" placeholder="Sayı" value={item.number || ''} onChange={(e) => { const items = [...(selectedBlock.content.items || [])]; items[i] = { ...items[i], number: e.target.value }; updateBlockContent(selectedBlock.id, { items }); }} style={{ flex: 1, background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '8px', fontSize: '12px', color: '#0f172a', outline: 'none' }} />
                        </div>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <input type="text" placeholder="Etiket" value={item.label || ''} onChange={(e) => { const items = [...(selectedBlock.content.items || [])]; items[i] = { ...items[i], label: e.target.value }; updateBlockContent(selectedBlock.id, { items }); }} style={{ flex: 1, background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '8px', fontSize: '12px', color: '#0f172a', outline: 'none' }} />
                          <button onClick={() => { const items = [...(selectedBlock.content.items || [])]; items.splice(i, 1); updateBlockContent(selectedBlock.id, { items }); }} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}><Trash size={14} /></button>
                        </div>
                      </div>
                    ))}
                    <button onClick={() => { const items = [...(selectedBlock.content.items || []), { number: '0', label: 'Yeni', icon: '📊' }]; updateBlockContent(selectedBlock.id, { items }); }} style={{ padding: '8px', background: 'rgba(0,0,0,0.03)', color: '#6366f1', border: '1px dashed rgba(0,0,0,0.12)', borderRadius: '8px', fontSize: '12px', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}><Plus size={14} /> Yeni Öğe Ekle</button>
                  </div>
                )}

                {/* ── FAQ Editor ── */}
                {selectedBlock.type === 'faq' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <label style={{ fontSize: '11px', color: '#64748b', fontWeight: '700', textTransform: 'uppercase' }}>Soru & Cevaplar</label>
                    {(selectedBlock.content.items || []).map((item, i) => (
                      <div key={i} style={{ background: 'rgba(0,0,0,0.02)', border: '1px solid rgba(0,0,0,0.06)', borderRadius: '8px', padding: '10px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        <input type="text" placeholder="Soru" value={item.question || ''} onChange={(e) => { const items = [...(selectedBlock.content.items || [])]; items[i] = { ...items[i], question: e.target.value }; updateBlockContent(selectedBlock.id, { items }); }} style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '8px', fontSize: '12px', color: '#0f172a', outline: 'none', fontWeight: '600' }} />
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <textarea placeholder="Cevap" value={item.answer || ''} onChange={(e) => { const items = [...(selectedBlock.content.items || [])]; items[i] = { ...items[i], answer: e.target.value }; updateBlockContent(selectedBlock.id, { items }); }} rows={2} style={{ flex: 1, background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '8px', fontSize: '11px', color: '#0f172a', outline: 'none', resize: 'vertical' }} />
                          <button onClick={() => { const items = [...(selectedBlock.content.items || [])]; items.splice(i, 1); updateBlockContent(selectedBlock.id, { items }); }} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', alignSelf: 'flex-start', marginTop: '6px' }}><Trash size={14} /></button>
                        </div>
                      </div>
                    ))}
                    <button onClick={() => { const items = [...(selectedBlock.content.items || []), { question: 'Yeni Soru?', answer: 'Cevap...' }]; updateBlockContent(selectedBlock.id, { items }); }} style={{ padding: '8px', background: 'rgba(0,0,0,0.03)', color: '#6366f1', border: '1px dashed rgba(0,0,0,0.12)', borderRadius: '8px', fontSize: '12px', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}><Plus size={14} /> Yeni Soru Ekle</button>
                  </div>
                )}

                {/* ── Spacer Editor ── */}
                {selectedBlock.type === 'spacer' && (
                  <div>
                    <label style={{ display: 'block', fontSize: '11px', color: '#64748b', fontWeight: '700', marginBottom: '6px' }}>Boşluk Yüksekliği (px)</label>
                    <input type="range" min="10" max="200" value={selectedBlock.content.height || 60} onChange={(e) => updateBlockContent(selectedBlock.id, { height: parseInt(e.target.value) })} style={{ width: '100%' }} />
                    <span style={{ fontSize: '11px', color: '#64748b' }}>{selectedBlock.content.height || 60}px</span>
                  </div>
                )}

                {/* ── Divider Editor ── */}
                {selectedBlock.type === 'divider' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#64748b', fontWeight: '700', marginBottom: '6px' }}>Çizgi Stili</label>
                      <select value={selectedBlock.content.style || 'solid'} onChange={(e) => updateBlockContent(selectedBlock.id, { style: e.target.value })} style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', fontSize: '12px', color: '#0f172a', outline: 'none' }}>
                        <option value="solid">Düz</option>
                        <option value="dashed">Kesikli</option>
                        <option value="dotted">Noktalı</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#64748b', fontWeight: '700', marginBottom: '6px' }}>Kalınlık (px)</label>
                      <input type="range" min="1" max="5" value={selectedBlock.content.thickness || 1} onChange={(e) => updateBlockContent(selectedBlock.id, { thickness: parseInt(e.target.value) })} style={{ width: '100%' }} />
                      <span style={{ fontSize: '11px', color: '#64748b' }}>{selectedBlock.content.thickness || 1}px</span>
                    </div>
                  </div>
                )}

                {/* ── Logo Strip Editor ── */}
                {selectedBlock.type === 'logo-strip' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#64748b', fontWeight: '700', marginBottom: '6px' }}>Başlık</label>
                      <input type="text" value={selectedBlock.content.heading || ''} onChange={(e) => updateBlockContent(selectedBlock.id, { heading: e.target.value })} style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', fontSize: '12px', color: '#0f172a', outline: 'none' }} />
                    </div>
                    <label style={{ fontSize: '11px', color: '#64748b', fontWeight: '700', textTransform: 'uppercase' }}>Logolar</label>
                    {(selectedBlock.content.logos || []).map((logo, i) => (
                      <div key={i} style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <input type="text" placeholder="Ad" value={logo.name || ''} onChange={(e) => { const logos = [...(selectedBlock.content.logos || [])]; logos[i] = { ...logos[i], name: e.target.value }; updateBlockContent(selectedBlock.id, { logos }); }} style={{ flex: 1, background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '8px', fontSize: '12px', color: '#0f172a', outline: 'none' }} />
                        <button onClick={() => { const logos = [...(selectedBlock.content.logos || [])]; logos.splice(i, 1); updateBlockContent(selectedBlock.id, { logos }); }} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}><Trash size={14} /></button>
                      </div>
                    ))}
                    <button onClick={() => { const logos = [...(selectedBlock.content.logos || []), { name: 'Yeni Logo', url: '' }]; updateBlockContent(selectedBlock.id, { logos }); }} style={{ padding: '8px', background: 'rgba(0,0,0,0.03)', color: '#6366f1', border: '1px dashed rgba(0,0,0,0.12)', borderRadius: '8px', fontSize: '12px', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}><Plus size={14} /> Logo Ekle</button>
                  </div>
                )}

                {/* ── Social Links Editor ── */}
                {selectedBlock.type === 'social-links' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '11px', color: '#64748b', fontWeight: '700', marginBottom: '6px' }}>Başlık</label>
                      <input type="text" value={selectedBlock.content.heading || ''} onChange={(e) => updateBlockContent(selectedBlock.id, { heading: e.target.value })} style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', fontSize: '12px', color: '#0f172a', outline: 'none' }} />
                    </div>
                    <label style={{ fontSize: '11px', color: '#64748b', fontWeight: '700', textTransform: 'uppercase' }}>Linkler</label>
                    {(selectedBlock.content.links || []).map((link, i) => (
                      <div key={i} style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <select value={link.platform || 'Instagram'} onChange={(e) => { const links = [...(selectedBlock.content.links || [])]; links[i] = { ...links[i], platform: e.target.value }; updateBlockContent(selectedBlock.id, { links }); }} style={{ width: '110px', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '8px', fontSize: '11px', color: '#0f172a', outline: 'none' }}>
                          <option>Instagram</option><option>Facebook</option><option>Twitter</option><option>YouTube</option><option>LinkedIn</option><option>TikTok</option>
                        </select>
                        <input type="text" placeholder="URL" value={link.url || ''} onChange={(e) => { const links = [...(selectedBlock.content.links || [])]; links[i] = { ...links[i], url: e.target.value }; updateBlockContent(selectedBlock.id, { links }); }} style={{ flex: 1, background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '8px', fontSize: '11px', color: '#0f172a', outline: 'none' }} />
                        <button onClick={() => { const links = [...(selectedBlock.content.links || [])]; links.splice(i, 1); updateBlockContent(selectedBlock.id, { links }); }} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}><Trash size={14} /></button>
                      </div>
                    ))}
                    <button onClick={() => { const links = [...(selectedBlock.content.links || []), { platform: 'Instagram', url: '' }]; updateBlockContent(selectedBlock.id, { links }); }} style={{ padding: '8px', background: 'rgba(0,0,0,0.03)', color: '#6366f1', border: '1px dashed rgba(0,0,0,0.12)', borderRadius: '8px', fontSize: '12px', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}><Plus size={14} /> Link Ekle</button>
                  </div>
                )}

                {/* ── HTML Embed Editor ── */}
                {selectedBlock.type === 'html-embed' && (
                  <div>
                    <label style={{ display: 'block', fontSize: '11px', color: '#64748b', fontWeight: '700', marginBottom: '6px' }}>HTML Kodu</label>
                    <textarea value={selectedBlock.content.code || ''} onChange={(e) => updateBlockContent(selectedBlock.id, { code: e.target.value })} rows={6} style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', fontSize: '11px', fontFamily: 'monospace', color: '#0f172a', outline: 'none', resize: 'vertical' }} />
                    <p style={{ fontSize: '9px', color: '#94a3b8', marginTop: '4px' }}>⚠️ HTML kodu doğrudan render edilir. Güvenli kod kullandığınızdan emin olun.</p>
                  </div>
                )}
              </div>
            ) : (
              // MAIN ELEMENTOR TABS CONTENT
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                {elementorTab === 'blocks' && (
                  <>
                    {/* Active Blocks List with Drag & Drop */}
                    <div>
                      <h3 style={{ fontSize: '12px', fontWeight: '800', color: '#64748b', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Aktif Sayfa Bölümleri</h3>
                      {blocks.length === 0 ? (
                        <p style={{ fontSize: '12px', color: '#64748b', fontStyle: 'italic', textAlign: 'center', padding: '20px', border: '1px dashed #334155', borderRadius: '8px' }}>
                          Henüz bir bölüm yok. Aşağıdan grafik bileşen sürükleyin veya tıklayarak ekleyin!
                        </p>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          {blocks.map((block, i) => (
                            <div
                              key={block.id}
                              onClick={() => setSelectedBlockId(block.id)}
                              draggable={true}
                              onDragStart={(e) => {
                                e.stopPropagation();
                                e.dataTransfer.setData("text/plain", i.toString());
                                e.currentTarget.style.opacity = '0.5';
                              }}
                              onDragEnd={(e) => {
                                e.currentTarget.style.opacity = '1';
                              }}
                              onDragOver={(e) => {
                                e.preventDefault();
                                e.currentTarget.style.borderTop = '3px solid #6366f1';
                              }}
                              onDragLeave={(e) => {
                                e.currentTarget.style.borderTop = '1px solid #334155';
                              }}
                              onDrop={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                e.currentTarget.style.borderTop = '1px solid #334155';
                                const fromIdx = parseInt(e.dataTransfer.getData("text/plain"), 10);
                                if (!isNaN(fromIdx) && fromIdx !== i) {
                                  handleDropBlock(fromIdx, i);
                                }
                              }}
                              onMouseOver={(e) => e.currentTarget.style.background = '#334155'}
                              onMouseOut={(e) => e.currentTarget.style.background = '#1e293b'}
                              style={{
                                background: '#1e293b',
                                border: '1px solid #334155',
                                padding: '10px 14px',
                                borderRadius: '8px',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                cursor: 'grab',
                                transition: 'all 0.2s'
                              }}
                            >
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                <span style={{ fontSize: '13px', fontWeight: '700', color: '#0f172a' }}>{block.title}</span>
                                <span style={{ fontSize: '10px', color: '#818cf8', textTransform: 'uppercase', fontWeight: '600' }}>{block.type}</span>
                              </div>
                              <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }} onClick={e => e.stopPropagation()}>
                                <span style={{ color: '#64748b', fontSize: '12px', cursor: 'grab', marginRight: '6px' }} title="Sürükle Taşı">☰</span>
                                <button
                                  type="button"
                                  onClick={() => moveBlock(i, -1)}
                                  disabled={i === 0}
                                  style={{ background: 'rgba(0,0,0,0.04)', border: 'none', color: '#475569', cursor: 'pointer', padding: '4px', borderRadius: '4px', opacity: i === 0 ? 0.3 : 1 }}
                                >
                                  <ChevronUp size={14} />
                                </button>
                                <button
                                  type="button"
                                  onClick={() => moveBlock(i, 1)}
                                  disabled={i === blocks.length - 1}
                                  style={{ background: 'rgba(0,0,0,0.04)', border: 'none', color: '#475569', cursor: 'pointer', padding: '4px', borderRadius: '4px', opacity: i === blocks.length - 1 ? 0.3 : 1 }}
                                >
                                  <ChevronDown size={14} />
                                </button>
                                <button
                                  type="button"
                                  onClick={() => deleteBlock(block.id)}
                                  style={{ background: 'rgba(239, 68, 68, 0.1)', border: 'none', color: '#f87171', cursor: 'pointer', padding: '4px', borderRadius: '4px', marginLeft: '6px' }}
                                >
                                  <Trash2 size={14} />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* ════════════════════════════════════════════ */}
                    {/* COMPONENT LIBRARY — Category-based UI       */}
                    {/* ════════════════════════════════════════════ */}
                    <div style={{ borderTop: '1px solid rgba(0,0,0,0.06)', paddingTop: '16px' }}>
                      
                      {/* Search Bar */}
                      <div style={{ position: 'relative', marginBottom: '14px' }}>
                        <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
                        <input
                          type="text"
                          placeholder="Bileşen ara..."
                          value={componentSearchQuery}
                          onChange={(e) => setComponentSearchQuery(e.target.value)}
                          style={{
                            width: '100%',
                            padding: '9px 12px 9px 32px',
                            background: '#f8fafc',
                            border: '1px solid rgba(0,0,0,0.08)',
                            borderRadius: '8px',
                            fontSize: '12px',
                            color: '#0f172a',
                            outline: 'none',
                            transition: 'all 0.2s'
                          }}
                          onFocus={(e) => { e.target.style.borderColor = '#6366f1'; e.target.style.boxShadow = '0 0 0 3px rgba(99,102,241,0.08)'; }}
                          onBlur={(e) => { e.target.style.borderColor = 'rgba(0,0,0,0.08)'; e.target.style.boxShadow = 'none'; }}
                        />
                      </div>

                      {/* Category Navigation Grid */}
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px', marginBottom: '16px' }}>
                        {COMPONENT_CATEGORIES.map(cat => {
                          const CatIcon = cat.icon;
                          const isActive = activeComponentCategory === cat.id;
                          const count = cat.id === 'all' ? COMPONENT_LIBRARY.length : COMPONENT_LIBRARY.filter(c => c.category === cat.id).length;
                          return (
                            <button
                              key={cat.id}
                              onClick={() => { setActiveComponentCategory(cat.id); setComponentSearchQuery(''); }}
                              style={{
                                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px',
                                padding: '8px 4px',
                                background: isActive ? `${cat.color}10` : '#fafafa',
                                border: isActive ? `1.5px solid ${cat.color}40` : '1px solid rgba(0,0,0,0.04)',
                                borderRadius: '8px', cursor: 'pointer', transition: 'all 0.15s', outline: 'none'
                              }}
                              onMouseOver={(e) => { if (!isActive) e.currentTarget.style.background = 'rgba(0,0,0,0.03)'; }}
                              onMouseOut={(e) => { if (!isActive) e.currentTarget.style.background = isActive ? `${cat.color}10` : '#fafafa'; }}
                            >
                              <CatIcon size={16} style={{ color: isActive ? cat.color : '#64748b' }} />
                              <span style={{ fontSize: '9px', fontWeight: '700', color: isActive ? cat.color : '#64748b', lineHeight: '1', textAlign: 'center' }}>{cat.label}</span>
                              <span style={{ fontSize: '8px', color: '#94a3b8', fontWeight: '600' }}>{count}</span>
                            </button>
                          );
                        })}
                      </div>

                      {/* Category Title */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                        <h3 style={{ fontSize: '12px', fontWeight: '800', color: '#334155', textTransform: 'uppercase', letterSpacing: '0.05em', margin: 0 }}>
                          {componentSearchQuery ? `"${componentSearchQuery}" Sonuçları` : (COMPONENT_CATEGORIES.find(c => c.id === activeComponentCategory)?.label || 'Tüm Bileşenler')}
                        </h3>
                      </div>

                      {/* Component Cards Grid */}
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                        {(() => {
                          let filtered = COMPONENT_LIBRARY;
                          if (activeComponentCategory !== 'all' && !componentSearchQuery.trim()) {
                            filtered = filtered.filter(c => c.category === activeComponentCategory);
                          }
                          if (componentSearchQuery.trim()) {
                            const q = componentSearchQuery.toLowerCase();
                            filtered = COMPONENT_LIBRARY.filter(c =>
                              c.label.toLowerCase().includes(q) || c.desc.toLowerCase().includes(q) ||
                              c.type.toLowerCase().includes(q) || (c.tags && c.tags.some(t => t.toLowerCase().includes(q)))
                            );
                          }
                          if (filtered.length === 0) {
                            return <div style={{ gridColumn: '1 / -1', padding: '24px', textAlign: 'center', color: '#94a3b8', fontSize: '12px' }}>Sonuç bulunamadı.</div>;
                          }
                          return filtered.map((widget) => {
                            const isLocked = widget.isPremium && activePlan !== 'Enterprise';
                            return (
                              <div key={widget.id}
                                onClick={() => { if (isLocked) { setShowUpgradeModal(true); return; } addBlockWithLayout(widget.type, widget.layout); }}
                                onMouseOver={(e) => { e.currentTarget.style.borderColor = isLocked ? '#e2e8f0' : '#6366f1'; e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = isLocked ? 'none' : '0 4px 12px rgba(99,102,241,0.12)'; }}
                                onMouseOut={(e) => { e.currentTarget.style.borderColor = 'rgba(0,0,0,0.06)'; e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none'; }}
                                style={{ background: '#fff', border: '1px solid rgba(0,0,0,0.06)', borderRadius: '10px', padding: '6px', cursor: isLocked ? 'not-allowed' : 'pointer', transition: 'all 0.2s ease', display: 'flex', flexDirection: 'column', gap: '6px', opacity: isLocked ? 0.65 : 1, position: 'relative' }}
                              >
                                {isLocked && (
                                  <div style={{ position: 'absolute', top: '8px', right: '8px', zIndex: 2, background: 'rgba(251,191,36,0.15)', border: '1px solid rgba(251,191,36,0.3)', borderRadius: '4px', padding: '2px 5px', display: 'flex', alignItems: 'center', gap: '3px' }}>
                                    <Lock size={8} style={{ color: '#f59e0b' }} /><span style={{ fontSize: '7px', fontWeight: '800', color: '#f59e0b' }}>PRO</span>
                                  </div>
                                )}
                                <div style={{ height: '52px', background: widget.previewBg, borderRadius: '6px', position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: '6px', boxShadow: 'inset 0 0 10px rgba(0,0,0,0.3)' }}>
                                  {widget.type === 'hero' && <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px', width: '100%' }}><div style={{ width: '55%', height: '3px', background: '#fff', borderRadius: '1px' }} /><div style={{ width: '35%', height: '1.5px', background: 'rgba(255,255,255,0.5)' }} /><div style={{ width: '22%', height: '4px', background: widget.previewAccent, borderRadius: '2px', marginTop: '1px' }} /></div>}
                                  {widget.type === 'about' && <div style={{ display: 'grid', gridTemplateColumns: '1fr 0.8fr', gap: '3px', width: '100%', height: '100%', alignItems: 'center' }}><div style={{ display: 'flex', flexDirection: 'column', gap: '1.5px' }}><div style={{ width: '40%', height: '2.5px', background: widget.previewAccent }} /><div style={{ width: '90%', height: '1.5px', background: 'rgba(255,255,255,0.5)' }} /><div style={{ width: '80%', height: '1.5px', background: 'rgba(255,255,255,0.5)' }} /></div><div style={{ height: '80%', background: 'rgba(255,255,255,0.12)', borderRadius: '2px' }} /></div>}
                                  {widget.type === 'menu' && <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '2px', width: '100%', height: '100%', alignItems: 'center' }}>{[1,2,3].map(i => <div key={i} style={{ background: 'rgba(255,255,255,0.08)', height: '80%', borderRadius: '2px', display: 'flex', flexDirection: 'column', padding: '1.5px', gap: '1px' }}><div style={{ height: '45%', background: 'rgba(255,255,255,0.15)', borderRadius: '1px' }} /><div style={{ width: '70%', height: '1.5px', background: '#fff' }} /><div style={{ width: '40%', height: '1.5px', background: widget.previewAccent }} /></div>)}</div>}
                                  {widget.type === 'testimonials' && <div style={{ display: 'flex', gap: '2px', width: '100%', height: '100%', alignItems: 'center' }}>{[1,2].map(i => <div key={i} style={{ background: 'rgba(255,255,255,0.08)', borderRadius: '3px', padding: '2px', flex: 1, display: 'flex', flexDirection: 'column', gap: '1px' }}><div style={{ display: 'flex', gap: '0.5px' }}>{[1,2,3].map(s => <span key={s} style={{ color: widget.previewAccent, fontSize: '3px' }}>★</span>)}</div><div style={{ width: '90%', height: '1.5px', background: 'rgba(255,255,255,0.5)' }} /></div>)}</div>}
                                  {widget.type === 'hours' && <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3px', width: '100%', height: '100%', alignItems: 'center' }}><div style={{ display: 'flex', flexDirection: 'column', gap: '1.5px' }}><div style={{ width: '80%', height: '2px', background: '#fff' }} /><div style={{ width: '60%', height: '1.5px', background: 'rgba(255,255,255,0.5)' }} /></div><div style={{ display: 'flex', flexDirection: 'column', gap: '1.5px', borderLeft: '1px solid rgba(255,255,255,0.2)', paddingLeft: '2px' }}><div style={{ width: '90%', height: '1.5px', background: widget.previewAccent }} /><div style={{ width: '70%', height: '1.5px', background: 'rgba(255,255,255,0.5)' }} /></div></div>}
                                  {widget.type === 'reservation' && <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}><div style={{ width: '50%', height: '2.5px', background: '#fff', borderRadius: '1px' }} /><div style={{ width: '60%', height: '8px', background: 'rgba(255,255,255,0.08)', borderRadius: '2px', border: '1px solid rgba(255,255,255,0.15)' }} /><div style={{ width: '35%', height: '5px', background: widget.previewAccent, borderRadius: '2px' }} /></div>}
                                  {widget.type === 'gallery' && <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '2px', width: '100%', height: '100%', alignItems: 'center' }}>{[1,2,3].map(i => <div key={i} style={{ background: 'rgba(255,255,255,0.12)', height: '80%', borderRadius: '2px' }} />)}</div>}
                                  {widget.type === 'cta' && <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}><div style={{ width: '60%', height: '3px', background: '#fff', borderRadius: '1px' }} /><div style={{ width: '40%', height: '1.5px', background: 'rgba(255,255,255,0.5)' }} /><div style={{ width: '30%', height: '5px', background: widget.previewAccent, borderRadius: '2px' }} /></div>}
                                  {widget.type === 'stats' && <div style={{ display: 'flex', gap: '4px', width: '100%', height: '100%', alignItems: 'center', justifyContent: 'center' }}>{[1,2,3,4].map(i => <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1px', flex: 1 }}><div style={{ width: '60%', height: '3px', background: widget.previewAccent, borderRadius: '1px' }} /><div style={{ width: '80%', height: '1.5px', background: 'rgba(255,255,255,0.5)' }} /></div>)}</div>}
                                  {widget.type === 'faq' && <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', width: '100%' }}>{[1,2,3].map(i => <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1px 2px', background: 'rgba(255,255,255,0.06)', borderRadius: '1px' }}><div style={{ width: '65%', height: '1.5px', background: 'rgba(255,255,255,0.5)' }} /><span style={{ fontSize: '4px', color: 'rgba(255,255,255,0.5)' }}>▸</span></div>)}</div>}
                                  {widget.type === 'spacer' && <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}><div style={{ width: '30%', height: '1px', borderTop: '1px dashed rgba(255,255,255,0.3)' }} /><span style={{ fontSize: '6px', color: 'rgba(255,255,255,0.4)', margin: '0 3px' }}>↕</span><div style={{ width: '30%', height: '1px', borderTop: '1px dashed rgba(255,255,255,0.3)' }} /></div>}
                                  {widget.type === 'divider' && <div style={{ width: '70%', height: '2px', background: `linear-gradient(90deg, transparent, ${widget.previewAccent}, transparent)` }} />}
                                  {widget.type === 'logo-strip' && <div style={{ display: 'flex', gap: '4px', alignItems: 'center', justifyContent: 'center' }}>{[1,2,3,4].map(i => <div key={i} style={{ width: '16px', height: '16px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', border: '1px solid rgba(255,255,255,0.15)' }} />)}</div>}
                                  {widget.type === 'social-links' && <div style={{ display: 'flex', gap: '4px', alignItems: 'center', justifyContent: 'center' }}>{['📸','📘','🐦','▶️'].map((em,i) => <span key={i} style={{ fontSize: '8px', background: 'rgba(255,255,255,0.1)', padding: '2px', borderRadius: '3px' }}>{em}</span>)}</div>}
                                  {widget.type === 'html-embed' && <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}><span style={{ fontSize: '8px', color: widget.previewAccent, fontFamily: 'monospace' }}>&lt;/&gt;</span><div style={{ width: '50%', height: '1.5px', background: 'rgba(255,255,255,0.3)' }} /></div>}
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', padding: '0 2px' }}>
                                  <span style={{ fontSize: '11px', fontWeight: '700', color: '#0f172a', lineHeight: '1.2' }}>{widget.label}</span>
                                  <span style={{ fontSize: '9px', color: '#94a3b8', lineHeight: '1.2' }}>{widget.desc}</span>
                                </div>
                              </div>
                            );
                          });
                        })()}
                      </div>
                    </div>
                  </>
                )}



                {elementorTab === 'presets' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    <div style={{ borderTop: '1px solid rgba(0,0,0,0.06)', paddingTop: '16px' }}>
                      <h3 style={{ fontSize: '12px', fontWeight: '800', color: '#64748b', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Renk & Yazı Tipi</h3>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        <div>
                          <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>Özel Tema Vurgu Rengi</label>
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <input
                              type="color"
                              value={themeColor}
                              onChange={(e) => setThemeColor(e.target.value)}
                              style={{
                                width: '40px',
                                height: '40px',
                                border: 'none',
                                borderRadius: '8px',
                                background: 'transparent',
                                cursor: 'pointer',
                                padding: 0
                              }}
                            />
                            <input
                              type="text"
                              value={themeColor}
                              onChange={(e) => {
                                const val = e.target.value;
                                if (val.startsWith('#') && val.length <= 7) {
                                  setThemeColor(val);
                                }
                              }}
                              placeholder="#6366f1"
                              style={{
                                flex: 1,
                                background: '#0f172a',
                                border: '1px solid #475569',
                                borderRadius: '8px',
                                padding: '10px',
                                color: '#0f172a',
                                fontSize: '13px',
                                outline: 'none',
                                fontFamily: 'monospace'
                              }}
                            />
                          </div>
                          <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                            {['#6366f1', '#d4af37', '#d96a3b', '#10b981', '#ec4899'].map(color => (
                              <button
                                key={color}
                                type="button"
                                onClick={() => setThemeColor(color)}
                                style={{
                                  width: '20px',
                                  height: '20px',
                                  borderRadius: '50%',
                                  background: color,
                                  border: themeColor === color ? '2px solid #fff' : '1px solid rgba(255,255,255,0.2)',
                                  cursor: 'pointer',
                                  padding: 0
                                }}
                              />
                            ))}
                          </div>
                        </div>

                        <div>
                          <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>Yazı Karakteri (Typography)</label>
                          <select
                            value={typography}
                            onChange={(e) => setTypography(e.target.value)}
                            style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none' }}
                          >
                            <option value="Sans-serif">Sans-serif (Modern & Sade)</option>
                            <option value="Outfit">Outfit (Zarif & Dinamik)</option>
                            <option value="Serif">Serif (Klasik & Lüks)</option>
                            <option value="Monospace">Monospace (Retro & Kod)</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {elementorTab === 'pages' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', position: 'relative' }}>
                    {/* Pages section */}
                    <div>
                      <h3 style={{ fontSize: '12px', fontWeight: '800', color: '#64748b', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Sayfalar & Menü Yapısı</h3>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {pages.map((p) => {
                          const isHome = p.id === 'home';
                          const isActive = p.id === activePageId;
                          return (
                            <div
                              key={p.id}
                              onClick={() => {
                                if (activePlan !== 'Enterprise' && !isHome) {
                                  setShowUpgradeModal(true);
                                  return;
                                }
                                handleSelectPage(p.id);
                              }}
                              onMouseOver={e => {
                                if (activePlan !== 'Enterprise' && !isHome) e.currentTarget.style.borderColor = '#fbbf24';
                              }}
                              onMouseOut={e => {
                                e.currentTarget.style.borderColor = isActive ? '#6366f1' : '#334155';
                              }}
                              style={{
                                background: isActive ? 'rgba(99, 102, 241, 0.15)' : 'rgba(30, 41, 59, 0.6)',
                                border: isActive ? '1px solid #6366f1' : '1px solid #334155',
                                borderRadius: '8px',
                                padding: '12px',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                cursor: 'pointer',
                                transition: 'all 0.2s',
                                position: 'relative'
                              }}
                            >
                              <div>
                                <span style={{ fontSize: '13px', fontWeight: '700', color: (activePlan !== 'Enterprise' && !isHome) ? '#64748b' : '#fff', display: 'block' }}>
                                  {p.title}
                                </span>
                                <span style={{ fontSize: '10px', color: isHome ? '#10b981' : '#64748b' }}>
                                  {isHome ? 'Ana Sayfa (Varsayılan)' : `/w/${domain || 'site'}/${p.slug}`}
                                </span>
                              </div>

                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }} onClick={e => e.stopPropagation()}>
                                {isHome ? (
                                  <span style={{ background: 'rgba(16,185,129,0.1)', color: '#10b981', fontSize: '9px', fontWeight: 'bold', padding: '2px 6px', borderRadius: '4px' }}>VARSAYILAN</span>
                                ) : (
                                  <>
                                    {activePlan !== 'Enterprise' ? (
                                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#fbbf24' }}>
                                        <Lock size={12} />
                                        <span style={{ fontSize: '10px', fontWeight: 'bold' }}>PREMIUM</span>
                                      </div>
                                    ) : (
                                      <button
                                        type="button"
                                        onClick={() => {
                                          if (window.confirm(`"${p.title}" sayfasını silmek istediğinizden emin misiniz?`)) {
                                            const updated = pages.filter(pg => pg.id !== p.id);
                                            setPages(updated);
                                            if (activePageId === p.id) {
                                              handleSelectPage('home');
                                            }
                                          }
                                        }}
                                        style={{ background: 'rgba(239, 68, 68, 0.15)', border: 'none', color: '#f87171', cursor: 'pointer', padding: '4px', borderRadius: '4px' }}
                                      >
                                        <Trash2 size={12} />
                                      </button>
                                    )}
                                  </>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {/* Add page button */}
                      <button
                        type="button"
                        onClick={() => {
                          if (activePlan !== 'Enterprise') {
                            setShowUpgradeModal(true);
                            return;
                          }
                          setShowAddPageDialog(true);
                        }}
                        style={{
                          width: '100%',
                          background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                          border: 'none',
                          color: '#0f172a',
                          padding: '10px',
                          borderRadius: '8px',
                          fontWeight: '750',
                          fontSize: '12px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '6px',
                          marginTop: '12px',
                          boxShadow: '0 4px 12px rgba(99,102,241,0.2)'
                        }}
                      >
                        <Plus size={14} /> Yeni Sayfa Ekle
                      </button>
                    </div>

                    {/* Active Page Settings Form (Rename & Slug) */}
                    {activePlan === 'Enterprise' && (
                      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', padding: '12px', marginTop: '4px' }}>
                        <h4 style={{ fontSize: '11px', fontWeight: '800', color: '#94a3b8', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Seçili Sayfa Ayarları</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                          <div>
                            <label style={{ display: 'block', fontSize: '10px', color: '#64748b', fontWeight: '600', marginBottom: '4px' }}>Sayfa Adı</label>
                            <input
                              type="text"
                              value={pages.find(p => p.id === activePageId)?.title || ''}
                              onChange={(e) => {
                                const val = e.target.value;
                                setPages(prev => prev.map(p => p.id === activePageId ? { ...p, title: val } : p));
                              }}
                              style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '8px', color: '#0f172a', fontSize: '12px', outline: 'none' }}
                            />
                          </div>
                          <div>
                            <label style={{ display: 'block', fontSize: '10px', color: '#64748b', fontWeight: '600', marginBottom: '4px' }}>Sayfa Adresi (Slug)</label>
                            <input
                              type="text"
                              value={pages.find(p => p.id === activePageId)?.slug || ''}
                              disabled={activePageId === 'home'}
                              onChange={(e) => {
                                const val = e.target.value.toLowerCase().replace(/[^a-z0-9-_]/g, '-');
                                setPages(prev => prev.map(p => p.id === activePageId ? { ...p, slug: val } : p));
                              }}
                              style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '6px', padding: '8px', color: '#0f172a', fontSize: '12px', outline: 'none', opacity: activePageId === 'home' ? 0.5 : 1 }}
                            />
                            {activePageId === 'home' && <span style={{ fontSize: '9px', color: '#64748b', display: 'block', marginTop: '2px' }}>Ana sayfa adresi değiştirilemez.</span>}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* SEO Meta Tags Section */}
                    <div style={{ borderTop: '1px solid rgba(0,0,0,0.06)', paddingTop: '16px', position: 'relative' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                        <h3 style={{ fontSize: '12px', fontWeight: '800', color: '#64748b', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Arama Motoru (SEO) Ayarları</h3>
                        {activePlan !== 'Enterprise' && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#fbbf24', fontSize: '11px', fontWeight: 'bold' }}>
                            <Lock size={12} /> Pro Plan
                          </div>
                        )}
                      </div>

                      <div style={{ position: 'relative', borderRadius: '12px', overflow: 'hidden' }}>
                        {activePlan !== 'Enterprise' && (
                          <div
                            onClick={() => setShowUpgradeModal(true)}
                            style={{
                              position: 'absolute',
                              top: 0,
                              left: 0,
                              right: 0,
                              bottom: 0,
                              background: 'rgba(30, 41, 59, 0.55)',
                              backdropFilter: 'blur(3px)',
                              zIndex: 10,
                              cursor: 'pointer',
                              display: 'flex',
                              flexDirection: 'column',
                              alignItems: 'center',
                              justifyContent: 'center',
                              gap: '8px'
                            }}
                          >
                            <div style={{
                              background: '#fbbf24',
                              color: '#000',
                              padding: '6px 12px',
                              borderRadius: '20px',
                              fontSize: '11px',
                              fontWeight: '800',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '6px',
                              boxShadow: '0 4px 12px rgba(251, 191, 36, 0.3)'
                            }}>
                              <Lock size={12} /> SEO Ayarlarını Aç
                            </div>
                            <span style={{ fontSize: '10px', color: '#64748b', fontWeight: '600' }}>Google ve arama motoru uyumluluğu için yükseltin</span>
                          </div>
                        )}

                        <div style={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '14px',
                          filter: activePlan !== 'Enterprise' ? 'blur(1.5px)' : 'none',
                          pointerEvents: activePlan !== 'Enterprise' ? 'none' : 'auto',
                          opacity: activePlan !== 'Enterprise' ? 0.7 : 1
                        }}>
                          <div>
                            <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>Sayfa Başlığı (Meta Title)</label>
                            <input
                              type="text"
                              value={seoTitle}
                              onChange={(e) => {
                                setSeoTitle(e.target.value);
                                setPages(prev => prev.map(p => p.id === activePageId ? {
                                  ...p,
                                  seo: { ...p.seo, title: e.target.value }
                                } : p));
                              }}
                              placeholder="Örn: En İyi Kebap Restoranı | Bidolu Restaurant"
                              style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none' }}
                            />
                          </div>

                          <div>
                            <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>Meta Açıklaması (Meta Description)</label>
                            <textarea
                              rows="3"
                              value={seoDescription}
                              onChange={(e) => {
                                setSeoDescription(e.target.value);
                                setPages(prev => prev.map(p => p.id === activePageId ? {
                                  ...p,
                                  seo: { ...p.seo, description: e.target.value }
                                } : p));
                              }}
                              placeholder="Örn: 20 yılı aşkın tecrübemiz ve taze malzemelerimizle hazırlanan eşsiz lezzetler Bidolu Restaurant'ta sizi bekliyor."
                              style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none', resize: 'vertical' }}
                            />
                          </div>

                          <div>
                            <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', fontWeight: '600', marginBottom: '6px' }}>Anahtar Kelimeler (Meta Keywords)</label>
                            <input
                              type="text"
                              value={seoKeywords}
                              onChange={(e) => {
                                setSeoKeywords(e.target.value);
                                setPages(prev => prev.map(p => p.id === activePageId ? {
                                  ...p,
                                  seo: { ...p.seo, keywords: e.target.value }
                                } : p));
                              }}
                              placeholder="Örn: kebap, istanbul restoran, lezzetli yemekler"
                              style={{ width: '100%', background: '#f8fafc', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '8px', padding: '10px', color: '#0f172a', fontSize: '13px', outline: 'none' }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Add Page Dialog overlay */}
                    {showAddPageDialog && (
                      <div style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'rgba(255, 255, 255, 0.98)',
                        zIndex: 100,
                        padding: '20px',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        gap: '14px',
                        borderRadius: '12px',
                        boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                        border: '1px solid rgba(0,0,0,0.06)'
                      }}>
                        <h3 style={{ fontSize: '14px', fontWeight: '800', color: '#0f172a', margin: 0 }}>Yeni Sayfa Ekle</h3>
                        <div>
                          <label style={{ display: 'block', fontSize: '11px', color: '#475569', marginBottom: '4px' }}>Sayfa Adı</label>
                          <input
                            type="text"
                            value={newPageTitle}
                            onChange={(e) => {
                              setNewPageTitle(e.target.value);
                              setNewPageSlug(e.target.value.toLowerCase()
                                .replace(/ğ/g, 'g')
                                .replace(/ü/g, 'u')
                                .replace(/ş/g, 's')
                                .replace(/ı/g, 'i')
                                .replace(/ö/g, 'o')
                                .replace(/ç/g, 'c')
                                .replace(/[^a-z0-9\s-]/g, '')
                                .replace(/\s+/g, '-'));
                            }}
                            placeholder="Örn: Hakkımızda, Rezervasyon"
                            style={{ width: '100%', background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '8px 10px', color: '#0f172a', fontSize: '13px', outline: 'none' }}
                          />
                        </div>
                        <div>
                          <label style={{ display: 'block', fontSize: '11px', color: '#475569', marginBottom: '4px' }}>Sayfa URL'i (Slug)</label>
                          <input
                            type="text"
                            value={newPageSlug}
                            onChange={(e) => setNewPageSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-_]/g, '-'))}
                            placeholder="hakkimizda"
                            style={{ width: '100%', background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '8px 10px', color: '#0f172a', fontSize: '13px', outline: 'none' }}
                          />
                        </div>
                        <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
                          <button
                            type="button"
                            onClick={() => {
                              setShowAddPageDialog(false);
                              setNewPageTitle('');
                              setNewPageSlug('');
                            }}
                            style={{
                              flex: 1,
                              background: 'rgba(0,0,0,0.03)',
                              border: '1px solid #cbd5e1',
                              color: '#64748b',
                              padding: '8px',
                              borderRadius: '8px',
                              cursor: 'pointer',
                              fontWeight: '700',
                              fontSize: '12px'
                            }}
                          >
                            İptal
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              if (!newPageTitle.trim() || !newPageSlug.trim()) {
                                alert("Lütfen sayfa adı ve slug alanlarını doldurun.");
                                return;
                              }
                              if (pages.some(p => p.slug === newPageSlug)) {
                                alert("Bu slug zaten kullanılıyor, lütfen başka bir slug seçin.");
                                return;
                              }
                              const newId = `page-${Date.now()}`;
                              const newPage = {
                                id: newId,
                                title: newPageTitle,
                                slug: newPageSlug,
                                blocks: [
                                  {
                                    id: `hero-${Date.now()}`,
                                    type: 'hero',
                                    title: 'Giriş',
                                    content: {
                                      banner: newPageTitle,
                                      subtitle: 'Bu sayfa yeni oluşturuldu. Canlı Editör ile düzenleyebilirsiniz.',
                                      button_text: 'Ana Sayfaya Dön',
                                      button_url: '#',
                                      layout: 'center'
                                    }
                                  }
                                ],
                                seo: { title: `${newPageTitle} | ${resName || 'Bidolu Restaurant'}`, description: '', keywords: '' }
                              };
                              const updatedPages = [...pages, newPage];
                              setPages(updatedPages);
                              setShowAddPageDialog(false);
                              setNewPageTitle('');
                              setNewPageSlug('');
                              handleSelectPage(newId);
                            }}
                            style={{
                              flex: 1,
                              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                              border: 'none',
                              color: '#0f172a',
                              padding: '8px',
                              borderRadius: '8px',
                              cursor: 'pointer',
                              fontWeight: '700',
                              fontSize: '12px'
                            }}
                          >
                            Ekle
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {elementorTab === 'upgrade' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    <div style={{
                      background: 'linear-gradient(135deg, rgba(251,191,36,0.1) 0%, rgba(217,119,6,0.05) 100%)',
                      border: '1px solid rgba(251, 191, 36, 0.2)',
                      borderRadius: '14px',
                      padding: '20px',
                      textAlign: 'center'
                    }}>
                      <div style={{
                        width: '48px',
                        height: '48px',
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #fbbf24 0%, #d97706 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#000',
                        margin: '0 auto 16px',
                        boxShadow: '0 4px 12px rgba(251, 191, 36, 0.3)'
                      }}>
                        <Star size={24} fill="#000" />
                      </div>

                      <h4 style={{ fontSize: '15px', fontWeight: '800', color: '#0f172a', margin: '0 0 6px 0' }}>Profesyonel Web Sitesi</h4>
                      <p style={{ fontSize: '11px', color: '#64748b', margin: '0 0 16px 0', lineHeight: '1.4' }}>Sınırları kaldırın ve tam kapsamlı kurumsal dijital kimliğinizi oluşturun.</p>
                      
                      {activePlan === 'Enterprise' ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          <div style={{
                            background: 'rgba(16, 185, 129, 0.15)',
                            border: '1px solid #10b981',
                            color: '#34d399',
                            borderRadius: '8px',
                            padding: '10px',
                            fontSize: '12px',
                            fontWeight: '700',
                            textAlign: 'center'
                          }}>
                            Mevcut Planınız: Profesyonel Plan ✅
                          </div>
                          <button
                            type="button"
                            onClick={() => simulateDowngrade()}
                            style={{
                              width: '100%',
                              padding: '8px 10px',
                              background: 'rgba(239, 68, 68, 0.15)',
                              border: '1px solid #f87171',
                              color: '#f87171',
                              borderRadius: '8px',
                              fontSize: '11px',
                              fontWeight: '700',
                              cursor: 'pointer',
                              transition: 'all 0.2s',
                              outline: 'none'
                            }}
                            onMouseOver={(e) => { e.currentTarget.style.background = 'rgba(239, 68, 68, 0.25)' }}
                            onMouseOut={(e) => { e.currentTarget.style.background = 'rgba(239, 68, 68, 0.15)' }}
                          >
                            Planı Düşür (Simüle Et)
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => simulateUpgrade()}
                          style={{
                            width: '100%',
                            padding: '10px',
                            background: 'linear-gradient(90deg, #fbbf24 0%, #f59e0b 100%)',
                            color: '#000',
                            border: 'none',
                            borderRadius: '8px',
                            fontWeight: '800',
                            fontSize: '12.5px',
                            cursor: 'pointer',
                            boxShadow: '0 4px 10px rgba(251, 191, 36, 0.2)',
                            transition: 'all 0.2s',
                            outline: 'none'
                          }}
                        >
                          Şimdi Yükselt (Simüle Et)
                        </button>
                      )}
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <h4 style={{ fontSize: '12px', fontWeight: '800', color: '#64748b', textTransform: 'uppercase', margin: '0 0 4px 0' }}>Plan Özellikleri</h4>
                      {[
                        { title: "Çoklu Sayfa Desteği", desc: "Hakkımızda, Menü, Rezervasyon, İletişim sayfaları ekleme." },
                        { title: "Arama Motoru (SEO)", desc: "Sayfa meta başlıkları, açıklaması ve site haritası desteği." },
                        { title: "Google Analytics Entegrasyonu", desc: "Ziyaretçi trafiği ve tıklama istatistiklerini anlık izleyin." },
                        { title: "Özel Alan Adı Yönlendirme", desc: "Kendi com/net/org domaininizi ücretsiz bağlayın." }
                      ].map((item, i) => (
                        <div key={i} style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                          <span style={{ color: '#fbbf24', fontWeight: 'bold', fontSize: '13px' }}>✓</span>
                          <div>
                            <strong style={{ fontSize: '12px', color: '#f8fafc', display: 'block' }}>{item.title}</strong>
                            <span style={{ fontSize: '10.5px', color: '#94a3b8', lineHeight: '1.3' }}>{item.desc}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Preview Pane */}
        <div style={{
          background: '#f8fafc',
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          overflow: 'hidden'
        }}>
          {/* Header Device Switcher */}
          <div style={{
            padding: '12px 24px',
            borderBottom: '1px solid rgba(0, 0, 0, 0.06)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: '#f8fafc'
          }}>
            <span style={{ fontSize: '13px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Eye size={16} /> Canlı Önizleme & Görsel Düzenleme
            </span>
            <div style={{ display: 'flex', gap: '6px', background: 'rgba(0, 0, 0, 0.04)', padding: '4px', borderRadius: '8px' }}>
              {Object.entries(DEVICE_CONFIGS).map(([key, cfg]) => {
                const Icon = cfg.icon;
                return (
                  <button
                    key={key}
                    onClick={() => setElementorDevice(key)}
                    style={{
                      background: elementorDevice === key ? '#6366f1' : 'transparent',
                      color: elementorDevice === key ? '#fff' : '#475569',
                      border: 'none',
                      padding: '6px 12px',
                      borderRadius: '6px',
                      fontSize: '11px',
                      fontWeight: '600',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <Icon size={12} /> {cfg.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Viewport Area */}
          <div style={{
            flex: 1,
            padding: '24px',
            overflowY: 'auto',
            display: 'flex',
            justifyContent: 'center',
            background: '#f1f5f9',
            backgroundImage: 'radial-gradient(rgba(0,0,0,0.02) 1px, transparent 0)',
            backgroundSize: '24px 24px'
          }}>
            <div style={{
              width: DEVICE_CONFIGS[elementorDevice].width,
              maxWidth: '100%',
              transition: 'all 0.35s ease',
              borderRadius: elementorDevice !== 'desktop' ? '16px' : '0',
              overflow: 'hidden',
              boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)',
              border: elementorDevice !== 'desktop' ? '8px solid #334155' : 'none',
              background: '#000',
              height: 'fit-content'
            }}>
              <WebsitePreview
                tpl={currentTpl}
                domain={domain}
                aboutText={aboutText}
                instagram={instagram}
                facebook={facebook}
                enableReservation={enableReservation}
                bannerText={bannerText}
                resName={resName}
                device={elementorDevice}
                blocks={blocks}
                elementorMode={true}
                selectedBlockId={selectedBlockId}
                onSelectBlock={setSelectedBlockId}
                onMoveBlock={moveBlock}
                onDeleteBlock={deleteBlock}
                onDropBlock={handleDropBlock}
                themeColor={themeColor}
                typography={typography}
                pages={pages}
                activePageId={activePageId}
                onSelectPage={handleSelectPage}
              />
            </div>
          </div>
        </div>

        {/* Plan Upgrade Modal Overlay */}
        {showUpgradeModal && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(9, 13, 22, 0.85)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10000,
            padding: '20px'
          }}>
            <div style={{
              background: '#ffffff',
              border: '1px solid rgba(79, 70, 229, 0.15)',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.15), 0 0 40px rgba(79, 70, 229, 0.06)',
              borderRadius: '20px',
              maxWidth: '540px',
              width: '100%',
              padding: '36px',
              position: 'relative',
              textAlign: 'center'
            }}>
              <button
                onClick={() => setShowUpgradeModal(false)}
                style={{
                  position: 'absolute',
                  top: '20px',
                  right: '20px',
                  background: 'none',
                  border: 'none',
                  color: '#64748b',
                  cursor: 'pointer',
                  fontSize: '20px',
                  fontWeight: '600'
                }}
              >
                ✕
              </button>

              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #fbbf24 0%, #d97706 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#000',
                margin: '0 auto 24px',
                boxShadow: '0 8px 24px rgba(251, 191, 36, 0.4)'
              }}>
                <Star size={32} fill="#000" />
              </div>

              <h2 style={{ fontSize: '24px', fontWeight: '800', color: '#0f172a', margin: '0 0 8px 0' }}>
                Profesyonel Web Sitesi Planı
              </h2>
              <p style={{ fontSize: '14px', color: '#64748b', margin: '0 0 28px 0', lineHeight: '1.5' }}>
                Canlı Editör ile çoklu sayfalar oluşturun, detaylı SEO ayarları yapın ve sitenizi profesyonel düzeye taşıyın!
              </p>

              <div style={{
                textAlign: 'left',
                background: 'rgba(79, 70, 229, 0.03)',
                border: '1px solid rgba(79, 70, 229, 0.08)',
                borderRadius: '12px',
                padding: '20px',
                marginBottom: '28px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}>
                {[
                  { title: "Çoklu Sayfa Özelliği", desc: "Hakkımızda, Menü, Rezervasyon, İletişim vb. sayfalar oluşturma." },
                  { title: "Gelişmiş SEO Ayarları", desc: "Sayfa meta başlığı, açıklaması, anahtar kelimeler ve site haritası." },
                  { title: "Özel Alan Adı Yönlendirme", desc: "Kendi com/net domaininizi ücretsiz bağlayın." },
                  { title: "Ziyaretçi Analitiği Entegrasyonu", desc: "Google Analytics ve tıklama istatistiklerini izleyin." },
                  { title: "Gelişmiş Tasarım Bileşenleri", desc: "Tüm Canlı Editör modülleri ve premium temalar." }
                ].map((item, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                    <span style={{ color: '#fbbf24', fontSize: '16px', fontWeight: 'bold', lineHeight: '1' }}>✓</span>
                    <div>
                      <strong style={{ fontSize: '13px', color: '#0f172a', display: 'block' }}>{item.title}</strong>
                      <span style={{ fontSize: '11px', color: '#64748b' }}>{item.desc}</span>
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <button
                  onClick={() => simulateUpgrade()}
                  style={{
                    width: '100%',
                    padding: '14px',
                    background: 'linear-gradient(90deg, #fbbf24 0%, #f59e0b 100%)',
                    color: '#000',
                    border: 'none',
                    borderRadius: '12px',
                    fontWeight: '800',
                    fontSize: '14.5px',
                    cursor: 'pointer',
                    boxShadow: '0 4px 20px rgba(251, 191, 36, 0.3)',
                    transition: 'all 0.2s',
                    outline: 'none'
                  }}
                >
                  Profesyonel Plana Yükselt (Simüle Et)
                </button>
                <button
                  onClick={() => setShowUpgradeModal(false)}
                  style={{
                    width: '100%',
                    padding: '12px',
                    background: 'transparent',
                    color: '#94a3b8',
                    border: '1px solid #475569',
                    borderRadius: '12px',
                    fontWeight: '600',
                    fontSize: '13px',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  Daha Sonra
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const currentTpl = TEMPLATES.find(t => t.id === selectedTemplate) || TEMPLATES[0];

  const sectionBtn = (key, label, icon) => {
    const Icon = icon;
    return (
      <button
        type="button"
        onClick={() => setActiveSection(key)}
        style={{
          padding: '7px 14px',
          fontSize: '12px',
          borderRadius: '8px',
          border: 'none',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          fontWeight: '600',
          background: activeSection === key ? 'var(--primary)' : 'rgba(255,255,255,0.04)',
          color: activeSection === key ? '#fff' : 'var(--text-muted)',
          transition: 'all 0.2s'
        }}
      >
        <Icon size={13} /> {label}
      </button>
    );
  };

  if (loading) return <div className="spinner" style={{ margin: '60px auto' }} />;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '380px 1fr', gap: isMobile ? '16px' : '24px', alignItems: 'start' }}>

      {/* ─── LEFT PANEL: Editor ─── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

        {/* Canlı Görsel Editör Trigger Button */}
        <button
          type="button"
          onClick={() => setShowElementorModal(true)}
          style={{
            width: '100%',
            padding: '12px 16px',
            background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
            color: '#ffffff',
            border: 'none',
            borderRadius: '12px',
            fontWeight: '700',
            fontSize: '13px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            boxShadow: '0 4px 15px rgba(79, 70, 229, 0.25)',
            transition: 'all 0.2s',
            outline: 'none'
          }}
          onMouseOver={(e) => { e.currentTarget.style.transform = 'translateY(-1px)'; e.currentTarget.style.boxShadow = '0 6px 20px rgba(79, 70, 229, 0.35)'; }}
          onMouseOut={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 4px 15px rgba(79, 70, 229, 0.25)'; }}
        >
          <span>✨ Canlı Editör</span>
        </button>

        {/* Section tabs */}
        <div style={{ display: 'flex', gap: '8px', background: 'rgba(255,255,255,0.02)', padding: '8px', borderRadius: '12px', border: '1px solid var(--panel-border)' }}>
          {sectionBtn('content', 'İçerik', Type)}
          {sectionBtn('design', 'Tasarım', Image)}
          {sectionBtn('settings', 'Ayarlar', Link)}
        </div>

        <form onSubmit={handleSave}>
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

            {/* ── CONTENT SECTION ── */}
            {activeSection === 'content' && (
              <>
                <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Type size={16} style={{ color: 'var(--primary)' }} /> İçerik Düzenleyici
                </h3>

                <div className="form-group">
                  <label>Hero Banner Yazısı</label>
                  <input
                    type="text"
                    className="form-control"
                    value={bannerText}
                    onChange={(e) => handleBannerTextChange(e.target.value)}
                    placeholder="Eşsiz Lezzetlerin Buluşma Noktası"
                  />
                  <small style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                    Ana sayfanın üst kısmında büyük yazı olarak görünür
                  </small>
                </div>

                <div className="form-group">
                  <label>Hakkımızda / Hikayemiz</label>
                  <textarea
                    className="form-control"
                    rows="4"
                    value={aboutText}
                    onChange={(e) => handleAboutTextChange(e.target.value)}
                    placeholder="Restoranınızın kuruluşu, mutfak kültürü ve vizyonu..."
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div className="form-group">
                    <label><AtSign size={12} style={{ verticalAlign: 'middle', marginRight: '4px' }} />Instagram</label>
                    <input type="text" className="form-control" placeholder="bidolu.kebap" value={instagram} onChange={(e) => setInstagram(e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label><AtSign size={12} style={{ verticalAlign: 'middle', marginRight: '4px' }} />Facebook</label>
                    <input type="text" className="form-control" placeholder="bidolu.kebap" value={facebook} onChange={(e) => setFacebook(e.target.value)} />
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '10px', border: '1px solid var(--panel-border)' }}>
                  <div>
                    <strong style={{ fontSize: '13px', display: 'block' }}>Online Rezervasyon Butonu</strong>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Müşteriler web sitenizden masa rezervasyonu yapabilir</span>
                  </div>
                  <button type="button" onClick={() => setEnableReservation(v => !v)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: enableReservation ? 'var(--success)' : 'var(--text-muted)' }}>
                    {enableReservation ? <ToggleRight size={28} /> : <ToggleLeft size={28} />}
                  </button>
                </div>
              </>
            )}

            {/* ── DESIGN SECTION ── */}
            {activeSection === 'design' && (
              <>
                <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Image size={16} style={{ color: 'var(--primary)' }} /> Tema & Tasarım
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {TEMPLATES.map(tpl => (
                    <div
                      key={tpl.id}
                      onClick={() => setSelectedTemplate(tpl.id)}
                      style={{
                        padding: '14px',
                        borderRadius: '12px',
                        border: `2px solid ${selectedTemplate === tpl.id ? 'var(--primary)' : 'var(--panel-border)'}`,
                        background: selectedTemplate === tpl.id ? 'rgba(99, 102, 241, 0.06)' : 'rgba(255,255,255,0.02)',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px'
                      }}
                    >
                      {/* Color dots preview */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flexShrink: 0 }}>
                        <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: tpl.bg, border: '1px solid rgba(255,255,255,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <div style={{ width: '14px', height: '3px', borderRadius: '2px', background: tpl.accent }} />
                        </div>
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <strong style={{ fontSize: '13px' }}>{tpl.name}</strong>
                          {selectedTemplate === tpl.id && <Check size={14} style={{ color: 'var(--primary)' }} />}
                        </div>
                        <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>{tpl.desc}</p>
                        <div style={{ display: 'flex', gap: '4px', marginTop: '6px' }}>
                          {[tpl.bg, tpl.accent, tpl.text].map((c, i) => (
                            <span key={i} style={{ width: '14px', height: '14px', borderRadius: '50%', background: c, border: '1px solid rgba(255,255,255,0.15)' }} />
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}

            {/* ── SETTINGS SECTION ── */}
            {activeSection === 'settings' && (
              <>
                <h3 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Link size={16} style={{ color: 'var(--primary)' }} /> Alan Adı & Yayın Ayarları
                </h3>

                <div className="form-group">
                  <label>Özel Alan Adı (Custom Domain)</label>
                  <input
                    type="text"
                    className="form-control"
                    value={domain}
                    onChange={(e) => setDomain(e.target.value.toLowerCase().replace(/\s+/g, ''))}
                    placeholder="www.restoraniniz.com"
                  />
                </div>

                <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px dashed var(--panel-border)', borderRadius: '10px', padding: '14px', fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.8' }}>
                  <span style={{ fontWeight: '700', color: 'var(--text-main)', display: 'block', marginBottom: '6px' }}>🌐 DNS Kurulum Rehberi</span>
                  Kendi alan adınızı yönlendirmek için DNS yönetim panelinizde şu kayıtları oluşturun:<br />
                  • <strong>A Record</strong>: <code style={{ background: 'rgba(255,255,255,0.06)', padding: '1px 5px', borderRadius: '3px' }}>@</code> ➜ <code style={{ background: 'rgba(255,255,255,0.06)', padding: '1px 5px', borderRadius: '3px' }}>76.76.21.21</code><br />
                  • <strong>CNAME Record</strong>: <code style={{ background: 'rgba(255,255,255,0.06)', padding: '1px 5px', borderRadius: '3px' }}>www</code> ➜ <code style={{ background: 'rgba(255,255,255,0.06)', padding: '1px 5px', borderRadius: '3px' }}>domains.bidolupos.com</code>
                </div>
              </>
            )}

            <button
              type="submit"
              disabled={saving}
              className="btn btn-primary"
              style={{ width: '100%', display: 'flex', gap: '8px', justifyContent: 'center', alignItems: 'center', background: saved ? 'var(--success)' : undefined, borderColor: saved ? 'var(--success)' : undefined, transition: 'all 0.3s' }}
            >
              {saved ? <><Check size={16} /> Kaydedildi!</> : saving ? 'Kaydediliyor...' : <><Save size={16} /> Değişiklikleri Kaydet</>}
            </button>
          </div>
        </form>
      </div>

      {/* ─── RIGHT PANEL: Live Preview ─── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', position: 'sticky', top: '24px' }}>

        {/* Device switcher toolbar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Eye size={15} style={{ color: 'var(--primary)' }} />
            <span style={{ fontSize: '13px', fontWeight: '700' }}>Canlı Önizleme</span>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', background: 'rgba(99,102,241,0.1)', padding: '2px 7px', borderRadius: '10px' }}>Anlık güncelleniyor</span>
          </div>
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: '4px', background: 'rgba(255,255,255,0.03)', padding: '4px', borderRadius: '10px', border: '1px solid var(--panel-border)' }}>
              {Object.entries(DEVICE_CONFIGS).map(([key, cfg]) => {
                const Icon = cfg.icon;
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setPreviewDevice(key)}
                    title={cfg.label}
                    style={{
                      padding: '6px 10px',
                      borderRadius: '7px',
                      border: 'none',
                      cursor: 'pointer',
                      background: previewDevice === key ? 'var(--primary)' : 'transparent',
                      color: previewDevice === key ? '#fff' : 'var(--text-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                      fontSize: '11px',
                      fontWeight: '600',
                      transition: 'all 0.15s'
                    }}
                  >
                    <Icon size={13} /> {cfg.label}
                  </button>
                );
              })}
            </div>
            {/* Open in new tab button */}
            <button
              type="button"
              onClick={() => {
                const baseUrl = (import.meta.env.VITE_API_URL || '');
                const siteSlug = domain || 'site';
                window.open(`${baseUrl}/w/${siteSlug}/`, '_blank');
              }}
              title="Siteyi yeni sekmede aç"
              style={{
                padding: '6px 12px',
                borderRadius: '8px',
                border: '1px solid var(--primary)',
                cursor: 'pointer',
                background: 'rgba(99, 102, 241, 0.08)',
                color: 'var(--primary)',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                fontSize: '11px',
                fontWeight: '600',
                transition: 'all 0.2s',
                whiteSpace: 'nowrap'
              }}
            >
              <ExternalLink size={13} /> Yeni Sekmede Aç
            </button>
          </div>
        </div>

        {/* Browser chrome mockup */}
        <div style={{ borderRadius: '14px', overflow: 'hidden', border: '1px solid var(--panel-border)', background: 'var(--bg-darker)', boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
          {/* Titlebar */}
          <div style={{ padding: '10px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--panel-border)' }}>
            <div style={{ display: 'flex', gap: '6px' }}>
              <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#ff5f56' }} />
              <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#ffbd2e' }} />
              <span style={{ width: '9px', height: '9px', borderRadius: '50%', background: '#27c93f' }} />
            </div>
            <div style={{ background: 'rgba(255,255,255,0.06)', padding: '4px 20px', borderRadius: '6px', fontSize: '10.5px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '5px', flex: 1, maxWidth: '260px', margin: '0 16px', justifyContent: 'center' }}>
              🔒 {domain || 'www.restoraniniz.com'} <ExternalLink size={9} />
            </div>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              {(() => { const Icon = DEVICE_CONFIGS[previewDevice].icon; return <Icon size={11} />; })()}
              {DEVICE_CONFIGS[previewDevice].label}
            </span>
          </div>

          {/* Preview viewport */}
          <div style={{ overflowX: 'auto', display: 'flex', justifyContent: previewDevice !== 'desktop' ? 'center' : 'stretch', background: previewDevice !== 'desktop' ? 'rgba(0,0,0,0.3)' : 'transparent', padding: previewDevice !== 'desktop' ? '16px' : '0' }}>
            <div style={{
              width: DEVICE_CONFIGS[previewDevice].width,
              minWidth: DEVICE_CONFIGS[previewDevice].width,
              maxWidth: DEVICE_CONFIGS[previewDevice].width,
              transition: 'all 0.35s ease',
              borderRadius: previewDevice !== 'desktop' ? '8px' : '0',
              overflow: 'hidden',
              boxShadow: previewDevice !== 'desktop' ? '0 4px 20px rgba(0,0,0,0.5)' : 'none'
            }}>
              <WebsitePreview
                tpl={currentTpl}
                domain={domain}
                aboutText={aboutText}
                instagram={instagram}
                facebook={facebook}
                enableReservation={enableReservation}
                bannerText={bannerText}
                resName={resName}
                device={previewDevice}
                blocks={blocks}
                onDropBlock={handleDropBlock}
                themeColor={themeColor}
                typography={typography}
                pages={pages}
                activePageId={activePageId}
                onSelectPage={handleSelectPage}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Visual Editor Modal Overlay */}
      {renderElementorModal()}
      {renderMediaLibraryModal()}
      {renderLayersPopup()}
    </div>
  );
}
