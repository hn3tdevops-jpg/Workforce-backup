import React from 'react'
import { Users, ShieldAlert } from 'lucide-react'

const ROLE_COLOR = {
  Attendant:  '#3b82f6',
  Houseman:   '#8b5cf6',
  Supervisor: '#10b981',
}

const STATUS_LABEL = {
  active:  { label: 'Active',  cls: 'hk-badge--success' },
  blocked: { label: 'Blocked', cls: 'hk-badge--danger' },
  idle:    { label: 'Idle',    cls: 'hk-badge--neutral' },
}

export default function StaffingOverviewPanel({ staffing, tasks }) {
  // Enrich staffing with live task counts from tasks array
  const enriched = staffing.map(s => {
    const myTasks = tasks.filter(t => t.assigned_staff_id === s.staff_id)
    const blocked = myTasks.filter(t => t.task_status === 'BLOCKED').length
    const inProg  = myTasks.filter(t => t.task_status === 'IN_PROGRESS').length
    const open    = myTasks.filter(t => ['OPEN','ASSIGNED'].includes(t.task_status)).length
    const done    = myTasks.filter(t => ['COMPLETED','VERIFIED'].includes(t.task_status)).length
    return { ...s, myTasks: myTasks.length, blocked, inProg, open, done }
  })

  const activeCount  = enriched.filter(s => s.status === 'active').length
  const blockedCount = enriched.filter(s => s.status === 'blocked').length

  return (
    <div className="hk-panel">
      <div className="hk-panel__header">
        <Users size={18} className="hk-icon-accent" />
        <h3 className="hk-panel__title">Staffing Overview</h3>
        <span className="hk-panel__meta">{activeCount} active · {blockedCount} blocked</span>
      </div>

      <div className="hk-panel__body">
        <div className="hk-staff-table">
          <div className="hk-staff-table__head">
            <span>Staff</span>
            <span>Role</span>
            <span>In Prog</span>
            <span>Open</span>
            <span>Done</span>
            <span>Status</span>
          </div>
          {enriched.map(s => {
            const statusCfg = STATUS_LABEL[s.status] || STATUS_LABEL.idle
            return (
              <div key={s.staff_id} className="hk-staff-table__row">
                <span className="hk-staff-name">
                  <span
                    className="hk-staff-avatar"
                    style={{ backgroundColor: ROLE_COLOR[s.role] || '#6b7280' }}
                  >
                    {s.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                  </span>
                  {s.name}
                </span>
                <span className="hk-staff-role">{s.role}</span>
                <span className="hk-staff-stat hk-staff-stat--inprog">{s.inProg}</span>
                <span className="hk-staff-stat">{s.open}</span>
                <span className="hk-staff-stat hk-staff-stat--done">{s.done}</span>
                <span>
                  <span className={`hk-badge ${statusCfg.cls}`}>
                    {s.status === 'blocked' && <ShieldAlert size={10} style={{ marginRight: 3 }} />}
                    {statusCfg.label}
                  </span>
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
