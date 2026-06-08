import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Loader2, CreditCard } from 'lucide-react';

const API_BASE = (import.meta.env.VITE_API_URL || '') + '/api';

export default function PaymentResult({ type, authToken, onComplete }) {
  const params = new URLSearchParams(window.location.search);
  const provider = params.get('provider') || 'mock';
  const sessionId = params.get('session_id');
  const invoiceId = params.get('invoice_id');
  const errorMsg = params.get('error');

  const [status, setStatus] = useState(type === 'success' ? 'loading' : 'cancelled');
  const [message, setMessage] = useState('');
  const [invoice, setInvoice] = useState(null);

  useEffect(() => {
    if (type !== 'success') {
      setMessage(errorMsg || 'Ödeme iptal edildi veya tamamlanamadı.');
      return;
    }

    const verify = async () => {
      try {
        if (provider === 'stripe' && sessionId && authToken) {
          const res = await fetch(`${API_BASE}/payments/stripe/verify/?session_id=${sessionId}`, {
            headers: { Authorization: `Token ${authToken}` },
          });
          const data = await res.json();
          if (!res.ok) {
            setStatus('error');
            setMessage(data.error || 'Ödeme doğrulanamadı.');
            return;
          }
          setInvoice(data.invoice);
          setMessage(data.message || 'Ödeme başarıyla tamamlandı!');
          setStatus('success');
          if (onComplete) onComplete(data.user);
          return;
        }

        if (provider === 'iyzico' && invoiceId && authToken) {
          const meRes = await fetch(`${API_BASE}/auth/me/`, {
            headers: { Authorization: `Token ${authToken}` },
          });
          if (meRes.ok) {
            const meData = await meRes.json();
            if (onComplete) onComplete(meData.user);
          }
          setStatus('success');
          setMessage('iyzico ödemeniz başarıyla alındı. Planınız aktifleştirildi.');
          return;
        }

        if (provider === 'mock') {
          setStatus('success');
          setMessage('Test ödemesi tamamlandı.');
          return;
        }

        setStatus('success');
        setMessage('Ödeme işlemi tamamlandı.');
      } catch {
        setStatus('error');
        setMessage('Sunucuya bağlanılamadı.');
      }
    };

    verify();
  }, [type, provider, sessionId, invoiceId, authToken, errorMsg, onComplete]);

  const isSuccess = status === 'success';
  const isLoading = status === 'loading';

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', padding: '24px',
    }}>
      <div style={{
        width: '100%', maxWidth: '440px', background: '#fff', borderRadius: '20px',
        padding: '36px', textAlign: 'center', boxShadow: '0 25px 60px rgba(0,0,0,0.35)',
      }}>
        {isLoading ? (
          <Loader2 size={48} color="#6366f1" style={{ animation: 'spin 1s linear infinite', margin: '0 auto 20px' }} />
        ) : isSuccess ? (
          <CheckCircle size={48} color="#10b981" style={{ margin: '0 auto 20px' }} />
        ) : (
          <XCircle size={48} color="#ef4444" style={{ margin: '0 auto 20px' }} />
        )}

        <h1 style={{ margin: '0 0 10px', fontSize: '20px', fontWeight: '800', color: '#0f172a' }}>
          {isLoading ? 'Ödeme Doğrulanıyor...' : isSuccess ? 'Ödeme Başarılı' : 'Ödeme Tamamlanamadı'}
        </h1>
        <p style={{ margin: '0 0 20px', fontSize: '14px', color: '#64748b', lineHeight: 1.6 }}>{message}</p>

        {invoice && (
          <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '14px', marginBottom: '20px', fontSize: '13px', textAlign: 'left' }}>
            <div><CreditCard size={14} style={{ display: 'inline', marginRight: '6px' }} /><strong>{invoice.invoice_number}</strong></div>
            <div style={{ marginTop: '6px', color: '#475569' }}>
              {Number(invoice.amount).toLocaleString('tr-TR')} ₺ — {invoice.plan?.toUpperCase()}
            </div>
          </div>
        )}

        <a href="/dashboard" className="btn btn-primary" style={{ display: 'inline-block', padding: '12px 28px', textDecoration: 'none' }}>
          Panele Dön
        </a>
      </div>
    </div>
  );
}
