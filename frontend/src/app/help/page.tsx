'use client'

/**
 * Help Center — Next.js App Router (UI/UX refresh)
 *
 * Goals
 *  - Keep existing behavior intact; only improve structure & visuals.
 *  - Self‑contained page using your existing UI primitives (Button/Card/Input/Label).
 *  - Searchable FAQ, Quick Actions, System Status, FTS Support Hours, Troubleshooting, Ticket.
 *
 * Where to save
 *  - app/help/page.tsx
 *
 * Optional sidebar link
 *  - <Link href="/help" className="nav-item"> <LifeBuoy className="h-4 w-4"/> <span>Help</span> </Link>
 */

import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import DashboardLayout from '@/components/DashboardLayout'

// UI primitives already in your repo
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import Link from 'next/link'

// Icons (lucide-react already installed)
import {
  LifeBuoy,
  Search as SearchIcon,
  BookOpen,
  Phone,
  MessageCircle,
  Mail,
  FileDown,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Clock,
  Globe
} from 'lucide-react'

// ---------------------------
// Helpers
// ---------------------------

function cx(...c: Array<string | false | null | undefined>) { return c.filter(Boolean).join(' ') }

type Status = 'operational' | 'degraded' | 'down' | 'unknown'

function Badge({ status }: { status: Status }) {
  const map: Record<Status, string> = {
    operational: 'bg-green-100 text-green-700 border-green-200',
    degraded: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    down: 'bg-red-100 text-red-700 border-red-200',
    unknown: 'bg-gray-100 text-gray-700 border-gray-200'
  }
  const label: Record<Status, string> = {
    operational: 'Operational',
    degraded: 'Degraded',
    down: 'Down',
    unknown: 'Unknown'
  }
  return <span className={cx('inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium', map[status])}>{label[status]}</span>
}

// naive time window checker (9:00-18:00 local)
function isOpenNow(timeZone: string, openHour = 9, closeHour = 18) {
  const fmt = new Intl.DateTimeFormat('en-US', { hour: 'numeric', hour12: false, timeZone })
  const hour = Number(fmt.format(new Date()))
  return hour >= openHour && hour < closeHour
}

function nowInTZ(timeZone: string) {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
    hour12: false, timeZone
  }).format(new Date())
}

// ---------------------------
// Data
// ---------------------------

type FAQ = { id: string; q: string; a: string }
const FAQS: FAQ[] = [
  { id: 'ws', q: '실시간 모니터링이 연결되지 않아요.', a: '브라우저 콘솔에서 WebSocket URL을 확인하세요. Monitoring 페이지는 localStorage의 socketUrl → NEXT_PUBLIC_WEBSOCKET_URL → ws://localhost:8080 순으로 연결을 시도합니다. 방화벽/프록시가 WS를 차단하지 않는지도 점검하세요.' },
  { id: 'account', q: '계정을 복구하려면?', a: '로그인 화면의 “비밀번호 재설정”을 사용해 이메일을 인증하세요. 2FA를 켰다면 백업 코드를 사용해야 합니다. 백업 코드가 없다면 조직 관리자에게 재발급을 요청하세요.' },
  { id: 'ingest', q: '유니티 가상공장 데이터가 안 들어옵니다.', a: 'Unity → MQTT → Kafka → Backend(FastAPI) → DB(TimescaleDB) 순서의 파이프라인 중 어디에서 끊겼는지 확인하세요. MQTT 토픽/브로커 주소, 인증 정보, 그리고 API Ingest 엔드포인트 상태를 점검하세요.' },
  { id: 'threshold', q: 'AutoEncoder 임계값은 어떻게 정하나요?', a: '정상 데이터의 재구성 오차 분포를 기반으로 사분위/백분위(예: 99.9%)로 설정합니다. 프로젝트 기본값이 과도하면 장비별 Fine-tuning으로 조정하세요.' },
  { id: 'exports', q: '로그/리포트를 내보내려면?', a: '우측 상단 “로그 다운로드” 버튼을 사용하거나 /api/logs.zip 엔드포인트를 호출하세요. 권한 정책상 일부 항목은 관리자만 접근 가능합니다.' }
]

// ---------------------------
// Components
// ---------------------------

