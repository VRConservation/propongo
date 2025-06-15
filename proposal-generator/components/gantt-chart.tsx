"use client"

import { useState, useEffect } from "react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts"
import { ChartContainer } from "@/components/ui/chart"
import { addDays, format, parseISO, differenceInDays } from "date-fns"

// --- Add types for better safety ---
type DeliverableDate = {
  startDate?: string
  endDate?: string
}

type ProposalData = {
  scope?: {
    deliverables?: string[]
    deliverableDates?: DeliverableDate[]
  }
}

type ChartDataItem = {
  name: string
  start: Date
  end: Date
  duration: number
  offset: number
  startFormatted: string
  endFormatted: string
}

type GanttChartProps = {
  proposalData: ProposalData
}

type CustomTooltipProps = {
  active?: boolean
  payload?: any[]
}

export function GanttChart({ proposalData }: GanttChartProps) {
  const [chartData, setChartData] = useState<ChartDataItem[]>([])
  const [today] = useState(new Date())

  useEffect(() => {
    if (!proposalData || !proposalData.scope || !proposalData.scope.deliverables) {
      console.error("Missing proposal data or deliverables:", proposalData)
      return
    }

    const { deliverables, deliverableDates } = proposalData.scope

    // Parse all start/end dates
    const parsedDates = deliverables.map((_, index) => {
      const dates = deliverableDates?.[index] || {}
      const startDate = dates.startDate ? parseISO(dates.startDate) : today
      const endDate = dates.endDate ? parseISO(dates.endDate) : addDays(startDate, 7)
      return { startDate, endDate }
    })

    // Find the earliest start date
    const earliest = parsedDates.reduce(
      (min, d) => (d.startDate < min ? d.startDate : min),
      parsedDates[0]?.startDate || today
    )

    // Build chart data with offset (distance from earliest)
    const data: ChartDataItem[] = deliverables.map((deliverable, index) => {
      const { startDate, endDate } = parsedDates[index]
      return {
        name: deliverable,
        start: startDate,
        end: endDate,
        duration: differenceInDays(endDate, startDate) || 1,
        offset: differenceInDays(startDate, earliest),
        startFormatted: format(startDate, "MMM d, yyyy"),
        endFormatted: format(endDate, "MMM d, yyyy"),
      }
    })

    setChartData(data)
  }, [proposalData, today])

  if (!chartData.length) {
    return <div className="flex justify-center items-center h-full">No timeline data available</div>
  }

  // Find the earliest and latest dates for chart boundaries
  const earliestDate = chartData.reduce((earliest, item) => (item.start < earliest ? item.start : earliest), chartData[0].start)
  const latestDate = chartData.reduce((latest, item) => (item.end > latest ? item.end : latest), chartData[0].end)
  const totalDays = differenceInDays(latestDate, earliestDate)

  // Generate ticks for X axis
  const tickInterval = Math.max(1, Math.floor(totalDays / 7))
  const ticks = Array.from({ length: Math.ceil(totalDays / tickInterval) + 1 }, (_, i) => i * tickInterval)

  // --- Custom Tooltip ---
  const CustomTooltip = ({ active, payload }: CustomTooltipProps) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-3 border rounded shadow-sm">
          <p className="font-medium">{data.name}</p>
          <p>Start: {data.startFormatted}</p>
          <p>End: {data.endFormatted}</p>
          <p>Duration: {data.duration} days</p>
        </div>
      )
    }
    return null
  }

  return (
    <ChartContainer
      config={{
        task: {
          label: "Task Duration",
          color: "hsl(var(--chart-1))",
        },
      }}
      className="h-full"
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 20, right: 30, left: 150, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            type="number"
            domain={[0, totalDays + 1]}
            tickFormatter={(value) => format(addDays(earliestDate, value), "MMM d")}
            ticks={ticks}
          />
          <YAxis dataKey="name" type="category" width={140} />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <ReferenceLine
            x={differenceInDays(today, earliestDate)}
            stroke="red"
            label={{ value: "Today", position: "top" }}
          />
          {/* Each bar starts at 'offset' and has a length of 'duration' */}
          <Bar
            dataKey="duration"
            name="Duration"
            fill="hsl(var(--chart-1))"
            background={{ fill: "#eee" }}
            radius={[4, 4, 4, 4]}
            stackId="a"
            minPointSize={2}
          >
            {/* Custom shape for offset bars */}
            {chartData.map((entry, index) => (
              <rect
                key={entry.name}
                x={`${((entry.offset / (totalDays + 1)) * 100).toFixed(2)}%`}
                y={index * 40}
                width={`${((entry.duration / (totalDays + 1)) * 100).toFixed(2)}%`}
                height={30}
                fill="hsl(var(--chart-1))"
                rx={4}
                ry={4}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
