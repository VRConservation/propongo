"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Download, ArrowLeft } from "lucide-react"
import { GanttChart } from "@/components/gantt-chart"
import { useRouter } from "next/navigation"

export default function GanttChartPage() {
  const router = useRouter()
  const [proposalData, setProposalData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // In a real app, this would fetch from an API or database
    // For now, we'll try to get it from localStorage if available
    try {
      const savedData = localStorage.getItem("proposalData")
      if (savedData) {
        const parsedData = JSON.parse(savedData)
        console.log("Loaded proposal data:", parsedData)
        setProposalData(parsedData)
      }
    } catch (error) {
      console.error("Error loading proposal data:", error)
    } finally {
      setLoading(false)
    }
  }, [])

  const handleDownload = () => {
    // In a real app, this would generate an image or PDF of the chart
    alert("In a production app, this would download the Gantt chart as an image or PDF")
  }

  const handleBack = () => {
    router.back()
  }

  if (loading) {
    return (
      <div className="container mx-auto py-10 px-4 max-w-6xl">
        <Card>
          <CardContent className="p-6 flex justify-center items-center min-h-[400px]">
            <p>Loading Gantt chart...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!proposalData) {
    return (
      <div className="container mx-auto py-10 px-4 max-w-6xl">
        <Card>
          <CardContent className="p-6 flex flex-col justify-center items-center min-h-[400px] gap-4">
            <p>No proposal data found. Please create a proposal first.</p>
            <Button onClick={handleBack}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Propongo
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!proposalData.scope || !proposalData.scope.deliverables || proposalData.scope.deliverables.length === 0) {
    return (
      <div className="container mx-auto py-10 px-4 max-w-6xl">
        <Card>
          <CardContent className="p-6 flex flex-col justify-center items-center min-h-[400px] gap-4">
            <p>No deliverables found. Please add deliverables to create a Gantt chart.</p>
            <Button onClick={handleBack}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Propongo
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-10 px-4 max-w-6xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Project Timeline Gantt Chart</h1>
          <p className="text-muted-foreground mt-1">{proposalData.projectTitle || "Project"} - Deliverables Timeline</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleBack}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Propongo
          </Button>
          <Button onClick={handleDownload}>
            <Download className="mr-2 h-4 w-4" />
            Download Chart
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Project Timeline</CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="h-[500px]">
            <GanttChart proposalData={proposalData} />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
