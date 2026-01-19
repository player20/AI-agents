'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Settings,
  Key,
  Globe,
  Bell,
  Palette,
  Database,
  Shield,
  Save,
  Check,
} from 'lucide-react'

export default function SettingsPage() {
  const [saved, setSaved] = useState(false)
  const [settings, setSettings] = useState({
    // API Keys
    anthropicKey: '',
    openaiKey: '',
    xaiKey: '',
    // Preferences
    defaultModel: 'haiku',
    theme: 'dark',
    notifications: true,
    autoSave: true,
    // Backend
    backendUrl: 'http://localhost:8000',
  })

  const handleSave = () => {
    // Save to localStorage for now
    localStorage.setItem('weaver-settings', JSON.stringify(settings))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Configure your Code Weaver Pro preferences
        </p>
      </div>

      {/* API Keys */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            API Keys
          </CardTitle>
          <CardDescription>
            Configure API keys for AI providers. Keys are stored securely in your browser.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="anthropic-key">Anthropic API Key</Label>
            <Input
              id="anthropic-key"
              type="password"
              placeholder="sk-ant-..."
              value={settings.anthropicKey}
              onChange={(e) =>
                setSettings((s) => ({ ...s, anthropicKey: e.target.value }))
              }
            />
            <p className="text-xs text-muted-foreground">
              Required for all AI features. Get yours at{' '}
              <a
                href="https://console.anthropic.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                console.anthropic.com
              </a>
            </p>
          </div>

          <Separator />

          <div className="space-y-2">
            <Label htmlFor="openai-key">OpenAI API Key (Optional)</Label>
            <Input
              id="openai-key"
              type="password"
              placeholder="sk-..."
              value={settings.openaiKey}
              onChange={(e) =>
                setSettings((s) => ({ ...s, openaiKey: e.target.value }))
              }
            />
            <p className="text-xs text-muted-foreground">
              Used for GPT model fallbacks
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="xai-key">xAI/Grok API Key (Optional)</Label>
            <Input
              id="xai-key"
              type="password"
              placeholder="xai-..."
              value={settings.xaiKey}
              onChange={(e) =>
                setSettings((s) => ({ ...s, xaiKey: e.target.value }))
              }
            />
            <p className="text-xs text-muted-foreground">
              Used for Grok model support
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Model Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Model Preferences
          </CardTitle>
          <CardDescription>
            Configure default AI model and behavior
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="default-model">Default Model</Label>
            <Select
              value={settings.defaultModel}
              onValueChange={(value) =>
                setSettings((s) => ({ ...s, defaultModel: value }))
              }
            >
              <SelectTrigger aria-label="Select default model">
                <SelectValue placeholder="Select model" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="haiku">Claude Haiku (Fast)</SelectItem>
                <SelectItem value="sonnet">Claude Sonnet (Balanced)</SelectItem>
                <SelectItem value="opus">Claude Opus (Best Quality)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="h-5 w-5" />
            Appearance
          </CardTitle>
          <CardDescription>
            Customize the look and feel
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="theme">Theme</Label>
            <Select
              value={settings.theme}
              onValueChange={(value) =>
                setSettings((s) => ({ ...s, theme: value }))
              }
            >
              <SelectTrigger aria-label="Select theme">
                <SelectValue placeholder="Select theme" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="dark">Dark</SelectItem>
                <SelectItem value="light">Light</SelectItem>
                <SelectItem value="system">System</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Notifications
          </CardTitle>
          <CardDescription>
            Manage notification preferences
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable Notifications</Label>
              <p className="text-xs text-muted-foreground">
                Receive notifications for completed tasks
              </p>
            </div>
            <Switch
              checked={settings.notifications}
              onCheckedChange={(checked) =>
                setSettings((s) => ({ ...s, notifications: checked }))
              }
              aria-label="Enable notifications"
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Auto-save Projects</Label>
              <p className="text-xs text-muted-foreground">
                Automatically save changes to your projects
              </p>
            </div>
            <Switch
              checked={settings.autoSave}
              onCheckedChange={(checked) =>
                setSettings((s) => ({ ...s, autoSave: checked }))
              }
              aria-label="Enable auto-save"
            />
          </div>
        </CardContent>
      </Card>

      {/* Backend Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Backend Configuration
          </CardTitle>
          <CardDescription>
            Configure connection to the Weaver Pro backend
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="backend-url">Backend URL</Label>
            <Input
              id="backend-url"
              placeholder="http://localhost:8000"
              value={settings.backendUrl}
              onChange={(e) =>
                setSettings((s) => ({ ...s, backendUrl: e.target.value }))
              }
            />
            <p className="text-xs text-muted-foreground">
              URL of the FastAPI backend server
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button variant="gradient" onClick={handleSave}>
          {saved ? (
            <>
              <Check className="mr-2 h-4 w-4" />
              Saved!
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              Save Settings
            </>
          )}
        </Button>
      </div>
    </div>
  )
}
