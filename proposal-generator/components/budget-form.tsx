"use client"

import { useState, useEffect } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Plus, X, ImportIcon as FileImport, ChevronDown, ChevronUp } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useHelp } from "@/contexts/help-context"
import { HelpButton } from "@/components/help-button"

// Helper function to format numbers with commas
const formatNumber = (num) => {
  return new Intl.NumberFormat("en-US").format(Number(num) || 0)
}

// Helper function to parse formatted numbers back to raw numbers
const parseFormattedNumber = (str) => {
  return Number.parseFloat(str.replace(/,/g, "")) || 0
}

export function BudgetForm({ data, updateData, scopeDeliverables = [] }) {
  const [budget, setBudget] = useState(data)
  const [newItem, setNewItem] = useState({
    description: "",
    units: "1",
    costPerUnit: "",
    amount: "0",
    deliverableId: "",
  })
  const [expandedGroups, setExpandedGroups] = useState({})
  const { helpResources } = useHelp()

  // Only update parent when local state changes, not on every render
  useEffect(() => {
    // This prevents the infinite loop by not updating if the data is the same
    if (JSON.stringify(budget) !== JSON.stringify(data)) {
      updateData(budget)
    }
  }, [budget, data, updateData])

  // Calculate item amount when units or costPerUnit changes
  useEffect(() => {
    const units = Number.parseFloat(newItem.units) || 0
    const costPerUnit = Number.parseFloat(newItem.costPerUnit) || 0
    const amount = (units * costPerUnit).toFixed(2)

    if (amount !== newItem.amount) {
      setNewItem((prev) => ({
        ...prev,
        amount,
      }))
    }
  }, [newItem.units, newItem.costPerUnit])

  const addBudgetItem = () => {
    if (newItem.description.trim() && Number.parseFloat(newItem.amount) > 0) {
      setBudget((prev) => ({
        ...prev,
        breakdown: [
          ...prev.breakdown,
          {
            ...newItem,
            units: newItem.units || "1",
            costPerUnit: newItem.costPerUnit || "0",
            amount: newItem.amount || "0",
          },
        ],
      }))
      setNewItem({
        description: "",
        units: "1",
        costPerUnit: "",
        amount: "0",
        deliverableId: newItem.deliverableId,
      })
    }
  }

  const removeBudgetItem = (index) => {
    setBudget((prev) => ({
      ...prev,
      breakdown: prev.breakdown.filter((_, i) => i !== index),
    }))
  }

  const calculateTotal = () => {
    return budget.breakdown
      .reduce((sum, item) => {
        const amount = Number.parseFloat(item.amount) || 0
        return sum + amount
      }, 0)
      .toFixed(2)
  }

  useEffect(() => {
    setBudget((prev) => ({
      ...prev,
      totalAmount: calculateTotal(),
    }))
  }, [budget.breakdown])

  const importDeliverables = () => {
    // Create deliverable groups if they don't exist
    if (!budget.deliverableGroups) {
      const groups = {}
      scopeDeliverables.forEach((deliverable, index) => {
        groups[index] = {
          name: deliverable,
          id: `del-${index}`,
        }
      })

      setBudget((prev) => ({
        ...prev,
        deliverableGroups: groups,
      }))
    } else {
      // Update existing groups and add new ones
      const updatedGroups = { ...budget.deliverableGroups }
      scopeDeliverables.forEach((deliverable, index) => {
        const existingGroupIndex = Object.keys(updatedGroups).find((key) => updatedGroups[key].name === deliverable)

        if (!existingGroupIndex) {
          const newId = `del-${Date.now()}-${index}`
          updatedGroups[newId] = {
            name: deliverable,
            id: newId,
          }
        }
      })

      setBudget((prev) => ({
        ...prev,
        deliverableGroups: updatedGroups,
      }))
    }

    // Initialize expanded state for all groups
    const expanded = {}
    Object.keys(budget.deliverableGroups || {}).forEach((key) => {
      expanded[key] = true
    })
    setExpandedGroups(expanded)
  }

  const toggleGroup = (groupId) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [groupId]: !prev[groupId],
    }))
  }

  const addDeliverableGroup = () => {
    const newId = `del-${Date.now()}`
    setBudget((prev) => ({
      ...prev,
      deliverableGroups: {
        ...(prev.deliverableGroups || {}),
        [newId]: {
          name: "New Deliverable",
          id: newId,
        },
      },
    }))

    setExpandedGroups((prev) => ({
      ...prev,
      [newId]: true,
    }))
  }

  const updateDeliverableGroupName = (groupId, name) => {
    setBudget((prev) => ({
      ...prev,
      deliverableGroups: {
        ...(prev.deliverableGroups || {}),
        [groupId]: {
          ...(prev.deliverableGroups[groupId] || {}),
          name,
        },
      },
    }))
  }

  const removeDeliverableGroup = (groupId) => {
    const updatedGroups = { ...(budget.deliverableGroups || {}) }
    delete updatedGroups[groupId]

    // Remove this group from any tasks
    const updatedBreakdown = budget.breakdown.map((item) => {
      if (item.deliverableId === groupId) {
        return { ...item, deliverableId: "" }
      }
      return item
    })

    setBudget((prev) => ({
      ...prev,
      deliverableGroups: updatedGroups,
      breakdown: updatedBreakdown,
    }))

    // Update expanded state
    const updatedExpanded = { ...expandedGroups }
    delete updatedExpanded[groupId]
    setExpandedGroups(updatedExpanded)
  }

  // Group budget items by deliverable
  const groupedItems = {}
  const ungroupedItems = []

  budget.breakdown.forEach((item) => {
    if (item.deliverableId && budget.deliverableGroups && budget.deliverableGroups[item.deliverableId]) {
      if (!groupedItems[item.deliverableId]) {
        groupedItems[item.deliverableId] = []
      }
      groupedItems[item.deliverableId].push(item)
    } else {
      ungroupedItems.push(item)
    }
  })

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="totalAmount">Total Budget Amount</Label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <span className="text-gray-500">$</span>
          </div>
          <Input id="totalAmount" className="pl-7" value={formatNumber(budget.totalAmount)} readOnly />
        </div>
        <p className="text-sm text-muted-foreground">This amount is calculated from the budget tasks below</p>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Label>Budget Tasks</Label>
            <HelpButton resource={helpResources.budget.breakdown} />
          </div>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={importDeliverables}
              disabled={!scopeDeliverables || scopeDeliverables.length === 0}
            >
              <FileImport className="mr-2 h-4 w-4" />
              Import Deliverables
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={addDeliverableGroup}>
              <Plus className="mr-2 h-4 w-4" />
              Add Group
            </Button>
          </div>
        </div>

        <Card>
          <CardContent className="p-4">
            <div className="grid grid-cols-1 gap-4">
              <div className="grid grid-cols-12 gap-2 items-end">
                <div className="col-span-12 md:col-span-5">
                  <Label htmlFor="itemDescription">Task Description</Label>
                  <Input
                    id="itemDescription"
                    placeholder="Task description"
                    value={newItem.description}
                    onChange={(e) => setNewItem((prev) => ({ ...prev, description: e.target.value }))}
                  />
                </div>
                <div className="col-span-4 md:col-span-2">
                  <Label htmlFor="itemUnits">Units</Label>
                  <Input
                    id="itemUnits"
                    placeholder="Qty"
                    type="number"
                    min="1"
                    step="1"
                    value={newItem.units}
                    onChange={(e) => setNewItem((prev) => ({ ...prev, units: e.target.value }))}
                  />
                </div>
                <div className="col-span-8 md:col-span-2">
                  <Label htmlFor="itemCostPerUnit">Cost/Unit</Label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                      <span className="text-gray-500">$</span>
                    </div>
                    <Input
                      id="itemCostPerUnit"
                      className="pl-7"
                      placeholder="0.00"
                      type="number"
                      min="0"
                      step="0.01"
                      value={newItem.costPerUnit}
                      onChange={(e) => setNewItem((prev) => ({ ...prev, costPerUnit: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="col-span-8 md:col-span-2">
                  <Label htmlFor="itemDeliverable">Group</Label>
                  <Select
                    value={newItem.deliverableId}
                    onValueChange={(value) => setNewItem((prev) => ({ ...prev, deliverableId: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select group" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">None</SelectItem>
                      {budget.deliverableGroups &&
                        Object.entries(budget.deliverableGroups).map(([id, group]) => (
                          <SelectItem key={id} value={id}>
                            {group.name}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="col-span-4 md:col-span-1">
                  <Button
                    type="button"
                    onClick={addBudgetItem}
                    className="w-full"
                    disabled={!newItem.description.trim() || Number.parseFloat(newItem.amount) <= 0}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Deliverable Groups */}
        {budget.deliverableGroups && Object.keys(budget.deliverableGroups).length > 0 && (
          <div className="space-y-4">
            {Object.entries(budget.deliverableGroups).map(([groupId, group]) => (
              <Card key={groupId} className="border-2">
                <div className="p-4 border-b flex items-center justify-between">
                  <div className="flex items-center gap-2 flex-1">
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={() => toggleGroup(groupId)}>
                      {expandedGroups[groupId] ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </Button>
                    <Input
                      value={group.name}
                      onChange={(e) => updateDeliverableGroupName(groupId, e.target.value)}
                      className="font-medium border-0 focus-visible:ring-0 p-0 h-auto"
                    />
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeDeliverableGroup(groupId)}
                    className="h-8 w-8 p-0"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {expandedGroups[groupId] && (
                  <CardContent className="p-4">
                    {groupedItems[groupId] && groupedItems[groupId].length > 0 ? (
                      <div className="space-y-2">
                        <div className="grid grid-cols-12 gap-2 font-medium text-sm border-b pb-2">
                          <div className="col-span-12 md:col-span-5">Description</div>
                          <div className="col-span-2 md:col-span-2 text-center">Units</div>
                          <div className="col-span-4 md:col-span-2 text-center">Cost/Unit</div>
                          <div className="col-span-5 md:col-span-2 text-right">Total</div>
                          <div className="col-span-1 md:col-span-1"></div>
                        </div>
                        {groupedItems[groupId].map((item, index) => {
                          const itemIndex = budget.breakdown.findIndex((i) => i === item)
                          return (
                            <div key={index} className="grid grid-cols-12 gap-2 items-center py-2 border-b">
                              <div className="col-span-12 md:col-span-5">{item.description}</div>
                              <div className="col-span-2 md:col-span-2 text-center">{item.units}</div>
                              <div className="col-span-4 md:col-span-2 text-center">
                                ${formatNumber(Number.parseFloat(item.costPerUnit).toFixed(2))}
                              </div>
                              <div className="col-span-5 md:col-span-2 text-right font-medium">
                                ${formatNumber(Number.parseFloat(item.amount).toFixed(2))}
                              </div>
                              <div className="col-span-1 md:col-span-1 flex justify-end">
                                <Button variant="ghost" size="icon" onClick={() => removeBudgetItem(itemIndex)}>
                                  <X className="h-4 w-4" />
                                </Button>
                              </div>
                            </div>
                          )
                        })}
                        <div className="flex items-center justify-between p-3 border-t mt-2">
                          <span className="font-medium">Subtotal</span>
                          <span className="font-medium">
                            $
                            {formatNumber(
                              groupedItems[groupId]
                                .reduce((sum, item) => sum + Number.parseFloat(item.amount), 0)
                                .toFixed(2),
                            )}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <p className="text-muted-foreground text-sm">
                        No tasks in this group. Add tasks above and select this group.
                      </p>
                    )}
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        )}

        {/* Ungrouped Items */}
        {ungroupedItems.length > 0 && (
          <Card>
            <CardContent className="p-4">
              <div className="space-y-2">
                <h3 className="font-medium mb-2">Ungrouped Tasks</h3>
                <div className="grid grid-cols-12 gap-2 font-medium text-sm border-b pb-2">
                  <div className="col-span-12 md:col-span-5">Description</div>
                  <div className="col-span-2 md:col-span-2 text-center">Units</div>
                  <div className="col-span-4 md:col-span-2 text-center">Cost/Unit</div>
                  <div className="col-span-5 md:col-span-2 text-right">Total</div>
                  <div className="col-span-1 md:col-span-1"></div>
                </div>
                {ungroupedItems.map((item, index) => {
                  const itemIndex = budget.breakdown.findIndex((i) => i === item)
                  return (
                    <div key={index} className="grid grid-cols-12 gap-2 items-center py-2 border-b">
                      <div className="col-span-12 md:col-span-5">{item.description}</div>
                      <div className="col-span-2 md:col-span-2 text-center">{item.units}</div>
                      <div className="col-span-4 md:col-span-2 text-center">
                        ${formatNumber(Number.parseFloat(item.costPerUnit).toFixed(2))}
                      </div>
                      <div className="col-span-5 md:col-span-2 text-right font-medium">
                        ${formatNumber(Number.parseFloat(item.amount).toFixed(2))}
                      </div>
                      <div className="col-span-1 md:col-span-1 flex justify-end">
                        <Button variant="ghost" size="icon" onClick={() => removeBudgetItem(itemIndex)}>
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {budget.breakdown.length > 0 && (
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between p-3 border-t mt-2">
                <span className="font-bold">Total Budget</span>
                <span className="font-bold">${formatNumber(budget.totalAmount)}</span>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Label htmlFor="budgetNarrative">Budget Narrative</Label>
          <HelpButton resource={helpResources.budget.narrative} />
        </div>
        <Textarea
          id="budgetNarrative"
          placeholder="Describe each item of the budget"
          rows={4}
          value={budget.paymentSchedule}
          onChange={(e) => setBudget((prev) => ({ ...prev, paymentSchedule: e.target.value }))}
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Label htmlFor="contingencyCosts">Contingency Costs</Label>
          <HelpButton resource={helpResources.budget.contingency} />
        </div>
        <Textarea
          id="contingencyCosts"
          placeholder="Describe and justify any contingency costs"
          rows={3}
          value={budget.additionalCosts}
          onChange={(e) => setBudget((prev) => ({ ...prev, additionalCosts: e.target.value }))}
        />
      </div>
    </div>
  )
}
