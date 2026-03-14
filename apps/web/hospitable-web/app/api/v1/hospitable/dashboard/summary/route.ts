import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '../../../../../../lib/db'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  try {
    const db = getDb()
    const { searchParams } = new URL(req.url)
    const locationId = searchParams.get('location_id') || ''

    const roomStats = db.prepare(`
      SELECT
        COUNT(*) as total_rooms,
        SUM(CASE WHEN housekeeping_status = 'clean' THEN 1 ELSE 0 END) as clean_rooms,
        SUM(CASE WHEN housekeeping_status = 'dirty' THEN 1 ELSE 0 END) as dirty_rooms,
        SUM(CASE WHEN housekeeping_status = 'assigned' THEN 1 ELSE 0 END) as assigned_rooms,
        SUM(CASE WHEN housekeeping_status = 'cleaning' THEN 1 ELSE 0 END) as cleaning_rooms,
        SUM(CASE WHEN housekeeping_status = 'inspect' THEN 1 ELSE 0 END) as inspect_rooms,
        SUM(CASE WHEN housekeeping_status = 'inspected' THEN 1 ELSE 0 END) as inspected_rooms,
        SUM(CASE WHEN housekeeping_status = 'blocked' THEN 1 ELSE 0 END) as blocked_rooms,
        SUM(CASE WHEN occupancy_status = 'occupied' THEN 1 ELSE 0 END) as occupied_rooms,
        SUM(CASE WHEN occupancy_status = 'vacant' THEN 1 ELSE 0 END) as vacant_rooms,
        SUM(CASE WHEN occupancy_status = 'checkout' THEN 1 ELSE 0 END) as checkout_rooms
      FROM hk_rooms WHERE location_id = ? AND is_active = 1
    `).get(locationId) as Record<string, number>

    const taskStats = db.prepare(`
      SELECT
        COUNT(*) as total_tasks,
        SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_tasks,
        SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tasks,
        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks
      FROM hk_tasks WHERE location_id = ?
    `).get(locationId) as Record<string, number>

    const issueStats = db.prepare(`
      SELECT
        COUNT(*) as total_issues,
        SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_issues,
        SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_issues,
        SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_issues
      FROM maintenance_issues WHERE location_id = ?
    `).get(locationId) as Record<string, number>

    return NextResponse.json({
      location_id: locationId,
      ...roomStats,
      ...taskStats,
      ...issueStats,
    })
  } catch (e: unknown) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
