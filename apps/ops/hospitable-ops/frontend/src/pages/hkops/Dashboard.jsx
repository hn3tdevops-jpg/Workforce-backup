import React, { useState, useCallback } from 'react'
import { getDashboardData, PROPERTIES } from '../../mock/hkopsMockData'
import DashboardHeader         from '../../components/hkops/dashboard/DashboardHeader'
import PropertyHealthBanner    from '../../components/hkops/dashboard/PropertyHealthBanner'
import DashboardKpiGrid        from '../../components/hkops/dashboard/DashboardKpiGrid'
import SupervisorAttentionPanel from '../../components/hkops/dashboard/SupervisorAttentionPanel'
import RoomStatusBreakdownPanel from '../../components/hkops/dashboard/RoomStatusBreakdownPanel'
import StaffingOverviewPanel   from '../../components/hkops/dashboard/StaffingOverviewPanel'
import InspectionQueuePanel    from '../../components/hkops/dashboard/InspectionQueuePanel'
import IssuesSummaryPanel      from '../../components/hkops/dashboard/IssuesSummaryPanel'
import InventoryExceptionsPanel from '../../components/hkops/dashboard/InventoryExceptionsPanel'
import ProductivityPanel       from '../../components/hkops/dashboard/ProductivityPanel'
import QuickActionsPanel       from '../../components/hkops/dashboard/QuickActionsPanel'

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function Dashboard({ onNavigate: parentNavigate }) {
  const [selectedPropertyId, setSelectedPropertyId] = useState(PROPERTIES[0].property_id)
  const [businessDate, setBusinessDate] = useState('2026-03-12')
  const [lastRefreshed, setLastRefreshed] = useState(formatTime(new Date()))
  const [refreshKey, setRefreshKey] = useState(0)

  const data = getDashboardData(selectedPropertyId)

  const handleRefresh = useCallback(() => {
    setLastRefreshed(formatTime(new Date()))
    setRefreshKey(k => k + 1)
  }, [])

  const handleNavigate = useCallback((destination, params) => {
    if (parentNavigate) {
      parentNavigate(destination, params)
    } else {
      // Fallback: log navigation intent (will be wired to router later)
      console.log('[HKops Dashboard] Navigate to:', destination, params)
    }
  }, [parentNavigate])

  return (
    <div className="hk-dashboard" key={refreshKey}>
      {/* ── Zone A: Command Header ─────────────────────────────────── */}
      <DashboardHeader
        selectedPropertyId={selectedPropertyId}
        onPropertyChange={setSelectedPropertyId}
        businessDate={businessDate}
        onDateChange={setBusinessDate}
        onRefresh={handleRefresh}
        lastRefreshed={lastRefreshed}
      />

      {/* ── Zone B: Health Banner ──────────────────────────────────── */}
      <PropertyHealthBanner alerts={data.alerts} />

      {/* ── Zone C: KPI Grid ──────────────────────────────────────── */}
      <DashboardKpiGrid
        kpis={data.kpis}
        onKpiClick={(kpiKey) => {
          const kpiRouteMap = {
            vacant_dirty:       ['tasks', { filter: 'dirty' }],
            in_progress:        ['tasks', { filter: 'in_progress' }],
            pending_inspection: ['inspections', { filter: 'pending' }],
            inspected:          ['inspections', { filter: 'passed' }],
            out_of_order:       ['room-board', { filter: 'out_of_order' }],
            open_tasks:         ['tasks', { filter: 'open' }],
            blocked_tasks:      ['tasks', { filter: 'blocked' }],
            failed_inspections: ['inspections', { filter: 'failed' }],
            unresolved_issues:  ['issues', { filter: 'open' }],
            supply_exceptions:  ['issues', { filter: 'supply' }],
          }
          const [dest, params] = kpiRouteMap[kpiKey] || ['room-board', {}]
          handleNavigate(dest, params)
        }}
      />

      {/* ── Zone D: Operational Panels ────────────────────────────── */}
      <div className="hk-dashboard-panels">

        {/* Row 1: Supervisor Attention + Room Status */}
        <div className="hk-panels-row hk-panels-row--2col">
          <SupervisorAttentionPanel
            tasks={data.tasks}
            issues={data.issues}
            onNavigate={handleNavigate}
          />
          <RoomStatusBreakdownPanel rooms={data.rooms} />
        </div>

        {/* Row 2: Staffing + Inspection Queue */}
        <div className="hk-panels-row hk-panels-row--2col">
          <StaffingOverviewPanel
            staffing={data.staffing}
            tasks={data.tasks}
          />
          <InspectionQueuePanel
            inspections={data.inspections}
            onNavigate={handleNavigate}
          />
        </div>

        {/* Row 3: Issues Summary + Inventory Exceptions */}
        <div className="hk-panels-row hk-panels-row--2col">
          <IssuesSummaryPanel
            issues={data.issues}
            onNavigate={handleNavigate}
          />
          <InventoryExceptionsPanel
            issues={data.issues}
            onNavigate={handleNavigate}
          />
        </div>

        {/* Row 4: Productivity Snapshot (full width) */}
        <div className="hk-panels-row hk-panels-row--1col">
          <ProductivityPanel
            tasks={data.tasks}
            staffing={data.staffing}
          />
        </div>
      </div>

      {/* ── Zone E: Quick Actions ─────────────────────────────────── */}
      <QuickActionsPanel
        onNavigate={handleNavigate}
        kpis={data.kpis}
      />
    </div>
  )
}
