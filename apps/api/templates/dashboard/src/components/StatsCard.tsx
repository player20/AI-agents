import { LucideIcon, TrendingUp, TrendingDown, ArrowUpRight } from 'lucide-react'

interface StatsCardProps {
  title: string
  value: string
  change: string
  changeType: 'increase' | 'decrease'
  icon: LucideIcon
}

const iconColors = [
  { bg: 'from-blue-500 to-indigo-600', shadow: 'shadow-blue-500/25' },
  { bg: 'from-emerald-500 to-teal-600', shadow: 'shadow-emerald-500/25' },
  { bg: 'from-violet-500 to-purple-600', shadow: 'shadow-violet-500/25' },
  { bg: 'from-amber-500 to-orange-600', shadow: 'shadow-amber-500/25' },
]

export function StatsCard({ title, value, change, changeType, icon: Icon }: StatsCardProps) {
  // Get consistent color based on title
  const colorIndex = title.length % iconColors.length
  const colors = iconColors[colorIndex]

  return (
    <div className="stat-card card p-6 group cursor-pointer">
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-xl bg-gradient-to-br ${colors.bg} shadow-lg ${colors.shadow} group-hover:scale-110 transition-transform duration-300`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <button className="p-2 rounded-lg text-content-muted hover:text-content hover:bg-surface-muted opacity-0 group-hover:opacity-100 transition-all">
          <ArrowUpRight className="w-4 h-4" />
        </button>
      </div>

      <div>
        <p className="text-sm text-content-muted font-medium mb-1">{title}</p>
        <p className="text-3xl font-bold tracking-tight">{value}</p>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-100 flex items-center gap-2">
        <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold ${
          changeType === 'increase'
            ? 'bg-emerald-50 text-emerald-600'
            : 'bg-red-50 text-red-600'
        }`}>
          {changeType === 'increase' ? (
            <TrendingUp className="w-3 h-3" />
          ) : (
            <TrendingDown className="w-3 h-3" />
          )}
          {change}
        </div>
        <span className="text-xs text-content-muted">vs last month</span>
      </div>
    </div>
  )
}
