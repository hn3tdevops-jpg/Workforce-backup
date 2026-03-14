// ─────────────────────────────────────────────────────────────────────────────
// HKops Mock Data
// Covers: 2 properties, 25-40 rooms each, staff, tasks, inspections, issues
// ─────────────────────────────────────────────────────────────────────────────

export const PROPERTIES = [
  {
    property_id: 'prop-001',
    property_name: 'Silver Sands Motel',
    location: 'Coastal Highway, CA',
    total_rooms: 30,
    business_date: '2026-03-12',
  },
  {
    property_id: 'prop-002',
    property_name: 'Harborview Inn',
    location: 'Marina District, CA',
    total_rooms: 28,
    business_date: '2026-03-12',
  },
]

export const STAFF = [
  { staff_id: 'staff-001', name: 'Maria Gonzalez', role: 'Attendant' },
  { staff_id: 'staff-002', name: 'James Carter',   role: 'Attendant' },
  { staff_id: 'staff-003', name: 'Priya Patel',    role: 'Attendant' },
  { staff_id: 'staff-004', name: 'DeShawn Williams', role: 'Houseman' },
  { staff_id: 'staff-005', name: 'Linda Tran',     role: 'Supervisor' },
  { staff_id: 'staff-006', name: 'Carlos Ruiz',    role: 'Attendant' },
  { staff_id: 'staff-007', name: 'Fatima Hassan',  role: 'Attendant' },
]

// ─── Silver Sands Rooms ───────────────────────────────────────────────────────
const SS_ROOMS = [
  // South Sector
  { room_id: 'r-ss-01', room_number: '1',  sector: 'South', bed_type: 'Queen', status: 'clean',      assigned_to: null },
  { room_id: 'r-ss-02', room_number: '2',  sector: 'South', bed_type: 'Queen', status: 'dirty',      assigned_to: 'staff-001' },
  { room_id: 'r-ss-03', room_number: '3',  sector: 'South', bed_type: 'King',  status: 'in_progress', assigned_to: 'staff-001' },
  { room_id: 'r-ss-04', room_number: '4',  sector: 'South', bed_type: 'Queen', status: 'pending_inspection', assigned_to: 'staff-002' },
  { room_id: 'r-ss-05', room_number: '5',  sector: 'South', bed_type: 'Queen', status: 'dirty',      assigned_to: null },
  { room_id: 'r-ss-06', room_number: '6',  sector: 'South', bed_type: 'Double', status: 'out_of_order', assigned_to: null },
  // North Sector
  { room_id: 'r-ss-07', room_number: '7',  sector: 'North', bed_type: 'Queen', status: 'dirty',      assigned_to: 'staff-003' },
  { room_id: 'r-ss-08', room_number: '8',  sector: 'North', bed_type: 'Queen', status: 'in_progress', assigned_to: 'staff-003' },
  { room_id: 'r-ss-09', room_number: '9',  sector: 'North', bed_type: 'King',  status: 'inspected',  assigned_to: 'staff-005' },
  { room_id: 'r-ss-10', room_number: '10', sector: 'North', bed_type: 'Queen', status: 'pending_inspection', assigned_to: 'staff-002' },
  { room_id: 'r-ss-11', room_number: '11', sector: 'North', bed_type: 'Queen', status: 'dirty',      assigned_to: null },
  { room_id: 'r-ss-12', room_number: '12', sector: 'North', bed_type: 'Double', status: 'dirty',     assigned_to: null },
  // East Sector
  { room_id: 'r-ss-13', room_number: '13', sector: 'East',  bed_type: 'King',  status: 'clean',      assigned_to: null },
  { room_id: 'r-ss-14', room_number: '14', sector: 'East',  bed_type: 'Queen', status: 'dirty',      assigned_to: 'staff-006' },
  { room_id: 'r-ss-15', room_number: '15', sector: 'East',  bed_type: 'Queen', status: 'in_progress', assigned_to: 'staff-006' },
  { room_id: 'r-ss-16', room_number: '16', sector: 'East',  bed_type: 'Double', status: 'pending_inspection', assigned_to: 'staff-007' },
  { room_id: 'r-ss-17', room_number: '17', sector: 'East',  bed_type: 'King',  status: 'inspected',  assigned_to: 'staff-005' },
  { room_id: 'r-ss-18', room_number: '18', sector: 'East',  bed_type: 'Queen', status: 'dirty',      assigned_to: null },
  // West Sector
  { room_id: 'r-ss-19', room_number: '19', sector: 'West',  bed_type: 'Queen', status: 'clean',      assigned_to: null },
  { room_id: 'r-ss-20', room_number: '20', sector: 'West',  bed_type: 'Double', status: 'dirty',     assigned_to: 'staff-007' },
  { room_id: 'r-ss-21', room_number: '21', sector: 'West',  bed_type: 'Queen', status: 'in_progress', assigned_to: 'staff-007' },
  { room_id: 'r-ss-22', room_number: '22', sector: 'West',  bed_type: 'King',  status: 'out_of_order', assigned_to: null },
  { room_id: 'r-ss-23', room_number: '23', sector: 'West',  bed_type: 'Queen', status: 'pending_inspection', assigned_to: 'staff-005' },
  { room_id: 'r-ss-24', room_number: '24', sector: 'West',  bed_type: 'Double', status: 'dirty',     assigned_to: null },
  { room_id: 'r-ss-25', room_number: '25', sector: 'West',  bed_type: 'Queen', status: 'inspected',  assigned_to: 'staff-005' },
  // Courtyard
  { room_id: 'r-ss-26', room_number: '101', sector: 'Courtyard', bed_type: 'Suite', status: 'clean', assigned_to: null },
  { room_id: 'r-ss-27', room_number: '102', sector: 'Courtyard', bed_type: 'Suite', status: 'dirty', assigned_to: 'staff-002' },
  { room_id: 'r-ss-28', room_number: '103', sector: 'Courtyard', bed_type: 'Suite', status: 'pending_inspection', assigned_to: 'staff-005' },
  { room_id: 'r-ss-29', room_number: '104', sector: 'Courtyard', bed_type: 'King',  status: 'in_progress', assigned_to: 'staff-002' },
  { room_id: 'r-ss-30', room_number: '105', sector: 'Courtyard', bed_type: 'King',  status: 'dirty', assigned_to: null },
]

