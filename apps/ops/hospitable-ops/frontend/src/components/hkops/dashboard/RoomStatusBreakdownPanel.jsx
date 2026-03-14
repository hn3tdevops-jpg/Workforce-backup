import React from 'react'
import { LayoutGrid } from 'lucide-react'

const STATUS_CONFIG = {
  clean:               { label: 'Clean',              color: '#22c55e', bg: '#f0fdf4' },
  dirty:               { label: 'Vacant Dirty',       color: '#f59e0b', bg: '#fffbeb' },
  in_progress:         { label: 'In Progress',        color: '#3b82f6', bg: '#eff6ff' },
  pending_inspection:  { label: 'Pending Inspection', color: '#a855f7', bg: '#faf5ff' },
  inspected:           { label: 'Inspected',          color: '#10b981', bg: '#ecfdf5' },
  out_of_order:        { label: 'Out of Order',       color: '#ef4444', bg: '#fef2f2' },
}

function RoomDot({ status }) {
  const cfg = STATUS_CONFIG[status] || { color: '#9ca3af', bg: '#f9fafb' }
  return (
    <span
      className="hk-room-dot"
      title={cfg.label}
      style={{ backgroundColor: cfg.color }}
    />
  )
}

export default function RoomStatusBreakdownPanel({ rooms }) {
  // Count by status
  const counts = {}
  rooms.forEach(r => {
    counts[r.status] = (counts[r.status] || 0) + 1
  })

  const total = rooms.length

  // Group by sector
  const sectors = {}
  rooms.forEach(r => {
    if (!sectors[r.sector]) sectors[r.sector] = []
    sectors[r.sector].push(r)
  })

  return (
    <div className="hk-panel">
      <div className="hk-panel__header">
        <LayoutGrid size={18} className="hk-icon-accent" />
        <h3 className="hk-panel__title">Room Status Breakdown</h3>
        <span className="hk-panel__meta">{total} total rooms</span>
      </div>

      <div className="hk-panel__body">
        {/* Status summary bars */}
        <div className="hk-status-summary">
          {Object.entries(STATUS_CONFIG).map(([key, cfg]) => {
            const count = counts[key] || 0
            if (count === 0) return null
            const pct = Math.round((count / total) * 100)
            return (
              <div key={key} className="hk-status-row">
                <span className="hk-status-row__dot" style={{ backgroundColor: cfg.color }} />
                <span className="hk-status-row__label">{cfg.label}</span>
                <div className="hk-status-row__bar-wrap">
                  <div
                    className="hk-status-row__bar"
                    style={{ width: `${pct}%`, backgroundColor: cfg.color }}
                  />
                </div>
                <span className="hk-status-row__count">{count}</span>
                <span className="hk-status-row__pct">{pct}%</span>
              </div>
            )
          })}
        </div>

        {/* Room grid by sector */}
        <div className="hk-sector-grid">
          {Object.entries(sectors).map(([sector, sectorRooms]) => (
            <div key={sector} className="hk-sector-block">
              <div className="hk-sector-block__header">
                <span className="hk-sector-block__name">{sector}</span>
                <span className="hk-sector-block__count">{sectorRooms.length} rooms</span>
              </div>
              <div className="hk-sector-block__rooms">
                {sectorRooms.map(room => (
                  <div key={room.room_id} className="hk-room-chip" title={`Room ${room.room_number} — ${STATUS_CONFIG[room.status]?.label || room.status}`}>
                    <RoomDot status={room.status} />
                    <span className="hk-room-chip__num">{room.room_number}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="hk-status-legend">
          {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
            <span key={key} className="hk-legend-item">
              <span className="hk-legend-dot" style={{ backgroundColor: cfg.color }} />
              {cfg.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
