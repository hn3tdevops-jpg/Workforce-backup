"use client"
import { useEffect, useState, useCallback } from 'react'
import { api, RoomListItem, HousekeepingStatus, OccupancyStatus } from '../../lib/api'

const LOCATION_ID = process.env.NEXT_PUBLIC_LOCATION_ID ?? 'silver-sands-main'

const HK_STATUSES: HousekeepingStatus[] = ['dirty','assigned','cleaning','clean','inspect','inspected','blocked']
const OCC_STATUSES: OccupancyStatus[] = ['vacant','occupied','checkout','stayover','ooo']

function Badge({ value }: { value: string }) {
  return <span className={`badge badge-${value}`}>{value.replace(/_/g, ' ')}</span>
}

export default function RoomsPage() {
  const [rooms, setRooms] = useState<RoomListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [filterHK, setFilterHK] = useState('')
  const [filterOcc, setFilterOcc] = useState('')
  const [bulkHK, setBulkHK] = useState<HousekeepingStatus | ''>('')
  const [bulkLoading, setBulkLoading] = useState(false)
  const [success, setSuccess] = useState<string | null>(null)

  const load = useCallback(() => {
    setLoading(true)
    const params: Record<string, string> = {}
    if (filterHK) params.housekeeping_status = filterHK
    if (filterOcc) params.occupancy_status = filterOcc
    api.listRooms(LOCATION_ID, params)
      .then(setRooms)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [filterHK, filterOcc])

  useEffect(() => { load() }, [load])

  const toggleSelect = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const selectAll = () => setSelected(new Set(rooms.map((r) => r.id)))
  const clearAll = () => setSelected(new Set())

  const applyBulk = async () => {
    if (!bulkHK || selected.size === 0) return
    setBulkLoading(true)
    try {
      const result = await api.bulkRoomStatus({ room_ids: Array.from(selected), housekeeping_status: bulkHK })
      setSuccess(`Updated ${result.count} rooms`)
      setSelected(new Set())
      setBulkHK('')
      load()
    } catch (e: any) {
      setError(e.message)
    } finally {
      setBulkLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Room Board</h1>
        <p className="page-subtitle">All rooms — click to select, use bulk actions to update status</p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="room-board-toolbar">
        <select value={filterHK} onChange={(e) => setFilterHK(e.target.value)}>
          <option value="">All HK statuses</option>
          {HK_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={filterOcc} onChange={(e) => setFilterOcc(e.target.value)}>
          <option value="">All occupancy</option>
          {OCC_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <button className="btn btn-secondary btn-sm" onClick={selectAll}>Select all</button>
        <button className="btn btn-secondary btn-sm" onClick={clearAll}>Clear</button>
        {selected.size > 0 && (
          <>
            <span className="text-sm text-muted">{selected.size} selected</span>
            <select value={bulkHK} onChange={(e) => setBulkHK(e.target.value as HousekeepingStatus)}>
              <option value="">Set HK status…</option>
              {HK_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <button className="btn btn-primary btn-sm" onClick={applyBulk} disabled={bulkLoading || !bulkHK}>
              {bulkLoading ? 'Updating…' : 'Apply'}
            </button>
          </>
        )}
      </div>

      {loading ? (
        <div className="loading">Loading rooms…</div>
      ) : rooms.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🏨</div>
          <div className="empty-state-text">No rooms found. Run the Silver Sands seed script to populate rooms.</div>
        </div>
      ) : (
        <div className="room-grid">
          {rooms.map((room) => (
            <div
              key={room.id}
              className={`room-card hk-${room.housekeeping_status}${selected.has(room.id) ? ' selected' : ''}`}
              onClick={() => toggleSelect(room.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && toggleSelect(room.id)}
            >
              <div className="room-card-number">Room {room.room_number}</div>
              <div className="room-card-label">{room.room_label ?? room.room_type ?? ''}</div>
              <div className="room-card-badges">
                <Badge value={room.housekeeping_status} />
                <Badge value={room.occupancy_status} />
                {room.maintenance_status !== 'ok' && <Badge value={room.maintenance_status} />}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
