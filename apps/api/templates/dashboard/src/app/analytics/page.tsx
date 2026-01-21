import { Sidebar } from '@/components/Sidebar'
import { Header } from '@/components/Header'
import { TrendingUp, TrendingDown, Users, Eye, Clock, MousePointer } from 'lucide-react'

const metrics = [
  { label: 'Page Views', value: '124,892', change: '+14.2%', up: true, icon: Eye },
  { label: 'Unique Visitors', value: '48,234', change: '+8.7%', up: true, icon: Users },
  { label: 'Avg. Session', value: '4m 32s', change: '+12.1%', up: true, icon: Clock },
  { label: 'Bounce Rate', value: '32.4%', change: '-5.3%', up: false, icon: MousePointer },
]

const topPages = [
  { path: '/dashboard', views: 12453, change: '+12%' },
  { path: '/products', views: 8234, change: '+8%' },
  { path: '/settings', views: 5123, change: '-3%' },
  { path: '/users', views: 4892, change: '+15%' },
  { path: '/reports', views: 3421, change: '+5%' },
]

export default function AnalyticsPage() {
  return (
    <div className="min-h-screen" style={{ minHeight: '100vh', background: '#f8fafc', color: '#1e293b' }}>
      <Sidebar />
      <main className="lg:ml-64">
        <Header title="Analytics" />

        <div className="p-6">
          {/* Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {metrics.map((metric, i) => (
              <div key={i} className="bg-surface rounded-xl border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <metric.icon className="w-5 h-5 text-content-muted" />
                  <span className={`text-sm font-medium flex items-center gap-1 ${metric.up ? 'text-green-600' : 'text-red-500'}`}>
                    {metric.up ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                    {metric.change}
                  </span>
                </div>
                <p className="text-2xl font-bold">{metric.value}</p>
                <p className="text-sm text-content-muted mt-1">{metric.label}</p>
              </div>
            ))}
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div className="bg-surface rounded-xl border border-gray-200 p-6">
              <h3 className="font-semibold mb-4">Traffic Over Time</h3>
              <div className="h-64 bg-gradient-to-br from-brand-primary/5 to-brand-secondary/5 rounded-lg flex items-end justify-around px-4 pb-4">
                {[65, 45, 75, 55, 85, 60, 90].map((h, i) => (
                  <div key={i} className="flex flex-col items-center gap-2">
                    <div className="w-8 bg-brand-primary rounded-t" style={{ height: `${h * 2}px` }} />
                    <span className="text-xs text-content-muted">
                      {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][i]}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-surface rounded-xl border border-gray-200 p-6">
              <h3 className="font-semibold mb-4">Traffic Sources</h3>
              <div className="space-y-4">
                {[
                  { source: 'Direct', value: 42, color: 'bg-brand-primary' },
                  { source: 'Organic Search', value: 28, color: 'bg-brand-secondary' },
                  { source: 'Referral', value: 18, color: 'bg-brand-accent' },
                  { source: 'Social', value: 12, color: 'bg-purple-500' },
                ].map((item, i) => (
                  <div key={i}>
                    <div className="flex justify-between text-sm mb-1">
                      <span>{item.source}</span>
                      <span className="font-medium">{item.value}%</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className={`h-full ${item.color} rounded-full`} style={{ width: `${item.value}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Top Pages */}
          <div className="bg-surface rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="font-semibold">Top Pages</h3>
            </div>
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-surface-muted">
                  <th className="text-left text-xs font-medium text-content-muted uppercase px-6 py-3">Page</th>
                  <th className="text-right text-xs font-medium text-content-muted uppercase px-6 py-3">Views</th>
                  <th className="text-right text-xs font-medium text-content-muted uppercase px-6 py-3">Change</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {topPages.map((page, i) => (
                  <tr key={i} className="hover:bg-surface-muted">
                    <td className="px-6 py-4 font-mono text-sm">{page.path}</td>
                    <td className="px-6 py-4 text-right">{page.views.toLocaleString()}</td>
                    <td className={`px-6 py-4 text-right ${page.change.startsWith('+') ? 'text-green-600' : 'text-red-500'}`}>
                      {page.change}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  )
}
