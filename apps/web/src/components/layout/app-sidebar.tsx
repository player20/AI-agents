'use client'

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
} from '@/components/ui/sidebar'
import {
  Home,
  FolderKanban,
  Search,
  FlaskConical,
  LineChart,
  Settings,
  HelpCircle,
  Sparkles,
  Eye,
  LayoutTemplate,
} from 'lucide-react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const mainNavItems = [
  {
    title: 'Create',
    url: '/',
    icon: Sparkles,
  },
  {
    title: 'Preview',
    url: '/preview',
    icon: Eye,
  },
  {
    title: 'Templates',
    url: '/templates',
    icon: LayoutTemplate,
  },
  {
    title: 'Projects',
    url: '/projects',
    icon: FolderKanban,
  },
  {
    title: 'Audit Mode',
    url: '/audit',
    icon: Search,
  },
  {
    title: 'A/B Tests',
    url: '/ab-tests',
    icon: FlaskConical,
  },
  {
    title: 'Market Research',
    url: '/market-research',
    icon: LineChart,
  },
]

const settingsNavItems = [
  {
    title: 'Settings',
    url: '/settings',
    icon: Settings,
  },
  {
    title: 'Help',
    url: '/help',
    icon: HelpCircle,
  },
]

export function AppSidebar() {
  const pathname = usePathname()

  return (
    <Sidebar>
      <SidebarHeader className="border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Sparkles className="h-4 w-4" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold">Code Weaver Pro</span>
            <span className="text-xs text-muted-foreground">52 AI Engineers</span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Main</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {mainNavItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={pathname === item.url}>
                    <Link href={item.url}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Settings</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {settingsNavItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={pathname === item.url}>
                    <Link href={item.url}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t p-4">
        <div className="text-xs text-muted-foreground">
          <p>Open Source</p>
          <p>v2.0.0</p>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
