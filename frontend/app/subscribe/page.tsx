'use client';

import { useState } from 'react';

export default function SubscribePage() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus('loading');

    const res = await fetch('/api/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });

    const data = await res.json();

    if (res.ok) {
      setStatus('success');
      setMessage('You\'re subscribed. You\'ll receive the daily digest when new jobs are found.');
    } else {
      setStatus('error');
      setMessage(data.error || 'Something went wrong. Try again.');
    }
  }

  return (
    <main style={{ minHeight: '100vh', background: '#f5f5f5', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
      <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,.08)', padding: '40px 48px', maxWidth: 480, width: '100%' }}>

        <p style={{ margin: '0 0 4px', fontSize: 13, color: '#93c5fd', letterSpacing: '.05em', textTransform: 'uppercase', fontWeight: 600 }}>Atlanta Data Jobs</p>
        <h1 style={{ margin: '0 0 8px', fontSize: 22, fontWeight: 700, color: '#1e3a5f' }}>Daily Digest</h1>
        <p style={{ margin: '0 0 32px', fontSize: 15, color: '#555' }}>
          Get notified when new data roles appear at Atlanta-area companies.
        </p>

        {status === 'success' ? (
          <p style={{ color: '#16a34a', fontSize: 15 }}>{message}</p>
        ) : (
          <form onSubmit={handleSubmit}>
            <input
              type="email"
              required
              placeholder="your@email.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              style={{ width: '100%', padding: '10px 14px', fontSize: 15, border: '1px solid #e2e8f0', borderRadius: 6, marginBottom: 12, boxSizing: 'border-box', outline: 'none' }}
            />
            <button
              type="submit"
              disabled={status === 'loading'}
              style={{ width: '100%', padding: '10px 14px', fontSize: 15, fontWeight: 600, color: '#fff', background: '#1e3a5f', border: 'none', borderRadius: 6, cursor: status === 'loading' ? 'not-allowed' : 'pointer', opacity: status === 'loading' ? 0.7 : 1 }}
            >
              {status === 'loading' ? 'Subscribing...' : 'Subscribe'}
            </button>
            {status === 'error' && (
              <p style={{ color: '#dc2626', fontSize: 13, marginTop: 8 }}>{message}</p>
            )}
          </form>
        )}
      </div>
    </main>
  );
}