// ─── Harborview Rooms ─────────────────────────────────────────────────────────
const HV_ROOMS = [
  { room_id: 'r-hv-01', room_number: '201', sector: 'North Wing', bed_type: 'King',   status: 'dirty',      assigned_to: null },
  { room_id: 'r-hv-02', room_number: '202', sector: 'North Wing', bed_type: 'Queen',  status: 'in_progress', assigned_to: 'staff-001' },
  { room_id: 'r-hv-03', room_number: '203', sector: 'North Wing', bed_type: 'Double', status: 'pending_inspection', assigned_to: 'staff-005' },
  { room_id: 'r-hv-04', room_number: '204', sector: 'North Wing', bed_type: 'Queen',  status: 'clean',      assigned_to: null },
  { room_id: 'r-hv-05', room_number: '205', sector: 'North Wing', bed_type: 'King',   status: 'dirty',      assigned_to: 'staff-003' },
  { room_id: 'r-hv-06', room_number: '206', sector: 'North Wing', bed_type: 'Queen',  status: 'out_of_order', assigned_to: null },
  { room_id: 'r-hv-07', room_number: '207', sector: 'North Wing', bed_type: 'Double', status: 'inspected',  assigned_to: 'staff-005' },
  { room_id: 'r-hv-08', room_number: '301', sector: 'South Wing', bed_type: 'Queen',  status: 'dirty',      assigned_to: null },
  { room_id: 'r-hv-09', room_number: '302', sector: 'South Wing', bed_type: 'King',   status: 'in_progress', assigned_to: 'staff-006' },
  { room_id: 'r-hv-10', room_number: '303', sector: 'South Wing', bed_type: 'Queen',  status: 'pending_inspection', assigned_to: 'staff-005' },
  { room_id: 'r-hv-11', room_number: '304', sector: 'South Wing', bed_type: 'Double', status: 'dirty',      assigned_to: 'staff-007' },
  { room_id: 'r-hv-12', room_number: '305', sector: 'South Wing', bed_type: 'Queen',  status: 'clean',      assigned_to: null },
  { room_id: 'r-hv-13', room_number: '306', sector: 'South Wing', bed_type: 'King',   status: 'dirty',      assigned_to: null },
  { room_id: 'r-hv-14', room_number: '307', sector: 'South Wing', bed_type: 'Queen',  status: 'inspected',  assigned_to: 'staff-005' },
  { room_id: 'r-hv-15', room_number: '401', sector: 'East Wing',  bed_type: 'Suite',  status: 'dirty',      assigned_to: 'staff-002' },
  { room_id: 'r-hv-16', room_number: '402', sector: 'East Wing',  bed_type: 'Suite',  status: 'in_progress', assigned_to: 'staff-002' },
  { room_id: 'r-hv-17', room_number: '403', sector: 'East Wing',  bed_type: 'King',   status: 'pending_inspection', assigned_to: 'staff-005' },
  { room_id: 'r-hv-18', room_number: '404', sector: 'East Wing',  bed_type: 'Queen',  status: 'out_of_order', assigned_to: null },
  { room_id: 'r-hv-19', room_number: '405', sector: 'East Wing',  bed_type: 'Queen',  status: 'dirty',      assigned_to: null },
  { room_id: 'r-hv-20', room_number: '501', sector: 'West Wing',  bed_type: 'King',   status: 'clean',      assigned_to: null },
  { room_id: 'r-hv-21', room_number: '502', sector: 'West Wing',  bed_type: 'Double', status: 'dirty',      assigned_to: 'staff-003' },
  { room_id: 'r-hv-22', room_number: '503', sector: 'West Wing',  bed_type: 'Queen',  status: 'in_progress', assigned_to: 'staff-003' },
  { room_id: 'r-hv-23', room_number: '504', sector: 'West Wing',  bed_type: 'Queen',  status: 'pending_inspection', assigned_to: 'staff-005' },
  { room_id: 'r-hv-24', room_number: '505', sector: 'West Wing',  bed_type: 'King',   status: 'dirty',      assigned_to: null },
  { room_id: 'r-hv-25', room_number: '506', sector: 'West Wing',  bed_type: 'Double', status: 'inspected',  assigned_to: 'staff-005' },
  { room_id: 'r-hv-26', room_number: '601', sector: 'Penthouse',  bed_type: 'Suite',  status: 'dirty',      assigned_to: 'staff-001' },
  { room_id: 'r-hv-27', room_number: '602', sector: 'Penthouse',  bed_type: 'Suite',  status: 'clean',      assigned_to: null },
  { room_id: 'r-hv-28', room_number: '603', sector: 'Penthouse',  bed_type: 'King',   status: 'out_of_order', assigned_to: null },
]

export const ROOMS_BY_PROPERTY = {
  'prop-001': SS_ROOMS,
  'prop-002': HV_ROOMS,
}

// ─── KPIs ─────────────────────────────────────────────────────────────────────
function computeKpis(rooms, tasks, inspections, issues) {
  return {
    vacant_dirty:        rooms.filter(r => r.status === 'dirty').length,
    in_progress:         rooms.filter(r => r.status === 'in_progress').length,
    pending_inspection:  rooms.filter(r => r.status === 'pending_inspection').length,
    inspected:           rooms.filter(r => r.status === 'inspected').length,
    out_of_order:        rooms.filter(r => r.status === 'out_of_order').length,
    open_tasks:          tasks.filter(t => ['OPEN','ASSIGNED','IN_PROGRESS'].includes(t.task_status)).length,
    blocked_tasks:       tasks.filter(t => t.task_status === 'BLOCKED').length,
    failed_inspections:  inspections.filter(i => i.inspection_result === 'FAIL').length,
    unresolved_issues:   issues.filter(i => !i.resolved_flag).length,
    supply_exceptions:   issues.filter(i => ['INVENTORY_SHORTAGE','LINEN_SHORTAGE'].includes(i.issue_type) && !i.resolved_flag).length,
  }
}

