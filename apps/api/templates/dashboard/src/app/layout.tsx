import './globals.css'
import { ErrorBoundary } from '@/components/ErrorBoundary'

export const metadata = {
  title: 'Dashboard',
  description: 'Modern dashboard prototype',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <script dangerouslySetInnerHTML={{__html: `
          window.onerror = function(m) { window.parent?.postMessage({type:'preview-error',message:m},'*') };
          window.onunhandledrejection = function(e) { window.parent?.postMessage({type:'preview-error',message:e.reason?.message||'Promise rejected'},'*') };
        `}} />
      </head>
      <body style={{ minHeight: '100vh', background: '#f8fafc', color: '#1e293b' }}>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </body>
    </html>
  )
}
