'use client'
import React from 'react'

export default function TimeRangeSelector({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <select
      className="border rounded px-2 py-1"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="1h">1h</option>
      <option value="24h">24h</option>
      <option value="7d">7d</option>
    </select>
  )
}
