import React from 'react'

export default function EmptyState({
  title,
  description,
  action,
}: {
  title: string
  description?: string
  action?: React.ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center p-8 border border-dashed border-neutral-300 rounded-lg bg-neutral-50">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        className="w-10 h-10 text-neutral-400 mb-3"
        aria-hidden="true"
      >
        <path stroke="currentColor" strokeWidth="1.5" d="M3 7a2 2 0 0 1 2-2h6l2 2h6a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z" />
      </svg>
      <h3 className="text-sm font-semibold text-neutral-800">{title}</h3>
      {description && (
        <p className="text-xs text-neutral-500 mt-1">{description}</p>
      )}
      {action && <div className="mt-3">{action}</div>}
    </div>
  )
}

