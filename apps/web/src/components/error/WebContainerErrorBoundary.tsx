'use client'

import React, { Component, ErrorInfo, ReactNode } from 'react'

interface WebContainerErrorBoundaryProps {
  children: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface WebContainerErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorType: 'browser' | 'runtime' | 'unknown'
}

/**
 * Specialized Error Boundary for WebContainer components
 *
 * Handles:
 * - Browser compatibility issues (SharedArrayBuffer)
 * - WebContainer boot failures
 * - Runtime errors during code execution
 *
 * Usage:
 * ```tsx
 * <WebContainerErrorBoundary>
 *   <WebContainerPreview files={files} />
 * </WebContainerErrorBoundary>
 * ```
 */
export class WebContainerErrorBoundary extends Component<
  WebContainerErrorBoundaryProps,
  WebContainerErrorBoundaryState
> {
  constructor(props: WebContainerErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorType: 'unknown'
    }
  }

  static getDerivedStateFromError(error: Error): Partial<WebContainerErrorBoundaryState> {
    // Categorize the error
    let errorType: 'browser' | 'runtime' | 'unknown' = 'unknown'

    const errorMessage = error.message.toLowerCase()

    if (
      errorMessage.includes('sharedarraybuffer') ||
      errorMessage.includes('cross-origin') ||
      errorMessage.includes('coop') ||
      errorMessage.includes('coep') ||
      errorMessage.includes('webcontainer') && errorMessage.includes('not supported')
    ) {
      errorType = 'browser'
    } else if (
      errorMessage.includes('boot') ||
      errorMessage.includes('spawn') ||
      errorMessage.includes('process')
    ) {
      errorType = 'runtime'
    }

    return { hasError: true, error, errorType }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.props.onError?.(error, errorInfo)

    // Log to console
    console.error('WebContainer Error:', {
      error,
      errorInfo,
      type: this.state.errorType
    })
  }

  handleRetry = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorType: 'unknown'
    })
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <WebContainerErrorFallback
          error={this.state.error}
          errorType={this.state.errorType}
          onRetry={this.handleRetry}
        />
      )
    }

    return this.props.children
  }
}

/**
 * Error fallback UI specific to WebContainer errors
 */
interface WebContainerErrorFallbackProps {
  error: Error | null
  errorType: 'browser' | 'runtime' | 'unknown'
  onRetry: () => void
}

function WebContainerErrorFallback({
  error,
  errorType,
  onRetry
}: WebContainerErrorFallbackProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-8 bg-gray-900 text-white">
      <div className="max-w-lg w-full">
        {/* Icon and Title */}
        <div className="text-center mb-6">
          <div className="text-4xl mb-3">
            {errorType === 'browser' ? '🌐' : errorType === 'runtime' ? '⚙️' : '⚠️'}
          </div>
          <h2 className="text-xl font-semibold text-red-400">
            {errorType === 'browser'
              ? 'Browser Not Supported'
              : errorType === 'runtime'
              ? 'Preview Runtime Error'
              : 'Preview Error'}
          </h2>
        </div>

        {/* Error Message */}
        <div className="bg-gray-800 rounded-lg p-4 mb-6">
          <p className="text-gray-300 text-sm">
            {error?.message || 'An unexpected error occurred while loading the preview.'}
          </p>
        </div>

        {/* Browser compatibility help */}
        {errorType === 'browser' && (
          <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4 mb-6">
            <h3 className="font-medium text-blue-300 mb-2">Requirements</h3>
            <p className="text-sm text-gray-300 mb-3">
              WebContainer requires a modern browser with SharedArrayBuffer support:
            </p>
            <ul className="text-sm text-gray-400 space-y-1 list-disc list-inside">
              <li>Chrome 91+ or Edge 91+</li>
              <li>Firefox 79+ (with enhanced tracking protection disabled)</li>
              <li>Safari 15.4+</li>
            </ul>
            <p className="text-sm text-gray-400 mt-3">
              Also ensure the page is served with proper COOP/COEP headers
              (already configured in Next.js).
            </p>
          </div>
        )}

        {/* Runtime error help */}
        {errorType === 'runtime' && (
          <div className="bg-yellow-900/30 border border-yellow-700 rounded-lg p-4 mb-6">
            <h3 className="font-medium text-yellow-300 mb-2">What happened?</h3>
            <p className="text-sm text-gray-300">
              The WebContainer runtime encountered an error while trying to execute
              the code. This could be due to:
            </p>
            <ul className="text-sm text-gray-400 mt-2 space-y-1 list-disc list-inside">
              <li>Invalid package.json configuration</li>
              <li>Missing dependencies</li>
              <li>Syntax errors in the code</li>
              <li>Unsupported Node.js features</li>
            </ul>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 justify-center">
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors"
          >
            Try Again
          </button>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm font-medium transition-colors"
          >
            Reload Page
          </button>
        </div>

        {/* Alternative: View code only */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            Can&apos;t load preview?{' '}
            <button
              onClick={() => {
                // Could emit an event to switch to code-only view
                const event = new CustomEvent('webcontainer:fallback-to-code')
                window.dispatchEvent(event)
              }}
              className="text-blue-400 hover:text-blue-300 underline"
            >
              View code only
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}

export default WebContainerErrorBoundary
