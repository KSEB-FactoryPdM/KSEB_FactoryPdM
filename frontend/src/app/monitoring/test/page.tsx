'use client'

import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Legend,
  ResponsiveContainer,
} from '@/lib/dynamicRecharts'
import { useState } from 'react'
import initialData from '../../../../public/mock-data.json'

type MyType = Array<{
  time: number
  total: number
  A: number
  AAAA: number
  PTR: number
  SOA: number
  SRV: number
  TXT: number
  zone1: number
  zone2: number
  zone3: number
  rul: number
  size50: number
  size90: number
  size99: number
}>

export default function MonitoringPage() {
  const [data] = useState<MyType>(initialData as MyType)

  const hasAnomaly = data?.[data.length - 1]?.total > 0

  return (
    <DashboardLayout>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* 1. Anomaly Count (total) */}
        <ChartCard title="Anomaly Count (total)" danger={hasAnomaly}>
          {data.length === 0 ? (
            <div className="h-[200px] flex items-center justify-center text-text-primary">
              No data
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={data}>
                <XAxis dataKey="time" tick={false} />
                <YAxis
                  domain={[0, 1.5]}
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  domain={[0, 1.5]}
                  tick={{ fill: 'rgb(var(--color-text-primary))' }}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="total"
                  stroke={hasAnomaly ? '#dc2626' : 'var(--color-accent)'}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* 2. Anomaly Count (by type) */}
        <ChartCard title="Anomaly Count (by type)">
          {data.length === 0 ? (
            <div className="h-[200px] flex items-center justify-center text-text-primary">
              No data
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={data}>
                <Legend />
                <Line
                  type="monotone"
                  dataKey="A"
                  stroke="rgb(var(--chart-a))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="AAAA"
                  stroke="var(--color-accent)"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="PTR"
                  stroke="rgb(var(--chart-ptr))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="SOA"
                  stroke="rgb(var(--chart-soa))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="SRV"
                  stroke="rgb(var(--chart-srv))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="TXT"
                  stroke="rgb(var(--chart-txt))"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* 3. Anomaly Count (by zone) */}
        <ChartCard title="Anomaly Count (by zone)">
          {data.length === 0 ? (
            <div className="h-[200px] flex items-center justify-center text-text-primary">
              No data
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={data}>
                <Legend />
                <Line
                  type="monotone"
                  dataKey="zone1"
                  stroke="rgb(var(--chart-zone))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="zone2"
                  stroke="rgb(var(--chart-zone))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="zone3"
                  stroke="rgb(var(--chart-zone))"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* 4. Prediction (Remaining Useful Life) */}
        <ChartCard title="Prediction (Remaining Useful Life)">
          {data.length === 0 ? (
            <div className="h-[200px] flex items-center justify-center text-text-primary">
              No data
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={data}>
                <Line
                  type="monotone"
                  dataKey="rul"
                  stroke="rgb(var(--chart-ptr))"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* 5. Sensor Data (size, temperature) */}
        <ChartCard title="Sensor Data (size, temperature)">
          {data.length === 0 ? (
            <div className="h-[200px] flex items-center justify-center text-text-primary">
              No data
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={data}>
                <Line
                  type="monotone"
                  dataKey="size50"
                  stroke="rgb(var(--chart-a))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="size90"
                  stroke="rgb(var(--chart-zone))"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="size99"
                  stroke="var(--color-accent)"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        {/* 6. Real-Time Signal */}

        <ChartCard title="Real-Time Signal" danger={hasAnomaly}>
          {data.length === 0 ? (
            <div className="h-[200px] flex items-center justify-center text-text-primary">
              No data
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={data}>
                <Line
                  type="monotone"
                  dataKey="size50"
                  stroke={hasAnomaly ? '#dc2626' : 'rgb(var(--chart-a))'}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>
    </DashboardLayout>
  )
}
