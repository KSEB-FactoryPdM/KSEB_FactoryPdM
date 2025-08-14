'use client'

import { useState } from 'react'
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'

const faqs = [
  {
    question: 'How do I reset my password?',
    answer: 'Go to Settings > Account and choose "Reset password".',
  },
  {
    question: 'How do I contact support?',
    answer: 'Use the Email Support button or the Contact Form below.',
  },
]

export default function HelpPage() {
  const [query, setQuery] = useState('')

  const filteredFaqs = faqs.filter(faq =>
    faq.question.toLowerCase().includes(query.toLowerCase())
  )

  return (
    <DashboardLayout>
      <div className="space-y-4">
        <ChartCard title="Search Help">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-2 top-2.5 h-5 w-5 text-gray-500" />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search the FAQ..."
              className="w-full pl-8 pr-2 py-2 border rounded bg-input-bg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
        </ChartCard>

        <ChartCard title="Frequently Asked Questions">
          <ul className="space-y-2">
            {filteredFaqs.map(faq => (
              <li key={faq.question}>
                <details className="group">
                  <summary className="cursor-pointer text-primary group-open:text-primary-hover">
                    {faq.question}
                  </summary>
                  <p className="mt-2 text-gray-700">{faq.answer}</p>
                </details>
              </li>
            ))}
            {filteredFaqs.length === 0 && (
              <li className="text-gray-500">No matches found.</li>
            )}
          </ul>
        </ChartCard>

        <ChartCard title="Guides">
          <ul className="list-disc list-inside space-y-1">
            <li>
              <a
                href="https://example.com/guide.pdf"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary underline hover:text-primary-hover"
              >
                PDF User Guide
              </a>
            </li>
            <li>
              <a
                href="https://example.com/tutorial.mp4"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary underline hover:text-primary-hover"
              >
                Video Tutorial
              </a>
            </li>
          </ul>
        </ChartCard>

        <ChartCard title="Tooltips & Inline Help">
          <p>
            Hover over the{' '}
            <span
              title="This is a tooltip example"
              className="underline cursor-help text-primary"
            >
              highlighted text
            </span>{' '}
            to see a tooltip.
          </p>
        </ChartCard>

        <ChartCard title="Need Help?">
          <div className="space-x-2">
            <a
              href="mailto:support@example.com"
              className="px-4 py-2 bg-primary text-white rounded transition-colors hover:bg-primary-hover"
            >
              Email Support
            </a>
            <a
              href="/contact"
              className="px-4 py-2 bg-accent/90 text-gray-900 rounded transition-colors hover:bg-accent"
            >
              Contact Form
            </a>
          </div>
        </ChartCard>
      </div>
    </DashboardLayout>
  )
}

