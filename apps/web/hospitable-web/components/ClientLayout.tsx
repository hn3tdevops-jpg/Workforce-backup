"use client"

import { useEffect, useState } from 'react'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import { usePathname, useRouter } from 'next/navigation'
import { useAuth } from '../lib/auth-store'

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const pathname = usePathname()
  const router = useRouter()
  const auth = useAuth()

  // Allow /login without chrome
  const isLogin = pathname === '/login'

  useEffect(() => {
    if (!isLogin && !auth.loading && !auth.user) {
      router.push('/login')
    }
  }, [isLogin, auth.loading, auth.user, router])

  if (auth.loading) return <div className="loading">Loading session…</div>

  // Protected-render guard: do not render shell chrome while unauthenticated and redirecting
  if (!isLogin && !auth.loading && !auth.user) {
    return <div className="loading">Redirecting to sign in…</div>
  }

  if (isLogin) return <main className="app-main">{children}</main>

  return (
    <div className="app-shell">
      <Topbar onMenuClick={() => setSidebarOpen((prev) => !prev)} />
      <div className="app-body">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main className="app-main">{children}</main>
      </div>
    </div>
  )
}
