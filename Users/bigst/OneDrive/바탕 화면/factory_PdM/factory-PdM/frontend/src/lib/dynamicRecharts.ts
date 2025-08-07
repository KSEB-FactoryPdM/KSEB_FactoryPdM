// 클라이언트 전용 차트 컴포넌트를 동적 로딩
'use client'

import dynamic from 'next/dynamic'

// Recharts 컴포넌트들을 SSR 없이 로드
export const LineChart = dynamic(() => import('recharts').then(m => m.LineChart), { ssr: false })
export const Line = dynamic(() => import('recharts').then(m => m.Line), { ssr: false })
export const XAxis = dynamic(() => import('recharts').then(m => m.XAxis), { ssr: false })
export const YAxis = dynamic(() => import('recharts').then(m => m.YAxis), { ssr: false })
export const Tooltip = dynamic(() => import('recharts').then(m => m.Tooltip), { ssr: false })
export const Legend = dynamic(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  () => import('recharts').then((m) => m.Legend as any),
  { ssr: false }
)
export const ResponsiveContainer = dynamic(() => import('recharts').then(m => m.ResponsiveContainer), { ssr: false })
export const BarChart = dynamic(() => import('recharts').then(m => m.BarChart), { ssr: false })
export const Bar = dynamic(() => import('recharts').then(m => m.Bar), { ssr: false })
export const AreaChart = dynamic(() => import('recharts').then(m => m.AreaChart), { ssr: false })
export const Area = dynamic(() => import('recharts').then(m => m.Area), { ssr: false })
export const ScatterChart = dynamic(() => import('recharts').then(m => m.ScatterChart), { ssr: false })
export const Scatter = dynamic(() => import('recharts').then(m => m.Scatter), { ssr: false })
export const ZAxis = dynamic(() => import('recharts').then(m => m.ZAxis), { ssr: false })
export const CartesianGrid = dynamic(() => import('recharts').then(m => m.CartesianGrid), { ssr: false })
