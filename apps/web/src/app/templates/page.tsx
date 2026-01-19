'use client'

import { useState } from 'react'
import Link from 'next/link'

// Template categories
type Category = 'all' | 'web' | 'mobile' | 'api' | 'fullstack'

// Template data structure
interface Template {
  id: string
  name: string
  description: string
  category: Category
  tags: string[]
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  preview: string
  stars: number
  uses: number
  author: string
  stack: string[]
}

// Sample templates - in production, these would come from an API
const TEMPLATES: Template[] = [
  {
    id: 'nextjs-saas',
    name: 'Next.js SaaS Starter',
    description: 'Production-ready SaaS template with authentication, billing, and dashboard. Includes Stripe integration and user management.',
    category: 'fullstack',
    tags: ['saas', 'stripe', 'auth', 'dashboard'],
    difficulty: 'intermediate',
    preview: '🚀',
    stars: 1247,
    uses: 3420,
    author: 'Code Weaver Pro',
    stack: ['Next.js', 'TypeScript', 'Tailwind', 'Prisma', 'Stripe']
  },
  {
    id: 'react-dashboard',
    name: 'Admin Dashboard',
    description: 'Beautiful admin dashboard with charts, tables, and data visualization. Dark mode included.',
    category: 'web',
    tags: ['dashboard', 'charts', 'admin'],
    difficulty: 'beginner',
    preview: '📊',
    stars: 892,
    uses: 2156,
    author: 'Code Weaver Pro',
    stack: ['React', 'TypeScript', 'Tailwind', 'Recharts']
  },
  {
    id: 'fastapi-backend',
    name: 'FastAPI REST API',
    description: 'High-performance REST API with authentication, rate limiting, and Swagger docs.',
    category: 'api',
    tags: ['api', 'rest', 'python', 'auth'],
    difficulty: 'intermediate',
    preview: '⚡',
    stars: 634,
    uses: 1823,
    author: 'Code Weaver Pro',
    stack: ['Python', 'FastAPI', 'PostgreSQL', 'Redis']
  },
  {
    id: 'react-native-app',
    name: 'React Native Mobile App',
    description: 'Cross-platform mobile app with navigation, authentication, and native features.',
    category: 'mobile',
    tags: ['mobile', 'ios', 'android', 'cross-platform'],
    difficulty: 'intermediate',
    preview: '📱',
    stars: 567,
    uses: 1245,
    author: 'Code Weaver Pro',
    stack: ['React Native', 'Expo', 'TypeScript']
  },
  {
    id: 'ecommerce-store',
    name: 'E-Commerce Store',
    description: 'Full-featured online store with product listings, cart, checkout, and payment integration.',
    category: 'fullstack',
    tags: ['ecommerce', 'store', 'payments', 'cart'],
    difficulty: 'advanced',
    preview: '🛒',
    stars: 1089,
    uses: 2867,
    author: 'Code Weaver Pro',
    stack: ['Next.js', 'TypeScript', 'Stripe', 'Prisma']
  },
  {
    id: 'landing-page',
    name: 'Marketing Landing Page',
    description: 'Beautiful, conversion-optimized landing page with animations and CTA sections.',
    category: 'web',
    tags: ['landing', 'marketing', 'animations'],
    difficulty: 'beginner',
    preview: '✨',
    stars: 723,
    uses: 4521,
    author: 'Code Weaver Pro',
    stack: ['Next.js', 'Tailwind', 'Framer Motion']
  },
  {
    id: 'blog-platform',
    name: 'Blog Platform',
    description: 'Full-featured blog with MDX support, comments, and SEO optimization.',
    category: 'fullstack',
    tags: ['blog', 'mdx', 'seo', 'comments'],
    difficulty: 'beginner',
    preview: '📝',
    stars: 456,
    uses: 1678,
    author: 'Code Weaver Pro',
    stack: ['Next.js', 'MDX', 'Tailwind']
  },
  {
    id: 'ai-chatbot',
    name: 'AI Chatbot Interface',
    description: 'Chat interface with AI integration, message history, and streaming responses.',
    category: 'web',
    tags: ['ai', 'chatbot', 'streaming', 'openai'],
    difficulty: 'intermediate',
    preview: '🤖',
    stars: 934,
    uses: 2345,
    author: 'Code Weaver Pro',
    stack: ['Next.js', 'TypeScript', 'OpenAI', 'Vercel AI SDK']
  },
]

