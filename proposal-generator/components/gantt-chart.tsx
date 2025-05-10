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

export function GanttChart({ proposalData }) {
  const [chartData, setChartData] = useState([])
  const [today] = useState(new Date())

  useEffect(() => {
    if (!proposalData || !proposalData.scope || !proposalData.scope.deliverables) {
      console.error("Missing proposal data or deliverables:", proposalData)
      return
    }

    console.log("Processing deliverables for Gantt chart:", proposalData.scope.deliverables)
    const { deliverables, deliverableDates } = proposalData.scope

    // Create chart data from deliverables
    const data = deliverables.map((deliverable, index) => {
      const dates = deliverableDates?.[index] || {}
      const startDate = dates.startDate ? parseISO(dates.startDate) : today
      const endDate = dates.endDate ? parseISO(dates.endDate) : addDays(startDate, 7)

      return {
        name: deliverable,
        start: startDate,
        end: endDate,
        duration: differenceInDays(endDate, startDate) || 1,
        startFormatted: format(startDate, "MMM d, yyyy"),
        endFormatted: format(endDate, "MMM d, yyyy"),
      }
    })

    setChartData(data)
  }, [proposalData, today])

  // Find the earliest and latest dates for chart boundaries
  const earliestDate = chartData.length
    ? chartData.reduce((earliest, item) => (item.start < earliest ? item.start : earliest), chartData[0]?.start)
    : today

  const latestDate = chartData.length
    ? chartData.reduce((latest, item) => (item.end > latest ? item.end : latest), chartData[0]?.end)
    : addDays(today, 30)

  // Create an array of dates for the x-axis
  const dateRange = []
  let currentDate = new Date(earliestDate)
  while (currentDate <= latestDate) {
    dateRange.push(new Date(currentDate))
    currentDate = addDays(currentDate, 1)
  }

  // Custom tooltip for the Gantt chart
  const CustomTooltip = ({ active, payload }) => {
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

  if (!chartData.length) {
    return <div className="flex justify-center items-center h-full">No timeline data available</div>
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
        <BarChart data={chartData} layout="vertical" margin={{ top: 20, right: 30, left: 150, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="duration"
            type="number"
            domain={[0, differenceInDays(latestDate, earliestDate) + 1]}
            tickFormatter={(value) => format(addDays(earliestDate, value), "MMM d")}
            ticks={[0, 7, 14, 21, 28, 35, 42, 49, 56]}
          />
          <YAxis dataKey="name" type="category" width={140} />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <ReferenceLine
            x={differenceInDays(today, earliestDate)}
            stroke="red"
            label={{ value: "Today", position: "top" }}
          />
          <Bar
            dataKey="duration"
            name="Duration"
            fill="var(--color-task)"
            background={{ fill: "#eee" }}
            radius={[4, 4, 4, 4]}
          />
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  )
}
