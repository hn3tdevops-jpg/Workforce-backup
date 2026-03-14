import Database from 'better-sqlite3'
import path from 'path'
import { randomUUID } from 'crypto'

const DB_PATH = process.env.DB_PATH || path.join(process.cwd(), 'workforce.db')

let _db: Database.Database | null = null

export function getDb(): Database.Database {
  if (_db) return _db
  _db = new Database(DB_PATH)
  _db.pragma('journal_mode = WAL')
  _db.pragma('foreign_keys = ON')
  initSchema(_db)
  seedIfEmpty(_db)
  return _db
}

function initSchema(db: Database.Database) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS locations (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      address TEXT,
      city TEXT,
      state TEXT,
      country TEXT DEFAULT 'US',
      timezone TEXT DEFAULT 'America/New_York',
      property_type TEXT DEFAULT 'hotel',
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS hk_buildings (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      location_id TEXT NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
      name TEXT NOT NULL,
      code TEXT,
      sort_order INTEGER DEFAULT 0,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS hk_floors (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      building_id INTEGER NOT NULL REFERENCES hk_buildings(id) ON DELETE CASCADE,
      name TEXT NOT NULL,
      floor_number INTEGER,
      sort_order INTEGER DEFAULT 0,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS hk_sectors (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      floor_id INTEGER NOT NULL REFERENCES hk_floors(id) ON DELETE CASCADE,
      name TEXT NOT NULL,
      code TEXT,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS hk_rooms (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      location_id TEXT NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
      building_id INTEGER REFERENCES hk_buildings(id) ON DELETE SET NULL,
      floor_id INTEGER REFERENCES hk_floors(id) ON DELETE SET NULL,
      sector_id INTEGER REFERENCES hk_sectors(id) ON DELETE SET NULL,
      room_number TEXT NOT NULL,
      room_type TEXT DEFAULT 'standard',
      bed_type TEXT,
      max_occupancy INTEGER DEFAULT 2,
      housekeeping_status TEXT DEFAULT 'dirty',
      occupancy_status TEXT DEFAULT 'vacant',
      is_active INTEGER DEFAULT 1,
      notes TEXT,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS hk_tasks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      location_id TEXT NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
      room_id INTEGER REFERENCES hk_rooms(id) ON DELETE SET NULL,
      task_type TEXT NOT NULL,
      title TEXT NOT NULL,
      description TEXT,
      priority TEXT DEFAULT 'normal',
      status TEXT DEFAULT 'open',
      assigned_user_id TEXT,
      due_at TEXT,
      completed_at TEXT,
      created_by_user_id TEXT,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS maintenance_issues (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      location_id TEXT NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
      room_id INTEGER REFERENCES hk_rooms(id) ON DELETE SET NULL,
      issue_type TEXT NOT NULL,
      title TEXT NOT NULL,
      description TEXT,
      severity TEXT DEFAULT 'normal',
      status TEXT DEFAULT 'open',
      assigned_user_id TEXT,
      reported_by_user_id TEXT,
      reported_at TEXT DEFAULT (datetime('now')),
      resolved_at TEXT,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS hk_room_assets (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      room_id INTEGER NOT NULL REFERENCES hk_rooms(id) ON DELETE CASCADE,
      asset_name TEXT NOT NULL,
      asset_type TEXT,
      serial_number TEXT,
      condition TEXT DEFAULT 'good',
      notes TEXT,
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS hk_supply_pars (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      room_id INTEGER NOT NULL REFERENCES hk_rooms(id) ON DELETE CASCADE,
      item_name TEXT NOT NULL,
      par_quantity INTEGER DEFAULT 1,
      unit TEXT DEFAULT 'each',
      category TEXT DEFAULT 'amenity',
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );
  `)
}

function seedIfEmpty(db: Database.Database) {
  const existing = db.prepare('SELECT COUNT(*) as n FROM locations').get() as { n: number }
  if (existing.n > 0) return

  const locationId = randomUUID()

  // Location
  db.prepare(`INSERT INTO locations (id, name, address, city, state, property_type, timezone)
    VALUES (?, 'Silver Sands Resort', '1 Ocean Drive', 'Miami Beach', 'FL', 'hotel', 'America/New_York')`
  ).run(locationId)

  // Building
  const building = db.prepare(`INSERT INTO hk_buildings (location_id, name, code, sort_order) VALUES (?, 'Building 1', 'B1', 1)`).run(locationId)
  const buildingId = building.lastInsertRowid

  // Floor
  const floor = db.prepare(`INSERT INTO hk_floors (building_id, name, floor_number, sort_order) VALUES (?, 'Floor 1', 1, 1)`).run(buildingId)
  const floorId = floor.lastInsertRowid

  // Sectors
  const northSector = db.prepare(`INSERT INTO hk_sectors (floor_id, name, code) VALUES (?, 'North Side', 'N')`).run(floorId)
  const southSector = db.prepare(`INSERT INTO hk_sectors (floor_id, name, code) VALUES (?, 'South Side', 'S')`).run(floorId)
  const northId = northSector.lastInsertRowid
  const southId = southSector.lastInsertRowid

  // Rooms 101-106 (North), 107-112 (South)
  const roomTypes = ['standard', 'standard', 'deluxe', 'deluxe', 'suite', 'standard']
  const bedTypes = ['king', 'queen', 'king', 'double', 'king', 'queen']
  const hkStatuses = ['dirty', 'dirty', 'dirty', 'assigned', 'clean', 'dirty', 'dirty', 'dirty', 'dirty', 'dirty', 'dirty', 'dirty']
  const occStatuses = ['checkout', 'vacant', 'occupied', 'occupied', 'vacant', 'vacant', 'checkout', 'vacant', 'occupied', 'occupied', 'vacant', 'vacant']

  const insertRoom = db.prepare(`INSERT INTO hk_rooms 
    (location_id, building_id, floor_id, sector_id, room_number, room_type, bed_type, max_occupancy, housekeeping_status, occupancy_status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)

  const roomIds: number[] = []
  for (let i = 0; i < 12; i++) {
    const roomNum = String(101 + i)
    const sectorId = i < 6 ? northId : southId
    const r = insertRoom.run(
      locationId, buildingId, floorId, sectorId,
      roomNum,
      roomTypes[i % 6],
      bedTypes[i % 6],
      i % 6 === 4 ? 4 : 2,
      hkStatuses[i],
      occStatuses[i]
    )
    roomIds.push(r.lastInsertRowid as number)
  }

  // Assets per room
  const assetNames = ['Smart TV', 'Mini Fridge', 'Microwave', 'Coffee Maker', 'Hair Dryer']
  const assetTypes = ['electronics', 'appliance', 'appliance', 'appliance', 'appliance']
  const insertAsset = db.prepare(`INSERT INTO hk_room_assets (room_id, asset_name, asset_type, condition) VALUES (?, ?, ?, 'good')`)
  for (const roomId of roomIds) {
    for (let j = 0; j < assetNames.length; j++) {
      insertAsset.run(roomId, assetNames[j], assetTypes[j])
    }
  }

  // Supply pars per room
  const supplies = [
    { name: 'Bath Towels', qty: 4, unit: 'each', cat: 'linen' },
    { name: 'Hand Towels', qty: 4, unit: 'each', cat: 'linen' },
    { name: 'Washcloths', qty: 4, unit: 'each', cat: 'linen' },
    { name: 'Shampoo', qty: 2, unit: 'bottle', cat: 'amenity' },
    { name: 'Conditioner', qty: 2, unit: 'bottle', cat: 'amenity' },
    { name: 'Body Wash', qty: 2, unit: 'bottle', cat: 'amenity' },
    { name: 'Bar Soap', qty: 2, unit: 'bar', cat: 'amenity' },
    { name: 'Toilet Paper', qty: 4, unit: 'roll', cat: 'supply' },
    { name: 'Facial Tissue', qty: 1, unit: 'box', cat: 'supply' },
    { name: 'Coffee Pods', qty: 4, unit: 'pod', cat: 'supply' },
  ]
  const insertPar = db.prepare(`INSERT INTO hk_supply_pars (room_id, item_name, par_quantity, unit, category) VALUES (?, ?, ?, ?, ?)`)
  for (const roomId of roomIds) {
    for (const s of supplies) {
      insertPar.run(roomId, s.name, s.qty, s.unit, s.cat)
    }
  }

  // Sample tasks
  const insertTask = db.prepare(`INSERT INTO hk_tasks (location_id, room_id, task_type, title, priority, status) VALUES (?, ?, ?, ?, ?, ?)`)
  insertTask.run(locationId, roomIds[0], 'clean_checkout', 'Checkout clean - Room 101', 'high', 'open')
  insertTask.run(locationId, roomIds[1], 'clean_stayover', 'Stayover service - Room 102', 'normal', 'open')
  insertTask.run(locationId, roomIds[3], 'inspection', 'Post-clean inspection - Room 104', 'normal', 'in_progress')
  insertTask.run(locationId, roomIds[6], 'clean_checkout', 'Checkout clean - Room 107', 'high', 'open')

  // Sample maintenance issues
  const insertIssue = db.prepare(`INSERT INTO maintenance_issues (location_id, room_id, issue_type, title, severity, status) VALUES (?, ?, ?, ?, ?, ?)`)
  insertIssue.run(locationId, roomIds[2], 'plumbing', 'Dripping faucet in bathroom', 'normal', 'open')
  insertIssue.run(locationId, roomIds[7], 'hvac', 'AC not cooling properly', 'high', 'open')
  insertIssue.run(locationId, roomIds[4], 'electrical', 'Bedside lamp not working', 'low', 'in_progress')

  console.log(`[DB] Seeded Silver Sands data. Location ID: ${locationId}`)
}

export function getLocationId(): string {
  const db = getDb()
  const row = db.prepare('SELECT id FROM locations LIMIT 1').get() as { id: string } | undefined
  return row?.id ?? ''
}
