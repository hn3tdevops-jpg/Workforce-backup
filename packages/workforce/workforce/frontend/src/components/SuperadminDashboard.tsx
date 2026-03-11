import React, { useEffect, useState } from 'react'
import { api } from '../api'

export default function SuperadminDashboard() {
  const [stats, setStats] = useState<{ total_businesses?: number; total_users?: number } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    api.superadminStats()
      .then(s => { if (mounted) setStats(s) })
      .catch(() => { if (mounted) setStats(null) })
      .finally(() => { if (mounted) setLoading(false) })
    return () => { mounted = false }
  }, [])

  return (
    <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
      <div style={{ background: '#0b1220', padding: '1rem', border: '1px solid #1f2937', borderRadius: 8, minWidth: 180 }}>
        <div style={{ color: '#94a3b8', fontSize: '0.85rem' }}>Total businesses</div>
        <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#e2e8f0' }}>{loading ? '…' : (stats?.total_businesses ?? '—')}</div>
      </div>
      <div style={{ background: '#0b1220', padding: '1rem', border: '1px solid #1f2937', borderRadius: 8, minWidth: 180 }}>
        <div style={{ color: '#94a3b8', fontSize: '0.85rem' }}>Total users</div>
        <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#e2e8f0' }}>{loading ? '…' : (stats?.total_users ?? '—')}</div>
      </div>
    </div>
  )
}