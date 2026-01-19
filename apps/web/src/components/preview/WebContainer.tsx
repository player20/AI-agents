'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { WebContainer, FileSystemTree } from '@webcontainer/api'

export interface WebContainerFile {
  path: string
  content: string
}

interface WebContainerPreviewProps {
  files: WebContainerFile[]
  entryCommand?: string
  onReady?: (url: string) => void
  onError?: (error: string) => void
  onOutput?: (output: string) => void
  className?: string
}

// Singleton WebContainer instance (can only boot once per page)
let webcontainerInstance: WebContainer | null = null
let bootPromise: Promise<WebContainer> | null = null

async function getWebContainer(): Promise<WebContainer> {
  if (webcontainerInstance) {
    return webcontainerInstance
  }

  if (bootPromise) {
    return bootPromise
  }

  bootPromise = WebContainer.boot()
  webcontainerInstance = await bootPromise
  return webcontainerInstance
}

function convertFilesToTree(files: WebContainerFile[]): FileSystemTree {
  const tree: FileSystemTree = {}

  for (const file of files) {
    const parts = file.path.split('/').filter(Boolean)
    let current: FileSystemTree = tree

    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i]
      if (!current[part]) {
        current[part] = { directory: {} }
      }
      const node = current[part]
      if ('directory' in node) {
        current = node.directory
      }
    }

    const filename = parts[parts.length - 1]
    current[filename] = {
      file: { contents: file.content }
    }
  }

  return tree
}

export function WebContainerPreview({
  files,
  entryCommand = 'npm run dev',
  onReady,
  onError,
  onOutput,
  className = ''
}: WebContainerPreviewProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState<string>('Initializing...')
  const [error, setError] = useState<string | null>(null)
  const containerRef = useRef<WebContainer | null>(null)
  const processRef = useRef<any>(null)

  const emitOutput = useCallback((text: string) => {
    onOutput?.(text)
  }, [onOutput])

  useEffect(() => {
    let mounted = true

    async function startContainer() {
      try {
        setStatus('Booting WebContainer...')
        emitOutput('[WebContainer] Booting...\n')

        const container = await getWebContainer()
        if (!mounted) return

        containerRef.current = container

        // Mount files
        setStatus('Mounting files...')
        emitOutput('[WebContainer] Mounting files...\n')
        const fileTree = convertFilesToTree(files)
        await container.mount(fileTree)

        if (!mounted) return

        // Check if package.json exists
        const hasPackageJson = files.some(f => f.path === 'package.json' || f.path === '/package.json')

        if (hasPackageJson) {
          // Install dependencies
          setStatus('Installing dependencies...')
          emitOutput('[WebContainer] Running npm install...\n')

          const installProcess = await container.spawn('npm', ['install'])

          installProcess.output.pipeTo(
            new WritableStream({
              write(data) {
                if (mounted) {
                  emitOutput(data)
                }
              },
            })
          )

          const installExitCode = await installProcess.exit

          if (installExitCode !== 0) {
            throw new Error(`npm install failed with exit code ${installExitCode}`)
          }

          if (!mounted) return

          // Start dev server
          setStatus('Starting development server...')
          emitOutput(`\n[WebContainer] Running ${entryCommand}...\n`)

          const [cmd, ...args] = entryCommand.split(' ')
          processRef.current = await container.spawn(cmd, args)

          processRef.current.output.pipeTo(
            new WritableStream({
              write(data) {
                if (mounted) {
                  emitOutput(data)
                }
              },
            })
          )

          // Listen for server ready
          container.on('server-ready', (port, url) => {
            if (mounted) {
              setPreviewUrl(url)
              setLoading(false)
              setStatus(`Server running on port ${port}`)
              emitOutput(`\n[WebContainer] Server ready at ${url}\n`)
              onReady?.(url)
            }
          })
        } else {
          // No package.json - just show static files
          setStatus('No package.json found - showing static content')
          emitOutput('[WebContainer] No package.json found\n')
          setLoading(false)
        }

      } catch (err) {
        if (mounted) {
          const errorMessage = err instanceof Error ? err.message : 'Unknown error'
          setError(errorMessage)
          setLoading(false)
          emitOutput(`\n[WebContainer] Error: ${errorMessage}\n`)
          onError?.(errorMessage)
        }
      }
    }

    startContainer()

    return () => {
      mounted = false
      // Kill the running process if any
      if (processRef.current) {
        processRef.current.kill()
      }
    }
  }, [files, entryCommand, emitOutput, onReady, onError])

  // Update files when they change
  useEffect(() => {
    if (!containerRef.current || loading) return

    async function updateFiles() {
      const container = containerRef.current
      if (!container) return

      for (const file of files) {
        try {
          await container.fs.writeFile(file.path, file.content)
        } catch (err) {
          // File might be in a directory that doesn't exist yet
          const parts = file.path.split('/').filter(Boolean)
          if (parts.length > 1) {
            const dir = parts.slice(0, -1).join('/')
            await container.fs.mkdir(dir, { recursive: true })
            await container.fs.writeFile(file.path, file.content)
          }
        }
      }
    }

    updateFiles()
  }, [files, loading])

  if (error) {
    return (
      <div className={`flex items-center justify-center bg-gray-900 text-red-400 p-4 ${className}`}>
        <div className="text-center">
          <div className="text-lg font-semibold mb-2">WebContainer Error</div>
          <div className="text-sm opacity-80">{error}</div>
          <div className="text-xs mt-4 opacity-60">
            Note: WebContainer requires a modern browser with SharedArrayBuffer support.
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`relative bg-white ${className}`}>
      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900 text-white z-10">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mb-4" />
          <div className="text-sm">{status}</div>
        </div>
      )}

      {previewUrl ? (
        <iframe
          ref={iframeRef}
          src={previewUrl}
          className="w-full h-full border-0"
          allow="cross-origin-isolated"
          title="Preview"
        />
      ) : !loading && (
        <div className="flex items-center justify-center h-full bg-gray-100 text-gray-500">
          <div className="text-center">
            <div className="text-lg">No preview available</div>
            <div className="text-sm opacity-70">Add a package.json with a dev script to see a live preview</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default WebContainerPreview
