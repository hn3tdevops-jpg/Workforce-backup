import { useState, useEffect, useCallback } from 'react'
import { api, setTokens, clearTokens } from '../api'

export interface AuthUser {
  id: string
  email: string
  is_superadmin: boolean
}

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) { setLoading(false); return }
    api.me()
      .then(setUser)
      .catch(() => { clearTokens(); setUser(null) })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    setError(null)
    const { access_token, refresh_token } = await api.login(email, password)
    setTokens(access_token, refresh_token)
    const me = await api.me()
    setUser(me)
  }, [])

  const logout = useCallback(async () => {
    const rt = localStorage.getItem('refresh_token') ?? ''
    try { await api.logout(rt) } catch { /* ignore */ }
    clearTokens()
    setUser(null)
  }, [])

  return { user, loading, error, setError, login, logout }
}
