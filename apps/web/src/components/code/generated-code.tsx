'use client'

import { useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useProjectStore } from '@/stores/project-store'
import { MultiFileEditor, CodeFile } from '@/components/preview/CodeEditor'
import { Code2, Download, Copy, Check, ExternalLink } from 'lucide-react'
import { toast } from 'sonner'
import { useState } from 'react'

export function GeneratedCode() {
  const { currentProject } = useProjectStore()
  const [copiedFile, setCopiedFile] = useState<string | null>(null)

  // Convert Record<string, string> to CodeFile[]
  const files: CodeFile[] = useMemo(() => {
    if (!currentProject?.generatedFiles) return []
    return Object.entries(currentProject.generatedFiles).map(([path, content]) => ({
      path,
      content,
    }))
  }, [currentProject?.generatedFiles])

  const handleCopyFile = async (path: string, content: string) => {
    try {
      await navigator.clipboard.writeText(content)
      setCopiedFile(path)
      toast.success(`Copied ${path} to clipboard`)
      setTimeout(() => setCopiedFile(null), 2000)
    } catch {
      toast.error('Failed to copy to clipboard')
    }
  }

  const handleDownloadAll = () => {
    if (!currentProject?.generatedFiles) return

    // Create a zip-like download by downloading individual files
    Object.entries(currentProject.generatedFiles).forEach(([path, content]) => {
      const blob = new Blob([content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = path.split('/').pop() || path
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    })

    toast.success(`Downloaded ${files.length} files`)
  }

  const handleOpenInPreview = () => {
    // Navigate to preview page with current project
    window.open('/preview', '_blank')
  }

  if (!currentProject || files.length === 0) {
    return null
  }

  // Only show when project is complete or has generated files
  if (currentProject.status !== 'complete' && !currentProject.generatedFiles) {
    return null
  }

  return (
    <Card className="mt-6">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Code2 className="h-5 w-5 text-primary" />
            Generated Code
          </span>
          <div className="flex items-center gap-2">
            <span className="text-sm font-normal text-muted-foreground">
              {files.length} files
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadAll}
              className="flex items-center gap-1"
            >
              <Download className="h-4 w-4" />
              Download All
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleOpenInPreview}
              className="flex items-center gap-1"
            >
              <ExternalLink className="h-4 w-4" />
              Preview
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* File list with copy buttons */}
        <div className="mb-4 flex flex-wrap gap-2">
          {files.map((file) => (
            <Button
              key={file.path}
              variant="secondary"
              size="sm"
              onClick={() => handleCopyFile(file.path, file.content)}
              className="flex items-center gap-1 text-xs"
            >
              {copiedFile === file.path ? (
                <Check className="h-3 w-3 text-green-500" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
              {file.path.split('/').pop()}
            </Button>
          ))}
        </div>

        {/* Code editor */}
        <div className="h-[500px] rounded-lg overflow-hidden border border-border">
          <MultiFileEditor
            files={files}
            readOnly={true}
            theme="vs-dark"
          />
        </div>

        {/* Instructions */}
        <div className="mt-4 p-4 bg-muted/50 rounded-lg">
          <h4 className="font-medium mb-2">Next Steps</h4>
          <ol className="list-decimal list-inside text-sm text-muted-foreground space-y-1">
            <li>Download all files or copy individual files</li>
            <li>Create a new project folder on your machine</li>
            <li>Paste the files maintaining the folder structure</li>
            <li>Run <code className="bg-muted px-1 rounded">npm install</code> to install dependencies</li>
            <li>Run <code className="bg-muted px-1 rounded">npm run dev</code> to start the development server</li>
          </ol>
        </div>
      </CardContent>
    </Card>
  )
}

export default GeneratedCode
