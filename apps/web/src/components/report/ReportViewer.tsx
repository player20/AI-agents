'use client'

import { useState, useRef, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Download, ExternalLink, Maximize2, Minimize2, FileText, Printer } from 'lucide-react'

interface ReportViewerProps {
  html: string
  reportType?: 'transformation_proposal' | 'ux_audit' | 'comprehensive'
  companyName?: string
  className?: string
}

export function ReportViewer({
  html,
  reportType = 'comprehensive',
  companyName = 'Business',
  className = ''
}: ReportViewerProps) {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Generate filename based on report type and company
  const getFilename = useCallback(() => {
    const sanitizedName = companyName.toLowerCase().replace(/[^a-z0-9]+/g, '-')
    const typeLabel = {
      transformation_proposal: 'transformation-proposal',
      ux_audit: 'ux-audit',
      comprehensive: 'comprehensive-report'
    }[reportType]
    const date = new Date().toISOString().split('T')[0]
    return `${sanitizedName}-${typeLabel}-${date}.html`
  }, [companyName, reportType])

  // Download report as HTML file
  const handleDownload = useCallback(() => {
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = getFilename()
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }, [html, getFilename])

  // Open report in new tab
  const handleOpenInNewTab = useCallback(() => {
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
  }, [html])

  // Print report
  const handlePrint = useCallback(() => {
    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.print()
    }
  }, [])

  // Toggle fullscreen
  const toggleFullscreen = useCallback(async () => {
    if (!containerRef.current) return

    if (!document.fullscreenElement) {
      await containerRef.current.requestFullscreen()
      setIsFullscreen(true)
    } else {
      await document.exitFullscreen()
      setIsFullscreen(false)
    }
  }, [])

  // Get report type badge
  const getReportTypeBadge = () => {
    const badges = {
      transformation_proposal: {
        label: 'Transformation Proposal',
        className: 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      },
      ux_audit: {
        label: 'UX & Performance Audit',
        className: 'bg-orange-500/20 text-orange-400 border-orange-500/30'
      },
      comprehensive: {
        label: 'Comprehensive Report',
        className: 'bg-purple-500/20 text-purple-400 border-purple-500/30'
      }
    }
    return badges[reportType]
  }

  const badge = getReportTypeBadge()

  if (!html) {
    return (
      <div className={`flex flex-col items-center justify-center h-full bg-gray-900 ${className}`}>
        <FileText className="w-16 h-16 text-gray-600 mb-4" />
        <h3 className="text-lg font-medium text-gray-400 mb-2">No Report Generated</h3>
        <p className="text-sm text-gray-500 text-center max-w-md">
          The business insights report will appear here once generation is complete.
        </p>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className={`flex flex-col h-full bg-gray-900 ${className}`}
    >
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-gray-400" />
          <span className="font-medium text-gray-200">Business Insights Report</span>
          <span className={`px-2 py-0.5 text-xs rounded-full border ${badge.className}`}>
            {badge.label}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handlePrint}
            className="text-gray-400 hover:text-white hover:bg-gray-700"
          >
            <Printer className="w-4 h-4 mr-1.5" />
            <span className="hidden sm:inline">Print</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleOpenInNewTab}
            className="text-gray-400 hover:text-white hover:bg-gray-700"
          >
            <ExternalLink className="w-4 h-4 mr-1.5" />
            <span className="hidden sm:inline">Open</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDownload}
            className="text-gray-400 hover:text-white hover:bg-gray-700"
          >
            <Download className="w-4 h-4 mr-1.5" />
            <span className="hidden sm:inline">Download</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleFullscreen}
            className="text-gray-400 hover:text-white hover:bg-gray-700"
          >
            {isFullscreen ? (
              <Minimize2 className="w-4 h-4" />
            ) : (
              <Maximize2 className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>

      {/* Report Content */}
      <div className="flex-1 overflow-hidden bg-white">
        <iframe
          ref={iframeRef}
          srcDoc={html}
          title="Business Report"
          className="w-full h-full border-0"
          sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
        />
      </div>
    </div>
  )
}

export default ReportViewer
