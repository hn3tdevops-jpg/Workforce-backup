import React from 'react'
import { AlertTriangle, AlertCircle, Info, X } from 'lucide-react'

const ICON_MAP = {
  danger:  <AlertTriangle size={16} />,
  warning: <AlertCircle size={16} />,
  info:    <Info size={16} />,
}

const CLASS_MAP = {
  danger:  'hk-alert--danger',
  warning: 'hk-alert--warning',
  info:    'hk-alert--info',
}

export default function PropertyHealthBanner({ alerts }) {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="hk-health-banner hk-health-banner--ok">
        <Info size={16} />
        <span>All systems operational — no urgent alerts at this time.</span>
      </div>
    )
  }

  return (
    <div className="hk-health-banner">
      {alerts.map((alert, idx) => (
        <div key={idx} className={`hk-alert ${CLASS_MAP[alert.type] || 'hk-alert--info'}`}>
          <span className="hk-alert__icon">{ICON_MAP[alert.type] || ICON_MAP.info}</span>
          <span className="hk-alert__message">{alert.message}</span>
        </div>
      ))}
    </div>
  )
}
