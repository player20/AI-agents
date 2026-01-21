'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowLeft, Globe, Bookmark, Share2, CheckCircle, AlertCircle, Clock, ExternalLink, Copy, Check, MessageSquare } from 'lucide-react'
import mockData from '@/data/mock.json'

// Sample detailed article data (would come from API in production)
const articleDetails = {
  'art-001': {
    id: 'art-001',
    title: 'Global Climate Summit Reaches Historic Agreement',
    category: 'World',
    source: 'Reuters',
    sourceUrl: 'https://reuters.com',
    time: '2 hours ago',
    readTime: '5 min read',
    facts_verified: 12,
    status: 'verified',
    summary: 'World leaders from 195 countries reached a landmark agreement at the Global Climate Summit, committing to reduce carbon emissions by 50% by 2035 and achieve net-zero by 2050.',

    // Verified Facts (neutral, objective)
    facts: [
      { id: 1, text: '195 countries signed the agreement', source: 'UN Official Statement', verified: true },
      { id: 2, text: 'Target: 50% emission reduction by 2035', source: 'Summit Communiqué', verified: true },
      { id: 3, text: 'Net-zero target set for 2050', source: 'Summit Communiqué', verified: true },
      { id: 4, text: '$100 billion annual climate fund established', source: 'World Bank', verified: true },
      { id: 5, text: 'Agreement is legally binding for signatories', source: 'UN Legal Framework', verified: true },
      { id: 6, text: 'China and US both committed to the targets', source: 'State Department, Chinese Foreign Ministry', verified: true },
    ],

    // Contextual Analysis (clearly labeled as interpretation)
    context: {
      background: 'This agreement follows five years of negotiations that began after the Paris Agreement showed limited enforcement mechanisms. The new framework includes binding penalties for non-compliance.',

      perspectives: [
        {
          viewpoint: 'Environmental Groups',
          position: 'Welcome the targets but express concern about implementation timelines and enforcement mechanisms.',
        },
        {
          viewpoint: 'Industry Leaders',
          position: 'Acknowledge the need for transition but request clearer guidelines and support for economic adaptation.',
        },
        {
          viewpoint: 'Developing Nations',
          position: 'Emphasize the need for climate finance and technology transfer to meet targets equitably.',
        },
      ],

      implications: [
        'Energy sector expected to accelerate renewable investments',
        'Carbon pricing mechanisms likely to expand globally',
        'Potential impact on fossil fuel industry employment',
        'New standards may affect international trade policies',
      ],
    },

    // Pros & Cons (balanced view)
    pros: [
      'Reduced emissions targets with measurable milestones',
      'International cooperation at unprecedented scale',
      'Legally binding commitments with enforcement',
      '$100B annual fund for developing nations',
    ],
    cons: [
      'Implementation challenges remain significant',
      'Funding gaps for developing economies',
      'Economic transition costs for heavy industries',
      'Political will may waver after leadership changes',
    ],

    // Related sources
    relatedSources: [
      { name: 'AP News', title: 'Climate Summit Analysis', reliability: 97 },
      { name: 'BBC', title: 'What the Agreement Means', reliability: 94 },
      { name: 'NPR', title: 'Expert Reactions', reliability: 95 },
    ],
  },
}

