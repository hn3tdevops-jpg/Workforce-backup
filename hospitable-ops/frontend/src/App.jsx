import React, { useEffect, useState } from 'react'
import Rbac from './pages/Rbac'
import Integrations from './pages/Integrations'

export default function App() {
  const [page, setPage] = useState('home')
  const [status, setStatus] = useState(null)

  useEffect(() => {
    fetch('/').then((r) => r.json()).then(setStatus).catch(() => setStatus({ error: 'Failed to reach backend' }))
  }, [])

  return (
    <div className="container">
      <h1>Hospitable Ops UI</h1>
      <nav style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <button onClick={() => setPage('home')}>Home</button>
        <button onClick={() => setPage('rbac')}>RBAC</button>
        <button onClick={() => setPage('integrations')}>Integrations</button>
        <a style={{ marginLeft: 10 }} href="/ui" target="_blank" rel="noreferrer">Open built UI</a>
      </nav>

      {page === 'home' && (
        <section>
          <h2>Backend status</h2>
          <pre>{JSON.stringify(status, null, 2)}</pre>
        </section>
      )}

      {page === 'rbac' && <Rbac />}
      {page === 'integrations' && <Integrations />}
    </div>
  )
}
