import React from 'react'
import {
  LayoutGrid, ListTodo, ClipboardCheck, AlertTriangle,
  Package, Upload, Plus, Zap
} from 'lucide-react'

export default function QuickActionsPanel({ onNavigate, kpis }) {
  const actions = [
    {
      key: 'room-board',
      label: 'Open Room Board',
      icon: <LayoutGrid size={20} />,
      description: 'Full room status grid',
      variant: 'primary',
      badge: null,
    },
    {
      key: 'tasks',
      label: 'Task Queue',
      icon: <ListTodo size={20} />,
      description: 'Manage work assignments',
      variant: 'default',
      badge: kpis.open_tasks > 0 ? kpis.open_tasks : null,
      badgeCls: 'hk-badge--neutral',
    },
    {
      key: 'create-task',
      label: 'Create Task',
      icon: <Plus size={20} />,
      description: 'Add a new housekeeping task',
      variant: 'default',
      badge: null,
    },
    {
      key: 'inspections',
      label: 'Review Inspections',
      icon: <ClipboardCheck size={20} />,
      description: 'QA queue and history',
      variant: kpis.pending_inspection > 0 ? 'warning' : 'default',
      badge: kpis.pending_inspection > 0 ? kpis.pending_inspection : null,
      badgeCls: 'hk-badge--warning',
    },
    {
      key: 'issues',
      label: 'Review Issues',
      icon: <AlertTriangle size={20} />,
      description: 'Open room problems',
      variant: kpis.unresolved_issues > 0 ? 'danger' : 'default',
      badge: kpis.unresolved_issues > 0 ? kpis.unresolved_issues : null,
      badgeCls: 'hk-badge--danger',
    },
    {
      key: 'supply',
      label: 'Supply Exceptions',
      icon: <Package size={20} />,
      description: 'Shortages and inventory',
      variant: kpis.supply_exceptions > 0 ? 'warning' : 'default',
      badge: kpis.supply_exceptions > 0 ? kpis.supply_exceptions : null,
      badgeCls: 'hk-badge--warning',
    },
    {
      key: 'export',
      label: 'Import / Export',
      icon: <Upload size={20} />,
      description: 'Data import and export',
      variant: 'default',
      badge: null,
    },
  ]

  return (
    <div className="hk-panel hk-panel--quick-actions">
      <div className="hk-panel__header">
        <Zap size={18} className="hk-icon-accent" />
        <h3 className="hk-panel__title">Quick Actions</h3>
      </div>

      <div className="hk-panel__body">
        <div className="hk-quick-actions-grid">
          {actions.map(action => (
            <button
              key={action.key}
              className={`hk-quick-action hk-quick-action--${action.variant}`}
              onClick={() => onNavigate && onNavigate(action.key)}
              type="button"
            >
              <span className="hk-quick-action__icon">{action.icon}</span>
              <div className="hk-quick-action__body">
                <span className="hk-quick-action__label">
                  {action.label}
                  {action.badge != null && (
                    <span className={`hk-badge ${action.badgeCls || 'hk-badge--neutral'}`} style={{ marginLeft: 6 }}>
                      {action.badge}
                    </span>
                  )}
                </span>
                <span className="hk-quick-action__desc">{action.description}</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
