'use client'

import { useCallback, useState } from 'react'
import Editor, { OnMount, OnChange, Monaco } from '@monaco-editor/react'
import type { editor } from 'monaco-editor'

export interface CodeFile {
  path: string
  content: string
  language?: string
}

interface CodeEditorProps {
  file: CodeFile
  onChange?: (content: string) => void
  readOnly?: boolean
  theme?: 'vs-dark' | 'light'
  className?: string
  showMinimap?: boolean
  wordWrap?: 'on' | 'off' | 'wordWrapColumn' | 'bounded'
  fontSize?: number
}

// Map file extensions to Monaco languages
const LANGUAGE_MAP: Record<string, string> = {
  '.js': 'javascript',
  '.jsx': 'javascript',
  '.ts': 'typescript',
  '.tsx': 'typescript',
  '.json': 'json',
  '.html': 'html',
  '.htm': 'html',
  '.css': 'css',
  '.scss': 'scss',
  '.sass': 'scss',
  '.less': 'less',
  '.md': 'markdown',
  '.markdown': 'markdown',
  '.py': 'python',
  '.rs': 'rust',
  '.go': 'go',
  '.java': 'java',
  '.c': 'c',
  '.cpp': 'cpp',
  '.h': 'c',
  '.hpp': 'cpp',
  '.cs': 'csharp',
  '.php': 'php',
  '.rb': 'ruby',
  '.swift': 'swift',
  '.kt': 'kotlin',
  '.sql': 'sql',
  '.xml': 'xml',
  '.yaml': 'yaml',
  '.yml': 'yaml',
  '.toml': 'toml',
  '.sh': 'shell',
  '.bash': 'shell',
  '.zsh': 'shell',
  '.dockerfile': 'dockerfile',
  '.graphql': 'graphql',
  '.gql': 'graphql',
}

function getLanguageFromPath(path: string): string {
  // Check for specific filenames first
  const filename = path.split('/').pop()?.toLowerCase() || ''

  if (filename === 'dockerfile') return 'dockerfile'
  if (filename === 'makefile') return 'makefile'
  if (filename === '.gitignore') return 'plaintext'
  if (filename === '.env' || filename.startsWith('.env.')) return 'plaintext'

  // Get extension
  const lastDot = filename.lastIndexOf('.')
  if (lastDot === -1) return 'plaintext'

  const ext = filename.slice(lastDot).toLowerCase()
  return LANGUAGE_MAP[ext] || 'plaintext'
}

export function CodeEditor({
  file,
  onChange,
  readOnly = false,
  theme = 'vs-dark',
  className = '',
  showMinimap = true,
  wordWrap = 'on',
  fontSize = 14
}: CodeEditorProps) {
  const [editorInstance, setEditorInstance] = useState<editor.IStandaloneCodeEditor | null>(null)

  const language = file.language || getLanguageFromPath(file.path)

  const handleEditorMount: OnMount = useCallback((editor: editor.IStandaloneCodeEditor, monaco: Monaco) => {
    setEditorInstance(editor)

    // Configure editor settings
    editor.updateOptions({
      tabSize: 2,
      insertSpaces: true,
      formatOnPaste: true,
      formatOnType: true,
      autoClosingBrackets: 'always',
      autoClosingQuotes: 'always',
      autoIndent: 'full',
      renderWhitespace: 'selection',
      smoothScrolling: true,
      cursorBlinking: 'smooth',
      cursorSmoothCaretAnimation: 'on',
      bracketPairColorization: {
        enabled: true
      }
    })

    // Add keyboard shortcuts
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      // Save action - trigger onChange with current content
      onChange?.(editor.getValue())
    })

    // Format document shortcut
    editor.addCommand(monaco.KeyMod.Shift | monaco.KeyMod.Alt | monaco.KeyCode.KeyF, () => {
      editor.getAction('editor.action.formatDocument')?.run()
    })

    // Focus editor
    editor.focus()
  }, [onChange])

  const handleChange: OnChange = useCallback((value: string | undefined) => {
    if (value !== undefined) {
      onChange?.(value)
    }
  }, [onChange])

  return (
    <div className={`h-full w-full ${className}`}>
      <Editor
        height="100%"
        language={language}
        value={file.content}
        theme={theme}
        onChange={handleChange}
        onMount={handleEditorMount}
        options={{
          readOnly,
          minimap: { enabled: showMinimap },
          wordWrap,
          fontSize,
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          automaticLayout: true,
          padding: { top: 12, bottom: 12 },
          lineHeight: 1.6,
          fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Menlo, Monaco, 'Courier New', monospace",
          fontLigatures: true,
        }}
        loading={
          <div className="flex items-center justify-center h-full bg-gray-900">
            <div className="text-gray-400">Loading editor...</div>
          </div>
        }
      />
    </div>
  )
}

// Multi-file editor with tabs
interface MultiFileEditorProps {
  files: CodeFile[]
  activeFile?: string
  onFileChange?: (path: string, content: string) => void
  onFileSelect?: (path: string) => void
  readOnly?: boolean
  theme?: 'vs-dark' | 'light'
  className?: string
}

export function MultiFileEditor({
  files,
  activeFile,
  onFileChange,
  onFileSelect,
  readOnly = false,
  theme = 'vs-dark',
  className = ''
}: MultiFileEditorProps) {
  const [selectedFile, setSelectedFile] = useState<string>(activeFile || files[0]?.path || '')

  const currentFile = files.find(f => f.path === selectedFile) || files[0]

  const handleFileSelect = useCallback((path: string) => {
    setSelectedFile(path)
    onFileSelect?.(path)
  }, [onFileSelect])

  const handleChange = useCallback((content: string) => {
    if (currentFile) {
      onFileChange?.(currentFile.path, content)
    }
  }, [currentFile, onFileChange])

  const getFileName = (path: string): string => {
    return path.split('/').pop() || path
  }

  const getFileIcon = (path: string): string => {
    const ext = path.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'ts':
      case 'tsx':
        return '📘'
      case 'js':
      case 'jsx':
        return '📙'
      case 'json':
        return '📋'
      case 'css':
      case 'scss':
        return '🎨'
      case 'html':
        return '🌐'
      case 'md':
        return '📝'
      case 'py':
        return '🐍'
      default:
        return '📄'
    }
  }

  if (files.length === 0) {
    return (
      <div className={`flex items-center justify-center h-full bg-gray-900 text-gray-400 ${className}`}>
        No files to display
      </div>
    )
  }

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* File tabs */}
      <div className="flex bg-gray-800 border-b border-gray-700 overflow-x-auto">
        {files.map(file => (
          <button
            key={file.path}
            onClick={() => handleFileSelect(file.path)}
            className={`
              flex items-center gap-1.5 px-3 py-2 text-sm whitespace-nowrap
              border-r border-gray-700 transition-colors
              ${selectedFile === file.path
                ? 'bg-gray-900 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }
            `}
          >
            <span>{getFileIcon(file.path)}</span>
            <span>{getFileName(file.path)}</span>
          </button>
        ))}
      </div>

      {/* Editor */}
      <div className="flex-1">
        {currentFile && (
          <CodeEditor
            file={currentFile}
            onChange={handleChange}
            readOnly={readOnly}
            theme={theme}
          />
        )}
      </div>
    </div>
  )
}

export default CodeEditor
