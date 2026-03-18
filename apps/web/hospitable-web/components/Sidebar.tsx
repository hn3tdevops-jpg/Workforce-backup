"use client"
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '../lib/auth-store'

const NAV_SECTIONS = [
  {
    label: 'Operations',
    links: [
      { label: 'Dashboard', href: '/', icon: '📊' },
      { label: 'Rooms', href: '/rooms', icon: '🏨', perm: 'hk.rooms.read' },
      { label: 'Housekeeping', href: '/housekeeping', icon: '🧹', perm: 'hk.tasks.manage' },
      { label: 'Assignments', href: '/assignments', icon: '📅', perm: 'schedule.read' },
      { label: 'Shifts', href: '/shifts', icon: '⏱️', perm: 'time.read' },
    ],
  },
]

export interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname()
  const { hasPermission } = useAuth()

  return (
    <>
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
          <span className="sidebar-brand">🏖️ Hospitable Ops</span>
          <button
            aria-label="Close navigation"
            className="sidebar-close"
            onClick={onClose}
          >
            ✕
          </button>
        </div>

        {NAV_SECTIONS.map((section) => (
          <div key={section.label}>
            <div className="sidebar-section-label">{section.label}</div>
            <ul className="sidebar-nav" role="list">
              {section.links.map(({ label, href, icon, perm }) => {
                if (perm && !hasPermission(perm)) return null
                const isActive = href === '/' ? pathname === '/' : pathname.startsWith(href)
                return (
                  <li key={href}>
                    <Link
                      href={href}
                      className={`sidebar-nav-link${isActive ? ' active' : ''}`}
                      onClick={onClose}
                    >
                      <span>{icon}</span>
                      {label}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </nav>
    </>
  )
}
