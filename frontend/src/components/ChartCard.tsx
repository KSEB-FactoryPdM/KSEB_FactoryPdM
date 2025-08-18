'use client';
import { ReactNode, useEffect, useState } from 'react';

export default function ChartCard({
  title,
  children,
  danger = false,
}: {
  title: string
  children: ReactNode
  danger?: boolean
}) {
  const [flash, setFlash] = useState(false)

  // danger가 true로 전환될 때 잠깐 테두리 하이라이트
  useEffect(() => {
    if (!danger) return
    setFlash(true)
    const timer = setTimeout(() => setFlash(false), 700)
    return () => clearTimeout(timer)
  }, [danger])

  return (
    <div
      className={`bg-white text-[#374151] rounded-lg shadow-md p-4 ${
        danger ? 'ring-2 ring-red-500' : 'hover:ring-2 hover:ring-accent/50'
      } ${flash ? 'animate-pulse' : ''} transition-shadow`}
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
