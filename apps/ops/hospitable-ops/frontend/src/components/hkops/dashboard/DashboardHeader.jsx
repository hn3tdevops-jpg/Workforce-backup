import React from 'react'
import { RefreshCw, Download, Calendar, Building2 } from 'lucide-react'
import { PROPERTIES } from '../../../mock/hkopsMockData'

export default function DashboardHeader({ selectedPropertyId, onPropertyChange, businessDate, onDateChange, onRefresh, lastRefreshed }) {
  return (
    <div className="hk-dashboard-header">
      <div className="hk-dashboard-header__left">
        <div className="hk-dashboard-header__title-row">
          <Building2 size={22} className="hk-icon-accent" />
          <h1 className="hk-dashboard-header__title">HKops Dashboard</h1>
          <span className="hk-badge hk-badge--ops">Operations</span>
        </div>
        {lastRefreshed && (
          <span className="hk-dashboard-header__last-refresh">
            Last refreshed: {lastRefreshed}
          </span>
        )}
      </div>

      <div className="hk-dashboard-header__controls">
        {/* Property Selector */}
        <div className="hk-control-group">
          <label className="hk-control-label">Property</label>
          <select
            className="hk-select"
            value={selectedPropertyId}
            onChange={e => onPropertyChange(e.target.value)}
          >
            {PROPERTIES.map(p => (
              <option key={p.property_id} value={p.property_id}>
                {p.property_name}
              </option>
            ))}
          </select>
        </div>

        {/* Business Date */}
        <div className="hk-control-group">
          <label className="hk-control-label">
            <Calendar size={13} style={{ marginRight: 4, verticalAlign: 'middle' }} />
            Business Date
          </label>
          <input
            type="date"
            className="hk-input"
            value={businessDate}
            onChange={e => onDateChange(e.target.value)}
          />
        </div>

        {/* Refresh */}
        <button className="hk-btn hk-btn--ghost" onClick={onRefresh} title="Refresh dashboard">
          <RefreshCw size={15} />
          <span>Refresh</span>
        </button>

        {/* Export */}
        <button className="hk-btn hk-btn--ghost" title="Export dashboard data">
          <Download size={15} />
          <span>Export</span>
        </button>
      </div>
    </div>
  )
}
