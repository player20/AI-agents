'use client'

import { useState, useRef, useCallback } from 'react'
import { WebContainerPreview, WebContainerFile } from './WebContainer'
import { Terminal, TerminalHandle } from './Terminal'
import { MultiFileEditor, CodeFile } from './CodeEditor'
import { ReportViewer } from '../report/ReportViewer'
import { FileText, Code2 } from 'lucide-react'

type ViewMode = 'split' | 'code' | 'preview'
type PreviewDevice = 'desktop' | 'tablet' | 'mobile'
type MainTab = 'report' | 'prototype'

interface PreviewPaneProps {
  files: CodeFile[]
  onFilesChange?: (files: CodeFile[]) => void
  className?: string
  initialView?: ViewMode
  readOnly?: boolean
  // Report props
  reportHtml?: string
  reportType?: 'transformation_proposal' | 'ux_audit' | 'comprehensive'
  companyName?: string
}

const DEVICE_SIZES: Record<PreviewDevice, { width: string; label: string }> = {
  desktop: { width: '100%', label: 'Desktop' },
  tablet: { width: '768px', label: 'Tablet' },
  mobile: { width: '375px', label: 'Mobile' },
}

export function PreviewPane({
  files,
  onFilesChange,
  className = '',
  initialView = 'split',
  readOnly = false,
  reportHtml,
  reportType,
  companyName
}: PreviewPaneProps) {
  // Main tab: report vs prototype (default to report if available)
  const [mainTab, setMainTab] = useState<MainTab>(reportHtml ? 'report' : 'prototype')
  const [viewMode, setViewMode] = useState<ViewMode>(initialView)
  const [device, setDevice] = useState<PreviewDevice>('desktop')
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [showTerminal, setShowTerminal] = useState(true)
  const [activeFile, setActiveFile] = useState<string>(files[0]?.path || '')
  const terminalRef = useRef<TerminalHandle>(null)

  // Auto-switch to report tab when report becomes available
  const hasReport = !!reportHtml

  // Convert CodeFile[] to WebContainerFile[]
  const webContainerFiles: WebContainerFile[] = files.map(f => ({
    path: f.path.startsWith('/') ? f.path.slice(1) : f.path,
    content: f.content
  }))

  const handleFileChange = useCallback((path: string, content: string) => {
    const newFiles = files.map(f =>
      f.path === path ? { ...f, content } : f
    )
    onFilesChange?.(newFiles)
  }, [files, onFilesChange])

  const handlePreviewReady = useCallback((url: string) => {
    setPreviewUrl(url)
    terminalRef.current?.writeln(`\x1b[32m✓ Preview ready at ${url}\x1b[0m`)
  }, [])

  const handlePreviewError = useCallback((error: string) => {
    terminalRef.current?.writeln(`\x1b[31m✗ Error: ${error}\x1b[0m`)
  }, [])

  const handleOutput = useCallback((output: string) => {
    terminalRef.current?.write(output)
  }, [])

  const ViewModeButton = ({ mode, label, icon }: { mode: ViewMode; label: string; icon: string }) => (
    <button
      onClick={() => setViewMode(mode)}
      className={`
        px-3 py-1.5 text-sm rounded transition-colors flex items-center gap-1.5
        ${viewMode === mode
          ? 'bg-blue-600 text-white'
          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
        }
      `}
    >
      <span>{icon}</span>
      <span className="hidden sm:inline">{label}</span>
    </button>
  )

  const DeviceButton = ({ deviceType, label }: { deviceType: PreviewDevice; label: string }) => (
    <button
      onClick={() => setDevice(deviceType)}
      className={`
        px-2 py-1 text-xs rounded transition-colors
        ${device === deviceType
          ? 'bg-gray-600 text-white'
          : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
        }
      `}
    >
      {label}
    </button>
  )

  // Tab button component for Report/Prototype tabs
  const MainTabButton = ({ tab, label, icon: Icon }: { tab: MainTab; label: string; icon: React.ElementType }) => (
    <button
      onClick={() => setMainTab(tab)}
      className={`
        px-4 py-2 text-sm font-medium rounded-t-lg transition-colors flex items-center gap-2
        border-b-2 -mb-[2px]
        ${mainTab === tab
          ? 'bg-gray-800 text-white border-blue-500'
          : 'bg-gray-900 text-gray-400 hover:text-gray-200 border-transparent hover:bg-gray-800/50'
        }
        ${tab === 'report' && !hasReport ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      disabled={tab === 'report' && !hasReport}
    >
      <Icon className="w-4 h-4" />
      {label}
      {tab === 'report' && hasReport && (
        <span className="ml-1 px-1.5 py-0.5 text-[10px] bg-green-500/20 text-green-400 rounded-full">
          NEW
        </span>
      )}
    </button>
  )

  return (
    <div className={`flex flex-col h-full bg-gray-900 ${className}`}>
      {/* Main Tabs: Report vs Prototype */}
      <div className="flex items-center px-4 pt-2 bg-gray-900 border-b border-gray-700">
        <MainTabButton tab="report" label="Business Report" icon={FileText} />
        <MainTabButton tab="prototype" label="Prototype" icon={Code2} />
      </div>

      {/* Report View */}
      {mainTab === 'report' && hasReport && (
        <ReportViewer
          html={reportHtml!}
          reportType={reportType}
          companyName={companyName}
          className="flex-1"
        />
      )}

      {/* Prototype View (existing functionality) */}
      {mainTab === 'prototype' && (
        <>
          {/* Toolbar */}
          <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
            {/* View mode buttons */}
            <div className="flex items-center gap-2">
              <ViewModeButton mode="code" label="Code" icon="📝" />
              <ViewModeButton mode="split" label="Split" icon="⚡" />
              <ViewModeButton mode="preview" label="Preview" icon="👁️" />
            </div>

            {/* Device selector (only in preview/split mode) */}
            {(viewMode === 'preview' || viewMode === 'split') && (
              <div className="flex items-center gap-1">
                <DeviceButton deviceType="desktop" label="🖥️" />
                <DeviceButton deviceType="tablet" label="📱" />
                <DeviceButton deviceType="mobile" label="📲" />
              </div>
            )}

            {/* Terminal toggle */}
            <button
              onClick={() => setShowTerminal(!showTerminal)}
              className={`
                px-3 py-1.5 text-sm rounded transition-colors flex items-center gap-1.5
                ${showTerminal
                  ? 'bg-gray-600 text-white'
                  : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                }
              `}
            >
                <span>⌨️</span>
              <span className="hidden sm:inline">Terminal</span>
            </button>
          </div>

          {/* Main content */}
          <div className="flex-1 flex overflow-hidden">
            {/* Code editor */}
            {(viewMode === 'code' || viewMode === 'split') && (
              <div className={`${viewMode === 'split' ? 'w-1/2' : 'w-full'} h-full border-r border-gray-700`}>
                <MultiFileEditor
                  files={files}
                  activeFile={activeFile}
                  onFileSelect={setActiveFile}
                  onFileChange={handleFileChange}
                  readOnly={readOnly}
                  theme="vs-dark"
                />
              </div>
            )}

            {/* Preview */}
            {(viewMode === 'preview' || viewMode === 'split') && (
              <div className={`${viewMode === 'split' ? 'w-1/2' : 'w-full'} h-full flex flex-col`}>
                {/* Preview header */}
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-800 border-b border-gray-700">
                  <div className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded-full bg-red-500" />
                    <span className="w-3 h-3 rounded-full bg-yellow-500" />
                    <span className="w-3 h-3 rounded-full bg-green-500" />
                  </div>
                  {previewUrl && (
                    <div className="flex-1 bg-gray-700 rounded px-3 py-1 text-sm text-gray-300 truncate">
                      {previewUrl}
                    </div>
                  )}
                  {previewUrl && (
                    <a
                      href={previewUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 text-sm"
                    >
                      ↗
                    </a>
                  )}
                </div>

                {/* Preview container with device frame */}
                <div className="flex-1 bg-gray-700 p-4 overflow-auto">
                  <div
                    className="mx-auto h-full transition-all duration-300 rounded-lg overflow-hidden shadow-2xl"
                    style={{
                      width: DEVICE_SIZES[device].width,
                      maxWidth: '100%'
                    }}
                  >
                    <WebContainerPreview
                      files={webContainerFiles}
                      onReady={handlePreviewReady}
                      onError={handlePreviewError}
                      onOutput={handleOutput}
                      className="h-full"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Terminal */}
          {showTerminal && (
            <div className="h-48 border-t border-gray-700">
              <Terminal
                ref={terminalRef}
                theme="dark"
              />
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default PreviewPane
