'use client'

import { useState, useEffect, useMemo, Suspense, useCallback } from 'react'
import { PreviewPane } from '@/components/preview'
import type { CodeFile } from '@/components/preview'
import { useProjectStore, getGeneratedFilesFromStorage, getCurrentProjectFromStorage } from '@/stores/project-store'
import { Download, FileDown, Loader2 } from 'lucide-react'

// Simple function to download a single file
function downloadFile(filename: string, content: string) {
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename.split('/').pop() || filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// Function to create and download a ZIP file (using JSZip-like approach)
async function downloadAsZip(files: CodeFile[], projectName: string) {
  // Dynamically import JSZip only when needed
  const JSZip = (await import('jszip')).default
  const zip = new JSZip()

  // Add all files to the zip
  files.forEach(file => {
    zip.file(file.path, file.content)
  })

  // Generate the zip file
  const blob = await zip.generateAsync({ type: 'blob' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${projectName.replace(/[^a-z0-9]/gi, '-').toLowerCase()}.zip`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// Sample React project files (fallback when no generated files)
const SAMPLE_FILES: CodeFile[] = [
  {
    path: 'package.json',
    content: JSON.stringify({
      name: 'demo-app',
      version: '1.0.0',
      private: true,
      scripts: {
        dev: 'vite',
        build: 'vite build',
        preview: 'vite preview'
      },
      dependencies: {
        react: '^18.2.0',
        'react-dom': '^18.2.0'
      },
      devDependencies: {
        '@vitejs/plugin-react': '^4.2.0',
        vite: '^5.0.0'
      }
    }, null, 2)
  },
  {
    path: 'index.html',
    content: `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Code Weaver Pro Demo</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>`
  },
  {
    path: 'vite.config.js',
    content: `import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})`
  },
  {
    path: 'src/main.jsx',
    content: `import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)`
  },
  {
    path: 'src/App.jsx',
    content: `import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="app">
      <header>
        <h1>Code Weaver Pro</h1>
        <p>AI-Powered App Generation</p>
      </header>

      <main>
        <div className="card">
          <button onClick={() => setCount(c => c + 1)}>
            Count: {count}
          </button>
          <p>Edit the code on the left to see live updates!</p>
        </div>

        <div className="features">
          <div className="feature">
            <span className="icon">🤖</span>
            <h3>52 AI Agents</h3>
            <p>Specialized agents for every task</p>
          </div>
          <div className="feature">
            <span className="icon">⚡</span>
            <h3>Lightning Fast</h3>
            <p>Apps in minutes, not weeks</p>
          </div>
          <div className="feature">
            <span className="icon">📱</span>
            <h3>Multi-Platform</h3>
            <p>Web, iOS, and Android</p>
          </div>
        </div>
      </main>

      <footer>
        <p>Built with Code Weaver Pro</p>
      </footer>
    </div>
  )
}

export default App`
  },
  {
    path: 'src/index.css',
    content: `* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  min-height: 100vh;
  color: white;
}

.app {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

header {
  text-align: center;
  margin-bottom: 3rem;
}

header h1 {
  font-size: 2.5rem;
  background: linear-gradient(90deg, #4d96ff, #c56cf0);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.5rem;
}

header p {
  color: #888;
  font-size: 1.1rem;
}

main {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
}

.card button {
  background: linear-gradient(90deg, #4d96ff, #6bcb77);
  border: none;
  padding: 1rem 2rem;
  border-radius: 8px;
  color: white;
  font-size: 1.2rem;
  font-weight: bold;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.card button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(77, 150, 255, 0.3);
}

.card p {
  margin-top: 1rem;
  color: #aaa;
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.feature {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  transition: transform 0.2s;
}

.feature:hover {
  transform: translateY(-4px);
}

.feature .icon {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 1rem;
}

.feature h3 {
  margin-bottom: 0.5rem;
  color: #4d96ff;
}

.feature p {
  color: #888;
  font-size: 0.9rem;
}

footer {
  text-align: center;
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  color: #666;
}`
  }
]

function PreviewContent() {
  const { currentProject } = useProjectStore()
  const [storageFiles, setStorageFiles] = useState<Record<string, string> | null>(null)
  const [storageProject, setStorageProject] = useState<{ name?: string } | null>(null)
  const [isDownloading, setIsDownloading] = useState(false)

  // Load from localStorage on mount (for cross-tab access)
  useEffect(() => {
    const filesFromStorage = getGeneratedFilesFromStorage()
    const projectFromStorage = getCurrentProjectFromStorage()
    if (filesFromStorage) {
      setStorageFiles(filesFromStorage)
    }
    if (projectFromStorage) {
      setStorageProject(projectFromStorage)
    }
  }, [])

  // Convert generated files from Record<string, string> to CodeFile[]
  // First check store, then fall back to localStorage
  const generatedFiles: CodeFile[] = useMemo(() => {
    const filesSource = currentProject?.generatedFiles || storageFiles
    if (!filesSource) return []
    return Object.entries(filesSource).map(([path, content]) => ({
      path,
      content,
    }))
  }, [currentProject?.generatedFiles, storageFiles])

  // Use generated files if available, otherwise fall back to sample files
  const initialFiles = generatedFiles.length > 0 ? generatedFiles : SAMPLE_FILES
  const [files, setFiles] = useState<CodeFile[]>(initialFiles)

  // Update files when generated files change
  useEffect(() => {
    if (generatedFiles.length > 0) {
      setFiles(generatedFiles)
    }
  }, [generatedFiles])

  const projectName = currentProject?.name || storageProject?.name || 'Demo App'
  const isUsingGeneratedFiles = generatedFiles.length > 0

  // Report data
  const reportHtml = currentProject?.reportHtml
  const reportType = currentProject?.reportType

  const handleDownloadZip = useCallback(async () => {
    setIsDownloading(true)
    try {
      await downloadAsZip(files, projectName)
    } catch (error) {
      console.error('Error downloading ZIP:', error)
    } finally {
      setIsDownloading(false)
    }
  }, [files, projectName])

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🧶</span>
          <h1 className="text-lg font-semibold text-white">Code Weaver Pro</h1>
          <span className="px-2 py-0.5 text-xs bg-blue-600 text-white rounded-full">Preview</span>
          {isUsingGeneratedFiles && (
            <span className="px-2 py-0.5 text-xs bg-green-600 text-white rounded-full">
              {projectName}
            </span>
          )}
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-400">
            {isUsingGeneratedFiles
              ? `${files.length} generated files`
              : 'WebContainer Live Preview (Demo)'}
          </span>
          <button
            onClick={handleDownloadZip}
            disabled={isDownloading}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 text-white rounded-md transition-colors"
          >
            {isDownloading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Downloading...
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                Download ZIP
              </>
            )}
          </button>
          <a
            href="/"
            className="text-sm text-blue-400 hover:text-blue-300"
          >
            ← Back to Home
          </a>
        </div>
      </div>

      {/* Preview pane */}
      <div className="flex-1 overflow-hidden">
        <PreviewPane
          files={files}
          onFilesChange={setFiles}
          initialView="split"
          reportHtml={reportHtml}
          reportType={reportType}
          companyName={projectName}
        />
      </div>
    </div>
  )
}

export default function PreviewDemoPage() {
  return (
    <Suspense fallback={
      <div className="h-screen flex items-center justify-center bg-gray-900 text-white">
        Loading preview...
      </div>
    }>
      <PreviewContent />
    </Suspense>
  )
}
