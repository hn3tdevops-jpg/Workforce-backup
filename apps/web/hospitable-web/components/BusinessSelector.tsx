"use client"

import { useAuth } from '../lib/auth-store'

export default function BusinessSelector() {
  const { memberships, businessId, switchBusiness } = useAuth()
  const disabled = memberships.length === 0

  const onChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value
    if (id) {
      await switchBusiness(id)
    }
  }

  return (
    <div>
      <label htmlFor="business">Business: </label>
      <select
        id="business"
        name="business"
        value={businessId ?? ''}
        onChange={onChange}
        disabled={disabled}
      >
        {disabled ? (
          <option value="">No businesses available</option>
        ) : (
          memberships.map((b) => (
            <option key={b.business_id} value={b.business_id}>
              {b.business_id}
            </option>
          ))
        )}
      </select>
    </div>
  )
}
