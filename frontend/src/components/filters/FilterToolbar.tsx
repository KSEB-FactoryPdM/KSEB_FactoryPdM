'use client'
import React, { ReactNode } from 'react'

export default function FilterToolbar({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={[
        'flex flex-wrap items-center gap-2 p-2 rounded-md ring-1 ring-neutral-200 bg-neutral-50',
        'hover:ring-neutral-300 transition-shadow',
        className,
      ].join(' ')}
    >
      {children}
    </div>
  )}

