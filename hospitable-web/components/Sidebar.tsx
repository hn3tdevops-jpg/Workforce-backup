"use client"

import Link from 'next/link'

const NAV_LINKS: { label: string; href: string }[] = [
  { label: 'Dashboard', href: '/' },
  { label: 'Schedule', href: '/schedule' },
  { label: 'Employees', href: '/employees' },
  { label: 'Jobs', href: '/jobs' },
  { label: 'Reports', href: '/reports' },
  { label: 'Integrations', href: '/integrations' },
  { label: 'Settings', href: '/settings' },
  { label: 'Help', href: '/help' },
]

export interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          role="button"
          tabIndex={0}
          aria-label="Dismiss sidebar"
          className="sidebar-overlay"
          onClick={onClose}
          onKeyDown={(e) => e.key === 'Escape' && onClose()}
        />
      )}

      <nav
        id="main-sidebar"
        aria-label="Main navigation"
        className={`sidebar${isOpen ? ' sidebar--open' : ''}`}
      >
        <div className="sidebar-header">
          <span className="sidebar-brand">Hospitable Ops</span>
          <button
            aria-label="Close navigation"
            className="sidebar-close"
            onClick={onClose}
          >
            ✕
          </button>
        </div>

        {/* Business selector placeholder */}
        <div className="sidebar-business">
          <label htmlFor="sidebar-business-select" className="sidebar-business-label">
            Business
          </label>
          <select
            id="sidebar-business-select"
            className="sidebar-business-select"
            defaultValue="Demo Business"
          >
            <option>Demo Business</option>
          </select>
        </div>

        <ul className="sidebar-nav" role="list">
          {NAV_LINKS.map(({ label, href }) => (
            <li key={href}>
              <Link href={href} className="sidebar-nav-link">
                {label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </>
  )
}
