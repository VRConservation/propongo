"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { HelpCircle, ExternalLink } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import type { HelpResource } from "@/contexts/help-context"

interface HelpButtonProps {
  resource: HelpResource
  className?: string
}

export function HelpButton({ resource, className = "" }: HelpButtonProps) {
  const [open, setOpen] = useState(false)

  const handleOpenResource = () => {
    window.open(resource.url, "_blank")
    setOpen(false)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className={`h-6 w-6 rounded-full p-0 ${className}`}
          title={`Help: ${resource.title}`}
        >
          <HelpCircle className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{resource.title}</DialogTitle>
          {resource.description && <DialogDescription>{resource.description}</DialogDescription>}
        </DialogHeader>
        <div className="flex justify-end mt-4">
          <Button onClick={handleOpenResource} className="gap-2">
            <ExternalLink className="h-4 w-4" />
            Open Resource
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
