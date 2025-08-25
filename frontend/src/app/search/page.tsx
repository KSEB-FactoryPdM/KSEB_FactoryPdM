'use client';

import { useMemo } from 'react';
import { useSearchParams } from 'next/navigation';
import DashboardLayout from '@/components/DashboardLayout';
import DeviceSearchResult from '@/components/DeviceSearchResult';
import { useQuery } from '@tanstack/react-query';
import { alertList } from '@/mockData';

interface Device {
  id: string;
  name: string;
  type: string;
  status: string;
}

export default function SearchPage() {
  const params = useSearchParams();
  const query = (params?.get('query') ?? '').trim();

  // Backend REST Base
  const backendBase =
    process.env.NEXT_PUBLIC_BACKEND_BASE_URL?.replace(/\/$/, '') ||
    'http://localhost:8000/api/v1';

  const { data: devices = [] } = useQuery<Device[]>({
    queryKey: ['devices'],
    queryFn: async () => {
      try {
        const res = await fetch(`${backendBase}/devices?limit=1000`);
        if (!res.ok) throw new Error('failed to load devices');
        const json = (await res.json()) as { devices?: Device[] };
        return json.devices ?? [];
      } catch (e) {
        console.error('Failed to fetch devices', e);
        try {
          const mock = await fetch('/mock-devices.json');
          if (mock.ok) return await mock.json();
        } catch {}
        return [];
      }
    },
    staleTime: 30000,
    gcTime: 300000,
  });

  const filtered = useMemo(() => {
    if (!query) return [];
    return devices.filter(
      (d) =>
        d.name.toLowerCase().includes(query.toLowerCase()) ||
        d.id.toLowerCase().includes(query.toLowerCase()),
    );
  }, [devices, query]);

  return (
    <DashboardLayout>
      <div className="space-y-4">
        <div className="flex items-baseline justify-between">
          <h2 className="text-xl font-semibold">Search</h2>
          {query && (
            <span className="text-sm text-neutral-500">Query: &quot;{query}&quot;</span>
          )}
        </div>
        {!query ? (
          <div className="bg-white rounded-lg shadow p-6 text-sm text-neutral-700">
            Type a keyword in the header search to find devices, alerts and
            events.
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-6 text-sm text-neutral-700">
            No devices found
          </div>
        ) : (
          <div className="space-y-4">
            {filtered.map((device) => (
              <DeviceSearchResult
                key={device.id}
                device={device}
                alerts={alertList.filter((a) => a.device === device.id)}
              />
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

