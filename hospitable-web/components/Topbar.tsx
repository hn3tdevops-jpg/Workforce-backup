"use client"

export interface TopbarProps {
  onMenuClick: () => void
}

export default function Topbar({ onMenuClick }: TopbarProps) {
  return (
    <header className="topbar" role="banner">
      <button
        aria-label="Open navigation menu"
        aria-controls="main-sidebar"
        className="topbar-menu-btn"
        onClick={onMenuClick}
      >
        ☰
      </button>

      <span className="topbar-brand">Hospitable Ops</span>

      <div className="topbar-actions">
        {/* Business selector placeholder */}
        <label htmlFor="topbar-business-select" className="sr-only">
          Business
        </label>
        <select
          id="topbar-business-select"
          className="topbar-business-select"
          defaultValue="Demo Business"
        >
          <option>Demo Business</option>
        </select>

        {/* Dark-mode toggle placeholder */}
        <button
          aria-label="Toggle dark mode"
          className="topbar-dark-toggle"
          type="button"
        >
          🌙
        </button>
      </div>
    </header>
  )
}
