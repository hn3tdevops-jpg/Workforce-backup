"use client"
import { useEffect, useState, useCallback } from 'react'
import { api, getLocationId, TaskRead, TaskStatus, TaskType, TaskPriority } from '../../lib/api'

const TASK_TYPES: TaskType[] = ['clean_checkout','clean_stayover','inspection','restock','maintenance_followup']
const PRIORITIES: TaskPriority[] = ['low','normal','high','urgent']

function Badge({ value }: { value: string }) {
  return <span className={`badge badge-${value}`}>{value.replace(/_/g, ' ')}</span>
}

export default function HousekeepingPage() {
  const [locationId, setLocationId] = useState('')
  const [tasks, setTasks] = useState<TaskRead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [filterStatus, setFilterStatus] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ room_id: '', task_type: 'clean_checkout' as TaskType, title: '', priority: 'normal' as TaskPriority, description: '' })
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    getLocationId().then(setLocationId).catch((e) => setError(e.message))
  }, [])

  const load = useCallback(() => {
    if (!locationId) return
    setLoading(true)
    const params: Record<string, string> = {}
    if (filterStatus) params.status = filterStatus
    api.listTasks(locationId, params)
      .then(setTasks)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [locationId, filterStatus])

  useEffect(() => { load() }, [load])

  const updateStatus = async (taskId: number, status: TaskStatus) => {
    setError(null)
    try {
      await api.patchTaskStatus(taskId, status)
      setSuccess('Task updated')
      load()
    } catch (e: unknown) { setError(e instanceof Error ? e.message : String(e)) }
  }

  const createTask = async () => {
    if (!form.title || !locationId) return
    setCreating(true)
    setError(null)
    try {
      await api.createTask({
        location_id: locationId,
        room_id: form.room_id ? parseInt(form.room_id) : null,
        task_type: form.task_type,
        title: form.title,
        priority: form.priority,
        description: form.description || null,
      })
      setSuccess('Task created')
      setShowCreate(false)
      setForm({ room_id: '', task_type: 'clean_checkout', title: '', priority: 'normal', description: '' })
      load()
    } catch (e: unknown) { setError(e instanceof Error ? e.message : String(e)) }
    finally { setCreating(false) }
  }

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Housekeeping Board</h1>
            <p className="page-subtitle">Dispatch and track housekeeping tasks</p>
          </div>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>+ New Task</button>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="room-board-toolbar">
        <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">All statuses</option>
          {['open','assigned','in_progress','completed','cancelled'].map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {showCreate && (
        <div className="modal-backdrop" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-title">Create Housekeeping Task</div>
            <div className="form-group">
              <label className="form-label">Title *</label>
              <input className="form-input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Clean Room 101 checkout" />
            </div>
            <div className="form-group">
              <label className="form-label">Task Type</label>
              <select className="form-select" value={form.task_type} onChange={(e) => setForm({ ...form, task_type: e.target.value as TaskType })}>
                {TASK_TYPES.map((t) => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Priority</label>
              <select className="form-select" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value as TaskPriority })}>
                {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
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
              <button className="btn btn-primary" onClick={createTask} disabled={creating || !form.title}>{creating ? 'Creating…' : 'Create'}</button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading tasks…</div>
      ) : tasks.length === 0 ? (
        <div className="empty-state"><div className="empty-state-icon">🧹</div><div className="empty-state-text">No tasks found</div></div>
      ) : (
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr><th>ID</th><th>Room</th><th>Type</th><th>Title</th><th>Priority</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.id}>
                  <td className="text-muted text-sm">#{t.id}</td>
                  <td>{(t as unknown as { room_number?: string }).room_number ?? (t.room_id ? `#${t.room_id}` : '—')}</td>
                  <td className="text-sm">{t.task_type.replace(/_/g, ' ')}</td>
                  <td>{t.title}</td>
                  <td><Badge value={t.priority} /></td>
                  <td><Badge value={t.status} /></td>
                  <td>
                    <div className="flex gap-2">
                      {t.status === 'open' && <button className="btn btn-secondary btn-sm" onClick={() => updateStatus(t.id, 'in_progress')}>Start</button>}
                      {t.status === 'in_progress' && <button className="btn btn-primary btn-sm" onClick={() => updateStatus(t.id, 'completed')}>Complete</button>}
                      {(t.status === 'open' || t.status === 'assigned') && <button className="btn btn-secondary btn-sm" onClick={() => updateStatus(t.id, 'cancelled')}>Cancel</button>}
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
