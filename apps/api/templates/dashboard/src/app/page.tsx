'use client'

import { Sidebar } from '@/components/Sidebar'
import { Header } from '@/components/Header'
import { StatsCard } from '@/components/StatsCard'
import { DataTable } from '@/components/DataTable'
import { DollarSign, Users, TrendingUp, Clock, ArrowUpRight, Sparkles, Calendar, CheckCircle, Activity, FileText, Shield, Package, ThumbsUp, LayoutGrid } from 'lucide-react'
import mockData from '@/data/mock.json'

const iconMap = {
  DollarSign,
  Users,
  TrendingUp,
  Clock,
  Calendar,
  CheckCircle,
  Activity,
  FileText,
  Shield,
  Package,
  ThumbsUp,
  LayoutGrid,
}

export default function DashboardPage() {
  return (
    <div className="min-h-screen gradient-mesh" style={{ minHeight: '100vh', background: '#f8fafc', color: '#1e293b' }}>
      <Sidebar />

      <main className="lg:ml-64">
        <Header title="Dashboard" />

        <div className="p-6 lg:p-8">
          {/* Welcome Banner */}
          <div className="mb-8 p-6 rounded-2xl bg-gradient-to-r from-blue-600 via-blue-500 to-indigo-600 text-white relative overflow-hidden animate-fade-in-up">
            <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="absolute bottom-0 left-1/2 w-32 h-32 bg-white/5 rounded-full translate-y-1/2" />
            <div className="relative">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-5 h-5" />
                <span className="text-sm font-medium text-blue-100">Mira News Editor Dashboard</span>
              </div>
              <h1 className="text-2xl md:text-3xl font-bold mb-2">Welcome back, Editor!</h1>
              <p className="text-blue-100 max-w-xl">
                Fact accuracy is at 98.2% today. Active readers are up 24% this week. Keep delivering truth.
              </p>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {mockData.stats.map((stat, index) => (
              <div
                key={index}
                className="animate-fade-in-up"
                style={{ animationDelay: `${index * 100}ms`, opacity: 0, animationFillMode: 'forwards' }}
              >
                <StatsCard
                  title={stat.title}
                  value={stat.value}
                  change={stat.change}
                  changeType={stat.changeType as 'increase' | 'decrease'}
                  icon={iconMap[stat.icon as keyof typeof iconMap]}
                />
              </div>
            ))}
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* Chart Section */}
            <div className="lg:col-span-2 card p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="font-semibold text-lg">Revenue Overview</h3>
                  <p className="text-sm text-content-muted">Monthly revenue performance</p>
                </div>
                <select className="text-sm border border-gray-200 rounded-xl px-4 py-2 bg-surface-muted focus:outline-none focus:ring-2 focus:ring-brand-primary/20">
                  <option>Last 6 months</option>
                  <option>Last year</option>
                  <option>All time</option>
                </select>
              </div>

              {/* Modern Chart */}
              <div className="chart-container h-72 relative">
                {/* Y-axis labels */}
                <div className="absolute left-0 top-0 bottom-8 w-12 flex flex-col justify-between text-xs text-content-muted">
                  <span>$60k</span>
                  <span>$40k</span>
                  <span>$20k</span>
                  <span>$0</span>
                </div>

                {/* Chart area */}
                <div className="ml-14 h-full flex items-end gap-4 pb-8">
                  {[
                    { month: 'Jan', value: 40, color: 'from-blue-400 to-blue-600' },
                    { month: 'Feb', value: 65, color: 'from-blue-400 to-blue-600' },
                    { month: 'Mar', value: 45, color: 'from-blue-400 to-blue-600' },
                    { month: 'Apr', value: 80, color: 'from-blue-400 to-blue-600' },
                    { month: 'May', value: 70, color: 'from-emerald-400 to-emerald-600' },
                    { month: 'Jun', value: 95, color: 'from-emerald-400 to-emerald-600' },
                  ].map((item, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center group">
                      <div className="w-full relative">
                        <div
                          className={`w-full bg-gradient-to-t ${item.color} rounded-xl transition-all duration-300 group-hover:shadow-lg group-hover:scale-105 cursor-pointer relative`}
                          style={{ height: `${item.value * 2.2}px` }}
                        >
                          {/* Tooltip */}
                          <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                            ${item.value}k
                          </div>
                          {/* Shine effect */}
                          <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 rounded-xl" />
                        </div>
                      </div>
                      <span className="text-xs text-content-muted mt-3">{item.month}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Activity Feed */}
            <div className="card p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="font-semibold text-lg">Recent Activity</h3>
                <span className="text-xs text-content-muted bg-surface-muted px-2 py-1 rounded-full">Live</span>
              </div>
              <div className="space-y-5">
                {mockData.recentActivity.map((activity, i) => (
                  <div
                    key={activity.id}
                    className="flex gap-4 p-3 rounded-xl hover:bg-surface-muted transition-colors cursor-pointer group"
                  >
                    <div className="relative">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-brand-primary to-brand-secondary flex items-center justify-center flex-shrink-0 shadow-lg">
                        <span className="text-xs font-semibold text-white">
                          {activity.user.split(' ').map(n => n[0]).join('')}
                        </span>
                      </div>
                      {i === 0 && <div className="status-dot online absolute -bottom-0.5 -right-0.5 border-2 border-white" />}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm">
                        <span className="font-semibold text-content">{activity.user}</span>{' '}
                        <span className="text-content-muted">{activity.action}</span>{' '}
                        <span className="font-medium text-brand-primary">{activity.target}</span>
                      </p>
                      <p className="text-xs text-content-muted mt-1">{activity.time}</p>
                    </div>
                    <ArrowUpRight className="w-4 h-4 text-content-muted opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                ))}
              </div>
              <button className="w-full mt-4 py-2.5 text-sm text-brand-primary font-semibold hover:bg-brand-primary/5 rounded-xl transition-colors">
                View all activity
              </button>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[
              { label: 'New Project', icon: '🚀', color: 'from-violet-500 to-purple-600' },
              { label: 'Add Team Member', icon: '👥', color: 'from-blue-500 to-cyan-500' },
              { label: 'Generate Report', icon: '📊', color: 'from-emerald-500 to-teal-500' },
              { label: 'View Analytics', icon: '📈', color: 'from-orange-500 to-amber-500' },
            ].map((action, i) => (
              <button
                key={i}
                className="card p-4 flex items-center gap-3 group hover:border-transparent"
              >
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${action.color} flex items-center justify-center text-xl shadow-lg group-hover:scale-110 transition-transform`}>
                  {action.icon}
                </div>
                <span className="font-medium text-sm">{action.label}</span>
              </button>
            ))}
          </div>

          {/* Users Table */}
          <div className="card overflow-hidden">
            <DataTable users={mockData.users} />
          </div>
        </div>
      </main>
    </div>
  )
}
