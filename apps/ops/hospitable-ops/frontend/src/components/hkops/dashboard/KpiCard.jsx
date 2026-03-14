import React from 'react'

export default function KpiCard({ label, value, icon, variant, onClick, subtitle }) {
  const variantClass = variant ? `hk-kpi-card--${variant}` : ''

  return (
    <button
      className={`hk-kpi-card ${variantClass} ${onClick ? 'hk-kpi-card--clickable' : ''}`}
      onClick={onClick}
      type="button"
      title={onClick ? `Click to filter by: ${label}` : undefined}
    >
      {icon && <span className="hk-kpi-card__icon">{icon}</span>}
      <div className="hk-kpi-card__body">
        <span className="hk-kpi-card__value">{value}</span>
        <span className="hk-kpi-card__label">{label}</span>
        {subtitle && <span className="hk-kpi-card__subtitle">{subtitle}</span>}
      </div>
    </button>
  )
}
