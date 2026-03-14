import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '../../../../../../../lib/db'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function POST(_req: NextRequest, { params }: { params: { taskId: string } }) {
  try {
    const db = getDb()
    const taskId = parseInt(params.taskId)
    db.prepare(`UPDATE hk_tasks SET status = 'completed', completed_at = datetime('now'), updated_at = datetime('now') WHERE id = ?`).run(taskId)
    const task = db.prepare(`
      SELECT t.*, r.room_number FROM hk_tasks t
      LEFT JOIN hk_rooms r ON t.room_id = r.id
      WHERE t.id = ?
    `).get(taskId)
    return NextResponse.json(task)
  } catch (e: unknown) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
