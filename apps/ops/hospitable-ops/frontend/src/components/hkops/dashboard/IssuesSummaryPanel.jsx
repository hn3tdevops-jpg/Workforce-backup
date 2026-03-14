import React from 'react'
import { AlertTriangle, ChevronRight, Clock } from 'lucide-react'

const PRIORITY_CONFIG = {
  URGENT: { label: 'Urgent', cls: 'hk-badge--danger',  order: 0 },
  HIGH:   { label: 'High',   cls: 'hk-badge--warning', order: 1 },
  NORMAL: { label: 'Normal', cls: 'hk-badge--neutral', order: 2 },
  LOW:    { label: 'Low',    cls: 'hk-badge--neutral', order: 3 },
}

const TYPE_LABELS = {
  MISSING_ITEM:       'Missing Item',
  DAMAGED_ITEM:       'Damaged Item',
  MAINTENANCE_FLAG:   'Maintenance',
  CLEANLINESS_DEFECT: 'Cleanliness',
  SAFETY_FLAG:        'Safety',
  INVENTORY_SHORTAGE: 'Inventory',
  LINEN_SHORTAGE:     'Linen',
}

function IssueRow({ issue, onAction }) {
  const pri = PRIORITY_CONFIG[issue.priority] || PRIORITY_CONFIG.NORMAL
  const isUrgent = issue.priority === 'URGENT'

  return (
    <div className={`hk-issue-row ${isUrgent ? 'hk-issue-row--urgent' : ''}`}>
      <div className="hk-issue-row__left">
        <span className={`hk-badge ${pri.cls}`}>{pri.label}</span>
        <span className="hk-issue-type">{TYPE_LABELS[issue.issue_type] || issue.issue_type}</span>
      </div>
      <div className="hk-issue-row__center">
        <span className="hk-issue-room">Rm {issue.room_number}</span>
        <span className="hk-issue-sector">{issue.sector_code}</span>
        <span className="hk-issue-asset">{issue.asset_name}</span>
      </div>
      <div className="hk-issue-row__right">
        {issue.age_minutes > 0 && (
          <span className={`hk-age-chip ${issue.age_minutes > 120 ? 'hk-age-chip--warn' : ''}`}>
            <Clock size={11} /> {issue.age_minutes < 60 ? `${issue.age_minutes}m` : `${Math.floor(issue.age_minutes / 60)}h`}
          </span>
        )}
        <button className="hk-btn hk-btn--xs hk-btn--ghost" onClick={() => onAction && onAction('view', issue)}>
          Review <ChevronRight size={11} />
        </button>
      </div>
    </div>
  )
}

export default function IssuesSummaryPanel({ issues, onNavigate }) {
  const open = issues
    .filter(i => !i.resolved_flag)
    .sort((a, b) => {
      const pa = PRIORITY_CONFIG[a.priority]?.order ?? 9
      const pb = PRIORITY_CONFIG[b.priority]?.order ?? 9
      return pa - pb
    })

  const resolved = issues.filter(i => i.resolved_flag)
  const urgentCount = open.filter(i => i.priority === 'URGENT').length

  return (
    <div className="hk-panel">
      <div className="hk-panel__header">
        <AlertTriangle size={18} className="hk-icon-warning" />
        <h3 className="hk-panel__title">Issues Summary</h3>
        <div style={{ display: 'flex', gap: '0.4rem', marginLeft: 'auto' }}>
          {urgentCount > 0 && <span className="hk-badge hk-badge--danger">{urgentCount} urgent</span>}
          <span className="hk-badge hk-badge--neutral">{open.length} open</span>
        </div>
      </div>

      <div className="hk-panel__body">
        {open.length === 0 ? (
          <p className="hk-empty-state">No open issues at this time.</p>
        ) : (
          <div className="hk-issue-list">
            {open.slice(0, 8).map(issue => (
              <IssueRow
                key={issue.issue_id}
                issue={issue}
                onAction={(action, item) => onNavigate && onNavigate('issues', { action, item })}
              />
            ))}
            {open.length > 8 && (
              <p className="hk-list-overflow">+{open.length - 8} more open issues</p>
            )}
          </div>
        )}

        {resolved.length > 0 && (
          <div className="hk-resolved-note">
            {resolved.length} issue{resolved.length > 1 ? 's' : ''} resolved today
          </div>
        )}

        <div className="hk-panel__footer">
          <button className="hk-btn hk-btn--ghost hk-btn--sm" onClick={() => onNavigate && onNavigate('issues')}>
            View all issues <ChevronRight size={13} />
          </button>
        </div>
      </div>
    </div>
  )
}
