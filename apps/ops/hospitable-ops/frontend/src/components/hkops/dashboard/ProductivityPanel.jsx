import React from 'react'
import { TrendingUp, Clock } from 'lucide-react'

export default function ProductivityPanel({ tasks, staffing }) {
  const completed = tasks.filter(t => ['COMPLETED', 'VERIFIED'].includes(t.task_status))
  const inProgress = tasks.filter(t => t.task_status === 'IN_PROGRESS')
  const totalTasks = tasks.length

  // Avg actual minutes for completed tasks with actual_minutes
  const withActual = completed.filter(t => t.actual_minutes != null)
  const avgActual = withActual.length > 0
    ? Math.round(withActual.reduce((s, t) => s + t.actual_minutes, 0) / withActual.length)
    : null

  // Avg estimated minutes
  const withEst = tasks.filter(t => t.estimated_minutes != null)
  const avgEst = withEst.length > 0
    ? Math.round(withEst.reduce((s, t) => s + t.estimated_minutes, 0) / withEst.length)
    : null

  // Completion rate
  const completionRate = totalTasks > 0 ? Math.round((completed.length / totalTasks) * 100) : 0

  // Tasks per active staff
  const activeStaff = staffing.filter(s => s.status === 'active' && s.role !== 'Supervisor').length
  const tasksPerStaff = activeStaff > 0 ? (tasks.filter(t => t.assigned_staff_id).length / activeStaff).toFixed(1) : '—'

  // Unassigned count
  const unassigned = tasks.filter(t => !t.assigned_staff_id && ['OPEN'].includes(t.task_status)).length

  const metrics = [
    { label: 'Tasks Completed',    value: completed.length,    sub: `of ${totalTasks} total` },
    { label: 'Completion Rate',    value: `${completionRate}%`, sub: 'tasks done today' },
    { label: 'Avg Est. Minutes',   value: avgEst != null ? `${avgEst}m` : '—', sub: 'per task' },
    { label: 'Avg Actual Minutes', value: avgActual != null ? `${avgActual}m` : '—', sub: 'completed tasks' },
    { label: 'Tasks / Attendant',  value: tasksPerStaff, sub: `${activeStaff} active staff` },
    { label: 'Unassigned Tasks',   value: unassigned, sub: 'need assignment', highlight: unassigned > 0 },
  ]

  return (
    <div className="hk-panel">
      <div className="hk-panel__header">
        <TrendingUp size={18} className="hk-icon-accent" />
        <h3 className="hk-panel__title">Productivity Snapshot</h3>
        <span className="hk-panel__meta">Today</span>
      </div>

      <div className="hk-panel__body">
        <div className="hk-productivity-grid">
          {metrics.map((m, idx) => (
            <div key={idx} className={`hk-productivity-metric ${m.highlight ? 'hk-productivity-metric--warn' : ''}`}>
              <span className="hk-productivity-metric__value">{m.value}</span>
              <span className="hk-productivity-metric__label">{m.label}</span>
              <span className="hk-productivity-metric__sub">{m.sub}</span>
            </div>
          ))}
        </div>

        {/* In-progress tasks */}
        {inProgress.length > 0 && (
          <div className="hk-inprog-section">
            <div className="hk-inprog-section__title">
              <Clock size={13} /> Currently In Progress
            </div>
            <div className="hk-inprog-list">
              {inProgress.map(t => (
                <div key={t.task_id} className="hk-inprog-row">
                  <span className="hk-inprog-room">Rm {t.room_number}</span>
                  <span className="hk-inprog-type">{t.task_type.replace(/_/g, ' ')}</span>
                  <span className="hk-inprog-staff">{t.assigned_staff_name || '—'}</span>
                  <span className="hk-inprog-est">{t.estimated_minutes}m est.</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
