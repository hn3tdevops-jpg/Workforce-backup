"use client"
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const NAV_SECTIONS = [
  {
    label: 'Operations',
    links: [
      { label: 'Dashboard', href: '/', icon: '📊' },
      { label: 'Room Board', href: '/rooms', icon: '🏨' },
      { label: 'Housekeeping', href: '/housekeeping', icon: '🧹' },
      { label: 'Maintenance', href: '/maintenance', icon: '🔧' },
      { label: 'Inspections', href: '/inspections', icon: '✅' },
      { label: 'Inventory', href: '/inventory', icon: '📦' },
    ],
  },
  {
    label: 'Configuration',
    links: [
      { label: 'Property Setup', href: '/property-setup', icon: '🏗️' },
      { label: 'Settings', href: '/settings', icon: '⚙️' },
    ],
  },
]

export interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname()

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

        <div className="sidebar-business">
          <label htmlFor="sidebar-business-select" className="sidebar-business-label">
            Property
          </label>
          <select
            id="sidebar-business-select"
            className="sidebar-business-select"
            defaultValue="Silver Sands Motel"
          >
            <option>Silver Sands Motel</option>
          </select>
        </div>

        {NAV_SECTIONS.map((section) => (
          <div key={section.label}>
            <div className="sidebar-section-label">{section.label}</div>
            <ul className="sidebar-nav" role="list">
              {section.links.map(({ label, href, icon }) => {
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
