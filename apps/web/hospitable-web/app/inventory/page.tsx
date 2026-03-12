"use client"
import { useEffect, useState } from 'react'
import { api, RoomListItem, RoomAsset, SupplyPar } from '../../lib/api'

const LOCATION_ID = process.env.NEXT_PUBLIC_LOCATION_ID ?? 'silver-sands-main'

export default function InventoryPage() {
  const [rooms, setRooms] = useState<RoomListItem[]>([])
  const [selectedRoom, setSelectedRoom] = useState<RoomListItem | null>(null)
  const [assets, setAssets] = useState<RoomAsset[]>([])
  const [pars, setPars] = useState<SupplyPar[]>([])
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.listRooms(LOCATION_ID)
      .then(setRooms)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const selectRoom = async (room: RoomListItem) => {
    setSelectedRoom(room)
    setDetailLoading(true)
    try {
      const [a, p] = await Promise.all([api.listRoomAssets(room.id), api.listSupplyPars(room.id)])
      setAssets(a)
      setPars(p)
    } catch (e: any) { setError(e.message) }
    finally { setDetailLoading(false) }
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Inventory</h1>
        <p className="page-subtitle">Room assets and supply par levels</p>
      </div>
      {error && <div className="alert alert-error">{error}</div>}
      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '1.5rem' }}>
        <div className="card" style={{ padding: '0.75rem', maxHeight: '70vh', overflowY: 'auto' }}>
          <div style={{ fontWeight: 600, fontSize: '0.8rem', textTransform: 'uppercase', color: '#64748b', padding: '0.5rem 0.5rem 0.75rem' }}>Select Room</div>
          {loading ? <div className="loading">Loading…</div> : rooms.map((r) => (
            <div key={r.id}
              onClick={() => selectRoom(r)}
              style={{
                padding: '0.5rem 0.75rem', borderRadius: '6px', cursor: 'pointer', fontSize: '0.875rem',
                background: selectedRoom?.id === r.id ? '#2563eb' : 'transparent',
                color: selectedRoom?.id === r.id ? '#fff' : 'inherit',
              }}
            >
              Room {r.room_number} {r.room_label ? `— ${r.room_label}` : ''}
            </div>
          ))}
        </div>
        <div>
          {!selectedRoom ? (
            <div className="empty-state"><div className="empty-state-icon">📦</div><div className="empty-state-text">Select a room to view inventory</div></div>
          ) : detailLoading ? (
            <div className="loading">Loading room details…</div>
          ) : (
            <>
              <div className="card">
                <h2 className="font-bold mb-4">Assets — Room {selectedRoom.room_number}</h2>
                {assets.length === 0 ? <div className="text-muted text-sm">No assets recorded</div> : (
                  <table className="data-table">
                    <thead><tr><th>Type</th><th>Name</th><th>Expected</th><th>Present</th><th>Condition</th></tr></thead>
                    <tbody>
                      {assets.map((a) => (
                        <tr key={a.id}>
                          <td className="text-sm">{a.asset_type}</td>
                          <td>{a.asset_name}</td>
                          <td>{a.quantity_expected}</td>
                          <td style={{ color: a.quantity_present < a.quantity_expected ? '#dc2626' : 'inherit' }}>{a.quantity_present}</td>
                          <td className="text-sm">{a.condition_status ?? '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
              <div className="card">
                <h2 className="font-bold mb-4">Supply Pars — Room {selectedRoom.room_number}</h2>
                {pars.length === 0 ? <div className="text-muted text-sm">No supply pars configured</div> : (
                  <table className="data-table">
                    <thead><tr><th>Item</th><th>Code</th><th>Expected</th><th>Min</th><th>Unit</th></tr></thead>
                    <tbody>
                      {pars.map((p) => (
                        <tr key={p.id}>
                          <td>{p.item_name}</td>
                          <td className="text-sm text-muted">{p.item_code}</td>
                          <td>{p.expected_qty}</td>
                          <td>{p.min_qty}</td>
                          <td className="text-sm">{p.unit}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
