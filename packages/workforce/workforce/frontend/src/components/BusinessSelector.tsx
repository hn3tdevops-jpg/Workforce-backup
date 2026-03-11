import React from 'react';

interface Business { id: string; name: string }

export default function BusinessSelector({ businesses, selected, onSelect }: {
  businesses: Business[]
  selected: string | null
  onSelect: (id: string) => void
}) {
  return (
    <select
      value={selected || ''}
      onChange={e => onSelect(e.target.value)}
      style={{
        background: '#0f1117', color: '#e2e8f0', border: '1px solid #374151',
        borderRadius: 4, padding: '4px 8px', fontSize: '0.875rem', cursor: 'pointer',
      }}
    >
      <option value="">Select business</option>
      {businesses.map(b => (
        <option key={b.id} value={b.id}>{b.name}</option>
      ))}
    </select>
  );
}
