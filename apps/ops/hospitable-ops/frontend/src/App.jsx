import React, { useEffect, useState } from 'react'
import Rbac from './pages/Rbac'
import Integrations from './pages/Integrations'
import Dashboard from './pages/hkops/Dashboard'
import './styles.css'
import './hkops.css'

export default function App() {
  const [page, setPage] = useState('dashboard')
  const [status, setStatus] = useState(null)

  useEffect(() => {
    fetch('/')
      .then((r) => r.json())
      .then(setStatus)
      .catch(() => setStatus({ error: 'Backend not reachable (running with mock data)' }))
  }, [])

  function handleNavigate(destination, params) {
    const routeMap = {
      'room-board':   'home',
      'tasks':        'home',
      'inspections':  'home',
      'issues':       'home',
      'supply':       'home',
      'create-task':  'home',
      'export':       'home',
    }
    const target = routeMap[destination] || destination
    console.log('[Navigation]', destination, params)
    // In a full router setup this would push to the correct route.
    // For now, show a toast-style notice.
    setPage(target === 'home' ? 'dashboard' : target)
  }

  return (
    <div className="hk-app">
      <nav className="hk-app-nav">
        <div className="hk-app-nav__brand">
          <span className="hk-app-nav__logo">⚡</span>
          <span className="hk-app-nav__name">Hospitable Ops</span>
        </div>
        <div className="hk-app-nav__links">
          <button
            className={`hk-nav-btn ${page === 'dashboard' ? 'hk-nav-btn--active' : ''}`}
            onClick={() => setPage('dashboard')}
          >
            HKops Dashboard
          </button>
          <button
            className={`hk-nav-btn ${page === 'rbac' ? 'hk-nav-btn--active' : ''}`}
            onClick={() => setPage('rbac')}
          >
            RBAC
          </button>
          <button
            className={`hk-nav-btn ${page === 'integrations' ? 'hk-nav-btn--active' : ''}`}
            onClick={() => setPage('integrations')}
          >
            Integrations
          </button>
          <button
            className={`hk-nav-btn ${page === 'home' ? 'hk-nav-btn--active' : ''}`}
            onClick={() => setPage('home')}
          >
            Backend Status
          </button>
        </div>
      </nav>

      <main className="hk-app-main">
        {page === 'dashboard'    && <Dashboard onNavigate={handleNavigate} />}
        {page === 'rbac'         && <Rbac />}
        {page === 'integrations' && <Integrations />}
        {page === 'home'         && (
          <div className="hk-status-page">
            <h2>Backend Status</h2>
            <pre>{JSON.stringify(status, null, 2)}</pre>
          </div>
        )}
      </main>
    </div>
  )
}
