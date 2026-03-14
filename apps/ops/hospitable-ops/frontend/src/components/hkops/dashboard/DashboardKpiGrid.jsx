import React from 'react'
import KpiCard from './KpiCard'
import {
  BedDouble, Loader2, ClipboardCheck, CheckCircle2, Ban,
  ListTodo, ShieldAlert, XCircle, AlertTriangle, Package
} from 'lucide-react'

export default function DashboardKpiGrid({ kpis, onKpiClick }) {
  const cards = [
    {
      key: 'vacant_dirty',
      label: 'Vacant Dirty',
      value: kpis.vacant_dirty,
      icon: <BedDouble size={20} />,
      variant: kpis.vacant_dirty > 5 ? 'warning' : 'neutral',
      subtitle: 'Needs cleaning',
    },
    {
      key: 'in_progress',
      label: 'In Progress',
      value: kpis.in_progress,
      icon: <Loader2 size={20} />,
      variant: 'active',
      subtitle: 'Being cleaned now',
    },
    {
      key: 'pending_inspection',
      label: 'Pending Inspection',
      value: kpis.pending_inspection,
      icon: <ClipboardCheck size={20} />,
      variant: kpis.pending_inspection > 3 ? 'warning' : 'neutral',
      subtitle: 'Awaiting QA check',
    },
    {
      key: 'inspected',
      label: 'Inspected',
      value: kpis.inspected,
      icon: <CheckCircle2 size={20} />,
      variant: 'success',
      subtitle: 'Clean & verified',
    },
    {
      key: 'out_of_order',
      label: 'Out of Order',
      value: kpis.out_of_order,
      icon: <Ban size={20} />,
      variant: kpis.out_of_order > 0 ? 'danger' : 'neutral',
      subtitle: 'Not available',
    },
    {
      key: 'open_tasks',
      label: 'Open Tasks',
      value: kpis.open_tasks,
      icon: <ListTodo size={20} />,
      variant: kpis.open_tasks > 8 ? 'warning' : 'neutral',
      subtitle: 'Open / assigned / in-progress',
    },
    {
      key: 'blocked_tasks',
      label: 'Blocked Tasks',
      value: kpis.blocked_tasks,
      icon: <ShieldAlert size={20} />,
      variant: kpis.blocked_tasks > 0 ? 'danger' : 'neutral',
      subtitle: 'Needs supervisor action',
    },
    {
      key: 'failed_inspections',
      label: 'Failed Inspections',
      value: kpis.failed_inspections,
      icon: <XCircle size={20} />,
      variant: kpis.failed_inspections > 0 ? 'danger' : 'neutral',
      subtitle: 'Requires follow-up',
    },
    {
      key: 'unresolved_issues',
      label: 'Open Issues',
      value: kpis.unresolved_issues,
      icon: <AlertTriangle size={20} />,
      variant: kpis.unresolved_issues > 3 ? 'warning' : 'neutral',
      subtitle: 'Unresolved room problems',
    },
    {
      key: 'supply_exceptions',
      label: 'Supply Exceptions',
      value: kpis.supply_exceptions,
      icon: <Package size={20} />,
      variant: kpis.supply_exceptions > 0 ? 'warning' : 'neutral',
      subtitle: 'Shortages affecting ops',
    },
  ]

  return (
    <div className="hk-kpi-grid">
      {cards.map(card => (
        <KpiCard
          key={card.key}
          label={card.label}
          value={card.value}
          icon={card.icon}
          variant={card.variant}
          subtitle={card.subtitle}
          onClick={onKpiClick ? () => onKpiClick(card.key) : undefined}
        />
      ))}
    </div>
  )
}
