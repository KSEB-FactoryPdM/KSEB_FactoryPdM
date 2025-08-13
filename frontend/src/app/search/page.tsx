'use client';

import { useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import DashboardLayout from '@/components/DashboardLayout';

function Section({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-semibold text-neutral-700 mb-2">{title}</h3>
      {items.length === 0 ? (
        <p className="text-neutral-500 text-sm">No results</p>
      ) : (
        <ul className="list-disc list-inside text-sm text-neutral-800">
          {items.map((it, idx) => (
            <li key={idx}>{it}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function SearchPage() {
  const params = useSearchParams();
  const query = params.get('query')?.trim() ?? '';

  const suggestions = useMemo(() => {
    if (!query) return [];
    return [
      `Try filtering by device: ${query}`,
      `Search in alerts: ${query}`,
      `Open device details: ${query}`,
    ];
  }, [query]);

  return (
    <DashboardLayout>
      <div className="space-y-4">
        <div className="flex items-baseline justify-between">
          <h2 className="text-xl font-semibold">Search</h2>
          {query && (
            <span className="text-sm text-neutral-500">Query: "{query}"</span>
          )}
        </div>
        {!query ? (
          <div className="bg-white rounded-lg shadow p-6 text-sm text-neutral-700">
            Type a keyword in the header search to find devices, alerts and events.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Section title="Devices" items={[]} />
            <Section title="Alerts" items={[]} />
            <Section title="Events" items={suggestions} />
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

