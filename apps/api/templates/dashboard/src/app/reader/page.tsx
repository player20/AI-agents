'use client'

import { useState } from 'react'
import { Globe, MapPin, Building2, Filter, Bookmark, Share2, CheckCircle, Clock, TrendingUp, ChevronDown, Search, ExternalLink } from 'lucide-react'
import Link from 'next/link'
import mockData from '@/data/mock.json'

// Region hierarchy
const regions = {
  world: { label: 'World', icon: Globe },
  countries: [
    { id: 'us', label: 'United States', states: ['California', 'New York', 'Texas', 'Florida'] },
    { id: 'uk', label: 'United Kingdom', states: ['England', 'Scotland', 'Wales'] },
    { id: 'eu', label: 'European Union', states: ['Germany', 'France', 'Spain', 'Italy'] },
  ]
}

// Trusted sources with reliability scores
const trustedSources = mockData.sources || [
  { id: 'reuters', name: 'Reuters', reliability: 98, category: 'Wire Service' },
  { id: 'ap', name: 'AP News', reliability: 97, category: 'Wire Service' },
  { id: 'npr', name: 'NPR', reliability: 95, category: 'Public Media' },
  { id: 'bbc', name: 'BBC', reliability: 94, category: 'International' },
]

export default function ReaderPage() {
  const [selectedRegion, setSelectedRegion] = useState<string>('world')
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null)
  const [selectedState, setSelectedState] = useState<string | null>(null)
  const [selectedSources, setSelectedSources] = useState<string[]>([])
  const [showSourceFilter, setShowSourceFilter] = useState(false)
  const [savedArticles, setSavedArticles] = useState<string[]>([])

  const articles = mockData.articles || []

  const toggleSource = (sourceId: string) => {
    setSelectedSources(prev =>
      prev.includes(sourceId)
        ? prev.filter(s => s !== sourceId)
        : [...prev, sourceId]
    )
  }

  const toggleSaved = (articleId: string) => {
    setSavedArticles(prev =>
      prev.includes(articleId)
        ? prev.filter(a => a !== articleId)
        : [...prev, articleId]
    )
  }

  const getRegionLabel = () => {
    if (selectedState) return selectedState
    if (selectedCountry) {
      const country = regions.countries.find(c => c.id === selectedCountry)
      return country?.label || selectedCountry
    }
    return 'World'
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur-xl border-b border-slate-700/50">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                <Globe className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Mira News</h1>
                <p className="text-xs text-slate-400">Fact-first journalism</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Link
                href="/reader/saved"
                className="flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
              >
                <Bookmark className="w-4 h-4" />
                <span className="hidden sm:inline">Saved ({savedArticles.length})</span>
              </Link>
              <Link
                href="/"
                className="px-3 py-2 text-sm text-slate-400 hover:text-white rounded-lg transition-colors"
              >
                Dashboard
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Region Selector */}
        <div className="mb-8">
          <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">Select Region</h2>
          <div className="flex flex-wrap gap-3">
            {/* World */}
            <button
              onClick={() => {
                setSelectedRegion('world')
                setSelectedCountry(null)
                setSelectedState(null)
              }}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                selectedRegion === 'world' && !selectedCountry
                  ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/25'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              <Globe className="w-4 h-4" />
              World
            </button>

            {/* Countries */}
            {regions.countries.map(country => (
              <div key={country.id} className="relative group">
                <button
                  onClick={() => {
                    setSelectedCountry(country.id)
                    setSelectedState(null)
                  }}
                  className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    selectedCountry === country.id
                      ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/25'
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  <MapPin className="w-4 h-4" />
                  {country.label}
                  <ChevronDown className="w-3 h-3" />
                </button>

                {/* State dropdown */}
                {selectedCountry === country.id && (
                  <div className="absolute top-full left-0 mt-2 w-48 bg-slate-800 border border-slate-700 rounded-xl shadow-xl overflow-hidden z-10">
                    <button
                      onClick={() => setSelectedState(null)}
                      className={`w-full px-4 py-2.5 text-left text-sm hover:bg-slate-700 transition-colors ${
                        !selectedState ? 'text-blue-400 bg-slate-700/50' : 'text-slate-300'
                      }`}
                    >
                      All {country.label}
                    </button>
                    {country.states.map(state => (
                      <button
                        key={state}
                        onClick={() => setSelectedState(state)}
                        className={`w-full px-4 py-2.5 text-left text-sm hover:bg-slate-700 transition-colors ${
                          selectedState === state ? 'text-blue-400 bg-slate-700/50' : 'text-slate-300'
                        }`}
                      >
                        <Building2 className="w-3 h-3 inline mr-2" />
                        {state}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Source Filter */}
        <div className="mb-8">
          <button
            onClick={() => setShowSourceFilter(!showSourceFilter)}
            className="flex items-center gap-2 text-sm font-medium text-slate-400 hover:text-white transition-colors"
          >
            <Filter className="w-4 h-4" />
            Filter by Source
            {selectedSources.length > 0 && (
              <span className="px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full">
                {selectedSources.length}
              </span>
            )}
            <ChevronDown className={`w-4 h-4 transition-transform ${showSourceFilter ? 'rotate-180' : ''}`} />
          </button>

          {showSourceFilter && (
            <div className="mt-4 p-4 bg-slate-800/50 rounded-xl border border-slate-700">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {trustedSources.map(source => (
                  <button
                    key={source.id}
                    onClick={() => toggleSource(source.id)}
                    className={`p-3 rounded-lg text-left transition-all ${
                      selectedSources.includes(source.id)
                        ? 'bg-blue-500/20 border-blue-500 border'
                        : 'bg-slate-700/50 border border-transparent hover:border-slate-600'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-white text-sm">{source.name}</span>
                      {selectedSources.includes(source.id) && (
                        <CheckCircle className="w-4 h-4 text-blue-400" />
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-slate-600 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-green-500 rounded-full"
                          style={{ width: `${source.reliability}%` }}
                        />
                      </div>
                      <span className="text-xs text-green-400">{source.reliability}%</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{source.category}</p>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Current Selection */}
        <div className="mb-6 flex items-center gap-2 text-sm">
          <span className="text-slate-400">Showing news for:</span>
          <span className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full font-medium">
            {getRegionLabel()}
          </span>
          {selectedSources.length > 0 && (
            <>
              <span className="text-slate-500">from</span>
              <span className="px-3 py-1 bg-slate-700 text-slate-300 rounded-full">
                {selectedSources.length} source{selectedSources.length > 1 ? 's' : ''}
              </span>
            </>
          )}
        </div>

        {/* News Articles */}
        <div className="space-y-6">
          {articles.map((article: any) => (
            <article
              key={article.id}
              className="bg-slate-800/50 rounded-2xl border border-slate-700/50 overflow-hidden hover:border-slate-600 transition-all group"
            >
              <div className="p-6">
                {/* Header */}
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="px-2.5 py-1 bg-blue-500/20 text-blue-300 text-xs font-medium rounded-full">
                        {article.category}
                      </span>
                      <span className="text-slate-500 text-sm">{article.source}</span>
                      <span className="text-slate-600 text-sm flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {article.time}
                      </span>
                    </div>
                    <Link href={`/reader/article/${article.id}`}>
                      <h3 className="text-xl font-semibold text-white group-hover:text-blue-400 transition-colors cursor-pointer">
                        {article.title}
                      </h3>
                    </Link>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => toggleSaved(article.id)}
                      className={`p-2 rounded-lg transition-colors ${
                        savedArticles.includes(article.id)
                          ? 'bg-blue-500/20 text-blue-400'
                          : 'text-slate-400 hover:text-white hover:bg-slate-700'
                      }`}
                    >
                      <Bookmark className="w-5 h-5" fill={savedArticles.includes(article.id) ? 'currentColor' : 'none'} />
                    </button>
                    <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
                      <Share2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                {/* Verification Badge */}
                <div className="flex items-center gap-4 mb-4 p-3 bg-green-500/10 border border-green-500/20 rounded-xl">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <div>
                    <span className="text-green-400 font-medium text-sm">
                      {article.facts_verified} facts verified
                    </span>
                    <span className="text-slate-500 text-sm ml-2">
                      Status: {article.status}
                    </span>
                  </div>
                </div>

                {/* Pros & Cons Preview */}
                <div className="grid md:grid-cols-2 gap-4 mb-4">
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                    <h4 className="text-xs font-medium text-emerald-400 uppercase tracking-wider mb-2">Key Points (Pros)</h4>
                    <ul className="space-y-1">
                      {article.pros?.slice(0, 2).map((pro: string, i: number) => (
                        <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                          <span className="text-emerald-400 mt-0.5">+</span>
                          {pro}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                    <h4 className="text-xs font-medium text-amber-400 uppercase tracking-wider mb-2">Considerations (Cons)</h4>
                    <ul className="space-y-1">
                      {article.cons?.slice(0, 2).map((con: string, i: number) => (
                        <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                          <span className="text-amber-400 mt-0.5">-</span>
                          {con}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Read More */}
                <Link
                  href={`/reader/article/${article.id}`}
                  className="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors"
                >
                  Read full analysis
                  <ExternalLink className="w-4 h-4" />
                </Link>
              </div>
            </article>
          ))}
        </div>

        {/* Trending Topics */}
        <div className="mt-12">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-400" />
            Trending Topics
          </h2>
          <div className="flex flex-wrap gap-3">
            {(mockData.trending || []).map((topic: any) => (
              <button
                key={topic.id}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-sm transition-colors flex items-center gap-2"
              >
                {topic.topic}
                <span className="text-xs text-slate-500">{topic.articles} articles</span>
                {topic.trend === 'up' && <TrendingUp className="w-3 h-3 text-green-400" />}
              </button>
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}
