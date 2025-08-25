
'use client'

/**
 * FTS (Follow‑the‑Sun) Call Desk — Next.js App Router (single‑file drop‑in)
 *
 * What you get in this file:
 *  - Sidebar nav example (Phone icon + “Call”) — snippet in comments
 *  - /app/fts/page.tsx main page
 *  - Left: interactive map (Korea / USA) using amCharts v4
 *  - Right: searchable directory (factory → manager → phone)
 *  - Country toggle + factory pills + free‑text search (name/manager/phone)
 *  - Map click filters directory by region
 *
 * Dependencies (install once):
 *   npm i @amcharts/amcharts4 @amcharts/amcharts4-geodata lucide-react
 *   # Tailwind assumed; if not, swap classes to your styling system
 *
 * Sidebar integration (example):
 *   // components/Sidebar.tsx (or wherever your nav is)
 *   import { Phone } from 'lucide-react'
 *   ...
 *   <Link href="/fts" className={cx('nav-item', pathname === '/fts' && 'active')}>
 *     <Phone className="h-4 w-4" />
 *     <span>Call</span>
 *   </Link>
 *
 * File placement:
 *   Save this as app/fts/page.tsx
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import { Phone, PhoneCall, Search as SearchIcon, X } from 'lucide-react'

// ---------------------------
// Types & Mock Data
// ---------------------------

type Country = 'KR' | 'US'

interface Factory {
  id: string
  name: string
  country: Country
  /** Region display name that should match the polygon's `{name}` from geodata */
  regionName: string
  manager: string
  phone: string // use international format if multi‑country
}

// NOTE: Ensure `regionName` matches the map polygon name from geodata.
// For Korea, amCharts geodata names are typically English (e.g., 'Seoul', 'Busan', 'Gyeonggi‑do').
// If your local KR geodata uses Korean labels (e.g., '서울특별시'), update these to match.
const FACTORIES: Factory[] = [
  // Korea examples
  { id: 'kr-seoul-01', name: 'Seoul Plant A', country: 'KR', regionName: 'Seoul', manager: '김미정', phone: '+82-2-1234-5678' },
  { id: 'kr-busan-01', name: 'Busan Plant', country: 'KR', regionName: 'Busan', manager: '이도현', phone: '+82-51-555-0101' },
  { id: 'kr-gg-01', name: 'Gyeonggi Plant', country: 'KR', regionName: 'Gyeonggi-do', manager: '박지훈', phone: '+82-31-777-0909' },

  // USA examples
  { id: 'us-ca-01', name: 'California Fab', country: 'US', regionName: 'California', manager: 'Ava Johnson', phone: '+1-415-555-0139' },
  { id: 'us-tx-01', name: 'Texas Assembly', country: 'US', regionName: 'Texas', manager: 'Noah Davis', phone: '+1-512-555-0110' },
  { id: 'us-ny-01', name: 'New York Hub', country: 'US', regionName: 'New York', manager: 'Liam Miller', phone: '+1-212-555-0188' }
]

// ---------------------------
// Utility helpers
// ---------------------------

function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(' ')
}

function unique<T>(arr: T[]): T[] {
  return Array.from(new Set(arr))
}

// ---------------------------
// MapRegionPicker (amCharts v4)
// ---------------------------

type MapRegionPickerProps = {
  country: Country
  height?: number | string
  highlightRegionName?: string | null
  onRegionSelect?: (regionName: string | null) => void
}

function MapRegionPicker({ country, height = 420, highlightRegionName, onRegionSelect }: MapRegionPickerProps) {
  const chartRef = useRef<any>(null)
  const containerId = 'ftsMap'

  useEffect(() => {
    if (typeof window === 'undefined') return

    // Runtime require to avoid SSR breakage
    const am4core = require('@amcharts/amcharts4/core')
    const am4maps = require('@amcharts/amcharts4/maps')

    // Resolve geodata per country; try official first, fallback to local if you ship one
    let geodata: any
    try {
      geodata = country === 'KR'
        ? require('@amcharts/amcharts4-geodata/southKoreaLow').default
        : require('@amcharts/amcharts4-geodata/usaLow').default
    } catch (e) {
      // Optional local fallback (put your file at src/geodata/southKoreaLow.js exporting default)
      if (country === 'KR') geodata = require('@/geodata/southKoreaLow').default
    }

    const chart = am4core.create(containerId, am4maps.MapChart)
    chart.geodata = geodata
    chart.projection = new am4maps.projections.Miller()
    chart.chartContainer.wheelable = false
    chart.series.clear()

    const series = chart.series.push(new am4maps.MapPolygonSeries())
    series.useGeodata = true

    const template = series.mapPolygons.template
    template.tooltipText = '{name}'
    template.fill = am4core.color('#f4effc')
    template.stroke = am4core.color('#d9d6e5')
    template.togglable = true

    const hover = template.states.create('hover')
    hover.properties.fill = am4core.color('#cbb5ff')

    const active = template.states.create('active')
    active.properties.fill = am4core.color('#8b5cf6')

    // On click, toggle active and emit region name
    template.events.on('hit', (ev: any) => {
      const polygon = ev.target
      // toggle active (exclusive select)
      series.mapPolygons.each((p: any) => (p.isActive = false))
      polygon.isActive = true
      const name = (polygon.dataItem?.dataContext as any)?.name ?? null
      onRegionSelect?.(name)
    })

    // Preselect highlight region if provided
    if (highlightRegionName) {
      setTimeout(() => {
        try {
          series.mapPolygons.each((p: any) => {
            const n = (p.dataItem?.dataContext as any)?.name
            if (n && n.toLowerCase() === highlightRegionName.toLowerCase()) {
              p.isActive = true
            }
          })
        } catch {}
      }, 0)
    }

    chartRef.current = chart
    return () => {
      try { chart.dispose() } catch {}
      chartRef.current = null
    }
  }, [country, highlightRegionName])

  return (
    <div className="w-full">
      <div id={containerId} style={{ width: '100%', height: typeof height === 'number' ? `${height}px` : height }} />
    </div>
  )
}

