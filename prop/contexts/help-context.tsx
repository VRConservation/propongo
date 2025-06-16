"use client"

import { createContext, useContext, useState, type ReactNode } from "react"

// Define the structure for help resources
export type HelpResource = {
  title: string
  url: string
  description?: string
}

// Define the help resources for each section
type HelpResources = {
  scope: {
    overview: HelpResource
    objectives: HelpResource
    deliverables: HelpResource
    timeline: HelpResource
    risks: HelpResource
    customSections: HelpResource
  }
  budget: {
    breakdown: HelpResource
    narrative: HelpResource
    contingency: HelpResource
  }
  qualifications: {
    companyBackground: HelpResource
    teamMembers: HelpResource
    relevantExperience: HelpResource
    testimonials: HelpResource
  }
}

// Default help resources - these would be replaced with your actual book URLs
const defaultHelpResources: HelpResources = {
  scope: {
    overview: {
      title: "Writing an Effective Project Overview",
      url: "https://example.com/book/chapter1",
      description: "Learn how to craft a compelling project overview that sets the stage for your proposal.",
    },
    objectives: {
      title: "Defining Clear Project Objectives",
      url: "https://example.com/book/chapter2",
      description: "Guidelines for creating specific, measurable, achievable, relevant, and time-bound objectives.",
    },
    deliverables: {
      title: "Specifying Project Deliverables",
      url: "https://example.com/book/chapter3",
      description: "How to clearly define what will be delivered to the client.",
    },
    timeline: {
      title: "Creating a Realistic Timeline",
      url: "https://example.com/book/chapter4",
      description: "Tips for estimating project duration and creating a timeline that works.",
    },
    risks: {
      title: "Identifying and Addressing Project Risks",
      url: "https://example.com/book/chapter5",
      description: "How to identify potential risks and develop mitigation strategies.",
    },
    customSections: {
      title: "Adding Custom Proposal Sections",
      url: "https://example.com/book/chapter6",
      description: "Guidelines for when and how to add custom sections to your proposal.",
    },
  },
  budget: {
    breakdown: {
      title: "Creating a Detailed Budget Breakdown",
      url: "https://example.com/book/chapter7",
      description: "How to itemize costs and create a transparent budget that builds client trust.",
    },
    narrative: {
      title: "Writing an Effective Budget Narrative",
      url: "https://example.com/book/chapter8",
      description: "Explaining your budget in a way that justifies costs and demonstrates value.",
    },
    contingency: {
      title: "Planning for Contingencies",
      url: "https://example.com/book/chapter9",
      description: "How to account for unexpected costs and changes in project scope.",
    },
  },
  qualifications: {
    companyBackground: {
      title: "Presenting Your Company Background",
      url: "https://example.com/book/chapter10",
      description: "How to highlight your company's history, mission, and values in a relevant way.",
    },
    teamMembers: {
      title: "Showcasing Your Team",
      url: "https://example.com/book/chapter11",
      description: "Best practices for presenting team members' qualifications and expertise.",
    },
    relevantExperience: {
      title: "Demonstrating Relevant Experience",
      url: "https://example.com/book/chapter12",
      description: "How to select and present past projects that demonstrate your capability.",
    },
    testimonials: {
      title: "Including Effective Testimonials",
      url: "https://example.com/book/chapter13",
      description: "Guidelines for selecting and presenting client testimonials that build credibility.",
    },
  },
}

// Create the context
type HelpContextType = {
  helpResources: HelpResources
  updateHelpResource: (section: keyof HelpResources, subsection: string, resource: Partial<HelpResource>) => void
}

const HelpContext = createContext<HelpContextType | undefined>(undefined)

// Create the provider component
export function HelpProvider({ children }: { children: ReactNode }) {
  const [helpResources, setHelpResources] = useState<HelpResources>(defaultHelpResources)

  const updateHelpResource = (section: keyof HelpResources, subsection: string, resource: Partial<HelpResource>) => {
    setHelpResources((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [subsection]: {
          ...prev[section][subsection],
          ...resource,
        },
      },
    }))
  }

  return <HelpContext.Provider value={{ helpResources, updateHelpResource }}>{children}</HelpContext.Provider>
}

// Create a hook to use the help context
export function useHelp() {
  const context = useContext(HelpContext)
  if (context === undefined) {
    throw new Error("useHelp must be used within a HelpProvider")
  }
  return context
}
