'use client'

import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'

export default function HelpPage() {
  return (
    <DashboardLayout>
      <div className="space-y-4">
        <ChartCard title="Tooltips & Inline Help">
          <p>
            Hover over the
            {' '}
            <span title="This is a tooltip example" className="underline cursor-help">
              highlighted text
            </span>
            {' '}to see a tooltip.
          </p>
        </ChartCard>
        <ChartCard title="Guides">
          <ul className="list-disc list-inside space-y-1">
            <li>
              <a
                href="https://example.com/guide.pdf"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 underline"
              >
                PDF User Guide
              </a>
            </li>
            <li>
              <a
                href="https://example.com/tutorial.mp4"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 underline"
              >
                Video Tutorial
              </a>
            </li>
          </ul>
        </ChartCard>
        <ChartCard title="Need Help?">
          <div className="space-x-2">
            <a
              href="mailto:support@example.com"
              className="px-4 py-2 bg-primary text-white rounded"
            >
              Email Support
            </a>
            <a href="/contact" className="px-4 py-2 bg-accent text-white rounded">
              Contact Form
            </a>
          </div>
        </ChartCard>
      </div>
    </DashboardLayout>
  )
}
