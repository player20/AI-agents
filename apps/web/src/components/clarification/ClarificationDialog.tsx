"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import { MessageSquareMore, Check, Sparkles } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

export interface ClarificationQuestion {
  id: string
  question: string
  type: string
  options: string[]
  allow_custom: boolean
  priority: number
  context: string
}

export interface ClarificationDialogProps {
  open: boolean
  questions: ClarificationQuestion[]
  detectedIndustry: string
  confidence: number
  onSubmit: (responses: Record<string, string>) => void
  onSkip: () => void
}

export function ClarificationDialog({
  open,
  questions,
  detectedIndustry,
  confidence,
  onSubmit,
  onSkip,
}: ClarificationDialogProps) {
  const [responses, setResponses] = useState<Record<string, string>>({})
  const [customInputs, setCustomInputs] = useState<Record<string, string>>({})
  const [currentIndex, setCurrentIndex] = useState(0)

  // Reset state when dialog opens with new questions
  useEffect(() => {
    if (open && questions.length > 0) {
      setResponses({})
      setCustomInputs({})
      setCurrentIndex(0)
    }
  }, [open, questions])

  const currentQuestion = questions[currentIndex]
  const isLastQuestion = currentIndex === questions.length - 1
  const hasResponse = currentQuestion && responses[currentQuestion.id]

  const handleOptionSelect = (questionId: string, option: string) => {
    setResponses((prev) => ({
      ...prev,
      [questionId]: option,
    }))
  }

  const handleCustomInput = (questionId: string, value: string) => {
    setCustomInputs((prev) => ({
      ...prev,
      [questionId]: value,
    }))
    // Also set as response if there's content
    if (value.trim()) {
      setResponses((prev) => ({
        ...prev,
        [questionId]: value.trim(),
      }))
    }
  }

  const handleNext = () => {
    if (isLastQuestion) {
      onSubmit(responses)
    } else {
      setCurrentIndex((prev) => prev + 1)
    }
  }

  const handleBack = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1)
    }
  }

  const answeredCount = Object.keys(responses).length

  if (!open || questions.length === 0) {
    return null
  }

  return (
    <Dialog open={open}>
      <DialogContent showCloseButton={false} className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
              <MessageSquareMore className="h-4 w-4 text-primary" />
            </div>
            <div>
              <DialogTitle>Quick Questions</DialogTitle>
              <DialogDescription>
                Help me understand your project better
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* Industry Badge */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Sparkles className="h-3 w-3" />
          <span>Detected:</span>
          <Badge variant="secondary" className="capitalize">
            {detectedIndustry.replace("-", " ")}
          </Badge>
          <span className="text-xs">({Math.round(confidence * 100)}% confident)</span>
        </div>

        {/* Progress */}
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
            />
          </div>
          <span className="text-xs text-muted-foreground">
            {currentIndex + 1}/{questions.length}
          </span>
        </div>

        {/* Question */}
        {currentQuestion && (
          <div className="space-y-4 py-2">
            <Label className="text-base font-medium">
              {currentQuestion.question}
            </Label>

            {currentQuestion.context && (
              <p className="text-xs text-muted-foreground">
                {currentQuestion.context}
              </p>
            )}

            {/* Options */}
            <div className="grid gap-2">
              {currentQuestion.options.map((option) => (
                <button
                  key={option}
                  onClick={() => handleOptionSelect(currentQuestion.id, option)}
                  className={cn(
                    "flex items-center gap-2 rounded-md border p-3 text-left text-sm transition-colors",
                    responses[currentQuestion.id] === option
                      ? "border-primary bg-primary/5"
                      : "border-muted hover:border-primary/50 hover:bg-muted/50"
                  )}
                >
                  <div
                    className={cn(
                      "flex h-4 w-4 shrink-0 items-center justify-center rounded-full border",
                      responses[currentQuestion.id] === option
                        ? "border-primary bg-primary"
                        : "border-muted-foreground/50"
                    )}
                  >
                    {responses[currentQuestion.id] === option && (
                      <Check className="h-2.5 w-2.5 text-primary-foreground" />
                    )}
                  </div>
                  <span>{option}</span>
                </button>
              ))}

              {/* Custom Input */}
              {currentQuestion.allow_custom && (
                <div className="mt-2">
                  <Input
                    placeholder="Or type your own answer..."
                    value={customInputs[currentQuestion.id] || ""}
                    onChange={(e) =>
                      handleCustomInput(currentQuestion.id, e.target.value)
                    }
                    className="text-sm"
                  />
                </div>
              )}
            </div>
          </div>
        )}

        <DialogFooter className="flex-row justify-between sm:justify-between">
          <div className="flex gap-2">
            {currentIndex > 0 && (
              <Button variant="ghost" size="sm" onClick={handleBack}>
                Back
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={onSkip}>
              Skip All
            </Button>
          </div>
          <Button
            onClick={handleNext}
            disabled={!hasResponse}
            size="sm"
          >
            {isLastQuestion ? `Submit (${answeredCount} answers)` : "Next"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
