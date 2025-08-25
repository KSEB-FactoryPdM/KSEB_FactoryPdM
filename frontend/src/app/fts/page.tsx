'use client';

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

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Phone, PhoneCall, Search as SearchIcon, X } from 'lucide-react'
import DashboardLayout from '@/components/DashboardLayout'
import { useTranslation } from 'react-i18next'

// ---------------------------
// Types & Mock Data
// ---------------------------

type Country = 'KR' | 'US'

interface Factory {
  id: string
  /** Factory name translations */
  name: { en: string; ko: string }
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
  {
    id: 'kr-ss-01',
    name: { en: 'Shinsegae Seongsu Plant', ko: '신세계 성수 공장' },
    country: 'KR',
    regionName: 'Seoul',
    manager: '김미정',
    phone: '+82-2-1234-5678',
  },
  {
    id: 'kr-cn-01',
    name: { en: 'Shinsegae Cheonan Plant', ko: '신세계 천안 공장' },
    country: 'KR',
    regionName: 'Chungcheongnam-do',
    manager: '이도현',
    phone: '+82-41-555-0101',
  },
  {
    id: 'kr-es-01',
    name: { en: 'Shinsegae Eumseong Plant', ko: '신세계 음성 공장' },
    country: 'KR',
    regionName: 'Chungcheongbuk-do',
    manager: '박지훈',
    phone: '+82-43-555-0101',
  },
  {
    id: 'kr-gg-01',
    name: { en: 'Gyeonggi Factory', ko: '경기 공장' },
    country: 'KR',
    regionName: 'Gyeonggi-do',
    manager: '박지훈',
    phone: '+82-31-777-0909',
  },
  {
    id: 'kr-gg-02',
    name: { en: 'Sungkyunkwan Factory', ko: '성균관 공장' },
    country: 'KR',
    regionName: 'Gyeonggi-do',
    manager: '정민수',
    phone: '+82-31-888-0000',
  },
  {
    id: 'kr-in-01',
    name: { en: 'Inha Factory', ko: '인하 공장' },
    country: 'KR',
    regionName: 'Incheon',
    manager: '최영희',
    phone: '+82-32-222-3333',
  },

  // USA examples
  {
    id: 'us-or-01',
    name: { en: 'Shinsegae Foods', ko: 'Shinsegae Foods' },
    country: 'US',
    regionName: 'Oregon',
    manager: 'Olivia Brown',
    phone: '+1-503-555-0100',
  },
  {
    id: 'us-ca-02',
    name: { en: 'Better Foods Inc.', ko: 'Better Foods Inc.' },
    country: 'US',
    regionName: 'California',
    manager: 'Mason Lee',
    phone: '+1-408-555-0199',
  },
  {
    id: 'us-ca-01',
    name: { en: 'California Fab', ko: 'California Fab' },
    country: 'US',
    regionName: 'California',
    manager: 'Ava Johnson',
    phone: '+1-415-555-0139',
  },
  {
    id: 'us-tx-01',
    name: { en: 'Texas Assembly', ko: 'Texas Assembly' },
    country: 'US',
    regionName: 'Texas',
    manager: 'Noah Davis',
    phone: '+1-512-555-0110',
  },
  {
    id: 'us-ny-01',
    name: { en: 'New York Hub', ko: 'New York Hub' },
    country: 'US',
    regionName: 'New York',
    manager: 'Liam Miller',
    phone: '+1-212-555-0188',
  },
]

const REGION_LABELS: Record<string, { en: string; ko: string }> = {
  'Seoul': { en: 'Seoul', ko: '서울특별시' },
  'Busan': { en: 'Busan', ko: '부산광역시' },
  'Daegu': { en: 'Daegu', ko: '대구광역시' },
  'Gwangju': { en: 'Gwangju', ko: '광주광역시' },
  'Daejeon': { en: 'Daejeon', ko: '대전광역시' },
  'Ulsan': { en: 'Ulsan', ko: '울산광역시' },
  'Incheon': { en: 'Incheon', ko: '인천광역시' },
  'Gyeonggi-do': { en: 'Gyeonggi-do', ko: '경기도' },
  'Gyeonggi': { en: 'Gyeonggi-do', ko: '경기도' },
  'Gangwon-do': { en: 'Gangwon-do', ko: '강원도' },
  'Chungcheongnam-do': { en: 'Chungcheongnam-do', ko: '충청남도' },
  'Chungcheongbuk-do': { en: 'Chungcheongbuk-do', ko: '충청북도' },
  'Jeollanam-do': { en: 'Jeollanam-do', ko: '전라남도' },
  'Jeollabuk-do': { en: 'Jeollabuk-do', ko: '전라북도' },
  'Gyeongsangnam-do': { en: 'Gyeongsangnam-do', ko: '경상남도' },
  'Gyeongsangbuk-do': { en: 'Gyeongsangbuk-do', ko: '경상북도' },
  'Jeju-do': { en: 'Jeju-do', ko: '제주도' },
  'California': { en: 'California', ko: '캘리포니아' },
  'Oregon': { en: 'Oregon', ko: '오리건' },
  'Texas': { en: 'Texas', ko: '텍사스' },
  'New York': { en: 'New York', ko: '뉴욕' },
}

