'use client'

import DashboardLayout from '@/components/DashboardLayout'
import ChartCard from '@/components/ChartCard'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  ScatterChart,
  Scatter,
  ZAxis,
  CartesianGrid,
} from '@/lib/dynamicRecharts'
import { summaryReports, distributionData, heatmapData } from '@/mockData'
import { useRequireRole } from '@/hooks/useRequireRole'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { useState } from 'react'
import jsPDF from 'jspdf'
import * as XLSX from 'xlsx'

export default function ReportsPage() {
  useRequireRole(['Admin', 'Viewer'])
  const [email, setEmail] = useState('')
  const [sendDate, setSendDate] = useState('')

  const handleExportPDF = () => {
    const doc = new jsPDF()
    doc.text('Summary Report', 10, 10)
    summaryReports.forEach((item, idx) => {
      doc.text(`${item.label}: ${item.value}`, 10, 20 + idx * 10)
    })
    doc.save('report.pdf')
  }

  const handleExportExcel = () => {
    const ws = XLSX.utils.json_to_sheet(summaryReports)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Report')
    XLSX.writeFile(wb, 'report.xlsx')
  }

  const handleScheduleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log('Schedule email', email, sendDate)
    setEmail('')
    setSendDate('')
  }
  return (
    <DashboardLayout>
      <ChartCard title="Summary Report">
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={summaryReports}>
            <XAxis
              dataKey="label"
              tick={{ fill: 'rgb(var(--color-text-primary))' }}
            />
            <YAxis tick={{ fill: 'rgb(var(--color-text-primary))' }} />
            <Tooltip />
            <Bar dataKey="value" fill="rgb(var(--color-accent))" />
          </BarChart>
        </ResponsiveContainer>
        <div className="flex gap-2 mt-2">
          <Button onClick={handleExportPDF}>Export PDF</Button>
          <Button onClick={handleExportExcel}>Export Excel</Button>
        </div>
      </ChartCard>

      <ChartCard title="Distribution Chart">
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={distributionData}>
            <XAxis dataKey="bin" tick={{ fill: 'rgb(var(--color-text-primary))' }} />
            <YAxis tick={{ fill: 'rgb(var(--color-text-primary))' }} />
            <Tooltip />
            <Area type="monotone" dataKey="count" fill="rgb(var(--color-accent))" />
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Heatmap">
        <ResponsiveContainer width="100%" height={200}>
          <ScatterChart>
            <CartesianGrid />
            <XAxis dataKey="x" tick={{ fill: 'rgb(var(--color-text-primary))' }} />
            <YAxis dataKey="y" tick={{ fill: 'rgb(var(--color-text-primary))' }} />
            <ZAxis dataKey="value" range={[0, 10]} />
            <Tooltip />
            <Scatter data={heatmapData} fill="rgb(var(--color-accent))" />
          </ScatterChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Schedule Report Email">
        <form onSubmit={handleScheduleSubmit} className="space-y-2">
          <div>
            <Input
              type="email"
              placeholder="email@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <Input
              type="date"
              value={sendDate}
              onChange={(e) => setSendDate(e.target.value)}
              required
            />
          </div>
          <Button type="submit">Schedule</Button>
        </form>
      </ChartCard>
    </DashboardLayout>
  )
}
