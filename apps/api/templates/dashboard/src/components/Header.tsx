'use client'

import { Bell, Search, Menu } from 'lucide-react'

interface HeaderProps {
  title: string
}

export function Header({ title }: HeaderProps) {
  return (
    <header className="h-16 bg-surface border-b border-gray-200 flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <button className="lg:hidden p-2 text-content-muted hover:text-content rounded-lg hover:bg-surface-muted">
          <Menu className="w-5 h-5" />
        </button>
        <h1 className="font-heading font-semibold text-xl">{title}</h1>
      </div>

      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="hidden md:flex items-center gap-2 px-3 py-2 bg-surface-muted rounded-lg">
          <Search className="w-4 h-4 text-content-muted" />
          <input
            type="text"
            placeholder="Search..."
            className="bg-transparent border-none outline-none text-sm w-48"
          />
          <kbd className="text-xs text-content-muted bg-surface px-1.5 py-0.5 rounded">⌘K</kbd>
        </div>

        {/* Notifications */}
        <button className="relative p-2 text-content-muted hover:text-content rounded-lg hover:bg-surface-muted">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-brand-accent rounded-full" />
        </button>

        {/* Profile */}
        <button className="w-8 h-8 rounded-full bg-brand-primary flex items-center justify-center">
          <span className="text-white text-sm font-medium">JD</span>
        </button>
      </div>
    </header>
  )
}
