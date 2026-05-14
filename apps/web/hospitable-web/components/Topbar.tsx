"use client"

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import BusinessSelector from './BusinessSelector'
import { useAuth } from '../lib/auth-store'

export interface TopbarProps {
  onMenuClick: () => void
}

export default function Topbar({ onMenuClick }: TopbarProps) {
  const { user, logout } = useAuth()
  const router = useRouter()

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

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
        <div className="topbar-user">{user?.email ?? ''}</div>
        <BusinessSelector />

        <button
          aria-label="Toggle dark mode"
          className="topbar-dark-toggle"
          type="button"
        >
          🌙
        </button>

        {user ? (
          <button className="btn btn-ghost" onClick={handleLogout}>Sign out</button>
        ) : (
          <Link href="/login" className="btn btn-primary">Sign in</Link>
        )}
      </div>
    </header>
  )
}
