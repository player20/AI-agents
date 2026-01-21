'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  Users,
  BarChart3,
  Settings,
  FileText,
  Bell,
  LogOut,
  ChevronRight,
  Sparkles,
  Globe,
  Bookmark,
  Newspaper
} from 'lucide-react'

const dashboardNav = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Users', href: '/users', icon: Users },
  { name: 'Reports', href: '/reports', icon: FileText },
  { name: 'Notifications', href: '/notifications', icon: Bell, badge: 3 },
  { name: 'Settings', href: '/settings', icon: Settings },
]

const readerNav = [
  { name: 'News Feed', href: '/reader', icon: Newspaper },
  { name: 'Saved Articles', href: '/reader/saved', icon: Bookmark },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed inset-y-0 left-0 w-64 hidden lg:flex flex-col sidebar">
      {/* Logo */}
      <div className="h-16 flex items-center px-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
            <Globe className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="font-bold text-white text-lg">Mira</span>
            <span className="text-blue-400 font-bold text-lg">News</span>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-6 space-y-1 overflow-y-auto">
        {/* Reader Section */}
        <p className="px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">
          News Reader
        </p>
        {readerNav.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/')
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`sidebar-link ${isActive ? 'active' : ''}`}
            >
              <item.icon className="w-5 h-5" />
              <span className="flex-1">{item.name}</span>
              {isActive && <ChevronRight className="w-4 h-4 opacity-50" />}
            </Link>
          )
        })}

        {/* Dashboard Section */}
        <p className="px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4 mt-8">
          Admin Dashboard
        </p>
        {dashboardNav.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`sidebar-link ${isActive ? 'active' : ''}`}
            >
              <item.icon className="w-5 h-5" />
              <span className="flex-1">{item.name}</span>
              {item.badge && (
                <span className="px-2 py-0.5 text-xs font-semibold bg-blue-500 text-white rounded-full">
                  {item.badge}
                </span>
              )}
              {isActive && <ChevronRight className="w-4 h-4 opacity-50" />}
            </Link>
          )
        })}
      </nav>

      {/* Pro Upgrade Card */}
      <div className="px-4 mb-4">
        <div className="p-4 rounded-2xl bg-gradient-to-br from-blue-600/20 to-indigo-600/20 border border-blue-500/20">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center">
              <span className="text-lg">👑</span>
            </div>
            <div>
              <p className="text-sm font-semibold text-white">Upgrade to Pro</p>
              <p className="text-xs text-slate-400">Unlock all features</p>
            </div>
          </div>
          <button className="w-full py-2 px-4 bg-gradient-to-r from-blue-500 to-indigo-500 text-white text-sm font-semibold rounded-xl hover:from-blue-600 hover:to-indigo-600 transition-all shadow-lg shadow-blue-500/25">
            Upgrade Now
          </button>
        </div>
      </div>

      {/* User section */}
      <div className="p-4 border-t border-slate-700/50">
        <div className="flex items-center gap-3 p-2 rounded-xl hover:bg-white/5 transition-colors cursor-pointer group">
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center shadow-lg">
              <span className="text-white font-semibold text-sm">JD</span>
            </div>
            <div className="status-dot online absolute bottom-0 right-0 border-2 border-slate-900" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-white truncate">Jane Doe</p>
            <p className="text-xs text-slate-400 truncate">Product Manager</p>
          </div>
          <button className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 opacity-0 group-hover:opacity-100 transition-all">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  )
}
