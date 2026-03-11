import React, { useEffect } from 'react'

type Props = {
  open: boolean
  onClose: () => void
  title?: string
  children?: React.ReactNode
}

export default function Modal({ open, onClose, title, children }: Props) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    if (open) document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  const [active, setActive] = React.useState(0)

  return (
    <div className="tab-panel" role="region" aria-label={title}>
      <div
        className="modal-dialog"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div className="tabs" role="tablist">
            <button role="tab" aria-selected={active===0} className={`tab ${active===0 ? 'active' : ''}`} onClick={() => setActive(0)}>Content</button>
            <button role="tab" aria-selected={active===1} className={`tab ${active===1 ? 'active' : ''}`} onClick={() => setActive(1)}>Details</button>
          </div>
          <button aria-label="Close panel" onClick={onClose}>×</button>
        </div>
        <div className="tab-content">
          {active === 0 ? children : <div style={{padding:12}}>Details panel (add content here)</div>}
        </div>
      </div>
    </div>
  )
}
