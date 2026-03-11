import React, { useEffect, useState } from 'react'

export default function Integrations() {
  const [data, setData] = useState(null)
  useEffect(() => {
    fetch('/integrations').then((r) => r.json()).then(setData).catch(() => setData({ error: 'Failed to fetch /integrations' }))
  }, [])

  return (
    <div>
      <h2>Integrations</h2>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  )
}
