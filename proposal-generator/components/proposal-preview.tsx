"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Download, Printer } from "lucide-react"
import { useRef } from "react"
import jsPDF from "jspdf"
import html2canvas from "html2canvas"

// Helper function to format numbers with commas
const formatNumber = (num: number | string) => {
  return new Intl.NumberFormat("en-US").format(Number(num) || 0)
}

interface ProposalPreviewProps {
  data: {
    projectTitle?: string
    clientName?: string
    scope: {
      overview?: string
      objectives: string[]
      deliverables: string[]
      deliverableDates?: { startDate?: string; endDate?: string }[]
      customSections?: {
        [sectionId: string]: { name: string; content: string }
      }
      timelineNotes?: string
      limitations?: string
    }
    budget: {
      totalAmount?: string
      breakdown?: {
        description: string
        units: string | number
        costPerUnit: string
        amount: string
        deliverableId?: string
      }[]
      deliverableGroups?: {
        [groupId: string]: { name: string }
      }
      paymentSchedule?: string
      additionalCosts?: string
    }
    qualifications: {
      companyBackground?: string
      teamMembers: {
        name: string
        role: string
        bio?: string
      }[]
      relevantExperience: string[]
      testimonials: {
        quote: string
        author: string
        company?: string
      }[]
    }
  }
}