export default function ArticlePage({ params }: { params: { id: string } }) {
  const [copied, setCopied] = useState(false)
  const [saved, setSaved] = useState(false)
  const [showAnalysis, setShowAnalysis] = useState(false)

  // Get article from mock data or detailed data
  const article = articleDetails[params.id as keyof typeof articleDetails] ||
    mockData.articles?.find((a: any) => a.id === params.id) ||
    articleDetails['art-001']

  const copyLink = () => {
    navigator.clipboard.writeText(window.location.href)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur-xl border-b border-slate-700/50">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link
              href="/reader"
              className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Back to news</span>
            </Link>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setSaved(!saved)}
                className={`p-2 rounded-lg transition-colors ${
                  saved ? 'bg-blue-500/20 text-blue-400' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <Bookmark className="w-5 h-5" fill={saved ? 'currentColor' : 'none'} />
              </button>
              <button
                onClick={copyLink}
                className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
              >
                {copied ? <Check className="w-5 h-5 text-green-400" /> : <Share2 className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Article Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <span className="px-3 py-1 bg-blue-500/20 text-blue-300 text-sm font-medium rounded-full">
              {article.category}
            </span>
            <a
              href={article.sourceUrl || '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-400 hover:text-white text-sm flex items-center gap-1 transition-colors"
            >
              {article.source}
              <ExternalLink className="w-3 h-3" />
            </a>
            <span className="text-slate-500 text-sm flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {article.time}
            </span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-4 leading-tight">
            {article.title}
          </h1>

          {/* Verification Status */}
          <div className="flex items-center gap-4 p-4 bg-green-500/10 border border-green-500/20 rounded-xl">
            <CheckCircle className="w-6 h-6 text-green-400" />
            <div>
              <p className="text-green-400 font-semibold">
                {article.facts_verified} facts independently verified
              </p>
              <p className="text-slate-400 text-sm">
                All claims cross-referenced with multiple trusted sources
              </p>
            </div>
          </div>
        </div>

        {/* Summary */}
        {article.summary && (
          <div className="mb-8 p-6 bg-slate-800/50 rounded-2xl border border-slate-700">
            <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-3">Summary</h2>
            <p className="text-lg text-slate-200 leading-relaxed">{article.summary}</p>
          </div>
        )}

        {/* FACTS Section - Primary, objective content */}
        <section className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">Verified Facts</h2>
              <p className="text-sm text-slate-400">Objective, source-verified information</p>
            </div>
          </div>

          <div className="space-y-3">
            {(article.facts || []).map((fact: any) => (
              <div
                key={fact.id}
                className="p-4 bg-slate-800/50 border border-slate-700 rounded-xl hover:border-blue-500/30 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-slate-200">{fact.text}</p>
                    <p className="text-sm text-slate-500 mt-1 flex items-center gap-1">
                      <span>Source:</span>
                      <span className="text-slate-400">{fact.source}</span>
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Pros & Cons - Balanced view */}
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">Balanced Analysis</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="p-5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
              <h3 className="text-emerald-400 font-semibold mb-3 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center text-sm">+</span>
                Key Benefits
              </h3>
              <ul className="space-y-2">
                {(article.pros || []).map((pro: string, i: number) => (
                  <li key={i} className="text-slate-300 text-sm flex items-start gap-2">
                    <span className="text-emerald-400 mt-1">•</span>
                    {pro}
                  </li>
                ))}
              </ul>
            </div>
            <div className="p-5 bg-amber-500/10 border border-amber-500/20 rounded-xl">
              <h3 className="text-amber-400 font-semibold mb-3 flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-amber-500/20 flex items-center justify-center text-sm">-</span>
                Key Challenges
              </h3>
              <ul className="space-y-2">
                {(article.cons || []).map((con: string, i: number) => (
                  <li key={i} className="text-slate-300 text-sm flex items-start gap-2">
                    <span className="text-amber-400 mt-1">•</span>
                    {con}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* CONTEXT Section - Optional, clearly labeled as interpretation */}
        {article.context && (
          <section className="mb-8">
            <button
              onClick={() => setShowAnalysis(!showAnalysis)}
              className="w-full flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-xl hover:border-slate-600 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center">
                  <MessageSquare className="w-5 h-5 text-purple-400" />
                </div>
                <div className="text-left">
                  <h2 className="text-lg font-semibold text-white">Contextual Analysis</h2>
                  <p className="text-sm text-slate-400">Background and perspectives (clearly labeled as interpretation)</p>
                </div>
              </div>
              <div className={`w-8 h-8 rounded-lg bg-slate-700 flex items-center justify-center transition-transform ${showAnalysis ? 'rotate-180' : ''}`}>
                <ArrowLeft className="w-4 h-4 text-slate-400 rotate-[-90deg]" />
              </div>
            </button>

            {showAnalysis && (
              <div className="mt-4 space-y-6 p-6 bg-purple-500/5 border border-purple-500/20 rounded-xl">
                {/* Disclaimer */}
                <div className="flex items-start gap-3 p-3 bg-slate-800/50 rounded-lg">
                  <AlertCircle className="w-5 h-5 text-purple-400 mt-0.5" />
                  <p className="text-sm text-slate-400">
                    The following content provides context and interpretation. It is clearly separated from verified facts to help you form your own conclusions.
                  </p>
                </div>

                {/* Background */}
                {article.context.background && (
                  <div>
                    <h3 className="text-purple-400 font-medium mb-2">Background</h3>
                    <p className="text-slate-300">{article.context.background}</p>
                  </div>
                )}

                {/* Multiple Perspectives */}
                {article.context.perspectives && (
                  <div>
                    <h3 className="text-purple-400 font-medium mb-3">Different Perspectives</h3>
                    <div className="space-y-3">
                      {article.context.perspectives.map((p: any, i: number) => (
                        <div key={i} className="p-3 bg-slate-800/50 rounded-lg">
                          <p className="text-white font-medium text-sm mb-1">{p.viewpoint}</p>
                          <p className="text-slate-400 text-sm">{p.position}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Implications */}
                {article.context.implications && (
                  <div>
                    <h3 className="text-purple-400 font-medium mb-2">Potential Implications</h3>
                    <ul className="space-y-2">
                      {article.context.implications.map((imp: string, i: number) => (
                        <li key={i} className="text-slate-300 text-sm flex items-start gap-2">
                          <span className="text-purple-400">→</span>
                          {imp}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {/* Related Sources */}
        {article.relatedSources && (
          <section className="mb-8">
            <h2 className="text-lg font-semibold text-white mb-4">Related Coverage</h2>
            <div className="grid gap-3">
              {article.relatedSources.map((source: any, i: number) => (
                <a
                  key={i}
                  href="#"
                  className="flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-xl hover:border-slate-600 transition-colors group"
                >
                  <div>
                    <p className="text-white group-hover:text-blue-400 transition-colors">{source.title}</p>
                    <p className="text-sm text-slate-500">{source.name}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full">
                      {source.reliability}% reliable
                    </div>
                    <ExternalLink className="w-4 h-4 text-slate-500 group-hover:text-blue-400 transition-colors" />
                  </div>
                </a>
              ))}
            </div>
          </section>
        )}

        {/* Share Actions */}
        <div className="flex flex-wrap gap-3 pt-6 border-t border-slate-700">
          <button
            onClick={copyLink}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition-colors"
          >
            {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Copied!' : 'Copy Link'}
          </button>
          <button
            onClick={() => setSaved(!saved)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-colors ${
              saved
                ? 'bg-blue-500/20 text-blue-400'
                : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
            }`}
          >
            <Bookmark className="w-4 h-4" fill={saved ? 'currentColor' : 'none'} />
            {saved ? 'Saved' : 'Save Article'}
          </button>
        </div>
      </main>
    </div>
  )
}
