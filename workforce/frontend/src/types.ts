import type { FC } from 'react'

export interface Business {
  id: string
  name: string
}

export interface DashboardProps {
  businessId: string
  businessName: string
}

export type DashboardComponent = FC<DashboardProps>
