"use client"
import { useEffect, useState, useCallback } from 'react'
import { api, getLocationId, MaintenanceIssueRead, MaintenanceIssueStatus } from '../../lib/api'

const SEVERITIES = ['low','normal','high','critical']
const ISSUE_TYPES = ['plumbing','electrical','hvac','furniture','appliance','structural','pest','other']

function Badge({ value }: { value: string }) {
  return <span className={`badge badge-${value}`}>{value.replace(/_/g, ' ')}</span>
}

export default function MaintenancePage() {
  const [locationId, setLocationId] = useState('')
  const [issues, setIssues] = useState<MaintenanceIssueRead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [filterStatus, setFilterStatus] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ room_id: '', issue_type: 'plumbing', title: '', severity: 'normal', description: '' })
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    getLocationId().then(setLocationId).catch((e) => setError(e.message))
  }, [])

  const load = useCallback(() => {
    if (!locationId) return
    setLoading(true)
    const params: Record<string, string> = {}
    if (filterStatus) params.status = filterStatus
    api.listMaintenanceIssues(locationId, params)
      .then(setIssues)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [locationId, filterStatus])

  useEffect(() => { load() }, [load])

  const updateStatus = async (issueId: number, status: MaintenanceIssueStatus) => {
    setError(null)
    try {
      await api.patchMaintenanceIssue(issueId, { status })
      setSuccess('Issue updated')
      load()
    } catch (e: unknown) { setError(e instanceof Error ? e.message : String(e)) }
  }

  const createIssue = async () => {
    if (!form.title || !locationId) return
    setCreating(true)
    setError(null)
    try {
      await api.createMaintenanceIssue({
        location_id: locationId,
        room_id: form.room_id ? parseInt(form.room_id) : null,
        issue_type: form.issue_type,
        title: form.title,
        severity: form.severity,
        description: form.description || null,
      })
      setSuccess('Issue created')
      setShowCreate(false)
      setForm({ room_id: '', issue_type: 'plumbing', title: '', severity: 'normal', description: '' })
      load()
    } catch (e: unknown) { setError(e instanceof Error ? e.message : String(e)) }
    finally { setCreating(false) }
  }

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Maintenance Board</h1>
            <p className="page-subtitle">Track and resolve property maintenance issues</p>
          </div>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>+ Report Issue</button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="room-board-toolbar">
        <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">All statuses</option>
          {['open','triaged','in_progress','resolved','closed'].map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {showCreate && (
        <div className="modal-backdrop" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-title">Report Maintenance Issue</div>
            <div className="form-group">
              <label className="form-label">Title *</label>
              <input className="form-input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Leaking faucet in Room 103" />
            </div>
            <div className="form-group">
              <label className="form-label">Issue Type</label>
              <select className="form-select" value={form.issue_type} onChange={(e) => setForm({ ...form, issue_type: e.target.value })}>
                {ISSUE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Severity</label>
              <select className="form-select" value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })}>
                {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Room ID (optional)</label>
              <input className="form-input" type="number" value={form.room_id} onChange={(e) => setForm({ ...form, room_id: e.target.value })} placeholder="Room ID number" />
            </div>
            <div className="form-group">
              <label className="form-label">Description</label>
              <textarea className="form-textarea" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={createIssue} disabled={creating || !form.title}>{creating ? 'Creating…' : 'Report'}</button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading issues…</div>
      ) : issues.length === 0 ? (
        <div className="empty-state"><div className="empty-state-icon">🔧</div><div className="empty-state-text">No maintenance issues found</div></div>
      ) : (
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr><th>ID</th><th>Room</th><th>Type</th><th>Title</th><th>Severity</th><th>Status</th><th>Reported</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {issues.map((i) => (
                <tr key={i.id}>
                  <td className="text-muted text-sm">#{i.id}</td>
                  <td>{(i as unknown as { room_number?: string }).room_number ?? (i.room_id ? `#${i.room_id}` : '—')}</td>
                  <td className="text-sm">{i.issue_type}</td>
                  <td>{i.title}</td>
                  <td><Badge value={i.severity} /></td>
                  <td><Badge value={i.status} /></td>
                  <td className="text-sm text-muted">{new Date(i.reported_at).toLocaleDateString()}</td>
                  <td>
                    <div className="flex gap-2">
                      {i.status === 'open' && <button className="btn btn-secondary btn-sm" onClick={() => updateStatus(i.id, 'in_progress')}>Start</button>}
                      {i.status === 'in_progress' && <button className="btn btn-primary btn-sm" onClick={() => updateStatus(i.id, 'resolved')}>Resolve</button>}
                      {i.status === 'resolved' && <button className="btn btn-secondary btn-sm" onClick={() => updateStatus(i.id, 'closed')}>Close</button>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
