'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowLeft, Bookmark, Trash2, Share2, Clock, CheckCircle, FolderOpen } from 'lucide-react'
import mockData from '@/data/mock.json'

export default function SavedArticlesPage() {
  // In production, this would come from localStorage or user account
  const [savedArticles, setSavedArticles] = useState(mockData.articles || [])

  const removeArticle = (articleId: string) => {
    setSavedArticles(prev => prev.filter((a: any) => a.id !== articleId))
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
            <Link
              href="/"
              className="px-3 py-2 text-sm text-slate-400 hover:text-white rounded-lg transition-colors"
            >
              Dashboard
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
              <Bookmark className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Saved Articles</h1>
              <p className="text-slate-400">{savedArticles.length} articles saved</p>
            </div>
          </div>
        </div>

        {/* Saved Articles List */}
        {savedArticles.length > 0 ? (
          <div className="space-y-4">
            {savedArticles.map((article: any) => (
              <article
                key={article.id}
                className="bg-slate-800/50 rounded-2xl border border-slate-700/50 overflow-hidden hover:border-slate-600 transition-all group"
              >
                <div className="p-5">
                  <div className="flex items-start justify-between gap-4">
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
                        <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors cursor-pointer">
                          {article.title}
                        </h3>
                      </Link>

                      {/* Verification Badge */}
                      <div className="flex items-center gap-2 mt-3">
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        <span className="text-green-400 text-sm">
                          {article.facts_verified} facts verified
                        </span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
                        <Share2 className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => removeArticle(article.id)}
                        className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          /* Empty State */
          <div className="text-center py-16">
            <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-slate-800 flex items-center justify-center">
              <FolderOpen className="w-10 h-10 text-slate-600" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">No saved articles</h2>
            <p className="text-slate-400 mb-6">
              Save articles to read later by clicking the bookmark icon
            </p>
            <Link
              href="/reader"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-xl transition-colors"
            >
              Browse news
              <ArrowLeft className="w-4 h-4 rotate-180" />
            </Link>
          </div>
        )}
      </main>
    </div>
  )
}
