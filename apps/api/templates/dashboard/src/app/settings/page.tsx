import { Sidebar } from '@/components/Sidebar'
import { Header } from '@/components/Header'
import { User, Bell, Shield, Palette, Globe, CreditCard } from 'lucide-react'

const settingsSections = [
  {
    icon: User,
    title: 'Profile',
    description: 'Manage your personal information and preferences',
  },
  {
    icon: Bell,
    title: 'Notifications',
    description: 'Configure how you receive alerts and updates',
  },
  {
    icon: Shield,
    title: 'Security',
    description: 'Password, two-factor authentication, and sessions',
  },
  {
    icon: Palette,
    title: 'Appearance',
    description: 'Customize the look and feel of your dashboard',
  },
  {
    icon: Globe,
    title: 'Language & Region',
    description: 'Set your language, timezone, and date format',
  },
  {
    icon: CreditCard,
    title: 'Billing',
    description: 'Manage your subscription and payment methods',
  },
]

export default function SettingsPage() {
  return (
    <div className="min-h-screen" style={{ minHeight: '100vh', background: '#f8fafc', color: '#1e293b' }}>
      <Sidebar />
      <main className="lg:ml-64">
        <Header title="Settings" />

        <div className="p-6 max-w-4xl">
          {/* Profile Section */}
          <div className="bg-surface rounded-xl border border-gray-200 p-6 mb-6">
            <div className="flex items-start gap-6">
              <div className="w-20 h-20 rounded-full bg-brand-primary flex items-center justify-center">
                <span className="text-white text-2xl font-medium">JD</span>
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold">Jane Doe</h2>
                <p className="text-content-muted">jane@acme.com</p>
                <p className="text-sm text-content-muted mt-2">Product Manager at Acme Inc</p>
                <button className="mt-4 px-4 py-2 bg-brand-primary text-white rounded-lg text-sm font-medium hover:bg-brand-primary/90">
                  Edit Profile
                </button>
              </div>
            </div>
          </div>

          {/* Settings Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {settingsSections.map((section, i) => (
              <button
                key={i}
                className="bg-surface rounded-xl border border-gray-200 p-6 text-left hover:border-brand-primary hover:shadow-md transition-all group"
              >
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-brand-primary/10 rounded-lg group-hover:bg-brand-primary/20 transition-colors">
                    <section.icon className="w-5 h-5 text-brand-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{section.title}</h3>
                    <p className="text-sm text-content-muted mt-1">{section.description}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>

          {/* Danger Zone */}
          <div className="mt-8 bg-red-50 border border-red-200 rounded-xl p-6">
            <h3 className="font-semibold text-red-700">Danger Zone</h3>
            <p className="text-sm text-red-600 mt-1">
              Irreversible and destructive actions
            </p>
            <div className="mt-4 flex gap-3">
              <button className="px-4 py-2 bg-white border border-red-300 text-red-600 rounded-lg text-sm font-medium hover:bg-red-50">
                Export Data
              </button>
              <button className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700">
                Delete Account
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
