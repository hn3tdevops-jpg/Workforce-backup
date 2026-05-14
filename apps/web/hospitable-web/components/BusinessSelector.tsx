"use client"
import { useAuth } from '../lib/auth-store'

export default function BusinessSelector() {
  const { memberships, businessId, switchBusiness } = useAuth()

  const onChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value
    await switchBusiness(id)
  }

  const disabled = memberships.length === 0

  return (
    <div>
      <label htmlFor="business">Business: </label>
      <select id="business" name="business" value={businessId ?? ''} onChange={onChange} disabled={disabled}>
        {disabled ? (
          <option value="" disabled>No businesses available</option>
        ) : (
          memberships.map((b: any) => {
            const val = b.business_id
            return <option key={val} value={val}>{val}</option>
          })
        )}
      </select>
    </div>
  )
}
