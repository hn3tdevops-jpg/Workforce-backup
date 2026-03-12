import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '../../../../../../lib/db'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  try {
    const db = getDb()
    const { searchParams } = new URL(req.url)
    const locationId = searchParams.get('location_id') || ''

    const issues = db.prepare(`
      SELECT i.*, r.room_number
      FROM maintenance_issues i
      LEFT JOIN hk_rooms r ON i.room_id = r.id
      WHERE i.location_id = ? AND i.status NOT IN ('resolved', 'closed')
      ORDER BY i.created_at DESC
      LIMIT 50
    `).all(locationId)

    return NextResponse.json(issues)
  } catch (e: unknown) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
