"use client"

import React, { createContext, useContext, useEffect, useState } from 'react'
import { api, type AuthUser, type AuthMembership } from './api'

type AuthContextValue = {
  loading: boolean
  user: AuthUser | null
  accessToken: string | null
  memberships: AuthMembership[]
  businessId: string | null
  roles: string[]
  permissions: string[]
  hydrate: () => Promise<void>
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  switchBusiness: (businessId: string) => Promise<void>
  hasPermission: (perm: string) => boolean
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<AuthUser | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [memberships, setMemberships] = useState<AuthMembership[]>([])
  const [businessId, setBusinessId] = useState<string | null>(null)
  const [roles, setRoles] = useState<string[]>([])
  const [permissions, setPermissions] = useState<string[]>([])

  const hydrate = async () => {
    setLoading(true)
    try {
      const token =
        typeof window !== 'undefined' ? localStorage.getItem('access_token') : null

      if (!token) {
        setUser(null)
        setAccessToken(null)
        setMemberships([])
        setBusinessId(null)
        setRoles([])
        setPermissions([])
        return
      }

      setAccessToken(token)

      const me = await api.auth.me()
      setUser(me.user)
      setMemberships(me.memberships ?? [])
      setBusinessId(me.business_id ?? null)
      setRoles(me.roles ?? [])
      setPermissions(me.permissions ?? [])
    } catch (e) {
      console.error('Hydrate failed', e)
      setUser(null)
      setAccessToken(null)
      setMemberships([])
      setBusinessId(null)
      setRoles([])
      setPermissions([])
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    hydrate()
  }, [])

  const login = async (email: string, password: string) => {
    setLoading(true)
    try {
      const res = await api.auth.login(email, password)
      const token = res.access_token

      if (!token) {
        throw new Error('No access token returned')
      }

      localStorage.setItem('access_token', token)
      setAccessToken(token)

      if (res.business_id) {
        setBusinessId(res.business_id)
      }

      await hydrate()
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
    }
    setUser(null)
    setAccessToken(null)
    setMemberships([])
    setBusinessId(null)
    setRoles([])
    setPermissions([])
  }

  const switchBusiness = async (nextBusinessId: string) => {
    setLoading(true)
    try {
      const res = await api.auth.switchBusiness(nextBusinessId)
      const newToken = res.access_token

      if (newToken) {
        localStorage.setItem('access_token', newToken)
        setAccessToken(newToken)
      }

      if (res.business_id) {
        setBusinessId(res.business_id)
      }

      const me = await api.auth.me()
      setUser(me.user)
      setMemberships(me.memberships ?? [])
      setBusinessId(me.business_id ?? null)
      setRoles(me.roles ?? [])
      setPermissions(me.permissions ?? [])
    } finally {
      setLoading(false)
    }
  }

  const hasPermission = (perm: string) => permissions.includes(perm)

  const value: AuthContextValue = {
    loading,
    user,
    accessToken,
    memberships,
    businessId,
    roles,
    permissions,
    hydrate,
    login,
    logout,
    switchBusiness,
    hasPermission,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
