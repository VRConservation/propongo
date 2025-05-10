"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ArrowLeft, Save } from "lucide-react"
import { useRouter } from "next/navigation"
import { useHelp, type HelpResource } from "@/contexts/help-context"

export default function SettingsPage() {
  const router = useRouter()
  const { helpResources, updateHelpResource } = useHelp()
  const [activeTab, setActiveTab] = useState("scope")
  const [resources, setResources] = useState(helpResources)

  // Update local state when context changes
  useEffect(() => {
    setResources(helpResources)
  }, [helpResources])

  const handleResourceChange = (
    section: keyof typeof helpResources,
    subsection: string,
    field: keyof HelpResource,
    value: string,
  ) => {
    setResources((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [subsection]: {
          ...prev[section][subsection],
          [field]: value,
        },
      },
    }))
  }

  const handleSave = () => {
    // Update all resources in the context
    Object.keys(resources).forEach((section) => {
      Object.keys(resources[section]).forEach((subsection) => {
        updateHelpResource(section as keyof typeof helpResources, subsection, resources[section][subsection])
      })
    })

    alert("Help resources updated successfully!")
  }

  const handleBack = () => {
    router.push("/")
  }

  const renderResourceInputs = (section: keyof typeof helpResources, subsection: string) => {
    const resource = resources[section][subsection]

    return (
      <div className="space-y-4 p-4 border rounded-md">
        <div className="space-y-2">
          <label className="text-sm font-medium">Title</label>
          <Input
            value={resource.title}
            onChange={(e) => handleResourceChange(section, subsection, "title", e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">URL</label>
          <Input
            value={resource.url}
            onChange={(e) => handleResourceChange(section, subsection, "url", e.target.value)}
            placeholder="https://example.com/book/chapter"
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Description</label>
          <Textarea
            value={resource.description || ""}
            onChange={(e) => handleResourceChange(section, subsection, "description", e.target.value)}
            rows={2}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-10 px-4 max-w-6xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Help Resources Settings</h1>
          <p className="text-muted-foreground mt-1">Configure links to your online book chapters</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleBack}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Propongo
          </Button>
          <Button onClick={handleSave}>
            <Save className="mr-2 h-4 w-4" />
            Save Settings
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Help Resource Configuration</CardTitle>
          <CardDescription>
            Link each section of the proposal generator to chapters in your online book or other resources.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid grid-cols-3 mb-8">
              <TabsTrigger value="scope">Scope Resources</TabsTrigger>
              <TabsTrigger value="budget">Budget Resources</TabsTrigger>
              <TabsTrigger value="qualifications">Qualifications Resources</TabsTrigger>
            </TabsList>

            <TabsContent value="scope">
              <div className="space-y-6">
                <h3 className="text-lg font-medium">Scope Section Resources</h3>
                <div className="grid gap-6">
                  <div>
                    <h4 className="font-medium mb-2">Project Overview</h4>
                    {renderResourceInputs("scope", "overview")}
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Project Objectives</h4>
                    {renderResourceInputs("scope", "objectives")}
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Deliverables</h4>
                    {renderResourceInputs("scope", "deliverables")}
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Timeline</h4>
                    {renderResourceInputs("scope", "timeline")}
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Risks</h4>
                    {renderResourceInputs("scope", "risks")}
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Custom Sections</h4>
                    {renderResourceInputs("scope", "customSections")}
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="budget">
              <div className="space-y-6">
                <h3 className="text-lg font-medium">Budget Section Resources</h3>
                <div className="grid gap-6">
                  <div>
                    <h4 className="font-medium mb-2">Budget Breakdown</h4>
                    {renderResourceInputs("budget", "breakdown")}
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Budget Narrative</h4>
                    {renderResourceInputs("budget", "narrative")}
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Contingency Costs</h4>
                    {renderResourceInputs("budget", "contingency")}
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="qualifications">
              <div className="space-y-6">
                <h3 className="text-lg font-medium">Qualifications Section Resources</h3>
                <div className="grid gap-6">
                  <div>
                    <h4 className="font-medium mb-2">Company Background</h4>
                    {renderResourceInputs("qualifications", "companyBackground")}
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Team Members</h4>
                    {renderResourceInputs("qualifications", "teamMembers")}
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Relevant Experience</h4>
                    {renderResourceInputs("qualifications", "relevantExperience")}
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Testimonials</h4>
                    {renderResourceInputs("qualifications", "testimonials")}
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
