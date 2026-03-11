import React, { useEffect, useState } from 'react'
import { api } from '../api'

export default function OpenShiftsWidget({ businessId }: { businessId: string }) {
  const [count, setCount] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    api.openShiftsCount(businessId)
      .then(n => { if (mounted) setCount(n) })
      .catch(() => { if (mounted) setCount(null) })
      .finally(() => { if (mounted) setLoading(false) })
    return () => { mounted = false }
  }, [businessId])

  return (
    <div style={{ background: '#0b1220', padding: '1rem', border: '1px solid #1f2937', borderRadius: 8 }}>
      <div style={{ color: '#94a3b8', fontSize: '0.85rem' }}>Open shifts</div>
      <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#e2e8f0' }}>
        {loading ? '…' : (count ?? '—')}
      </div>
    </div>
  )
}