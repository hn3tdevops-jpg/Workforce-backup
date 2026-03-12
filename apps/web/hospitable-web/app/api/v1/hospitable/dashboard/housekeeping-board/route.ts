import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '../../../../../../lib/db'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  try {
    const db = getDb()
    const { searchParams } = new URL(req.url)
    const locationId = searchParams.get('location_id') || ''

    const tasks = db.prepare(`
      SELECT t.*, r.room_number
      FROM hk_tasks t
      LEFT JOIN hk_rooms r ON t.room_id = r.id
      WHERE t.location_id = ? AND t.status NOT IN ('completed', 'cancelled')
      ORDER BY t.created_at DESC
      LIMIT 50
    `).all(locationId)

    return NextResponse.json(tasks)
  } catch (e: unknown) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
