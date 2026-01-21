import { NextRequest, NextResponse } from 'next/server'

// Backend API URL - use environment variable or default to localhost
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export async function POST(request: NextRequest) {
  const body = await request.json()
  const { description, platform } = body

  if (!description) {
    return NextResponse.json(
      { error: 'Description is required' },
      { status: 400 }
    )
  }

  try {
    console.log(`[Generate] Calling backend at: ${BACKEND_URL}/api/generate/`)
    console.log(`[Generate] Request: description=${description.substring(0, 50)}..., platform=${platform}`)

    // Call the backend API with AbortController for timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 300000) // 5 minute timeout

    const backendResponse = await fetch(`${BACKEND_URL}/api/generate/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ description, platform }),
      signal: controller.signal,
    })

    clearTimeout(timeoutId)
    console.log(`[Generate] Backend response status: ${backendResponse.status}`)

    if (!backendResponse.ok) {
      // If backend fails, fall back to mock mode
      console.warn(`[Generate] Backend returned ${backendResponse.status}, using mock mode`)
      return generateMockResponse(description, platform)
    }

    // Stream the response from backend
    const stream = new ReadableStream({
      async start(controller) {
        const reader = backendResponse.body?.getReader()
        if (!reader) {
          controller.close()
          return
        }

        try {
          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            controller.enqueue(value)
          }
        } finally {
          controller.close()
        }
      },
    })

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
      },
    })
  } catch (error) {
    console.error('[Generate] Backend connection failed:', error)
    console.warn('[Generate] Using mock mode as fallback')
    return generateMockResponse(description, platform)
  }
}

// Fallback mock response when backend is unavailable
function generateMockResponse(description: string, platform: string) {
  const encoder = new TextEncoder()

  const MOCK_AGENTS = [
    { name: 'Validator', type: 'validation', delay: 500 },
    { name: 'Market Researcher', type: 'research', delay: 800 },
    { name: 'UI/UX Designer', type: 'design', delay: 1000 },
    { name: 'Architect', type: 'architecture', delay: 700 },
    { name: 'Web Engineer', type: 'frontend', delay: 1200 },
    { name: 'Backend Engineer', type: 'backend', delay: 1000 },
    { name: 'Database Specialist', type: 'database', delay: 600 },
    { name: 'Test Engineer', type: 'testing', delay: 800 },
    { name: 'Security Auditor', type: 'security', delay: 500 },
    { name: 'Performance Optimizer', type: 'performance', delay: 400 },
  ]

  const stream = new ReadableStream({
    async start(controller) {
      // Send initial status
      controller.enqueue(
        encoder.encode(
          `data: ${JSON.stringify({
            type: 'status',
            message: 'Starting code generation (mock mode)...',
            platform,
          })}\n\n`
        )
      )

      // Simulate agent executions
      for (const agent of MOCK_AGENTS) {
        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({
              type: 'agent_start',
              agent: agent.name,
              agentType: agent.type,
            })}\n\n`
          )
        )

        await new Promise((resolve) => setTimeout(resolve, agent.delay))

        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({
              type: 'agent_complete',
              agent: agent.name,
              output: `${agent.name} completed analysis for: ${description.substring(0, 50)}...`,
            })}\n\n`
          )
        )
      }

      // Generate mock files
      const mockFiles = generateMockFiles(description, platform)
      controller.enqueue(
        encoder.encode(
          `data: ${JSON.stringify({
            type: 'files',
            files: mockFiles,
          })}\n\n`
        )
      )

      controller.enqueue(
        encoder.encode(
          `data: ${JSON.stringify({
            type: 'complete',
            message: 'Code generation complete!',
            summary: {
              filesGenerated: Object.keys(mockFiles).length,
              platform,
              agents: MOCK_AGENTS.length,
              mode: 'mock',
            },
          })}\n\n`
        )
      )

      controller.close()
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  })
}

function generateMockFiles(
  description: string,
  platform: string
): Record<string, string> {
  const projectName = description
    .split(' ')
    .slice(0, 3)
    .join('-')
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, '')

  if (platform === 'web' || platform === 'all') {
    return {
      'package.json': JSON.stringify(
        {
          name: projectName,
          version: '0.1.0',
          private: true,
          scripts: {
            dev: 'next dev',
            build: 'next build',
            start: 'next start',
          },
          dependencies: {
            next: '13.5.6',
            react: '^18.2.0',
            'react-dom': '^18.2.0',
          },
          devDependencies: {
            '@types/node': '^20.0.0',
            '@types/react': '^18.2.0',
            '@types/react-dom': '^18.2.0',
            typescript: '^5.3.0',
            tailwindcss: '^3.4.0',
            postcss: '^8.4.0',
            autoprefixer: '^10.4.0',
          },
        },
        null,
        2
      ),
      'tsconfig.json': JSON.stringify(
        {
          compilerOptions: {
            target: 'es5',
            lib: ['dom', 'dom.iterable', 'esnext'],
            allowJs: true,
            skipLibCheck: true,
            strict: true,
            noEmit: true,
            esModuleInterop: true,
            module: 'esnext',
            moduleResolution: 'bundler',
            resolveJsonModule: true,
            isolatedModules: true,
            jsx: 'preserve',
            incremental: true,
            plugins: [{ name: 'next' }],
            paths: { '@/*': ['./src/*'] },
          },
          include: ['next-env.d.ts', '**/*.ts', '**/*.tsx', '.next/types/**/*.ts'],
          exclude: ['node_modules'],
        },
        null,
        2
      ),
      'src/app/page.tsx': `'use client'

