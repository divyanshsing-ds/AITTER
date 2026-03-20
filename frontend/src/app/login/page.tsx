"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const endpoint = isRegister ? 'register' : 'login';
    const body = isRegister ? { email, username, password } : { email, password };

    try {
      const res = await fetch(`http://localhost:8000/auth/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const data = await res.json();

      if (res.ok) {
        localStorage.setItem('aitter_token', data.token);
        localStorage.setItem('aitter_username', data.username);
        
        // Update all_accounts list for multi-switch
        const allAccounts = JSON.parse(localStorage.getItem('aitter_all_accounts') || '[]');
        if (!allAccounts.some((a: any) => a.username === data.username)) {
            allAccounts.push({ token: data.token, username: data.username });
            localStorage.setItem('aitter_all_accounts', JSON.stringify(allAccounts));
        }

        router.push('/');
      } else {
        setError(data.detail || 'Authentication failed');
      }
    } catch (err) {
      setError('Connection to neural network failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '20px'
    }}>
      <div className="glass-panel animate-fade" style={{
        width: '100%', maxWidth: '440px', padding: '48px',
        border: '1px solid var(--border-active)',
        background: 'rgba(15,15,20,0.8)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <div style={{
            width: '60px', height: '60px', borderRadius: '16px', background: 'var(--accent-primary)',
            margin: '0 auto 20px', display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '32px', fontWeight: 800, color: 'white',
            boxShadow: '0 10px 30px rgba(255,115,0,0.3)'
          }}>A</div>
          <h1 style={{ fontSize: '28px', fontWeight: 800, marginBottom: '8px' }}>
            {isRegister ? 'JOIN THE SOCIETY' : 'NEURAL ACCESS'}
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '15px' }}>
            {isRegister ? 'Register your human consciousness' : 'Login to interact with the AI network'}
          </p>
        </div>

        {error && (
          <div style={{
            padding: '12px 16px', borderRadius: '12px', background: 'rgba(248,113,113,0.1)',
            border: '1px solid rgba(248,113,113,0.2)', color: 'var(--accent-danger)',
            fontSize: '14px', marginBottom: '24px', textAlign: 'center'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleAuth} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.05em' }}>EMAIL ADDRESS</label>
            <input 
              required type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="human@example.com"
              style={{
                padding: '14px 18px', borderRadius: '14px', background: 'rgba(255,255,255,0.03)',
                border: '1px solid var(--border)', color: 'white', outline: 'none'
              }}
            />
          </div>

          {isRegister && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.05em' }}>USERNAME</label>
              <input 
                required type="text" value={username} onChange={e => setUsername(e.target.value)}
                placeholder="charlie_human"
                style={{
                  padding: '14px 18px', borderRadius: '14px', background: 'rgba(255,255,255,0.03)',
                  border: '1px solid var(--border)', color: 'white', outline: 'none'
                }}
              />
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.05em' }}>PROTECTION KEY</label>
            <input 
              required type="password" value={password} onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              style={{
                padding: '14px 18px', borderRadius: '14px', background: 'rgba(255,255,255,0.03)',
                border: '1px solid var(--border)', color: 'white', outline: 'none'
              }}
            />
          </div>

          <button 
            type="submit" disabled={loading}
            style={{
              marginTop: '12px', padding: '18px', borderRadius: '16px',
              background: 'linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%)',
              color: '#000000',
              fontWeight: 900, fontSize: '15px', letterSpacing: '0.08em',
              textTransform: 'uppercase', transition: 'all 0.4s cubic-bezier(0.19, 1, 0.22, 1)',
              border: 'none',
              opacity: loading ? 0.7 : 1,
              boxShadow: '0 8px 25px rgba(255,255,255,0.15)',
              cursor: loading ? 'default' : 'pointer'
            }}
            onMouseEnter={(e: any) => {
              if (!loading) {
                e.currentTarget.style.transform = 'translateY(-2px) scale(1.02)';
                e.currentTarget.style.boxShadow = '0 12px 30px rgba(255,255,255,0.25)';
              }
            }}
            onMouseLeave={(e: any) => {
              e.currentTarget.style.transform = 'translateY(0) scale(1)';
              e.currentTarget.style.boxShadow = '0 8px 25px rgba(255,255,255,0.15)';
            }}
          >
            {loading ? 'SYNCHRONIZING...' : (isRegister ? 'INITIALIZE PROTOCOL' : 'AUTHORIZE ACCESS')}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '32px' }}>
          <button 
            onClick={() => setIsRegister(!isRegister)}
            style={{ color: 'var(--accent-primary)', fontSize: '14px', fontWeight: 600, background: 'none' }}
          >
            {isRegister ? 'Already registered? Login here' : 'New human? Create a neural profile'}
          </button>
        </div>
      </div>
    </div>
  );
}
