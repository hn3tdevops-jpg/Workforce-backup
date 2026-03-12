import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '../../../../../../../lib/db'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest, { params }: { params: { locationId: string } }) {
  try {
    const db = getDb()
    const locationId = params.locationId

    const location = db.prepare('SELECT * FROM locations WHERE id = ?').get(locationId) as Record<string, unknown> | undefined
    if (!location) return NextResponse.json({ error: 'Location not found' }, { status: 404 })

    const buildings = db.prepare('SELECT * FROM hk_buildings WHERE location_id = ? ORDER BY sort_order').all(locationId) as Record<string, unknown>[]

    const result = {
      ...location,
      buildings: buildings.map((b) => {
        const floors = db.prepare('SELECT * FROM hk_floors WHERE building_id = ? ORDER BY sort_order').all(b.id as number) as Record<string, unknown>[]
        return {
          ...b,
          floors: floors.map((f) => {
            const sectors = db.prepare('SELECT * FROM hk_sectors WHERE floor_id = ?').all(f.id as number) as Record<string, unknown>[]
            const roomCount = (db.prepare('SELECT COUNT(*) as n FROM hk_rooms WHERE floor_id = ?').get(f.id as number) as { n: number }).n
            return { ...f, sectors, room_count: roomCount }
          }),
        }
      }),
    }

    return NextResponse.json(result)
  } catch (e: unknown) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
