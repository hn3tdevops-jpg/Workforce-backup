import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '../../../../../../../lib/db'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function PATCH(req: NextRequest, { params }: { params: { roomId: string } }) {
  try {
    const db = getDb()
    const roomId = parseInt(params.roomId)
    const body = await req.json()

    const updates: string[] = []
    const args: unknown[] = []

    if (body.housekeeping_status) { updates.push('housekeeping_status = ?'); args.push(body.housekeeping_status) }
    if (body.occupancy_status) { updates.push('occupancy_status = ?'); args.push(body.occupancy_status) }
    if (body.notes !== undefined) { updates.push('notes = ?'); args.push(body.notes) }

    if (updates.length === 0) return NextResponse.json({ error: 'Nothing to update' }, { status: 400 })

    updates.push("updated_at = datetime('now')")
    args.push(roomId)

    db.prepare(`UPDATE hk_rooms SET ${updates.join(', ')} WHERE id = ?`).run(...args)
    const room = db.prepare('SELECT * FROM hk_rooms WHERE id = ?').get(roomId)
    return NextResponse.json(room)
  } catch (e: unknown) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
