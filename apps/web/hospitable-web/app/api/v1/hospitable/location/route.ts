import { NextResponse } from 'next/server'
import { getLocationId } from '../../../../../lib/db'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    const id = getLocationId()
    return NextResponse.json({ location_id: id })
  } catch (e: unknown) {
    return NextResponse.json({ error: String(e) }, { status: 500 })
  }
}
