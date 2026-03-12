"use client"
import { useEffect, useState } from 'react'
import { api, PropertyTree } from '../../lib/api'

const LOCATION_ID = process.env.NEXT_PUBLIC_LOCATION_ID ?? 'silver-sands-main'

export default function PropertySetupPage() {
  const [tree, setTree] = useState<PropertyTree | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getPropertyTree(LOCATION_ID)
      .then(setTree)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Property Setup</h1>
        <p className="page-subtitle">Buildings, floors, and sectors for Silver Sands Motel</p>
      </div>
      {error && <div className="alert alert-error">{error}</div>}
      {loading ? (
        <div className="loading">Loading property structure…</div>
      ) : !tree || tree.buildings.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🏗️</div>
          <div className="empty-state-text">No property structure found. Run the Silver Sands seed script to set up buildings, floors, and sectors.</div>
        </div>
      ) : tree.buildings.map((b) => (
        <div key={b.id} className="card">
          <h2 className="font-bold mb-2">🏢 {b.name} <span className="text-muted text-sm">({b.code})</span></h2>
          {b.floors.map((f) => (
            <div key={f.id} style={{ marginLeft: '1rem', marginBottom: '0.75rem' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.4rem' }}>Floor {f.floor_number} — {f.label}</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginLeft: '1rem' }}>
                {f.sectors.map((s) => (
                  <div key={s.id} style={{ background: '#f1f5f9', borderRadius: '6px', padding: '0.4rem 0.75rem', fontSize: '0.85rem' }}>
                    <strong>{s.name}</strong> <span className="text-muted">({s.code})</span>
                    {s.description && <div className="text-muted text-sm">{s.description}</div>}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}