// ─── Tasks ────────────────────────────────────────────────────────────────────
export const TASKS = [
  // Silver Sands
  { task_id:'t-001', property_id:'prop-001', room_id:'r-ss-02', room_number:'2',  sector_code:'South', task_type:'CHECKOUT_CLEAN',   task_status:'ASSIGNED',    priority:'HIGH',   assigned_staff_id:'staff-001', assigned_staff_name:'Maria Gonzalez', estimated_minutes:45, actual_minutes:null, created_at:'2026-03-12T07:00:00Z', due_at:'2026-03-12T10:00:00Z', started_at:null, completed_at:null, blocked_reason:null,  task_summary:'Checkout clean room 2', task_notes:'Guest checked out early', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-002', property_id:'prop-001', room_id:'r-ss-03', room_number:'3',  sector_code:'South', task_type:'STAYOVER',          task_status:'IN_PROGRESS', priority:'NORMAL', assigned_staff_id:'staff-001', assigned_staff_name:'Maria Gonzalez', estimated_minutes:30, actual_minutes:null, created_at:'2026-03-12T07:15:00Z', due_at:'2026-03-12T11:00:00Z', started_at:'2026-03-12T09:00:00Z', completed_at:null, blocked_reason:null, task_summary:'Stayover service room 3', task_notes:'', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-003', property_id:'prop-001', room_id:'r-ss-05', room_number:'5',  sector_code:'South', task_type:'CHECKOUT_CLEAN',   task_status:'OPEN',        priority:'HIGH',   assigned_staff_id:null, assigned_staff_name:null, estimated_minutes:45, actual_minutes:null, created_at:'2026-03-12T07:30:00Z', due_at:'2026-03-12T10:30:00Z', started_at:null, completed_at:null, blocked_reason:null, task_summary:'Checkout clean room 5', task_notes:'', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-004', property_id:'prop-001', room_id:'r-ss-07', room_number:'7',  sector_code:'North', task_type:'STAYOVER',          task_status:'ASSIGNED',    priority:'NORMAL', assigned_staff_id:'staff-003', assigned_staff_name:'Priya Patel', estimated_minutes:30, actual_minutes:null, created_at:'2026-03-12T07:00:00Z', due_at:'2026-03-12T11:30:00Z', started_at:null, completed_at:null, blocked_reason:null, task_summary:'Stayover service room 7', task_notes:'', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-005', property_id:'prop-001', room_id:'r-ss-08', room_number:'8',  sector_code:'North', task_type:'CHECKOUT_CLEAN',   task_status:'IN_PROGRESS', priority:'HIGH',   assigned_staff_id:'staff-003', assigned_staff_name:'Priya Patel', estimated_minutes:45, actual_minutes:null, created_at:'2026-03-12T07:00:00Z', due_at:'2026-03-12T10:00:00Z', started_at:'2026-03-12T09:30:00Z', completed_at:null, blocked_reason:null, task_summary:'Checkout clean room 8', task_notes:'', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-006', property_id:'prop-001', room_id:'r-ss-11', room_number:'11', sector_code:'North', task_type:'CHECKOUT_CLEAN',   task_status:'OPEN',        priority:'HIGH',   assigned_staff_id:null, assigned_staff_name:null, estimated_minutes:45, actual_minutes:null, created_at:'2026-03-12T08:00:00Z', due_at:'2026-03-12T11:00:00Z', started_at:null, completed_at:null, blocked_reason:null, task_summary:'Checkout clean room 11', task_notes:'', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-007', property_id:'prop-001', room_id:'r-ss-12', room_number:'12', sector_code:'North', task_type:'DEEP_CLEAN',        task_status:'BLOCKED',     priority:'URGENT', assigned_staff_id:'staff-004', assigned_staff_name:'DeShawn Williams', estimated_minutes:90, actual_minutes:null, created_at:'2026-03-12T06:00:00Z', due_at:'2026-03-12T09:00:00Z', started_at:null, completed_at:null, blocked_reason:'Waiting for linen delivery', task_summary:'Deep clean room 12', task_notes:'Linen cart not available', linked_issue_id:'iss-003', linked_inspection_id:null },
  { task_id:'t-008', property_id:'prop-001', room_id:'r-ss-14', room_number:'14', sector_code:'East',  task_type:'STAYOVER',          task_status:'ASSIGNED',    priority:'NORMAL', assigned_staff_id:'staff-006', assigned_staff_name:'Carlos Ruiz', estimated_minutes:30, actual_minutes:null, created_at:'2026-03-12T07:00:00Z', due_at:'2026-03-12T12:00:00Z', started_at:null, completed_at:null, blocked_reason:null, task_summary:'Stayover service room 14', task_notes:'', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-009', property_id:'prop-001', room_id:'r-ss-15', room_number:'15', sector_code:'East',  task_type:'CHECKOUT_CLEAN',   task_status:'IN_PROGRESS', priority:'HIGH',   assigned_staff_id:'staff-006', assigned_staff_name:'Carlos Ruiz', estimated_minutes:45, actual_minutes:null, created_at:'2026-03-12T07:00:00Z', due_at:'2026-03-12T10:30:00Z', started_at:'2026-03-12T09:15:00Z', completed_at:null, blocked_reason:null, task_summary:'Checkout clean room 15', task_notes:'', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-010', property_id:'prop-001', room_id:'r-ss-18', room_number:'18', sector_code:'East',  task_type:'AMENITY_RESTOCK',   task_status:'BLOCKED',     priority:'HIGH',   assigned_staff_id:'staff-004', assigned_staff_name:'DeShawn Williams', estimated_minutes:15, actual_minutes:null, created_at:'2026-03-12T08:30:00Z', due_at:'2026-03-12T10:00:00Z', started_at:null, completed_at:null, blocked_reason:'Supply closet locked – key missing', task_summary:'Restock amenities room 18', task_notes:'', linked_issue_id:'iss-005', linked_inspection_id:null },
  { task_id:'t-011', property_id:'prop-001', room_id:'r-ss-20', room_number:'20', sector_code:'West',  task_type:'STAYOVER',          task_status:'ASSIGNED',    priority:'NORMAL', assigned_staff_id:'staff-007', assigned_staff_name:'Fatima Hassan', estimated_minutes:30, actual_minutes:null, created_at:'2026-03-12T07:00:00Z', due_at:'2026-03-12T12:00:00Z', started_at:null, completed_at:null, blocked_reason:null, task_summary:'Stayover service room 20', task_notes:'', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-012', property_id:'prop-001', room_id:'r-ss-21', room_number:'21', sector_code:'West',  task_type:'CHECKOUT_CLEAN',   task_status:'IN_PROGRESS', priority:'HIGH',   assigned_staff_id:'staff-007', assigned_staff_name:'Fatima Hassan', estimated_minutes:45, actual_minutes:null, created_at:'2026-03-12T07:00:00Z', due_at:'2026-03-12T10:00:00Z', started_at:'2026-03-12T09:45:00Z', completed_at:null, blocked_reason:null, task_summary:'Checkout clean room 21', task_notes:'', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-013', property_id:'prop-001', room_id:'r-ss-24', room_number:'24', sector_code:'West',  task_type:'CHECKOUT_CLEAN',   task_status:'OPEN',        priority:'HIGH',   assigned_staff_id:null, assigned_staff_name:null, estimated_minutes:45, actual_minutes:null, created_at:'2026-03-12T08:00:00Z', due_at:'2026-03-12T11:00:00Z', started_at:null, completed_at:null, blocked_reason:null, task_summary:'Checkout clean room 24', task_notes:'', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-014', property_id:'prop-001', room_id:'r-ss-27', room_number:'102', sector_code:'Courtyard', task_type:'CHECKOUT_CLEAN', task_status:'ASSIGNED', priority:'HIGH', assigned_staff_id:'staff-002', assigned_staff_name:'James Carter', estimated_minutes:60, actual_minutes:null, created_at:'2026-03-12T07:00:00Z', due_at:'2026-03-12T10:00:00Z', started_at:null, completed_at:null, blocked_reason:null, task_summary:'Checkout clean suite 102', task_notes:'VIP guest', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-015', property_id:'prop-001', room_id:'r-ss-29', room_number:'104', sector_code:'Courtyard', task_type:'STAYOVER', task_status:'IN_PROGRESS', priority:'NORMAL', assigned_staff_id:'staff-002', assigned_staff_name:'James Carter', estimated_minutes:45, actual_minutes:null, created_at:'2026-03-12T07:00:00Z', due_at:'2026-03-12T12:00:00Z', started_at:'2026-03-12T10:00:00Z', completed_at:null, blocked_reason:null, task_summary:'Stayover service suite 104', task_notes:'', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-016', property_id:'prop-001', room_id:'r-ss-30', room_number:'105', sector_code:'Courtyard', task_type:'CHECKOUT_CLEAN', task_status:'OPEN', priority:'HIGH', assigned_staff_id:null, assigned_staff_name:null, estimated_minutes:60, actual_minutes:null, created_at:'2026-03-12T08:30:00Z', due_at:'2026-03-12T11:30:00Z', started_at:null, completed_at:null, blocked_reason:null, task_summary:'Checkout clean suite 105', task_notes:'', linked_issue_id:null, linked_inspection_id:null },
  // Completed
  { task_id:'t-017', property_id:'prop-001', room_id:'r-ss-09', room_number:'9',  sector_code:'North', task_type:'CHECKOUT_CLEAN',   task_status:'COMPLETED',   priority:'HIGH',   assigned_staff_id:'staff-003', assigned_staff_name:'Priya Patel', estimated_minutes:45, actual_minutes:42, created_at:'2026-03-12T06:00:00Z', due_at:'2026-03-12T09:00:00Z', started_at:'2026-03-12T07:00:00Z', completed_at:'2026-03-12T07:42:00Z', blocked_reason:null, task_summary:'Checkout clean room 9', task_notes:'', linked_issue_id:null, linked_inspection_id:'insp-001' },
  { task_id:'t-018', property_id:'prop-001', room_id:'r-ss-17', room_number:'17', sector_code:'East',  task_type:'CHECKOUT_CLEAN',   task_status:'VERIFIED',    priority:'HIGH',   assigned_staff_id:'staff-006', assigned_staff_name:'Carlos Ruiz', estimated_minutes:45, actual_minutes:40, created_at:'2026-03-12T06:00:00Z', due_at:'2026-03-12T09:00:00Z', started_at:'2026-03-12T07:00:00Z', completed_at:'2026-03-12T07:40:00Z', blocked_reason:null, task_summary:'Checkout clean room 17', task_notes:'', linked_issue_id:null, linked_inspection_id:'insp-002' },
  // Harborview
  { task_id:'t-019', property_id:'prop-002', room_id:'r-hv-01', room_number:'201', sector_code:'North Wing', task_type:'CHECKOUT_CLEAN', task_status:'OPEN', priority:'HIGH', assigned_staff_id:null, assigned_staff_name:null, estimated_minutes:45, actual_minutes:null, created_at:'2026-03-12T07:00:00Z', due_at:'2026-03-12T10:00:00Z', started_at:null, completed_at:null, blocked_reason:null, task_summary:'Checkout clean room 201', task_notes:'', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-020', property_id:'prop-002', room_id:'r-hv-02', room_number:'202', sector_code:'North Wing', task_type:'STAYOVER', task_status:'IN_PROGRESS', priority:'NORMAL', assigned_staff_id:'staff-001', assigned_staff_name:'Maria Gonzalez', estimated_minutes:30, actual_minutes:null, created_at:'2026-03-12T07:00:00Z', due_at:'2026-03-12T11:00:00Z', started_at:'2026-03-12T09:00:00Z', completed_at:null, blocked_reason:null, task_summary:'Stayover service room 202', task_notes:'', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-021', property_id:'prop-002', room_id:'r-hv-05', room_number:'205', sector_code:'North Wing', task_type:'CHECKOUT_CLEAN', task_status:'ASSIGNED', priority:'HIGH', assigned_staff_id:'staff-003', assigned_staff_name:'Priya Patel', estimated_minutes:45, actual_minutes:null, created_at:'2026-03-12T07:00:00Z', due_at:'2026-03-12T10:30:00Z', started_at:null, completed_at:null, blocked_reason:null, task_summary:'Checkout clean room 205', task_notes:'', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-022', property_id:'prop-002', room_id:'r-hv-08', room_number:'301', sector_code:'South Wing', task_type:'CHECKOUT_CLEAN', task_status:'OPEN', priority:'HIGH', assigned_staff_id:null, assigned_staff_name:null, estimated_minutes:45, actual_minutes:null, created_at:'2026-03-12T08:00:00Z', due_at:'2026-03-12T11:00:00Z', started_at:null, completed_at:null, blocked_reason:null, task_summary:'Checkout clean room 301', task_notes:'', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-023', property_id:'prop-002', room_id:'r-hv-09', room_number:'302', sector_code:'South Wing', task_type:'STAYOVER', task_status:'IN_PROGRESS', priority:'NORMAL', assigned_staff_id:'staff-006', assigned_staff_name:'Carlos Ruiz', estimated_minutes:30, actual_minutes:null, created_at:'2026-03-12T07:00:00Z', due_at:'2026-03-12T11:30:00Z', started_at:'2026-03-12T09:30:00Z', completed_at:null, blocked_reason:null, task_summary:'Stayover service room 302', task_notes:'', linked_issue_id:null, linked_inspection_id:null },
  { task_id:'t-024', property_id:'prop-002', room_id:'r-hv-11', room_number:'304', sector_code:'South Wing', task_type:'CHECKOUT_CLEAN', task_status:'BLOCKED', priority:'URGENT', assigned_staff_id:'staff-007', assigned_staff_name:'Fatima Hassan', estimated_minutes:45, actual_minutes:null, created_at:'2026-03-12T07:00:00Z', due_at:'2026-03-12T10:00:00Z', started_at:null, completed_at:null, blocked_reason:'Maintenance issue – AC unit not working', task_summary:'Checkout clean room 304', task_notes:'', linked_issue_id:'iss-008', linked_inspection_id:null },
  { task_id:'t-025', property_id:'prop-002', room_id:'r-hv-15', room_number:'401', sector_code:'East Wing', task_type:'CHECKOUT_CLEAN', task_status:'ASSIGNED', priority:'HIGH', assigned_staff_id:'staff-002', assigned_staff_name:'James Carter', estimated_minutes:60, actual_minutes:null, created_at:'2026-03-12T07:00:00Z', due_at:'2026-03-12T10:00:00Z', started_at:null, completed_at:null, blocked_reason:null, task_summary:'Checkout clean suite 401', task_notes:'VIP checkout', linked_issue_id:null, linked_inspection_id:null },
]

// ─── Inspections ──────────────────────────────────────────────────────────────
export const INSPECTIONS = [
  // Silver Sands
  { inspection_id:'insp-001', property_id:'prop-001', room_id:'r-ss-09', room_number:'9',  sector_code:'North', related_task_id:'t-017', related_task_summary:'Checkout clean room 9',  inspector_staff_id:'staff-005', inspector_staff_name:'Linda Tran', inspection_at:'2026-03-12T08:00:00Z', inspection_result:'PASS',           score_percent:96, defects_count:0, notes:'',                        followup_required_flag:false, followup_task_id:null, followup_task_summary:null, queue_age_minutes:0 },
  { inspection_id:'insp-002', property_id:'prop-001', room_id:'r-ss-17', room_number:'17', sector_code:'East',  related_task_id:'t-018', related_task_summary:'Checkout clean room 17', inspector_staff_id:'staff-005', inspector_staff_name:'Linda Tran', inspection_at:'2026-03-12T08:30:00Z', inspection_result:'PASS',           score_percent:98, defects_count:0, notes:'',                        followup_required_flag:false, followup_task_id:null, followup_task_summary:null, queue_age_minutes:0 },
  { inspection_id:'insp-003', property_id:'prop-001', room_id:'r-ss-25', room_number:'25', sector_code:'West',  related_task_id:null,    related_task_summary:null,                     inspector_staff_id:'staff-005', inspector_staff_name:'Linda Tran', inspection_at:'2026-03-12T09:00:00Z', inspection_result:'PASS_WITH_NOTES', score_percent:82, defects_count:2, notes:'Bathroom grout needs attention; towel rack loose', followup_required_flag:true, followup_task_id:'t-026', followup_task_summary:'Maintenance follow-up room 25', queue_age_minutes:0 },
  { inspection_id:'insp-004', property_id:'prop-001', room_id:'r-ss-04', room_number:'4',  sector_code:'South', related_task_id:'t-001', related_task_summary:'Checkout clean room 4',  inspector_staff_id:null,        inspector_staff_name:null,         inspection_at:null,                   inspection_result:'PENDING',         score_percent:0,  defects_count:0, notes:'',                        followup_required_flag:false, followup_task_id:null, followup_task_summary:null, queue_age_minutes:95 },
  { inspection_id:'insp-005', property_id:'prop-001', room_id:'r-ss-10', room_number:'10', sector_code:'North', related_task_id:null,    related_task_summary:null,                     inspector_staff_id:null,        inspector_staff_name:null,         inspection_at:null,                   inspection_result:'PENDING',         score_percent:0,  defects_count:0, notes:'',                        followup_required_flag:false, followup_task_id:null, followup_task_summary:null, queue_age_minutes:120 },
  { inspection_id:'insp-006', property_id:'prop-001', room_id:'r-ss-16', room_number:'16', sector_code:'East',  related_task_id:null,    related_task_summary:null,                     inspector_staff_id:null,        inspector_staff_name:null,         inspection_at:null,                   inspection_result:'PENDING',         score_percent:0,  defects_count:0, notes:'',                        followup_required_flag:false, followup_task_id:null, followup_task_summary:null, queue_age_minutes:75 },
  { inspection_id:'insp-007', property_id:'prop-001', room_id:'r-ss-23', room_number:'23', sector_code:'West',  related_task_id:null,    related_task_summary:null,                     inspector_staff_id:null,        inspector_staff_name:null,         inspection_at:null,                   inspection_result:'PENDING',         score_percent:0,  defects_count:0, notes:'',                        followup_required_flag:false, followup_task_id:null, followup_task_summary:null, queue_age_minutes:45 },
  { inspection_id:'insp-008', property_id:'prop-001', room_id:'r-ss-28', room_number:'103', sector_code:'Courtyard', related_task_id:null, related_task_summary:null, inspector_staff_id:null, inspector_staff_name:null, inspection_at:null, inspection_result:'PENDING', score_percent:0, defects_count:0, notes:'', followup_required_flag:false, followup_task_id:null, followup_task_summary:null, queue_age_minutes:30 },
  { inspection_id:'insp-009', property_id:'prop-001', room_id:'r-ss-06', room_number:'6',  sector_code:'South', related_task_id:null,    related_task_summary:null,                     inspector_staff_id:'staff-005', inspector_staff_name:'Linda Tran', inspection_at:'2026-03-12T07:00:00Z', inspection_result:'FAIL',            score_percent:55, defects_count:5, notes:'Mold in bathroom, broken lamp, stained carpet', followup_required_flag:true, followup_task_id:'t-027', followup_task_summary:'Deep clean + maintenance room 6', queue_age_minutes:0 },
  // Harborview
  { inspection_id:'insp-010', property_id:'prop-002', room_id:'r-hv-03', room_number:'203', sector_code:'North Wing', related_task_id:null, related_task_summary:null, inspector_staff_id:null, inspector_staff_name:null, inspection_at:null, inspection_result:'PENDING', score_percent:0, defects_count:0, notes:'', followup_required_flag:false, followup_task_id:null, followup_task_summary:null, queue_age_minutes:85 },
  { inspection_id:'insp-011', property_id:'prop-002', room_id:'r-hv-07', room_number:'207', sector_code:'North Wing', related_task_id:null, related_task_summary:null, inspector_staff_id:'staff-005', inspector_staff_name:'Linda Tran', inspection_at:'2026-03-12T08:45:00Z', inspection_result:'PASS', score_percent:94, defects_count:0, notes:'', followup_required_flag:false, followup_task_id:null, followup_task_summary:null, queue_age_minutes:0 },
  { inspection_id:'insp-012', property_id:'prop-002', room_id:'r-hv-10', room_number:'303', sector_code:'South Wing', related_task_id:null, related_task_summary:null, inspector_staff_id:null, inspector_staff_name:null, inspection_at:null, inspection_result:'PENDING', score_percent:0, defects_count:0, notes:'', followup_required_flag:false, followup_task_id:null, followup_task_summary:null, queue_age_minutes:110 },
  { inspection_id:'insp-013', property_id:'prop-002', room_id:'r-hv-14', room_number:'307', sector_code:'South Wing', related_task_id:null, related_task_summary:null, inspector_staff_id:'staff-005', inspector_staff_name:'Linda Tran', inspection_at:'2026-03-12T09:15:00Z', inspection_result:'PASS_WITH_NOTES', score_percent:88, defects_count:1, notes:'Minor scuff on wall near door', followup_required_flag:true, followup_task_id:null, followup_task_summary:null, queue_age_minutes:0 },
  { inspection_id:'insp-014', property_id:'prop-002', room_id:'r-hv-17', room_number:'403', sector_code:'East Wing', related_task_id:null, related_task_summary:null, inspector_staff_id:null, inspector_staff_name:null, inspection_at:null, inspection_result:'PENDING', score_percent:0, defects_count:0, notes:'', followup_required_flag:false, followup_task_id:null, followup_task_summary:null, queue_age_minutes:60 },
  { inspection_id:'insp-015', property_id:'prop-002', room_id:'r-hv-23', room_number:'504', sector_code:'West Wing', related_task_id:null, related_task_summary:null, inspector_staff_id:null, inspector_staff_name:null, inspection_at:null, inspection_result:'PENDING', score_percent:0, defects_count:0, notes:'', followup_required_flag:false, followup_task_id:null, followup_task_summary:null, queue_age_minutes:40 },
]

// ─── Issues ───────────────────────────────────────────────────────────────────
export const ISSUES = [
  // Silver Sands
  { issue_id:'iss-001', property_id:'prop-001', room_id:'r-ss-06', room_number:'6',  sector_code:'South', issue_type:'MAINTENANCE_FLAG',   priority:'URGENT', asset_category:'Fixture',   asset_name:'Bathroom Lamp',      quantity_affected:1, condition_code:'broken',  issue_description:'Lamp broken, glass shards on floor', reported_by_staff_id:'staff-001', reported_by_staff_name:'Maria Gonzalez', reported_at:'2026-03-12T07:05:00Z', resolved_flag:false, resolved_at:null, resolution_notes:'', linked_task_id:'t-027', linked_work_order_id:null, age_minutes:175 },
  { issue_id:'iss-002', property_id:'prop-001', room_id:'r-ss-06', room_number:'6',  sector_code:'South', issue_type:'CLEANLINESS_DEFECT',  priority:'HIGH',   asset_category:'Bathroom',  asset_name:'Grout/Tiles',        quantity_affected:1, condition_code:'damaged', issue_description:'Visible mold in shower grout', reported_by_staff_id:'staff-001', reported_by_staff_name:'Maria Gonzalez', reported_at:'2026-03-12T07:05:00Z', resolved_flag:false, resolved_at:null, resolution_notes:'', linked_task_id:'t-027', linked_work_order_id:null, age_minutes:175 },
  { issue_id:'iss-003', property_id:'prop-001', room_id:'r-ss-12', room_number:'12', sector_code:'North', issue_type:'LINEN_SHORTAGE',      priority:'HIGH',   asset_category:'Linen',     asset_name:'Sheet Set',          quantity_affected:3, condition_code:'missing', issue_description:'Linen cart for North sector missing 3 sheet sets', reported_by_staff_id:'staff-004', reported_by_staff_name:'DeShawn Williams', reported_at:'2026-03-12T06:30:00Z', resolved_flag:false, resolved_at:null, resolution_notes:'', linked_task_id:'t-007', linked_work_order_id:null, age_minutes:210 },
  { issue_id:'iss-004', property_id:'prop-001', room_id:'r-ss-22', room_number:'22', sector_code:'West',  issue_type:'MAINTENANCE_FLAG',   priority:'URGENT', asset_category:'HVAC',      asset_name:'AC Unit',            quantity_affected:1, condition_code:'needs_service', issue_description:'AC not cooling, guest complaint', reported_by_staff_id:'staff-007', reported_by_staff_name:'Fatima Hassan', reported_at:'2026-03-12T08:00:00Z', resolved_flag:false, resolved_at:null, resolution_notes:'', linked_task_id:null, linked_work_order_id:null, age_minutes:120 },
  { issue_id:'iss-005', property_id:'prop-001', room_id:'r-ss-18', room_number:'18', sector_code:'East',  issue_type:'INVENTORY_SHORTAGE',  priority:'HIGH',   asset_category:'Amenity',   asset_name:'Shampoo/Conditioner', quantity_affected:6, condition_code:'missing', issue_description:'East sector supply closet locked, key missing', reported_by_staff_id:'staff-006', reported_by_staff_name:'Carlos Ruiz', reported_at:'2026-03-12T08:30:00Z', resolved_flag:false, resolved_at:null, resolution_notes:'', linked_task_id:'t-010', linked_work_order_id:null, age_minutes:90 },
  { issue_id:'iss-006', property_id:'prop-001', room_id:'r-ss-25', room_number:'25', sector_code:'West',  issue_type:'DAMAGED_ITEM',        priority:'NORMAL', asset_category:'Fixture',   asset_name:'Towel Rack',         quantity_affected:1, condition_code:'damaged', issue_description:'Towel rack loose, needs tightening', reported_by_staff_id:'staff-005', reported_by_staff_name:'Linda Tran', reported_at:'2026-03-12T09:00:00Z', resolved_flag:false, resolved_at:null, resolution_notes:'', linked_task_id:'t-026', linked_work_order_id:null, age_minutes:60 },
  { issue_id:'iss-007', property_id:'prop-001', room_id:'r-ss-09', room_number:'9',  sector_code:'North', issue_type:'MISSING_ITEM',        priority:'LOW',    asset_category:'Electronics', asset_name:'TV Remote',        quantity_affected:1, condition_code:'missing', issue_description:'TV remote not found after checkout clean', reported_by_staff_id:'staff-003', reported_by_staff_name:'Priya Patel', reported_at:'2026-03-12T07:45:00Z', resolved_flag:true, resolved_at:'2026-03-12T08:15:00Z', resolution_notes:'Remote found in drawer, replaced in holder', linked_task_id:null, linked_work_order_id:null, age_minutes:0 },
  // Harborview
  { issue_id:'iss-008', property_id:'prop-002', room_id:'r-hv-11', room_number:'304', sector_code:'South Wing', issue_type:'MAINTENANCE_FLAG', priority:'URGENT', asset_category:'HVAC', asset_name:'AC Unit', quantity_affected:1, condition_code:'needs_service', issue_description:'AC unit not working, room cannot be occupied', reported_by_staff_id:'staff-007', reported_by_staff_name:'Fatima Hassan', reported_at:'2026-03-12T07:00:00Z', resolved_flag:false, resolved_at:null, resolution_notes:'', linked_task_id:'t-024', linked_work_order_id:null, age_minutes:180 },
  { issue_id:'iss-009', property_id:'prop-002', room_id:'r-hv-06', room_number:'206', sector_code:'North Wing', issue_type:'MAINTENANCE_FLAG', priority:'HIGH', asset_category:'Plumbing', asset_name:'Toilet', quantity_affected:1, condition_code:'needs_service', issue_description:'Toilet running continuously', reported_by_staff_id:'staff-001', reported_by_staff_name:'Maria Gonzalez', reported_at:'2026-03-12T07:30:00Z', resolved_flag:false, resolved_at:null, resolution_notes:'', linked_task_id:null, linked_work_order_id:null, age_minutes:150 },
  { issue_id:'iss-010', property_id:'prop-002', room_id:'r-hv-18', room_number:'404', sector_code:'East Wing', issue_type:'SAFETY_FLAG', priority:'URGENT', asset_category:'Electrical', asset_name:'Outlet', quantity_affected:2, condition_code:'damaged', issue_description:'Exposed wiring near bathroom outlet, safety hazard', reported_by_staff_id:'staff-002', reported_by_staff_name:'James Carter', reported_at:'2026-03-12T08:15:00Z', resolved_flag:false, resolved_at:null, resolution_notes:'', linked_task_id:null, linked_work_order_id:null, age_minutes:105 },
  { issue_id:'iss-011', property_id:'prop-002', room_id:'r-hv-28', room_number:'603', sector_code:'Penthouse', issue_type:'MAINTENANCE_FLAG', priority:'HIGH', asset_category:'Plumbing', asset_name:'Shower', quantity_affected:1, condition_code:'needs_service', issue_description:'Shower drain blocked, water pooling', reported_by_staff_id:'staff-001', reported_by_staff_name:'Maria Gonzalez', reported_at:'2026-03-12T09:00:00Z', resolved_flag:false, resolved_at:null, resolution_notes:'', linked_task_id:null, linked_work_order_id:null, age_minutes:60 },
  { issue_id:'iss-012', property_id:'prop-002', room_id:'r-hv-21', room_number:'502', sector_code:'West Wing', issue_type:'LINEN_SHORTAGE', priority:'NORMAL', asset_category:'Linen', asset_name:'Pillowcases', quantity_affected:4, condition_code:'missing', issue_description:'West wing linen cart short 4 pillowcases', reported_by_staff_id:'staff-003', reported_by_staff_name:'Priya Patel', reported_at:'2026-03-12T08:45:00Z', resolved_flag:false, resolved_at:null, resolution_notes:'', linked_task_id:null, linked_work_order_id:null, age_minutes:75 },
]

// ─── Staffing ─────────────────────────────────────────────────────────────────
export const STAFFING_BY_PROPERTY = {
  'prop-001': [
    { staff_id:'staff-001', name:'Maria Gonzalez', role:'Attendant', tasks_assigned:2, tasks_completed:0, rooms_cleaned:0, status:'active' },
    { staff_id:'staff-002', name:'James Carter',   role:'Attendant', tasks_assigned:2, tasks_completed:0, rooms_cleaned:0, status:'active' },
    { staff_id:'staff-003', name:'Priya Patel',    role:'Attendant', tasks_assigned:2, tasks_completed:1, rooms_cleaned:1, status:'active' },
    { staff_id:'staff-004', name:'DeShawn Williams', role:'Houseman', tasks_assigned:2, tasks_completed:0, rooms_cleaned:0, status:'blocked' },
    { staff_id:'staff-005', name:'Linda Tran',     role:'Supervisor', tasks_assigned:0, tasks_completed:3, rooms_cleaned:0, status:'active' },
    { staff_id:'staff-006', name:'Carlos Ruiz',    role:'Attendant', tasks_assigned:2, tasks_completed:1, rooms_cleaned:1, status:'active' },
    { staff_id:'staff-007', name:'Fatima Hassan',  role:'Attendant', tasks_assigned:2, tasks_completed:0, rooms_cleaned:0, status:'active' },
  ],
  'prop-002': [
    { staff_id:'staff-001', name:'Maria Gonzalez', role:'Attendant', tasks_assigned:2, tasks_completed:0, rooms_cleaned:0, status:'active' },
    { staff_id:'staff-002', name:'James Carter',   role:'Attendant', tasks_assigned:1, tasks_completed:0, rooms_cleaned:0, status:'active' },
    { staff_id:'staff-003', name:'Priya Patel',    role:'Attendant', tasks_assigned:2, tasks_completed:0, rooms_cleaned:0, status:'active' },
    { staff_id:'staff-005', name:'Linda Tran',     role:'Supervisor', tasks_assigned:0, tasks_completed:2, rooms_cleaned:0, status:'active' },
    { staff_id:'staff-006', name:'Carlos Ruiz',    role:'Attendant', tasks_assigned:1, tasks_completed:0, rooms_cleaned:0, status:'active' },
    { staff_id:'staff-007', name:'Fatima Hassan',  role:'Attendant', tasks_assigned:1, tasks_completed:0, rooms_cleaned:0, status:'blocked' },
  ],
}

// ─── Dashboard Summary per property ──────────────────────────────────────────
export function getDashboardData(propertyId) {
  const property = PROPERTIES.find(p => p.property_id === propertyId) || PROPERTIES[0]
  const rooms     = ROOMS_BY_PROPERTY[property.property_id] || []
  const tasks     = TASKS.filter(t => t.property_id === property.property_id)
  const inspections = INSPECTIONS.filter(i => i.property_id === property.property_id)
  const issues    = ISSUES.filter(i => i.property_id === property.property_id)
  const staffing  = STAFFING_BY_PROPERTY[property.property_id] || []

  const kpis = computeKpis(rooms, tasks, inspections, issues)

  const alerts = []
  if (kpis.unresolved_issues > 0) {
    const urgent = issues.filter(i => !i.resolved_flag && i.priority === 'URGENT')
    if (urgent.length > 0) alerts.push({ type:'danger', message:`${urgent.length} urgent issue${urgent.length > 1 ? 's' : ''} require immediate attention` })
  }
  if (kpis.blocked_tasks > 0) alerts.push({ type:'warning', message:`${kpis.blocked_tasks} task${kpis.blocked_tasks > 1 ? 's' : ''} blocked – supervisor action needed` })
  if (kpis.supply_exceptions > 0) alerts.push({ type:'warning', message:`${kpis.supply_exceptions} supply shortage${kpis.supply_exceptions > 1 ? 's' : ''} affecting operations` })
  const agingInspections = inspections.filter(i => i.inspection_result === 'PENDING' && i.queue_age_minutes > 90)
  if (agingInspections.length > 0) alerts.push({ type:'info', message:`${agingInspections.length} inspection${agingInspections.length > 1 ? 's' : ''} aging in queue (>90 min)` })

  return { property, kpis, rooms, tasks, inspections, issues, staffing, alerts }
}
