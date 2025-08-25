'use client'
import { useState, useMemo } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import { useQuery } from '@tanstack/react-query'

interface Device {
  id: string
  name: string
  type: string
  status: string
}

const PAGE_SIZE = 5

export default function DevicesPage() {
  // Static mock data rarely changes, so we cache it for a short period to
  // avoid unnecessary refetches while still allowing manual refreshes.
  const { data: devices = [] } = useQuery<Device[]>({
    queryKey: ['devices'],
    queryFn: () => fetch('/mock-devices.json').then(r => r.json()),
    staleTime: 30000, // treat data as fresh for 30s
    gcTime: 300000, // keep in cache for 5 minutes
  })

  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState<'id' | 'name'>('id')
  const [page, setPage] = useState(0)

  const filtered = useMemo(() => {
    return devices
      .filter(d =>
        d.name.toLowerCase().includes(search.toLowerCase()) ||
        d.id.toLowerCase().includes(search.toLowerCase())
      )
      .sort((a, b) => {
        if (a[sortKey] < b[sortKey]) return -1
        if (a[sortKey] > b[sortKey]) return 1
        return 0
      })
  }, [devices, search, sortKey])

  const pageCount = Math.ceil(filtered.length / PAGE_SIZE)
  const paged = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  return (
    <DashboardLayout>
      <ChartCard title="Devices">
        <div className="flex items-center gap-2 mb-2">
          <input
            className="border rounded px-2 py-1 text-sm"
            placeholder="Search"
            value={search}
            onChange={e => {
              setSearch(e.target.value)
              setPage(0)
            }}
          />
          <select
            className="border rounded px-2 py-1 text-sm"
            value={sortKey}
            onChange={e => setSortKey(e.target.value as 'id' | 'name')}
          >
            <option value="id">ID</option>
            <option value="name">Name</option>
          </select>
        </div>
        <table className="w-full text-sm">
          <thead className="text-left">
            <tr>
              <th className="py-2">ID</th>
              <th className="py-2">Name</th>
              <th className="py-2">Type</th>
              <th className="py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {paged.map(device => (
              <tr key={device.id} className="border-t">
                <td className="py-2">
                  <a className="text-blue-600 underline" href={`/devices/${device.id}`}>{device.id}</a>
                </td>
                <td className="py-2">{device.name}</td>
                <td className="py-2">{device.type}</td>
                <td className="py-2">{device.status}</td>
              </tr>
            ))}
            {paged.length === 0 && (
              <tr>
                <td className="py-2" colSpan={4}>No devices</td>
              </tr>
            )}
          </tbody>
        </table>
        <div className="flex justify-between items-center mt-2">
          <button
            className="px-2 py-1 border rounded disabled:opacity-50"
            disabled={page === 0}
            onClick={() => setPage(p => Math.max(0, p - 1))}
          >Previous</button>
          <span className="text-sm">Page {page + 1} / {pageCount || 1}</span>
          <button
            className="px-2 py-1 border rounded disabled:opacity-50"
            disabled={page + 1 >= pageCount}
            onClick={() => setPage(p => Math.min(pageCount - 1, p + 1))}
          >Next</button>
        </div>
      </ChartCard>
    </DashboardLayout>
  )
}
