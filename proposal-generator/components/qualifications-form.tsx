"use client"

import { useState, useEffect } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Plus, X } from "lucide-react"
import { useHelp } from "@/contexts/help-context"
import { HelpButton } from "@/components/help-button"

export function QualificationsForm({ data, updateData }) {
  const [qualifications, setQualifications] = useState(data)
  const [newTeamMember, setNewTeamMember] = useState({ name: "", role: "", bio: "" })
  const [newExperience, setNewExperience] = useState("")
  const [newTestimonial, setNewTestimonial] = useState({ quote: "", author: "", company: "" })
  const [activeForm, setActiveForm] = useState(null)
  const { helpResources } = useHelp()

  // Only update parent when local state changes, not on every render
  useEffect(() => {
    // This prevents the infinite loop by not updating if the data is the same
    if (JSON.stringify(qualifications) !== JSON.stringify(data)) {
      updateData(qualifications)
    }
  }, [qualifications, data, updateData])

  const addTeamMember = () => {
    if (newTeamMember.name.trim() && newTeamMember.role.trim()) {
      setQualifications((prev) => ({
        ...prev,
        teamMembers: [...prev.teamMembers, newTeamMember],
      }))
      setNewTeamMember({ name: "", role: "", bio: "" })
      setActiveForm(null)
    }
  }

  const removeTeamMember = (index) => {
    setQualifications((prev) => ({
      ...prev,
      teamMembers: prev.teamMembers.filter((_, i) => i !== index),
    }))
  }

  const addExperience = () => {
    if (newExperience.trim()) {
      setQualifications((prev) => ({
        ...prev,
        relevantExperience: [...prev.relevantExperience, newExperience],
      }))
      setNewExperience("")
      setActiveForm(null)
    }
  }

  const removeExperience = (index) => {
    setQualifications((prev) => ({
      ...prev,
      relevantExperience: prev.relevantExperience.filter((_, i) => i !== index),
    }))
  }

  const addTestimonial = () => {
    if (newTestimonial.quote.trim() && newTestimonial.author.trim()) {
      setQualifications((prev) => ({
        ...prev,
        testimonials: [...prev.testimonials, newTestimonial],
      }))
      setNewTestimonial({ quote: "", author: "", company: "" })
      setActiveForm(null)
    }
  }

  const removeTestimonial = (index) => {
    setQualifications((prev) => ({
      ...prev,
      testimonials: prev.testimonials.filter((_, i) => i !== index),
    }))
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Label htmlFor="companyBackground">Company Background</Label>
          <HelpButton resource={helpResources.qualifications.companyBackground} />
        </div>
        <Textarea
          id="companyBackground"
          placeholder="Provide a brief background of your company"
          rows={4}
          value={qualifications.companyBackground}
          onChange={(e) => setQualifications((prev) => ({ ...prev, companyBackground: e.target.value }))}
        />
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Label>Team Members</Label>
            <HelpButton resource={helpResources.qualifications.teamMembers} />
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setActiveForm(activeForm === "team" ? null : "team")}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Team Member
          </Button>
        </div>

        {activeForm === "team" && (
          <Card>
            <CardContent className="p-4 space-y-4">
              <div className="space-y-2">
                <Label htmlFor="memberName">Name</Label>
                <Input
                  id="memberName"
                  placeholder="Team member name"
                  value={newTeamMember.name}
                  onChange={(e) => setNewTeamMember((prev) => ({ ...prev, name: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="memberRole">Role</Label>
                <Input
                  id="memberRole"
                  placeholder="Team member role"
                  value={newTeamMember.role}
                  onChange={(e) => setNewTeamMember((prev) => ({ ...prev, role: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="memberBio">Bio (Optional)</Label>
                <Textarea
                  id="memberBio"
                  placeholder="Brief bio"
                  rows={2}
                  value={newTeamMember.bio}
                  onChange={(e) => setNewTeamMember((prev) => ({ ...prev, bio: e.target.value }))}
                />
              </div>
              <Button type="button" onClick={addTeamMember}>
                Add Member
              </Button>
            </CardContent>
          </Card>
        )}

        {qualifications.teamMembers.length > 0 && (
          <Card>
            <CardContent className="p-4">
              <ul className="space-y-3">
                {qualifications.teamMembers.map((member, index) => (
                  <li key={index} className="bg-muted p-3 rounded">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">{member.name}</h4>
                        <p className="text-sm text-muted-foreground">{member.role}</p>
                        {member.bio && <p className="text-sm mt-1">{member.bio}</p>}
                      </div>
                      <Button variant="ghost" size="icon" onClick={() => removeTeamMember(index)}>
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
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
            <Label>Relevant Experience</Label>
            <HelpButton resource={helpResources.qualifications.relevantExperience} />
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setActiveForm(activeForm === "experience" ? null : "experience")}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Experience
          </Button>
        </div>

        {activeForm === "experience" && (
          <Card>
            <CardContent className="p-4 space-y-4">
              <div className="space-y-2">
                <Label htmlFor="experience">Project/Experience Description</Label>
                <Textarea
                  id="experience"
                  placeholder="Describe a relevant project or experience"
                  rows={3}
                  value={newExperience}
                  onChange={(e) => setNewExperience(e.target.value)}
                />
              </div>
              <Button type="button" onClick={addExperience}>
                Add Experience
              </Button>
            </CardContent>
          </Card>
        )}

        {qualifications.relevantExperience.length > 0 && (
          <Card>
            <CardContent className="p-4">
              <ul className="space-y-2">
                {qualifications.relevantExperience.map((experience, index) => (
                  <li key={index} className="flex items-center justify-between bg-muted p-3 rounded">
                    <span>{experience}</span>
                    <Button variant="ghost" size="icon" onClick={() => removeExperience(index)}>
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
            <Label>Testimonials</Label>
            <HelpButton resource={helpResources.qualifications.testimonials} />
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setActiveForm(activeForm === "testimonial" ? null : "testimonial")}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add Testimonial
          </Button>
        </div>

        {activeForm === "testimonial" && (
          <Card>
            <CardContent className="p-4 space-y-4">
              <div className="space-y-2">
                <Label htmlFor="testimonialQuote">Quote</Label>
                <Textarea
                  id="testimonialQuote"
                  placeholder="Client testimonial"
                  rows={3}
                  value={newTestimonial.quote}
                  onChange={(e) => setNewTestimonial((prev) => ({ ...prev, quote: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="testimonialAuthor">Author</Label>
                <Input
                  id="testimonialAuthor"
                  placeholder="Author name"
                  value={newTestimonial.author}
                  onChange={(e) => setNewTestimonial((prev) => ({ ...prev, author: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="testimonialCompany">Company (Optional)</Label>
                <Input
                  id="testimonialCompany"
                  placeholder="Company name"
                  value={newTestimonial.company}
                  onChange={(e) => setNewTestimonial((prev) => ({ ...prev, company: e.target.value }))}
                />
              </div>
              <Button type="button" onClick={addTestimonial}>
                Add Testimonial
              </Button>
            </CardContent>
          </Card>
        )}

        {qualifications.testimonials.length > 0 && (
          <Card>
            <CardContent className="p-4">
              <ul className="space-y-3">
                {qualifications.testimonials.map((testimonial, index) => (
                  <li key={index} className="bg-muted p-3 rounded">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="italic">"{testimonial.quote}"</p>
                        <p className="text-sm font-medium mt-2">
                          — {testimonial.author}
                          {testimonial.company && `, ${testimonial.company}`}
                        </p>
                      </div>
                      <Button variant="ghost" size="icon" onClick={() => removeTestimonial(index)} className="ml-2">
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
