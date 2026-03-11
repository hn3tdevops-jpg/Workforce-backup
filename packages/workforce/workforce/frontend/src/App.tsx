import React, { useEffect, useState } from 'react'
import LoginForm from './components/LoginForm'
import BusinessSelector from './components/BusinessSelector'
import { useAuth } from './hooks/useAuth'
import { api } from './api'
import Dashboard from './components/Dashboard'

interface Membership {
  business_id: string
  business_name: string
  status: string
  primary_location_id: string | null
}

export default function App() {
  const { user, loading, error, setError, login, logout } = useAuth()
  const [memberships, setMemberships] = useState<Membership[]>([])
  const [selectedBiz, setSelectedBiz] = useState<string | null>(null)

  useEffect(() => {
    if (!user) { setMemberships([]); return }
    api.memberships()
      .then(rows => {
        setMemberships(rows)
        if (rows.length === 1) setSelectedBiz(rows[0].business_id)
      })
      .catch(() => setMemberships([]))
  }, [user])

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f1117', color: '#94a3b8' }}>
        Loading…
      </div>
    )
  }

  if (!user) {
    return (
      <LoginForm
        onLogin={async (email, password) => {
          try { await login(email, password) }
          catch (e: any) {
            let msg = 'Login failed'
            try { msg = JSON.parse(e.message)?.detail ?? e.message } catch { msg = e.message }
            setError(msg)
            throw e
          }
        }}
        error={error}
      />
    )
  }

  const businesses = memberships.map(m => ({ id: m.business_id, name: m.business_name }))
  const activeMembership = memberships.find(m => m.business_id === selectedBiz)

  return (
    <div style={{ minHeight: '100vh', background: '#0f1117', color: '#e2e8f0', fontFamily: 'system-ui, sans-serif' }}>
      {/* Top bar */}
      <header style={{
        background: '#1a1d27', borderBottom: '1px solid #2d3748',
        padding: '0.75rem 1.5rem', display: 'flex', alignItems: 'center', gap: '1rem',
      }}>
        <span style={{ fontWeight: 700, fontSize: '1rem', color: '#60a5fa' }}>Workforce</span>
        <div style={{ flex: 1 }}>
          {businesses.length > 0 && (
            <BusinessSelector
              businesses={businesses}
              selected={selectedBiz}
              onSelect={setSelectedBiz}
            />
          )}
        </div>
        <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{user.email}</span>
        {user.is_superadmin && (
          <span style={{ fontSize: '0.7rem', background: '#7c3aed', color: '#fff', padding: '2px 6px', borderRadius: 4 }}>
            superadmin
          </span>
        )}
        <button
          onClick={logout}
          style={{ fontSize: '0.8rem', background: 'none', border: '1px solid #374151', color: '#94a3b8', padding: '4px 10px', borderRadius: 4, cursor: 'pointer' }}
        >
          Sign out
        </button>
      </header>

      {/* Main */}
      <main style={{ padding: '2rem 1.5rem' }}>
        {!selectedBiz ? (
          <div style={{ color: '#94a3b8' }}>
            {businesses.length === 0 ? 'No business memberships found.' : 'Select a business above to continue.'}
          </div>
        ) : (
          <div>
            <h2 style={{ marginTop: 0, color: '#e2e8f0' }}>
              {activeMembership?.business_name}
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
              Business ID: <code style={{ color: '#60a5fa' }}>{selectedBiz}</code>
            </p>
            <Dashboard businessId={selectedBiz!} businessName={activeMembership?.business_name ?? ''} isSuperadmin={user.is_superadmin} />
          </div>
        )}
      </main>
    </div>
  )
}
