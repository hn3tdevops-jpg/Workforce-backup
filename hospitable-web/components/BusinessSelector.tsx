"use client"
import { useEffect, useState } from 'react'

export default function BusinessSelector() {
  const [businesses, setBusinesses] = useState<string[]>([])

  useEffect(() => {
    fetch('/api/me/businesses')
      .then((r) => r.json())
      .then((data) => setBusinesses(data.map((b: any) => b.name)))
      .catch(() => setBusinesses(['Demo Business']))
  }, [])

  return (
    <div>
      <label htmlFor="business">Business: </label>
      <select id="business" name="business">
        {businesses.map((b) => (
          <option key={b}>{b}</option>
        ))}
      </select>
    </div>
  )
}
