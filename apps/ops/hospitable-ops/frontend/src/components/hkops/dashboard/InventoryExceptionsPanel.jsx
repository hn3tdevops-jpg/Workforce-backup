import React from 'react'
import { Package, ChevronRight, AlertCircle } from 'lucide-react'

const SUPPLY_TYPES = ['INVENTORY_SHORTAGE', 'LINEN_SHORTAGE']

const TYPE_LABELS = {
  INVENTORY_SHORTAGE: 'Inventory',
  LINEN_SHORTAGE:     'Linen',
}

const TYPE_COLOR = {
  INVENTORY_SHORTAGE: '#f59e0b',
  LINEN_SHORTAGE:     '#8b5cf6',
}

export default function InventoryExceptionsPanel({ issues, onNavigate }) {
  const supplyIssues = issues.filter(i => SUPPLY_TYPES.includes(i.issue_type) && !i.resolved_flag)

  return (
    <div className="hk-panel">
      <div className="hk-panel__header">
        <Package size={18} className="hk-icon-warning" />
        <h3 className="hk-panel__title">Inventory Exceptions</h3>
        {supplyIssues.length > 0 && (
          <span className="hk-badge hk-badge--warning">{supplyIssues.length} active</span>
        )}
      </div>

      <div className="hk-panel__body">
        {supplyIssues.length === 0 ? (
          <p className="hk-empty-state">No supply exceptions — inventory levels are adequate.</p>
        ) : (
          <div className="hk-supply-list">
            {supplyIssues.map(issue => (
              <div key={issue.issue_id} className="hk-supply-row">
                <span
                  className="hk-supply-type-dot"
                  style={{ backgroundColor: TYPE_COLOR[issue.issue_type] || '#9ca3af' }}
                />
                <div className="hk-supply-row__body">
                  <div className="hk-supply-row__header">
                    <span className="hk-supply-type">{TYPE_LABELS[issue.issue_type] || issue.issue_type}</span>
                    <span className="hk-supply-item">{issue.asset_name}</span>
                    <span className="hk-supply-qty">×{issue.quantity_affected}</span>
                  </div>
                  <p className="hk-supply-desc">{issue.issue_description}</p>
                  <div className="hk-supply-meta">
                    <span>Room {issue.room_number}</span>
                    <span>{issue.sector_code}</span>
                    <span>Reported by {issue.reported_by_staff_name}</span>
                  </div>
                </div>
                <div className="hk-supply-row__actions">
                  {issue.linked_task_id && (
                    <span className="hk-badge hk-badge--neutral" style={{ fontSize: '0.68rem' }}>
                      <AlertCircle size={10} /> Blocking task
                    </span>
                  )}
                  <button
                    className="hk-btn hk-btn--xs hk-btn--ghost"
                    onClick={() => onNavigate && onNavigate('issues', { issueId: issue.issue_id })}
                  >
                    Resolve <ChevronRight size={11} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="hk-panel__footer">
          <button className="hk-btn hk-btn--ghost hk-btn--sm" onClick={() => onNavigate && onNavigate('issues', { filter: 'supply' })}>
            View supply exceptions <ChevronRight size={13} />
          </button>
        </div>
      </div>
    </div>
  )
}
