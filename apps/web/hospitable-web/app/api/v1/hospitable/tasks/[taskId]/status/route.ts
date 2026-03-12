import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '../../../../../../../lib/db'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function PATCH(req: NextRequest, { params }: { params: { taskId: string } }) {
  try {
    const db = getDb()
    const taskId = parseInt(params.taskId)
    const body = await req.json()
    const { status, notes } = body

    const updates: string[] = ['status = ?', "updated_at = datetime('now')"]
    const args: unknown[] = [status]

    if (status === 'completed') { updates.push("completed_at = datetime('now')") }
    if (notes !== undefined) { updates.push('description = ?'); args.push(notes) }

    args.push(taskId)
    db.prepare(`UPDATE hk_tasks SET ${updates.join(', ')} WHERE id = ?`).run(...args)

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
