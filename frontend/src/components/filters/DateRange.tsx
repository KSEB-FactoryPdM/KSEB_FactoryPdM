'use client'
import React from 'react'

export default function DateRange({
  start,
  end,
  onStart,
  onEnd,
  startLabel = 'Start Date',
  endLabel = 'End Date',
  clearLabel = 'Clear dates',
}: {
  start: string
  end: string
  onStart: (v: string) => void
  onEnd: (v: string) => void
  startLabel?: string
  endLabel?: string
  clearLabel?: string
}) {
  const minEnd = start ? start : undefined
  const maxStart = end ? end : undefined
  const showClear = Boolean(start || end)
  return (
    <div
      className="inline-flex items-center gap-2 rounded-md ring-1 ring-neutral-200 bg-white px-2 py-1 hover:ring-neutral-300 focus-within:ring-2 focus-within:ring-accent transition"
    >
      <button
        type="button"
        onClick={() => {
          const el = document.getElementById('date-range-start') as HTMLInputElement | null
          el?.focus()
        }}
        aria-hidden
        tabIndex={-1}
        className="text-neutral-400 hover:text-neutral-600"
        title={startLabel}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="3" y="5" width="18" height="16" rx="2" stroke="currentColor" strokeWidth="1.5" />
          <path d="M8 3v4M16 3v4M3 9h18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>
      <label htmlFor="date-range-start" className="sr-only">
        {startLabel}
      </label>
      <input
        id="date-range-start"
        type="date"
        className="px-1 py-1 outline-none border-0 focus:ring-0"
        value={start}
        onChange={(e) => onStart(e.target.value)}
        aria-label={startLabel}
        title={startLabel}
        max={maxStart}
      />
      <span className="mx-1 h-4 w-px bg-neutral-200" />
      <label htmlFor="date-range-end" className="sr-only">
        {endLabel}
      </label>
      <input
        id="date-range-end"
        type="date"
        className="px-1 py-1 outline-none border-0 focus:ring-0"
        value={end}
        onChange={(e) => onEnd(e.target.value)}
        aria-label={endLabel}
        title={endLabel}
        min={minEnd}
      />
      {showClear && (
        <button
          type="button"
          onClick={() => {
            onStart('');
            onEnd('');
          }}
          aria-label={clearLabel}
          title={clearLabel}
          className="ml-1 inline-flex h-5 w-5 items-center justify-center rounded hover:bg-neutral-100 text-neutral-400 hover:text-neutral-600"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      )}
    </div>
  )
}
