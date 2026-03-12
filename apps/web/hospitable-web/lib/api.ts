/**
 * Hospitable API client.
 * All requests go to /api/v1/hospitable/...
 * The Next.js app proxies to the FastAPI backend in production.
 */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? ''

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type HousekeepingStatus =
  | 'dirty' | 'assigned' | 'cleaning' | 'clean' | 'inspect' | 'inspected' | 'blocked'

export type OccupancyStatus =
  | 'vacant' | 'occupied' | 'checkout' | 'stayover' | 'ooo'

export type InspectionStatus =
  | 'not_required' | 'pending' | 'passed' | 'failed'

export type MaintenanceStatus =
  | 'ok' | 'issue' | 'in_progress' | 'resolved'

export type TaskStatus =
  | 'open' | 'assigned' | 'in_progress' | 'done' | 'cancelled'

export type TaskType =
  | 'clean_checkout' | 'clean_stayover' | 'inspection' | 'restock' | 'maintenance_followup'

export type TaskPriority = 'low' | 'normal' | 'high' | 'urgent'

export type MaintenanceIssueStatus =
  | 'open' | 'triaged' | 'in_progress' | 'resolved' | 'closed'

export interface RoomListItem {
  id: number
  room_number: string
  room_label: string | null
  room_type: string | null
  housekeeping_status: HousekeepingStatus
  occupancy_status: OccupancyStatus
  inspection_status: InspectionStatus
  maintenance_status: MaintenanceStatus
  building_id: number
  floor_id: number
  sector_id: number
  room_group_id: number | null
  is_active: boolean
}

export interface RoomRead extends RoomListItem {
  bed_count: number | null
  bed_type_summary: string | null
  floor_surface: string
  out_of_order_reason: string | null
  notes: string | null
  last_cleaned_at: string | null
  last_inspected_at: string | null
  assets: RoomAsset[]
  supply_pars: SupplyPar[]
}

export interface RoomAsset {
  id: number
  asset_type: string
  asset_name: string
  quantity_expected: number
  quantity_present: number
  condition_status: string | null
  maintenance_notes: string | null
}

export interface SupplyPar {
  id: number
  item_code: string
  item_name: string
  expected_qty: number
  min_qty: number
  unit: string
}

export interface DashboardSummary {
  location_id: string
  total_rooms: number
  dirty_rooms: number
  assigned_rooms: number
  cleaning_rooms: number
  clean_rooms: number
  inspect_rooms: number
  inspected_rooms: number
  blocked_rooms: number
  maintenance_flagged_rooms: number
  open_tasks: number
  open_maintenance_issues: number
}

export interface TaskRead {
  id: number
  location_id: string
  room_id: number | null
  room_number?: string | null
  task_type: TaskType
  title: string
  description: string | null
  priority: TaskPriority
  status: TaskStatus
  assigned_user_id: string | null
  due_at: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface MaintenanceIssueRead {
  id: number
  location_id: string
  room_id: number | null
  room_number?: string | null
  issue_type: string
  title: string
  description: string | null
  severity: string
  status: MaintenanceIssueStatus
  assigned_user_id: string | null
  reported_by_user_id: string | null
  reported_at: string
  resolved_at: string | null
  created_at: string
  updated_at: string
}

export interface PropertyTree {
  location_id: string
  buildings: PropertyBuilding[]
}

export interface PropertyBuilding {
  id: number
  code: string
  name: string
  sort_order: number
  is_active: boolean
  floors: PropertyFloor[]
}

export interface PropertyFloor {
  id: number
  floor_number: number
  label: string
  sort_order: number
  sectors: PropertySector[]
}

export interface PropertySector {
  id: number
  code: string
  name: string
  description: string | null
  sort_order: number
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

export const api = {
  // Dashboard
  getDashboardSummary: (locationId: string) =>
    apiFetch<DashboardSummary>(`/api/v1/hospitable/dashboard/summary?location_id=${locationId}`),

  getHousekeepingBoard: (locationId: string) =>
    apiFetch<TaskRead[]>(`/api/v1/hospitable/dashboard/housekeeping-board?location_id=${locationId}`),

  getMaintenanceBoard: (locationId: string) =>
    apiFetch<MaintenanceIssueRead[]>(`/api/v1/hospitable/dashboard/maintenance-board?location_id=${locationId}`),

  // Property tree
  getPropertyTree: (locationId: string) =>
    apiFetch<PropertyTree>(`/api/v1/hospitable/locations/${locationId}/property-tree`),

  // Rooms
  listRooms: (locationId: string, params?: Record<string, string>) => {
    const qs = new URLSearchParams({ location_id: locationId, ...params }).toString()
    return apiFetch<RoomListItem[]>(`/api/v1/hospitable/rooms?${qs}`)
  },

  getRoom: (roomId: number) =>
    apiFetch<RoomRead>(`/api/v1/hospitable/rooms/${roomId}`),

  createRoom: (payload: object) =>
    apiFetch<RoomRead>('/api/v1/hospitable/rooms', { method: 'POST', body: JSON.stringify(payload) }),

  patchRoomStatus: (roomId: number, patch: object) =>
    apiFetch<RoomListItem>(`/api/v1/hospitable/rooms/${roomId}/status`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }),

  bulkRoomStatus: (payload: object) =>
    apiFetch<{ updated_room_ids: number[]; count: number }>('/api/v1/hospitable/rooms/bulk-status', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Tasks
  listTasks: (locationId: string, params?: Record<string, string>) => {
    const qs = new URLSearchParams({ location_id: locationId, ...params }).toString()
    return apiFetch<TaskRead[]>(`/api/v1/hospitable/tasks?${qs}`)
  },

  createTask: (payload: object) =>
    apiFetch<TaskRead>('/api/v1/hospitable/tasks', { method: 'POST', body: JSON.stringify(payload) }),

  patchTaskStatus: (taskId: number, status: TaskStatus, notes?: string) =>
    apiFetch<TaskRead>(`/api/v1/hospitable/tasks/${taskId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, notes }),
    }),

  assignTask: (taskId: number, userId: string) =>
    apiFetch<TaskRead>(`/api/v1/hospitable/tasks/${taskId}/assign`, {
      method: 'POST',
      body: JSON.stringify({ assigned_user_id: userId }),
    }),

  completeTask: (taskId: number) =>
    apiFetch<TaskRead>(`/api/v1/hospitable/tasks/${taskId}/complete`, { method: 'POST' }),

  // Maintenance
  listMaintenanceIssues: (locationId: string, params?: Record<string, string>) => {
    const qs = new URLSearchParams({ location_id: locationId, ...params }).toString()
    return apiFetch<MaintenanceIssueRead[]>(`/api/v1/hospitable/maintenance/issues?${qs}`)
  },

  createMaintenanceIssue: (payload: object) =>
    apiFetch<MaintenanceIssueRead>('/api/v1/hospitable/maintenance/issues', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  patchMaintenanceIssue: (issueId: number, patch: object) =>
    apiFetch<MaintenanceIssueRead>(`/api/v1/hospitable/maintenance/issues/${issueId}`, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }),

  // Room assets
  listRoomAssets: (roomId: number) =>
    apiFetch<RoomAsset[]>(`/api/v1/hospitable/rooms/${roomId}/assets`),

  // Supply pars
  listSupplyPars: (roomId: number) =>
    apiFetch<SupplyPar[]>(`/api/v1/hospitable/rooms/${roomId}/supply-pars`),
}
