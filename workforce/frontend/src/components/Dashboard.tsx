import React from 'react'
import { DashboardProps, DashboardComponent } from '../types'
import EmployeesWidget from './EmployeesWidget'
import OpenShiftsWidget from './OpenShiftsWidget'
import SuperadminDashboard from './SuperadminDashboard'

export const Dashboard: DashboardComponent = ({ businessId, businessName, isSuperadmin }) => {
  return (
    <section>
      <h3 style={{ color: '#e2e8f0' }}>Overview</h3>
      <p style={{ color: '#94a3b8' }}>
        Business: {businessName} <code style={{ color: '#60a5fa' }}>{businessId}</code>
      </p>

      <div style={{ marginTop: '1rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        <EmployeesWidget businessId={businessId} />
        <OpenShiftsWidget businessId={businessId} />
      </div>

      {isSuperadmin && (
        <div style={{ marginTop: '2rem' }}>
          <h3 style={{ color: '#e2e8f0' }}>Superadmin</h3>
          <SuperadminDashboard />
        </div>
      )}
    </section>
  )
}

export default Dashboard