const CATEGORIES = [
  { id: 'all', label: 'All Templates', icon: '🎯' },
  { id: 'web', label: 'Web Apps', icon: '🌐' },
  { id: 'mobile', label: 'Mobile Apps', icon: '📱' },
  { id: 'api', label: 'APIs', icon: '⚡' },
  { id: 'fullstack', label: 'Full Stack', icon: '🚀' },
]

const DIFFICULTY_COLORS = {
  beginner: 'bg-green-500/20 text-green-400',
  intermediate: 'bg-yellow-500/20 text-yellow-400',
  advanced: 'bg-red-500/20 text-red-400',
}

export default function TemplatesPage() {
  const [category, setCategory] = useState<Category>('all')
  const [searchQuery, setSearchQuery] = useState('')

  // Filter templates
  const filteredTemplates = TEMPLATES.filter(template => {
    const matchesCategory = category === 'all' || template.category === category
    const matchesSearch = searchQuery === '' ||
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))

    return matchesCategory && matchesSearch
  })

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Template Marketplace</h1>
          <p className="text-gray-400">
            Start your next project with a production-ready template. All templates are customizable and built with modern best practices.
          </p>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col lg:flex-row gap-4 mb-8">
          {/* Search */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Category Filter */}
          <div className="flex gap-2 flex-wrap">
            {CATEGORIES.map(cat => (
              <button
                key={cat.id}
                onClick={() => setCategory(cat.id as Category)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  category === cat.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                <span className="mr-1">{cat.icon}</span>
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Results count */}
        <div className="text-sm text-gray-500 mb-4">
          Showing {filteredTemplates.length} template{filteredTemplates.length !== 1 ? 's' : ''}
        </div>

        {/* Templates Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTemplates.map(template => (
            <TemplateCard key={template.id} template={template} />
          ))}
        </div>

        {/* Empty State */}
        {filteredTemplates.length === 0 && (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold mb-2">No templates found</h3>
            <p className="text-gray-400">
              Try adjusting your search or filters to find what you&apos;re looking for.
            </p>
          </div>
        )}

        {/* CTA Section */}
        <div className="mt-12 bg-gradient-to-r from-blue-900/50 to-purple-900/50 rounded-2xl p-8 text-center">
          <h2 className="text-2xl font-bold mb-4">Can&apos;t find what you need?</h2>
          <p className="text-gray-300 mb-6 max-w-2xl mx-auto">
            Describe your project and let our 52 AI agents build a custom application for you in minutes.
          </p>
          <Link
            href="/"
            className="inline-flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
          >
            Start Building
            <svg className="ml-2 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        </div>
      </div>
    </div>
  )
}

function TemplateCard({ template }: { template: Template }) {
  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden hover:border-gray-600 transition-colors group">
      {/* Preview Header */}
      <div className="h-32 bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center">
        <span className="text-5xl transform group-hover:scale-110 transition-transform">
          {template.preview}
        </span>
      </div>

      {/* Content */}
      <div className="p-5">
        <div className="flex items-start justify-between mb-2">
          <h3 className="text-lg font-semibold">{template.name}</h3>
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${DIFFICULTY_COLORS[template.difficulty]}`}>
            {template.difficulty}
          </span>
        </div>

        <p className="text-gray-400 text-sm mb-4 line-clamp-2">
          {template.description}
        </p>

        {/* Stack */}
        <div className="flex flex-wrap gap-1 mb-4">
          {template.stack.slice(0, 4).map(tech => (
            <span
              key={tech}
              className="px-2 py-0.5 bg-gray-700 rounded text-xs text-gray-300"
            >
              {tech}
            </span>
          ))}
          {template.stack.length > 4 && (
            <span className="px-2 py-0.5 bg-gray-700 rounded text-xs text-gray-500">
              +{template.stack.length - 4}
            </span>
          )}
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
          <span className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
            {template.stars.toLocaleString()}
          </span>
          <span className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            {template.uses.toLocaleString()} uses
          </span>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Link
            href={`/preview?template=${template.id}`}
            className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium text-center transition-colors"
          >
            Preview
          </Link>
          <Link
            href={`/?template=${template.id}`}
            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium text-center transition-colors"
          >
            Use Template
          </Link>
        </div>
      </div>
    </div>
  )
}
