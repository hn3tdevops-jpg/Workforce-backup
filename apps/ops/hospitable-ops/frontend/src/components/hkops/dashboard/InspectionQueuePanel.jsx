import React from 'react'
import { ClipboardCheck, Clock, CheckCircle2, XCircle, AlertCircle, ChevronRight } from 'lucide-react'

const RESULT_CONFIG = {
  PENDING:        { label: 'Pending',         cls: 'hk-badge--pending',  icon: <Clock size={12} /> },
  PASS:           { label: 'Pass',            cls: 'hk-badge--success',  icon: <CheckCircle2 size={12} /> },
  FAIL:           { label: 'Fail',            cls: 'hk-badge--danger',   icon: <XCircle size={12} /> },
  PASS_WITH_NOTES:{ label: 'Pass w/ Notes',   cls: 'hk-badge--warning',  icon: <AlertCircle size={12} /> },
}

function InspectionRow({ insp, onAction }) {
  const cfg = RESULT_CONFIG[insp.inspection_result] || RESULT_CONFIG.PENDING
  const isAging = insp.inspection_result === 'PENDING' && insp.queue_age_minutes > 90

  return (
    <div className={`hk-insp-row ${isAging ? 'hk-insp-row--aging' : ''} ${insp.inspection_result === 'FAIL' ? 'hk-insp-row--fail' : ''}`}>
      <div className="hk-insp-row__room">
        <span className="hk-insp-room-num">Rm {insp.room_number}</span>
        <span className="hk-insp-sector">{insp.sector_code}</span>
      </div>
      <div className="hk-insp-row__inspector">
        {insp.inspector_staff_name || <span className="hk-text-muted">Unassigned</span>}
      </div>
      <div className="hk-insp-row__result">
        <span className={`hk-badge ${cfg.cls}`}>
          {cfg.icon} {cfg.label}
        </span>
      </div>
      <div className="hk-insp-row__age">
        {insp.inspection_result === 'PENDING' && insp.queue_age_minutes > 0 && (
          <span className={`hk-age-chip ${isAging ? 'hk-age-chip--warn' : ''}`}>
            <Clock size={11} /> {insp.queue_age_minutes}m
          </span>
        )}
        {insp.inspection_result !== 'PENDING' && insp.score_percent > 0 && (
          <span className="hk-score-chip">{insp.score_percent}%</span>
        )}
      </div>
      <div className="hk-insp-row__actions">
        {insp.inspection_result === 'PENDING' && (
          <button className="hk-btn hk-btn--xs hk-btn--primary" onClick={() => onAction && onAction('inspect', insp)}>
            Inspect
          </button>
        )}
        {insp.inspection_result !== 'PENDING' && (
          <button className="hk-btn hk-btn--xs hk-btn--ghost" onClick={() => onAction && onAction('view', insp)}>
            View <ChevronRight size={11} />
          </button>
        )}
      </div>
    </div>
  )
}

export default function InspectionQueuePanel({ inspections, onNavigate }) {
  const pending = inspections.filter(i => i.inspection_result === 'PENDING')
  const recent  = inspections.filter(i => i.inspection_result !== 'PENDING').slice(0, 5)
  const aging   = pending.filter(i => i.queue_age_minutes > 90)

  return (
    <div className="hk-panel">
      <div className="hk-panel__header">
        <ClipboardCheck size={18} className="hk-icon-accent" />
        <h3 className="hk-panel__title">Inspection Queue</h3>
        <div style={{ display: 'flex', gap: '0.4rem', marginLeft: 'auto' }}>
          {pending.length > 0 && <span className="hk-badge hk-badge--pending">{pending.length} pending</span>}
          {aging.length > 0   && <span className="hk-badge hk-badge--warning">{aging.length} aging</span>}
        </div>
      </div>

      <div className="hk-panel__body">
        {pending.length === 0 && recent.length === 0 ? (
          <p className="hk-empty-state">No inspections to show.</p>
        ) : (
          <>
            {pending.length > 0 && (
              <div className="hk-insp-section">
                <div className="hk-insp-section__title">Pending Queue</div>
                <div className="hk-insp-list">
                  {pending.map(i => (
                    <InspectionRow key={i.inspection_id} insp={i} onAction={(action, item) => onNavigate && onNavigate('inspections', { action, item })} />
                  ))}
                </div>
              </div>
            )}
            {recent.length > 0 && (
              <div className="hk-insp-section">
                <div className="hk-insp-section__title">Recent Results</div>
                <div className="hk-insp-list">
                  {recent.map(i => (
                    <InspectionRow key={i.inspection_id} insp={i} onAction={(action, item) => onNavigate && onNavigate('inspections', { action, item })} />
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        <div className="hk-panel__footer">
          <button className="hk-btn hk-btn--ghost hk-btn--sm" onClick={() => onNavigate && onNavigate('inspections')}>
            View all inspections <ChevronRight size={13} />
          </button>
        </div>
      </div>
    </div>
  )
}
