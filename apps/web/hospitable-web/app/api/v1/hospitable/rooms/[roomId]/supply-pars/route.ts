import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '../../../../../../../lib/db'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(_req: NextRequest, { params }: { params: { roomId: string } }) {
  try {
    const db = getDb()
    const roomId = parseInt(params.roomId)
    const pars = db.prepare('SELECT * FROM hk_supply_pars WHERE room_id = ? ORDER BY category, item_name').all(roomId)
    return NextResponse.json(pars)
  } catch (e: unknown) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
