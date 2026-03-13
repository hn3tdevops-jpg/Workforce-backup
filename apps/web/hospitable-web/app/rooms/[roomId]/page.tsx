"use client"

import { useEffect, useState, use } from 'react'
import { api, RoomRead, TaskRead, MaintenanceIssueRead } from '../../../lib/api'
import Link from 'next/link'

function Badge({ value }: { value: string }) {
  return <span className={`badge badge-${value}`}>{value.replace(/_/g, ' ')}</span>
}

export default function RoomDetailPage({ params }: { params: Promise<{ roomId: string }> }) {
  const { roomId } = use(params)
  const [room, setRoom] = useState<RoomRead | null>(null)
  const [tasks, setTasks] = useState<TaskRead[]>([])
  const [issues, setIssues] = useState<MaintenanceIssueRead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const id = parseInt(roomId)
    if (isNaN(id)) {
      setError('Invalid room ID')
      setLoading(false)
      return
    }

    api.getRoom(id)
      .then((roomData) => {
        setRoom(roomData)
        return Promise.all([
          api.listTasks(roomData.location_id, { room_id: roomId }),
          api.listMaintenanceIssues(roomData.location_id, { room_id: roomId })
        ])
      })
      .then(([taskData, issueData]) => {
        setTasks(taskData)
        setIssues(issueData)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [roomId])

  if (loading) return <div className="loading">Loading room details...</div>
  if (error) return <div className="alert alert-error">{error}</div>
  if (!room) return <div className="alert">Room not found</div>

  return (
    <div className="room-detail">
      <div className="page-header">
        <div className="flex items-center gap-4">
          <Link href="/rooms" className="btn btn-secondary btn-sm">← Back</Link>
          <h1 className="page-title">Room {room.room_number}</h1>
        </div>
        <p className="page-subtitle">{room.room_type || 'Standard Room'} — {room.room_label || ''}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <h2 className="font-bold mb-4">Status</h2>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-muted block mb-1">Housekeeping</label>
              <Badge value={room.housekeeping_status} />
            </div>
            <div>
              <label className="text-sm text-muted block mb-1">Occupancy</label>
              <Badge value={room.occupancy_status} />
            </div>
            <div>
              <label className="text-sm text-muted block mb-1">Inspection</label>
              <Badge value={room.inspection_status} />
            </div>
            <div>
              <label className="text-sm text-muted block mb-1">Maintenance</label>
              <Badge value={room.maintenance_status} />
            </div>
            {room.last_cleaned_at && (
              <div className="text-xs text-muted">
                Last cleaned: {new Date(room.last_cleaned_at).toLocaleString()}
              </div>
            )}
          </div>
        </div>

        <div className="card md:col-span-2">
          <h2 className="font-bold mb-4">Room Details</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-muted block">Beds</label>
              <div className="font-medium">{room.bed_count || 0} {room.bed_type_summary || ''}</div>
            </div>
            <div>
              <label className="text-sm text-muted block">Floor Surface</label>
              <div className="font-medium">{room.floor_surface}</div>
            </div>
            <div className="col-span-2">
              <label className="text-sm text-muted block">Notes</label>
              <div className="p-2 bg-slate-50 rounded text-sm min-h-[60px]">
                {room.notes || <span className="text-muted italic">No notes available</span>}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-bold mb-4">Recent Tasks</h2>
          {tasks.length === 0 ? (
            <div className="text-center py-8 text-muted italic">No tasks for this room</div>
          ) : (
            <div className="space-y-3">
              {tasks.map(t => (
                <div key={t.id} className="flex items-center justify-between p-2 border-b last:border-0">
                  <div>
                    <div className="font-medium">{t.title}</div>
                    <div className="text-xs text-muted">{t.task_type.replace(/_/g, ' ')}</div>
                  </div>
                  <Badge value={t.status} />
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="font-bold mb-4">Maintenance Issues</h2>
          {issues.length === 0 ? (
            <div className="text-center py-8 text-muted italic">No issues for this room</div>
          ) : (
            <div className="space-y-3">
              {issues.map(i => (
                <div key={i.id} className="flex items-center justify-between p-2 border-b last:border-0">
                  <div>
                    <div className="font-medium">{i.title}</div>
                    <div className="text-xs text-muted">{i.issue_type} — {new Date(i.reported_at).toLocaleDateString()}</div>
                  </div>
                  <Badge value={i.status} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-bold mb-4">Room Assets</h2>
          {!room.assets || room.assets.length === 0 ? (
            <div className="text-center py-8 text-muted italic">No assets listed</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="pb-2">Asset</th>
                  <th className="pb-2">Qty</th>
                  <th className="pb-2">Condition</th>
                </tr>
              </thead>
              <tbody>
                {room.assets.map(a => (
                  <tr key={a.id} className="border-b last:border-0">
                    <td className="py-2">{a.asset_name} <span className="text-xs text-muted">({a.asset_type})</span></td>
                    <td className="py-2">{a.quantity_present} / {a.quantity_expected}</td>
                    <td className="py-2">{a.condition_status || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="card">
          <h2 className="font-bold mb-4">Supply Par Levels</h2>
          {!room.supply_pars || room.supply_pars.length === 0 ? (
            <div className="text-center py-8 text-muted italic">No supply pars listed</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="pb-2">Item</th>
                  <th className="pb-2">Expected</th>
                  <th className="pb-2">Min</th>
                </tr>
              </thead>
              <tbody>
                {room.supply_pars.map(p => (
                  <tr key={p.id} className="border-b last:border-0">
                    <td className="py-2">{p.item_name} <span className="text-xs text-muted">({p.item_code})</span></td>
                    <td className="py-2">{p.expected_qty} {p.unit}</td>
                    <td className="py-2">{p.min_qty} {p.unit}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
