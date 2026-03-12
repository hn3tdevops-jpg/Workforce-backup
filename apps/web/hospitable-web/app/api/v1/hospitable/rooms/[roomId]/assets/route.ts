import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '../../../../../../../lib/db'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(_req: NextRequest, { params }: { params: { roomId: string } }) {
  try {
    const db = getDb()
    const roomId = parseInt(params.roomId)
    const assets = db.prepare('SELECT * FROM hk_room_assets WHERE room_id = ? ORDER BY asset_name').all(roomId)
    return NextResponse.json(assets)
  } catch (e: unknown) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
