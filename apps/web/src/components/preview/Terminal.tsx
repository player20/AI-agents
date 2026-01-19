'use client'

import { useEffect, useRef, useImperativeHandle, forwardRef, useCallback } from 'react'
import { Terminal as XTerm } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'

export interface TerminalHandle {
  write: (text: string) => void
  writeln: (text: string) => void
  clear: () => void
  focus: () => void
}

interface TerminalProps {
  className?: string
  onInput?: (data: string) => void
  fontSize?: number
  fontFamily?: string
  theme?: 'dark' | 'light'
}

const DARK_THEME = {
  background: '#1a1a2e',
  foreground: '#eaeaea',
  cursor: '#f8f8f2',
  cursorAccent: '#1a1a2e',
  selection: 'rgba(248, 248, 242, 0.3)',
  black: '#1a1a2e',
  red: '#ff6b6b',
  green: '#6bcb77',
  yellow: '#ffd93d',
  blue: '#4d96ff',
  magenta: '#c56cf0',
  cyan: '#00d9ff',
  white: '#eaeaea',
  brightBlack: '#6c6c6c',
  brightRed: '#ff8787',
  brightGreen: '#7ee787',
  brightYellow: '#ffe066',
  brightBlue: '#79c0ff',
  brightMagenta: '#d2a8ff',
  brightCyan: '#56d4dd',
  brightWhite: '#ffffff',
}

const LIGHT_THEME = {
  background: '#ffffff',
  foreground: '#1a1a2e',
  cursor: '#1a1a2e',
  cursorAccent: '#ffffff',
  selection: 'rgba(0, 0, 0, 0.2)',
  black: '#1a1a2e',
  red: '#e53935',
  green: '#43a047',
  yellow: '#fb8c00',
  blue: '#1e88e5',
  magenta: '#8e24aa',
  cyan: '#00acc1',
  white: '#f5f5f5',
  brightBlack: '#757575',
  brightRed: '#ef5350',
  brightGreen: '#66bb6a',
  brightYellow: '#ffa726',
  brightBlue: '#42a5f5',
  brightMagenta: '#ab47bc',
  brightCyan: '#26c6da',
  brightWhite: '#fafafa',
}

export const Terminal = forwardRef<TerminalHandle, TerminalProps>(
  function Terminal(
    {
      className = '',
      onInput,
      fontSize = 14,
      fontFamily = "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Menlo, Monaco, 'Courier New', monospace",
      theme = 'dark'
    },
    ref
  ) {
    const containerRef = useRef<HTMLDivElement>(null)
    const terminalRef = useRef<XTerm | null>(null)
    const fitAddonRef = useRef<FitAddon | null>(null)

    // Expose methods to parent
    useImperativeHandle(ref, () => ({
      write: (text: string) => {
        terminalRef.current?.write(text)
      },
      writeln: (text: string) => {
        terminalRef.current?.writeln(text)
      },
      clear: () => {
        terminalRef.current?.clear()
      },
      focus: () => {
        terminalRef.current?.focus()
      }
    }), [])

    const handleResize = useCallback(() => {
      if (fitAddonRef.current && terminalRef.current) {
        try {
          fitAddonRef.current.fit()
        } catch (err) {
          // Ignore fit errors during unmount
        }
      }
    }, [])

    useEffect(() => {
      if (!containerRef.current) return

      // Initialize terminal
      const terminal = new XTerm({
        fontSize,
        fontFamily,
        cursorBlink: true,
        cursorStyle: 'block',
        convertEol: true,
        scrollback: 10000,
        theme: theme === 'dark' ? DARK_THEME : LIGHT_THEME,
      })

      terminalRef.current = terminal

      // Initialize fit addon
      const fitAddon = new FitAddon()
      fitAddonRef.current = fitAddon
      terminal.loadAddon(fitAddon)

      // Open terminal in container
      terminal.open(containerRef.current)

      // Fit to container
      setTimeout(() => {
        try {
          fitAddon.fit()
        } catch (err) {
          // Ignore
        }
      }, 0)

      // Handle input
      if (onInput) {
        terminal.onData(onInput)
      }

      // Handle resize
      const resizeObserver = new ResizeObserver(() => {
        handleResize()
      })
      resizeObserver.observe(containerRef.current)

      window.addEventListener('resize', handleResize)

      // Welcome message
      terminal.writeln('\x1b[1;36m╔══════════════════════════════════════════╗\x1b[0m')
      terminal.writeln('\x1b[1;36m║\x1b[0m  \x1b[1;33mCode Weaver Pro\x1b[0m - WebContainer Terminal  \x1b[1;36m║\x1b[0m')
      terminal.writeln('\x1b[1;36m╚══════════════════════════════════════════╝\x1b[0m')
      terminal.writeln('')

      return () => {
        resizeObserver.disconnect()
        window.removeEventListener('resize', handleResize)
        terminal.dispose()
        terminalRef.current = null
        fitAddonRef.current = null
      }
    }, [fontSize, fontFamily, theme, onInput, handleResize])

    // Update theme when it changes
    useEffect(() => {
      if (terminalRef.current) {
        terminalRef.current.options.theme = theme === 'dark' ? DARK_THEME : LIGHT_THEME
      }
    }, [theme])

    return (
      <div
        ref={containerRef}
        className={`h-full w-full overflow-hidden ${className}`}
        style={{
          backgroundColor: theme === 'dark' ? DARK_THEME.background : LIGHT_THEME.background
        }}
      />
    )
  }
)

export default Terminal
