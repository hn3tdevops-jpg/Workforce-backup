import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '../../../../../lib/db'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  try {
    const db = getDb()
    const { searchParams } = new URL(req.url)
    const locationId = searchParams.get('location_id') || ''
    const hkStatus = searchParams.get('housekeeping_status')
    const occStatus = searchParams.get('occupancy_status')

    let query = `
      SELECT r.*, b.name as building_name, f.name as floor_name, s.name as sector_name
      FROM hk_rooms r
      LEFT JOIN hk_buildings b ON r.building_id = b.id
      LEFT JOIN hk_floors f ON r.floor_id = f.id
      LEFT JOIN hk_sectors s ON r.sector_id = s.id
      WHERE r.location_id = ? AND r.is_active = 1
    `
    const args: unknown[] = [locationId]

    if (hkStatus) { query += ' AND r.housekeeping_status = ?'; args.push(hkStatus) }
    if (occStatus) { query += ' AND r.occupancy_status = ?'; args.push(occStatus) }
    query += ' ORDER BY r.room_number'

    const rooms = db.prepare(query).all(...args)
    return NextResponse.json(rooms)
  } catch (e: unknown) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  try {
    const db = getDb()
    const body = await req.json()
    const result = db.prepare(`
      INSERT INTO hk_rooms (location_id, building_id, floor_id, sector_id, room_number, room_type, bed_type, max_occupancy, housekeeping_status, occupancy_status, notes)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      body.location_id, body.building_id || null, body.floor_id || null, body.sector_id || null,
      body.room_number, body.room_type || 'standard', body.bed_type || null,
      body.max_occupancy || 2, body.housekeeping_status || 'dirty', body.occupancy_status || 'vacant',
      body.notes || null
    )
    const room = db.prepare('SELECT * FROM hk_rooms WHERE id = ?').get(result.lastInsertRowid)
    return NextResponse.json(room, { status: 201 })
  } catch (e: unknown) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
