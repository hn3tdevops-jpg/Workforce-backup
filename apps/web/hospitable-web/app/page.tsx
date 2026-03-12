"use client"
import { useEffect, useState } from 'react'
import { api, getLocationId, DashboardSummary, TaskRead, MaintenanceIssueRead } from '../lib/api'
import Link from 'next/link'

function StatCard({ label, value, variant }: { label: string; value: number; variant?: 'warn' | 'danger' | 'ok' }) {
  return (
    <div className="stat-card">
      <div className="stat-card-label">{label}</div>
      <div className={`stat-card-value${variant ? ` ${variant}` : ''}`}>{value}</div>
    </div>
  )
}

function Badge({ value }: { value: string }) {
  return <span className={`badge badge-${value}`}>{value.replace(/_/g, ' ')}</span>
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [tasks, setTasks] = useState<TaskRead[]>([])
  const [issues, setIssues] = useState<MaintenanceIssueRead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getLocationId()
      .then((locationId) =>
        Promise.all([
          api.getDashboardSummary(locationId),
          api.getHousekeepingBoard(locationId),
          api.getMaintenanceBoard(locationId),
        ])
      )
      .then(([s, t, i]) => { setSummary(s); setTasks(t.slice(0, 5)); setIssues(i.slice(0, 5)) })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Loading dashboard…</div>
  if (error) return <div className="alert alert-error">{error}</div>

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Hospitable Dashboard</h1>
        <p className="page-subtitle">Silver Sands Resort — operational overview</p>
      </div>
      {summary && (
        <div className="stat-grid">
          <StatCard label="Total Rooms" value={summary.total_rooms} />
          <StatCard label="Dirty" value={summary.dirty_rooms} variant={summary.dirty_rooms > 0 ? 'warn' : 'ok'} />
          <StatCard label="Assigned" value={summary.assigned_rooms} />
          <StatCard label="Cleaning" value={summary.cleaning_rooms} />
          <StatCard label="Clean" value={summary.clean_rooms} variant="ok" />
          <StatCard label="Inspect" value={summary.inspect_rooms} />
          <StatCard label="Inspected" value={summary.inspected_rooms} variant="ok" />
          <StatCard label="Blocked" value={summary.blocked_rooms} variant={summary.blocked_rooms > 0 ? 'danger' : undefined} />
          <StatCard label="Occupied" value={summary.occupied_rooms} />
          <StatCard label="Open Tasks" value={summary.open_tasks} variant={summary.open_tasks > 0 ? 'warn' : 'ok'} />
          <StatCard label="Open Issues" value={summary.open_issues} variant={summary.open_issues > 0 ? 'warn' : 'ok'} />
        </div>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold">Active Tasks</h2>
            <Link href="/housekeeping" className="btn btn-secondary btn-sm">View all</Link>
          </div>
          {tasks.length === 0 ? (
            <div className="empty-state"><div className="empty-state-icon">✅</div><div className="empty-state-text">No active tasks</div></div>
          ) : (
            <table className="data-table"><thead><tr><th>Room</th><th>Type</th><th>Priority</th><th>Status</th></tr></thead>
              <tbody>{tasks.map((t) => (<tr key={t.id}><td>{t.room_number ?? `#${t.room_id}`}</td><td className="text-sm">{t.task_type.replace(/_/g, ' ')}</td><td><Badge value={t.priority} /></td><td><Badge value={t.status} /></td></tr>))}</tbody>
            </table>
          )}
        </div>
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold">Open Maintenance</h2>
            <Link href="/maintenance" className="btn btn-secondary btn-sm">View all</Link>
          </div>
          {issues.length === 0 ? (
            <div className="empty-state"><div className="empty-state-icon">🔧</div><div className="empty-state-text">No open issues</div></div>
          ) : (
            <table className="data-table"><thead><tr><th>Room</th><th>Title</th><th>Severity</th><th>Status</th></tr></thead>
              <tbody>{issues.map((i) => (<tr key={i.id}><td>{i.room_number ?? `#${i.room_id}`}</td><td className="text-sm">{i.title}</td><td><Badge value={i.severity} /></td><td><Badge value={i.status} /></td></tr>))}</tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