function SystemStatusCard() {
  const [api, setApi] = useState<Status>('unknown')
  const [ingest, setIngest] = useState<Status>('unknown')
  const [dashboard, setDashboard] = useState<Status>('unknown')
  const [ts, setTs] = useState<string>('')

  async function refresh() {
    setTs(new Date().toLocaleString())
    try {
      // Optional health checks — safe fallbacks if endpoints are missing
      const tryFetch = async (path: string): Promise<Status> => {
        try {
          const r = await fetch(path, { method: 'GET' })
          if (r.ok) return 'operational'
          return r.status >= 500 ? 'down' : 'degraded'
        } catch { return 'unknown' }
      }
      const [a, i, d] = await Promise.all([
        tryFetch('/api/health'),
        tryFetch('/api/ingest/health'),
        tryFetch('/api/dashboard/health')
      ])
      setApi(a); setIngest(i); setDashboard(d)
    } catch {
      setApi('unknown'); setIngest('unknown'); setDashboard('unknown')
    }
  }

  useEffect(() => { refresh() }, [])

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2"><AlertCircle className="h-5 w-5"/> 시스템 상태</CardTitle>
        <Button onClick={refresh} type="button" className="text-sm">새로고침</Button>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="rounded-lg border p-3">
            <div className="text-xs text-gray-500">API</div>
            <div className="mt-1 flex items-center gap-2"><Badge status={api}/></div>
          </div>
          <div className="rounded-lg border p-3">
            <div className="text-xs text-gray-500">데이터 수집(ingest)</div>
            <div className="mt-1 flex items-center gap-2"><Badge status={ingest}/></div>
          </div>
          <div className="rounded-lg border p-3">
            <div className="text-xs text-gray-500">대시보드</div>
            <div className="mt-1 flex items-center gap-2"><Badge status={dashboard}/></div>
          </div>
        </div>
        {ts && <div className="mt-3 text-xs text-gray-500">업데이트: {ts}</div>}
        <div className="mt-3 text-xs">
          <Link href="/status" className="inline-flex items-center gap-1 text-primary hover:underline">
            자세히 보기 <ExternalLink className="h-3.5 w-3.5"/>
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}

function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2"><LifeBuoy className="h-5 w-5"/> 빠른 작업</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Link href="/fts" className="rounded-xl border p-3 hover:bg-gray-50 flex items-center justify-center gap-2">
            <Phone className="h-4 w-4"/> Call
          </Link>
          <Link href={process.env.NEXT_PUBLIC_HELP_CHAT_URL || '#'} className="rounded-xl border p-3 hover:bg-gray-50 flex items-center justify-center gap-2">
            <MessageCircle className="h-4 w-4"/> Chat
          </Link>
          <a href={`mailto:${process.env.NEXT_PUBLIC_HELP_EMAIL || 'support@example.com'}`} className="rounded-xl border p-3 hover:bg-gray-50 flex items-center justify-center gap-2">
            <Mail className="h-4 w-4"/> Email
          </a>
          <Link href={process.env.NEXT_PUBLIC_DOCS_URL || '#'} className="rounded-xl border p-3 hover:bg-gray-50 flex items-center justify-center gap-2">
            <BookOpen className="h-4 w-4"/> Docs
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}

function FTSSupportHours() {
  const [, setTick] = useState(0)
  useEffect(() => { const id = setInterval(() => setTick((v) => v + 1), 60 * 1000); return () => clearInterval(id) }, [])
  const openKR = isOpenNow('Asia/Seoul')
  const openUS = isOpenNow('America/Los_Angeles')
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2"><Globe className="h-5 w-5"/> Follow‑the‑Sun 지원</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="rounded-lg border p-3">
            <div className="flex items-center justify-between">
              <div className="font-medium">대한민국</div>
              <Badge status={openKR ? 'operational' : 'degraded'} />
            </div>
            <div className="mt-1 text-sm text-gray-600 flex items-center gap-2"><Clock className="h-4 w-4"/> 09:00–18:00 KST</div>
            <div className="mt-1 text-xs text-gray-500">현재: {nowInTZ('Asia/Seoul')}</div>
          </div>
          <div className="rounded-lg border p-3">
            <div className="flex items-center justify-between">
              <div className="font-medium">United States (Pacific)</div>
              <Badge status={openUS ? 'operational' : 'degraded'} />
            </div>
            <div className="mt-1 text-sm text-gray-600 flex items-center gap-2"><Clock className="h-4 w-4"/> 09:00–18:00 PT</div>
            <div className="mt-1 text-xs text-gray-500">Now: {nowInTZ('America/Los_Angeles')}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function FAQItem({ item }: { item: FAQ }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="rounded-xl border border-gray-200">
      <button type="button" onClick={() => setOpen((v) => !v)} className="w-full flex items-center justify-between px-4 py-3">
        <div className="text-left font-medium">{item.q}</div>
        {open ? <ChevronUp className="h-4 w-4"/> : <ChevronDown className="h-4 w-4"/>}
      </button>
      {open && (
        <div className="px-4 pb-4 text-sm text-gray-700">
          {item.a}
        </div>
      )}
    </div>
  )
}

