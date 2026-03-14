import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '../../../../../../lib/db'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  try {
    const db = getDb()
    const body = await req.json()
    const { room_ids, housekeeping_status, occupancy_status } = body

    if (!room_ids || !Array.isArray(room_ids) || room_ids.length === 0) {
      return NextResponse.json({ error: 'room_ids required' }, { status: 400 })
    }

    const placeholders = room_ids.map(() => '?').join(',')
    const updates: string[] = []
    const args: unknown[] = []

    if (housekeeping_status) { updates.push('housekeeping_status = ?'); args.push(housekeeping_status) }
    if (occupancy_status) { updates.push('occupancy_status = ?'); args.push(occupancy_status) }

    if (updates.length === 0) return NextResponse.json({ error: 'No status fields to update' }, { status: 400 })

    updates.push("updated_at = datetime('now')")
    args.push(...room_ids)

    db.prepare(`UPDATE hk_rooms SET ${updates.join(', ')} WHERE id IN (${placeholders})`).run(...args)

    return NextResponse.json({ updated_room_ids: room_ids, count: room_ids.length })
  } catch (e: unknown) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
