import React from 'react';

export default function BusinessSelector({ businesses, selected, onSelect }: any) {
  return (
    <div className="business-selector">
      <select value={selected || ''} onChange={(e)=>onSelect(e.target.value)}>
        <option value="">Select business</option>
        {businesses.map((b: any) => (
          <option key={b.id} value={b.id}>{b.name}</option>
        ))}
      </select>
    </div>
  );
}