export default function Home() {
  return (
    <main style={{ minHeight: '100vh', padding: '2rem', backgroundColor: '#0f172a', color: 'white' }} className="min-h-screen p-8 bg-slate-900 text-white">
      <h1 style={{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '1rem' }} className="text-4xl font-bold mb-4">${projectName}</h1>
      <p style={{ color: '#94a3b8' }} className="text-slate-400">
        Generated from: "${description.substring(0, 100)}..."
      </p>
      <div style={{ marginTop: '2rem', padding: '1.5rem', backgroundColor: '#1e293b', borderRadius: '0.5rem' }} className="mt-8 p-6 bg-slate-800 rounded-lg">
        <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '0.5rem' }} className="text-xl font-semibold mb-2">Getting Started</h2>
        <p style={{ color: '#94a3b8' }} className="text-slate-400">This app was generated by Code Weaver Pro.</p>
      </div>
    </main>
  )
}
`,
      'src/app/layout.tsx': `import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '${projectName}',
  description: 'Generated by Code Weaver Pro',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
`,
      'src/app/globals.css': `@tailwind base;
@tailwind components;
@tailwind utilities;
`,
      'tailwind.config.js': `/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {},
  },
  plugins: [],
}
`,
      'next.config.mjs': `/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Use SWC WASM for WebContainer compatibility
  experimental: {
    forceSwcTransforms: true,
  },
  // Disable SWC minification in dev (uses WASM instead)
  swcMinify: false,
}

export default nextConfig
`,
      'postcss.config.js': `module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
`,
      '.babelrc': `{
  "presets": ["next/babel"]
}
`,
      'README.md': `# ${projectName}

Generated by Code Weaver Pro

## Description
${description}

## Getting Started

\`\`\`bash
npm install
npm run dev
\`\`\`

Open [http://localhost:3000](http://localhost:3000) to see your app.
`,
    }
  }

  if (platform === 'ios') {
    return {
      'Package.swift': `// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "${projectName}",
    platforms: [.iOS(.v17)],
    products: [
        .library(name: "${projectName}", targets: ["${projectName}"]),
    ],
    targets: [
        .target(name: "${projectName}"),
    ]
)
`,
      'Sources/App.swift': `import SwiftUI

@main
struct ${projectName.replace(/-/g, '')}App: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
`,
      'Sources/ContentView.swift': `import SwiftUI

struct ContentView: View {
    var body: some View {
        VStack {
            Text("${projectName}")
                .font(.largeTitle)
            Text("${description.substring(0, 50)}...")
                .foregroundColor(.secondary)
        }
        .padding()
    }
}
`,
    }
  }

  if (platform === 'android') {
    return {
      'build.gradle.kts': `plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.example.${projectName.replace(/-/g, '')}"
    compileSdk = 34
}

dependencies {
    implementation("androidx.compose.ui:ui:1.5.4")
    implementation("androidx.compose.material3:material3:1.1.2")
}
`,
      'src/main/kotlin/MainActivity.kt': `package com.example.${projectName.replace(/-/g, '')}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.Text

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            Text("${projectName}")
        }
    }
}
`,
    }
  }

  return {}
}
