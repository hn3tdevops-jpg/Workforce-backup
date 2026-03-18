"use client"

import { useMemo } from 'react'
import Link from 'next/link'
import { useAuth } from '../lib/auth-store'

const MODULES = [
  { label: 'Rooms', href: '/rooms', perm: 'hk.rooms.read', icon: '🏨' },
  { label: 'Tasks', href: '/housekeeping', perm: 'hk.tasks.manage', icon: '🧹' },
  { label: 'Assignments', href: '/assignments', perm: 'schedule.read', icon: '📅' },
  { label: 'Shifts', href: '/shifts', perm: 'time.read', icon: '⏱️' },
]

export default function WorkspaceHome() {
  const { user, businessId, memberships, roles, permissions } = useAuth()

  const availableModules = useMemo(() => MODULES.filter((m) => permissions.includes(m.perm)), [permissions])

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Workspace</h1>
        <p className="page-subtitle">Welcome to your workspace</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1rem' }}>
        <div className="card">
          <h3>User</h3>
          <div>{user ? (user.name ?? user.email ?? JSON.stringify(user)) : '—'}</div>

          <h3 style={{ marginTop: '1rem' }}>Active business</h3>
          <div>{businessId ?? '—'}</div>

          <h3 style={{ marginTop: '1rem' }}>Memberships</h3>
          <div>{memberships.length} memberships</div>

          <h3 style={{ marginTop: '1rem' }}>Roles</h3>
          <div>{roles.join(', ') || '—'}</div>

          <h3 style={{ marginTop: '1rem' }}>Permissions</h3>
          <div>{permissions.join(', ') || '—'}</div>
        </div>

        <div>
          <div className="card">
            <h3>Available modules</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
              {availableModules.length === 0 ? (
                <div>No modules available for your permissions.</div>
              ) : (
                availableModules.map((m) => (
                  <Link key={m.href} href={m.href} className="card card-module">
                    <div style={{ fontSize: 28 }}>{m.icon}</div>
                    <div>{m.label}</div>
                  </Link>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
