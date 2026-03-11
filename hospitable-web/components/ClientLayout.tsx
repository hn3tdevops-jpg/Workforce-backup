"use client"

import { useState } from 'react'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

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
