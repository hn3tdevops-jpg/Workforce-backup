import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '../../../../../../lib/db'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  try {
    const db = getDb()
    const { searchParams } = new URL(req.url)
    const locationId = searchParams.get('location_id') || ''
    const status = searchParams.get('status')

    let query = `
      SELECT i.*, r.room_number
      FROM maintenance_issues i
      LEFT JOIN hk_rooms r ON i.room_id = r.id
      WHERE i.location_id = ?
    `
    const args: unknown[] = [locationId]

    if (status) { query += ' AND i.status = ?'; args.push(status) }
    query += ' ORDER BY i.created_at DESC'

    const issues = db.prepare(query).all(...args)
    return NextResponse.json(issues)
  } catch (e: unknown) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  try {
    const db = getDb()
    const body = await req.json()
    const result = db.prepare(`
      INSERT INTO maintenance_issues (location_id, room_id, issue_type, title, description, severity, status)
      VALUES (?, ?, ?, ?, ?, ?, 'open')
    `).run(
      body.location_id, body.room_id || null,
      body.issue_type, body.title,
      body.description || null, body.severity || 'normal'
    )
    const issue = db.prepare(`
      SELECT i.*, r.room_number FROM maintenance_issues i
      LEFT JOIN hk_rooms r ON i.room_id = r.id
      WHERE i.id = ?
    `).get(result.lastInsertRowid)
    return NextResponse.json(issue, { status: 201 })
  } catch (e: unknown) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
