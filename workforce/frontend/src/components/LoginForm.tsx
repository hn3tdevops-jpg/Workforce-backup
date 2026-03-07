import React, { useState } from 'react'

interface Props {
  onLogin: (email: string, password: string) => Promise<void>
  error: string | null
}

export default function LoginForm({ onLogin, error }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    try {
      await onLogin(email, password)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: '#0f1117', color: '#e2e8f0',
    }}>
      <form onSubmit={handleSubmit} style={{
        background: '#1a1d27', padding: '2rem', borderRadius: 8,
        width: 320, boxShadow: '0 4px 24px rgba(0,0,0,0.4)',
      }}>
        <h2 style={{ marginTop: 0, marginBottom: '1.5rem', fontSize: '1.25rem', fontWeight: 600 }}>
          Workforce Sign In
        </h2>

        {error && (
          <div style={{
            background: '#2d1b1b', border: '1px solid #7f1d1d', borderRadius: 4,
            padding: '0.5rem 0.75rem', marginBottom: '1rem', color: '#fca5a5', fontSize: '0.875rem',
          }}>
            {error}
          </div>
        )}

        <label style={{ display: 'block', marginBottom: '1rem' }}>
          <span style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: 4 }}>Email</span>
          <input
            type="email" value={email} onChange={e => setEmail(e.target.value)}
            required autoFocus
            style={inputStyle}
          />
        </label>

        <label style={{ display: 'block', marginBottom: '1.5rem' }}>
          <span style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: 4 }}>Password</span>
          <input
            type="password" value={password} onChange={e => setPassword(e.target.value)}
            required
            style={inputStyle}
          />
        </label>

        <button type="submit" disabled={busy} style={{
          width: '100%', padding: '0.6rem', background: busy ? '#374151' : '#3b82f6',
          color: '#fff', border: 'none', borderRadius: 4, cursor: busy ? 'not-allowed' : 'pointer',
          fontSize: '0.95rem', fontWeight: 500,
        }}>
          {busy ? 'Signing in…' : 'Sign In'}
        </button>
      </form>
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '0.5rem 0.6rem', background: '#0f1117',
  border: '1px solid #374151', borderRadius: 4, color: '#e2e8f0',
  fontSize: '0.9rem', boxSizing: 'border-box',
}
