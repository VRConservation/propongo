"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScopeForm } from "@/components/scope-form"
import { BudgetForm } from "@/components/budget-form"
import { QualificationsForm } from "@/components/qualifications-form"
import { ProposalPreview } from "@/components/proposal-preview"
import { FileText, Download, Save, Settings } from "lucide-react"
import Link from "next/link"

export default function ProposalGenerator() {
  const [activeTab, setActiveTab] = useState("scope")
  const [proposalData, setProposalData] = useState({
    clientName: "",
    projectTitle: "",
    scope: {
      overview: "",
      objectives: [],
      deliverables: [],
      deliverableDates: {},
      timelineNotes: "",
      limitations: "",
      customSections: {},
    },
    budget: {
      totalAmount: "",
      breakdown: [],
      deliverableGroups: {},
      paymentSchedule: "",
      additionalCosts: "",
    },
    qualifications: {
      companyBackground: "",
      teamMembers: [],
      relevantExperience: [],
      testimonials: [],
    },
  })

  // Try to load saved data from localStorage on initial load
  useEffect(() => {
    try {
      const savedData = localStorage.getItem("proposalData")
      if (savedData) {
        const parsedData = JSON.parse(savedData)

        // Update the budget breakdown items to ensure they have the new structure
        if (parsedData.budget && parsedData.budget.breakdown) {
          parsedData.budget.breakdown = parsedData.budget.breakdown.map((item) => {
            // If the item doesn't have units or costPerUnit, add them
            if (!item.units || !item.costPerUnit) {
              const amount = Number.parseFloat(item.amount) || 0
              return {
                ...item,
                units: item.units || "1",
                costPerUnit: item.costPerUnit || amount.toString(),
                deliverableId: item.deliverableId || "",
              }
            }
            return item
          })
        }

        // Ensure deliverableGroups exists
        if (parsedData.budget && !parsedData.budget.deliverableGroups) {
          parsedData.budget.deliverableGroups = {}
        }

        // Ensure customSections exists
        if (parsedData.scope && !parsedData.scope.customSections) {
          parsedData.scope.customSections = {}
        }

        setProposalData(parsedData)
      }
    } catch (error) {
      console.error("Error loading saved proposal data:", error)
    }
  }, [])

  // Save proposal data to localStorage when it changes
  useEffect(() => {
    try {
      localStorage.setItem("proposalData", JSON.stringify(proposalData))
    } catch (error) {
      console.error("Error saving proposal data:", error)
    }
  }, [proposalData])

  const updateProposalData = (section, data) => {
    setProposalData((prev) => ({
      ...prev,
      [section]: data,
    }))
  }

  // Add this function to handle client name and project title updates more efficiently
  const updateBasicInfo = (field, value) => {
    setProposalData((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  const handleNext = () => {
    if (activeTab === "scope") setActiveTab("budget")
    else if (activeTab === "budget") setActiveTab("qualifications")
    else if (activeTab === "qualifications") setActiveTab("preview")
  }

  const handlePrevious = () => {
    if (activeTab === "preview") setActiveTab("qualifications")
    else if (activeTab === "qualifications") setActiveTab("budget")
    else if (activeTab === "budget") setActiveTab("scope")
  }

  const handleExport = () => {
    // In a real application, this would generate a PDF or document
    alert("In a production app, this would export your proposal as a PDF or document")
  }

  const handleSave = () => {
    // In a real application, this would save to a database
    const proposalJson = JSON.stringify(proposalData, null, 2)
    const blob = new Blob([proposalJson], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "proposal.json"
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const openGanttChart = () => {
    // Save current data to localStorage before opening Gantt chart
    localStorage.setItem("proposalData", JSON.stringify(proposalData))
    window.open("/gantt-chart", "_blank")
  }

  return (
    <div className="container mx-auto py-10 px-4 max-w-6xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Propongo</h1>
          <p className="text-muted-foreground mt-1">Create high quality proposals</p>
        </div>
        <div className="flex gap-2">
          <Link href="/settings">
            <Button variant="outline" size="icon" title="Help Resource Settings">
              <Settings className="h-4 w-4" />
            </Button>
          </Link>
          <Button variant="outline" onClick={handleSave}>
            <Save className="mr-2 h-4 w-4" />
            Save
          </Button>
          <Button onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-6">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid grid-cols-4 mb-8">
              <TabsTrigger value="scope">Scope</TabsTrigger>
              <TabsTrigger value="budget">Budget</TabsTrigger>
              <TabsTrigger value="qualifications">Qualifications</TabsTrigger>
              <TabsTrigger value="preview">Preview</TabsTrigger>
            </TabsList>

            <TabsContent value="scope">
              <ScopeForm
                data={proposalData}
                updateData={(data) => updateProposalData("scope", data)}
                updateClientName={(name) => updateBasicInfo("clientName", name)}
                updateProjectTitle={(title) => updateBasicInfo("projectTitle", title)}
              />
            </TabsContent>

            <TabsContent value="budget">
              <BudgetForm
                data={proposalData.budget}
                updateData={(data) => updateProposalData("budget", data)}
                scopeDeliverables={proposalData.scope.deliverables}
              />
            </TabsContent>

            <TabsContent value="qualifications">
              <QualificationsForm
                data={proposalData.qualifications}
                updateData={(data) => updateProposalData("qualifications", data)}
              />
            </TabsContent>

            <TabsContent value="preview">
              <ProposalPreview data={proposalData} />
            </TabsContent>
          </Tabs>

          <div className="flex justify-between mt-8">
            <Button variant="outline" onClick={handlePrevious} disabled={activeTab === "scope"}>
              Previous
            </Button>
            {activeTab !== "preview" ? (
              <Button onClick={handleNext}>Next</Button>
            ) : (
              <Button onClick={handleExport}>
                <FileText className="mr-2 h-4 w-4" />
                Generate Proposal
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
