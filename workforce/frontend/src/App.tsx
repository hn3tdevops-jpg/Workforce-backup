import React, { useState } from 'react'
import Modal from './components/Modal'

export default function App() {
  const [open, setOpen] = useState(false)

  return (
    <div style={{fontFamily: 'system-ui, sans-serif', padding: 24}}>
      <h1>Workforce UI</h1>
      <p>React + Vite + TypeScript scaffold. Connect to the API and expand features as needed.</p>

      <div style={{marginTop: 16}}>
        <button onClick={() => setOpen(true)}>Open Modal</button>
      </div>

      <Modal open={open} title="Demo Modal" onClose={() => setOpen(false)}>
        <p>This is a demo modal. Add content here.</p>
        <div style={{marginTop:12}}>
          <button onClick={() => setOpen(false)}>Close</button>
        </div>
      </Modal>
    </div>
  )
}
