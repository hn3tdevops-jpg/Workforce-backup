"use client"

import { useEffect, useState, useCallback } from 'react'
import { api, getLocationId, TaskRead, HousekeepingStatus, InspectionStatus } from '../../lib/api'

function Badge({ value }: { value: string }) {
  return <span className={`badge badge-${value}`}>{value.replace(/_/g, ' ')}</span>
}

export default function InspectionsPage() {
  const [locationId, setLocationId] = useState('')
  const [tasks, setTasks] = useState<TaskRead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [updatingId, setUpdatingId] = useState<number | null>(null)

  useEffect(() => {
    getLocationId().then(setLocationId).catch((e) => setError(e.message))
  }, [])

  const load = useCallback(() => {
    if (!locationId) return
    setLoading(true)
    api.listTasks(locationId, { status: 'done' })
      .then((data) => setTasks(data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [locationId])

  useEffect(() => { load() }, [load])

  const handleInspect = async (taskId: number, roomId: number | null, result: 'pass' | 'fail') => {
    setUpdatingId(taskId)
    setError(null)
    setSuccess(null)
    try {
      if (result === 'pass') {
        if (roomId) {
          await api.patchRoomStatus(roomId, { 
            housekeeping_status: 'inspected' as HousekeepingStatus,
            inspection_status: 'passed' as InspectionStatus 
          })
        }
        setSuccess('Inspection passed. Room marked as inspected.')
      } else {
        await api.patchTaskStatus(taskId, 'open' as any, 'Inspection failed')
        if (roomId) {
          await api.patchRoomStatus(roomId, { 
            housekeeping_status: 'dirty' as HousekeepingStatus,
            inspection_status: 'failed' as InspectionStatus 
          })
        }
        setSuccess('Inspection failed. Task reopened and room marked as dirty.')
      }
      load()
    } catch (e: any) {
      setError(e.message)
    } finally {
      setUpdatingId(null)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Inspections</h1>
        <p className="page-subtitle">Verify completed housekeeping tasks</p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {loading ? (
        <div className="loading">Loading tasks for inspection...</div>
      ) : tasks.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">✅</div>
          <div className="empty-state-text">No tasks awaiting inspection.</div>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Room</th>
                <th>Task Title</th>
                <th>Priority</th>
                <th>Completed At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.id}>
                  <td>{(t as any).room_number ?? (t.room_id ? `#${t.room_id}` : '—')}</td>
                  <td>{t.title}</td>
                  <td><Badge value={t.priority} /></td>
                  <td className="text-sm text-muted">
                    {t.completed_at ? new Date(t.completed_at).toLocaleString() : '—'}
                  </td>
                  <td>
                    <div className="flex gap-2">
                      <button 
                        className="btn btn-primary btn-sm" 
                        onClick={() => handleInspect(t.id, t.room_id, 'pass')}
                        disabled={updatingId === t.id}
                      >
                        {updatingId === t.id ? '...' : 'Pass'}
                      </button>
                      <button 
                        className="btn btn-danger btn-sm" 
                        onClick={() => handleInspect(t.id, t.room_id, 'fail')}
                        disabled={updatingId === t.id}
                      >
                        {updatingId === t.id ? '...' : 'Fail'}
                      </button>
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
