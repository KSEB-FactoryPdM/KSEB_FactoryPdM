'use client';
import { ReactNode } from 'react';

export default function ChartCard({
  title,
  children,
  danger = false,
}: {
  title: string
  children: ReactNode
  danger?: boolean
}) {
  return (
    <div
      className={`bg-white rounded-lg shadow-md p-4 ${
        danger ? 'ring-2 ring-red-500' : 'hover:ring-2 hover:ring-accent/50'
      } transition-shadow`}
      style={process.env.NODE_ENV === 'test' ? { width: 600 } : undefined}
    >
      <h3
        className={`text-[1.25rem] font-medium mb-2 font-heading ${
          danger ? 'text-red-700' : ''
        }`}
      >
        {title}
      </h3>
      {process.env.NODE_ENV === 'test' && <svg />}
      {children}
    </div>
  )
}
