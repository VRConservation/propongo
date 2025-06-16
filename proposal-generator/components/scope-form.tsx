"use client"

import { useState, useEffect } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Plus, X, ChevronDown, ChevronUp, Edit } from "lucide-react"
import { useHelp } from "@/contexts/help-context"
import { HelpButton } from "@/components/help-button"

export function ScopeForm({ data, updateData, updateClientName, updateProjectTitle }) {
  const [scope, setScope] = useState(data.scope)
  const [clientName, setClientName] = useState(data.clientName || "")
  const [projectTitle, setProjectTitle] = useState(data.projectTitle || "")
  const [newObjective, setNewObjective] = useState("")
  const [newDeliverable, setNewDeliverable] = useState("")
  const [newSectionName, setNewSectionName] = useState("")
  const [expandedSections, setExpandedSections] = useState({})
  const [editingSectionName, setEditingSectionName] = useState(null)
  const { helpResources } = useHelp()

  // Only update parent when local state changes, not on every render
  useEffect(() => {
    // This prevents the infinite loop by not updating if the data is the same
    if (JSON.stringify(scope) !== JSON.stringify(data.scope)) {
      updateData(scope)
    }
  }, [scope, data.scope, updateData])

  const handleClientNameChange = (e) => {
    setClientName(e.target.value)
    updateClientName(e.target.value)
  }

  const handleProjectTitleChange = (e) => {
    setProjectTitle(e.target.value)
    updateProjectTitle(e.target.value)
  }

  const addObjective = () => {
    if (newObjective.trim()) {
      setScope((prev) => ({
        ...prev,
        objectives: [...prev.objectives, newObjective],
      }))
      setNewObjective("")
    }
  }

  const removeObjective = (index) => {
    setScope((prev) => ({
      ...prev,
      objectives: prev.objectives.filter((_, i) => i !== index),
    }))
  }

  const addDeliverable = () => {
    if (newDeliverable.trim()) {
      setScope((prev) => ({
        ...prev,
        deliverables: [...prev.deliverables, newDeliverable],
      }))
      setNewDeliverable("")
    }
  }

  const removeDeliverable = (index) => {
    setScope((prev) => ({
      ...prev,
      deliverables: prev.deliverables.filter((_, i) => i !== index),
    }))
  }

  const addCustomSection = () => {
    if (newSectionName.trim()) {
      const sectionId = `section-${Date.now()}`
      setScope((prev) => ({
        ...prev,
        customSections: {
          ...(prev.customSections || {}),
          [sectionId]: {
            name: newSectionName,
            content: "",
          },
        },
      }))
      setExpandedSections((prev) => ({
        ...prev,
        [sectionId]: true,
      }))
      setNewSectionName("")
    }
  }

  const updateSectionContent = (sectionId, content) => {
    setScope((prev) => ({
      ...prev,
      customSections: {
        ...(prev.customSections || {}),
        [sectionId]: {
          ...prev.customSections[sectionId],
          content,
        },
      },
    }))
  }

  const updateSectionName = (sectionId, name) => {
    setScope((prev) => ({
      ...prev,
      customSections: {
        ...(prev.customSections || {}),
        [sectionId]: {
          ...prev.customSections[sectionId],
          name,
        },
      },
    }))
    setEditingSectionName(null)
  }

  const removeCustomSection = (sectionId) => {
    const updatedSections = { ...(scope.customSections || {}) }
    delete updatedSections[sectionId]

    setScope((prev) => ({
      ...prev,
      customSections: updatedSections,
    }))

    const updatedExpanded = { ...expandedSections }
    delete updatedExpanded[sectionId]
    setExpandedSections(updatedExpanded)
  }

  const toggleSection = (sectionId) => {
    setExpandedSections((prev) => ({
      ...prev,
      [sectionId]: !prev[sectionId],
    }))
  }

  const openGanttChart = () => {
    // Save current data to localStorage before opening Gantt chart
    localStorage.setItem(
      "proposalData",
      JSON.stringify({
        clientName,
        projectTitle,
        scope,
        budget: data.budget,
        qualifications: data.qualifications,
      }),
    )
    window.open("/gantt-chart", "_blank")
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="clientName">Client Name</Label>
          <Input id="clientName" placeholder="Enter client name" value={clientName} onChange={handleClientNameChange} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="projectTitle">Project Title</Label>
          <Input
            id="projectTitle"
            placeholder="Enter project title"
            value={projectTitle}
            onChange={handleProjectTitleChange}
          />
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Label htmlFor="overview">Project Overview</Label>
          <HelpButton resource={helpResources.scope.overview} />
        </div>
        <Textarea
          id="overview"
          placeholder="Provide a brief overview of the project"
          rows={4}
          value={scope.overview}
          onChange={(e) => setScope((prev) => ({ ...prev, overview: e.target.value }))}
        />
      </div>

      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Label>Project Goals & Objectives</Label>
          <HelpButton resource={helpResources.scope.objectives} />
        </div>
        <div className="flex gap-2">
          <Input
            placeholder="Add a project objective"
            value={newObjective}
            onChange={(e) => setNewObjective(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addObjective()}
          />
          <Button type="button" onClick={addObjective} size="icon">
            <Plus className="h-4 w-4" />
          </Button>
        </div>

        {scope.objectives.length > 0 && (
          <Card>
            <CardContent className="p-4">
              <ul className="space-y-2">
                {scope.objectives.map((objective, index) => (
                  <li key={index} className="flex items-center justify-between bg-muted p-2 rounded">
                    <span>{objective}</span>
                    <Button variant="ghost" size="icon" onClick={() => removeObjective(index)}>
                      <X className="h-4 w-4" />
                    </Button>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>

      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Label>Deliverables</Label>
          <HelpButton resource={helpResources.scope.deliverables} />
        </div>
        <div className="flex gap-2">
          <Input
            placeholder="Add a deliverable"
            value={newDeliverable}
            onChange={(e) => setNewDeliverable(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addDeliverable()}
          />
          <Button type="button" onClick={addDeliverable} size="icon">
            <Plus className="h-4 w-4" />
          </Button>
        </div>

        {scope.deliverables.length > 0 && (
          <Card>
            <CardContent className="p-4">
              <ul className="space-y-2">
                {scope.deliverables.map((deliverable, index) => (
                  <li key={index} className="flex items-center justify-between bg-muted p-2 rounded">
                    <span>{deliverable}</span>
                    <Button variant="ghost" size="icon" onClick={() => removeDeliverable(index)}>
                      <X className="h-4 w-4" />
                    </Button>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Label>Project Timeline</Label>
            <HelpButton resource={helpResources.scope.timeline} />
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={openGanttChart}
            disabled={scope.deliverables.length === 0}
          >
            Create Gantt Chart
          </Button>
        </div>

        {scope.deliverables.length > 0 ? (
          <Card>
            <CardContent className="p-4">
              <h3 className="font-medium mb-2">Deliverable Timeline Summary</h3>
              <ul className="space-y-2">
                {scope.deliverables.map((deliverable, index) => (
                  <li key={index} className="flex items-center justify-between bg-muted p-2 rounded">
                    <span>{deliverable}</span>
                    <div className="flex gap-2">
                      <Input
                        type="date"
                        className="w-auto"
                        value={scope.deliverableDates?.[index]?.startDate || ""}
                        onChange={(e) => {
                          const newDates = { ...(scope.deliverableDates || {}) }
                          newDates[index] = {
                            ...newDates[index],
                            startDate: e.target.value,
                          }
                          setScope((prev) => ({
                            ...prev,
                            deliverableDates: newDates,
                          }))
                        }}
                        placeholder="Start date"
                      />
                      <Input
                        type="date"
                        className="w-auto"
                        value={scope.deliverableDates?.[index]?.endDate || ""}
                        onChange={(e) => {
                          const newDates = { ...(scope.deliverableDates || {}) }
                          newDates[index] = {
                            ...newDates[index],
                            endDate: e.target.value,
                          }
                          setScope((prev) => ({
                            ...prev,
                            deliverableDates: newDates,
                          }))
                        }}
                        placeholder="End date"
                      />
                    </div>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ) : (
          <p className="text-sm text-muted-foreground">Add deliverables above to create a project timeline</p>
        )}

        <div className="space-y-2">
          <Label htmlFor="timelineNotes">Additional Timeline Notes</Label>
          <Textarea
            id="timelineNotes"
            placeholder="Add any additional notes about the project timeline"
            rows={3}
            value={scope.timelineNotes || ""}
            onChange={(e) => setScope((prev) => ({ ...prev, timelineNotes: e.target.value }))}
          />
        </div>
      </div>

      {/* Custom Sections */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Label>Custom Sections</Label>
            <HelpButton resource={helpResources.scope.customSections} />
          </div>
          <div className="flex gap-2">
            <Input
              placeholder="New section name"
              value={newSectionName}
              onChange={(e) => setNewSectionName(e.target.value)}
              className="w-48 md:w-64"
              onKeyDown={(e) => e.key === "Enter" && addCustomSection()}
            />
            <Button type="button" onClick={addCustomSection} size="sm" disabled={!newSectionName.trim()}>
              <Plus className="mr-2 h-4 w-4" />
              Add Section
            </Button>
          </div>
        </div>

        {scope.customSections && Object.keys(scope.customSections).length > 0 && (
          <div className="space-y-4">
            {Object.entries(scope.customSections).map(([sectionId, section]) => (
              <Card key={sectionId}>
                <div className="p-4 border-b flex items-center justify-between">
                  <div className="flex items-center gap-2 flex-1">
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => toggleSection(sectionId)}>
                      {expandedSections[sectionId] ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </Button>
                    {editingSectionName === sectionId ? (
                      <Input
                        value={section.name}
                        onChange={(e) =>
                          setScope((prev) => ({
                            ...prev,
                            customSections: {
                              ...(prev.customSections || {}),
                              [sectionId]: {
                                ...prev.customSections[sectionId],
                                name: e.target.value,
                              },
                            },
                          }))
                        }
                        onBlur={() => updateSectionName(sectionId, section.name)}
                        onKeyDown={(e) => e.key === "Enter" && updateSectionName(sectionId, section.name)}
                        className="h-8"
                        autoFocus
                      />
                    ) : (
                      <h3 className="font-medium">{section.name}</h3>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setEditingSectionName(sectionId)}
                      className="h-8 w-8 p-0 ml-2"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeCustomSection(sectionId)}
                    className="h-8 w-8 p-0"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {expandedSections[sectionId] && (
                  <CardContent className="p-4">
                    <Textarea
                      placeholder={`Enter content for ${section.name}...`}
                      rows={5}
                      value={section.content || ""}
                      onChange={(e) => updateSectionContent(sectionId, e.target.value)}
                    />
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Label htmlFor="limitations">Risks</Label>
          <HelpButton resource={helpResources.scope.risks} />
        </div>
        <Textarea
          id="limitations"
          placeholder="Describe any risks or limitations to implementing your scope"
          rows={3}
          value={scope.limitations}
          onChange={(e) => setScope((prev) => ({ ...prev, limitations: e.target.value }))}
        />
      </div>
    </div>
  )
}
