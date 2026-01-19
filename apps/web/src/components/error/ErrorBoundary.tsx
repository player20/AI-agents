'use client'

import React, { Component, ErrorInfo, ReactNode } from 'react'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
  resetKeys?: unknown[]
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

/**
 * Generic Error Boundary component for catching and handling React errors
 *
 * Usage:
 * ```tsx
 * <ErrorBoundary fallback={<ErrorFallback />}>
 *   <YourComponent />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo })
    this.props.onError?.(error, errorInfo)

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo)
    }
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    // Reset error state when resetKeys change
    if (this.state.hasError && this.props.resetKeys) {
      const hasKeyChanged = this.props.resetKeys.some(
        (key, index) => key !== prevProps.resetKeys?.[index]
      )
      if (hasKeyChanged) {
        this.reset()
      }
    }
  }

  reset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    })
  }

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <DefaultErrorFallback
          error={this.state.error}
          reset={this.reset}
        />
      )
    }

    return this.props.children
  }
}

/**
 * Default error fallback UI
 */
interface DefaultErrorFallbackProps {
  error: Error | null
  reset: () => void
}

function DefaultErrorFallback({ error, reset }: DefaultErrorFallbackProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[200px] p-6 bg-gray-900 text-white rounded-lg">
      <div className="text-red-400 text-xl mb-2">⚠️ Something went wrong</div>
      <p className="text-gray-400 text-sm mb-4 text-center max-w-md">
        {error?.message || 'An unexpected error occurred'}
      </p>
      <button
        onClick={reset}
        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm transition-colors"
      >
        Try Again
      </button>
    </div>
  )
}

export default ErrorBoundary
