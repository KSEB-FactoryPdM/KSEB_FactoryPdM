'use client'

import { ReactNode } from 'react'
import Header from '@/components/Header'
import Footer from '@/components/Footer'
import ErrorBoundary from '@/components/ErrorBoundary'

export default function DashboardLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <ErrorBoundary>
      <div className="min-h-screen flex bg-white text-[#374151]">
        <div className="flex flex-col flex-1">
          <Header />
          <main className="p-4 space-y-4 flex-1">{children}</main>
          <Footer />
        </div>
      </div>
    </ErrorBoundary>
  )
}
