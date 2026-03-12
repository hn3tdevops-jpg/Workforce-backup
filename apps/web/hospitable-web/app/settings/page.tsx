"use client"

export default function SettingsPage() {
  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Application and property configuration</p>
      </div>
      <div className="card">
        <h2 className="font-bold mb-4">Property Information</h2>
        <div className="form-group">
          <label className="form-label">Property Name</label>
          <input className="form-input" defaultValue="Silver Sands Motel" readOnly />
        </div>
        <div className="form-group">
          <label className="form-label">Location ID</label>
          <input className="form-input" defaultValue={process.env.NEXT_PUBLIC_LOCATION_ID ?? 'silver-sands-main'} readOnly />
        </div>
        <div className="form-group">
          <label className="form-label">API Base URL</label>
          <input className="form-input" defaultValue={process.env.NEXT_PUBLIC_API_URL ?? '(same origin)'} readOnly />
        </div>
      </div>
      <div className="card">
        <h2 className="font-bold mb-4">Housekeeping Defaults</h2>
        <div className="form-group">
          <label className="form-label">Default Task Priority</label>
          <select className="form-select" defaultValue="normal">
            <option value="low">Low</option>
            <option value="normal">Normal</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>
        </div>
        <div className="alert alert-info mt-2">Settings persistence is not yet implemented. This page is a UI placeholder.</div>
      </div>
    </div>
  )
}
