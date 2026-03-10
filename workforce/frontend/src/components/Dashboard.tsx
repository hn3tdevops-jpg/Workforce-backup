import React from 'react'
import { DashboardProps, DashboardComponent } from '../types'

export const Dashboard: DashboardComponent = ({ businessId, businessName }) => {
  return (
    <section>
      <h3 style={{ color: '#e2e8f0' }}>Overview</h3>
      <p style={{ color: '#94a3b8' }}>
        Business: {businessName} <code style={{ color: '#60a5fa' }}>{businessId}</code>
      </p>
      <div style={{ marginTop: '1rem', color: '#94a3b8' }}>
        {/* Placeholder widgets */}
        <div>Employees: —</div>
        <div>Open shifts: —</div>
      </div>
    </section>
  )
}

export default Dashboard
