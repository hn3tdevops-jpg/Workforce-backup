import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '../../../../../lib/db'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  try {
    const db = getDb()
    const { searchParams } = new URL(req.url)
    const locationId = searchParams.get('location_id') || ''
    const status = searchParams.get('status')

    let query = `
      SELECT t.*, r.room_number
      FROM hk_tasks t
      LEFT JOIN hk_rooms r ON t.room_id = r.id
      WHERE t.location_id = ?
    `
    const args: unknown[] = [locationId]

    if (status) { query += ' AND t.status = ?'; args.push(status) }
    query += ' ORDER BY t.created_at DESC'

    const tasks = db.prepare(query).all(...args)
    return NextResponse.json(tasks)
  } catch (e: unknown) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  try {
    const db = getDb()
    const body = await req.json()
    const result = db.prepare(`
      INSERT INTO hk_tasks (location_id, room_id, task_type, title, description, priority, status)
      VALUES (?, ?, ?, ?, ?, ?, 'open')
    `).run(
      body.location_id, body.room_id || null,
      body.task_type, body.title,
      body.description || null, body.priority || 'normal'
    )
    const task = db.prepare(`
      SELECT t.*, r.room_number FROM hk_tasks t
      LEFT JOIN hk_rooms r ON t.room_id = r.id
      WHERE t.id = ?
    `).get(result.lastInsertRowid)
    return NextResponse.json(task, { status: 201 })
  } catch (e: unknown) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