export function ProposalPreview({ data }: ProposalPreviewProps) {
  const printRef = useRef<HTMLDivElement>(null)

  const handlePrint = () => {
    const content = printRef.current
    const printWindow = window.open("", "_blank")

    if (printWindow && content) {
      printWindow.document.write(`
        <html>
          <head>
            <title>Business Proposal - ${data.projectTitle}</title>
            <style>
              body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
              }
              h1 { font-size: 24px; margin-bottom: 20px; }
              h2 { font-size: 20px; margin-top: 30px; margin-bottom: 15px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
              h3 { font-size: 18px; margin-top: 20px; }
              h4 { font-size: 16px; margin-top: 15px; font-weight: bold; }
              ul { margin-bottom: 20px; }
              li { margin-bottom: 8px; }
              .section { margin-bottom: 30px; }
              .budget-item { display: flex; justify-content: space-between; margin-bottom: 8px; }
              .testimonial { font-style: italic; margin-bottom: 15px; }
              .testimonial-author { font-weight: bold; }
              table { width: 100%; border-collapse: collapse; }
              th, td { padding: 8px; text-align: left; }
              th { border-bottom: 1px solid #ddd; }
              td { border-bottom: 1px solid #eee; }
              .group-header { background-color: #f5f5f5; font-weight: bold; }
            </style>
          </head>
          <body>
            ${content.innerHTML}
          </body>
        </html>
      `)

      printWindow.document.close()
      printWindow.focus()
      printWindow.print()
    }
  }

  // PDF download with multi-page support
  const handleDownloadPDF = async () => {
    if (!printRef.current) return

    const element = printRef.current
    const canvas = await html2canvas(element, { scale: 2 })
    const imgData = canvas.toDataURL("image/png")

    const pdf = new jsPDF({
      orientation: "portrait",
      unit: "pt",
      format: "a4",
    })

    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()

    // Calculate the image dimensions in PDF units
    const imgProps = pdf.getImageProperties(imgData)
    const pdfWidth = pageWidth
    const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width

    let position = 0
    let remainingHeight = pdfHeight

    // Add first page
    pdf.addImage(imgData, "PNG", 0, position, pdfWidth, pdfHeight)
    remainingHeight -= pageHeight

    // Add more pages if needed
    while (remainingHeight > 0) {
      position -= pageHeight
      pdf.addPage()
      pdf.addImage(imgData, "PNG", 0, position, pdfWidth, pdfHeight)
      remainingHeight -= pageHeight
    }

    pdf.save(
      `proposal-${data.projectTitle ? data.projectTitle.replace(/\s+/g, "-").toLowerCase() : "download"}.pdf`
    )
  }

  const formatDate = () => {
    const date = new Date()
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  }

  // Group budget items by deliverable
  const groupedItems: { [key: string]: NonNullable<ProposalPreviewProps["data"]["budget"]["breakdown"]> } = {}
  const ungroupedItems: NonNullable<ProposalPreviewProps["data"]["budget"]["breakdown"]>[number][] = []

  if (data.budget.breakdown) {
    data.budget.breakdown.forEach((item) => {
      if (item.deliverableId && data.budget.deliverableGroups && data.budget.deliverableGroups[item.deliverableId]) {
        if (!groupedItems[item.deliverableId]) {
          groupedItems[item.deliverableId] = []
        }
        groupedItems[item.deliverableId].push(item)
      } else {
        ungroupedItems.push(item)
      }
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={handlePrint}>
          <Printer className="mr-2 h-4 w-4" />
          Print
        </Button>
        <Button onClick={handleDownloadPDF}>
          <Download className="mr-2 h-4 w-4" />
          Download PDF
        </Button>
      </div>

      <Card className="border-2">
        <CardContent className="p-6">
          <div ref={printRef} className="space-y-8">
            <div className="text-center border-b pb-6">
              <h1 className="text-3xl font-bold mb-2">Business Proposal</h1>
              {data.projectTitle && <p className="text-xl">{data.projectTitle}</p>}
              <p className="text-muted-foreground mt-4">Prepared for: {data.clientName || "[Client Name]"}</p>
              <p className="text-muted-foreground">Date: {formatDate()}</p>
              <p className="text-muted-foreground mt-2">Created with Propongo</p>
            </div>

            {/* Scope Section */}
            <div className="space-y-4">
              <h2 className="text-2xl font-bold border-b pb-2">1. Project Scope</h2>

              {data.scope.overview && (
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">Overview</h3>
                  <p>{data.scope.overview}</p>
                </div>
              )}

              {data.scope.objectives.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">Objectives</h3>
                  <ul className="list-disc pl-6 space-y-1">
                    {data.scope.objectives.map((objective, index) => (
                      <li key={index}>{objective}</li>
                    ))}
                  </ul>
                </div>
              )}

              {data.scope.deliverables.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">Deliverables</h3>
                  <ul className="list-disc pl-6 space-y-1">
                    {data.scope.deliverables.map((deliverable, index) => (
                      <li key={index}>{deliverable}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Custom Sections */}
              {data.scope.customSections && Object.keys(data.scope.customSections).length > 0 && (
                <>
                  {Object.entries(data.scope.customSections).map(([sectionId, section]) => (
                    <div key={sectionId} className="space-y-2">
                      <h3 className="text-xl font-semibold">{section.name}</h3>
                      <div className="whitespace-pre-wrap">{section.content}</div>
                    </div>
                  ))}
                </>
              )}

              {data.scope.deliverables.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">Timeline</h3>
                  <div className="border rounded-md p-4">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left pb-2">Deliverable</th>
                          <th className="text-left pb-2">Start Date</th>
                          <th className="text-left pb-2">End Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.scope.deliverables.map((deliverable, index) => {
                          const dates = data.scope.deliverableDates?.[index] || {}
                          return (
                            <tr key={index} className="border-b">
                              <td className="py-2">{deliverable}</td>
                              <td className="py-2">
                                {dates.startDate ? new Date(dates.startDate).toLocaleDateString() : "TBD"}
                              </td>
                              <td className="py-2">
                                {dates.endDate ? new Date(dates.endDate).toLocaleDateString() : "TBD"}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                  {data.scope.timelineNotes && <p>{data.scope.timelineNotes}</p>}
                </div>
              )}

              {data.scope.limitations && (
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">Risks</h3>
                  <p>{data.scope.limitations}</p>
                </div>
              )}
            </div>

            {/* Budget Section */}
            <div className="space-y-4">
              <h2 className="text-2xl font-bold border-b pb-2">2. Budget</h2>

              {data.budget.totalAmount && (
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">Total Budget</h3>
                  <p className="text-2xl font-bold">
                    ${formatNumber(Number.parseFloat(data.budget.totalAmount ?? "0").toFixed(2))}
                  </p>
                </div>
              )}

              {data.budget.breakdown && data.budget.breakdown.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">Budget Tasks</h3>

                  {/* Grouped Items */}
                  {data.budget.deliverableGroups && Object.keys(data.budget.deliverableGroups).length > 0 && (
                    <div className="space-y-6">
                      {Object.entries(data.budget.deliverableGroups).map(([groupId, group]) =>
                        groupedItems[groupId] && groupedItems[groupId].length > 0 ? (
                          <div key={groupId} className="space-y-2">
                            <h4 className="font-semibold">{group.name}</h4>
                            <div className="border rounded-md p-4">
                              <table className="w-full">
                                <thead>
                                  <tr className="border-b">
                                    <th className="text-left pb-2">Description</th>
                                    <th className="text-center pb-2">Units</th>
                                    <th className="text-center pb-2">Cost/Unit</th>
                                    <th className="text-right pb-2">Total</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {groupedItems[groupId].map((item, index) => (
                                    <tr key={index} className="border-b">
                                      <td className="py-2">{item.description}</td>
                                      <td className="py-2 text-center">{item.units}</td>
                                      <td className="py-2 text-center">
                                        ${formatNumber(Number.parseFloat(item.costPerUnit).toFixed(2))}
                                      </td>
                                      <td className="py-2 text-right">
                                        ${formatNumber(Number.parseFloat(item.amount).toFixed(2))}
                                      </td>
                                    </tr>
                                  ))}
                                  <tr className="font-medium">
                                    <td className="pt-3" colSpan={3}>
                                      Subtotal
                                    </td>
                                    <td className="pt-3 text-right">
                                      $
                                      {formatNumber(
                                        groupedItems[groupId]
                                          .reduce((sum, item) => sum + Number.parseFloat(item.amount), 0)
                                          .toFixed(2),
                                      )}
                                    </td>
                                  </tr>
                                </tbody>
                              </table>
                            </div>
                          </div>
                        ) : null,
                      )}
                    </div>
                  )}

                  {/* Ungrouped Items */}
                  {ungroupedItems.length > 0 && (
                    <div className="space-y-2">
                      {Object.keys(groupedItems).length > 0 && <h4 className="font-semibold">Other Tasks</h4>}
                      <div className="border rounded-md p-4">
                        <table className="w-full">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left pb-2">Description</th>
                              <th className="text-center pb-2">Units</th>
                              <th className="text-center pb-2">Cost/Unit</th>
                              <th className="text-right pb-2">Total</th>
                            </tr>
                          </thead>
                          <tbody>
                            {ungroupedItems.map((item, index) => (
                              <tr key={index} className="border-b">
                                <td className="py-2">{item.description}</td>
                                <td className="py-2 text-center">{item.units}</td>
                                <td className="py-2 text-center">
                                  ${formatNumber(Number.parseFloat(item.costPerUnit).toFixed(2))}
                                </td>
                                <td className="py-2 text-right">
                                  ${formatNumber(Number.parseFloat(item.amount).toFixed(2))}
                                </td>
                              </tr>
                            ))}
                            {Object.keys(groupedItems).length > 0 && (
                              <tr className="font-medium">
                                <td className="pt-3" colSpan={3}>
                                  Subtotal
                                </td>
                                <td className="pt-3 text-right">
                                  $
                                  {formatNumber(
                                    ungroupedItems
                                      .reduce((sum, item) => sum + Number.parseFloat(item.amount), 0)
                                      .toFixed(2),
                                  )}
                                </td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  <div className="border rounded-md p-4 mt-4">
                    <table className="w-full">
                      <tbody>
                        <tr className="font-bold text-lg">
                          <td>Total Budget</td>
                          <td className="text-right">
                            ${formatNumber(Number.parseFloat(data.budget.totalAmount ?? "0").toFixed(2))}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {data.budget.paymentSchedule && (
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">Budget Narrative</h3>
                  <p>{data.budget.paymentSchedule}</p>
                </div>
              )}

              {data.budget.additionalCosts && (
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">Contingency Costs</h3>
                  <p>{data.budget.additionalCosts}</p>
                </div>
              )}
            </div>

            {/* Qualifications Section */}
            <div className="space-y-4">
              <h2 className="text-2xl font-bold border-b pb-2">3. Qualifications</h2>

              {data.qualifications.companyBackground && (
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">Company Background</h3>
                  <p>{data.qualifications.companyBackground}</p>
                </div>
              )}

              {data.qualifications.teamMembers.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">Team Members</h3>
                  <div className="space-y-4">
                    {data.qualifications.teamMembers.map((member, index) => (
                      <div key={index} className="space-y-1">
                        <h4 className="font-medium">{member.name}</h4>
                        <p className="text-muted-foreground">{member.role}</p>
                        {member.bio && <p className="text-sm">{member.bio}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {data.qualifications.relevantExperience.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">Relevant Experience</h3>
                  <ul className="list-disc pl-6 space-y-1">
                    {data.qualifications.relevantExperience.map((experience, index) => (
                      <li key={index}>{experience}</li>
                    ))}
                  </ul>
                </div>
              )}

              {data.qualifications.testimonials.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">Client Testimonials</h3>
                  <div className="space-y-4">
                    {data.qualifications.testimonials.map((testimonial, index) => (
                      <div key={index} className="border-l-4 pl-4 py-2">
                        <p className="italic">"{testimonial.quote}"</p>
                        <p className="text-sm font-medium mt-2">
                          — {testimonial.author}
                          {testimonial.company && `, ${testimonial.company}`}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Conclusion */}
            <div className="border-t pt-6 mt-8">
              <p className="font-medium">
                Thank you for considering our proposal. We look forward to the opportunity to work with you on this
                project.
              </p>
              <p className="mt-4">For any questions or clarifications, please don't hesitate to contact us.</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
