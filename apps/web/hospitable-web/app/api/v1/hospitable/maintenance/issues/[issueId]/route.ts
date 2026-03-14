import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '../../../../../../../lib/db'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function PATCH(req: NextRequest, { params }: { params: { issueId: string } }) {
  try {
    const db = getDb()
    const issueId = parseInt(params.issueId)
    const body = await req.json()

    const updates: string[] = ["updated_at = datetime('now')"]
    const args: unknown[] = []

    if (body.status) {
      updates.push('status = ?')
      args.push(body.status)
      if (body.status === 'resolved') {
        updates.push("resolved_at = datetime('now')")
      }
    }
    if (body.severity) { updates.push('severity = ?'); args.push(body.severity) }
    if (body.assigned_user_id !== undefined) { updates.push('assigned_user_id = ?'); args.push(body.assigned_user_id) }
    if (body.description !== undefined) { updates.push('description = ?'); args.push(body.description) }

    args.push(issueId)
    db.prepare(`UPDATE maintenance_issues SET ${updates.join(', ')} WHERE id = ?`).run(...args)

    const issue = db.prepare(`
      SELECT i.*, r.room_number FROM maintenance_issues i
      LEFT JOIN hk_rooms r ON i.room_id = r.id
      WHERE i.id = ?
    `).get(issueId)
    return NextResponse.json(issue)
  } catch (e: unknown) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