// ---------------------------
// Utility helpers
// ---------------------------

function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(' ')
}

// unique 유틸은 사용하지 않아 제거

function normalizeRegionName(name: string) {
  return name.replace(/[-\s]/g, '').replace(/do$/i, '').toLowerCase()
}

// ---------------------------
// MapRegionPicker (amCharts v4)
// ---------------------------

type MapRegionPickerProps = {
  country: Country
  height?: number | string
  highlightRegionName?: string | null
  onRegionSelect?: (regionName: string | null) => void
  getRegionLabel: (name: string) => string
}

function MapRegionPicker({ country, height = 420, highlightRegionName, onRegionSelect, getRegionLabel }: MapRegionPickerProps) {
  const chartRef = useRef<unknown>(null)
  const containerId = 'ftsMap'

  useEffect(() => {
    if (typeof window === 'undefined') return

    // 동적 import로 SSR 문제 회피
    let am4core: typeof import('@amcharts/amcharts4/core')
    let am4maps: typeof import('@amcharts/amcharts4/maps')
    let cleanup = () => {}

    const load = async () => {
      const core = await import('@amcharts/amcharts4/core')
      const maps = await import('@amcharts/amcharts4/maps')
      am4core = core
      am4maps = maps

      // 국가별 geodata 로드
      let geodata: unknown
      try {
        geodata = country === 'KR'
          ? (await import('@amcharts/amcharts4-geodata/southKoreaLow')).default
          : (await import('@amcharts/amcharts4-geodata/usaLow')).default
      } catch {
        if (country === 'KR') {
          try {
            geodata = (await import('@/geodata/southKoreaLow')).default
          } catch {}
        }
      }

      const chart = am4core.create(containerId, am4maps.MapChart)
      chart.geodata = geodata as object
      chart.projection = new am4maps.projections.Miller()
      chart.chartContainer.wheelable = false
      chart.series.clear()

      const series = chart.series.push(new am4maps.MapPolygonSeries())
      series.useGeodata = true

      const template = series.mapPolygons.template
      template.tooltipText = '{name}'
      template.adapter.add('tooltipText', (_: unknown, target: unknown) => {
        const dataCtx = (target as { dataItem?: { dataContext?: Record<string, unknown> } })?.dataItem?.dataContext
        const rawName = dataCtx?.['name']
        const name = typeof rawName === 'string' ? rawName : ''
        return name ? getRegionLabel(name) : ''
      })
      template.fill = am4core.color('#f4effc')
      template.stroke = am4core.color('#d9d6e5')
      template.togglable = true

      const hover = template.states.create('hover')
      hover.properties.fill = am4core.color('#cbb5ff')

      const active = template.states.create('active')
      active.properties.fill = am4core.color('#8b5cf6')

      // On click, toggle active and emit region name
      template.events.on('hit', (ev: unknown) => {
        const polygon = (ev as { target?: unknown }).target as { isActive?: boolean; dataItem?: { dataContext?: Record<string, unknown> } } | undefined
        series.mapPolygons.each((p: unknown) => {
          const poly = p as { isActive?: boolean }
          if (poly) poly.isActive = false
        })
        if (polygon) polygon.isActive = true
        const rawName = polygon?.dataItem?.dataContext?.['name']
        const name = typeof rawName === 'string' ? rawName : null
        onRegionSelect?.(name)
      })

      // Preselect highlight region if provided
      if (highlightRegionName) {
        setTimeout(() => {
          try {
            series.mapPolygons.each((p: unknown) => {
              const poly = p as { isActive?: boolean; dataItem?: { dataContext?: Record<string, unknown> } }
              const raw = poly?.dataItem?.dataContext?.['name']
              const n = typeof raw === 'string' ? raw : undefined
              if (n && n.toLowerCase() === highlightRegionName.toLowerCase()) {
                if (poly) poly.isActive = true
              }
            })
          } catch {}
        }, 0)
      }

      let dragStartY: number | null = null
      chart.chartContainer.background.events.on('down', (ev: unknown) => {
        const evt = ev as { event?: { shiftKey?: boolean }; pointer?: { point?: { y?: number } } }
        if (evt?.event?.shiftKey) {
          dragStartY = evt?.pointer?.point?.y ?? null
          chart.seriesContainer.draggable = false
        }
      })
      chart.chartContainer.background.events.on('up', (ev: unknown) => {
        const evt = ev as { event?: { shiftKey?: boolean }; pointer?: { point?: { y?: number } } }
        if (dragStartY !== null && evt?.event?.shiftKey) {
          const currentY = evt?.pointer?.point?.y
          if (typeof currentY === 'number') {
            const dy = dragStartY - currentY
            if (Math.abs(dy) > 5) {
              if (dy > 0) chart.zoomIn()
              else chart.zoomOut()
            }
          }
        }
        dragStartY = null
        chart.seriesContainer.draggable = true
      })

      chartRef.current = chart
      cleanup = () => {
        try { chart.dispose() } catch {}
        chartRef.current = null
      }
    }
    load()
    return () => cleanup()
  }, [country, highlightRegionName, getRegionLabel, onRegionSelect])

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
  const { t } = useTranslation('common')
  return (
    <div className="inline-flex rounded-2xl border bg-white shadow-sm overflow-hidden">
      {([['US', t('fts.usa')], ['KR', t('fts.korea')]] as const).map(([code, label]) => {
        const active = value === code
        return (
          <button
            key={code}
            type="button"
            className={cx(
              'px-4 py-2 text-sm font-medium transition',
              active ? 'bg-purple-600 text-white' : 'hover:bg-purple-600/10 text-gray-700'
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

function SearchBox({ value, onChange, placeholder }: SearchBoxProps) {
  const { t } = useTranslation('common')
  return (
    <div className="relative w-full">
      <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
      <input
        className="w-full rounded-full border border-gray-200 bg-white pl-10 pr-10 py-2 text-sm shadow-sm focus:border-purple-600 focus:outline-none"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange('')}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full p-1 hover:bg-gray-100"
          aria-label={t('fts.clear')}
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
  getFactoryName: (f: Factory) => string
}

function FactoryPills({ factories, selectedFactoryId, onSelect, getFactoryName }: FactoryPillsProps) {
  const { t } = useTranslation('common')
  const sorted = useMemo(() => factories.slice().sort((a, b) => getFactoryName(a).localeCompare(getFactoryName(b))), [factories, getFactoryName])
  const uniqueById = sorted // already unique
  return (
    <div className="flex flex-wrap gap-2">
      <button
        type="button"
        className={cx(
          'px-3 py-1.5 rounded-full border text-xs font-medium',
          !selectedFactoryId ? 'bg-purple-600 border-purple-600 text-white' : 'hover:bg-purple-600/10 border-gray-200'
        )}
        onClick={() => onSelect(null)}
      >
        {t('fts.all')}
      </button>
      {uniqueById.map((f) => (
        <button
          key={f.id}
          type="button"
          className={cx(
            'px-3 py-1.5 rounded-full border text-xs font-medium transition',
            selectedFactoryId === f.id ? 'bg-purple-600 border-purple-600 text-white' : 'hover:bg-purple-600/10 border-gray-200'
          )}
          onClick={() => onSelect(f.id)}
          title={getFactoryName(f)}
        >
          {getFactoryName(f)}
        </button>
      ))}
    </div>
  )
}

function DirectoryList({ items, getRegionLabel, getFactoryName }: { items: Factory[]; getRegionLabel: (name: string) => string; getFactoryName: (f: Factory) => string }) {
  const { t } = useTranslation('common')
  if (!items.length) {
    return (
      <div className="text-sm text-gray-500 py-8 text-center">{t('fts.noResults')}</div>
    )
  }
  return (
    <div className="overflow-hidden rounded-2xl border border-gray-100 shadow-sm">
      <div className="grid grid-cols-12 bg-gray-50 px-4 py-2 text-xs font-semibold text-gray-600">
        <div className="col-span-4">{t('fts.factoryName')}</div>
        <div className="col-span-4">{t('fts.manager')}</div>
        <div className="col-span-4">{t('fts.phone')}</div>
      </div>
      <div className="divide-y divide-gray-100">
        {items.map((f) => (
          <div key={f.id} className="grid grid-cols-12 items-center px-4 py-3 text-sm">
            <div className="col-span-4 truncate" title={`${getFactoryName(f)} · ${getRegionLabel(f.regionName)}`}>
              <div className="font-medium text-gray-900">{getFactoryName(f)}</div>
              <div className="text-xs text-gray-500">{getRegionLabel(f.regionName)}</div>
            </div>
            <div className="col-span-4">
              <div className="font-medium text-gray-900">{f.manager}</div>
              <div className="text-xs text-gray-500">{f.country === 'KR' ? t('fts.korea') : t('fts.usa')}</div>
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
  const { t, i18n } = useTranslation('common')
  const [country, setCountry] = useState<Country>('KR')
  const [search, setSearch] = useState('')
  const [selectedFactoryId, setSelectedFactoryId] = useState<string | null>(null)
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null)

  const getRegionLabel = useCallback((name: string) => {
    const langKey: 'en' | 'ko' = i18n.language?.startsWith('ko') ? 'ko' : 'en'
    const labels = REGION_LABELS[name]
    return labels ? labels[langKey] : name
  }, [i18n.language])
  const getFactoryName = useCallback((f: Factory) => {
    const langKey: 'en' | 'ko' = i18n.language?.startsWith('ko') ? 'ko' : 'en'
    return f.name[langKey] || f.name.en
  }, [i18n.language])

  // Factories filtered by country first
  const countryFactories = useMemo(() => FACTORIES.filter((f) => f.country === country), [country])

  // Pills source (country‑scoped)
  const pillsFactories = countryFactories

  // Apply region filter when selected
  const regionFiltered = useMemo(() => {
    if (!selectedRegion) return countryFactories
    return countryFactories.filter(
      (f) => normalizeRegionName(f.regionName) === normalizeRegionName(selectedRegion)
    )
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
      // match against both Korean and English names regardless of UI language
      Object.values(f.name)
        .map((n) => n.toLowerCase())
        .some((n) => n.includes(q)) ||
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
    <DashboardLayout>
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-600/10">
              <Phone className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold">{t('fts.title')}</h1>
              <p className="text-sm text-gray-500">{t('fts.subtitle')}</p>
            </div>
          </div>
          <CountryToggle value={country} onChange={setCountry} />
        </div>

        {/* Controls */}
        <div className="mb-5 grid grid-cols-12 gap-4">
          <div className="col-span-12 lg:col-span-6">
            <SearchBox value={search} onChange={setSearch} placeholder={t('fts.searchPlaceholder')} />
          </div>
          <div className="col-span-12 lg:col-span-6">
            <div className="rounded-2xl border border-gray-100 p-3 shadow-sm">
              <div className="mb-2 text-xs font-semibold text-gray-600">{t('fts.factoryShortcut')}</div>
              <FactoryPills
                factories={pillsFactories}
                selectedFactoryId={selectedFactoryId}
                onSelect={setSelectedFactoryId}
                getFactoryName={getFactoryName}
              />
            </div>
          </div>
        </div>

        {/* Content: Map (left) + Directory (right) */}
        <div className="grid grid-cols-12 gap-6">
          {/* Left: Map */}
          <section className="col-span-12 lg:col-span-6">
            <div className="rounded-2xl border border-gray-100 p-3 shadow-sm">
              <div className="mb-2 flex items-center justify-between">
                <div className="text-sm font-semibold text-gray-700">{t('fts.map')}</div>
                <div className="text-xs text-gray-500">
                  {selectedRegion ? (
                    <span>
                      {t('fts.selectedRegion', {
                        region: getRegionLabel(selectedRegion),
                      })}
                    </span>
                  ) : (
                    <span>{t('fts.clickRegion')}</span>
                  )}
                </div>
              </div>
              <MapRegionPicker
                country={country}
                height={440}
                highlightRegionName={selectedRegion}
                onRegionSelect={(r) => setSelectedRegion(r)}
                getRegionLabel={getRegionLabel}
              />
              {selectedRegion && (
                <div className="mt-3 text-right">
                  <button
                    type="button"
                    onClick={() => setSelectedRegion(null)}
                    className="text-xs text-gray-500 hover:text-gray-700 underline"
                  >
                    {t('fts.clearRegion')}
                  </button>
                </div>
              )}
            </div>
          </section>

          {/* Right: Directory */}
          <section className="col-span-12 lg:col-span-6">
            <div className="mb-2 flex items-baseline justify-between">
              <h2 className="text-sm font-semibold text-gray-700">
                {selectedRegion
                  ? t('fts.regionContacts', { region: getRegionLabel(selectedRegion) })
                  : t('fts.allContacts', { country: country === 'KR' ? t('fts.korea') : t('fts.usa') })}
              </h2>
              <div className="text-xs text-gray-500">{t('fts.total', { count: finalList.length })}</div>
            </div>
            <DirectoryList items={finalList} getRegionLabel={getRegionLabel} getFactoryName={getFactoryName} />
          </section>
        </div>
      </div>
    </DashboardLayout>
  )
}
