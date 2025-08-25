'use client'

import Link from 'next/link'
import type { Route } from 'next'
import DashboardLayout from '@/components/DashboardLayout'

export default function NotFound() {
  return (
    <DashboardLayout>
      <div className="bg-white rounded-lg shadow-md p-8 flex flex-col items-center justify-center space-y-4">
        <h1 className="text-2xl font-heading">Page Not Found</h1>
        <p className="text-text-primary">Sorry, the page you are looking for does not exist.</p>
        <Link href={'/monitoring' as Route} className="text-primary hover:underline">
          Back to Dashboard
        </Link>
      </div>
    </DashboardLayout>
  )
}
