import React from 'react'
import { ShieldAlert, AlertTriangle, ChevronRight, Clock } from 'lucide-react'

function AttentionItem({ icon, label, room, sector, detail, age, variant, onAction, actionLabel }) {
  return (
    <div className={`hk-attention-item hk-attention-item--${variant}`}>
      <span className="hk-attention-item__icon">{icon}</span>
      <div className="hk-attention-item__body">
        <div className="hk-attention-item__header">
          <span className="hk-attention-item__label">{label}</span>
          <span className="hk-attention-item__room">Room {room}</span>
          {sector && <span className="hk-attention-item__sector">{sector}</span>}
        </div>
        <p className="hk-attention-item__detail">{detail}</p>
        {age !== undefined && age !== null && (
          <span className="hk-attention-item__age">
            <Clock size={11} /> {age < 60 ? `${age}m ago` : `${Math.floor(age / 60)}h ${age % 60}m ago`}
          </span>
        )}
      </div>
      {onAction && (
        <button className="hk-btn hk-btn--xs hk-btn--ghost" onClick={onAction}>
          {actionLabel || 'Review'} <ChevronRight size={12} />
        </button>
      )}
    </div>
  )
}

export default function SupervisorAttentionPanel({ tasks, issues, onNavigate }) {
  const blockedTasks = tasks.filter(t => t.task_status === 'BLOCKED')
  const urgentIssues = issues.filter(i => !i.resolved_flag && i.priority === 'URGENT')
  const total = blockedTasks.length + urgentIssues.length

  return (
    <div className="hk-panel">
      <div className="hk-panel__header">
        <ShieldAlert size={18} className="hk-icon-danger" />
        <h3 className="hk-panel__title">Supervisor Attention Queue</h3>
        {total > 0 && <span className="hk-badge hk-badge--danger">{total}</span>}
      </div>

      <div className="hk-panel__body">
        {total === 0 ? (
          <p className="hk-empty-state">No items requiring immediate supervisor attention.</p>
        ) : (
          <div className="hk-attention-list">
            {blockedTasks.map(task => (
              <AttentionItem
                key={task.task_id}
                icon={<ShieldAlert size={16} />}
                label="Blocked Task"
                room={task.room_number}
                sector={task.sector_code}
                detail={task.blocked_reason || 'Task is blocked'}
                age={null}
                variant="danger"
                onAction={() => onNavigate && onNavigate('tasks', { taskId: task.task_id })}
                actionLabel="Unblock"
              />
            ))}
            {urgentIssues.map(issue => (
              <AttentionItem
                key={issue.issue_id}
                icon={<AlertTriangle size={16} />}
                label={issue.issue_type.replace(/_/g, ' ')}
                room={issue.room_number}
                sector={issue.sector_code}
                detail={issue.issue_description}
                age={issue.age_minutes}
                variant="urgent"
                onAction={() => onNavigate && onNavigate('issues', { issueId: issue.issue_id })}
                actionLabel="Resolve"
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
