'use client'

import { Button } from '@/components/ui/button'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { Sparkles, Github, Settings } from 'lucide-react'

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center px-4">
        <SidebarTrigger className="mr-4" aria-label="Toggle sidebar" />

        <div className="flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-primary" />
          <span className="font-bold text-lg">Code Weaver Pro</span>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <Button variant="ghost" size="icon" asChild aria-label="View GitHub repository">
            <a
              href="https://github.com/your-repo/code-weaver-pro"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Github className="h-5 w-5" />
            </a>
          </Button>
          <Button variant="ghost" size="icon" aria-label="Open settings">
            <Settings className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </header>
  )
}