function FAQSection() {
  const [query, setQuery] = useState('')
  const list = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return FAQS
    return FAQS.filter(f => f.q.toLowerCase().includes(q) || f.a.toLowerCase().includes(q))
  }, [query])

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2"><BookOpen className="h-5 w-5"/> FAQ</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-3 relative">
          <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400"/>
          <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="검색: 예) WebSocket, 계정, 임계값" className="pl-9"/>
        </div>
        <div className="space-y-2">
          {list.length ? list.map((f) => <FAQItem key={f.id} item={f}/>) : (
            <div className="text-sm text-gray-500 py-8 text-center">검색 결과가 없습니다.</div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function Troubleshoot() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2"><CheckCircle2 className="h-5 w-5"/> 문제 해결 가이드</CardTitle>
      </CardHeader>
      <CardContent>
        <ol className="space-y-3 list-decimal pl-5">
          <li>
            <div className="font-medium">네트워크 상태 확인</div>
            <div className="text-sm text-gray-600">사내 프록시/방화벽에서 MQTT(1883/8883), WS(80/443)가 허용되는지 확인하세요.</div>
          </li>
          <li>
            <div className="font-medium">환경 변수 점검</div>
            <div className="text-sm text-gray-600">NEXT_PUBLIC_WEBSOCKET_URL, NEXT_PUBLIC_API_BASE, MQTT 브로커/토픽 값을 확인하세요.</div>
          </li>
          <li>
            <div className="font-medium">로그 수집</div>
            <div className="text-sm text-gray-600">오류가 재현된 직후 아래 “로그 다운로드”로 파일을 확보해 주세요.</div>
          </li>
          <li>
            <div className="font-medium">문의 등록</div>
            <div className="text-sm text-gray-600">가능하면 스크린샷/영상과 함께 문제 발생 시간대(KST/PT)를 포함하세요.</div>
          </li>
        </ol>
        <div className="mt-4 flex flex-wrap gap-2">
          <Button asChild variant="outline" className="bg-white border border-gray-200 text-gray-700 hover:bg-gray-50">
            <a href="/api/logs.zip" download>
              <FileDown className="h-4 w-4 mr-2"/> 로그 다운로드
            </a>
          </Button>
          <Button asChild>
            <a href={`mailto:${process.env.NEXT_PUBLIC_HELP_EMAIL || 'support@example.com'}`}>문의 메일 보내기</a>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default function HelpPage() {
  const { t } = useTranslation('common')

  return (
    <DashboardLayout>
      <div className="mx-auto max-w-7xl p-6">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
              <LifeBuoy className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold">{t('help.title', { defaultValue: 'Help Center' })}</h1>
              <p className="text-sm text-gray-500">{t('help.subtitle', { defaultValue: '문서를 검색하고, 상태를 확인하고, 24h FTS 지원을 이용하세요.' })}</p>
            </div>
          </div>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-12 gap-6">
          <section className="col-span-12 lg:col-span-8 space-y-6">
            <QuickActions/>
            <SystemStatusCard/>
            <FAQSection/>
            <Troubleshoot/>
          </section>

          <aside className="col-span-12 lg:col-span-4 space-y-6">
            <FTSSupportHours/>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><BookOpen className="h-5 w-5"/> 빠른 링크</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="list-disc pl-5 space-y-2 text-sm">
                    <li><Link href={process.env.NEXT_PUBLIC_DOCS_URL || '#'} className="text-primary hover:underline">제품 문서</Link></li>
                    <li><Link href="/fts" className="text-primary hover:underline">FTS 연락처</Link></li>
                    <li><Link href="/settings" className="text-primary hover:underline">설정</Link></li>
                </ul>
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>
    </DashboardLayout>
  )
}