// ---------------------------
// UI Components
// ---------------------------

type CountryToggleProps = {
  value: Country
  onChange: (c: Country) => void
}

function CountryToggle({ value, onChange }: CountryToggleProps) {
  return (
    <div className="inline-flex rounded-2xl border bg-white shadow-sm overflow-hidden">
      {([['US', 'United States'], ['KR', '대한민국']] as const).map(([code, label]) => {
        const active = value === code
        return (
          <button
            key={code}
            type="button"
            className={cx(
              'px-4 py-2 text-sm font-medium transition',
              active ? 'bg-violet-600 text-white' : 'hover:bg-violet-50 text-gray-700'
            )}
            onClick={() => onChange(code as Country)}
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}

type SearchBoxProps = {
  value: string
  onChange: (v: string) => void
  placeholder?: string
}

function SearchBox({ value, onChange, placeholder = '공장명 / 관리자 / 전화번호 검색' }: SearchBoxProps) {
  return (
    <div className="relative w-full">
      <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
      <input
        className="w-full rounded-full border border-gray-200 bg-white pl-10 pr-10 py-2 text-sm shadow-sm focus:border-violet-400 focus:outline-none"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange('')}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full p-1 hover:bg-gray-100"
          aria-label="clear"
        >
          <X className="h-4 w-4 text-gray-400" />
        </button>
      )}
    </div>
  )
}

type FactoryPillsProps = {
  factories: Factory[]
  selectedFactoryId: string | null
  onSelect: (id: string | null) => void
}

function FactoryPills({ factories, selectedFactoryId, onSelect }: FactoryPillsProps) {
  const sorted = useMemo(() => factories.slice().sort((a, b) => a.name.localeCompare(b.name)), [factories])
  const uniqueById = sorted // already unique
  return (
    <div className="flex flex-wrap gap-2">
      <button
        type="button"
        className={cx(
          'px-3 py-1.5 rounded-full border text-xs font-medium',
          !selectedFactoryId ? 'bg-violet-600 border-violet-600 text-white' : 'hover:bg-gray-50 border-gray-200'
        )}
        onClick={() => onSelect(null)}
      >
        전체
      </button>
      {uniqueById.map((f) => (
        <button
          key={f.id}
          type="button"
          className={cx(
            'px-3 py-1.5 rounded-full border text-xs font-medium transition',
            selectedFactoryId === f.id ? 'bg-violet-600 border-violet-600 text-white' : 'hover:bg-gray-50 border-gray-200'
          )}
          onClick={() => onSelect(f.id)}
          title={f.name}
        >
          {f.name}
        </button>
      ))}
    </div>
  )
}

function DirectoryList({ items }: { items: Factory[] }) {
  if (!items.length) {
    return (
      <div className="text-sm text-gray-500 py-8 text-center">검색 결과가 없습니다.</div>
    )
  }
  return (
    <div className="overflow-hidden rounded-2xl border border-gray-100 shadow-sm">
      <div className="grid grid-cols-12 bg-gray-50 px-4 py-2 text-xs font-semibold text-gray-600">
        <div className="col-span-4">공장명</div>
        <div className="col-span-4">관리자</div>
        <div className="col-span-4">전화</div>
      </div>
      <div className="divide-y divide-gray-100">
        {items.map((f) => (
          <div key={f.id} className="grid grid-cols-12 items-center px-4 py-3 text-sm">
            <div className="col-span-4 truncate" title={`${f.name} · ${f.regionName}`}>
              <div className="font-medium text-gray-900">{f.name}</div>
              <div className="text-xs text-gray-500">{f.regionName}</div>
            </div>
            <div className="col-span-4">
              <div className="font-medium text-gray-900">{f.manager}</div>
              <div className="text-xs text-gray-500">{f.country === 'KR' ? '대한민국' : 'United States'}</div>
            </div>
            <div className="col-span-4">
              <a href={`tel:${f.phone}`} className="inline-flex items-center gap-2 rounded-lg border border-gray-200 px-2.5 py-1.5 text-sm hover:bg-gray-50">
                <PhoneCall className="h-4 w-4" />
                <span className="font-medium">{f.phone}</span>
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ---------------------------
// Main Page
// ---------------------------

export default function FTSPage() {
  const [country, setCountry] = useState<Country>('KR')
  const [search, setSearch] = useState('')
  const [selectedFactoryId, setSelectedFactoryId] = useState<string | null>(null)
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null)

  // Factories filtered by country first
  const countryFactories = useMemo(() => FACTORIES.filter((f) => f.country === country), [country])

  // Pills source (country‑scoped)
  const pillsFactories = countryFactories

  // Apply region filter when selected
  const regionFiltered = useMemo(() => {
    if (!selectedRegion) return countryFactories
    return countryFactories.filter((f) => f.regionName.toLowerCase() === selectedRegion.toLowerCase())
  }, [countryFactories, selectedRegion])

  // Apply factory pill (specific factory)
  const factoryScoped = useMemo(() => {
    if (!selectedFactoryId) return regionFiltered
    return regionFiltered.filter((f) => f.id === selectedFactoryId)
  }, [regionFiltered, selectedFactoryId])

  // Apply free‑text search across name / manager / phone
  const finalList = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return factoryScoped
    return factoryScoped.filter((f) =>
      f.name.toLowerCase().includes(q) ||
      f.manager.toLowerCase().includes(q) ||
      f.phone.toLowerCase().includes(q)
    )
  }, [factoryScoped, search])

  // Reset state when country changes
  useEffect(() => {
    setSelectedRegion(null)
    setSelectedFactoryId(null)
    setSearch('')
  }, [country])

  return (
    <main className="mx-auto max-w-7xl p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100">
            <Phone className="h-5 w-5 text-violet-700" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">FTS (Follow‑the‑Sun) Call Desk</h1>
            <p className="text-sm text-gray-500">지역별 공장 책임자 즉시 연락</p>
          </div>
        </div>
        <CountryToggle value={country} onChange={setCountry} />
      </div>

      {/* Controls */}
      <div className="mb-5 grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-7">
          <SearchBox value={search} onChange={setSearch} placeholder="공장명 / 관리자 / 전화번호 검색" />
        </div>
        <div className="col-span-12 lg:col-span-5">
          <div className="rounded-2xl border border-gray-100 p-3 shadow-sm">
            <div className="mb-2 text-xs font-semibold text-gray-600">공장 바로가기</div>
            <FactoryPills factories={pillsFactories} selectedFactoryId={selectedFactoryId} onSelect={setSelectedFactoryId} />
          </div>
        </div>
      </div>

      {/* Content: Map (left) + Directory (right) */}
      <div className="grid grid-cols-12 gap-6">
        {/* Left: Map */}
        <section className="col-span-12 lg:col-span-6">
          <div className="rounded-2xl border border-gray-100 p-3 shadow-sm">
            <div className="mb-2 flex items-center justify-between">
              <div className="text-sm font-semibold text-gray-700">지도</div>
              <div className="text-xs text-gray-500">
                {selectedRegion ? (
                  <span>선택 지역: <span className="font-medium text-violet-700">{selectedRegion}</span></span>
                ) : (
                  <span>지역을 클릭해 필터링</span>
                )}
              </div>
            </div>
            <MapRegionPicker
              country={country}
              height={440}
              highlightRegionName={selectedRegion}
              onRegionSelect={(r) => setSelectedRegion(r)}
            />
            {selectedRegion && (
              <div className="mt-3 text-right">
                <button
                  type="button"
                  onClick={() => setSelectedRegion(null)}
                  className="text-xs text-gray-500 hover:text-gray-700 underline"
                >
                  지역 선택 해제
                </button>
              </div>
            )}
          </div>
        </section>

        {/* Right: Directory */}
        <section className="col-span-12 lg:col-span-6">
          <div className="mb-2 flex items-baseline justify-between">
            <h2 className="text-sm font-semibold text-gray-700">
              {selectedRegion ? `${selectedRegion} 지역 연락처` : (country === 'KR' ? '대한민국 전체 연락처' : 'United States — All contacts')}
            </h2>
            <div className="text-xs text-gray-500">총 {finalList.length}건</div>
          </div>
          <DirectoryList items={finalList} />
        </section>
      </div>
    </main>
  )
}
