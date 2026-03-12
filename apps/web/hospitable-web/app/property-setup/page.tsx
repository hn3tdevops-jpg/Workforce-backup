"use client"
import { useEffect, useState } from 'react'
import { api, getLocationId } from '../../lib/api'

interface Sector {
  id: number
  name: string
  code?: string
  description?: string
}

interface Floor {
  id: number
  floor_number?: number
  name?: string
  label?: string
  sectors: Sector[]
  room_count?: number
}

interface Building {
  id: number
  name: string
  code?: string
  floors: Floor[]
}

interface PropertyTree {
  id: string
  name: string
  buildings: Building[]
}

export default function PropertySetupPage() {
  const [tree, setTree] = useState<PropertyTree | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getLocationId()
      .then((locationId) => api.getPropertyTree(locationId))
      .then((data) => setTree(data as unknown as PropertyTree))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Property Setup</h1>
        <p className="page-subtitle">Buildings, floors, and sectors for Silver Sands Resort</p>
      </div>
      {error && <div className="alert alert-error">{error}</div>}
      {loading ? (
        <div className="loading">Loading property structure…</div>
      ) : !tree || tree.buildings.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🏗️</div>
          <div className="empty-state-text">No property structure found.</div>
        </div>
      ) : tree.buildings.map((b) => (
        <div key={b.id} className="card">
          <h2 className="font-bold mb-2">🏢 {b.name} {b.code && <span className="text-muted text-sm">({b.code})</span>}</h2>
          {b.floors.map((f) => (
            <div key={f.id} style={{ marginLeft: '1rem', marginBottom: '0.75rem' }}>
              <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.4rem' }}>
                Floor {f.floor_number ?? ''} — {f.name ?? f.label ?? ''}
                {f.room_count != null && <span className="text-muted text-sm"> ({f.room_count} rooms)</span>}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginLeft: '1rem' }}>
                {f.sectors.map((s) => (
                  <div key={s.id} style={{ background: '#f1f5f9', borderRadius: '6px', padding: '0.4rem 0.75rem', fontSize: '0.85rem' }}>
                    <strong>{s.name}</strong> {s.code && <span className="text-muted">({s.code})</span>}
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
