'use client'

import { ArrowRight, Play, Sparkles, Star } from 'lucide-react'

export function Hero() {
  return (
    <section className="relative pt-32 pb-20 md:pt-40 md:pb-32 gradient-hero overflow-hidden">
      {/* Background decorations */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-400/20 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute top-40 right-20 w-96 h-96 bg-purple-400/15 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
        <div className="absolute bottom-20 left-1/3 w-64 h-64 bg-emerald-400/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '2s' }} />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="text-center max-w-4xl mx-auto">
          {/* Badge */}
          <div className="animate-fade-in-up inline-flex items-center gap-2 px-4 py-2 bg-white/80 backdrop-blur-sm border border-gray-200/50 rounded-full text-sm font-medium mb-8 shadow-lg">
            <span className="flex items-center gap-1.5 px-2 py-0.5 bg-gradient-to-r from-blue-500 to-indigo-500 text-white rounded-full text-xs font-semibold">
              <Sparkles className="w-3 h-3" />
              NEW
            </span>
            AI-powered analytics now available
            <ArrowRight className="w-4 h-4 text-blue-500" />
          </div>

          {/* Headline */}
          <h1 className="animate-fade-in-up text-5xl md:text-7xl font-extrabold text-gray-900 mb-6 leading-[1.1] tracking-tight" style={{ animationDelay: '0.1s', opacity: 0, animationFillMode: 'forwards' }}>
            Build products that{' '}
            <span className="relative">
              <span className="relative z-10 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
                users love
              </span>
              <svg className="absolute -bottom-2 left-0 w-full" viewBox="0 0 300 12" fill="none">
                <path d="M2 10C50 4 150 4 298 10" stroke="url(#gradient)" strokeWidth="4" strokeLinecap="round"/>
                <defs>
                  <linearGradient id="gradient" x1="0" y1="0" x2="300" y2="0">
                    <stop stopColor="#3b82f6"/>
                    <stop offset="1" stopColor="#8b5cf6"/>
                  </linearGradient>
                </defs>
              </svg>
            </span>
          </h1>

          {/* Subheadline */}
          <p className="animate-fade-in-up text-xl md:text-2xl text-gray-600 mb-10 max-w-2xl mx-auto leading-relaxed" style={{ animationDelay: '0.2s', opacity: 0, animationFillMode: 'forwards' }}>
            The all-in-one platform that helps teams ship faster. Trusted by{' '}
            <span className="font-semibold text-gray-900">10,000+</span> companies worldwide.
          </p>

          {/* CTA Buttons */}
          <div className="animate-fade-in-up flex flex-col sm:flex-row items-center justify-center gap-4 mb-12" style={{ animationDelay: '0.3s', opacity: 0, animationFillMode: 'forwards' }}>
            <a
              href="#"
              className="group flex items-center gap-2 px-8 py-4 btn-primary text-white rounded-2xl font-semibold text-lg"
            >
              Start Free Trial
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </a>
            <a
              href="#"
              className="group flex items-center gap-2 px-8 py-4 btn-secondary rounded-2xl font-semibold text-lg text-gray-700"
            >
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 flex items-center justify-center">
                <Play className="w-4 h-4 text-white ml-0.5" />
              </div>
              Watch Demo
            </a>
          </div>

          {/* Social Proof */}
          <div className="animate-fade-in-up" style={{ animationDelay: '0.4s', opacity: 0, animationFillMode: 'forwards' }}>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
              {/* Avatars */}
              <div className="flex -space-x-3">
                {[
                  'from-blue-400 to-blue-600',
                  'from-emerald-400 to-emerald-600',
                  'from-purple-400 to-purple-600',
                  'from-amber-400 to-amber-600',
                  'from-pink-400 to-pink-600',
                ].map((gradient, i) => (
                  <div
                    key={i}
                    className={`w-12 h-12 rounded-full bg-gradient-to-br ${gradient} border-3 border-white shadow-lg flex items-center justify-center`}
                    style={{ borderWidth: '3px' }}
                  >
                    <span className="text-white font-semibold text-sm">
                      {['JD', 'AK', 'MR', 'SC', 'EL'][i]}
                    </span>
                  </div>
                ))}
              </div>

              {/* Stats */}
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-5 h-5 fill-amber-400 text-amber-400" />
                  ))}
                </div>
                <div className="text-left">
                  <p className="font-semibold text-gray-900">4.9/5 rating</p>
                  <p className="text-sm text-gray-500">from 2,000+ reviews</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Hero Image/Preview */}
        <div className="mt-20 relative animate-scale-in" style={{ animationDelay: '0.5s', opacity: 0, animationFillMode: 'forwards' }}>
          {/* Glow effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 via-indigo-500/20 to-purple-500/20 rounded-3xl blur-3xl transform scale-95" />

          {/* Main preview card */}
          <div className="relative glass rounded-3xl p-2 shadow-2xl">
            <div className="bg-white rounded-2xl overflow-hidden shadow-inner">
              {/* Browser chrome */}
              <div className="flex items-center gap-2 px-4 py-3 bg-gray-50 border-b border-gray-100">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-400" />
                  <div className="w-3 h-3 rounded-full bg-amber-400" />
                  <div className="w-3 h-3 rounded-full bg-emerald-400" />
                </div>
                <div className="flex-1 flex justify-center">
                  <div className="px-4 py-1.5 bg-gray-100 rounded-lg text-xs text-gray-500 font-medium">
                    app.acme.io/dashboard
                  </div>
                </div>
              </div>

              {/* Dashboard preview */}
              <div className="aspect-[16/9] bg-gradient-to-br from-gray-50 to-gray-100 p-6">
                <div className="grid grid-cols-4 gap-4 mb-4">
                  {[
                    { label: 'Revenue', value: '$48.2K', color: 'from-blue-500 to-indigo-500' },
                    { label: 'Users', value: '2,420', color: 'from-emerald-500 to-teal-500' },
                    { label: 'Growth', value: '+24%', color: 'from-purple-500 to-pink-500' },
                    { label: 'Active', value: '1,893', color: 'from-amber-500 to-orange-500' },
                  ].map((stat, i) => (
                    <div key={i} className="bg-white rounded-xl p-4 shadow-sm">
                      <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${stat.color} mb-3`} />
                      <p className="text-xs text-gray-500">{stat.label}</p>
                      <p className="text-lg font-bold text-gray-900">{stat.value}</p>
                    </div>
                  ))}
                </div>
                <div className="bg-white rounded-xl p-4 shadow-sm">
                  <div className="flex items-end justify-between gap-3 h-32">
                    {[40, 65, 45, 80, 70, 95, 60, 85].map((h, i) => (
                      <div
                        key={i}
                        className="flex-1 bg-gradient-to-t from-blue-500 to-indigo-400 rounded-t-lg"
                        style={{ height: `${h}%` }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Floating elements */}
          <div className="absolute -top-6 -right-6 p-4 bg-white rounded-2xl shadow-xl animate-float">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center">
                <span className="text-lg">📈</span>
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-900">Revenue up!</p>
                <p className="text-xs text-emerald-600 font-medium">+32% this month</p>
              </div>
            </div>
          </div>

          <div className="absolute -bottom-4 -left-6 p-4 bg-white rounded-2xl shadow-xl animate-float" style={{ animationDelay: '2s' }}>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                <span className="text-lg">🎉</span>
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-900">New milestone!</p>
                <p className="text-xs text-blue-600 font-medium">10K users reached</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
