import React, { useEffect, useState } from 'react'

export default function Rbac() {
  const [data, setData] = useState(null)
  useEffect(() => {
    fetch('/api/rbac').then((r) => r.json()).then(setData).catch(() => setData({ error: 'Failed to fetch /api/rbac' }))
  }, [])

  return (
    <div>
      <h2>RBAC</h2>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  )
}
